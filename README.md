# MovieHub - 롯데시네마 굿즈 재고 추적 시스템

실시간으로 롯데시네마의 이벤트 굿즈(아트카드, 뱃지 등) 재고를 추적하고 시각화하는 모던 웹 서비스 및 지능형 스케줄러입니다.

## 주요 기능

### 1. 지능형 재고 수집 (Collectors)
*   **자동 탐색 및 매칭**: 신규 이벤트를 분석하여 최적의 굿즈 ID(GiftID)를 자동으로 매칭합니다.
*   **업데이트 최적화**: 이미 재고가 소진된 지점은 업데이트 대상에서 제외하여 효율적으로 운영됩니다.
*   **변동 이력 관리**: 수량이 변동될 때만 시계열 데이터를 기록하여 정밀한 추이를 제공합니다.

### 2. 고도화된 스케줄러 (Scheduler)
*   **이벤트별 개별 Job**: 각 이벤트가 독립된 주기로 업데이트되어 네트워크 지연 영향을 최소화합니다.
*   **초 단위 랜덤 주기**: 09:00 ~ 24:00 사이, 5~10분 간격의 랜덤한 초 단위 주기로 탐지 패턴을 분산합니다.

### 3. 모던 다크 UI (Web UI)
*   **Modern Dark Theme**: 시각적 피로도를 낮춘 세련된 다크 모드를 지원합니다.
*   **가로형 배너 최적화**: 이벤트 리스트에 최적화된 배너형 카드 레이아웃을 제공합니다.
*   **수량 변동 차트**: 지점별 재고 변화를 그라데이션이 적용된 아름다운 라인 차트로 시각화합니다.
*   **사용자 친화적 표기**: '50개 이상', '개 이하', '소진' 등 직관적인 상태 메시지를 사용합니다.

## 기술 스택
*   **Backend**: Python, FastAPI, SQLAlchemy
*   **Frontend**: Bootstrap 5 (Dark Mode), Chart.js, Pretendard Font
*   **Scheduler**: APScheduler (Background Mode)
*   **Database**: SQLite

## 설치 및 실행

### 패키지 설치
```bash
pip install -r requirements.txt
```

### 서비스 실행
```bash
python main.py
```
*   접속 주소: `http://localhost:8000` (Tailscale 환경 시 `http://bizu-macbookpro:8000`)

## 데이터베이스 구조
*   `events`: 이벤트 상세 정보 및 매칭된 GiftID
*   `inventory`: 지점별 최신 재고 현황 및 지역명
*   `inventory_history`: 수량 변동 이력 데이터 (차트 시각화용)
