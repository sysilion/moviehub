import sys
import os
import json

# Add root to path
sys.path.append(os.getcwd())

from src.database.models import get_session
from src.collectors.lotte import LotteCinemaCollector

def main():
    session = get_session()
    collector = LotteCinemaCollector(session)
    
    params = {
        "MethodName": "GetEventLists", 
        "channelType": "MW", 
        "osType": "W", 
        "osVersion": "Mozilla/5.0", 
        "EventClassificationCode": "0", 
        "PageNo": 1, 
        "PageSize": 20,
        "MemberNo": "0",
        "IsMemberYN": "N",
        "SearchText": ""
    }
    data = collector._make_request("GetEventLists", params)
    
    print("--- Response with MemberNo ---")
    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
    else:
        print("Response is None")

if __name__ == "__main__":
    main()
