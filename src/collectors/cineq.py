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

    def fetch_events(self, page=1):
        # 씨네Q는 eventId=0으로 시작하여 더보기 방식으로 호출함
        payload = {
            "eventId": "0",
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
        
        event.EventName = event_data.get("Title")
        event.ProgressStartDate = event_data.get("StartDate", "").replace(".", "-")
        event.ProgressEndDate = event_data.get("EndDate", "").replace(".", "-")
        event.ImageUrl = "https://www.cineq.co.kr" + event_data.get("ImgUrl", "")
        
        self.session.commit()
        return event

    def collect_target_inventory(self, event_id: str, gift_id: str):
        return False

    def discover_new_events(self):
        logger.info("CineQ auto-discovery started...")
        data = self.fetch_events()
        if not data: return 0
        
        # 씨네Q 응답은 리스트 형태이거나 'List' 필드에 담겨올 수 있음
        items = data if isinstance(data, list) else data.get("List", [])
        if not items:
            logger.info("CineQ no events found.")
            return 0
            
        found = 0
        for item in items:
            event_id = str(item.get("EventId"))
            if not event_id: continue
            
            event = self.session.query(Event).filter_by(EventID=event_id).first()
            if not event:
                self.save_event(item)
                found += 1
        logger.info(f"CineQ discovery finished. Found {found} new events.")
        return found
