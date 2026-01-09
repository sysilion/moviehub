from src.utils.logger import get_logger
from dotenv import load_dotenv
import uvicorn
import os

load_dotenv()
logger = get_logger("Main")

if __name__ == "__main__":
    try:
        logger.info("Starting MovieHub Web & Scheduler Service...")
        # 웹 서버 실행 (FastAPI 앱 내에서 스케줄러 자동 시작됨)
        uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        logger.info("Service stopped by user.")