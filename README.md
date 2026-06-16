# MovieHub — 영화관 이벤트 모아보기

롯데시네마, CGV, 메가박스, 씨네Q 4대 영화관의 진행 중 이벤트를 하나의 페이지에서 통합해서 볼 수 있는 정적 사이트입니다.

🌐 **사이트**: https://sysilion.github.io/moviehub/

## 주요 기능

- **통합 이벤트 목록**: 4대 영화관 이벤트를 한 화면에서 확인
- **실시간 필터**: 영화관별 버튼 / 제목 검색 / 종료 이벤트 토글
- **자동 갱신**: 국내 Mac에서 매 시간 정각에 크롤링 → GitHub Pages에 자동 반영
- **신규 이벤트 알림**: 새로운 이벤트 발견 시 텔레그램 알림 발송 (필터 설정 가능)

## 아키텍처

```
[국내 Mac, launchd 매시간]
  tools/refresh_events.py
    ↓ 4개 영화관 API 크롤
    ↓ docs/data/events.json 병합 (기존 이벤트 보존)
    ↓ 신규 이벤트 텔레그램 알림
    ↓ git commit & push

[GitHub repo/docs/] → GitHub Pages
  docs/index.html       정적 셸 + 클라이언트 JS
  docs/data/events.json 매시간 갱신되는 통합 이벤트 데이터
```

> **국내 IP 필요**: 한국 영화관 API는 해외 클라우드 IP를 차단하므로 크롤링은
> 반드시 국내 네트워크 환경에서 실행해야 합니다.

## 설치

```bash
pip install -r requirements.txt
```

## 환경 변수 (`.env`)

```env
# 텔레그램 알림 (선택)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# 알림 필터 (비워두면 전체 알림)
# NOTIFY_OPERATORS=LOTTE,CGV      # 특정 영화관만 알림
# NOTIFY_KEYWORDS=증정,뱃지,아트카드  # 키워드 포함 이벤트만 알림
```

## 수동 실행

```bash
# 이벤트 갱신 및 GitHub push
python3 tools/refresh_events.py
```

## 매시간 자동 실행 설정 (Mac launchd)

```bash
# plist 복사
cp com.moviehub.refresh.plist ~/Library/LaunchAgents/

# launchd에 등록
launchctl load ~/Library/LaunchAgents/com.moviehub.refresh.plist

# 즉시 테스트 실행
launchctl start com.moviehub.refresh

# 제거
launchctl unload ~/Library/LaunchAgents/com.moviehub.refresh.plist
```

## 프로젝트 구조

```
src/
└── collectors/   # 영화관별 이벤트 수집기 (DB 없음, dict 반환)
    ├── base.py
    ├── lotte.py
    ├── cgv.py
    ├── megabox.py
    └── cineq.py
src/utils/        # 로거, 텔레그램 알림, 설정
tools/
└── refresh_events.py  # 수집 → 병합 → commit/push 메인 스크립트
docs/
├── index.html         # 정적 사이트 (단일 파일)
└── data/events.json   # 매시간 갱신되는 이벤트 데이터
```

## events.json 스키마

```json
[
  {
    "EventID": "string",
    "Operator": "LOTTE | CGV | MEGABOX | CINEQ",
    "EventName": "string",
    "EventTypeName": "string | null",
    "ProgressStartDate": "YYYY-MM-DD | null",
    "ProgressEndDate": "YYYY-MM-DD | null",
    "ImageUrl": "string | null",
    "DetailImageUrl": "string | null",
    "DetailUrl": "string | null",
    "FirstSeen": "ISO8601 datetime"
  }
]
```
