# MovieHub Utility Tools

이 디렉토리는 롯데시네마 이벤트 데이터 수집 및 관리를 위한 보조 유틸리티 스크립트들을 포함합니다.

## 스크립트 목록 및 기능

### 1. 데이터 분석 및 확인
*   **analyze_event_gaps.py**: 수집된 `EventID` 간의 공백(Gap)을 분석하여 누락된 ID 구간을 찾아냅니다.
*   **check_gaps.py**: `Event` 정보는 존재하지만 실제 재고 데이터(`inventory`)가 연결되지 않은 항목들을 식별합니다.
*   **report_status.py**: 데이터베이스의 전반적인 수집 현황(총 이벤트 수, 재고 추적 중인 굿즈 목록)을 요약 보고합니다.

### 2. 데이터 수집 및 보정
*   **scan_events_range.py**: 특정 범위의 `EventID`와 `GiftID`를 지정하여 루프를 돌며 데이터를 강제 스캔합니다.
*   **scan_missing_events.py**: 분석을 통해 발견된 누락된 ID 구간에 대해 재수집을 시도합니다.
*   **add_manual_event.py**: 특정 `EventID`와 `GiftID`를 직접 입력하여 수동으로 데이터를 등록합니다.

## 실행 방법
모든 스크립트는 프로젝트 루트 디렉토리에서 가상환경의 Python을 사용하여 실행해야 합니다.
```bash
./.venv/bin/python3 tools/<스크립트명>.py
```
