from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

class BaseCollector(ABC):
    def __init__(self, session: Session):
        self.session = session

    @abstractmethod
    def fetch_events(self, page: int = 1):
        """이벤트 목록을 가져옵니다."""
        pass

    @abstractmethod
    def fetch_event_detail(self, event_id: str):
        """이벤트 상세 정보를 가져옵니다."""
        pass

    @abstractmethod
    def fetch_inventory(self, event_id: str, gift_id: str):
        """특정 이벤트의 지점별 재고 정보를 가져옵니다."""
        pass

    @abstractmethod
    def save_event(self, event_data: dict, gift_id: str = None):
        """이벤트 정보를 데이터베이스에 저장합니다."""
        pass

    @abstractmethod
    def collect_target_inventory(self, event_id: str, gift_id: str):
        """대상 이벤트의 실시간 재고를 수집하여 저장합니다."""
        pass
