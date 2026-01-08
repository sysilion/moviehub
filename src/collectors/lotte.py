import requests
import json
import time
from datetime import datetime
from sqlalchemy.orm import Session
from src.database.models import Event, Inventory
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

    def __init__(self, session: Session):
        self.session = session

    def _make_request(self, method_name, params):
        boundary = '----WebKitFormBoundaryLotteCinema'
        headers = self.HEADERS.copy()
        
        param_list_json = json.dumps(params)
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="paramList"\r\n\r\n'
            f"{param_list_json}\r\n"
            f"--{boundary}--\r\n"
        )
        
        try:
            response = requests.post(self.BASE_URL, headers=headers, data=body.encode('utf-8'))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Request failed for {method_name}: {e}")
            return None

    def fetch_events(self, page=1):
        params = {
            "MethodName": "GetEventLists",
            "channelType": "MW",
            "osType": "W",
            "osVersion": "Mozilla/5.0",
            "EventClassificationCode": "0",
            "SearchText": "",
            "CinemaID": "",
            "PageNo": str(page),
            "PageSize": 40,
            "MemberNo": "0"
        }
        return self._make_request("GetEventLists", params)

    def fetch_event_detail(self, event_id):
        params = {
            "MethodName": "GetInfomationDeliveryEventDetail",
            "channelType": "MW",
            "osType": "W",
            "osVersion": "Mozilla/5.0",
            "EventID": str(event_id)
        }
        return self._make_request("GetInfomationDeliveryEventDetail", params)

    def fetch_inventory(self, event_id, gift_id):
        params = {
            "MethodName": "GetCinemaGoods",
            "channelType": "MW",
            "osType": "W",
            "osVersion": "Mozilla/5.0",
            "EventID": str(event_id),
            "GiftID": str(gift_id)
        }
        return self._make_request("GetCinemaGoods", params)

    def save_event(self, event_data):
        event_id = event_data.get('EventID')
        if not event_id:
            return None

        event = self.session.query(Event).filter_by(EventID=event_id).first()
        if not event:
            event = Event(EventID=event_id)
            self.session.add(event)
        
        event.EventName = event_data.get('EventName')
        event.EventClassificationCode = event_data.get('EventClassificationCode')
        event.EventTypeCode = event_data.get('EventTypeCode')
        event.EventTypeName = event_data.get('EventTypeName')
        event.ProgressStartDate = event_data.get('ProgressStartDate')
        event.ProgressEndDate = event_data.get('ProgressEndDate')
        event.ImageUrl = event_data.get('ImageUrl')
        event.RawData = json.dumps(event_data)
        
        self.session.commit()
        return event

    def save_inventory(self, event_id, gift_id, inventory_data):
        if not inventory_data or 'CinemaDivisionGoods' not in inventory_data:
            return

        items = inventory_data['CinemaDivisionGoods']
        self.session.query(Inventory).filter_by(EventID=event_id, GiftID=gift_id).delete()
        
        count = 0
        for item in items:
            inv = Inventory(
                EventID=event_id,
                GiftID=gift_id,
                CinemaID=item.get('CinemaID'),
                CinemaName=item.get('CinemaNameKR'),
                DivisionCode=str(item.get('DivisionCode')),
                DetailDivisionCode=item.get('DetailDivisionCode'),
                ItemCount=item.get('Cnt'),
                LastUpdated=datetime.now()
            )
            self.session.add(inv)
            count += 1
        
        self.session.commit()
        logger.info(f"Saved {count} inventory items for Event {event_id}, Gift {gift_id}")

    def scan_gift_ids(self, event_id, base_gift_id):
        """
        GiftID 주변부를 스캔하여 유효한 데이터를 찾습니다.
        """
        try:
            base_id = int(base_gift_id)
        except ValueError:
            logger.error(f"Invalid base_gift_id for scan: {base_gift_id}")
            return None

        search_range = range(base_id - 5, base_id + 11)
        
        for g_id in search_range:
            current_gift_id = str(g_id)
            logger.info(f"Scanning GiftID {current_gift_id} for Event {event_id}...")
            inv_data = self.fetch_inventory(event_id, current_gift_id)
            
            if inv_data and inv_data.get('CinemaDivisionGoods'):
                logger.info(f"Found valid GiftID {current_gift_id} for Event {event_id}!")
                self.save_inventory(event_id, current_gift_id, inv_data)
                return current_gift_id
            
            time.sleep(0.5) 
        return None

    def collect_target_inventory(self, event_id, gift_id):
        """특정 이벤트와 굿즈 ID에 대해 수량을 수집합니다."""
        logger.info(f"Collecting inventory for Event:{event_id}, Gift:{gift_id}")
        
        if not self.session.query(Event).filter_by(EventID=event_id).first():
            detail = self.fetch_event_detail(event_id)
            if detail and 'InfomationDeliveryEventDetail' in detail and detail['InfomationDeliveryEventDetail']:
                d_item = detail['InfomationDeliveryEventDetail'][0]
                mapped_item = {
                    "EventID": d_item.get("EventID"),
                    "EventName": d_item.get("EventName"),
                    "EventClassificationCode": d_item.get("EventClassificationCode"),
                    "ProgressStartDate": d_item.get("ProgressStartDate"),
                    "ProgressEndDate": d_item.get("ProgressEndDate"),
                    "ImageUrl": d_item.get("ImgUrl") 
                }
                self.save_event(mapped_item)
        
        inv_data = self.fetch_inventory(event_id, gift_id)
        
        if not inv_data or not inv_data.get('CinemaDivisionGoods'):
            logger.warning(f"No data for GiftID {gift_id}. Starting scan...")
            return self.scan_gift_ids(event_id, gift_id)
        
        self.save_inventory(event_id, gift_id, inv_data)
        return gift_id

    def process_events(self):
        logger.info("Starting event processing...")
        response = self.fetch_events(1)
        if not response or 'Items' not in response:
            logger.error("Failed to fetch event list.")
            return

        items = response['Items']
        logger.info(f"Fetched {len(items)} events.")

        for item in items:
            event = self.save_event(item)
            if not event:
                continue

            if any(keyword in event.EventName for keyword in self.KEYWORDS):
                pass
                
        logger.info("Event processing complete.")