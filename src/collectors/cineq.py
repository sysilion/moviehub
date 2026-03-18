import requests
import json
from datetime import datetime
from sqlalchemy.orm import Session
from src.database.models import Event, Inventory
from src.utils.logger import get_logger
from src.collectors.base import BaseCollector
from src.utils.notifier import notifier

logger = get_logger("CineQCollector")

class CineQCollector(BaseCollector):
    # 발견된 API 주소
    BASE_URL = "https://www.cineq.co.kr/Event/MoreList"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.cineq.co.kr/Event/List"
    }

    def __init__(self, session: Session):
        super().__init__(session)

    def fetch_events(self, last_id="0"):
        # 씨네Q는 eventId=0으로 시작하여 더보기 방식으로 호출함
        payload = {
            "eventId": last_id,
            "eventSort": "-1" # 최신순
        }
        try:
            response = requests.post(self.BASE_URL, data=payload, headers=self.HEADERS)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"CineQ fetch failed: {e}")
            return None

    def fetch_event_detail(self, event_id):
        return None

    def fetch_inventory(self, event_id, gift_id):
        return None

    def save_event(self, event_data: dict, gift_id: str = None):
        # 씨네Q 데이터 구조: EventId, Title, ImgUrl, StartDate, EndDate 등
        event_id = str(event_data.get("EventId"))
        if not event_id: return None
        
        event = self.session.query(Event).filter_by(EventID=event_id).first()
        if not event:
            event = Event(EventID=event_id, Operator="CINEQ")
            self.session.add(event)
        else:
            event.Operator = "CINEQ"
        
        def parse_date(date_str):
            if not date_str: return None
            # "2025.01.01", "2025-01-01", "20250101" 형식 대응
            clean_date = str(date_str).replace(".", "-")[:10]
            try:
                if "-" in clean_date:
                    return datetime.strptime(clean_date, "%Y-%m-%d").date()
                else:
                    return datetime.strptime(clean_date, "%Y%m%d").date()
            except (ValueError, TypeError):
                return None

        event.EventName = event_data.get("Title")
        
        # Duration 필드에서 날짜 추출 (형식: "2026.02.04~2026.03.29")
        duration = event_data.get("Duration", "")
        if duration and "~" in duration:
            parts = duration.split("~")
            new_start = parse_date(parts[0].strip())
            if new_start:
                event.ProgressStartDate = new_start
            
            new_end = parse_date(parts[1].strip())
            if new_end:
                event.ProgressEndDate = new_end
        
        event.ImageUrl = event_data.get("Thumb", "") # CineQ는 Thumb 필드에 풀 경로가 포함됨
        
        self.session.commit()
        return event

    def collect_target_inventory(self, event_id: str, gift_id: str):
        return False

    def discover_new_events(self):
        logger.info("CineQ auto-discovery started...")
        found_total = 0
        last_id = "0"
        
        # 최대 3페이지까지 탐색
        for _ in range(3):
            data = self.fetch_events(last_id=last_id)
            if not data: break
            
            items = data if isinstance(data, list) else data.get("List", [])
            if not items: break
                
            for item in items:
                event_id = str(item.get("EventId"))
                if not event_id: continue
                
                if self.save_event(item):
                    found_total += 1
                last_id = event_id
                
        logger.info(f"CineQ discovery finished. Found {found_total} new/updated events.")
        return found_total
