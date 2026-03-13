import sys
import os
import requests

# 루트 경로 추가
sys.path.append(os.getcwd())

from src.database.models import get_session
from src.collectors.megabox import MegaboxCollector
from src.collectors.cgv import CGVCollector
from src.utils.logger import get_logger

logger = get_logger("CheckRawData")

def save_raw_data(name, collector_class):
    print(f"\n--- [Step 1] Fetching Raw Data from {name} ---")
    session = get_session()
    try:
        collector = collector_class(session)
        html = collector.fetch_events()
        if html:
            filename = f"raw_{name.lower()}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"✅ Saved raw {name} HTML to {filename} (Size: {len(html)} bytes)")
            # 처음 200자 미리보기
            print(f"Preview: {html[:200]}")
        else:
            print(f"❌ Failed to fetch {name} HTML")
    finally:
        session.close()

if __name__ == "__main__":
    save_raw_data("MEGABOX", MegaboxCollector)
    save_raw_data("CGV", CGVCollector)
