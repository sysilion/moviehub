import pytest
from src.database.models import Event
from datetime import datetime

def test_get_gift_id_search_limit_fallback(lotte_collector):
    # If no events in DB, should return fallback 14125
    limit = lotte_collector.get_gift_id_search_limit()
    assert limit == 14125

def test_get_gift_id_search_limit_with_data(lotte_collector, session):
    # Add a mock event with GiftID
    mock_event = Event(
        EventID="12345",
        Operator="LOTTE",
        EventName="Test Event",
        GiftID="13000",
        CreatedAt=datetime.now()
    )
    session.add(mock_event)
    session.commit()
    
    # Limit should be 13000 + 50 = 13050
    limit = lotte_collector.get_gift_id_search_limit()
    assert limit == 13050

def test_get_gift_id_search_limit_with_multiple_data(lotte_collector, session):
    # Add multiple mock events with different GiftIDs
    events = [
        Event(EventID="1", Operator="LOTTE", EventName="E1", GiftID="10000"),
        Event(EventID="2", Operator="LOTTE", EventName="E2", GiftID="15000"),
        Event(EventID="3", Operator="LOTTE", EventName="E3", GiftID="12000"),
    ]
    session.add_all(events)
    session.commit()
    
    # Max GiftID is 15000, so limit should be 15050
    limit = lotte_collector.get_gift_id_search_limit()
    assert limit == 15050

def test_get_latest_gift_id(lotte_collector, session):
    # Initially None
    assert lotte_collector.get_latest_gift_id() is None
    
    # Add data
    session.add(Event(EventID="1", GiftID="13700"))
    session.commit()
    
    assert lotte_collector.get_latest_gift_id() == "13700"
