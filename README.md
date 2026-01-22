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
*   **강력한 검색 및 필터링**: 이벤트명 검색 기능과 종료된 이벤트 보기 필터를 제공하여 원하는 정보를 빠르게 찾을 수 있습니다.
*   **페이지네이션**: 대량의 이벤트 데이터도 페이지네이션을 통해 빠르고 쾌적하게 탐색할 수 있습니다.
*   **실시간 알림 (Toast)**: 업데이트 요청 결과 등 시스템의 주요 상태 변화를 세련된 토스트 메시지로 즉시 알려줍니다.

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

## 관리자 유틸리티 (Admin Tools)
자동 수집 외에 수동으로 데이터를 관리하거나 정밀 스캔이 필요할 때 사용하는 도구입니다.

### 1. 수동 이벤트 추가 (add_manual_event.py)
특정 이벤트 ID에 대해 지정된 범위의 GiftID를 스캔하여 추가합니다.
```bash
python add_manual_event.py [EventID] [StartGiftID] [EndGiftID]
# 예시: python add_manual_event.py 201010016926026 13800 13850
```

### 2. 누락 데이터 정밀 스캔 (scan_missing_events.py)
비어있는 GiftID 슬롯과 특정 이벤트 ID 범위를 교차 분석하여 누락된 매칭 정보를 찾아냅니다.
```bash
python scan_missing_events.py
```
