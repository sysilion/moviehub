from datetime import datetime

import requests

from src.collectors.base import BaseCollector
from src.utils.logger import get_logger

logger = get_logger("MegaboxCollector")


def _parse_date(date_str) -> str | None:
    if not date_str:
        return None
    try:
        clean = str(date_str).replace(".", "-")[:10]
        datetime.strptime(clean, "%Y-%m-%d")
        return clean
    except (ValueError, TypeError):
        return None


class MegaboxCollector(BaseCollector):
    BASE_URL = "https://www.megabox.co.kr/on/oh/ohe/Event/selectEventList.do"
    DETAIL_URL_TEMPLATE = "https://www.megabox.co.kr/event/detail?eventNo={event_id}"

    HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        "Referer": "https://m.megabox.co.kr/event",
    }

    CATEGORY_MAP = {
        "CED01": "영화",
        "CED02": "극장",
        "CED03": "굿즈/메가Pick",
        "CED04": "시사회/무대인사",
        "CED05": "제휴/할인",
    }

    def _fetch_events(self, status="ONG"):
        payload = {
            "currentPage": "1",
            "recordCountPerPage": "200",
            "eventStatCd": status,
        }
        try:
            response = requests.post(
                self.BASE_URL, data=payload, headers=self.HEADERS, timeout=15
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Megabox API fetch failed (status={status}): {e}")
            return None

    def _normalize(self, item) -> dict:
        event_id = str(item.get("eventNo") or "")
        img_base = "https://img.megabox.co.kr"
        img_path = item.get("moFilePathNm") or item.get("pcFilePathNm")
        image_url = (img_base + img_path) if img_path else None

        div_cd = item.get("eventDivCd")

        return {
            "EventID": event_id,
            "Operator": "MEGABOX",
            "EventName": item.get("eventTitle") or "",
            "EventTypeName": self.CATEGORY_MAP.get(div_cd, "이벤트"),
            "ProgressStartDate": _parse_date(item.get("eventStartDt")),
            "ProgressEndDate": _parse_date(item.get("eventEndDt")),
            "ImageUrl": image_url,
            "DetailImageUrl": None,
            "DetailUrl": self.DETAIL_URL_TEMPLATE.format(event_id=event_id) if event_id else None,
        }

    def collect_events(self) -> list[dict]:
        logger.info("Megabox: collecting events...")
        seen_ids: set[str] = set()
        results: list[dict] = []

        for status in ("ONG", "END"):
            data = self._fetch_events(status=status)
            if not data or "eventDivList" not in data:
                continue
            for item in data["eventDivList"]:
                e_id = str(item.get("eventNo") or "")
                if not e_id or e_id in seen_ids:
                    continue
                seen_ids.add(e_id)
                results.append(self._normalize(item))
            # 진행 중 이벤트(ONG)만으로 충분하면 여기서 멈춰도 됨
            if status == "ONG":
                break

        logger.info(f"Megabox: collected {len(results)} events")
        return results
