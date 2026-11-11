#!/usr/bin/env python3
"""Invitation codes, student users, and access logs for the mock exam."""

from __future__ import annotations

import fcntl
import json
import os
import re
import secrets
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

TZ_SHANGHAI = timezone(timedelta(hours=8))

ACCESS_LOG_CAP = 5000
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

_DATA_DIR: Path | None = None

WRITING_MODES = {"full", "task1", "task2"}
READING_MODES = {"full", "passage1", "passage2", "passage3"}
SPEAKING_MODES = {"full", "topic"}
MODULES = {"writing", "reading", "speaking"}
MODULE_MODES = {
    "writing": WRITING_MODES,
    "reading": READING_MODES,
    "speaking": SPEAKING_MODES,
}


class AccessError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


class CodeExistsError(AccessError):
    def __init__(self, message: str = "该邀请码已存在。"):
        super().__init__(message, 400)


def bind(data_dir: Path | str) -> None:
    global _DATA_DIR
    _DATA_DIR = Path(data_dir)
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def data_dir() -> Path:
    if _DATA_DIR is None:
        bind(Path(__file__).resolve().parent / "data")
    assert _DATA_DIR is not None
    return _DATA_DIR


def now_iso() -> str:
    return datetime.now(TZ_SHANGHAI).isoformat(timespec="seconds")


def normalize_code(code: str | None) -> str:
    return (code or "").strip().upper()


def normalize_name(name: str | None) -> str:
    return " ".join((name or "").split()).casefold()


def codes_path() -> Path:
    return data_dir() / "invite_codes.json"


def users_path() -> Path:
    return data_dir() / "users.json"


def log_path() -> Path:
    return data_dir() / "access_log.json"


def lock_path() -> Path:
    return data_dir() / ".access.lock"


@contextmanager
def _locked() -> Iterator[None]:
    data_dir().mkdir(parents=True, exist_ok=True)
    path = lock_path()
    with path.open("a", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return json.loads(json.dumps(default))
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return json.loads(json.dumps(default))


def load_codes() -> dict:
    data = _load_json(codes_path(), {"codes": []})
    data.setdefault("codes", [])
    return data


def load_users() -> dict:
    data = _load_json(users_path(), {"users": []})
    data.setdefault("users", [])
    return data


def load_log() -> dict:
    data = _load_json(log_path(), {"events": []})
    data.setdefault("events", [])
    return data


def save_codes(data: dict) -> None:
    atomic_write_json(codes_path(), data)


def save_users(data: dict) -> None:
    atomic_write_json(users_path(), data)


def save_log(data: dict) -> None:
    events = data.get("events") or []
    if len(events) > ACCESS_LOG_CAP:
        data["events"] = events[-ACCESS_LOG_CAP:]
    atomic_write_json(log_path(), data)


def generate_code() -> str:
    raw = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"


def find_code(store: dict, code: str | None) -> dict | None:
    key = normalize_code(code)
    if not key:
        return None
    for item in store.get("codes") or []:
        if normalize_code(item.get("code")) == key:
            return item
    return None


def get_code_by_id(store: dict, code_id: str | None) -> dict | None:
    if not code_id:
        return None
    for item in store.get("codes") or []:
        if item.get("id") == code_id:
            return item
    return None


def code_is_usable(item: dict | None) -> bool:
    if not item or not item.get("enabled"):
        return False
    max_uses = item.get("max_uses")
    if max_uses is None:
        return True
    try:
        limit = int(max_uses)
    except (TypeError, ValueError):
        return False
    return int(item.get("use_count") or 0) < limit


def create_code(
    code: str | None = None,
    note: str = "",
    max_uses: int | None = None,
    created_by: str = "",
) -> dict:
    typed = (code or "").strip()
    if typed:
        if len(normalize_code(typed)) < 4:
            raise AccessError("邀请码至少 4 个字符。")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,31}", typed):
            raise AccessError("邀请码仅可使用字母、数字、连字符或下划线。")
    with _locked():
        store = load_codes()
        value = typed or generate_code()
        # Avoid accidental collisions when generating.
        if not typed:
            for _ in range(8):
                if find_code(store, value) is None:
                    break
                value = generate_code()
        if find_code(store, value) is not None:
            raise CodeExistsError()
        rec = {
            "id": str(uuid.uuid4()),
            "code": value,
            "enabled": True,
            "note": (note or "").strip(),
            "max_uses": max_uses,
            "use_count": 0,
            "created_at": now_iso(),
            "created_by": (created_by or "").strip(),
        }
        store.setdefault("codes", []).insert(0, rec)
        save_codes(store)
        return rec


def set_code_enabled(code_id: str, enabled: bool) -> dict | None:
    with _locked():
        store = load_codes()
        rec = get_code_by_id(store, code_id)
        if not rec:
            return None
        rec["enabled"] = bool(enabled)
        save_codes(store)
        return rec


def list_codes() -> list[dict]:
    return list(load_codes().get("codes") or [])


def list_users() -> list[dict]:
    users = list(load_users().get("users") or [])
    users.sort(key=lambda u: u.get("last_seen") or "", reverse=True)
    return users


def list_events(limit: int = 200) -> list[dict]:
    events = list(load_log().get("events") or [])
    events.reverse()
    if limit and len(events) > limit:
        return events[:limit]
    return events


def _append_event_unlocked(event: dict) -> None:
    log = load_log()
    log.setdefault("events", []).append(event)
    save_log(log)


def _client_meta(ip: str | None, user_agent: str | None) -> tuple[str, str]:
    ip_val = (ip or "").strip()
    if "," in ip_val:
        ip_val = ip_val.split(",", 1)[0].strip()
    ua = (user_agent or "").strip()
    if len(ua) > 240:
        ua = ua[:239] + "…"
    return ip_val, ua


def log_denied(
    *,
    candidate_name: str = "",
    module: str = "",
    mode: str = "",
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    ip_val, ua = _client_meta(ip, user_agent)
    with _locked():
        log = load_log()
        events = log.get("events") or []
        # Avoid flooding: skip if the same IP was already denied in the last minute.
        cutoff = datetime.now(TZ_SHANGHAI) - timedelta(minutes=1)
        for ev in reversed(events[-20:]):
            if ev.get("action") != "denied" or ev.get("ip") != ip_val:
                continue
            try:
                ts = datetime.fromisoformat(str(ev.get("timestamp") or ""))
            except ValueError:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=TZ_SHANGHAI)
            if ts >= cutoff:
                return
            break
        events.append(
            {
                "id": str(uuid.uuid4()),
                "timestamp": now_iso(),
                "action": "denied",
                "candidate_name": (candidate_name or "").strip(),
                "user_id": None,
                "invite_code_id": None,
                "module": module,
                "mode": mode,
                "ip": ip_val,
                "user_agent": ua,
            }
        )
        log["events"] = events
        save_log(log)


def _user_key(name: str, code_id: str) -> str:
    return f"{normalize_name(name)}::{code_id}"


def _find_user(store: dict, name: str, code_id: str) -> dict | None:
    key = _user_key(name, code_id)
    for item in store.get("users") or []:
        if item.get("key") == key:
            return item
        if item.get("invite_code_id") == code_id and normalize_name(item.get("name")) == normalize_name(name):
            return item
    return None


def start_student(
    *,
    candidate_name: str | None,
    invite_code: str | None,
    module: str | None,
    mode: str | None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> dict:
    name = " ".join((candidate_name or "").split())
    if not name:
        raise AccessError("请输入姓名", 400)
    if not (invite_code or "").strip():
        raise AccessError("请输入邀请码", 400)

    module_key = (module or "").strip().lower()
    if module_key not in MODULES:
        raise AccessError("请选择模考科目", 400)

    mode_key = (mode or "full").strip().lower()
    allowed = MODULE_MODES.get(module_key, {"full"})
    if mode_key not in allowed:
        mode_key = "full"

    ip_val, ua = _client_meta(ip, user_agent)

    with _locked():
        codes = load_codes()
        rec = find_code(codes, invite_code)
        if not code_is_usable(rec):
            # Denied logging is best-effort and happens after release via log_denied,
            # but we still want it consistent. Do it here under the same lock.
            log = load_log()
            events = log.get("events") or []
            should_log = True
            cutoff = datetime.now(TZ_SHANGHAI) - timedelta(minutes=1)
            for ev in reversed(events[-20:]):
                if ev.get("action") != "denied" or ev.get("ip") != ip_val:
                    continue
                try:
                    ts = datetime.fromisoformat(str(ev.get("timestamp") or ""))
                except ValueError:
                    continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=TZ_SHANGHAI)
                if ts >= cutoff:
                    should_log = False
                break
            if should_log:
                events.append(
                    {
                        "id": str(uuid.uuid4()),
                        "timestamp": now_iso(),
                        "action": "denied",
                        "candidate_name": name,
                        "user_id": None,
                        "invite_code_id": None,
                        "module": module_key,
                        "mode": mode_key,
                        "ip": ip_val,
                        "user_agent": ua,
                    }
                )
                log["events"] = events
                save_log(log)
            raise AccessError("邀请码无效或已失效", 403)

        assert rec is not None
        rec["use_count"] = int(rec.get("use_count") or 0) + 1
        save_codes(codes)

        users = load_users()
        user = _find_user(users, name, rec["id"])
        ts = now_iso()
        if user is None:
            user = {
                "id": str(uuid.uuid4()),
                "key": _user_key(name, rec["id"]),
                "name": name,
                "invite_code_id": rec["id"],
                "invite_code": rec.get("code") or "",
                "first_seen": ts,
                "last_seen": ts,
                "start_count": 1,
                "writing_started": 0,
                "writing_submitted": 0,
                "reading_started": 0,
                "reading_submitted": 0,
                "last_submission_id": None,
                "last_writing_submission_id": None,
                "last_reading_submission_id": None,
            }
            users.setdefault("users", []).insert(0, user)
        else:
            user["name"] = name
            user["invite_code"] = rec.get("code") or user.get("invite_code") or ""
            user["last_seen"] = ts
            user["start_count"] = int(user.get("start_count") or 0) + 1
            if not user.get("first_seen"):
                user["first_seen"] = ts
        started_field = f"{module_key}_started"
        user[started_field] = int(user.get(started_field) or 0) + 1
        save_users(users)

        log = load_log()
        log.setdefault("events", []).append(
            {
                "id": str(uuid.uuid4()),
                "timestamp": ts,
                "action": "start",
                "candidate_name": name,
                "user_id": user["id"],
                "invite_code_id": rec["id"],
                "module": module_key,
                "mode": mode_key,
                "ip": ip_val,
                "user_agent": ua,
            }
        )
        save_log(log)

        return {
            "ok": True,
            "user_id": user["id"],
            "candidate_name": name,
            "invite_code_id": rec["id"],
            "module": module_key,
            "mode": mode_key,
        }


def get_code(code_id: str | None) -> dict | None:
    return get_code_by_id(load_codes(), code_id)


def get_user(user_id: str | None) -> dict | None:
    if not user_id:
        return None
    for item in load_users().get("users") or []:
        if item.get("id") == user_id:
            return item
    return None


def session_is_valid(sess: dict) -> bool:
    if not sess.get("student_ok"):
        return False
    if not (sess.get("student_name") or "").strip():
        return False
    rec = get_code(sess.get("invite_code_id"))
    if not rec or not rec.get("enabled"):
        return False
    return True


def resolve_student(
    sess: dict,
    *,
    candidate_name: str | None = None,
    invite_code: str | None = None,
    module: str | None = None,
) -> dict:
    """Return student identity from a live session, or from a still-valid invite code."""
    if session_is_valid(sess):
        name = (sess.get("student_name") or "").strip()
        return {
            "user_id": sess.get("student_user_id"),
            "candidate_name": name,
            "invite_code_id": sess.get("invite_code_id"),
            "module": sess.get("student_module") or module,
        }

    name = " ".join((candidate_name or "").split())
    if not name:
        raise AccessError("请填写姓名", 400)
    if not (invite_code or "").strip():
        raise AccessError("请先使用有效邀请码开始模考", 403)

    with _locked():
        rec = find_code(load_codes(), invite_code)
        if not code_is_usable(rec) and not (rec and rec.get("enabled")):
            raise AccessError("请先使用有效邀请码开始模考", 403)
        # Allow submit with an enabled code even if max_uses is now exhausted,
        # as long as the student already started (they may have the last slot).
        if not rec or not rec.get("enabled"):
            raise AccessError("请先使用有效邀请码开始模考", 403)
        users = load_users()
        user = _find_user(users, name, rec["id"])
        return {
            "user_id": (user or {}).get("id"),
            "candidate_name": name,
            "invite_code_id": rec["id"],
            "module": module,
        }


def record_submit(
    *,
    user_id: str | None,
    module: str,
    submission_id: str,
    candidate_name: str | None = None,
    invite_code_id: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    mode: str | None = None,
) -> None:
    ts = now_iso()
    ip_val, ua = _client_meta(ip, user_agent)
    module_key = (module or "writing").strip().lower()
    if module_key not in MODULES:
        module_key = "writing"
    with _locked():
        users = load_users()
        user = None
        if user_id:
            for item in users.get("users") or []:
                if item.get("id") == user_id:
                    user = item
                    break
        if user is None and candidate_name and invite_code_id:
            user = _find_user(users, candidate_name, invite_code_id)
        if user is not None:
            user["last_seen"] = ts
            field = f"{module_key}_submitted"
            user[field] = int(user.get(field) or 0) + 1
            user["last_submission_id"] = submission_id
            user[f"last_{module_key}_submission_id"] = submission_id
            save_users(users)
            user_id = user.get("id")

        log = load_log()
        log.setdefault("events", []).append(
            {
                "id": str(uuid.uuid4()),
                "timestamp": ts,
                "action": "submit",
                "candidate_name": (candidate_name or (user or {}).get("name") or "").strip(),
                "user_id": user_id,
                "invite_code_id": invite_code_id or (user or {}).get("invite_code_id"),
                "module": module_key,
                "mode": mode or "",
                "ip": ip_val,
                "user_agent": ua,
                "submission_id": submission_id,
            }
        )
        save_log(log)


def codes_by_id() -> dict[str, dict]:
    return {c["id"]: c for c in list_codes() if c.get("id")}
