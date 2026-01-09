import time
import random
import signal
import sys
from datetime import datetime, timedelta
from sqlalchemy import func
from apscheduler.schedulers.background import BackgroundScheduler
from src.database.models import init_db, get_session, Inventory, Event
from src.collectors.lotte import LotteCinemaCollector
from src.utils.logger import get_logger

logger = get_logger("Scheduler")

class MovieHubScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.running = False

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
        logger.info(f"--- [Job] Updating Event {event_id} (Gift {gift_id}) ---")
        session = get_session()
        try:
            # 기간 및 소진 여부 재확인
            now_str = datetime.now().strftime("%Y-%m-%d")
            event = session.query(Event).filter_by(EventID=event_id).first()
            
            if not event or event.ProgressEndDate < now_str:
                logger.info(f"Event {event_id} has ended. Removing job.")
                self.remove_job(event_id)
                return

            total_stock = session.query(func.sum(Inventory.ItemCount)).filter_by(EventID=event_id, GiftID=gift_id).scalar() or 0
            if total_stock <= 0:
                # 마지막 한 번 더 확인 시도 후 종료
                logger.info(f"Event {event_id} stock potentially exhausted.")
            
            collector = LotteCinemaCollector(session)
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
        
        job_id = f"job_{event_id}"
        self.scheduler.add_job(
            self.update_event_inventory,
            'date',
            run_date=run_time,
            args=[event_id, gift_id],
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Scheduled next update for Event {event_id} at {run_time.strftime('%H:%M:%S')} (in {interval_seconds}s)")

    def remove_job(self, event_id):
        job_id = f"job_{event_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    def main_discovery_job(self):
        """활성 이벤트를 찾아 각각의 스케줄에 등록하는 메인 관리 작업"""
        logger.info("=== Main Discovery Job Started ===")
        session = get_session()
        try:
            # collector.process_events() # 요청에 의해 비활성화 유지
            
            now_str = datetime.now().strftime("%Y-%m-%d")
            active_targets = session.query(Inventory.EventID, Inventory.GiftID).distinct().join(
                Event, Event.EventID == Inventory.EventID
            ).filter(
                Event.ProgressEndDate >= now_str
            ).all()

            for event_id, gift_id in active_targets:
                job_id = f"job_{event_id}"
                # 이미 스케줄링된 작업이 없다면 새로 등록
                if not self.scheduler.get_job(job_id):
                    total_stock = session.query(func.sum(Inventory.ItemCount)).filter_by(EventID=event_id, GiftID=gift_id).scalar() or 0
                    if total_stock > 0:
                        logger.info(f"Registering new tracking job for Event {event_id}")
                        self.schedule_single_event(event_id, gift_id)
                        
        except Exception as e:
            logger.error(f"Discovery job error: {e}")
        finally:
            session.close()

    def start(self):
        init_db()
        self.running = True
        
        # 메인 관리 작업: 1시간마다 새로운 활성 이벤트가 있는지 체크
        self.scheduler.add_job(self.main_discovery_job, 'interval', hours=1, id='main_discovery')
        
        # 즉시 한 번 실행하여 현재 활성 타겟들 등록
        self.main_discovery_job()
        
        self.scheduler.start()
        logger.info("Background scheduler with per-event jobs started.")

    def stop(self):
        self.running = False
        self.scheduler.shutdown()
        logger.info("Scheduler shut down.")

_hub_scheduler = MovieHubScheduler()
scheduler = _hub_scheduler 

def start_scheduler():
    _hub_scheduler.start()

def stop_scheduler():
    _hub_scheduler.stop()
