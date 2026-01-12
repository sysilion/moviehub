from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import get_session, Event, Inventory, InventoryHistory
from src.scheduler.main import start_scheduler, stop_scheduler, scheduler
from src.collectors.lotte import LotteCinemaCollector
from contextlib import asynccontextmanager
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, db: Session = Depends(get_db)):
    events = db.query(Event).order_by(Event.ProgressStartDate.desc()).all()
    dashboard_data = []
    for event in events:
        total_stock = db.query(func.sum(Inventory.ItemCount)).filter(Inventory.EventID == event.EventID).scalar() or 0
        last_updated = db.query(func.max(Inventory.LastUpdated)).filter(Inventory.EventID == event.EventID).scalar()
        dashboard_data.append({
            "event": event,
            "total_stock": total_stock,
            "gift_id": event.GiftID, # Event 모델의 GiftID 사용
            "last_updated": last_updated
        })
    return templates.TemplateResponse("index.html", {"request": request, "events": dashboard_data})

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
    inv = db.query(Inventory).filter_by(EventID=event_id).first()
    if not inv: return JSONResponse({"status": "error", "message": "No GiftID found for this event"}, status_code=400)
    
    def update_task():
        session = get_session()
        try:
            collector = LotteCinemaCollector(session)
            collector.collect_target_inventory(event_id, inv.GiftID)
        finally: session.close()
        
    background_tasks.add_task(update_task)
    return {"status": "success", "message": "Update task started in background"}

@app.get("/api/history/{event_id}/{cinema_id}")
async def get_stock_history(event_id: str, cinema_id: str, db: Session = Depends(get_db)):
    """특정 지점의 수량 변동 이력 데이터 반환 (현재 상태 포함)"""
    # 1. 과거 이력 조회
    history = db.query(InventoryHistory).filter_by(EventID=event_id, CinemaID=cinema_id).order_by(InventoryHistory.RecordTime.asc()).all()
    
    data = [{
        "time": h.RecordTime.strftime("%m-%d %H:%M"),
        "count": h.ItemCount
    } for h in history]
    
    # 2. 현재 최신 상태 추가 (이력의 마지막보다 최신인 경우)
    current = db.query(Inventory).filter_by(EventID=event_id, CinemaID=cinema_id).first()
    if current:
        current_time_str = current.LastUpdated.strftime("%m-%d %H:%M")
        # 마지막 이력과 시간이 다르거나 이력이 없는 경우 추가
        if not data or data[-1]["time"] != current_time_str:
            data.append({
                "time": current_time_str,
                "count": current.ItemCount
            })
            
    return data
