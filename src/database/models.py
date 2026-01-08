from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from datetime import datetime

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'

    EventID = Column(String, primary_key=True)
    EventName = Column(String)
    EventClassificationCode = Column(String, nullable=True) # 구분 코드
    EventTypeCode = Column(String, nullable=True)
    EventTypeName = Column(String, nullable=True)
    ProgressStartDate = Column(String, nullable=True) # API might return strings, parsing later
    ProgressEndDate = Column(String, nullable=True)
    ImageUrl = Column(String, nullable=True)
    LinkEventFlag = Column(String, nullable=True)
    CinemaID = Column(String, nullable=True)
    DetailImageUrl = Column(String, nullable=True)
    # Storing full raw JSON might be useful if schema changes often, 
    # but for now we map specific fields.
    RawData = Column(Text, nullable=True)
    CreatedAt = Column(DateTime, default=datetime.now)
    UpdatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Inventory(Base):
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    EventID = Column(String, ForeignKey('events.EventID'), index=True)
    GiftID = Column(String, index=True)
    CinemaID = Column(String)
    CinemaName = Column(String)
    DivisionCode = Column(String, nullable=True) # Region (Seoul, etc.)
    DetailDivisionCode = Column(String, nullable=True) 
    ItemCount = Column(Integer) # Cnt
    LastUpdated = Column(DateTime, default=datetime.now)

    event = relationship("Event", back_populates="inventories")

Event.inventories = relationship("Inventory", order_by=Inventory.id, back_populates="event")

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
