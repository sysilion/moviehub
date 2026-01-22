import requests
import json
import time
import random
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

    def get_latest_event_id(self):
        last_event = self.session.query(Event.EventID).order_by(Event.EventID.desc()).first()
        return last_event[0] if last_event else None

    def get_latest_gift_id(self):
        last_gift = self.session.query(Event.GiftID).filter(Event.GiftID != None).order_by(Event.GiftID.desc()).first()
        return last_gift[0] if last_gift else None

    def discover_new_events(self):
        """
        Automatically discovers new events by incrementing from the last known EventID and GiftID.
        """
        last_event_id = self.get_latest_event_id()
        last_gift_id = self.get_latest_gift_id()

        if not last_event_id or not last_gift_id:
            logger.warning("No existing events or gifts found to increment from.")
            return

        start_event_num = int(last_event_id) + 1
        start_gift_num = int(last_gift_id)
        
        # Define search bounds
        max_events_to_check = 20
        max_gifts_to_check = 50 
        
        logger.info(f"Auto-discovery started. Base Event: {last_event_id}, Base Gift: {last_gift_id}")

        current_gift_cursor = start_gift_num
        found_new = 0

        for i in range(max_events_to_check):
            event_num = start_event_num + i
            event_id = str(event_num)
            
            try:
                detail = self.fetch_event_detail(event_id)
            except Exception:
                continue

            if not (detail and 'InfomationDeliveryEventDetail' in detail and detail['InfomationDeliveryEventDetail']):
                continue
                
            event_info = detail['InfomationDeliveryEventDetail'][0]
            self.save_event(event_info, gift_id=None)
            logger.info(f"Discovered potential event: {event_id} - {event_info.get('EventName')}")

            matched = False
            # Check a range of gifts starting from current cursor
            for j in range(max_gifts_to_check):
                gift_num = current_gift_cursor + j
                gift_id = str(gift_num)
                inv = self.fetch_inventory(event_id, gift_id)
                if inv and inv.get('CinemaDivisionGoods'):
                    logger.info(f"  -> MATCH: Gift {gift_id} for Event {event_id}")
                    self.save_event(event_info, gift_id=gift_id)
                    self.save_inventory(event_id, gift_id, inv)
                    
                    current_gift_cursor = gift_num
                    found_new += 1
                    matched = True
                    break 
            
        logger.info(f"Auto-discovery finished. Found {found_new} new items.")

    def match_missing_gift_id(self, event_id):
        """
        Scans for a valid GiftID for the given event_id by checking ranges determined from neighboring events.
        Range logic: Neighbors (EventID ± 30) -> Min GiftID to Max GiftID + 50.
        Excludes already registered GiftIDs.
        Delays 1~3s between requests.
        """
        # 1. Get all used GiftIDs (global exclusion list)
        used_gift_ids = set()
        results = self.session.query(Event.GiftID).filter(Event.GiftID != None).all()
        for r in results:
            if r.GiftID and r.GiftID.isdigit():
                used_gift_ids.add(int(r.GiftID))
        
        # 2. Determine search range from neighbors
        try:
            target_event_num = int(event_id)
            neighbor_min = target_event_num - 30
            neighbor_max = target_event_num + 30
            
            # Find neighbors with valid GiftIDs
            neighbors = self.session.query(Event.GiftID).filter(
                Event.EventID >= str(neighbor_min),
                Event.EventID <= str(neighbor_max),
                Event.GiftID != None
            ).all()
            
            neighbor_gifts = []
            for n in neighbors:
                if n.GiftID and n.GiftID.isdigit():
                    neighbor_gifts.append(int(n.GiftID))
            
            if neighbor_gifts:
                search_start = min(neighbor_gifts)
                search_end = max(neighbor_gifts) + 50
                logger.info(f"Search range determined from {len(neighbor_gifts)} neighbors: {search_start} ~ {search_end}")
            else:
                # Fallback if no neighbors found
                logger.warning(f"No neighbors found for Event {event_id}. Using global max fallback.")
                if not used_gift_ids:
                    return False
                global_max = max(used_gift_ids)
                search_start = max(1, global_max - 200)
                search_end = global_max + 50
        except ValueError:
             logger.error(f"Invalid EventID format: {event_id}")
             return False

        # 3. Generate candidates (excluding used ones)
        candidates = []
        for i in range(search_start, search_end + 1):
            if i not in used_gift_ids:
                candidates.append(str(i))
        
        logger.info(f"Scanning {len(candidates)} candidate GiftIDs for Event {event_id}...")
        
        # 4. Iterate and check
        for gift_id in candidates:
            # Random delay 1~3s
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            try:
                inv = self.fetch_inventory(event_id, gift_id)
                if inv and inv.get('CinemaDivisionGoods'):
                    logger.info(f"MATCH FOUND! Event {event_id} mapped to GiftID {gift_id}")
                    
                    # Update DB
                    detail = self.fetch_event_detail(event_id)
                    if detail and 'InfomationDeliveryEventDetail' in detail:
                        self.save_event(detail['InfomationDeliveryEventDetail'][0], gift_id=gift_id)
                    
                    self.save_inventory(event_id, gift_id, inv)
                    return True
            except Exception as e:
                logger.error(f"Error checking gift {gift_id}: {e}")
                continue
                
        logger.info(f"No matching GiftID found for Event {event_id} after scanning.")
        return False

    def process_events(self):
        # (생략: 기존 탐색 로직 동일)
        pass
