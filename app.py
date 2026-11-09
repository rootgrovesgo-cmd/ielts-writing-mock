#!/usr/bin/env python3
"""IELTS Writing timed mock-exam — Flask app (local + online)."""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SUBMISSIONS_DIR = DATA_DIR / "submissions"
INDEX_PATH = DATA_DIR / "index.json"
PROMPTS_PATH = BASE_DIR / "prompts" / "prompts.json"

TZ_SHANGHAI = timezone(timedelta(hours=8))

DEFAULT_ADMIN_PASSWORD = "ielts2026"
DEFAULT_PORT = 8765

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ielts-mock")

app = Flask(__name__)
app.secret_key = os.environ.get("IELTS_SECRET_KEY") or secrets.token_hex(16)
ADMIN_PASSWORD = os.environ.get("IELTS_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
NOTION_TOKEN = (os.environ.get("NOTION_TOKEN") or "").strip()
NOTION_DATABASE_ID = (os.environ.get("NOTION_DATABASE_ID") or "").strip()


def notion_enabled() -> bool:
    return bool(NOTION_TOKEN and NOTION_DATABASE_ID)


def ensure_storage() -> None:
    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_PATH.exists():
        INDEX_PATH.write_text(
            json.dumps({"submissions": []}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def load_prompts() -> dict:
    with PROMPTS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_index() -> dict:
    ensure_storage()
    with INDEX_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def save_index(index: dict) -> None:
    ensure_storage()
    with INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


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


def save_to_notion(record: dict) -> dict | None:
    """Create a Notion database row. Returns page meta or None if disabled/failed."""
    if not notion_enabled():
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
        # Notion date prefers ISO; strip timezone offset issues by using UTC Z if needed
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
        if not session.get("admin_ok"):
            return redirect(url_for("admin_login", next=request.path))
        return fn(*args, **kwargs)

    return wrapper


@app.route("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "service": "ielts-writing-mock",
            "notion": notion_enabled(),
        }
    )


@app.route("/")
def index():
    prompts = load_prompts()
    return render_template(
        "exam.html",
        sets=prompts.get("sets", []),
        notion_on=notion_enabled(),
    )


@app.route("/api/prompts")
def api_prompts():
    return jsonify(load_prompts())


@app.route("/api/submit", methods=["POST"])
def api_submit():
    ensure_storage()
    data = request.get_json(silent=True) or {}

    candidate_name = (data.get("candidate_name") or "").strip()
    if not candidate_name:
        return jsonify({"ok": False, "error": "请填写姓名"}), 400

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
    }

    # Always persist locally (fallback / admin list)
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
            "mode": mode,
            "prompt_set_id": prompt_set_id,
            "task1_word_count": record["task1_word_count"],
            "task2_word_count": record["task2_word_count"],
            "time_used_seconds": time_used_seconds,
            "auto_submitted": auto_submitted,
            "file": f"submissions/{sid}.json",
        },
    )
    save_index(index)

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


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    nxt = request.args.get("next") or request.form.get("next") or url_for("admin")
    if request.method == "POST":
        password = request.form.get("password") or ""
        if password == ADMIN_PASSWORD:
            session["admin_ok"] = True
            return redirect(nxt)
        error = "密码错误，请重试。"
    return render_template("admin_login.html", error=error, next=nxt)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_ok", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin():
    index = load_index()
    return render_template(
        "admin.html",
        submissions=index.get("submissions", []),
        notion_on=notion_enabled(),
    )


@app.route("/admin/submission/<sid>")
@admin_required
def admin_submission(sid: str):
    path = SUBMISSIONS_DIR / f"{sid}.json"
    if not path.exists():
        return "未找到该答卷", 404
    with path.open(encoding="utf-8") as f:
        record = json.load(f)
    return render_template("admin_detail.html", record=record)


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
            "mode",
            "prompt_set_id",
            "task1_word_count",
            "task2_word_count",
            "time_used_seconds",
            "time_remaining_seconds",
            "auto_submitted",
            "task1_text",
            "task2_text",
        ]
    )
    for item in index.get("submissions", []):
        path = SUBMISSIONS_DIR / f"{item['id']}.json"
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as f:
            r = json.load(f)
        writer.writerow(
            [
                r.get("id"),
                r.get("timestamp"),
                r.get("candidate_name") or "",
                r.get("mode"),
                r.get("prompt_set_id"),
                r.get("task1_word_count"),
                r.get("task2_word_count"),
                r.get("time_used_seconds"),
                r.get("time_remaining_seconds"),
                r.get("auto_submitted"),
                (r.get("task1_text") or "").replace("\n", "\\n"),
                (r.get("task2_text") or "").replace("\n", "\\n"),
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
    # Local default 127.0.0.1; production / LAN: HOST=0.0.0.0
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"IELTS Writing Mock → http://{host}:{port}/")
    print(f"Health → http://{host}:{port}/health")
    print(f"教师后台 → http://{host}:{port}/admin")
    print(f"Notion sync: {'ON' if notion_enabled() else 'OFF'}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
