import pytest
import time
from src.database.models import Event
from datetime import date

def test_dashboard_performance(client, session):
    # Create 100 mock events
    events = []
    for i in range(100):
        events.append(Event(
            EventID=f"PERF_TEST_{i}",
            Operator="LOTTE",
            EventName=f"Performance Test Event {i} 아트카드",
            GiftID=str(10000 + i),
            ProgressStartDate=date(2026, 3, 1),
            ProgressEndDate=date(2026, 3, 31)
        ))
    session.add_all(events)
    session.commit()
    
    start_time = time.time()
    response = client.get("/")
    end_time = time.time()
    
    duration = end_time - start_time
    assert response.status_code == 200
    print(f"\nDashboard Load Time (100 events): {duration:.4f}s")
    # Recommended threshold: < 500ms
    assert duration < 1.0 
