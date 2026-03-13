import math
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from src.database.models import Event, Inventory

# 굿즈 판별 키워드
GOODS_KEYWORDS = ["증정", "뱃지", "아트카드", "artcard", "무비티켓", "키링", "시그니처"]
EXCLUDE_KEYWORDS = ["콤보", "런칭"]

class EventService:
    @staticmethod
    def get_dashboard_events(
        db: Session,
        q: str = None,
        operator: str = None,
        show_ended: bool = False,
        show_all: bool = False,
        page: int = 1,
        limit: int = 30
    ):
        query = db.query(Event)
        
        # 운영사 필터 적용
        if operator:
            query = query.filter(Event.Operator == operator)
        
        today = datetime.now().date()
        
        # 기본적으로 굿즈 관련 이벤트만 노출 (show_all이 False일 때 필터 적용)
        if not show_all:
            goods_filters = [Event.GiftID != None]
            for kw in GOODS_KEYWORDS:
                goods_filters.append(Event.EventName.ilike(f"%{kw}%"))
            
            # 합집합(확정 OR 예상 키워드) 적용
            query = query.filter(or_(*goods_filters))
            
            # 제외 키워드 적용 (NOT LIKE)
            for ex_kw in EXCLUDE_KEYWORDS:
                query = query.filter(Event.EventName.not_ilike(f"%{ex_kw}%"))

        # 검색어가 있으면 날짜 필터 무시하고 검색 결과 전체 반환
        if q:
            query = query.filter(Event.EventName.ilike(f"%{q}%"))
        else:
            # 검색어가 없을 때만 종료된 이벤트 필터링 적용
            if not show_ended:
                query = query.filter(or_(Event.ProgressEndDate >= today, Event.ProgressEndDate == None))

        # 전체 개수 계산 (페이지네이션 전)
        total_count = query.count()
        total_pages = math.ceil(total_count / limit)
        
        # 페이지네이션 적용
        offset = (page - 1) * limit
        events = query.order_by(Event.ProgressStartDate.desc()).offset(offset).limit(limit).all()
        
        dashboard_data = []
        for event in events:
            total_stock = db.query(func.sum(Inventory.ItemCount)).filter(Inventory.EventID == event.EventID).scalar() or 0
            last_updated = db.query(func.max(Inventory.LastUpdated)).filter(Inventory.EventID == event.EventID).scalar()
            
            # 굿즈 예상 여부 판별 (제외 키워드 포함)
            is_potential = False
            event_name_lower = event.EventName.lower()
            if not event.GiftID:
                has_good_kw = any(kw.lower() in event_name_lower for kw in GOODS_KEYWORDS)
                has_exclude_kw = any(ex_kw.lower() in event_name_lower for ex_kw in EXCLUDE_KEYWORDS)
                is_potential = has_good_kw and not has_exclude_kw

            dashboard_data.append({
                "event": event,
                "total_stock": total_stock,
                "gift_id": event.GiftID,
                "last_updated": last_updated,
                "is_potential": is_potential
            })
            
        return dashboard_data, total_pages, total_count
