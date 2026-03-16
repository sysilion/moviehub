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
        logger.info("Initializing MovieHub Service...")
        
        # 앱 시작 전 DB 초기화 및 마이그레이션 실행 (동기 방식)
        from src.database.models import init_db, run_migrations
        try:
            logger.info("Initializing database schema...")
            init_db()
            logger.info("Running database migrations...")
            run_migrations()
            logger.info("Database initialization complete.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # 마이그레이션 실패 시에도 일단 서버 실행을 시도할지 여부는 정책에 따라 결정
            # 여기서는 계속 진행합니다.

        logger.info("Starting MovieHub Web & Scheduler Service...")
        # host="0.0.0.0"은 외부 접속(내부망 및 터널링)을 허용하는 설정입니다.
        uvicorn.run(
            "src.web.app:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Service shut down complete.")
