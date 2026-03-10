import sys
import os
from sqlalchemy import text

# 루트 경로 추가
sys.path.append(os.getcwd())

from src.database.models import get_session, get_engine, Event
from src.collectors.lotte import LotteCinemaCollector
from src.collectors.megabox import MegaboxCollector
from src.collectors.cgv import CGVCollector
from src.collectors.cineq import CineQCollector
from src.utils.logger import get_logger

logger = get_logger("DebugTool")

def check_db_schema():
    print("\n--- [Step 1] Checking DB Schema ---")
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(events)"))
        columns = [row[1] for row in result]
        print(f"Columns in 'events' table: {columns}")
        if "Operator" in columns:
            print("✅ 'Operator' column exists.")
        else:
            print("❌ 'Operator' column MISSING!")

def test_collector(name, collector_class):
    print(f"\n--- [Step 2] Testing {name} Collector ---")
    session = get_session()
    try:
        collector = collector_class(session)
        print(f"Instantiated {name}Collector successfully.")
        
        # 신규 이벤트 탐색 실행
        found = collector.discover_new_events()
        print(f"✅ {name} discovery finished. Result: {found}")
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_db_schema()
    
    collectors = [
        ("LOTTE", LotteCinemaCollector),
        ("MEGABOX", MegaboxCollector),
        ("CGV", CGVCollector),
        ("CINEQ", CineQCollector)
    ]
    
    for name, cls in collectors:
        test_collector(name, cls)
