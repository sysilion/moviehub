#!/usr/bin/env python3
"""
MovieHub 이벤트 갱신 스크립트

동작:
  1. git pull --rebase 로 원격 최신화
  2. docs/data/events.json 기존 데이터 로드 (없으면 빈 리스트)
  3. 4개 영화관 컬렉터로 이벤트 수집
  4. (Operator, EventID) 키로 upsert 병합 (종료 이벤트도 보존)
  5. 신규 이벤트 텔레그램 알림 (필터 적용)
  6. events.json 저장 → git commit & push (변경 있을 때만)

국내 Mac에서 launchd 매시간 실행 용도.
"""
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone

# 프로젝트 루트를 sys.path에 추가
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.collectors.cgv import CGVCollector
from src.collectors.cineq import CineQCollector
from src.collectors.lotte import LotteCinemaCollector
from src.collectors.megabox import MegaboxCollector
from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.notifier import notifier

logger = get_logger("RefreshEvents")

DATA_FILE = os.path.join(ROOT, "docs", "data", "events.json")


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def run_cmd(cmd: list[str], check=True, capture=False) -> subprocess.CompletedProcess:
    kwargs = dict(cwd=ROOT)
    if capture:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    result = subprocess.run(cmd, **kwargs)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result


def git_pull():
    logger.info("git pull --rebase...")
    try:
        run_cmd(["git", "pull", "--rebase", "--autostash"])
    except Exception as e:
        logger.warning(f"git pull failed (continuing anyway): {e}")


def git_push(new_count: int, updated_count: int):
    """변경이 있을 때만 commit & push."""
    # 변경 여부 확인
    result = run_cmd(
        ["git", "diff", "--quiet", "docs/data/events.json"],
        check=False
    )
    if result.returncode == 0:
        logger.info("events.json: no changes, skipping commit")
        return

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    msg = f"data: refresh events {now_str} (+{new_count} new, {updated_count} updated)"
    run_cmd(["git", "add", DATA_FILE])
    run_cmd(["git", "commit", "-m", msg])
    run_cmd(["git", "push"])
    logger.info(f"Pushed: {msg}")


# ---------------------------------------------------------------------------
# JSON persistence
# ---------------------------------------------------------------------------

def load_events() -> dict[str, dict]:
    """(Operator, EventID) → event dict 인덱스로 반환."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            items: list[dict] = json.load(f)
        return {_key(e): e for e in items if e.get("EventID")}
    except Exception as e:
        logger.warning(f"Failed to load {DATA_FILE}: {e}")
        return {}


def save_events(index: dict[str, dict]):
    events = list(index.values())
    # 정렬: 운영사 → 시작일 내림차순 → EventID
    events.sort(key=lambda e: (
        e.get("Operator", ""),
        -(int((e.get("ProgressStartDate") or "0000-00-00").replace("-", "")) or 0),
        e.get("EventID", ""),
    ))
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(events)} events to {DATA_FILE}")


def _key(event: dict) -> str:
    return f"{event.get('Operator','')}__{event.get('EventID','')}"


# ---------------------------------------------------------------------------
# 알림 필터
# ---------------------------------------------------------------------------

def _should_notify(event: dict) -> bool:
    ops = settings.notify_operators_list
    if ops and event.get("Operator", "").upper() not in ops:
        return False
    kws = settings.notify_keywords_list
    if kws:
        name = event.get("EventName", "").lower()
        return any(kw.lower() in name for kw in kws)
    return True


def _send_new_event_notification(event: dict):
    op = event.get("Operator", "")
    name = event.get("EventName", "")
    start = event.get("ProgressStartDate", "")
    end = event.get("ProgressEndDate", "")
    detail_url = event.get("DetailUrl", "")
    period = ""
    if start or end:
        period = f"\n📅 {start or '?'} ~ {end or '?'}"
    link = f"\n🔗 {detail_url}" if detail_url else ""
    text = f"🎬 <b>[{op}] 새 이벤트 발견!</b>\n{name}{period}{link}"
    try:
        notifier.send_message(text)
    except Exception as e:
        logger.warning(f"Telegram notify failed: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    logger.info("=== refresh_events.py started ===")

    git_pull()

    existing = load_events()
    logger.info(f"Existing events: {len(existing)}")

    collectors = [
        ("LOTTE", LotteCinemaCollector),
        ("CGV", CGVCollector),
        ("MEGABOX", MegaboxCollector),
        ("CINEQ", CineQCollector),
    ]
    random.shuffle(collectors)

    new_count = 0
    updated_count = 0
    first_seen_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for name, cls in collectors:
        try:
            logger.info(f"[{name}] collecting...")
            events = cls().collect_events()
            logger.info(f"[{name}] got {len(events)} events")

            for ev in events:
                k = _key(ev)
                if k not in existing:
                    # 신규 이벤트
                    ev["FirstSeen"] = first_seen_ts
                    existing[k] = ev
                    new_count += 1
                    if _should_notify(ev):
                        _send_new_event_notification(ev)
                else:
                    # 기존 이벤트: 정보 업데이트 (FirstSeen 보존)
                    preserved = existing[k].get("FirstSeen")
                    existing[k].update(ev)
                    if preserved:
                        existing[k]["FirstSeen"] = preserved
                    updated_count += 1

        except Exception as e:
            logger.error(f"[{name}] collector failed: {e}")

        # 운영사 간 지연 (서버 부하 방지)
        time.sleep(random.uniform(3, 8))

    logger.info(f"Merge done: {new_count} new, {updated_count} updated")

    save_events(existing)
    git_push(new_count, updated_count)

    logger.info("=== refresh_events.py done ===")


if __name__ == "__main__":
    main()
