import base64
import hashlib
import hmac
import re
import time
from datetime import datetime

import requests

from src.collectors.base import BaseCollector
from src.utils.logger import get_logger

logger = get_logger("CGVCollector")


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


class CGVCollector(BaseCollector):
    BASE_URL = "https://event-mobile.cgv.co.kr/evt/evt/evt/searchEvtListForPage"
    DETAIL_URL_TEMPLATE = "https://www.cgv.co.kr/culture-event/detail.aspx?eventId={event_id}"

    SIGNATURE_SECRET = "ydqXY0ocnFLmJGHr_zNzFcpjwAsXq_8JcBNURAkRscg"

    HEADERS_TEMPLATE = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json",
        "Origin": "https://cgv.co.kr",
        "Referer": "https://cgv.co.kr/",
    }

    def _generate_signature(self, path, body, timestamp):
        payload = f"{timestamp}|{path}|{body}"
        signature = hmac.new(
            self.SIGNATURE_SECRET.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(signature).decode("utf-8")

    def _signed_request(self, full_url, params=None):
        path = full_url.replace("https://event-mobile.cgv.co.kr", "").split("?")[0]
        ts = str(int(time.time()))
        sig = self._generate_signature(path, "", ts)

        headers = self.HEADERS_TEMPLATE.copy()
        headers.update({"X-TIMESTAMP": ts, "X-SIGNATURE": sig})

        response = requests.get(full_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def _normalize_title(self, title):
        if not title:
            return ""
        t = re.sub(r"[^가-힣a-zA-Z0-9]", "", title)
        t = t.replace("현장증정", "").replace("이벤트", "").replace("증정", "")
        return t

    def _normalize(self, item) -> dict:
        event_id = str(item.get("saprmEvntNo") or item.get("evntNo") or "")
        img = item.get("evtImgPath")
        image_url = None
        if img:
            image_url = f"https://img.cgv.co.kr{img}" if img.startswith("/") else img

        return {
            "EventID": event_id,
            "Operator": "CGV",
            "EventName": item.get("saprmEvntNm") or item.get("evntNm") or "",
            "EventTypeName": item.get("evntTypNm") or None,
            "ProgressStartDate": _parse_date(
                item.get("evntStartYmd") or item.get("evntStartDt") or item.get("saprmEvntStartYmd")
            ),
            "ProgressEndDate": _parse_date(
                item.get("evntEndYmd") or item.get("evntEndDt") or item.get("saprmEvntEndYmd")
            ),
            "ImageUrl": image_url,
            "DetailImageUrl": None,
            "DetailUrl": self.DETAIL_URL_TEMPLATE.format(event_id=event_id) if event_id else None,
        }

    def collect_events(self) -> list[dict]:
        logger.info("CGV: collecting events...")
        seen_ids: set[str] = set()
        results: list[dict] = []

        # 일반 이벤트 목록
        try:
            url = f"{self.BASE_URL}?coCd=A420&expoChnlCd=03&startRow=0&listCount=1000"
            data = self._signed_request(url)
            if data and "data" in data and "list" in data["data"]:
                for item in data["data"]["list"]:
                    e_id = str(item.get("evntNo") or "")
                    if not e_id or e_id in seen_ids:
                        continue
                    seen_ids.add(e_id)
                    results.append(self._normalize(item))
        except Exception as e:
            logger.error(f"CGV general events failed: {e}")

        logger.info(f"CGV: collected {len(results)} events")
        return results
