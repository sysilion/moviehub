import os
import sys
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
    
    collectors = {
        "LOTTE": LotteCinemaCollector(session),
        "MEGABOX": MegaboxCollector(session),
        "CGV": CGVCollector(session),
        "CINEQ": CineQCollector(session)
    }
    
    # 1. 신규 이벤트 탐색
    logger.info("Step 1: Discovering new events...")
    for name, col in collectors.items():
        try:
            found = col.discover_new_events()
            logger.info(f"  - {name}: Found {found} new items")
        except Exception as e:
            logger.error(f"  - {name} discovery failed: {e}")

    # 2. 진행 중인 모든 굿즈 수량 업데이트
    logger.info("Step 2: Updating active event inventories...")
    today = datetime.now().date()
    # 종료되지 않았거나 종료일 정보가 없는 굿즈 매칭 이벤트들 조회
    active_events = session.query(Event).filter(
        Event.GiftID != None,
        or_(Event.ProgressEndDate >= today, Event.ProgressEndDate == None)
    ).all()

    logger.info(f"  - Found {len(active_events)} active events to update")
    
    for event in active_events:
        col = collectors.get(event.Operator)
        if col:
            try:
                col.collect_target_inventory(event.EventID, event.GiftID)
                logger.info(f"  - [Updated] {event.Operator}: {event.EventName}")
            except Exception as e:
                logger.error(f"  - [Failed] {event.Operator}: {event.EventID}: {e}")

    session.close()
    logger.info("=== Cron Task Finished ===")

if __name__ == "__main__":
    run_task()
