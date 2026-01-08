from src.database.models import get_session, Event, Inventory
from src.utils.logger import get_logger
from sqlalchemy import func
import os

logger = get_logger("Report")

def generate_report():
    session = get_session()
    try:
        print("\n" + "="*60)
        print(f" MovieHub Status Report - {os.uname().nodename}")
        print("="*60)
        
        # 1. 수집된 이벤트 통계
        total_events = session.query(Event).count()
        print(f"[*] Total Events Collected: {total_events}")
        
        # 2. 인벤토리 요약 (재고가 있는 시네마 수 기준)
        active_goods = session.query(Inventory.EventID, Inventory.GiftID, func.sum(Inventory.ItemCount).label('total_cnt')) \
                              .group_by(Inventory.EventID, Inventory.GiftID).all()
        
        print(f"[*] Tracked Goods: {len(active_goods)}")
        print("-" * 60)
        print(f"{ 'EventID':<16} | {'GiftID':<8} | {'Total Stock':<12}")
        print("-" * 60)
        
        for item in active_goods:
            event = session.query(Event).filter_by(EventID=item.EventID).first()
            event_name = (event.EventName[:30] + '..') if event and len(event.EventName) > 30 else (event.EventName if event else "Unknown")
            print(f"{item.EventID:<16} | {item.GiftID:<8} | {item.total_cnt:<12} ({event_name})")
            
        print("="*60 + "\n")

    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    generate_report()
