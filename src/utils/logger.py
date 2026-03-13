import logging
import sys

def get_logger(name):
    # FastAPI/Uvicorn 환경과 통합하기 위해 uvicorn.error 계층 구조 사용
    logger = logging.getLogger(f"uvicorn.error.{name}")
    
    # 상위 로거에서 핸들러가 이미 설정되어 있는지 확인 (uvicorn 실행 시)
    temp_logger = logger
    has_handlers = False
    while temp_logger:
        if temp_logger.handlers:
            has_handlers = True
            break
        if not temp_logger.propagate:
            break
        temp_logger = temp_logger.parent
        
    if not has_handlers:
        # 단독 스크립트 실행 등 uvicorn 외부 환경일 때만 직접 핸들러 설정
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        # uvicorn 스타일의 포맷 적용
        formatter = logging.Formatter('%(levelname)s:\t%(name)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger
