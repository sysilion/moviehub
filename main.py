from src.utils.logger import get_logger
from dotenv import load_dotenv
import uvicorn
import os

load_dotenv()
logger = get_logger("Main")

if __name__ == "__main__":
    try:
        logger.info("Starting MovieHub Web & Scheduler Service...")
        # host="0.0.0.0"은 외부 접속(내부망 및 터널링)을 허용하는 설정입니다.
        uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        logger.info("Service stopped by user.")
