import time
import random
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from src.database.models import init_db, get_session
from src.collectors.lotte import LotteCinemaCollector
from src.utils.logger import get_logger

logger = get_logger("Scheduler")

scheduler = BackgroundScheduler()

# 알려주신 기준 데이터 설정
TRACKING_TARGETS = [
    ("201010016925850", "13684"),
    ("201010016925841", "13674")
]

def job_function():
    logger.info("=== Scheduled Job Started ===")
    session = get_session()
    try:
        collector = LotteCinemaCollector(session)
        
        # 1. 최신 이벤트 목록 수집
        collector.process_events()
        
        # 2. 알려주신 기준 데이터 및 타겟 굿즈 재고 수집
        for event_id, gift_id in TRACKING_TARGETS:
            try:
                collector.collect_target_inventory(event_id, gift_id)
            except Exception as e:
                logger.error(f"Failed to collect for {event_id}: {e}")
                
    except Exception as e:
        logger.error(f"Job execution failed: {e}")
    finally:
        session.close()
    
    logger.info("=== Scheduled Job Finished ===")
    schedule_next_job()

def schedule_next_job():
    now = datetime.now()
    hour = now.hour
    
    if 9 <= hour < 18:
        minutes = random.randint(10, 15)
        mode = "WORKING TIME"
    else:
        minutes = random.randint(60, 180)
        mode = "OFF-HOURS"
        
    next_run_time = datetime.now() + timedelta(minutes=minutes)
    scheduler.add_job(job_function, 'date', run_date=next_run_time, id='moviehub_main_job', replace_existing=True)
    logger.info(f"Mode: {mode}. Next job at {next_run_time.strftime('%H:%M:%S')}")

def start_scheduler():
    init_db()
    logger.info("Database initialized. Starting scheduler...")
    
    # 즉시 실행
    scheduler.add_job(job_function, 'date', run_date=datetime.now(), id='moviehub_main_job')
    scheduler.start()
    
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped.")
