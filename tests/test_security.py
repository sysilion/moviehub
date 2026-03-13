import pytest
from src.database.models import Event
from datetime import date

def test_event_detail_not_found(client):
    response = client.get("/event/NON_EXISTENT_ID")
    # Should probably return 404 or a nice message
    assert response.status_code == 404

def test_event_detail_found(client, session):
    event = Event(
        EventID="EXISTING_ID",
        Operator="LOTTE",
        EventName="Test Event",
        ProgressStartDate=date(2026, 3, 1),
        ProgressEndDate=date(2026, 3, 31)
    )
    session.add(event)
    session.commit()
    
    response = client.get("/event/EXISTING_ID")
    assert response.status_code == 200
    assert "Test Event" in response.text

def test_update_event_public_access(client):
    # Documentation of security gap: This administrative endpoint is currently public
    response = client.post("/api/update/SOME_ID")
    # If it's public, it might return 200 or 404 depending on existence, but it won't be 401/403
    assert response.status_code in [200, 404]
