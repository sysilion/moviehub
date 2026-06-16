from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Telegram Notifier
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # 알림 필터: 쉼표 구분 운영사 목록 (비어 있으면 전체)
    # 예: "LOTTE,CGV"
    NOTIFY_OPERATORS: Optional[str] = None

    # 알림 필터: 쉼표 구분 키워드 목록 (비어 있으면 전체)
    # 예: "증정,뱃지,아트카드"
    NOTIFY_KEYWORDS: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def notify_operators_list(self) -> list[str]:
        if not self.NOTIFY_OPERATORS:
            return []
        return [op.strip().upper() for op in self.NOTIFY_OPERATORS.split(",") if op.strip()]

    @property
    def notify_keywords_list(self) -> list[str]:
        if not self.NOTIFY_KEYWORDS:
            return []
        return [kw.strip() for kw in self.NOTIFY_KEYWORDS.split(",") if kw.strip()]


settings = Settings()
