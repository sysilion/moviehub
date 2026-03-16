from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from src.utils.config import settings

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
    ProgressStartDate = Column(Date, nullable=True)
    ProgressEndDate = Column(Date, nullable=True)
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
_Session = None

def get_engine(db_url=None):
    global _engine
    if _engine:
        return _engine

    if not db_url:
        db_url = settings.final_db_url
    
    if db_url.startswith('sqlite'):
        connect_args = {'check_same_thread': False}
        _engine = create_engine(db_url, connect_args=connect_args)
    else:
        # Postgres 등 외부 DB 사용 시 연결 풀 설정 보강 및 싱글톤 적용
        _engine = create_engine(
            db_url,
            pool_size=20,       # 기본 연결 수 확대
            max_overflow=30,    # 필요 시 추가 허용 수
            pool_recycle=1800,
            pool_pre_ping=True
        )
    return _engine

def get_session(engine=None):
    global _Session
    if not engine:
        engine = get_engine()
    
    if _Session is None:
        _Session = sessionmaker(bind=engine)
    
    return _Session()

def init_db(engine=None):
    if not engine:
        engine = get_engine()
    Base.metadata.create_all(engine)

def run_migrations():
    """Alembic 마이그레이션을 프로그램 방식으로 실행합니다."""
    from alembic.config import Config
    from alembic import command
    import os
    
    # 이 파일(src/database/models.py)의 위치를 기준으로 alembic.ini 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    ini_path = os.path.join(project_root, "alembic.ini")
    
    if os.path.exists(ini_path):
        alembic_cfg = Config(ini_path)
        # 런타임에 DB URL 명시적 설정
        db_url = str(get_engine().url).replace('%', '%%')
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        # 버전 위치를 절대 경로로 명시
        version_locations = os.path.join(project_root, "alembic", "versions")
        alembic_cfg.set_main_option("version_locations", version_locations)
        
        try:
            from src.utils.logger import get_logger
            m_logger = get_logger("Migration")
            m_logger.info(f"Applying Alembic migrations to {db_url}...")
            command.upgrade(alembic_cfg, "head")
            m_logger.info("Alembic migrations applied successfully.")
        except Exception as e:
            # print를 사용하여 uvicorn 로그와 별도로 확인 가능하도록 함
            print(f"Migration Error: {e}")
            raise
