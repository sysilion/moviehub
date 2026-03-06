import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from src.database.models import get_session, Event
from src.collectors.lotte import LotteCinemaCollector

def main():
    session = get_session()
    collector = LotteCinemaCollector(session)
    
    print("Fetching current events from Lotte Cinema...")
    all_remote_events = []
    # 1페이지부터 3페이지까지 조회 (최신 이벤트 포함)
    for page in [1, 2, 3]:
        data = collector.fetch_events(page=page)
        if data and 'Items' in data:
            all_remote_events.extend(data['Items'])
            
    if not all_remote_events:
        print("Failed to fetch events from Lotte Cinema. Check API parameters or network.")
        return

    # DB에 저장된 EventID 목록 가져오기
    existing_ids = {e.EventID for e in session.query(Event.EventID).all()}
    
    new_events = []
    for item in all_remote_events:
        eid = str(item.get('EventID'))
        if eid not in existing_ids:
            new_events.append(item)
            
    if new_events:
        print(f"\nFound {len(new_events)} new events not in DB:")
        for e in new_events:
            print(f" - [{e.get('EventID')}] {e.get('EventName')} ({e.get('ProgressStartDate')} ~ {e.get('ProgressEndDate')})")
    else:
        print("\nAll current events from the list are already registered in the DB.")
        
    session.close()

if __name__ == "__main__":
    main()
