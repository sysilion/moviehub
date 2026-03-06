import sys
import os
import time
import random

# Add root to path
sys.path.append(os.getcwd())

from src.database.models import get_session, Event
from src.collectors.lotte import LotteCinemaCollector
from src.utils.logger import get_logger

logger = get_logger("MissingScan")

def get_empty_gift_ids(session, start, end):
    """
    지정된 범위 내에서 현재 DB에 존재하지 않는(비어있는) GiftID 리스트를 반환합니다.
    """
    events = session.query(Event.GiftID).filter(Event.GiftID != None).all()
    used_ids = set()
    for e in events:
        if e.GiftID and e.GiftID.isdigit():
            used_ids.add(int(e.GiftID))
            
    empty_ids = []
    for i in range(start, end + 1):
        if i not in used_ids:
            empty_ids.append(i)
            
    return empty_ids

def main():
    session = get_session()
    collector = LotteCinemaCollector(session)
    
    # 대상 EventID 구간
    missing_ranges = [
        (201010024726007, 201010024726007)
    ]
    
    # 비어있는 GiftID 후보 추출
    gift_scan_start = 13000
    gift_scan_end = collector.get_gift_id_search_limit()
    candidate_gift_ids = get_empty_gift_ids(session, gift_scan_start, gift_scan_end)
    
    print(f"Target Event Ranges: {len(missing_ranges)} groups")
    print(f"Empty GiftID Candidates: {len(candidate_gift_ids)} IDs")
    print(f"Delay: 0.5~1.5 seconds per request")
    
    found_count = 0
    
    for start_id, end_id in missing_ranges:
        print(f"\nScanning EventID range: {start_id} ~ {end_id}")
        
        for event_num in range(start_id, end_id + 1):
            event_id = str(event_num)
            
            # 1. 이벤트 존재 여부 확인
            try:
                delay = random.uniform(0.5, 1.5)
                time.sleep(delay)
                detail = collector.fetch_event_detail(event_id)
                if not (detail and 'InfomationDeliveryEventDetail' in detail and detail['InfomationDeliveryEventDetail']):
                    continue
            except Exception as e:
                print(f"E", end="", flush=True)
                continue
                
            event_info = detail['InfomationDeliveryEventDetail'][0]
            event_name = event_info.get('EventName')
            print(f"\n[NEW EVENT FOUND] ID: {event_id}, Name: {event_name}")
            
            # 2. 이벤트 저장 (일단 GiftID 없이)
            collector.save_event(event_info, gift_id=None)
            found_count += 1
            
            # 3. 비어있는 GiftID들로 매칭 시도
            print(f"  > Matching GiftIDs (Candidates left: {len(candidate_gift_ids)})...")
            matched_gift = None
            
            # shallow copy to avoid modification during iteration
            candidates_to_check = list(candidate_gift_ids)
            for gift_num in candidates_to_check:
                gift_id = str(gift_num)
                try:
                    delay = random.uniform(0.5, 1.5)
                    time.sleep(delay)
                    inv_data = collector.fetch_inventory(event_id, gift_id)
                    if inv_data and inv_data.get('CinemaDivisionGoods'):
                        print(f"  ✅ MATCHED! GiftID: {gift_id}")
                        
                        collector.save_event(event_info, gift_id=gift_id)
                        collector.save_inventory(event_id, gift_id, inv_data)
                        
                        matched_gift = gift_id
                        candidate_gift_ids.remove(gift_num) 
                        break 
                except Exception:
                    pass
            
            if not matched_gift:
                print("  ❌ No matching GiftID found in empty slots.")
                
    print(f"\nScan complete. Found {found_count} new events.")
    session.close()

if __name__ == "__main__":
    main()