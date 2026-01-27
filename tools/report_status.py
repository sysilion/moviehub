from src.database.models import get_session, Event

def report_missing_status():
    session = get_session()
    events = session.query(Event).all()
    
    # 1. EventID 분석
    event_ids = sorted([int(e.EventID) for e in events if e.EventID.isdigit()])
    
    # 2. GiftID 분석
    used_gift_ids = set()
    for e in events:
        if e.GiftID and e.GiftID.isdigit():
            used_gift_ids.add(int(e.GiftID))
            
    # 범위 설정 (데이터 존재 범위 기준)
    min_event = event_ids[0]
    max_event = event_ids[-1]
    
    # GiftID 범위는 대략적인 관측 범위로 설정 (13658 ~ 13830)
    min_gift = 13658
    max_gift = 13830
    
    print("=== [ Missing Data Report ] ===\n")
    
    # --- EventID Gaps ---
    print(f"1. EventID Gaps (Range: {min_event} ~ {max_event})")
    event_gaps = []
    prev = min_event
    for curr in event_ids[1:]:
        if curr - prev > 1:
            event_gaps.append((prev + 1, curr - 1))
        prev = curr
        
    if event_gaps:
        for start, end in event_gaps:
            count = end - start + 1
            print(f"   - {start} ~ {end} ({count} missing)")
    else:
        print("   - No gaps found.")
        
    # --- GiftID Gaps ---
    print(f"\n2. Unassigned GiftIDs (Range: {min_gift} ~ {max_gift})")
    gift_gaps = []
    # 연속된 번호들을 묶어서 표현하기 위한 로직
    current_gap_start = None
    
    for i in range(min_gift, max_gift + 1):
        if i not in used_gift_ids:
            if current_gap_start is None:
                current_gap_start = i
        else:
            if current_gap_start is not None:
                gift_gaps.append((current_gap_start, i - 1))
                current_gap_start = None
                
    if current_gap_start is not None:
        gift_gaps.append((current_gap_start, max_gift))
        
    if gift_gaps:
        for start, end in gift_gaps:
            count = end - start + 1
            if start == end:
                print(f"   - {start}")
            else:
                print(f"   - {start} ~ {end} ({count} IDs)")
    else:
        print("   - No empty slots found.")

    print(f"\nTotal Events in DB: {len(events)}")
    print(f"Total Assigned Gifts: {len(used_gift_ids)}")
    
    session.close()

if __name__ == "__main__":
    report_missing_status()
