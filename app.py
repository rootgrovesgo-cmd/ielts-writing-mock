#!/usr/bin/env python3
"""IELTS Academic Writing, Reading, Listening, and Speaking practice — Flask app (local + online)."""

from __future__ import annotations

import csv
import hmac
import io
import json
import logging
import os
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path
from urllib.parse import quote

from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

import access
import reading_scoring as rs
import listening_scoring as ls
import report_pdf
import reading_review as rr
import student_portal as sp

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SUBMISSIONS_DIR = DATA_DIR / "submissions"
INDEX_PATH = DATA_DIR / "index.json"
PROMPTS_PATH = BASE_DIR / "prompts" / "prompts.json"
READING_PAPER_PATH = BASE_DIR / "prompts" / "reading_set_a.json"
READING_KEYS_PATH = BASE_DIR / "prompts" / "reading_keys.json"
LISTENING_PAPER_PATH = BASE_DIR / "prompts" / "listening_set_a.json"
LISTENING_KEYS_PATH = BASE_DIR / "prompts" / "listening_keys.json"
LISTENING_AUDIO_DIR = BASE_DIR / "static" / "audio" / "listening_set_a"
SPEAKING_BANK_PATH = BASE_DIR / "prompts" / "speaking_sept2026.json"

TZ_SHANGHAI = timezone(timedelta(hours=8))

DEFAULT_PORT = 8765

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ielts-mock")

app = Flask(__name__)
app.secret_key = os.environ.get("IELTS_SECRET_KEY") or secrets.token_hex(16)
app.config["MAX_FLASH_MESSAGES"] = 8
NOTION_TOKEN = (os.environ.get("NOTION_TOKEN") or "").strip()
NOTION_DATABASE_ID = (os.environ.get("NOTION_DATABASE_ID") or "").strip()

access.bind(DATA_DIR)


@app.template_filter("duration")
def jinja_duration(seconds):
    return report_pdf.format_duration(seconds)



def notion_enabled() -> bool:
    return bool(NOTION_TOKEN and NOTION_DATABASE_ID)


def admin_username() -> str:
    return (os.environ.get("IELTS_ADMIN_USERNAME") or "").strip()


def admin_password() -> str:
    return os.environ.get("IELTS_ADMIN_PASSWORD") or ""


def admin_password_hash() -> str:
    return (os.environ.get("IELTS_ADMIN_PASSWORD_HASH") or "").strip()


def admin_credentials_configured() -> bool:
    return bool(admin_username() and (admin_password_hash() or admin_password()))


def _digest_equal(left: str, right: str) -> bool:
    try:
        return hmac.compare_digest(left, right)
    except (TypeError, ValueError):
        return False


def verify_admin_login(username: str, password: str) -> bool:
    expected_user = admin_username()
    expected_password = admin_password()
    expected_hash = admin_password_hash()
    given_user = (username or "").strip()
    given_password = password or ""

    if not expected_user or (not expected_hash and not expected_password):
        log.warning("Admin login is closed: IELTS_ADMIN_USERNAME / password env is not set")
        _digest_equal(given_user or "x", "y")
        if expected_hash:
            check_password_hash(expected_hash, given_password)
        else:
            _digest_equal(given_password or "x", "y")
        return False

    user_ok = _digest_equal(given_user, expected_user)
    if expected_hash:
        pw_ok = check_password_hash(expected_hash, given_password)
    else:
        pw_ok = _digest_equal(given_password, expected_password)
    return bool(user_ok and pw_ok)


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    access.bind(DATA_DIR)
    if not INDEX_PATH.exists():
        access.atomic_write_json(INDEX_PATH, {"submissions": []})


def load_prompts() -> dict:
    with PROMPTS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def prompt_set_summaries() -> list[dict]:
    prompts = load_prompts()
    return [
        {"id": s.get("id"), "title": s.get("title") or s.get("id")}
        for s in prompts.get("sets", [])
        if s.get("id")
    ]


def load_reading_paper() -> dict:
    return rs.load_paper(READING_PAPER_PATH)


def load_reading_keys() -> dict:
    return rs.load_keys(READING_KEYS_PATH)


def load_listening_paper() -> dict:
    paper = ls.load_paper(LISTENING_PAPER_PATH)
    ls.refresh_modes(paper)
    return paper


def load_listening_keys() -> dict:
    return ls.load_keys(LISTENING_KEYS_PATH)


def load_speaking_bank() -> dict:
    with SPEAKING_BANK_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_index() -> dict:
    ensure_storage()
    with INDEX_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def save_index(index: dict) -> None:
    ensure_storage()
    access.atomic_write_json(INDEX_PATH, index)


def word_count(text: str) -> int:
    text = (text or "").strip()
    if not text:
        return 0
    return len(text.split())


def truncate(text: str, limit: int = 1900) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def record_module(record: dict | None) -> str:
    if not record:
        return "writing"
    mod = (record.get("module") or "").strip().lower()
    if mod in {"reading", "listening", "speaking"}:
        return mod
    return "writing"


def request_client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For") or ""
    if forwarded.strip():
        return forwarded.split(",", 1)[0].strip()
    return (request.remote_addr or "").strip()


STUDENT_SESSION_KEYS = (
    "student_ok",
    "student_name",
    "student_user_id",
    "invite_code_id",
    "student_module",
)


@app.context_processor
def inject_student_nav():
    if access.session_is_valid(session):
        return {
            "student_logged_in": True,
            "student_name": session.get("student_name") or "",
        }
    return {"student_logged_in": False, "student_name": ""}


def current_student() -> dict | None:
    if not access.session_is_valid(session):
        return None
    return {
        "user_id": session.get("student_user_id"),
        "candidate_name": session.get("student_name"),
        "invite_code_id": session.get("invite_code_id"),
    }


def apply_student_login(result: dict, *, keep_module: bool = False) -> None:
    session["student_ok"] = True
    session["student_name"] = result["candidate_name"]
    session["student_user_id"] = result["user_id"]
    session["invite_code_id"] = result["invite_code_id"]
    if keep_module and result.get("module"):
        session["student_module"] = result["module"]
    elif not keep_module:
        session.pop("student_module", None)


def clear_student_session() -> None:
    for key in STUDENT_SESSION_KEYS:
        session.pop(key, None)


def safe_student_next(raw: str | None) -> str:
    nxt = (raw or "").strip()
    if nxt.startswith("/me") and not nxt.startswith("//") and "\\" not in nxt and ":" not in nxt:
        return nxt
    return url_for("student_home")


def load_owned_submission(sid: str, ident: dict) -> dict | None:
    """Return a submission only if it exists and belongs to this student."""
    token = (sid or "").strip()
    if not token or any(ch in token for ch in ("/", "\\", "..")):
        return None
    path = SUBMISSIONS_DIR / f"{token}.json"
    if not path.is_file() or path.resolve().parent != SUBMISSIONS_DIR.resolve():
        return None
    with path.open(encoding="utf-8") as f:
        record = json.load(f)
    if not sp.owns_record(record, ident):
        return None
    return record


def save_to_notion(record: dict) -> dict | None:
    """Create a Notion database row. Returns page meta or None if disabled/failed."""
    if not notion_enabled():
        return None
    # Reading submissions skip Notion: existing DBs lack reading properties.
    if record_module(record) in {"reading", "listening"}:
        return None
    try:
        from notion_client import Client
    except ImportError:
        log.warning("notion-client not installed; skip Notion save")
        return None

    try:
        client = Client(auth=NOTION_TOKEN)
        name = record.get("candidate_name") or "未命名"
        submitted_at = record.get("timestamp") or datetime.now(TZ_SHANGHAI).isoformat()
        props = {
            "Name": {"title": [{"text": {"content": truncate(str(name), 100)}}]},
            "Candidate Name": {
                "rich_text": [{"text": {"content": truncate(str(name), 200)}}]
            },
            "Mode": {"select": {"name": truncate(str(record.get("mode") or "full"), 50)}},
            "Prompt Set": {
                "rich_text": [
                    {"text": {"content": truncate(str(record.get("prompt_set_id") or ""), 100)}}
                ]
            },
            "Task 1": {
                "rich_text": [
                    {"text": {"content": truncate(record.get("task1_text") or "", 1900)}}
                ]
            },
            "Task 2": {
                "rich_text": [
                    {"text": {"content": truncate(record.get("task2_text") or "", 1900)}}
                ]
            },
            "Task1 Words": {"number": int(record.get("task1_word_count") or 0)},
            "Task2 Words": {"number": int(record.get("task2_word_count") or 0)},
            "Time Used (sec)": {"number": int(record.get("time_used_seconds") or 0)},
            "Submitted At": {"date": {"start": submitted_at}},
            "Submission ID": {
                "rich_text": [{"text": {"content": truncate(str(record.get("id") or ""), 80)}}]
            },
            "Auto Submitted": {
                "checkbox": bool(record.get("auto_submitted", False))
            },
        }
        page = client.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=props,
        )
        page_id = page.get("id")
        log.info("Notion page created: %s", page_id)
        return {"id": page_id, "url": page.get("url")}
    except Exception as exc:  # noqa: BLE001 — never fail the student submit
        log.exception("Notion save failed: %s", exc)
        return {"error": str(exc)}


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_ok") or not admin_credentials_configured():
            return redirect(url_for("admin_login", next=request.path))
        if session.get("admin_username") != admin_username():
            session.pop("admin_ok", None)
            session.pop("admin_username", None)
            return redirect(url_for("admin_login", next=request.path))
        return fn(*args, **kwargs)

    return wrapper


def student_session_error():
    if access.session_is_valid(session):
        return None
    return jsonify({"ok": False, "error": "请先使用有效邀请码开始模考"}), 403


def ident_for_submit(data: dict, module: str):
    try:
        ident = access.resolve_student(
            session,
            candidate_name=data.get("candidate_name"),
            invite_code=data.get("invite_code"),
            module=module,
        )
    except access.AccessError as exc:
        return None, (jsonify({"ok": False, "error": exc.message}), exc.status)
    if not (ident.get("candidate_name") or "").strip():
        return None, (jsonify({"ok": False, "error": "请填写姓名"}), 400)
    return ident, None


@app.route("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "service": "ielts-writing-mock",
            "modules": ["writing", "reading", "speaking", "listening"],
            "notion": notion_enabled(),
        }
    )


@app.route("/")
def index():
    return render_template("hub.html")


@app.route("/writing")
def writing():
    return render_template(
        "exam.html",
        sets=prompt_set_summaries(),
        notion_on=notion_enabled(),
    )


@app.route("/reading")
def reading():
    return render_template("reading.html")


@app.route("/listening")
def listening():
    return render_template("listening.html")


@app.route("/speaking")
def speaking():
    return render_template("speaking.html")


@app.route("/me")
def student_home():
    ident = current_student()
    if not ident:
        return render_template(
            "student_login.html",
            error=None,
            next=safe_student_next(request.args.get("next")),
        )
    attempts = sp.list_own_attempts(load_index(), ident)
    return render_template(
        "student_home.html",
        student_name=ident.get("candidate_name") or "",
        attempts=attempts,
    )


@app.route("/me/login", methods=["POST"])
def student_login():
    nxt = safe_student_next(request.form.get("next") or request.args.get("next"))
    try:
        result = access.login_student(
            candidate_name=request.form.get("candidate_name"),
            invite_code=request.form.get("invite_code"),
            ip=request_client_ip(),
            user_agent=request.headers.get("User-Agent"),
        )
    except access.AccessError as exc:
        return render_template(
            "student_login.html",
            error=exc.message,
            next=nxt,
        )
    apply_student_login(result)
    return redirect(nxt)


@app.route("/me/logout")
def student_logout():
    clear_student_session()
    return redirect(url_for("index"))


def _review_context(record: dict, *, mistakes_only: bool = False) -> dict:
    return {
        "sid": record.get("id"),
        "mistakes_only": bool(mistakes_only),
        "module": sp.module_of(record),
    }


def render_attempt_exam(record: dict, *, mistakes_only: bool = False):
    """Render the live exam templates in read-only review mode."""
    review = _review_context(record, mistakes_only=mistakes_only)
    if sp.module_of(record) == "reading":
        return render_template("reading.html", review=review)
    if sp.module_of(record) == "listening":
        return render_template("listening.html", review=review)
    return render_template(
        "exam.html",
        sets=prompt_set_summaries(),
        notion_on=notion_enabled(),
        review=review,
    )


def reject_review_submit(data: dict):
    """Block a client that tries to submit or overwrite from a review view."""
    if not isinstance(data, dict):
        return None
    if data.get("review") or data.get("review_mode") or data.get("review_sid") or data.get("attempt_review"):
        return jsonify({"ok": False, "error": "回顾模式不可交卷"}), 403
    return None


@app.route("/me/submission/<sid>")
def student_submission(sid: str):
    ident = current_student()
    if not ident:
        return redirect(url_for("student_home", next=f"/me/submission/{sid}"))
    record = load_owned_submission(sid, ident)
    if record is None:
        return "未找到该答卷", 404
    return render_attempt_exam(record, mistakes_only=False)


@app.route("/me/submission/<sid>/review")
def student_submission_review(sid: str):
    ident = current_student()
    if not ident:
        return redirect(url_for("student_home", next=f"/me/submission/{sid}/review"))
    record = load_owned_submission(sid, ident)
    if record is None or sp.module_of(record) not in {"reading", "listening"}:
        return "未找到该答卷", 404
    return render_attempt_exam(record, mistakes_only=True)


@app.route("/api/me/submission/<sid>")
def api_me_submission(sid: str):
    ident = current_student()
    if not ident:
        return jsonify({"ok": False, "error": "请先登录后查看记录"}), 401
    record = load_owned_submission(sid, ident)
    if record is None:
        return jsonify({"ok": False, "error": "未找到该答卷"}), 404
    module = sp.module_of(record)
    if module == "reading":
        payload = sp.attempt_review_payload(
            record,
            paper=load_reading_paper(),
            keys=load_reading_keys(),
        )
    elif module == "listening":
        payload = sp.attempt_review_payload(
            record,
            paper=load_listening_paper(),
            keys=load_listening_keys(),
        )
    else:
        payload = sp.attempt_review_payload(record, prompts_data=load_prompts())
    return jsonify(payload)


@app.route("/api/session/start", methods=["POST"])
def api_session_start():
    data = request.get_json(silent=True) or {}
    try:
        result = access.start_student(
            candidate_name=data.get("candidate_name"),
            invite_code=data.get("invite_code"),
            module=data.get("module"),
            mode=data.get("mode"),
            ip=request_client_ip(),
            user_agent=request.headers.get("User-Agent"),
        )
    except access.AccessError as exc:
        return jsonify({"ok": False, "error": exc.message}), exc.status
    session["student_ok"] = True
    session["student_name"] = result["candidate_name"]
    session["student_user_id"] = result["user_id"]
    session["invite_code_id"] = result["invite_code_id"]
    session["student_module"] = result["module"]
    return jsonify(
        {
            "ok": True,
            "candidate_name": result["candidate_name"],
            "module": result["module"],
        }
    )


@app.route("/api/prompts")
def api_prompts():
    err = student_session_error()
    if err:
        return err
    return jsonify(load_prompts())


@app.route("/api/reading/paper")
def api_reading_paper():
    """Student-facing paper only — never includes keys or explanations."""
    err = student_session_error()
    if err:
        return err
    return jsonify(load_reading_paper())


@app.route("/api/listening/paper")
def api_listening_paper():
    """Student-facing listening paper only — never includes keys or transcripts."""
    err = student_session_error()
    if err:
        return err
    return jsonify(load_listening_paper())


@app.route("/api/listening/audio/<section>")
def api_listening_audio(section: str):
    """Stream a section mp3. Requires a student session or a teacher login."""
    token = (section or "").strip().lower().replace("section", "")
    if token not in {"1", "2", "3", "4"}:
        return jsonify({"ok": False, "error": "未找到该音频"}), 404
    is_admin = bool(session.get("admin_ok") and admin_credentials_configured())
    if not is_admin:
        err = student_session_error()
        if err:
            return err
    path = (LISTENING_AUDIO_DIR / f"section{token}.mp3").resolve()
    if path.parent != LISTENING_AUDIO_DIR.resolve() or not path.is_file():
        return jsonify({"ok": False, "error": "未找到该音频"}), 404
    return send_file(path, mimetype="audio/mpeg", conditional=True, max_age=0, download_name=f"section{token}.mp3")


@app.route("/api/speaking/bank")
def api_speaking_bank():
    """Speaking practice bank. Prompts only — no sample answers or scores."""
    err = student_session_error()
    if err:
        return err
    bank = load_speaking_bank()
    return jsonify(
        {
            "season": bank.get("season"),
            "season_label": bank.get("season_label"),
            "disclaimer": bank.get("disclaimer"),
            "disclaimer_zh": bank.get("disclaimer_zh"),
            "part1": bank.get("part1") or [],
            "part2": bank.get("part2") or [],
        }
    )


@app.route("/api/submit", methods=["POST"])
def api_submit():
    ensure_storage()
    data = request.get_json(silent=True) or {}
    blocked = reject_review_submit(data)
    if blocked:
        return blocked
    ident, err = ident_for_submit(data, "writing")
    if err:
        return err

    candidate_name = ident["candidate_name"]

    task1_text = data.get("task1_text") or ""
    task2_text = data.get("task2_text") or ""
    mode = data.get("mode") or "full"
    prompt_set_id = data.get("prompt_set_id") or ""
    task1_prompt_id = data.get("task1_prompt_id") or ""
    task2_prompt_id = data.get("task2_prompt_id") or ""
    duration_seconds = int(data.get("duration_seconds") or 0)
    time_remaining_seconds = int(data.get("time_remaining_seconds") or 0)
    time_used_seconds = int(
        data.get("time_used_seconds")
        or max(0, duration_seconds - time_remaining_seconds)
    )
    auto_submitted = bool(data.get("auto_submitted", False))
    paused_total_seconds = int(data.get("paused_total_seconds") or 0)

    now = datetime.now(TZ_SHANGHAI)
    sid = str(uuid.uuid4())
    record = {
        "id": sid,
        "timestamp": now.isoformat(timespec="seconds"),
        "candidate_name": candidate_name,
        "module": "writing",
        "mode": mode,
        "prompt_set_id": prompt_set_id,
        "task1_prompt_id": task1_prompt_id,
        "task2_prompt_id": task2_prompt_id,
        "task1_text": task1_text,
        "task2_text": task2_text,
        "task1_word_count": word_count(task1_text),
        "task2_word_count": word_count(task2_text),
        "duration_seconds": duration_seconds,
        "time_remaining_seconds": time_remaining_seconds,
        "time_used_seconds": time_used_seconds,
        "paused_total_seconds": paused_total_seconds,
        "auto_submitted": auto_submitted,
        "user_id": ident.get("user_id"),
        "invite_code_id": ident.get("invite_code_id"),
    }

    out_path = SUBMISSIONS_DIR / f"{sid}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    index = load_index()
    index.setdefault("submissions", []).insert(
        0,
        {
            "id": sid,
            "timestamp": record["timestamp"],
            "candidate_name": candidate_name,
            "module": "writing",
            "mode": mode,
            "prompt_set_id": prompt_set_id,
            "task1_word_count": record["task1_word_count"],
            "task2_word_count": record["task2_word_count"],
            "time_used_seconds": time_used_seconds,
            "auto_submitted": auto_submitted,
            "file": f"submissions/{sid}.json",
            "user_id": ident.get("user_id"),
            "invite_code_id": ident.get("invite_code_id"),
        },
    )
    save_index(index)

    access.record_submit(
        user_id=ident.get("user_id"),
        module="writing",
        submission_id=sid,
        candidate_name=candidate_name,
        invite_code_id=ident.get("invite_code_id"),
        ip=request_client_ip(),
        user_agent=request.headers.get("User-Agent"),
        mode=mode,
    )

    notion_result = save_to_notion(record)
    if notion_result and notion_result.get("id"):
        record["notion_page_id"] = notion_result["id"]
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

    return jsonify(
        {
            "ok": True,
            "id": sid,
            "timestamp": record["timestamp"],
            "notion": bool(notion_result and notion_result.get("id")),
            "notion_error": (notion_result or {}).get("error"),
        }
    )



PART_TIME_KEYS = ("1", "2", "3")
LISTENING_PART_TIME_KEYS = ("1", "2", "3", "4")
HIGHLIGHTS_MAX_BYTES = 400_000


def normalize_part_times(raw, duration_seconds: int = 0, keys=None) -> dict[str, int]:
    """Sanitize client part-time payloads into a fixed key map of seconds."""
    part_keys = tuple(keys) if keys else PART_TIME_KEYS
    out = {key: 0 for key in part_keys}
    if not isinstance(raw, dict):
        return out
    try:
        cap = max(0, int(duration_seconds or 0)) or (3 * 60 * 60)
    except (TypeError, ValueError):
        cap = 3 * 60 * 60
    for key, value in raw.items():
        token = str(key).strip().lower().replace(" ", "").replace("_", "")
        token = token.replace("passage", "").replace("section", "")
        if token not in out:
            continue
        try:
            seconds = int(value)
        except (TypeError, ValueError):
            continue
        out[token] = max(0, min(seconds, cap))
    return out


def normalize_highlights(raw, max_bytes: int = HIGHLIGHTS_MAX_BYTES) -> dict | None:
    """Optionally keep student highlight HTML with the submission (size-capped)."""
    if not isinstance(raw, dict):
        return None
    cleaned: dict = {}
    passage = raw.get("passage") or raw.get("passages")
    if isinstance(passage, dict):
        passage_out: dict[str, str] = {}
        for key, html in passage.items():
            token = str(key).strip()
            if token not in PART_TIME_KEYS or not isinstance(html, str):
                continue
            passage_out[token] = html
        if passage_out:
            cleaned["passage"] = passage_out
    questions = raw.get("questions")
    if isinstance(questions, str) and questions:
        cleaned["questions"] = questions
    if not cleaned:
        return None
    encoded = json.dumps(cleaned, ensure_ascii=False)
    if len(encoded.encode("utf-8")) > max_bytes:
        return None
    return cleaned


def student_reading_result(record: dict) -> dict:
    """Student-facing submit result: score and times, never keys or marking."""
    return {
        "ok": True,
        "id": record["id"],
        "timestamp": record["timestamp"],
        "score": record["score"],
        "total": record["total"],
        "band_estimate": record["band_estimate"],
        "time_used_seconds": record["time_used_seconds"],
        "part_times": record.get("part_times") or {key: 0 for key in PART_TIME_KEYS},
        "mode": record.get("mode"),
        "auto_submitted": bool(record.get("auto_submitted", False)),
    }


@app.route("/api/reading/submit", methods=["POST"])
def api_reading_submit():
    ensure_storage()
    data = request.get_json(silent=True) or {}
    blocked = reject_review_submit(data)
    if blocked:
        return blocked
    ident, err = ident_for_submit(data, "reading")
    if err:
        return err

    candidate_name = ident["candidate_name"]

    mode = data.get("mode") or "full"
    if mode not in rs.MODES:
        mode = "full"
    prompt_set_id = data.get("prompt_set_id") or "set-a"
    answers = data.get("answers") or {}
    if not isinstance(answers, dict):
        answers = {}
    flags = data.get("flags") or []
    if not isinstance(flags, list):
        flags = []

    duration_seconds = int(data.get("duration_seconds") or rs.MODES[mode]["seconds"])
    time_remaining_seconds = int(data.get("time_remaining_seconds") or 0)
    time_used_seconds = int(
        data.get("time_used_seconds")
        or max(0, duration_seconds - time_remaining_seconds)
    )
    auto_submitted = bool(data.get("auto_submitted", False))
    paused_total_seconds = int(data.get("paused_total_seconds") or 0)
    part_times = normalize_part_times(data.get("part_times"), duration_seconds)
    highlights = normalize_highlights(data.get("highlights"))

    result = rs.score_paper(answers, mode=mode, keys=load_reading_keys())

    now = datetime.now(TZ_SHANGHAI)
    sid = str(uuid.uuid4())
    record = {
        "id": sid,
        "timestamp": now.isoformat(timespec="seconds"),
        "candidate_name": candidate_name,
        "module": "reading",
        "mode": mode,
        "prompt_set_id": prompt_set_id,
        "answers": {str(k): ("" if v is None else str(v)) for k, v in answers.items()},
        "flags": flags,
        "marking": result["marking"],
        "score": result["score"],
        "total": result["total"],
        "band_estimate": result["band_estimate"],
        "duration_seconds": duration_seconds,
        "time_remaining_seconds": time_remaining_seconds,
        "time_used_seconds": time_used_seconds,
        "paused_total_seconds": paused_total_seconds,
        "part_times": part_times,
        "auto_submitted": auto_submitted,
        "user_id": ident.get("user_id"),
        "invite_code_id": ident.get("invite_code_id"),
    }
    if highlights:
        record["highlights"] = highlights

    out_path = SUBMISSIONS_DIR / f"{sid}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    index = load_index()
    index.setdefault("submissions", []).insert(
        0,
        {
            "id": sid,
            "timestamp": record["timestamp"],
            "candidate_name": candidate_name,
            "module": "reading",
            "mode": mode,
            "prompt_set_id": prompt_set_id,
            "score": record["score"],
            "total": record["total"],
            "band_estimate": record["band_estimate"],
            "time_used_seconds": time_used_seconds,
            "part_times": part_times,
            "auto_submitted": auto_submitted,
            "file": f"submissions/{sid}.json",
            "user_id": ident.get("user_id"),
            "invite_code_id": ident.get("invite_code_id"),
        },
    )
    save_index(index)

    access.record_submit(
        user_id=ident.get("user_id"),
        module="reading",
        submission_id=sid,
        candidate_name=candidate_name,
        invite_code_id=ident.get("invite_code_id"),
        ip=request_client_ip(),
        user_agent=request.headers.get("User-Agent"),
        mode=mode,
    )

    # Intentionally skip Notion for reading so a missing property cannot
    # interfere. Local JSON is the source of truth.
    return jsonify(student_reading_result(record))


def normalize_listening_part_times(raw, cap: int) -> dict:
    return normalize_part_times(raw, cap, keys=LISTENING_PART_TIME_KEYS)


def student_listening_result(record: dict) -> dict:
    """Student-facing submit result: score and times, never keys or transcripts."""
    return {
        "ok": True,
        "id": record["id"],
        "timestamp": record["timestamp"],
        "score": record["score"],
        "total": record["total"],
        "band_estimate": record["band_estimate"],
        "time_used_seconds": record["time_used_seconds"],
        "part_times": record.get("part_times") or {key: 0 for key in LISTENING_PART_TIME_KEYS},
        "mode": record.get("mode"),
        "auto_submitted": bool(record.get("auto_submitted", False)),
    }


@app.route("/api/listening/submit", methods=["POST"])
def api_listening_submit():
    ensure_storage()
    data = request.get_json(silent=True) or {}
    blocked = reject_review_submit(data)
    if blocked:
        return blocked
    ident, err = ident_for_submit(data, "listening")
    if err:
        return err

    candidate_name = ident["candidate_name"]
    paper = load_listening_paper()
    modes = ls.modes_info(paper)
    mode = data.get("mode") or "full"
    if mode not in modes:
        mode = "full"
    prompt_set_id = data.get("prompt_set_id") or "set-a"
    answers = data.get("answers") or {}
    if not isinstance(answers, dict):
        answers = {}
    flags = data.get("flags") or []
    if not isinstance(flags, list):
        flags = []

    duration_seconds = int(data.get("duration_seconds") or modes[mode]["seconds"])
    time_remaining_seconds = int(data.get("time_remaining_seconds") or 0)
    time_used_seconds = int(
        data.get("time_used_seconds")
        or max(0, duration_seconds - time_remaining_seconds)
    )
    auto_submitted = bool(data.get("auto_submitted", False))
    paused_total_seconds = int(data.get("paused_total_seconds") or 0)
    part_times = normalize_listening_part_times(data.get("part_times"), duration_seconds)

    result = ls.score_paper(answers, mode=mode, keys=load_listening_keys())

    now = datetime.now(TZ_SHANGHAI)
    sid = str(uuid.uuid4())
    record = {
        "id": sid,
        "timestamp": now.isoformat(timespec="seconds"),
        "candidate_name": candidate_name,
        "module": "listening",
        "mode": mode,
        "prompt_set_id": prompt_set_id,
        "answers": {str(k): ("" if v is None else str(v)) for k, v in answers.items()},
        "flags": flags,
        "marking": result["marking"],
        "score": result["score"],
        "total": result["total"],
        "band_estimate": result["band_estimate"],
        "duration_seconds": duration_seconds,
        "time_remaining_seconds": time_remaining_seconds,
        "time_used_seconds": time_used_seconds,
        "paused_total_seconds": paused_total_seconds,
        "part_times": part_times,
        "auto_submitted": auto_submitted,
        "user_id": ident.get("user_id"),
        "invite_code_id": ident.get("invite_code_id"),
    }

    out_path = SUBMISSIONS_DIR / f"{sid}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    index = load_index()
    index.setdefault("submissions", []).insert(
        0,
        {
            "id": sid,
            "timestamp": record["timestamp"],
            "candidate_name": candidate_name,
            "module": "listening",
            "mode": mode,
            "prompt_set_id": prompt_set_id,
            "score": record["score"],
            "total": record["total"],
            "band_estimate": record["band_estimate"],
            "time_used_seconds": time_used_seconds,
            "part_times": part_times,
            "auto_submitted": auto_submitted,
            "file": f"submissions/{sid}.json",
            "user_id": ident.get("user_id"),
            "invite_code_id": ident.get("invite_code_id"),
        },
    )
    save_index(index)

    access.record_submit(
        user_id=ident.get("user_id"),
        module="listening",
        submission_id=sid,
        candidate_name=candidate_name,
        invite_code_id=ident.get("invite_code_id"),
        ip=request_client_ip(),
        user_agent=request.headers.get("User-Agent"),
        mode=mode,
    )
    return jsonify(student_listening_result(record))


def safe_admin_next(raw: str | None) -> str:
    nxt = (raw or "").strip()
    if nxt.startswith("/") and not nxt.startswith("//") and "\\" not in nxt and ":" not in nxt:
        return nxt
    return url_for("admin")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    nxt = safe_admin_next(request.args.get("next") or request.form.get("next"))
    if request.method == "POST":
        username = request.form.get("username") or ""
        password = request.form.get("password") or ""
        if verify_admin_login(username, password):
            session["admin_ok"] = True
            session["admin_username"] = admin_username()
            return redirect(nxt)
        error = "用户名或密码错误。"
    return render_template("admin_login.html", error=error, next=nxt)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_ok", None)
    session.pop("admin_username", None)
    return redirect(url_for("admin_login"))


def _admin_view_data():
    index = load_index()
    submissions = index.get("submissions", [])
    codes = access.list_codes()
    code_map = {c["id"]: c for c in codes if c.get("id")}
    users = access.list_users()
    events = access.list_events(200)

    subs_by_user: dict[str, list] = {}
    for item in submissions:
        uid = item.get("user_id")
        if uid:
            subs_by_user.setdefault(uid, []).append(item)

    user_rows = []
    for user in users:
        code = code_map.get(user.get("invite_code_id") or "")
        user_rows.append(
            {
                "user": user,
                "code": (code or {}).get("code") or user.get("invite_code") or "—",
                "note": (code or {}).get("note") or "",
                "submissions": subs_by_user.get(user.get("id") or "", []),
            }
        )

    event_rows = []
    for ev in events:
        code = code_map.get(ev.get("invite_code_id") or "")
        event_rows.append(
            {
                "event": ev,
                "code": (code or {}).get("code") or "",
                "note": (code or {}).get("note") or "",
            }
        )
    return {
        "submissions": submissions,
        "codes": codes,
        "user_rows": user_rows,
        "event_rows": event_rows,
        "notion_on": notion_enabled(),
        "admin_name": session.get("admin_username") or "",
    }


@app.route("/admin")
@admin_required
def admin():
    tab = (request.args.get("tab") or "scripts").strip()
    if tab not in {"scripts", "users", "log", "invites"}:
        tab = "scripts"
    data = _admin_view_data()
    return render_template("admin.html", tab=tab, **data)


@app.route("/admin/invites/create", methods=["POST"])
@admin_required
def admin_invite_create():
    code = (request.form.get("code") or "").strip()
    note = (request.form.get("note") or "").strip()
    max_uses_raw = (request.form.get("max_uses") or "").strip()
    max_uses = None
    if max_uses_raw:
        try:
            max_uses = int(max_uses_raw)
            if max_uses < 1:
                raise ValueError("max_uses must be positive")
        except (TypeError, ValueError):
            flash("次数上限须为正整数，或留空表示不限。", "error")
            return redirect(url_for("admin", tab="invites"))
    try:
        rec = access.create_code(
            code=code or None,
            note=note,
            max_uses=max_uses,
            created_by=session.get("admin_username") or "",
        )
    except access.AccessError as exc:
        flash(exc.message, "error")
        return redirect(url_for("admin", tab="invites"))
    flash(f"已创建邀请码：{rec['code']}", "success")
    return redirect(url_for("admin", tab="invites"))


@app.route("/admin/invites/<cid>/toggle", methods=["POST"])
@admin_required
def admin_invite_toggle(cid: str):
    raw = (request.form.get("enabled") or "").strip().lower()
    enabled = raw in {"1", "true", "on", "yes"}
    rec = access.set_code_enabled(cid, enabled)
    if not rec:
        flash("未找到该邀请码。", "error")
    elif enabled:
        flash(f"已启用邀请码：{rec.get('code')}", "success")
    else:
        flash(f"已停用邀请码：{rec.get('code')}", "success")
    return redirect(url_for("admin", tab="invites"))


@app.route("/admin/submission/<sid>")
@admin_required
def admin_submission(sid: str):
    path = SUBMISSIONS_DIR / f"{sid}.json"
    if not path.exists():
        return "未找到该答卷", 404
    with path.open(encoding="utf-8") as f:
        record = json.load(f)
    explanations = {}
    transcripts = {}
    listening_layouts = []
    module = record_module(record)
    if module == "reading":
        keys = load_reading_keys().get("questions", {})
        for q, meta in keys.items():
            explanations[int(q)] = meta.get("explanation") or ""
        for row in record.get("marking") or []:
            row["explanation"] = explanations.get(int(row.get("q") or 0), "")
    elif module == "listening":
        keys = load_listening_keys()
        for q, meta in (keys.get("questions") or {}).items():
            explanations[int(q)] = meta.get("explanation") or ""
        for row in record.get("marking") or []:
            row["explanation"] = explanations.get(int(row.get("q") or 0), "")
        transcripts = ls.transcripts(keys)
        listening_layouts = sp.listening_layout_blocks(ls.load_paper(), record, keys)
    invite = access.get_code(record.get("invite_code_id"))
    is_reading = module == "reading"
    is_listening = module == "listening"
    part_times_label = None
    passage_profiles = []
    highlight_review = None
    if is_reading:
        part_times_label = report_pdf.part_times_summary(record.get("part_times"))
        passage_profiles = rr.passage_profiles(record)
        for profile in passage_profiles:
            if profile.get("time_recorded"):
                profile["time_label"] = report_pdf.format_duration(profile.get("time_seconds"))
            else:
                profile["time_label"] = "本题卷未记录"
        highlight_review = rr.highlight_review(record)
    elif is_listening:
        part_times_label = report_pdf.part_times_summary(
            record.get("part_times"), label="Section"
        )
    band_fmt = rs.format_band if is_reading else ls.format_band
    return render_template(
        "admin_detail.html",
        record=record,
        is_reading=is_reading,
        is_listening=is_listening,
        band_label=band_fmt(record.get("band_estimate")),
        part_times_label=part_times_label,
        passage_profiles=passage_profiles,
        highlight_review=highlight_review,
        transcripts=transcripts,
        listening_layouts=listening_layouts,
        invite=invite,
    )




@app.route("/admin/submission/<sid>/report.pdf")
@admin_required
def admin_submission_report(sid: str):
    path = SUBMISSIONS_DIR / f"{sid}.json"
    if not path.exists():
        return "未找到该答卷", 404
    with path.open(encoding="utf-8") as f:
        record = json.load(f)
    invite = access.get_code(record.get("invite_code_id"))
    pdf_bytes = report_pdf.build_submission_report(record, invite=invite)
    filename = report_pdf.report_filename(record)
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": _content_disposition(filename),
        },
    )


def _content_disposition(filename: str) -> str:
    """ASCII fallback plus RFC 5987 UTF-8 filename for CJK candidate names."""
    ascii_name = filename.encode("ascii", "ignore").decode("ascii")
    ascii_name = ascii_name.replace('"', "").strip() or "report.pdf"
    if not ascii_name.lower().endswith(".pdf"):
        ascii_name = f"{ascii_name}.pdf" if ascii_name else "report.pdf"
    # Collapse leftover double dashes from stripped CJK, e.g. reading--20261112-report.pdf
    while "--" in ascii_name:
        ascii_name = ascii_name.replace("--", "-")
    quoted = quote(filename)
    return f'attachment; filename="{ascii_name}"; filename*=UTF-8''{quoted}'


@app.route("/admin/export.json")
@admin_required
def admin_export_json():
    index = load_index()
    full = []
    for item in index.get("submissions", []):
        path = SUBMISSIONS_DIR / f"{item['id']}.json"
        if path.exists():
            with path.open(encoding="utf-8") as f:
                full.append(json.load(f))
    return Response(
        json.dumps(full, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=ielts_submissions.json"},
    )


def _answers_summary(record: dict) -> str:
    answers = record.get("answers")
    if not isinstance(answers, dict) or not answers:
        return ""
    parts = []
    for k in sorted(answers.keys(), key=lambda x: int(x) if str(x).isdigit() else str(x)):
        parts.append(f"{k}:{answers[k]}")
    return " | ".join(parts)


@app.route("/admin/export.csv")
@admin_required
def admin_export_csv():
    index = load_index()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "id",
            "timestamp",
            "candidate_name",
            "module",
            "mode",
            "prompt_set_id",
            "task1_word_count",
            "task2_word_count",
            "score",
            "total",
            "band_estimate",
            "time_used_seconds",
            "time_remaining_seconds",
            "auto_submitted",
            "task1_text",
            "task2_text",
            "answers_summary",
            "user_id",
            "invite_code_id",
        ]
    )
    for item in index.get("submissions", []):
        path = SUBMISSIONS_DIR / f"{item['id']}.json"
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as f:
            r = json.load(f)
        module = record_module(r)
        writer.writerow(
            [
                r.get("id"),
                r.get("timestamp"),
                r.get("candidate_name") or "",
                module,
                r.get("mode"),
                r.get("prompt_set_id"),
                r.get("task1_word_count") if module == "writing" else "",
                r.get("task2_word_count") if module == "writing" else "",
                r.get("score") if module in {"reading", "listening"} else "",
                r.get("total") if module in {"reading", "listening"} else "",
                r.get("band_estimate") if module in {"reading", "listening"} else "",
                r.get("time_used_seconds"),
                r.get("time_remaining_seconds"),
                r.get("auto_submitted"),
                (r.get("task1_text") or "").replace("\n", "\\n") if module == "writing" else "",
                (r.get("task2_text") or "").replace("\n", "\\n") if module == "writing" else "",
                _answers_summary(r) if module in {"reading", "listening"} else "",
                r.get("user_id") or "",
                r.get("invite_code_id") or "",
            ]
        )
    return Response(
        "\ufeff" + buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=ielts_submissions.csv"},
    )


def main() -> None:
    ensure_storage()
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Rosette Exclusive Mock Exam → http://{host}:{port}/")
    print(f"Writing → http://{host}:{port}/writing")
    print(f"Reading → http://{host}:{port}/reading")
    print(f"Listening → http://{host}:{port}/listening")
    print(f"Speaking → http://{host}:{port}/speaking")
    print(f"学生记录 → http://{host}:{port}/me")
    print(f"Health → http://{host}:{port}/health")
    print(f"教师后台 → http://{host}:{port}/admin")
    print(f"Notion sync: {'ON' if notion_enabled() else 'OFF'}")
    if not admin_credentials_configured():
        print("警告：未设置 IELTS_ADMIN_USERNAME 与密码环境变量，教师后台将无法登录。")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
