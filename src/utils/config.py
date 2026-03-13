from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: Optional[str] = None
    
    # Telegram Notifier
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    # Environment
    VERCEL: Optional[str] = "0"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_vercel(self) -> bool:
        return self.VERCEL == "1"

    @property
    def final_db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.is_vercel:
            return "sqlite:////tmp/moviehub.db"
        return "sqlite:///moviehub.db"

settings = Settings()
