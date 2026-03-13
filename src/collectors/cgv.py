import requests
import hmac
import hashlib
import base64
import time
from datetime import datetime
from sqlalchemy.orm import Session
from src.database.models import Event, Inventory, InventoryHistory
from src.utils.logger import get_logger
from src.collectors.base import BaseCollector
from src.utils.notifier import notifier

logger = get_logger("CGVCollector")

class CGVCollector(BaseCollector):
    # 일반 이벤트 API
    BASE_URL = "https://event-mobile.cgv.co.kr/evt/evt/evt/searchEvtListForPage"
    # SAPRM (굿즈 재고 전용) API
    SAPRM_URL = "https://event-mobile.cgv.co.kr/evt/saprm/saprm"
    
    SIGNATURE_SECRET = "ydqXY0ocnFLmJGHr_zNzFcpjwAsXq_8JcBNURAkRscg"
    
    HEADERS_TEMPLATE = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json",
        "Origin": "https://cgv.co.kr",
        "Referer": "https://cgv.co.kr/",
    }

    def __init__(self, session: Session):
        super().__init__(session)

    def _generate_signature(self, path, body, timestamp):
        """HMAC SHA256 서명 생성"""
        payload = f"{timestamp}|{path}|{body}"
        signature = hmac.new(
            self.SIGNATURE_SECRET.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')

    def _signed_request(self, full_url, params=None):
        """서명된 GET 요청 수행"""
        # 경로 추출 (https://...co.kr 제외, 쿼리 제외)
        path = full_url.replace("https://event-mobile.cgv.co.kr", "").split("?")[0]
        ts = str(int(time.time()))
        sig = self._generate_signature(path, "", ts)
        
        headers = self.HEADERS_TEMPLATE.copy()
        headers.update({
            "X-TIMESTAMP": ts,
            "X-SIGNATURE": sig
        })
        
        response = requests.get(full_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def fetch_events(self, page=1):
        """일반 이벤트 목록 조회"""
        url = f"{self.BASE_URL}?coCd=A420&expoChnlCd=03&startRow=0&listCount=1000"
        return self._signed_request(url)

    def fetch_special_events(self):
        """굿즈 전용(SAPRM) 이벤트 목록 조회"""
        url = f"{self.SAPRM_URL}/searchSaprmEvtListForPage?coCd=A420&expoChnlCd=03&startRow=0&listCount=100"
        return self._signed_request(url)

    def fetch_goods_id(self, event_id):
        """이벤트 번호로 굿즈 ID(spmtlNo) 조회"""
        url = f"{self.SAPRM_URL}/searchSaprmEvtProdList?coCd=A420&expoChnlCd=03&saprmEvntNo={event_id}"
        data = self._signed_request(url)
        if data and "data" in data and len(data["data"]) > 0:
            return data["data"][0].get("spmtlNo"), data["data"][0].get("onlnExpoNm")
        return None, None

    def fetch_event_detail(self, event_id):
        """이벤트 상세 정보 조회 (SAPRM 기준)"""
        url = f"https://event-mobile.cgv.co.kr/evt/evt/evtDtl/searchEvtDtl?coCd=A420&expoChnlCd=03&evntNo={event_id}"
        return self._signed_request(url)

    def fetch_inventory(self, event_id, gift_id):
        """지점별 실시간 재고 조회"""
        url = f"{self.SAPRM_URL}/searchSaprmEvtTgtsiteList?coCd=A420&expoChnlCd=03&saprmEvntNo={event_id}&spmtlNo={gift_id}"
        return self._signed_request(url)

    def save_event(self, event_data: dict, gift_id: str = None):
        # saprmEvntNo 또는 evntNo 사용
        e_id = str(event_data.get("saprmEvntNo") or event_data.get("evntNo"))
        if not e_id: return None
        
        event = self.session.query(Event).filter_by(EventID=e_id).first()
        if not event:
            event = Event(EventID=e_id, Operator="CGV")
            self.session.add(event)
        else:
            event.Operator = "CGV"
        
        event.EventName = event_data.get("saprmEvntNm") or event_data.get("evntNm")
        if gift_id:
            event.GiftID = gift_id
            
        # 이미지 처리
        img = event_data.get("evtImgPath")
        if img:
            event.ImageUrl = f"https://img.cgv.co.kr{img}" if img.startswith("/") else img
            
        def parse_date(date_str):
            if not date_str: return None
            # "2025.01.01" 또는 "2025-01-01" 형식 대응
            clean_date = date_str.replace(".", "-")[:10]
            try:
                return datetime.strptime(clean_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return None

        event.ProgressStartDate = parse_date(event_data.get("evntStartYmd") or event_data.get("evntStartDt"))
        event.ProgressEndDate = parse_date(event_data.get("evntEndYmd") or event_data.get("evntEndDt"))
        
        self.session.commit()
        return event

    def save_inventory(self, event_id, gift_id, inventory_data):
        if not inventory_data or "data" not in inventory_data: return
        items = inventory_data["data"]
        if not isinstance(items, list): return

        event = self.session.query(Event).filter_by(EventID=event_id).first()
        event_name = event.EventName if event else "CGV 이벤트"
        now = datetime.now()

        existing_records = {
            str(inv.CinemaID): inv
            for inv in self.session.query(Inventory).filter_by(EventID=event_id, GiftID=gift_id).all()
        }

        for item in items:
            c_id = str(item.get("siteCd") or item.get("siteNm")) # CGV는 지점코드 또는 이름 사용
            cinema_name = item.get("siteNm")
            new_count = int(item.get("rlInvntQty") or 0)
            
            existing = existing_records.get(c_id)
            if existing and existing.ItemCount == 0 and new_count == 0: continue

            if not existing:
                inv = Inventory(
                    EventID=event_id, GiftID=gift_id, CinemaID=c_id,
                    CinemaName=cinema_name, DivisionName=item.get("regnGrpNm"),
                    ItemCount=new_count, LastUpdated=now
                )
                self.session.add(inv)
                if new_count > 0:
                    notifier.send_message(f"🆕 <b>[CGV] 신규 재고!</b>\n{event_name}\n지점: {cinema_name}\n수량: {new_count}개")
            else:
                if existing.ItemCount != new_count:
                    if existing.ItemCount > 0 and new_count == 0:
                        notifier.send_message(f"🚨 <b>[CGV] 품절!</b>\n{event_name}\n지점: {cinema_name}")
                    elif existing.ItemCount == 0 and new_count > 0:
                        notifier.send_message(f"✅ <b>[CGV] 재입고!</b>\n{event_name}\n지점: {cinema_name}\n수량: {new_count}개")
                    
                    existing.ItemCount = new_count
                    existing.LastUpdated = now
            
            self.session.add(InventoryHistory(
                EventID=event_id, GiftID=gift_id, CinemaID=c_id,
                CinemaName=cinema_name, ItemCount=new_count, RecordTime=now
            ))

        self.session.commit()
        logger.info(f"Updated active inventory items for CGV : {event_name} ({event_id})")

    def collect_target_inventory(self, event_id: str, gift_id: str):
        inv_data = self.fetch_inventory(event_id, gift_id)
        if inv_data and "data" in inv_data:
            self.save_inventory(event_id, gift_id, inv_data)
            return True
        return False

    def discover_new_events(self):
        logger.info("CGV comprehensive discovery started...")
        found = 0
        
        # 1. 일반 이벤트 탐색
        try:
            gen_data = self.fetch_events()
            if gen_data and "data" in gen_data and "list" in gen_data["data"]:
                for item in gen_data["data"]["list"]:
                    if not self.session.query(Event).filter_by(EventID=str(item.get("evntNo"))).first():
                        self.save_event(item)
                        found += 1
        except Exception as e: logger.error(f"CGV General discovery failed: {e}")

        # 2. SAPRM(굿즈) 이벤트 탐색 및 굿즈 ID 매칭
        try:
            sp_data = self.fetch_special_events()
            if sp_data and "data" in sp_data and "list" in sp_data["data"]:
                for item in sp_data["data"]["list"]:
                    e_id = str(item.get("saprmEvntNo"))
                    event = self.session.query(Event).filter_by(EventID=e_id).first()
                    
                    # 굿즈 ID가 없는 경우 매칭 시도
                    if not event or not event.GiftID:
                        g_id, g_name = self.fetch_goods_id(e_id)
                        if g_id:
                            self.save_event(item, gift_id=g_id)
                            logger.info(f"Matched CGV Goods: {g_name} ({g_id}) for Event {e_id}")
                            # 재고 수집 즉시 실행
                            self.collect_target_inventory(e_id, g_id)
                            found += 1
                        elif not event:
                            self.save_event(item)
                            found += 1
        except Exception as e: logger.error(f"CGV Special discovery failed: {e}")
        
        logger.info(f"CGV discovery finished. Found {found} new/updated items.")
        return found
