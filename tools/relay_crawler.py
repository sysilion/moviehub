import os
import sys
import time
import random
import requests
import logging
from datetime import datetime
from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import Base, Event, Inventory
from src.collectors.lotte import LotteCinemaCollector
from src.collectors.megabox import MegaboxCollector
from src.collectors.cgv import CGVCollector
from src.collectors.cineq import CineQCollector
from src.utils.logger import get_logger

# 설정
RELAY_DB_URL = "sqlite:///relay.db"
TARGET_URL = os.getenv("TARGET_URL", "http://localhost:8000") # 배포 시 실제 URL로 변경 필요
RELAY_API_KEY = os.getenv("RELAY_API_KEY", "moviehub-relay-secret-key")
UPLOAD_ENDPOINT = f"{TARGET_URL}/api/sync/upload"

logger = get_logger("RelayCrawler")

# 로컬 DB 엔진 및 세션
engine = create_engine(RELAY_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def init_relay_db():
    Base.metadata.create_all(engine)
    logger.info("Relay DB initialized.")

def get_db():
    return SessionLocal()

def send_data_to_server(events, inventories):
    """수집된 데이터를 서버로 전송합니다."""
    if not events and not inventories:
        return

    payload = {
        "events": [],
        "inventory": []
    }

    for e in events:
        payload["events"].append({
            "EventID": e.EventID,
            "Operator": e.Operator,
            "EventName": e.EventName,
            "GiftID": e.GiftID,
            "EventClassificationCode": e.EventClassificationCode,
            "EventTypeCode": e.EventTypeCode,
            "EventTypeName": e.EventTypeName,
            "ProgressStartDate": str(e.ProgressStartDate) if e.ProgressStartDate else None,
            "ProgressEndDate": str(e.ProgressEndDate) if e.ProgressEndDate else None,
            "ImageUrl": e.ImageUrl,
            "DetailImageUrl": e.DetailImageUrl
        })

    for i in inventories:
        payload["inventory"].append({
            "EventID": i.EventID,
            "GiftID": i.GiftID,
            "CinemaID": i.CinemaID,
            "CinemaName": i.CinemaName,
            "DivisionCode": i.DivisionCode,
            "DetailDivisionCode": i.DetailDivisionCode,
            "DivisionName": i.DivisionName,
            "ItemCount": i.ItemCount
        })

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": RELAY_API_KEY
    }

    try:
        # 데이터가 많을 경우 분할 전송 고려 가능 (현재는 한 번에 전송)
        logger.info(f"Sending {len(payload['events'])} events and {len(payload['inventory'])} inventory items to {UPLOAD_ENDPOINT}")
        response = requests.post(UPLOAD_ENDPOINT, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Upload success: {result}")
        return True
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.text}")
        return False

def run_crawler_loop():
    init_relay_db()
    
    collectors = {
        "LOTTE": LotteCinemaCollector,
        "MEGABOX": MegaboxCollector,
        "CGV": CGVCollector,
        "CINEQ": CineQCollector
    }

    while True:
        session = get_db()
        try:
            # 1. 신규 이벤트 탐색
            logger.info("=== Starting Event Discovery ===")
            new_events = []
            for name, col_cls in collectors.items():
                try:
                    col = col_cls(session)
                    found = col.discover_new_events()
                    if found > 0:
                        logger.info(f"[{name}] Found {found} new events.")
                except Exception as e:
                    logger.error(f"[{name}] Discovery failed: {e}")
            
            # 탐색 후 모든 이벤트 조회 (최근 변경된 것만 보내면 좋겠지만, 일단 전체 동기화)
            # 최적화: 최근 1시간 내에 업데이트된 이벤트만 전송하거나 전체 전송
            # 여기서는 안전하게 전체 활성 이벤트 전송
            all_events = session.query(Event).all()
            
            # 2. 재고 수집
            logger.info("=== Starting Inventory Collection ===")
            today = datetime.now().date()
            targets = session.query(Inventory.EventID, Inventory.GiftID).distinct().join(
                Event, Event.EventID == Inventory.EventID
            ).filter(
                or_(Event.ProgressEndDate >= today, Event.ProgressEndDate == None)
            ).all()

            updated_inventory = []
            
            # 타겟이 없으면 이벤트 테이블에서 직접 조회 (초기 상태)
            if not targets:
                 targets = session.query(Event.EventID, Event.GiftID).filter(
                    Event.GiftID != None,
                    or_(Event.ProgressEndDate >= today, Event.ProgressEndDate == None)
                ).all()

            for event_id, gift_id in targets:
                if not gift_id: continue
                
                event = session.query(Event).filter_by(EventID=event_id).first()
                if not event: continue

                col_cls = collectors.get(event.Operator)
                if not col_cls: continue

                try:
                    col = col_cls(session)
                    col.collect_target_inventory(event_id, gift_id)
                    logger.info(f"Collected inventory for {event.Operator} {event.EventName}")
                    
                    # 수집된 인벤토리 조회
                    invs = session.query(Inventory).filter_by(EventID=event_id, GiftID=gift_id).all()
                    updated_inventory.extend(invs)
                    
                    # 딜레이 (서버 부하 방지)
                    time.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.error(f"Collection failed for {event_id}: {e}")

            # 3. 데이터 전송
            logger.info("=== Uploading Data ===")
            send_data_to_server(all_events, updated_inventory)
            
        except Exception as e:
            logger.error(f"Crawler loop error: {e}")
        finally:
            session.close()

        # 대기 (10분 ~ 20분)
        sleep_time = random.randint(600, 1200)
        logger.info(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    run_crawler_loop()
