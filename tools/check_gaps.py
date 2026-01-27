from src.database.models import get_session, Event
import re

def find_gaps():
    session = get_session()
    events = session.query(Event).all()
    
    print(f"Total events: {len(events)}")
    
    # GiftID가 없는 이벤트들
    missing_gift_id = [e for e in events if not e.GiftID]
    if missing_gift_id:
        print("\n[Events with missing GiftID]")
        for e in missing_gift_id:
            print(f"EventID: {e.EventID}, Name: {e.EventName}")
    else:
        print("\nNo events with null or empty GiftID found.")

    # GiftID가 있는 이벤트들 분석
    events_with_gift = [e for e in events if e.GiftID]
    
    # GiftID가 숫자인 경우 정렬하여 공백 확인
    numeric_gifts = []
    for e in events_with_gift:
        try:
            val = int(e.GiftID)
            numeric_gifts.append((val, e))
        except ValueError:
            pass
            
    if numeric_gifts:
        numeric_gifts.sort(key=lambda x: x[0])
        print("\n[Sequence Analysis of numeric GiftIDs]")
        
        min_id = numeric_gifts[0][0]
        max_id = numeric_gifts[-1][0]
        
        gift_dict = {val: e for val, e in numeric_gifts}
        
        gaps = []
        for i in range(min_id, max_id + 1):
            if i not in gift_dict:
                gaps.append(i)
        
        if gaps:
            print(f"Found {len(gaps)} gaps in sequence between {min_id} and {max_id}:")
            # 연속된 공백은 묶어서 표시
            if len(gaps) > 20:
                print(f"{gaps[:10]} ... {gaps[-10:]}")
            else:
                print(gaps)
        else:
            print("No gaps found in numeric sequence.")
            
        print("\n[Current Numeric GiftIDs List]")
        for val, e in numeric_gifts:
            print(f"GiftID: {val}, EventID: {e.EventID}, Name: {e.EventName}")
    
    session.close()

if __name__ == "__main__":
    find_gaps()
