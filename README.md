# MovieHub - 영화 굿즈 재고 트래커

영화관(롯데시네마, CGV, 메가박스, 씨네Q)의 이벤트 및 굿즈 재고를 실시간으로 추적하고 알림을 보내는 시스템입니다.

## 주요 기능
- **실시간 재고 추적**: 주요 4대 영화관의 이벤트 굿즈 수량을 자동으로 모니터링합니다.
- **스마트 알림**: 재고 신규 발견, 품절, 재입고 발생 시 텔레그램으로 즉시 알림을 전송합니다.
- **데이터 시각화**: 각 지점별 재고 변동 이력을 그래프로 확인할 수 있습니다.
- **자동 탐색**: 새로운 이벤트와 굿즈 번호를 자동으로 스캔하여 등록합니다.

## 기술 스택
- **Backend**: FastAPI, SQLAlchemy, Alembic (Database Migration)
- **Database**: PostgreSQL (Production), SQLite (Local/Test)
- **Frontend**: Jinja2 Templates, Bootstrap 5, Vercel Speed Insights
- **Scheduler**: Vercel Cron Jobs (Production), APScheduler (Local)
- **Settings**: Pydantic Settings (Environment Variable Management)

## 프로젝트 구조
```
src/
├── collectors/   # 각 영화관별 데이터 수집 로직
├── services/     # 비즈니스 로직 (이벤트 필터링, 조회 등)
├── database/     # DB 모델 및 엔진 설정
├── scheduler/    # 백그라운드 작업 관리 (Local용)
├── utils/        # 로그, 알림, 설정 등 공통 유틸리티
└── web/          # FastAPI 라우터 및 HTML 템플릿
```

## 설치 및 실행

### 1. 환경 변수 설정
`.env` 파일을 생성하고 다음 정보를 입력합니다.
```env
DATABASE_URL=postgresql://user:pass@host:port/db
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 2. 로컬 실행
```bash
# 의존성 설치
pip install -r requirements.txt

# DB 마이그레이션 및 앱 실행
PYTHONPATH=. python main.py
```

### 3. Vercel 배포
- Vercel에 프로젝트 연결 시 환경 변수를 설정합니다.
- `vercel.json` 설정을 통해 자동 크론 작업이 수행됩니다.

## 마이그레이션 관리 (Alembic)
스키마 변경 시 다음 명령어를 사용합니다.
```bash
# 마이그레이션 스크립트 생성
alembic revision --autogenerate -m "description"

# DB에 반영
alembic upgrade head
```
