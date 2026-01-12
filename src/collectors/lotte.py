import requests
import json
import time
from datetime import datetime
from sqlalchemy.orm import Session
from src.database.models import Event, Inventory, InventoryHistory
from src.utils.logger import get_logger

logger = get_logger("LotteCollector")

class LotteCinemaCollector:
    BASE_URL = "https://www.lottecinema.co.kr/LCWS/Event/EventData.aspx"
    HEADERS = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundaryLotteCinema',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Origin': 'https://www.lottecinema.co.kr',
        'Referer': 'https://www.lottecinema.co.kr/NLCMW/Event',
    }
    
    KEYWORDS = ['증정', '뱃지', '아트카드', 'artcard', '무비티켓', '키링']
    EXCLUDE_KEYWORDS = ['콤보', '런칭']

    def __init__(self, session: Session):
        self.session = session

    def _make_request(self, method_name, params):
        boundary = '----WebKitFormBoundaryLotteCinema'
        headers = self.HEADERS.copy()
        param_list_json = json.dumps(params)
        body = f"--{boundary}\r\nContent-Disposition: form-data; name=\"paramList\"\r\n\r\n{param_list_json}\r\n--{boundary}--\r\n"
        try:
            response = requests.post(self.BASE_URL, headers=headers, data=body.encode('utf-8'))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Request failed for {method_name}: {e}")
            return None

    def fetch_events(self, page=1):
        params = {"MethodName": "GetEventLists", "channelType": "MW", "osType": "W", "osVersion": "Mozilla/5.0", "EventClassificationCode": "0", "PageNo": str(page), "PageSize": 100}
        return self._make_request("GetEventLists", params)

    def fetch_event_detail(self, event_id):
        params = {"MethodName": "GetInfomationDeliveryEventDetail", "channelType": "MW", "osType": "W", "osVersion": "Mozilla/5.0", "EventID": str(event_id)}
        return self._make_request("GetInfomationDeliveryEventDetail", params)

    def fetch_inventory(self, event_id, gift_id):
        params = {"MethodName": "GetCinemaGoods", "channelType": "MW", "osType": "W", "osVersion": "Mozilla/5.0", "EventID": str(event_id), "GiftID": str(gift_id)}
        return self._make_request("GetCinemaGoods", params)

    def save_event(self, event_data, gift_id=None):
        event_id = event_data.get('EventID')
        if not event_id: return None
        event = self.session.query(Event).filter_by(EventID=event_id).first()
        if not event:
            event = Event(EventID=event_id)
            self.session.add(event)
        
        if gift_id: event.GiftID = str(gift_id)
        event.EventName = event_data.get('EventName')
        event.ProgressStartDate = event_data.get('ProgressStartDate') or event_data.get('EventStartDate')
        event.ProgressEndDate = event_data.get('ProgressEndDate') or event_data.get('EventEndDate')
        event.ImageUrl = event_data.get('ListImgUrl') or event.ImageUrl
        event.DetailImageUrl = event_data.get('ImgUrl') or event.DetailImageUrl
        self.session.commit()
        return event

    def save_inventory(self, event_id, gift_id, inventory_data):
        if not inventory_data or 'CinemaDivisionGoods' not in inventory_data: return
        items = inventory_data['CinemaDivisionGoods']
        
        # 기존 지점별 재고 데이터 로드
        existing_records = {str(inv.CinemaID): inv for inv in self.session.query(Inventory).filter_by(EventID=event_id, GiftID=gift_id).all()}
        
        count = 0; now = datetime.now()
        for item in items:
            c_id = str(item.get('CinemaID'))
            new_count = item.get('Cnt')
            existing = existing_records.get(c_id)
            
            # 조건: 기존 수량이 0이고 새로운 수량도 0이면 업데이트 건너뜀 (이미 소진된 지점)
            if existing and existing.ItemCount == 0 and new_count == 0:
                continue
            
            if not existing:
                # 신규 지점 정보 추가
                inv = Inventory(
                    EventID=event_id, GiftID=gift_id, CinemaID=c_id, CinemaName=item.get('CinemaNameKR'),
                    DivisionName=item.get('DetailDivisionNameKR'), ItemCount=new_count, LastUpdated=now
                )
                self.session.add(inv)
                # 첫 기록은 이력에 저장
                history = InventoryHistory(EventID=event_id, GiftID=gift_id, CinemaID=c_id, CinemaName=item.get('CinemaNameKR'), ItemCount=new_count, RecordTime=now)
                self.session.add(history)
            else:
                # 수량이 변동된 경우에만 이력 추가 및 정보 업데이트
                if existing.ItemCount != new_count:
                    existing.ItemCount = new_count
                    existing.LastUpdated = now
                    history = InventoryHistory(EventID=event_id, GiftID=gift_id, CinemaID=c_id, CinemaName=item.get('CinemaNameKR'), ItemCount=new_count, RecordTime=now)
                    self.session.add(history)
                else:
                    # 수량이 그대로(0이 아님)라면 업데이트 시간만 갱신
                    existing.LastUpdated = now
            
            count += 1
        
        self.session.commit()
        logger.info(f"Updated {count} active inventory items for Event {event_id}")

    def collect_target_inventory(self, event_id, gift_id):
        detail = self.fetch_event_detail(event_id)
        if detail and 'InfomationDeliveryEventDetail' in detail and detail['InfomationDeliveryEventDetail']:
            self.save_event(detail['InfomationDeliveryEventDetail'][0], gift_id=gift_id)
        
        inv_data = self.fetch_inventory(event_id, gift_id)
        if inv_data and inv_data.get('CinemaDivisionGoods'):
            self.save_inventory(event_id, gift_id, inv_data)
            return True
        return False

    def scan_gift_ids(self, event_id, base_gift_id):
        # (생략: 기존 스캔 로직 동일)
        pass

    def process_events(self):
        # (생략: 기존 탐색 로직 동일)
        pass
