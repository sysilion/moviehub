from datetime import datetime
import random
import time
import json

import requests
from sqlalchemy.orm import Session
from src.database.models import Event, Inventory, InventoryHistory
from src.utils.logger import get_logger
from src.collectors.base import BaseCollector
from src.utils.notifier import notifier

logger = get_logger("LotteCollector")


class LotteCinemaCollector(BaseCollector):
    BASE_URL = "https://www.lottecinema.co.kr/LCWS/Event/EventData.aspx"
    HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundaryLotteCinema",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Origin": "https://www.lottecinema.co.kr",
        "Referer": "https://www.lottecinema.co.kr/NLCMW/Event",
    }

    KEYWORDS = ["증정", "뱃지", "아트카드", "artcard", "무비티켓", "키링"]
    EXCLUDE_KEYWORDS = ["콤보", "런칭"]

    def __init__(self, session: Session):
        self.session = session

    def _make_request(self, method_name, params):
        boundary = "----WebKitFormBoundaryLotteCinema"
        headers = self.HEADERS.copy()
        param_list_json = json.dumps(params)
        body = f'--{boundary}\r\nContent-Disposition: form-data; name="paramList"\r\n\r\n{param_list_json}\r\n--{boundary}--\r\n'
        try:
            response = requests.post(
                self.BASE_URL, headers=headers, data=body.encode("utf-8")
            )
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
            "PageNo": page,
            "PageSize": 100,
            "MemberNo": "0",
        }
        return self._make_request("GetEventLists", params)

    def fetch_event_detail(self, event_id):
        params = {
            "MethodName": "GetInfomationDeliveryEventDetail",
            "channelType": "MW",
            "osType": "W",
            "osVersion": "Mozilla/5.0",
            "EventID": str(event_id),
        }
        return self._make_request("GetInfomationDeliveryEventDetail", params)

    def fetch_inventory(self, event_id, gift_id):
        params = {
            "MethodName": "GetCinemaGoods",
            "channelType": "MW",
            "osType": "W",
            "osVersion": "Mozilla/5.0",
            "EventID": str(event_id),
            "GiftID": str(gift_id),
        }
        return self._make_request("GetCinemaGoods", params)

    def save_event(self, event_data, gift_id=None):
        event_id = event_data.get("EventID")
        if not event_id:
            return None
        event = self.session.query(Event).filter_by(EventID=event_id).first()
        if not event:
            event = Event(EventID=event_id, Operator="LOTTE")
            self.session.add(event)
        else:
            event.Operator = "LOTTE"

        if gift_id:
            event.GiftID = str(gift_id)
        
        def parse_date(date_str):
            if not date_str: return None
            # "2025.01.01" 또는 "2025-01-01" 형식 대응
            clean_date = str(date_str).replace(".", "-")[:10]
            try:
                if "-" in clean_date:
                    return datetime.strptime(clean_date, "%Y-%m-%d").date()
                else:
                    return datetime.strptime(clean_date, "%Y%m%d").date()
            except (ValueError, TypeError):
                return None

        event.EventName = event_data.get("EventName")
        
        new_start = parse_date(event_data.get("ProgressStartDate") or event_data.get("EventStartDate") or event_data.get("StartDate"))
        if new_start:
            event.ProgressStartDate = new_start
            
        new_end = parse_date(event_data.get("ProgressEndDate") or event_data.get("EventEndDate") or event_data.get("EndDate"))
        if new_end:
            event.ProgressEndDate = new_end
            
        event.ImageUrl = event_data.get("ListImgUrl") or event_data.get("ImageUrl") or event.ImageUrl
        event.DetailImageUrl = event_data.get("ImgUrl") or event_data.get("DetailImageUrl") or event.DetailImageUrl
        self.session.commit()
        return event

    def save_inventory(self, event_id, gift_id, inventory_data):
        if not inventory_data or "CinemaDivisionGoods" not in inventory_data:
            return
        items = inventory_data["CinemaDivisionGoods"]

        # 기존 지점별 재고 데이터 로드
        existing_records = {
            str(inv.CinemaID): inv
            for inv in self.session.query(Inventory)
            .filter_by(EventID=event_id, GiftID=gift_id)
            .all()
        }

        event = self.session.query(Event).filter_by(EventID=event_id).first()
        event_name = event.EventName if event else "알 수 없는 이벤트"

        count = 0
        now = datetime.now()
        for item in items:
            c_id = str(item.get("CinemaID"))
            new_count = item.get("Cnt")
            existing = existing_records.get(c_id)
            cinema_name = item.get("CinemaNameKR") or "알 수 없는 지점"

            # 조건: 기존 수량이 0이고 새로운 수량도 0이면 업데이트 건너뜀 (이미 소진된 지점)
            if existing and existing.ItemCount == 0 and new_count == 0:
                continue

            if not existing:
                # 신규 지점 정보 추가
                inv = Inventory(
                    EventID=event_id,
                    GiftID=gift_id,
                    CinemaID=c_id,
                    CinemaName=cinema_name,
                    DivisionName=item.get("DetailDivisionNameKR"),
                    ItemCount=new_count,
                    LastUpdated=now,
                )
                self.session.add(inv)
                if new_count > 0:
                    notifier.send_message(f"🆕 <b>신규 재고 발견!</b>\n{event_name}\n지점: {cinema_name}\n수량: {new_count}개")
                
                # 첫 기록은 이력에 저장
                history = InventoryHistory(
                    EventID=event_id,
                    GiftID=gift_id,
                    CinemaID=c_id,
                    CinemaName=cinema_name,
                    ItemCount=new_count,
                    RecordTime=now,
                )
                self.session.add(history)
            else:
                # 수량이 변동된 경우에만 이력 추가 및 정보 업데이트
                if existing.ItemCount != new_count:
                    # 알림 로직
                    if existing.ItemCount > 0 and new_count == 0:
                        notifier.send_message(f"🚨 <b>품절 발생!</b>\n{event_name}\n지점: {cinema_name}")
                    elif existing.ItemCount == 0 and new_count > 0:
                        notifier.send_message(f"✅ <b>재입고 알림!</b>\n{event_name}\n지점: {cinema_name}\n수량: {new_count}개")
                    
                    existing.ItemCount = new_count
                    existing.LastUpdated = now
                    history = InventoryHistory(
                        EventID=event_id,
                        GiftID=gift_id,
                        CinemaID=c_id,
                        CinemaName=cinema_name,
                        ItemCount=new_count,
                        RecordTime=now,
                    )
                    self.session.add(history)
                else:
                    # 수량이 그대로(0이 아님)라면 업데이트 시간만 갱신
                    existing.LastUpdated = now

            count += 1

        self.session.commit()
        logger.info(f"Updated {count} active inventory items for LOTTE : {event_name} ({event_id})")

    def collect_target_inventory(self, event_id, gift_id):
        detail = self.fetch_event_detail(event_id)
        if (
            detail
            and "InfomationDeliveryEventDetail" in detail
            and detail["InfomationDeliveryEventDetail"]
        ):
            self.save_event(detail["InfomationDeliveryEventDetail"][0], gift_id=gift_id)

        inv_data = self.fetch_inventory(event_id, gift_id)
        if inv_data and inv_data.get("CinemaDivisionGoods"):
            self.save_inventory(event_id, gift_id, inv_data)
            return True
        return False

    def get_latest_event_id(self, year_yy=None):
        prefix = f"2010100169{year_yy}" if year_yy else "2010100169"
        # 숫자로만 구성된 ID 중 가장 큰 것 찾기 (PostgreSQL regex)
        query = self.session.query(Event.EventID).filter(
            Event.EventID.like(f"{prefix}%"),
            Event.EventID.op("~")("^[0-9]+$")
        ).order_by(Event.EventID.desc())
        
        last_event = query.first()
        return last_event[0] if last_event else None

    def get_latest_gift_id(self):
        # 숫자로만 구성된 ID 중 가장 큰 것 찾기 (PostgreSQL regex)
        query = self.session.query(Event.GiftID).filter(
            Event.GiftID != None,
            Event.GiftID.op("~")("^[0-9]+$")
        ).order_by(Event.GiftID.desc())
        
        last_gift = query.first()
        return last_gift[0] if last_gift else None

    def get_gift_id_search_limit(self):
        latest_id = self.get_latest_gift_id()
        if latest_id and latest_id.isdigit():
            return int(latest_id) + 50
        return 14125  # Fallback default

    def discover_new_events(self):
        logger.info("Auto-discovery Part 1: Fetching current events from Lotte Cinema API...")
        found_total = 0
        for page in [1, 2, 3, 4, 5]:
            try:
                data = self.fetch_events(page=page)
                if data and "Items" in data:
                    for item in data["Items"]:
                        # 기존 여부와 상관없이 정보 갱신을 위해 save_event 호출
                        if self.save_event(item, gift_id=None):
                            found_total += 1
            except Exception as e:
                logger.error(f"Error processing event list on page {page}: {e}")

        now = datetime.now()
        current_year_yy = now.strftime("%y")
        logger.info(f"Auto-discovery Part 2: Starting incremental scanning for year {current_year_yy}...")

        last_event_id = self.get_latest_event_id(current_year_yy)
        if not last_event_id:
            start_event_num = int(f"2010100169{current_year_yy}001")
            logger.info(f"No events found for year {current_year_yy}. Starting from {start_event_num}")
        else:
            start_event_num = int(last_event_id) + 1

        last_gift_id = self.get_latest_gift_id()
        if not last_gift_id:
            last_gift_id = "13870"
        
        start_gift_num = int(last_gift_id)
        gift_limit = self.get_gift_id_search_limit()

        max_events_to_check = 20
        max_gifts_to_check = 50
        current_gift_cursor = start_gift_num

        for i in range(max_events_to_check):
            event_id = str(start_event_num + i)
            detail = self.fetch_event_detail(event_id)
            if not (detail and "InfomationDeliveryEventDetail" in detail and detail["InfomationDeliveryEventDetail"]):
                continue

            event_info = detail["InfomationDeliveryEventDetail"][0]
            self.save_event(event_info, gift_id=None)

            for j in range(max_gifts_to_check):
                gift_id = str(current_gift_cursor + j)
                if int(gift_id) > gift_limit: break
                
                inv = self.fetch_inventory(event_id, gift_id)
                if inv and inv.get("CinemaDivisionGoods"):
                    self.save_event(event_info, gift_id=gift_id)
                    self.save_inventory(event_id, gift_id, inv)
                    notifier.send_message(f"🎯 <b>새로운 굿즈 번호 매칭!</b>\n{event_info.get('EventName')}\nEvent: {event_id}, Gift: {gift_id}")
                    current_gift_cursor = int(gift_id)
                    found_total += 1
                    break
        
        return found_total
    def match_missing_gift_id(self, event_id):
        used_gift_ids = set()
        results = self.session.query(Event.GiftID).filter(Event.GiftID != None).all()
        for r in results:
            if r.GiftID and r.GiftID.isdigit(): used_gift_ids.add(int(r.GiftID))

        global_search_limit = self.get_gift_id_search_limit()
        try:
            target_event_num = int(event_id)
            neighbor_min, neighbor_max = target_event_num - 30, target_event_num + 30
            neighbors = self.session.query(Event.GiftID).filter(Event.EventID >= str(neighbor_min), Event.EventID <= str(neighbor_max), Event.GiftID != None).all()
            neighbor_gifts = [int(n.GiftID) for n in neighbors if n.GiftID and n.GiftID.isdigit()]

            if neighbor_gifts:
                search_start = min(neighbor_gifts)
                search_end = min(max(neighbor_gifts) + 50, global_search_limit)
            else:
                if not used_gift_ids: return False
                global_max = max(used_gift_ids)
                search_start, search_end = max(1, global_max - 200), global_search_limit
        except ValueError: return False

        candidates = [str(i) for i in range(search_start, search_end + 1) if i not in used_gift_ids]
        for gift_id in candidates:
            time.sleep(random.uniform(1, 3))
            try:
                inv = self.fetch_inventory(event_id, gift_id)
                if inv and inv.get("CinemaDivisionGoods"):
                    detail = self.fetch_event_detail(event_id)
                    if detail and "InfomationDeliveryEventDetail" in detail:
                        self.save_event(detail["InfomationDeliveryEventDetail"][0], gift_id=gift_id)
                    self.save_inventory(event_id, gift_id, inv)
                    notifier.send_message(f"🎯 <b>미할당 굿즈 번호 찾음!</b>\nEvent: {event_id} → Gift: {gift_id}")
                    return True
            except Exception: continue
        return False
