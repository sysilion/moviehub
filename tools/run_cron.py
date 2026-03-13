import os
import sys
import time
import random
from datetime import datetime

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import or_
from src.database.models import get_session, Event, init_db
from src.collectors.lotte import LotteCinemaCollector
from src.collectors.megabox import MegaboxCollector
from src.collectors.cgv import CGVCollector
from src.collectors.cineq import CineQCollector
from src.utils.logger import get_logger

logger = get_logger("CronRunner")

def run_task():
    logger.info("=== Cron Task Started (GitHub Actions) ===")
    session = get_session()
    init_db() # 테이블 확인
    
    # 1. 신규 이벤트 탐색 (순서 무작위)
    logger.info("Step 1: Discovering new events...")
    collectors_list = [
        ("LOTTE", LotteCinemaCollector(session)),
        ("MEGABOX", MegaboxCollector(session)),
        ("CGV", CGVCollector(session)),
        ("CINEQ", CineQCollector(session))
    ]
    random.shuffle(collectors_list)

    for name, col in collectors_list:
        try:
            found = col.discover_new_events()
            logger.info(f"  - {name}: Found {found} new items")
            time.sleep(random.uniform(5, 10)) # 운영사 간 지연
        except Exception as e:
            logger.error(f"  - {name} discovery failed: {e}")

    # 2. 진행 중인 모든 굿즈 수량 업데이트
    logger.info("Step 2: Updating active event inventories...")
    today = datetime.now().date()
    active_events = session.query(Event).filter(
        Event.GiftID != None,
        or_(Event.ProgressEndDate >= today, Event.ProgressEndDate == None)
    ).all()

    # 이벤트 목록 섞기
    random.shuffle(active_events)
    logger.info(f"  - Found {len(active_events)} active events to update. Order randomized.")
    
    for i, event in enumerate(active_events):
        # 운영사별 새 세션 및 컬렉터 생성 (안전성)
        collector_classes = {
            "LOTTE": LotteCinemaCollector,
            "MEGABOX": MegaboxCollector,
            "CGV": CGVCollector,
            "CINEQ": CineQCollector
        }
        col_class = collector_classes.get(event.Operator)
        if col_class:
            try:
                col = col_class(session)
                col.collect_target_inventory(event.EventID, event.GiftID)
                logger.info(f"  - [{i+1}/{len(active_events)}] Updated {event.Operator}: {event.EventName}")
                
                # 요청 간 랜덤 지연 (2~5초)
                time.sleep(random.uniform(2, 5))
            except Exception as e:
                logger.error(f"  - [Failed] {event.Operator}: {event.EventID}: {e}")

    session.close()
    logger.info("=== Cron Task Finished ===")

if __name__ == "__main__":
    run_task()
