import sys
import os
import requests

# 루트 경로 추가
sys.path.append(os.getcwd())

from src.database.models import get_session
from src.collectors.cgv import CGVCollector

def check_cgv():
    session = get_session()
    collector = CGVCollector(session)
    html = collector.fetch_events()
    if html:
        with open("raw_cgv_desktop.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved CGV Desktop HTML. Size: {len(html)}")
        # 처음 1000자에서 링크 패턴 확인
        import re
        links = re.findall(r'href="/culture/event/detail-view\.aspx\?idx=(\d+)"', html)
        print(f"Found idx links: {links[:10]}")
    session.close()

if __name__ == "__main__":
    check_cgv()
