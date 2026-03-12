from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'

    EventID = Column(String, primary_key=True)
    Operator = Column(String, default="LOTTE", index=True) # 운영사 (LOTTE, CGV, MEGABOX, CINEQ)
    EventName = Column(String)
    GiftID = Column(String, nullable=True) # 굿즈 번호 필드 추가
    EventClassificationCode = Column(String, nullable=True)
    EventTypeCode = Column(String, nullable=True)
    EventTypeName = Column(String, nullable=True)
    ProgressStartDate = Column(String, nullable=True)
    ProgressEndDate = Column(String, nullable=True)
    ImageUrl = Column(String, nullable=True)
    DetailImageUrl = Column(String, nullable=True)
    RawData = Column(Text, nullable=True)
    CreatedAt = Column(DateTime, default=datetime.now)
    UpdatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    inventories = relationship("Inventory", back_populates="event", cascade="all, delete-orphan")

class Inventory(Base):
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    EventID = Column(String, ForeignKey('events.EventID'), index=True)
    GiftID = Column(String, index=True)
    CinemaID = Column(String, index=True)
    CinemaName = Column(String)
    DivisionCode = Column(String, nullable=True)
    DetailDivisionCode = Column(String, nullable=True)
    DivisionName = Column(String, nullable=True)
    ItemCount = Column(Integer)
    LastUpdated = Column(DateTime, default=datetime.now)

    event = relationship("Event", back_populates="inventories")

class InventoryHistory(Base):
    __tablename__ = 'inventory_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    EventID = Column(String, index=True)
    GiftID = Column(String, index=True)
    CinemaID = Column(String, index=True)
    CinemaName = Column(String)
    ItemCount = Column(Integer)
    RecordTime = Column(DateTime, default=datetime.now)

_engine = None

def get_engine(db_url=None):
    global _engine
    if _engine:
        return _engine

    if not db_url:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            if os.getenv('VERCEL') == '1':
                db_url = 'sqlite:////tmp/moviehub.db'
            else:
                db_url = 'sqlite:///moviehub.db'
    
    # SQLite의 경우 멀티스레드 환경(FastAPI + Scheduler)에서 check_same_thread=False 필요
    connect_args = {}
    if db_url.startswith('sqlite'):
        connect_args = {'check_same_thread': False}
    else:
        # Postgres 등 외부 DB 사용 시 연결 풀 설정 보강
        return create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
            pool_pre_ping=True
        )

    _engine = create_engine(db_url, connect_args=connect_args)
    return _engine

def get_session(engine=None):
    if not engine:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_db(engine=None):
    if not engine:
        engine = get_engine()
    Base.metadata.create_all(engine)