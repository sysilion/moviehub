# MovieHub

롯데시네마 굿즈 및 이벤트 트래킹 시스템

## 주요 기능
- 롯데시네마 이벤트 목록 및 상세 정보 수집
- 굿즈(아트카드, 키링 등) 재고 현황 실시간 트래킹
- GiftID 자동 스캔 알고리즘 탑재
- 워킹 타임 기반 지능형 스케줄링 (09:00 ~ 18:00 집중 모니터링)

## 설치 및 실행

1. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```

2. 서비스 실행:
   ```bash
   python main.py
   ```

## 기술 스택
- Python 3.x
- SQLAlchemy (ORM)
- SQLite (Local DB)
- APScheduler (Task Scheduling)
- Requests (API Integration)
