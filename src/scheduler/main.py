import time
import random
import signal
import sys
from datetime import datetime, timedelta
from sqlalchemy import func, or_
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from src.database.models import init_db, get_session, Inventory, Event, get_engine
from src.collectors.lotte import LotteCinemaCollector
from src.collectors.megabox import MegaboxCollector
from src.collectors.cgv import CGVCollector
from src.collectors.cineq import CineQCollector
from src.utils.logger import get_logger

logger = get_logger("Scheduler")

class MovieHubScheduler:
    def __init__(self):
        # DB 기반 JobStore 설정 (SQLite 또는 Postgres 연동)
        jobstores = {
            'default': SQLAlchemyJobStore(engine=get_engine())
        }
        
        # 데몬 스레드를 사용하도록 설정하여 프로세스 종료 시 함께 종료되도록 함
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            job_defaults={'misfire_grace_time': 60, 'coalesce': True},
            # job을 관리하는 스레드 풀을 데몬으로 설정
            executors={'default': {'type': 'threadpool', 'max_workers': 5}}
        )
        self.running = False
        self.collector_map = {
            "LOTTE": LotteCinemaCollector,
            "MEGABOX": MegaboxCollector,
            "CGV": CGVCollector,
            "CINEQ": CineQCollector
        }
        
    def _job_listener(self, event):
        if event.exception:
            logger.error(f"Job {event.job_id} failed: {event.exception}")

    def get_tracking_interval(self):
        """5분(300초)에서 10분(600초) 사이의 랜덤 초를 반환합니다."""
        now = datetime.now()
        # 09:00 ~ 24:00 (추적 시간)
        if 9 <= now.hour < 24:
            return random.randint(300, 600)
        # 그 외 시간 (1~3시간 간격)
        return random.randint(3600, 10800)

    def update_event_inventory(self, event_id, gift_id):
        """특정 이벤트의 재고를 업데이트하는 작업 단위"""
        session = get_session()
        try:
            # 기간 및 소진 여부 재확인
            today = datetime.now().date()
            event = session.query(Event).filter_by(EventID=event_id).first()
            
            if not event:
                logger.info(f"Event {event_id} not found. Removing job.")
                self.remove_job(event_id)
                return

            event_label = f"{event.Operator} : {event.EventName} ({event_id})"
            logger.info(f"--- [Job] Updating {event_label} (Gift {gift_id}) ---")

            if event.ProgressEndDate and event.ProgressEndDate < today:
                logger.info(f"Event {event_label} has ended. Removing job.")
                self.remove_job(event_id)
                return

            collector_class = self.collector_map.get(event.Operator, LotteCinemaCollector)
            collector = collector_class(session)
            collector.collect_target_inventory(event_id, gift_id)
            
        except Exception as e:
            logger.error(f"Error in job for Event {event_id}: {e}")
        finally:
            session.close()
        
        # 다음 실행 시간 스케줄링 (랜덤 초 적용)
        self.schedule_single_event(event_id, gift_id)

    def schedule_single_event(self, event_id, gift_id):
        """개별 이벤트에 대해 다음 실행 시간을 예약합니다."""
        interval_seconds = self.get_tracking_interval()
        run_time = datetime.now() + timedelta(seconds=interval_seconds)
        
        # 로그를 위한 이벤트 정보 조회
        session = get_session()
        event = session.query(Event).filter_by(EventID=event_id).first()
        event_label = f"{event.Operator} : {event.EventName} ({event_id})" if event else event_id
        session.close()

        job_id = f"job_{event_id}"
        self.scheduler.add_job(
            self.update_event_inventory,
            'date',
            run_date=run_time,
            args=[event_id, gift_id],
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Scheduled next update for {event_label} at {run_time.strftime('%H:%M:%S')} (in {interval_seconds}s)")

    def remove_job(self, event_id):
        job_id = f"job_{event_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    def main_discovery_job(self):
        """활성 이벤트를 찾아 각각의 스케줄에 등록하는 메인 관리 작업 (동적 주기 적용)"""
        logger.info("=== Main Discovery Job Started ===")
        session = get_session()
        try:
            # 모든 운영사 컬렉터 탐색 실행
            for operator, collector_class in self.collector_map.items():
                try:
                    collector = collector_class(session)
                    collector.discover_new_events()
                except Exception as e:
                    logger.error(f"Discovery failed for {operator}: {e}")
            
            today = datetime.now().date()
            active_targets = session.query(Inventory.EventID, Inventory.GiftID).distinct().join(
                Event, Event.EventID == Inventory.EventID
            ).filter(
                or_(Event.ProgressEndDate >= today, Event.ProgressEndDate == None)
            ).all()

            for event_id, gift_id in active_targets:
                job_id = f"job_{event_id}"
                if not self.scheduler.get_job(job_id):
                    total_stock = session.query(func.sum(Inventory.ItemCount)).filter_by(EventID=event_id, GiftID=gift_id).scalar() or 0
                    if total_stock > 0:
                        event = session.query(Event).filter_by(EventID=event_id).first()
                        event_label = f"{event.Operator} : {event.EventName} ({event_id})" if event else event_id
                        logger.info(f"Registering new tracking job for {event_label}")
                        self.schedule_single_event(event_id, gift_id)
                        
        except Exception as e:
            logger.error(f"Discovery job error: {e}")
        finally:
            session.close()

        # 다음 탐색 작업 예약 (동적 주기 적용)
        now = datetime.now()
        if 9 <= now.hour < 18:
            # 활동 시간: 10~15분 랜덤
            next_interval = random.randint(600, 900)
        else:
            # 비활동 시간: 1~3시간 랜덤
            next_interval = random.randint(3600, 10800)
            
        run_time = datetime.now() + timedelta(seconds=next_interval)
        self.scheduler.add_job(
            self.main_discovery_job,
            'date',
            run_date=run_time,
            id='main_discovery',
            replace_existing=True
        )
        logger.info(f"Next Discovery Job scheduled at {run_time.strftime('%H:%M:%S')} (in {next_interval}s)")

    def start(self):
        init_db()
        self.running = True
        
        # 리스너 등록 (에러 로그 수집)
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_ERROR)
        
        # 즉시 한 번 실행하여 탐색 루프 시작
        self.main_discovery_job()
        
        self.scheduler.start()
        logger.info("Background scheduler with persistent job store started.")

    def stop(self):
        if self.running:
            self.running = False
            # wait=False를 주어 즉시 종료를 시도하고, 
            # 이미 실행 중인 작업이 있어도 셧다운을 진행합니다.
            try:
                self.scheduler.shutdown(wait=False)
                logger.info("Scheduler shut down successfully.")
            except Exception as e:
                logger.error(f"Error during scheduler shutdown: {e}")

_hub_scheduler = MovieHubScheduler()
scheduler = _hub_scheduler 

def start_scheduler():
    _hub_scheduler.start()

def stop_scheduler():
    _hub_scheduler.stop()
