import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, get_session
import src.database.models as models
from fastapi.testclient import TestClient
from src.web.app import app, get_db
import os
import unittest.mock as mock

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    os.environ["DATABASE_URL"] = "sqlite:///file:testdb_global?mode=memory&cache=shared"
    yield

@pytest.fixture(scope="function")
def engine():
    db_url = os.environ["DATABASE_URL"]
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    
    connection = engine.connect()
    Base.metadata.create_all(engine)
    
    original_get_engine = models.get_engine
    models.get_engine = lambda db_url=None: engine
    
    yield engine
    
    models.get_engine = original_get_engine
    Base.metadata.drop_all(engine)
    connection.close()

@pytest.fixture(scope="function")
def session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def lotte_collector(session):
    from src.collectors.lotte import LotteCinemaCollector
    return LotteCinemaCollector(session)

@pytest.fixture
def client(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock scheduler in src.web.app where it is used
    with mock.patch("src.web.app.start_scheduler"), \
         mock.patch("src.web.app.stop_scheduler"):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()
