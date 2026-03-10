import uvicorn
import os
import signal
import sys
from dotenv import load_dotenv
from src.utils.logger import get_logger
from src.web.app import app # Vercel이 인식할 진입점

load_dotenv()
logger = get_logger("Main")

def handle_signal(sig, frame):
    logger.info(f"Received termination signal: {sig}. Exiting MovieHub...")
    sys.exit(0)

if __name__ == "__main__":
    # OS 신호 핸들러 등록 (SIGINT, SIGTERM)
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        logger.info("Starting MovieHub Web & Scheduler Service...")
        # host="0.0.0.0"은 외부 접속(내부망 및 터널링)을 허용하는 설정입니다.
        # reload=True는 개발용입니다. 
        # 운영 환경에서는 reload=False를 권장하며 worker 수를 조절할 수 있습니다.
        uvicorn.run(
            "src.web.app:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Service shut down complete.")
