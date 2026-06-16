import re
from datetime import datetime

import requests

from src.collectors.base import BaseCollector
from src.utils.logger import get_logger

logger = get_logger("CineQCollector")


def _parse_date(date_str) -> str | None:
    if not date_str:
        return None
    try:
        return datetime.strptime(str(date_str)[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


class CineQCollector(BaseCollector):
    BASE_URL = "https://api.cineq.co.kr/api/v1/Movie/GetEvent"
    DETAIL_URL_TEMPLATE = "https://m.cineq.co.kr/event/{event_id}"

    HEADERS = {
        "accept": "*/*",
        "origin": "https://m.cineq.co.kr",
        "referer": "https://m.cineq.co.kr/",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36",
    }

    def _normalize_title(self, title):
        if not title:
            return ""
        match = re.search(r"<(.*?)>", title)
        if match:
            title = match.group(1)
        return re.sub(r"[^가-힣a-zA-Z0-9]", "", title)

    def _normalize(self, item) -> dict:
        event_id = str(item.get("eventId") or "")
        t_code = item.get("eventType")
        return {
            "EventID": event_id,
            "Operator": "CINEQ",
            "EventName": item.get("eventTitle") or "",
            "EventTypeName": "굿즈증정" if t_code == 2 else "이벤트",
            "ProgressStartDate": _parse_date(item.get("startDate")),
            "ProgressEndDate": _parse_date(item.get("endDate")),
            "ImageUrl": item.get("thumbnail") or None,
            "DetailImageUrl": item.get("contents") or None,
            "DetailUrl": self.DETAIL_URL_TEMPLATE.format(event_id=event_id) if event_id else None,
        }

    def collect_events(self) -> list[dict]:
        logger.info("CineQ: collecting events...")
        try:
            response = requests.get(self.BASE_URL, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            raw_data = response.json()
        except Exception as e:
            logger.error(f"CineQ API fetch failed: {e}")
            return []

        if not raw_data or "data" not in raw_data:
            return []

        seen_ids: set[str] = set()
        results: list[dict] = []

        items = raw_data["data"]
        # eventType==1 은 일반 이벤트, eventType==2 는 굿즈 재고 정보
        # 두 타입 모두 이벤트로 수집하되 중복(같은 eventId)은 제외
        for item in items:
            e_id = str(item.get("eventId") or "")
            if not e_id or e_id in seen_ids:
                continue
            seen_ids.add(e_id)
            results.append(self._normalize(item))

        logger.info(f"CineQ: collected {len(results)} events")
        return results
