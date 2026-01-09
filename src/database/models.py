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
    EventName = Column(String)
    EventClassificationCode = Column(String, nullable=True)
    EventTypeCode = Column(String, nullable=True)
    EventTypeName = Column(String, nullable=True)
    ProgressStartDate = Column(String, nullable=True)
    ProgressEndDate = Column(String, nullable=True)
    ImageUrl = Column(String, nullable=True)
    LinkEventFlag = Column(String, nullable=True)
    CinemaID = Column(String, nullable=True)
    DetailImageUrl = Column(String, nullable=True)
    RawData = Column(Text, nullable=True)
    CreatedAt = Column(DateTime, default=datetime.now)
    UpdatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    inventories = relationship("Inventory", back_populates="event", cascade="all, delete-orphan")

class Inventory(Base):
    """현재 시점의 최신 재고 정보를 저장합니다."""
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    EventID = Column(String, ForeignKey('events.EventID'), index=True)
    GiftID = Column(String, index=True)
    CinemaID = Column(String, index=True)
    CinemaName = Column(String)
    DivisionCode = Column(String, nullable=True)
    DetailDivisionCode = Column(String, nullable=True)
    ItemCount = Column(Integer)
    LastUpdated = Column(DateTime, default=datetime.now)

    event = relationship("Event", back_populates="inventories")

class InventoryHistory(Base):
    """시간대별 재고 변동 이력을 저장합니다."""
    __tablename__ = 'inventory_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    EventID = Column(String, index=True)
    GiftID = Column(String, index=True)
    CinemaID = Column(String, index=True)
    CinemaName = Column(String)
    ItemCount = Column(Integer)
    RecordTime = Column(DateTime, default=datetime.now)

def get_engine(db_url=None):
    if not db_url:
        db_url = os.getenv('DATABASE_URL', 'sqlite:///moviehub.db')
    return create_engine(db_url)

def get_session(engine=None):
    if not engine:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_db(engine=None):
    if not engine:
        engine = get_engine()
    Base.metadata.create_all(engine)