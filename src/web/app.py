import math
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, Depends, BackgroundTasks, HTTPException, Header
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from pydantic import BaseModel
from typing import List, Optional

from src.database.models import get_session, Event, Inventory, InventoryHistory, init_db, run_migrations
from src.scheduler.main import start_scheduler, stop_scheduler, scheduler
from src.collectors.lotte import LotteCinemaCollector
from src.collectors.megabox import MegaboxCollector
from src.collectors.cgv import CGVCollector
from src.collectors.cineq import CineQCollector
from src.services.event_service import EventService
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger("WebApp")

# API Key 설정 (환경변수 권장)
API_KEY = os.getenv("RELAY_API_KEY", "moviehub-relay-secret-key")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# Pydantic Models for Sync
class EventUpload(BaseModel):
    EventID: str
    Operator: str
    EventName: str
    GiftID: Optional[str] = None
    EventClassificationCode: Optional[str] = None
    EventTypeCode: Optional[str] = None
    EventTypeName: Optional[str] = None
    ProgressStartDate: Optional[str] = None # YYYY-MM-DD
    ProgressEndDate: Optional[str] = None   # YYYY-MM-DD
    ImageUrl: Optional[str] = None
    DetailImageUrl: Optional[str] = None

class InventoryUpload(BaseModel):
    EventID: str
    GiftID: str
    CinemaID: str
    CinemaName: str
    DivisionCode: Optional[str] = None
    DetailDivisionCode: Optional[str] = None
    DivisionName: Optional[str] = None
    ItemCount: int

class BatchUploadRequest(BaseModel):
    events: List[EventUpload] = []
    inventory: List[InventoryUpload] = []

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Vercel(Serverless) 환경에서는 로컬 백그라운드 스케줄러를 시작하지 않습니다.
    # 대신 Vercel Cron Jobs를 사용합니다.
    if not settings.is_vercel:
        logger.info("Starting local background scheduler...")
        try:
            start_scheduler()
            logger.info("Local background scheduler started.")
        except Exception as e:
            logger.error(f"Failed to start local background scheduler: {e}", exc_info=True)
    else:
        logger.info("Vercel environment detected. Local scheduler disabled (using Vercel Cron).")
    
    yield
    
    if not settings.is_vercel:
        logger.info("Stopping background scheduler...")
        try:
            stop_scheduler()
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")

app = FastAPI(lifespan=lifespan)

@app.get("/api/cron/discovery")
async def cron_discovery(db: Session = Depends(get_db)):
    """Vercel Cron용: 신규 이벤트 탐색 및 진행 중인 이벤트 재고 업데이트"""
    logger.info("=== Vercel Cron Job Started ===")
    collectors = {
        "LOTTE": LotteCinemaCollector(db),
        "MEGABOX": MegaboxCollector(db),
        "CGV": CGVCollector(db),
        "CINEQ": CineQCollector(db)
    }
    
    results = {"discovery": {}, "updates": []}
    
    # 1. 신규 이벤트 탐색
    for name, col in collectors.items():
        try:
            found = col.discover_new_events()
            results["discovery"][name] = f"Found {found}"
            logger.info(f"[Discovery] {name}: {found} new events")
        except Exception as e:
            logger.error(f"[Discovery] {name} failed: {e}")

    # 2. 진행 중인 이벤트 재고 업데이트 (최대 10개씩 - 타임아웃 방지)
    today = datetime.now().date()
    active_events = db.query(Event).filter(
        Event.GiftID != None,
        or_(Event.ProgressEndDate >= today, Event.ProgressEndDate == None)
    ).order_by(func.random()).limit(10).all()

    for event in active_events:
        col = collectors.get(event.Operator)
        if col:
            try:
                col.collect_target_inventory(event.EventID, event.GiftID)
                results["updates"].append(f"{event.Operator}: {event.EventID} updated")
                logger.info(f"[Update] {event.Operator}: {event.EventName} ({event.EventID})")
            except Exception as e:
                logger.error(f"[Update] {event.EventID} failed: {e}")

    logger.info("=== Vercel Cron Job Finished ===")
    return {"status": "success", "results": results}

@app.post("/api/sync/upload")
async def upload_sync_data(
    data: BatchUploadRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """크롤링 서버로부터 데이터를 수신하여 DB에 동기화합니다."""
    
    # 1. 이벤트 동기화 (Upsert)
    synced_events = 0
    for e_data in data.events:
        try:
            event = db.query(Event).filter_by(EventID=e_data.EventID).first()
            if not event:
                event = Event(EventID=e_data.EventID)
                db.add(event)
            
            # 필드 업데이트
            event.Operator = e_data.Operator
            event.EventName = e_data.EventName
            event.GiftID = e_data.GiftID
            event.EventClassificationCode = e_data.EventClassificationCode
            event.EventTypeCode = e_data.EventTypeCode
            event.EventTypeName = e_data.EventTypeName
            event.ImageUrl = e_data.ImageUrl
            event.DetailImageUrl = e_data.DetailImageUrl
            
            # 날짜 파싱 (YYYY-MM-DD)
            def parse_date(d_str):
                if not d_str: return None
                try: return datetime.strptime(d_str, "%Y-%m-%d").date()
                except: return None

            event.ProgressStartDate = parse_date(e_data.ProgressStartDate)
            event.ProgressEndDate = parse_date(e_data.ProgressEndDate)
            
            synced_events += 1
        except Exception as e:
            logger.error(f"Event sync failed for {e_data.EventID}: {e}")
    
    # 2. 인벤토리 동기화 및 히스토리 기록
    synced_inv = 0
    now = datetime.now()
    
    for i_data in data.inventory:
        try:
            # 해당 이벤트가 존재하는지 확인 (FK 제약)
            # 만약 이벤트가 이번 배치에 포함되어 있지 않고 DB에도 없다면 스킵
            # (보통 events 리스트가 먼저 처리되므로 괜찮음)
            
            inv = db.query(Inventory).filter_by(
                EventID=i_data.EventID, 
                GiftID=i_data.GiftID, 
                CinemaID=i_data.CinemaID
            ).first()
            
            should_add_history = False
            
            if not inv:
                inv = Inventory(
                    EventID=i_data.EventID,
                    GiftID=i_data.GiftID,
                    CinemaID=i_data.CinemaID,
                    CinemaName=i_data.CinemaName,
                    DivisionCode=i_data.DivisionCode,
                    DetailDivisionCode=i_data.DetailDivisionCode,
                    DivisionName=i_data.DivisionName,
                    ItemCount=i_data.ItemCount,
                    LastUpdated=now
                )
                db.add(inv)
                should_add_history = True
            else:
                # 수량이 변경되었거나 업데이트 시간이 많이 지났을 경우
                if inv.ItemCount != i_data.ItemCount:
                    inv.ItemCount = i_data.ItemCount
                    inv.LastUpdated = now
                    should_add_history = True
                else:
                    # 수량 변경은 없지만 업데이트 시간 갱신
                    inv.LastUpdated = now

            if should_add_history:
                history = InventoryHistory(
                    EventID=i_data.EventID,
                    GiftID=i_data.GiftID,
                    CinemaID=i_data.CinemaID,
                    CinemaName=i_data.CinemaName,
                    ItemCount=i_data.ItemCount,
                    RecordTime=now
                )
                db.add(history)
            
            synced_inv += 1
        except Exception as e:
            logger.error(f"Inventory sync failed for {i_data.EventID}/{i_data.CinemaID}: {e}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Commit failed: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    logger.info(f"Sync complete. Events: {synced_events}, Inventory: {synced_inv}")
    return {"status": "success", "events_processed": synced_events, "inventory_processed": synced_inv}

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
    dashboard_data, total_pages, total_count = EventService.get_dashboard_events(
        db, q, operator, show_ended, show_all, page, limit
    )
    
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

@app.get("/cinemas", response_class=HTMLResponse)
async def list_cinemas(request: Request, db: Session = Depends(get_db)):
    """지점 목록 조회 페이지"""
    cinemas_by_operator = EventService.get_all_cinemas(db)
    return templates.TemplateResponse("cinemas.html", {
        "request": request,
        "cinemas": cinemas_by_operator
    })

@app.get("/cinemas/{operator}/{cinema_id}", response_class=HTMLResponse)
async def read_cinema_detail(
    request: Request, 
    operator: str, 
    cinema_id: str, 
    db: Session = Depends(get_db)
):
    """지점별 굿즈 조회 페이지"""
    inventory_list = EventService.get_cinema_inventory(db, operator, cinema_id)
    
    # 지점 이름 찾기 (첫 번째 항목에서 추출)
    cinema_name = "알 수 없음"
    if inventory_list:
        cinema_name = inventory_list[0]["Inventory"].CinemaName
        
    return templates.TemplateResponse("cinema_detail.html", {
        "request": request,
        "operator": operator,
        "cinema_name": cinema_name,
        "inventory_list": inventory_list
    })

@app.get("/event/{event_id}", response_class=HTMLResponse)
async def read_event_detail(request: Request, event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.EventID == event_id).first()
    if not event:
        return HTMLResponse("이벤트를 찾을 수 없습니다.", status_code=404)
    inventory = db.query(Inventory).filter(Inventory.EventID == event_id).order_by(Inventory.DivisionName, Inventory.CinemaName).all()
    total_stock = sum(item.ItemCount for item in inventory)
    return templates.TemplateResponse("detail.html", {
        "request": request, "event": event, "inventory": inventory, "total_stock": total_stock
    })

@app.post("/api/update/{event_id}")
async def trigger_update(event_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """즉시 수량 갱신 요청"""
    event = db.query(Event).filter_by(EventID=event_id).first()
    if not event:
        return JSONResponse({"status": "error", "message": "Event not found."}, status_code=404)
    if not event.GiftID: 
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
        # ProgressStartDate가 이제 date 객체이므로 datetime으로 변환
        start_dt = datetime.combine(event.ProgressStartDate, datetime.min.time())

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
        # 마지막 이력과 시간이 다르거나 이력이 없는 경우 추가
        if not data or data[-1]["actual_time"] != current.LastUpdated.strftime("%m-%d %H:%M"):
            data.append(build_point(current.LastUpdated, current.ItemCount))
            
    return data
