import requests
import json
import re
from datetime import datetime
from sqlalchemy.orm import Session
from src.database.models import Event, Inventory, InventoryHistory
from src.utils.logger import get_logger
from src.collectors.base import BaseCollector
from src.utils.notifier import notifier

logger = get_logger("CineQCollector")

class CineQCollector(BaseCollector):
    BASE_URL = "https://api.cineq.co.kr/api/v1/Movie/GetEvent"
    
    HEADERS = {
        "accept": "*/*",
        "origin": "https://m.cineq.co.kr",
        "referer": "https://m.cineq.co.kr/",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36",
    }

    THEATER_MAP = {
        "1001": "신도림", "2102": "청라", "2002": "남양주다산",
        "4101": "천안불당", "5001": "전주영화의거리", "6001": "경주보문",
        "6002": "구미봉곡", "6003": "칠곡호이", "4002": "보은",
        "6005": "영덕예주", "1000": "씨네Q(공통)"
    }

    def __init__(self, session: Session):
        super().__init__(session)

    def fetch_events(self):
        try:
            response = requests.get(self.BASE_URL, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"CineQ API fetch failed: {e}")
            return None

    def fetch_event_detail(self, event_id):
        return None

    def fetch_inventory(self, event_id, gift_id=None):
        return None

    def _normalize_title(self, title):
        if not title: return ""
        # 영화 제목 추출 (예: <메소드 연기> -> 메소드연기)
        match = re.search(r'<(.*?)>', title)
        if match:
            title = match.group(1)
        return re.sub(r'[^가-힣a-zA-Z0-9]', '', title)

    def discover_new_events(self):
        logger.info("CineQ Smart-Mapping discovery started...")
        raw_data = self.fetch_events()
        if not raw_data or "data" not in raw_data: return 0
        
        items = raw_data["data"]
        base_events = [item for item in items if item.get("eventType") == 1]
        stock_items = [item for item in items if item.get("eventType") == 2]
        
        found_count = 0
        
        # 1. 메인 이벤트(Type 1) 저장
        event_map = {} # 제목(정규화) -> Event 객체
        for item in base_events:
            event = self.save_event(item)
            if event:
                norm_title = self._normalize_title(event.EventName)
                event_map[norm_title] = event
                found_count += 1
                
        # 2. 굿즈 재고(Type 2) 매핑 및 저장
        for s_item in stock_items:
            s_title = s_item.get("eventTitle")
            norm_s_title = self._normalize_title(s_title)
            
            # 메인 이벤트 찾기
            target_event = None
            for base_norm, base_evt in event_map.items():
                if norm_s_title in base_norm or base_norm in norm_s_title:
                    target_event = base_evt
                    break
            
            # 매핑된 이벤트가 없으면 스스로를 이벤트로 저장
            if not target_event:
                target_event = self.save_event(s_item)
                if target_event:
                    found_count += 1
            
            if target_event:
                self.save_inventory(target_event.EventID, s_item)
                
        return found_count

    def save_event(self, item):
        e_id = str(item.get("eventId"))
        event = self.session.query(Event).filter_by(EventID=e_id).first()
        if not event:
            event = Event(EventID=e_id, Operator="CINEQ")
            self.session.add(event)
        
        event.EventName = item.get("eventTitle")
        event.ImageUrl = item.get("thumbnail") or event.ImageUrl
        event.DetailImageUrl = item.get("contents")
        
        def parse_date(date_str):
            if not date_str: return None
            try: return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
            except: return None

        event.ProgressStartDate = parse_date(item.get("startDate"))
        event.ProgressEndDate = parse_date(item.get("endDate"))
        
        # 타입 정보
        t_code = item.get("eventType")
        event.EventTypeCode = str(t_code)
        event.EventTypeName = "굿즈증정" if t_code == 2 else "이벤트"
        
        self.session.commit()
        return event

    def save_inventory(self, base_event_id, s_item):
        # s_item은 실제 재고 정보를 가진 Type 2 아이템
        gift_id = str(s_item.get("eventId")) # 굿즈별 고유 ID
        t_code = str(s_item.get("theaterCode"))
        cinema_name = self.THEATER_MAP.get(t_code, f"알 수 없는 지점({t_code})")
        
        # 씨네큐의 maxCount는 현재 잔여 수량으로 판단됨 (issueCount는 총 수량)
        current_stock = int(s_item.get("maxCount") or 0)
        now = datetime.now()

        # 재고 정보 업데이트 (EventID + GiftID + CinemaID 기준)
        existing = self.session.query(Inventory).filter_by(
            EventID=base_event_id, GiftID=gift_id, CinemaID=t_code
        ).first()

        if not existing:
            inv = Inventory(
                EventID=base_event_id, GiftID=gift_id, CinemaID=t_code,
                CinemaName=cinema_name, DivisionName="전체",
                ItemCount=current_stock, LastUpdated=now
            )
            self.session.add(inv)
        else:
            if existing.ItemCount != current_stock:
                existing.ItemCount = current_stock
                existing.LastUpdated = now

        # 이력 저장
        self.session.add(InventoryHistory(
            EventID=base_event_id, GiftID=gift_id, CinemaID=t_code,
            CinemaName=cinema_name, ItemCount=current_stock, RecordTime=now
        ))
        self.session.commit()

    def collect_target_inventory(self, event_id: str, gift_id: str = "0"):
        # 씨네큐는 discover_new_events에서 모든 재고를 한꺼번에 처리함
        return self.discover_new_events() > 0
