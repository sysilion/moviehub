from src.scheduler.main import start_scheduler
from src.utils.logger import get_logger
from dotenv import load_dotenv
import os

load_dotenv()
logger = get_logger("Main")

if __name__ == "__main__":
    try:
        logger.info("Starting MovieHub Service...")
        start_scheduler()
    except KeyboardInterrupt:
        logger.info("Service stopped by user.")