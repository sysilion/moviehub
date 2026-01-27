from src.database.models import get_session, Event

def analyze_event_id_gaps():
    session = get_session()
    # EventID를 숫자로 변환하여 정렬
    events = session.query(Event.EventID).all()
    event_ids = sorted([int(e.EventID) for e in events if e.EventID.isdigit()])
    
    if not event_ids:
        print("No numeric EventIDs found.")
        return

    print(f"Total Events: {len(event_ids)}")
    print(f"Range: {event_ids[0]} ~ {event_ids[-1]}")
    
    gaps = []
    prev = event_ids[0]
    
    # 공백 구간 찾기 (너무 큰 공백은 제외하거나 별도 표시 가능하지만 여기선 단순 스캔)
    for current in event_ids[1:]:
        if current - prev > 1:
            # 공백 발견
            gap_start = prev + 1
            gap_end = current - 1
            gaps.append((gap_start, gap_end))
        prev = current
        
    print(f"\nFound {len(gaps)} gaps in EventID sequence:")
    for start, end in gaps:
        count = end - start + 1
        print(f" - Gap: {start} ~ {end} ({count} missing)")
        
    session.close()

if __name__ == "__main__":
    analyze_event_id_gaps()
