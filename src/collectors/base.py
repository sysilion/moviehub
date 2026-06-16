from abc import ABC, abstractmethod


class BaseCollector(ABC):
    """영화관 이벤트 수집기 베이스 클래스. DB 의존 없음."""

    @abstractmethod
    def collect_events(self) -> list[dict]:
        """이벤트 목록을 수집해 정규화된 dict 리스트로 반환합니다.

        반환 스키마:
            {
                "EventID": str,
                "Operator": "LOTTE" | "CGV" | "MEGABOX" | "CINEQ",
                "EventName": str,
                "EventTypeName": str | None,
                "ProgressStartDate": "YYYY-MM-DD" | None,
                "ProgressEndDate": "YYYY-MM-DD" | None,
                "ImageUrl": str | None,
                "DetailImageUrl": str | None,
                "DetailUrl": str | None,
            }
        """
        pass
