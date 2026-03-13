from abc import ABC, abstractmethod
import requests
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger("Notifier")

class BaseNotifier(ABC):
    @abstractmethod
    def send_message(self, text: str):
        pass

class TelegramNotifier(BaseNotifier):
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = bool(self.token and self.chat_id)
        if not self.enabled:
            logger.warning("Telegram Bot Token or Chat ID not configured.")

    def send_message(self, text: str):
        if not self.enabled:
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

class CompositeNotifier(BaseNotifier):
    def __init__(self, notifiers: list[BaseNotifier]):
        self.notifiers = notifiers

    def send_message(self, text: str):
        for notifier in self.notifiers:
            notifier.send_message(text)

# 기본 알림 객체 생성
_telegram = TelegramNotifier()
notifier = CompositeNotifier([_telegram])
