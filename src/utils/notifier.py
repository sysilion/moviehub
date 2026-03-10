import os
import requests
from src.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_logger("Notifier")

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token and self.chat_id)
        if not self.enabled:
            logger.warning("Telegram Bot Token or Chat ID not found in environment variables.")

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
            logger.info("Notification sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

notifier = TelegramNotifier()
