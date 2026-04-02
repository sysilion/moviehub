import time
import random
import signal
import sys
import pickle
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
from src.utils.config import settings

logger = get_logger("Scheduler")

# 전역 인스턴스를 위한 플레이스홀더
_hub_scheduler = None

class MovieHubScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(
            job_defaults={'misfire_grace_time': None, 'coalesce': True},
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

    def schedule_single_event(self, event_id, gift_id):
        """개별 이벤트에 대해 다음 실행 시간을 예약합니다."""
        interval_seconds = self.get_tracking_interval()
        run_time = datetime.now() + timedelta(seconds=interval_seconds)
        
        # 로그를 위한 이벤트 정보 조회
        session = get_session()
        try:
            event = session.query(Event).filter_by(EventID=event_id).first()
            event_label = f"{event.Operator} : {event.EventName} ({event_id})" if event else event_id
        except Exception as e:
            logger.warning(f"Failed to fetch event info for logging: {e}")
            event_label = event_id
        finally:
            session.close()

        job_id = f"job_{event_id}"
        self.scheduler.add_job(
            update_event_inventory_task,
            'date',
            run_date=run_time,
            args=[event_id, gift_id],
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Scheduled next update for {event_label} at {run_time.strftime('%H:%M:%S')} (in {interval_seconds}s)")

    def remove_job(self, event_id):
        job_id = f"job_{event_id}"
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
        except Exception as e:
            logger.warning(f"Failed to remove job {job_id}: {e}")

    def schedule_next_discovery(self):
        """다음 탐색 작업의 실행 시간을 예약합니다. (동적 주기 적용)"""
        now = datetime.now()
        if 9 <= now.hour < 18:
            # 활동 시간: 10~15분 랜덤
            next_interval = random.randint(600, 900)
        else:
            # 비활동 시간: 1~3시간 랜덤
            next_interval = random.randint(3600, 10800)
            
        run_time = datetime.now() + timedelta(seconds=next_interval)
        self.scheduler.add_job(
            main_discovery_task,
            'date',
            run_date=run_time,
            id='main_discovery',
            replace_existing=True
        )
        logger.info(f"Next Discovery Job scheduled at {run_time.strftime('%H:%M:%S')} (in {next_interval}s)")

    def start(self):
        try:
            # DB 기반 JobStore 설정 (SQLite 또는 Postgres 연동)
            # migrations가 끝난 후 start() 시점에 추가하여 lock 충돌 방지
            if not settings.is_vercel:
                try:
                    # 'default' jobstore가 이미 존재하는지 확인
                    if 'default' not in self.scheduler._jobstores:
                        self.scheduler.add_jobstore(SQLAlchemyJobStore(engine=get_engine()), 'default')
                        logger.info("Persistent SQLAlchemyJobStore added to scheduler.")
                except Exception as e:
                    logger.error(f"Failed to initialize SQLAlchemyJobStore: {e}")

            self.running = True
            
            # 리스너 등록 (에러 로그 수집)
            self.scheduler.add_listener(self._job_listener, EVENT_JOB_ERROR)
            
            # 초기 탐색 작업 등록 (즉시 실행)
            self.scheduler.add_job(
                main_discovery_task,
                'date',
                run_date=datetime.now(),
                id='main_discovery_initial',
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("Background scheduler started successfully.")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            self.running = False

    def stop(self):
        if self.running:
            self.running = False
            try:
                self.scheduler.shutdown(wait=False)
                logger.info("Scheduler shut down successfully.")
            except Exception as e:
                logger.error(f"Error during scheduler shutdown: {e}")

def update_event_inventory_task(event_id, gift_id):
    """특정 이벤트의 재고를 업데이트하는 작업 단위 (독립 함수)"""
    if not _hub_scheduler:
        logger.error("Scheduler instance is not initialized.")
        return

    session = get_session()
    try:
        today = datetime.now().date()
        event = session.query(Event).filter_by(EventID=event_id).first()
        
        if not event:
            logger.info(f"Event {event_id} not found. Removing job.")
            _hub_scheduler.remove_job(event_id)
            return

        event_label = f"{event.Operator} : {event.EventName} ({event_id})"
        logger.info(f"--- [Job] Updating {event_label} (Gift {gift_id}) ---")

        if event.ProgressEndDate and event.ProgressEndDate < today:
            logger.info(f"Event {event_label} has ended. Removing job.")
            _hub_scheduler.remove_job(event_id)
            return

        collector_class = _hub_scheduler.collector_map.get(event.Operator, LotteCinemaCollector)
        collector = collector_class(session)
        collector.collect_target_inventory(event_id, gift_id)
        
    except Exception as e:
        logger.error(f"Error in job for Event {event_id}: {e}")
    finally:
        session.close()
    
    # 다음 실행 시간 스케줄링
    _hub_scheduler.schedule_single_event(event_id, gift_id)

def main_discovery_task():
    """활성 이벤트를 찾아 각각의 스케줄에 등록하는 메인 관리 작업 (독립 함수)"""
    if not _hub_scheduler:
        logger.error("Scheduler instance is not initialized.")
        return

    logger.info("=== [Discovery] Main Discovery Job Started ===")
    session = get_session()
    try:
        for operator, collector_class in _hub_scheduler.collector_map.items():
            try:
                logger.info(f"--- [Discovery] Starting discovery for {operator} ---")
                collector = collector_class(session)
                count = collector.discover_new_events()
                logger.info(f"--- [Discovery] Finished {operator}: found/updated {count} items ---")
            except Exception as e:
                logger.error(f"Discovery failed for {operator}: {e}")
        
        today = datetime.now().date()
        active_targets = session.query(Inventory.EventID, Inventory.GiftID).distinct().join(
            Event, Event.EventID == Inventory.EventID
        ).filter(
            or_(Event.ProgressEndDate >= today, Event.ProgressEndDate == None)
        ).all()

        logger.info(f"=== [Discovery] Processing {len(active_targets)} active tracking targets ===")
        
        for event_id, gift_id in active_targets:
            # 씨네큐는 discover_new_events에서 모든 재고를 한꺼번에 처리하므로 개별 잡을 생성하지 않음
            event = session.query(Event).filter_by(EventID=event_id).first()
            if event and event.Operator == "CINEQ":
                continue

            job_id = f"job_{event_id}"
            existing_job = _hub_scheduler.scheduler.get_job(job_id)
            
            should_schedule = False
            if not existing_job:
                should_schedule = True
            elif existing_job.next_run_time is None:
                should_schedule = True
            else:
                # 다음 실행 시간이 과거인 경우 (misfire 되어 중단된 상태)
                now = datetime.now(existing_job.next_run_time.tzinfo) if existing_job.next_run_time.tzinfo else datetime.now()
                if existing_job.next_run_time < now:
                    logger.info(f"Stale job detected: {job_id} (last scheduled for {existing_job.next_run_time}). Rescheduling...")
                    should_schedule = True

            if should_schedule:
                total_stock = session.query(func.sum(Inventory.ItemCount)).filter_by(EventID=event_id, GiftID=gift_id).scalar() or 0
                if total_stock > 0:
                    try:
                        event = session.query(Event).filter_by(EventID=event_id).first()
                        event_label = f"{event.Operator} : {event.EventName} ({event_id})" if event else event_id
                        logger.info(f"Registering/Rescheduling tracking job for {event_label}")
                        _hub_scheduler.schedule_single_event(event_id, gift_id)
                    except Exception as e:
                        logger.error(f"Failed to register/reschedule job for {event_id}: {e}")
        
        logger.info("=== [Discovery] Main Discovery Job Completed Successfully ===")
    except Exception as e:
        logger.error(f"Discovery job error: {e}")
    finally:
        session.close()
    
    # 다음 탐색 작업 예약
    if _hub_scheduler:
        _hub_scheduler.schedule_next_discovery()

# 싱글톤 인스턴스 생성
_hub_scheduler = MovieHubScheduler()
scheduler = _hub_scheduler 

def start_scheduler():
    if _hub_scheduler:
        _hub_scheduler.start()

def stop_scheduler():
    if _hub_scheduler:
        _hub_scheduler.stop()
