import sys
import os
import argparse

# Add root to path
sys.path.append(os.getcwd())

from src.database.models import get_session, init_db, get_engine
from src.collectors.lotte import LotteCinemaCollector
from src.utils.logger import get_logger

logger = get_logger("ManualAdd")

def main():
    parser = argparse.ArgumentParser(description="Add event and scan goods in range.")
    parser.add_argument("event_id", type=str, help="The Event ID")
    parser.add_argument("start_id", type=int, help="Start Gift ID")
    parser.add_argument("end_id", type=int, help="End Gift ID")
    
    args = parser.parse_args()
    
    event_id = args.event_id
    start_id = args.start_id
    end_id = args.end_id
    
    # Initialize DB
    engine = get_engine()
    init_db(engine)
    session = get_session(engine)
    
    collector = LotteCinemaCollector(session)
    
    logger.info(f"Processing Event {event_id} | Scan Range: {start_id} ~ {end_id}")
    
    # 1. Fetch and Save Event Info (Once)
    detail = collector.fetch_event_detail(event_id)
    if not (detail and 'InfomationDeliveryEventDetail' in detail and detail['InfomationDeliveryEventDetail']):
        logger.error(f"Failed to fetch event detail for {event_id}")
        return

    event_info = detail['InfomationDeliveryEventDetail'][0]
    logger.info(f"Event Found: {event_info.get('EventName')}")
    
    # Save event initially
    collector.save_event(event_info, gift_id=None)
    
    found_count = 0
    
    # 2. Scan GiftID Range
    for gift_id_int in range(start_id, end_id + 1):
        gift_id = str(gift_id_int)
        
        try:
            inv_data = collector.fetch_inventory(event_id, gift_id)
            if inv_data and inv_data.get('CinemaDivisionGoods'):
                logger.info(f"[MATCH] Valid GiftID found: {gift_id}")
                
                # Update event with this GiftID and save inventory
                collector.save_event(event_info, gift_id=gift_id)
                collector.save_inventory(event_id, gift_id, inv_data)
                found_count += 1
            else:
                # logger.debug(f"No data for {gift_id}")
                pass
        except Exception as e:
            logger.error(f"Error checking {gift_id}: {e}")
            
    logger.info(f"Scan complete. Found {found_count} valid goods items.")

if __name__ == "__main__":
    main()
