# MovieHub 코드 분석 리포트

> 생성일: 2026-06-24

## 프로젝트 개요

- **언어**: Python 3.12+ / HTML+JS (단일 파일)
- **구조**: 정적 사이트 (v2) — 로컬 Mac 크롤러 → GitHub Pages
- **의존성**: `requests`, `python-dotenv`, `pydantic-settings` (최소화)

---

## 🔴 HIGH — 즉시 수정 필요

### 1. 테스트 전체가 v1 잔재로 실행 불가 (`tests/`)

**영향**: 모든 테스트 파일 5개

```
conftest.py  → src.database.models, src.web.app (존재하지 않음)
test_web.py, test_cinema_pages.py, test_lotte_collector.py
test_security.py, test_performance.py
→ SQLAlchemy Event/Inventory 모델, FastAPI TestClient, APScheduler 의존
```

프로젝트가 FastAPI+SQLite(v1) → 정적 사이트(v2)로 전환됐지만 테스트는 v1 기준 그대로. **`pytest` 실행 시 ImportError로 즉시 실패**함.

**권고**: v2 구조에 맞게 테스트 재작성 (수집기 단위 테스트, `events.json` 스키마 검증)

---

### 2. `report.py` — 삭제된 모듈 참조

```python
# report.py:1
from src.database.models import get_session, Event, Inventory
```

v1 DB 레이어 참조. 실행하면 `ModuleNotFoundError`. README나 진입점에서 노출되면 혼란 유발.

**권고**: 파일 삭제 또는 새 구조(`events.json` 기반)로 대체

---

## 🟠 MEDIUM — 기술적 부채

### 3. `src/utils/logger.py` — 죽은 코드 2건

```python
# uvicorn 없는데 uvicorn.error 네임스페이스 사용
logger = logging.getLogger(f"uvicorn.error.{name}")

# apscheduler 의존성도 없는데 레벨 설정
aps_logger = logging.getLogger("apscheduler")
aps_logger.setLevel(logging.WARNING)
```

단독 스크립트(`refresh_events.py`)만 남아 있으므로 표준 `logging.getLogger(name)` 으로 충분.

---

### 4. `MegaboxCollector` — `END` 수집 로직 버그

```python
# megabox.py:81-93
for status in ("ONG", "END"):
    ...
    if status == "ONG":
        break   # ← END는 절대 실행되지 않음
```

루프를 `("ONG", "END")`로 돌지만 ONG 처리 후 무조건 `break`. 종료 이벤트 수집이 의도라면 조건 수정 필요, 의도가 아니라면 루프 자체 제거.

---

### 5. `com.moviehub.refresh.plist` — 절대 경로 하드코딩

```xml
<string>/opt/homebrew/bin/python3</string>
<string>/Users/sysilion/proj/moviehub/tools/refresh_events.py</string>
```

`homebrew` Python 경로와 사용자 홈 경로가 고정. 환경이 바뀌면 silent failure.

**권고**: `ProgramArguments`를 셸 래퍼 스크립트로 교체하거나 `which python3` 기반으로 변경

---

### 6. CGV `SIGNATURE_SECRET` 소스코드 하드코딩

```python
# cgv.py:22
SIGNATURE_SECRET = "ydqXY0ocnFLmJGHr_zNzFcpjwAsXq_8JcBNURAkRscg"
```

공개 API 서명 키라도 소스에 직접 노출하면 git 히스토리에 영구 기록됨. `.env`로 이동 권고.

---

## 🟡 LOW — 품질 개선

### 7. 아키텍처 문서-코드 불일치

- `pyproject.toml`에 없는 의존성을 테스트 코드가 참조: `sqlalchemy`, `fastapi`, `pytest-mock`, `uvicorn`
- `requirements.txt`에도 없음 → `pip install -r requirements.txt` 후 테스트 실행하면 즉시 실패

### 8. `events.json` 로컬 미존재 (DX 문제)

`docs/data/.gitkeep`만 커밋됨. 클론 직후 `docs/index.html`을 로컬에서 열면 fetch 실패. README에 초기 실행 방법이 있지만 명시적 안내 부족.

### 9. `server.log` 미 `.gitignore`

launchd stdout/stderr 출력 파일(`server.log`)이 `.gitignore`에 없을 경우 git에 추적될 수 있음.

---

## 📊 지표 요약

| 도메인 | 상태 | 주요 이슈 |
|--------|------|-----------|
| **코드 품질** | 🔴 위험 | 테스트 전량 broken, dead code 다수 |
| **보안** | 🟠 주의 | API 키 하드코딩 |
| **성능** | 🟢 양호 | 수집기 간 랜덤 지연, 캐시버스팅 fetch |
| **아키텍처** | 🟠 주의 | v1→v2 전환 후 잔재 미정리 |

---

## 권고 우선순위

1. **즉시**: `tests/`, `report.py` → v2 기준 재작성 or 삭제
2. **단기**: `MegaboxCollector` break 버그 수정, logger 정리
3. **중기**: `SIGNATURE_SECRET` `.env` 이동, plist 경로 유연화
