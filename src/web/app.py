import math
from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from src.database.models import get_session, Event, Inventory, InventoryHistory
from src.scheduler.main import start_scheduler, stop_scheduler, scheduler
from src.collectors.lotte import LotteCinemaCollector
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import os

# 템플릿 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def format_stock(count):
    if count is None: return "정보 없음"
    count = int(count)
    if count >= 50: return f"{count}개 이상"
    elif count > 0: return f"{count}개 이하"
    else: return "소진"

templates.env.filters["format_stock"] = format_stock

# DB 세션 의존성
def get_db():
    db = get_session()
    try: yield db
    finally: db.close()

from src.collectors.megabox import MegaboxCollector
from src.collectors.cgv import CGVCollector
from src.collectors.cineq import CineQCollector

# ... (생략된 기존 코드)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 시작 시 DB 초기화 (테이블 생성)
    from src.database.models import init_db
    init_db()
    
    # Vercel(Serverless) 환경에서는 로컬 백그라운드 스케줄러를 시작하지 않습니다.
    # 대신 Vercel Cron Jobs를 사용합니다.
    if os.getenv("VERCEL") != "1":
        start_scheduler()
    yield
    if os.getenv("VERCEL") != "1":
        stop_scheduler()

app = FastAPI(lifespan=lifespan)

@app.get("/api/cron/discovery")
async def cron_discovery(db: Session = Depends(get_db)):
    """Vercel Cron용: 신규 이벤트 탐색 및 자동 등록"""
    collectors = [
        LotteCinemaCollector(db),
        MegaboxCollector(db),
        CGVCollector(db),
        CineQCollector(db)
    ]
    results = {}
    for col in collectors:
        name = col.__class__.__name__
        try:
            found = col.discover_new_events()
            results[name] = f"Found {found}"
        except Exception as e:
            results[name] = f"Error: {str(e)}"
    
    return {"status": "success", "results": results}

# 굿즈 판별 키워드
GOODS_KEYWORDS = ["증정", "뱃지", "아트카드", "artcard", "무비티켓", "키링", "시그니처"]
EXCLUDE_KEYWORDS = ["콤보", "런칭"]

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(
    request: Request, 
    q: str = None, 
    operator: str = None, # 운영사 필터 (LOTTE, CGV, MEGABOX, CINEQ)
    show_ended: bool = False, 
    show_all: bool = False,
    page: int = 1,
    limit: int = 30,
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    
    # 운영사 필터 적용
    if operator:
        query = query.filter(Event.Operator == operator)
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
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
            query = query.filter(or_(Event.ProgressEndDate >= today_str, Event.ProgressEndDate == None))

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
        
    return templates.TemplateResponse("index.html", {
        "request": request,
        "events": dashboard_data,
        "q": q,
        "operator": operator,
        "show_ended": show_ended,
        "show_all": show_all,
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count
    })
@app.get("/event/{event_id}", response_class=HTMLResponse)
async def read_event_detail(request: Request, event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.EventID == event_id).first()
    inventory = db.query(Inventory).filter(Inventory.EventID == event_id).order_by(Inventory.DivisionCode, Inventory.CinemaName).all()
    total_stock = sum(item.ItemCount for item in inventory)
    return templates.TemplateResponse("detail.html", {
        "request": request, "event": event, "inventory": inventory, "total_stock": total_stock
    })

@app.post("/api/update/{event_id}")
async def trigger_update(event_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """즉시 수량 갱신 요청"""
    event = db.query(Event).filter_by(EventID=event_id).first()
    if not event or not event.GiftID: 
        return JSONResponse({"status": "error", "message": "No GiftID found for this event. Please find GiftID first."}, status_code=400)
    
    gift_id = event.GiftID
    
    def update_task():
        session = get_session()
        try:
            collector = LotteCinemaCollector(session)
            if collector.collect_target_inventory(event_id, gift_id):
                # 갱신 성공 시 스케줄러에 잡이 없으면 등록
                if not scheduler.scheduler.get_job(f"job_{event_id}"):
                    scheduler.schedule_single_event(event_id, gift_id)
        finally: session.close()
        
    background_tasks.add_task(update_task)
    return {"status": "success", "message": "Update task started in background"}

@app.post("/api/scan-gift/{event_id}")
async def trigger_gift_scan(event_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """누락된 GiftID 스캔 요청"""
    
    def scan_task():
        session = get_session()
        try:
            collector = LotteCinemaCollector(session)
            if collector.match_missing_gift_id(event_id):
                # 굿즈 매칭 성공 시 즉시 인벤토리 갱신 및 스케줄러 등록
                event = session.query(Event).filter_by(EventID=event_id).first()
                if event and event.GiftID:
                    collector.collect_target_inventory(event_id, event.GiftID)
                    if not scheduler.scheduler.get_job(f"job_{event_id}"):
                        scheduler.schedule_single_event(event_id, event.GiftID)
        finally: session.close()
        
    background_tasks.add_task(scan_task)
    return {"status": "success", "message": "GiftID scan started in background"}

@app.get("/api/history/{event_id}/{cinema_id}")
async def get_stock_history(event_id: str, cinema_id: str, db: Session = Depends(get_db)):
    """특정 지점의 수량 변동 이력 데이터 반환 (현재 상태 포함)"""
    event = db.query(Event).filter(Event.EventID == event_id).first()
    start_dt = None
    if event and event.ProgressStartDate:
        try:
            start_dt = datetime.strptime(event.ProgressStartDate, "%Y-%m-%d")
        except ValueError:
            start_dt = None

    pre_start_index = 0
    def build_point(record_time: datetime, count: int):
        nonlocal pre_start_index
        display_time = record_time
        if start_dt and record_time < start_dt:
            display_time = start_dt + timedelta(hours=6 + pre_start_index)
            pre_start_index += 1
        return {
            "time": display_time.isoformat(timespec="seconds"),
            "actual_time": record_time.strftime("%m-%d %H:%M"),
            "count": count
        }

    # 1. 과거 이력 조회
    history = db.query(InventoryHistory).filter_by(EventID=event_id, CinemaID=cinema_id).order_by(InventoryHistory.RecordTime.asc()).all()
    
    data = [build_point(h.RecordTime, h.ItemCount) for h in history]
    
    # 2. 현재 최신 상태 추가 (이력의 마지막보다 최신인 경우)
    current = db.query(Inventory).filter_by(EventID=event_id, CinemaID=cinema_id).first()
    if current:
        current_time_str = current.LastUpdated.isoformat(timespec="seconds")
        # 마지막 이력과 시간이 다르거나 이력이 없는 경우 추가
        if not data or data[-1]["actual_time"] != current.LastUpdated.strftime("%m-%d %H:%M"):
            data.append(build_point(current.LastUpdated, current.ItemCount))
            
    return data
