import pytest
from datetime import datetime, date
from src.database.models import Event, Inventory

def test_cinemas_list_page(client, session):
    # Create test data
    event1 = Event(
        EventID="TEST_EVENT_1",
        Operator="LOTTE",
        EventName="Test Event 1",
        ProgressStartDate=date(2026, 3, 1),
        ProgressEndDate=date(2026, 3, 31)
    )
    event2 = Event(
        EventID="TEST_EVENT_2",
        Operator="CGV",
        EventName="Test Event 2",
        ProgressStartDate=date(2026, 3, 1),
        ProgressEndDate=date(2026, 3, 31)
    )
    inv1 = Inventory(
        EventID="TEST_EVENT_1",
        GiftID="GIFT1",
        CinemaID="1013",
        CinemaName="Gimpo Airport",
        ItemCount=10,
        LastUpdated=datetime(2026, 3, 19, 12, 0)
    )
    inv2 = Inventory(
        EventID="TEST_EVENT_2",
        GiftID="GIFT2",
        CinemaID="001",
        CinemaName="Gangnam",
        ItemCount=5,
        LastUpdated=datetime(2026, 3, 19, 12, 0)
    )
    
    session.add_all([event1, event2, inv1, inv2])
    session.commit()
    
    response = client.get("/cinemas")
    assert response.status_code == 200
    assert "롯데시네마" in response.text
    assert "CGV" in response.text
    assert "Gimpo Airport" in response.text
    assert "Gangnam" in response.text

def test_cinema_detail_page(client, session):
    # Create test data
    event = Event(
        EventID="TEST_EVENT_1",
        Operator="LOTTE",
        EventName="Test Event 1",
        ProgressStartDate=date(2026, 3, 1),
        ProgressEndDate=date(2026, 3, 31)
    )
    inv = Inventory(
        EventID="TEST_EVENT_1",
        GiftID="GIFT1",
        CinemaID="1013",
        CinemaName="Gimpo Airport",
        ItemCount=10,
        LastUpdated=datetime(2026, 3, 19, 12, 0)
    )
    
    session.add_all([event, inv])
    session.commit()
    
    response = client.get("/cinemas/LOTTE/1013")
    assert response.status_code == 200
    assert "Gimpo Airport" in response.text
    assert "Test Event 1" in response.text
    assert "10개 이하" in response.text  # format_stock uses this logic: 10 > 0 -> "10개 이하" (wait, check filter logic)

def test_cinema_detail_not_found(client, session):
    response = client.get("/cinemas/LOTTE/9999")
    assert response.status_code == 200
    assert "현재 이 지점에 등록된 굿즈 정보가 없습니다" in response.text
