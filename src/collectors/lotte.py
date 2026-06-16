import json
from datetime import datetime

import requests

from src.collectors.base import BaseCollector
from src.utils.logger import get_logger

logger = get_logger("LotteCollector")


def _parse_date(date_str) -> str | None:
    if not date_str:
        return None
    clean = str(date_str).replace(".", "-")[:10]
    try:
        if "-" in clean:
            datetime.strptime(clean, "%Y-%m-%d")
            return clean
        else:
            d = datetime.strptime(clean, "%Y%m%d")
            return d.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


class LotteCinemaCollector(BaseCollector):
    BASE_URL = "https://www.lottecinema.co.kr/LCWS/Event/EventData.aspx"
    DETAIL_URL_TEMPLATE = "https://www.lottecinema.co.kr/NLCMW/Event/EventDetail?EventID={event_id}"

    HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundaryLotteCinema",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Origin": "https://www.lottecinema.co.kr",
        "Referer": "https://www.lottecinema.co.kr/NLCMW/Event",
    }

    def _make_request(self, method_name, params):
        boundary = "----WebKitFormBoundaryLotteCinema"
        headers = self.HEADERS.copy()
        param_list_json = json.dumps(params)
        body = f'--{boundary}\r\nContent-Disposition: form-data; name="paramList"\r\n\r\n{param_list_json}\r\n--{boundary}--\r\n'
        try:
            response = requests.post(
                self.BASE_URL, headers=headers, data=body.encode("utf-8"), timeout=15
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Request failed for {method_name}: {e}")
            return None

    def _fetch_events_page(self, page=1):
        params = {
            "MethodName": "GetEventLists",
            "channelType": "MW",
            "osType": "W",
            "osVersion": "Mozilla/5.0",
            "EventClassificationCode": "0",
            "SearchText": "",
            "CinemaID": "",
            "PageNo": page,
            "PageSize": 100,
            "MemberNo": "0",
        }
        return self._make_request("GetEventLists", params)

    def _normalize(self, item) -> dict:
        event_id = str(item.get("EventID", ""))
        return {
            "EventID": event_id,
            "Operator": "LOTTE",
            "EventName": item.get("EventName") or "",
            "EventTypeName": item.get("EventTypeName") or None,
            "ProgressStartDate": _parse_date(
                item.get("ProgressStartDate") or item.get("EventStartDate") or item.get("StartDate")
            ),
            "ProgressEndDate": _parse_date(
                item.get("ProgressEndDate") or item.get("EventEndDate") or item.get("EndDate")
            ),
            "ImageUrl": item.get("ListImgUrl") or item.get("ImageUrl") or None,
            "DetailImageUrl": item.get("ImgUrl") or item.get("DetailImageUrl") or None,
            "DetailUrl": self.DETAIL_URL_TEMPLATE.format(event_id=event_id) if event_id else None,
        }

    def collect_events(self) -> list[dict]:
        logger.info("Lotte Cinema: collecting events...")
        seen_ids: set[str] = set()
        results: list[dict] = []

        for page in range(1, 6):
            try:
                data = self._fetch_events_page(page=page)
                if not data or "Items" not in data:
                    break
                items = data["Items"]
                if not items:
                    break
                for item in items:
                    e_id = str(item.get("EventID", ""))
                    if not e_id or e_id in seen_ids:
                        continue
                    seen_ids.add(e_id)
                    results.append(self._normalize(item))
            except Exception as e:
                logger.error(f"Lotte page {page} failed: {e}")
                break

        logger.info(f"Lotte: collected {len(results)} events")
        return results
