import sys
import os
import time

# Add root to path
sys.path.append(os.getcwd())

from src.database.models import get_session, init_db, get_engine
from src.collectors.lotte import LotteCinemaCollector
from src.utils.logger import get_logger

logger = get_logger("RangeScan")

def main():
    # Configuration
    start_event_num = 201010014726004
    end_event_num = 201010014726004
    
    start_gift_num = 13700
    end_gift_num = collector.get_gift_id_search_limit()
    
    # Initialize DB
    engine = get_engine()
    init_db(engine)
    session = get_session(engine)
    collector = LotteCinemaCollector(session)
    
    current_gift_cursor = start_gift_num
    
    logger.info(f"Starting Scan: Events {start_event_num}~{end_event_num}")
    logger.info(f"Initial Gift Range: {current_gift_cursor}~{end_gift_num}")
    
    for event_num in range(start_event_num, end_event_num + 1):
        event_id = str(event_num)
        
        # 1. Fetch Event Detail
        # logger.info(f"Checking Event {event_id}...")
        try:
            detail = collector.fetch_event_detail(event_id)
        except Exception as e:
            logger.error(f"Error fetching detail for {event_id}: {e}")
            continue

        if not (detail and 'InfomationDeliveryEventDetail' in detail and detail['InfomationDeliveryEventDetail']):
            # Event doesn't exist or invalid
            # logger.warning(f"Event {event_id} not found or invalid.")
            continue
            
        event_info = detail['InfomationDeliveryEventDetail'][0]
        event_name = event_info.get('EventName')
        logger.info(f"[{event_id}] Found: {event_name}")
        
        # Save event basic info
        collector.save_event(event_info, gift_id=None)
        
        # 2. Scan Gift IDs from current cursor
        # If the range becomes invalid (cursor > end), stop? 
        # Or should we just stick to the end?
        if current_gift_cursor > end_gift_num:
            logger.warning("Current gift cursor exceeded end range. Stopping scan.")
            break
            
        matched_gifts = []
        
        # Scan loop
        for gift_num in range(current_gift_cursor, end_gift_num + 1):
            gift_id = str(gift_num)
            try:
                # Slight delay to be polite if needed, but sequential is usually slow enough
                # time.sleep(0.05) 
                
                inv_data = collector.fetch_inventory(event_id, gift_id)
                if inv_data and inv_data.get('CinemaDivisionGoods'):
                    logger.info(f"  -> MATCH: Gift {gift_id}")
                    
                    collector.save_event(event_info, gift_id=gift_id)
                    collector.save_inventory(event_id, gift_id, inv_data)
                    matched_gifts.append(gift_num)
            except Exception as e:
                logger.error(f"Error scanning gift {gift_id}: {e}")
        
        # Update cursor if matches found
        if matched_gifts:
            # The prompt says: "intermediate matched number... search from that number onwards"
            # We take the smallest match found for this event, or the largest?
            # Typically if Event N uses Gift 10, Event N+1 uses 11+.
            # So we set cursor to the first match? 
            # Or if multiple matches (10, 11), next event likely starts at 11 or 12?
            # Let's set cursor to min(matched_gifts). 
            # Actually, to be safe and "search from that number onwards", 
            # keeping it at the matched number is safe.
            # If we want to optimize more, we could do max(matched_gifts).
            # But let's stick to the prompt: "search from that number onwards".
            # So if we found 13720, next loop starts at 13720.
            current_gift_cursor = min(matched_gifts)
            logger.info(f"  -> Updating Gift Cursor to {current_gift_cursor}")

if __name__ == "__main__":
    main()
