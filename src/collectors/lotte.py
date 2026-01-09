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
            "PageSize": 100,
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
        old_counts = {inv.CinemaID: inv.ItemCount for inv in self.session.query(Inventory).filter_by(EventID=event_id, GiftID=gift_id).all()}
        
        self.session.query(Inventory).filter_by(EventID=event_id, GiftID=gift_id).delete() 
        
        count = 0
        now = datetime.now()
        for item in items:
            c_id = item.get('CinemaID')
            new_count = item.get('Cnt')
            
            inv = Inventory(
                EventID=event_id,
                GiftID=gift_id,
                CinemaID=c_id,
                CinemaName=item.get('CinemaNameKR'),
                DivisionCode=str(item.get('DivisionCode')),
                DetailDivisionCode=item.get('DetailDivisionCode'),
                ItemCount=new_count,
                LastUpdated=now
            )
            self.session.add(inv)
            
            if c_id not in old_counts or old_counts[c_id] != new_count:
                history = InventoryHistory(
                    EventID=event_id,
                    GiftID=gift_id,
                    CinemaID=c_id,
                    CinemaName=item.get('CinemaNameKR'),
                    ItemCount=new_count,
                    RecordTime=now
                )
                self.session.add(history)
            count += 1
        
        self.session.commit()
        logger.info(f"Saved {count} inventory items for Event {event_id}, Gift {gift_id}")

    def scan_gift_ids(self, event_id, base_gift_id, scan_range_plus=30, scan_range_minus=5):
        """GiftID 정방향 스캔 (최대 +30)"""
        try:
            base_id = int(base_gift_id)
        except (ValueError, TypeError):
            base_id = 13600

        used_gift_ids = {item[0] for item in self.session.query(Inventory.GiftID).filter(Inventory.EventID != event_id).distinct().all()}
        
        # 정방향 스캔 범위: -5 ~ +30
        search_range = range(base_id - scan_range_minus, base_id + scan_range_plus + 1)
        
        for g_id in search_range:
            current_gift_id = str(g_id)
            if current_gift_id in used_gift_ids: continue
            
            logger.info(f"Scanning GiftID {current_gift_id} (Forward) for Event {event_id}...")
            inv_data = self.fetch_inventory(event_id, current_gift_id)
            if inv_data and inv_data.get('CinemaDivisionGoods'):
                logger.info(f"SUCCESS: Found GiftID {current_gift_id} for Event {event_id}")
                self.save_inventory(event_id, current_gift_id, inv_data)
                return current_gift_id
            time.sleep(0.3)
        return None

    def collect_target_inventory(self, event_id, gift_id):
        """특정 타겟 재고 수집"""
        logger.info(f"Updating inventory for Event:{event_id}, Gift:{gift_id}")
        inv_data = self.fetch_inventory(event_id, gift_id)
        if inv_data and inv_data.get('CinemaDivisionGoods'):
            self.save_inventory(event_id, gift_id, inv_data)
            return True
        return False

    def estimate_gift_id(self, target_event_id):
        try:
            target_id = int(target_event_id)
            known_items = self.session.query(Inventory.EventID, Inventory.GiftID).distinct().all()
            DEFAULT_GIFT_ID = 13687
            if not known_items: return str(DEFAULT_GIFT_ID)
            best_match = None
            min_diff = float('inf')
            for evt_id, gift_id in known_items:
                try:
                    curr_evt_id = int(evt_id); curr_gift_id = int(gift_id)
                    diff = abs(target_id - curr_evt_id)
                    if diff < min_diff:
                        min_diff = diff; best_match = (curr_evt_id, curr_gift_id)
                except ValueError: continue
            if best_match:
                ref_evt_id, ref_gift_id = best_match
                id_diff = target_id - ref_evt_id
                if abs(id_diff) > 1000000: return str(ref_gift_id)
                estimated = ref_gift_id + id_diff
                return str(max(1000, estimated))
            return str(DEFAULT_GIFT_ID)
        except Exception: return "13687"

    def process_events(self):
        """정방향 이벤트 탐색 (EventID > 201010016925852)"""
        logger.info("Starting Forward event processing...")
        
        priority_id = "201010016925852"
        priority_id_int = int(priority_id)
        
        response = self.fetch_events(1)
        if not response or 'Items' not in response: return
        items = response['Items']

        candidates = []
        for item in items:
            try:
                event_id_int = int(item.get('EventID', 0))
                event_name = item.get('EventName', '')
                is_target = any(keyword in event_name for keyword in self.KEYWORDS)
                is_excluded = any(ex in event_name for ex in self.EXCLUDE_KEYWORDS)
                
                if event_id_int > priority_id_int and is_target and not is_excluded:
                    candidates.append(item)
            except (ValueError, TypeError): continue
        
        candidates.sort(key=lambda x: int(x.get('EventID', 0)))
        logger.info(f"Filtered {len(candidates)} new candidate events.")

        for item in candidates:
            event = self.save_event(item)
            if not event: continue

            exists = self.session.query(Inventory).filter_by(EventID=event.EventID).first()
            if not exists:
                est = self.estimate_gift_id(event.EventID)
                logger.info(f"Processing new event: {event.EventName} ({event.EventID}). Search Start: {est}")
                self.scan_gift_ids(event.EventID, est)
        
        logger.info("Forward processing complete.")
