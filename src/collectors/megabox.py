import requests
import re
from datetime import datetime
from sqlalchemy.orm import Session
from src.database.models import Event, Inventory
from src.utils.logger import get_logger
from src.collectors.base import BaseCollector
from src.utils.notifier import notifier

logger = get_logger("MegaboxCollector")

class MegaboxCollector(BaseCollector):
    # 이벤트 목록 페이지 (AJAX 호출 결과가 HTML 조각임)
    BASE_URL = "https://www.megabox.co.kr/on/oh/ohe/Event/eventMngDiv.do"
    
    HEADERS = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.megabox.co.kr/event"
    }
    
    KEYWORDS = ["오리지널", "티켓", "굿즈", "증정", "돌비", "포스터"]

    def __init__(self, session: Session):
        super().__init__(session)

    def fetch_events(self, page=1):
        payload = {
            "currentPage": str(page),
            "recordCountPerPage": "100",
            "eventStatCd": "ONG",
            "orderReqCd": "ONGlist"
        }
        try:
            response = requests.post(self.BASE_URL, data=payload, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Megabox fetch failed: {e}")
            return None

    def fetch_event_detail(self, event_id):
        return None

    def fetch_inventory(self, event_id, gift_id):
        return None

    def save_event(self, event_data: dict, gift_id: str = None):
        event_id = str(event_data.get("EventID"))
        if not event_id: return None
        
        event = self.session.query(Event).filter_by(EventID=event_id).first()
        if not event:
            event = Event(EventID=event_id, Operator="MEGABOX")
            self.session.add(event)
        else:
            event.Operator = "MEGABOX"
        
        def parse_date(date_str):
            if not date_str: return None
            # "2025.01.01" 또는 "2025-01-01" 형식 대응
            clean_date = date_str.replace(".", "-")[:10]
            try:
                return datetime.strptime(clean_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return None

        event.EventName = event_data.get("EventName")
        event.ImageUrl = event_data.get("ImageUrl")
        event.ProgressStartDate = parse_date(event_data.get("StartDate"))
        event.ProgressEndDate = parse_date(event_data.get("EndDate"))
        
        self.session.commit()
        return event

    def collect_target_inventory(self, event_id: str, gift_id: str):
        return False

    def discover_new_events(self):
        logger.info("Megabox auto-discovery (HTML Fragment Parsing) started...")
        html = self.fetch_events()
        if not html: return 0
        
        # 메가박스 HTML에서 data-no와 tit을 추출하는 가장 단순한 패턴
        # data-no="(\d+)" ... <p class="tit">(.*?)</p>
        import re
        import html as html_lib
        
        # 1. 개별 리스트 아이템 분리 (<li> 단위)
        items_raw = re.findall(r'<li[^>]*>(.*?)</li>', html, re.DOTALL)
        
        found = 0
        for item_html in items_raw:
            # 2. data-no 추출
            no_match = re.search(r'data-no="(\d+)"', item_html)
            # 3. 제목 추출
            tit_match = re.search(r'<p\s+class="tit"[^>]*>(.*?)</p>', item_html, re.DOTALL)
            # 4. 이미지 추출
            img_match = re.search(r'<img\s+src="([^"]+)"', item_html)
            # 5. 날짜 추출
            date_match = re.search(r'<p\s+class="date">([\d\.]+)\s*~\s*([\d\.]+)</p>', item_html)
            
            if no_match and tit_match:
                event_id = no_match.group(1)
                event = self.session.query(Event).filter_by(EventID=event_id).first()
                
                if not event:
                    title = html_lib.unescape(tit_match.group(1).strip())
                    img = img_match.group(1) if img_match else ""
                    start = date_match.group(1).replace(".", "-") if date_match else ""
                    end = date_match.group(2).replace(".", "-") if date_match else ""
                    
                    data = {
                        "EventID": event_id,
                        "EventName": title,
                        "ImageUrl": img if img.startswith("http") else "https://img.megabox.co.kr" + img,
                        "StartDate": start,
                        "EndDate": end
                    }
                    self.save_event(data)
                    found += 1
                
        logger.info(f"Megabox discovery finished. Found {found} new events.")
        return found
