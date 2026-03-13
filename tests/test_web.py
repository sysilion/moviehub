import pytest
from fastapi.testclient import TestClient
from src.database.models import Event
from datetime import datetime, date

def test_read_dashboard_empty(client):
    response = client.get("/")
    assert response.status_code == 200
    # Check if some expected text is in the HTML
    assert "MovieHub" in response.text

def test_read_dashboard_with_data(client, session):
    # Add data to the session (which should be the same as the client's session)
    # Actually, in conftest.py, we overridden get_db to use TestingSessionLocal(bind=engine).
    # Since we use engine fixture here too, they share the same in-memory DB.
    
    event = Event(
        EventID="TEST_EVENT_1",
        Operator="LOTTE",
        EventName="Test 아트카드 증정 이벤트",
        GiftID="12345",
        ProgressStartDate=date(2026, 3, 1),
        ProgressEndDate=date(2026, 3, 31)
    )
    session.add(event)
    session.commit()
    
    response = client.get("/")
    assert response.status_code == 200
    assert "Test 아트카드 증정 이벤트" in response.text

def test_cron_discovery_endpoint(client, mocker):
    # Mock the collectors to avoid real API calls
    mocker.patch("src.collectors.lotte.LotteCinemaCollector.discover_new_events", return_value=5)
    mocker.patch("src.collectors.megabox.MegaboxCollector.discover_new_events", return_value=3)
    mocker.patch("src.collectors.cgv.CGVCollector.discover_new_events", return_value=0)
    mocker.patch("src.collectors.cineq.CineQCollector.discover_new_events", return_value=1)
    
    response = client.get("/api/cron/discovery")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["results"]["LotteCinemaCollector"] == "Found 5"
