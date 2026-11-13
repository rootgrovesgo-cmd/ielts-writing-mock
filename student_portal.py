"""Student portal helpers: owned-attempt lists and post-submit review views."""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

import access
import reading_scoring as rs
import report_pdf

MODULE_LABELS = {
    "writing": "写作",
    "reading": "阅读",
}

MODE_LABELS = {
    "writing": {
        "full": "完整测试",
        "task1": "仅 Task 1",
        "task2": "仅 Task 2",
    },
    "reading": {
        "full": "完整测试",
        "passage1": "Passage 1",
        "passage2": "Passage 2",
        "passage3": "Passage 3",
    },
}

WRITING_SCORE_KEYS = (
    "score",
    "total",
    "band",
    "band_estimate",
    "task1_score",
    "task2_score",
    "task1_band",
    "task2_band",
    "official_score",
    "official_band",
    "marking",
    "descriptors",
    "band_descriptors",
)


def module_of(record: dict | None) -> str:
    if not record:
        return "writing"
    mod = (record.get("module") or "").strip().lower()
    if mod == "reading":
        return "reading"
    return "writing"


def module_label(module: str | None) -> str:
    return MODULE_LABELS.get((module or "writing").strip().lower(), "写作")


def mode_label(module: str | None, mode: str | None) -> str:
    mod = (module or "writing").strip().lower()
    key = (mode or "full").strip().lower()
    return MODE_LABELS.get(mod, {}).get(key, key or "完整测试")


def format_shanghai(timestamp: str | None) -> str:
    raw = (timestamp or "").strip()
    if not raw:
        return "—"
    try:
        ts = datetime.fromisoformat(raw)
    except ValueError:
        return raw
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=access.TZ_SHANGHAI)
    else:
        ts = ts.astimezone(access.TZ_SHANGHAI)
    return ts.strftime("%Y-%m-%d %H:%M")


def duration_label(seconds) -> str:
    return report_pdf.format_duration(seconds)


def owns_record(record: dict | None, ident: dict | None) -> bool:
    """True if this submission belongs to the logged-in student."""
    if not record or not ident:
        return False
    uid = ident.get("user_id")
    rec_uid = record.get("user_id")
    if uid and rec_uid and str(uid) == str(rec_uid):
        return True
    code_id = ident.get("invite_code_id")
    rec_code = record.get("invite_code_id")
    if not code_id or not rec_code or str(code_id) != str(rec_code):
        return False
    return access.normalize_name(record.get("candidate_name")) == access.normalize_name(
        ident.get("candidate_name")
    )


def list_own_attempts(index: dict, ident: dict) -> list[dict]:
    items = [
        item
        for item in (index.get("submissions") or [])
        if owns_record(item, ident) and item.get("id")
    ]
    items.sort(key=lambda s: s.get("timestamp") or "", reverse=True)
    return [summarize_attempt(item) for item in items]


def summarize_attempt(item: dict) -> dict:
    module = module_of(item)
    band = None
    score_label = None
    if module == "reading":
        score = item.get("score")
        total = item.get("total")
        if score is not None and total is not None:
            score_label = f"{score}/{total}"
        band = rs.format_band(item.get("band_estimate"))
    return {
        "id": item.get("id"),
        "module": module,
        "module_label": module_label(module),
        "mode": item.get("mode") or "full",
        "mode_label": mode_label(module, item.get("mode")),
        "timestamp": item.get("timestamp") or "",
        "when": format_shanghai(item.get("timestamp")),
        "duration": duration_label(item.get("time_used_seconds")),
        "score_label": score_label,
        "band_label": band,
        "task1_word_count": item.get("task1_word_count") if module == "writing" else None,
        "task2_word_count": item.get("task2_word_count") if module == "writing" else None,
        "auto_submitted": bool(item.get("auto_submitted")),
    }


def writing_prompts_for(record: dict, prompts_data: dict) -> tuple[dict | None, dict | None, dict | None]:
    set_id = record.get("prompt_set_id")
    found = None
    for item in prompts_data.get("sets") or []:
        if item.get("id") == set_id:
            found = item
            break
    if not found:
        return None, None, None
    return found.get("task1"), found.get("task2"), found


def writing_visual_html(task: dict | None) -> str:
    if not task:
        return ""
    if task.get("image"):
        return _render_image(task["image"])
    if task.get("line_chart"):
        return _render_line_chart(task["line_chart"])
    if task.get("flowchart"):
        return _render_flowchart(task["flowchart"])
    if task.get("chart"):
        return _render_bar_table(task["chart"])
    if task.get("table"):
        return _render_table(task["table"])
    if task.get("process_steps"):
        return _render_process(task["process_steps"])
    return ""


def _render_image(image: dict) -> str:
    src = escape(str(image.get("src") or ""))
    alt = escape(str(image.get("alt") or "Task 1 chart"))
    if not src:
        return ""
    return (
        f'<div class="chart-wrap image-wrap">'
        f'<img class="task1-image" src="{src}" alt="{alt}" />'
        f"</div>"
    )


def _render_table(table: dict) -> str:
    headers = table.get("headers") or []
    rows = table.get("rows") or []
    parts = ['<div class="table-wrap"><table class="data"><thead><tr>']
    for h in headers:
        parts.append(f"<th>{escape(str(h))}</th>")
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>")
        for cell in row:
            parts.append(f"<td>{escape(str(cell))}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def _render_process(steps: list) -> str:
    parts = ['<div class="process-wrap"><ol class="process-list">']
    for step in steps or []:
        parts.append(f"<li>{escape(str(step))}</li>")
    parts.append("</ol></div>")
    return "".join(parts)


def _render_bar_table(chart: dict) -> str:
    cats = chart.get("categories") or []
    series = chart.get("series") or []
    y_label = escape(str(chart.get("yLabel") or ""))
    parts = ['<div class="chart-wrap">']
    if y_label:
        parts.append(f'<div class="muted" style="text-align:center;margin-bottom:6px">{y_label}</div>')
    parts.append('<table class="data"><thead><tr><th></th>')
    for cat in cats:
        parts.append(f"<th>{escape(str(cat))}</th>")
    parts.append("</tr></thead><tbody>")
    for ser in series:
        parts.append(f"<tr><th>{escape(str(ser.get('name') or ''))}</th>")
        for val in ser.get("values") or []:
            parts.append(f"<td>{escape(str(val))}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def _render_line_chart(chart: dict) -> str:
    labels = chart.get("xLabels") or []
    series = chart.get("series") or []
    values = [v for ser in series for v in (ser.get("values") or [])]
    max_val = max(values) if values else 1
    width, height = 560, 280
    pad_l, pad_b, pad_t, pad_r = 48, 40, 24, 20
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    colors = ["#5c6b73", "#a67c52", "#6f8f7a", "#7d8b99"]
    n = max(len(labels) - 1, 1)
    ticks = []
    for t in range(5):
        val = round((max_val * t) / 4)
        y = pad_t + plot_h - (plot_h * t) / 4
        ticks.append(
            f'<line x1="{pad_l}" y1="{y}" x2="{width - pad_r}" y2="{y}" stroke="#d6d0c8"/>'
        )
        ticks.append(
            f'<text x="{pad_l - 6}" y="{y + 3}" text-anchor="end" font-size="10" fill="#8a847c">{val}</text>'
        )
    x_labels = []
    for i, lab in enumerate(labels):
        x = pad_l + (plot_w * i) / n
        x_labels.append(
            f'<text x="{x}" y="{height - 12}" text-anchor="middle" font-size="10" fill="#3f3c3a">{escape(str(lab))}</text>'
        )
    lines = []
    for si, ser in enumerate(series):
        color = colors[si % len(colors)]
        pts = []
        circles = []
        for i, v in enumerate(ser.get("values") or []):
            x = pad_l + (plot_w * i) / n
            y = pad_t + plot_h - (float(v) / max_val) * plot_h
            pts.append(f"{x},{y}")
            circles.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{color}"/>')
        if pts:
            lines.append(
                f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{" ".join(pts)}"/>'
            )
        lines.extend(circles)
    legend = "".join(
        f'<span><i class="swatch" style="background:{colors[i % len(colors)]}"></i>{escape(str(s.get("name") or ""))}</span>'
        for i, s in enumerate(series)
    )
    y_label = escape(str(chart.get("yLabel") or ""))
    title = f'<div class="muted" style="text-align:center;margin-bottom:6px">{y_label}</div>' if y_label else ""
    return (
        f'<div class="chart-wrap">{title}'
        f'<div class="line-chart"><svg viewBox="0 0 {width} {height}" role="img" aria-label="Line graph">'
        f'{"".join(ticks)}{"".join(lines)}{"".join(x_labels)}</svg></div>'
        f'<div class="legend">{legend}</div></div>'
    )


def _render_flowchart(flow: dict) -> str:
    steps = (flow or {}).get("steps") or []
    box_w, box_h, gap, pad_x, pad_y = 200, 70, 28, 40, 20
    width = box_w + pad_x * 2
    height = pad_y * 2 + len(steps) * box_h + max(len(steps) - 1, 0) * gap
    shapes = []
    for i, step in enumerate(steps):
        y = pad_y + i * (box_h + gap)
        x = pad_x
        shapes.append(
            f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="10" fill="#eef2f4" stroke="#5c6b73" stroke-width="2"/>'
        )
        shapes.append(
            f'<text x="{x + box_w / 2}" y="{y + 28}" text-anchor="middle" font-size="14" font-weight="700" fill="#3f3c3a">{escape(str(step.get("label") or ""))}</text>'
        )
        shapes.append(
            f'<text x="{x + box_w / 2}" y="{y + 50}" text-anchor="middle" font-size="11" fill="#8a847c">{escape(str(step.get("detail") or ""))}</text>'
        )
        if i < len(steps) - 1:
            ax = x + box_w / 2
            y1 = y + box_h
            y2 = y + box_h + gap
            shapes.append(
                f'<line x1="{ax}" y1="{y1}" x2="{ax}" y2="{y2 - 8}" stroke="#8a847c" stroke-width="2"/>'
            )
            shapes.append(
                f'<polygon points="{ax},{y2} {ax - 6},{y2 - 10} {ax + 6},{y2 - 10}" fill="#8a847c"/>'
            )
    title = ""
    if flow and flow.get("title"):
        title = f'<div class="muted" style="text-align:center;margin-bottom:8px">{escape(str(flow["title"]))}</div>'
    return (
        f'<div class="chart-wrap flowchart-wrap">{title}'
        f'<div class="flowchart"><svg viewBox="0 0 {width} {height}" role="img" aria-label="Process diagram">'
        f'{"".join(shapes)}</svg></div></div>'
    )


def writing_view(record: dict, prompts_data: dict) -> dict:
    """Safe writing review: prompts and the student's text, never official scores."""
    task1, task2, prompt_set = writing_prompts_for(record, prompts_data)
    mode = (record.get("mode") or "full").strip().lower()
    show_t1 = mode in {"full", "task1"} or bool((record.get("task1_text") or "").strip())
    show_t2 = mode in {"full", "task2"} or bool((record.get("task2_text") or "").strip())
    return {
        "module": "writing",
        "module_label": "写作",
        "mode_label": mode_label("writing", mode),
        "set_title": (prompt_set or {}).get("title") or record.get("prompt_set_id") or "",
        "when": format_shanghai(record.get("timestamp")),
        "duration": duration_label(record.get("time_used_seconds")),
        "auto_submitted": bool(record.get("auto_submitted")),
        "show_task1": show_t1,
        "show_task2": show_t2,
        "task1_instruction": (task1 or {}).get("instruction") or "",
        "task1_visual": writing_visual_html(task1) if show_t1 else "",
        "task1_text": record.get("task1_text") or "",
        "task1_word_count": int(record.get("task1_word_count") or 0),
        "task2_instruction": (task2 or {}).get("instruction") or "",
        "task2_text": record.get("task2_text") or "",
        "task2_word_count": int(record.get("task2_word_count") or 0),
    }


def _answer_map(record: dict) -> dict[str, str]:
    answers = record.get("answers") or {}
    if not isinstance(answers, dict):
        return {}
    return {str(k): ("" if v is None else str(v)) for k, v in answers.items()}


def _marking_by_q(record: dict, keys: dict | None = None) -> dict[int, dict]:
    by_q: dict[int, dict] = {}
    for row in record.get("marking") or []:
        try:
            q = int(row.get("q"))
        except (TypeError, ValueError):
            continue
        by_q[q] = dict(row)
    if by_q:
        return by_q
    # Older or partial records: re-score from saved answers, never from the client.
    mode = (record.get("mode") or "full").strip().lower()
    result = rs.score_paper(_answer_map(record), mode=mode, keys=keys)
    for row in result.get("marking") or []:
        by_q[int(row["q"])] = dict(row)
    return by_q


def _explanation_map(keys: dict) -> dict[int, str]:
    questions = keys.get("questions") or {}
    out: dict[int, str] = {}
    for q, meta in questions.items():
        try:
            num = int(q)
        except (TypeError, ValueError):
            continue
        if isinstance(meta, dict):
            out[num] = meta.get("explanation") or ""
        else:
            out[num] = ""
    return out


def _question_range(mode: str) -> set[int]:
    info = rs.MODES.get(mode) or rs.MODES["full"]
    return set(info["questions"])


def _walk_notes_for_q(node: Any, qnum: int) -> str | None:
    if isinstance(node, dict):
        parts = node.get("parts")
        if isinstance(parts, list) and any(
            isinstance(p, dict) and p.get("q") == qnum for p in parts
        ):
            bits: list[str] = []
            for part in parts:
                if isinstance(part, str):
                    bits.append(part)
                elif isinstance(part, dict) and "q" in part:
                    bits.append("______")
            return "".join(bits).strip()
        for key in ("sections", "items", "children", "notes"):
            found = _walk_notes_for_q(node.get(key), qnum)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _walk_notes_for_q(item, qnum)
            if found:
                return found
    return None


def question_context(paper: dict, qnum: int) -> dict:
    """Stem and enough surrounding context from the student paper (no keys)."""
    for group in paper.get("groups") or []:
        start, end = group.get("from"), group.get("to")
        if start is None or end is None or not (start <= qnum <= end):
            continue
        ctx = {
            "q": qnum,
            "type": group.get("type") or "",
            "heading": group.get("heading") or "",
            "instructions": list(group.get("instructions") or []),
            "passage": group.get("passage"),
            "stem": "",
            "options": None,
            "endings": None,
        }
        gtype = group.get("type")
        if gtype == "notes":
            ctx["stem"] = _walk_notes_for_q(group.get("notes"), qnum) or ""
            title = (group.get("notes") or {}).get("title")
            if title:
                ctx["notes_title"] = title
        else:
            for item in group.get("items") or []:
                if item.get("q") == qnum:
                    ctx["stem"] = item.get("stem") or ""
                    if item.get("options"):
                        ctx["options"] = item.get("options")
                    break
            if gtype == "matching_endings" and group.get("endings"):
                ctx["endings"] = group.get("endings")
            if group.get("legend"):
                ctx["legend"] = group.get("legend")
        return ctx
    return {"q": qnum, "type": "", "heading": "", "instructions": [], "stem": "", "passage": None}


def _is_blank(answer: str | None) -> bool:
    return not (answer or "").strip()


def _question_rows(
    record: dict,
    paper: dict,
    keys: dict,
    *,
    mistakes_only: bool,
) -> list[dict]:
    mode = (record.get("mode") or "full").strip().lower()
    allowed = _question_range(mode)
    answers = _answer_map(record)
    marking = _marking_by_q(record, keys)
    explanations = _explanation_map(keys)
    rows: list[dict] = []
    for q in sorted(allowed):
        mark = marking.get(q) or {}
        student = mark.get("student")
        if student is None:
            student = answers.get(str(q), "")
        student = "" if student is None else str(student)
        correct = mark.get("correct")
        if correct is None:
            meta = (keys.get("questions") or {}).get(str(q)) or (keys.get("questions") or {}).get(q)
            if isinstance(meta, dict):
                correct = meta.get("answer") or ""
            elif meta is not None:
                correct = str(meta)
            else:
                correct = ""
        # Unanswered items count as mistakes even if a stored row was marked ok.
        ok = bool(mark.get("ok")) and not _is_blank(student)
        if mistakes_only and ok:
            continue
        ctx = question_context(paper, q)
        rows.append(
            {
                "q": q,
                "stem": ctx.get("stem") or "",
                "heading": ctx.get("heading") or "",
                "instructions": ctx.get("instructions") or [],
                "notes_title": ctx.get("notes_title") or "",
                "options": ctx.get("options"),
                "endings": ctx.get("endings"),
                "legend": ctx.get("legend"),
                "passage": ctx.get("passage"),
                "type": ctx.get("type") or "",
                "student": student,
                "student_blank": _is_blank(student),
                "correct": "" if correct is None else str(correct),
                "explanation": explanations.get(q) or "",
                "ok": ok,
            }
        )
    return rows


def _passages_for_mode(paper: dict, mode: str) -> list[dict]:
    allowed = _question_range(mode)
    passage_ids: set[int] = set()
    for group in paper.get("groups") or []:
        start, end = group.get("from"), group.get("to")
        if start is None or end is None:
            continue
        if any(q in allowed for q in range(start, end + 1)):
            if group.get("passage") is not None:
                passage_ids.add(int(group["passage"]))
    if mode == "passage1":
        passage_ids = {1}
    elif mode == "passage2":
        passage_ids = {2}
    elif mode == "passage3":
        passage_ids = {3}
    out = []
    for passage in paper.get("passages") or []:
        if int(passage.get("id") or 0) in passage_ids or (not passage_ids and mode == "full"):
            out.append(
                {
                    "id": passage.get("id"),
                    "label": passage.get("label") or f"Passage {passage.get('id')}",
                    "title": passage.get("title") or "",
                    "paragraphs": list(passage.get("paragraphs") or []),
                }
            )
    return out


def _groups_for_detail(paper: dict, record: dict, keys: dict) -> list[dict]:
    mode = (record.get("mode") or "full").strip().lower()
    allowed = _question_range(mode)
    rows_by_q = {row["q"]: row for row in _question_rows(record, paper, keys, mistakes_only=False)}
    groups = []
    for group in paper.get("groups") or []:
        start, end = group.get("from"), group.get("to")
        if start is None or end is None:
            continue
        qnums = [q for q in range(start, end + 1) if q in allowed]
        if not qnums:
            continue
        groups.append(
            {
                "id": group.get("id"),
                "heading": group.get("heading") or "",
                "instructions": list(group.get("instructions") or []),
                "type": group.get("type") or "",
                "passage": group.get("passage"),
                "notes_title": (group.get("notes") or {}).get("title") or "",
                "questions": [rows_by_q[q] for q in qnums if q in rows_by_q],
            }
        )
    return groups


def part_time_pills(record: dict) -> list[dict]:
    times = record.get("part_times") or {}
    if not isinstance(times, dict):
        return []
    mode = (record.get("mode") or "full").strip().lower()
    if mode == "passage1":
        keys = ("1",)
    elif mode == "passage2":
        keys = ("2",)
    elif mode == "passage3":
        keys = ("3",)
    else:
        keys = ("1", "2", "3")
    has_any = any(int(times.get(k) or times.get(int(k) or 0) or 0) for k in keys)
    pills = []
    for key in keys:
        raw = times.get(key)
        if raw is None:
            raw = times.get(int(key)) if str(key).isdigit() else 0
        try:
            seconds = int(raw or 0)
        except (TypeError, ValueError):
            seconds = 0
        pills.append(
            {
                "id": key,
                "label": f"Passage {key} {duration_label(seconds) if has_any else '本题卷未记录'}",
                "recorded": has_any,
            }
        )
    return pills


def reading_detail_view(record: dict, paper: dict, keys: dict) -> dict:
    """Post-submit reading review for the owner: paper, answers, keys, 解析."""
    mode = (record.get("mode") or "full").strip().lower()
    score = record.get("score")
    total = record.get("total")
    questions = _question_rows(record, paper, keys, mistakes_only=False)
    mistakes = [row for row in questions if not row["ok"] or row["student_blank"]]
    return {
        "module": "reading",
        "module_label": "阅读",
        "mode_label": mode_label("reading", mode),
        "set_title": paper.get("title") or record.get("prompt_set_id") or "",
        "when": format_shanghai(record.get("timestamp")),
        "duration": duration_label(record.get("time_used_seconds")),
        "auto_submitted": bool(record.get("auto_submitted")),
        "score": score,
        "total": total,
        "score_label": f"{score}/{total}" if score is not None and total is not None else None,
        "band_label": rs.format_band(record.get("band_estimate")),
        "part_times": part_time_pills(record),
        "passages": _passages_for_mode(paper, mode),
        "groups": _groups_for_detail(paper, record, keys),
        "questions": questions,
        "mistake_count": len(mistakes),
        "total_questions": len(questions),
    }


def reading_mistakes_view(record: dict, paper: dict, keys: dict) -> dict:
    """Wrong and unanswered items only, with the student's answer, key, and 解析."""
    mode = (record.get("mode") or "full").strip().lower()
    mistakes = _question_rows(record, paper, keys, mistakes_only=True)
    allowed = _question_range(mode)
    return {
        "module": "reading",
        "module_label": "阅读",
        "mode_label": mode_label("reading", mode),
        "when": format_shanghai(record.get("timestamp")),
        "duration": duration_label(record.get("time_used_seconds")),
        "score": record.get("score"),
        "total": record.get("total"),
        "score_label": (
            f"{record.get('score')}/{record.get('total')}"
            if record.get("score") is not None and record.get("total") is not None
            else None
        ),
        "band_label": rs.format_band(record.get("band_estimate")),
        "mistakes": mistakes,
        "mistake_count": len(mistakes),
        "total_questions": len(allowed),
        "all_correct": len(mistakes) == 0,
    }


def writing_has_official_score(view: dict) -> bool:
    return any(view.get(key) not in (None, "", []) for key in WRITING_SCORE_KEYS)


def _slim_question_rows(rows: list[dict]) -> list[dict]:
    slim = []
    for row in rows:
        slim.append(
            {
                "q": row.get("q"),
                "student": row.get("student") or "",
                "student_blank": bool(row.get("student_blank")),
                "correct": row.get("correct") or "",
                "explanation": row.get("explanation") or "",
                "ok": bool(row.get("ok")),
            }
        )
    return slim


def attempt_review_payload(
    record: dict,
    *,
    paper: dict | None = None,
    keys: dict | None = None,
    prompts_data: dict | None = None,
) -> dict:
    """Owner-scoped payload for the read-only exam-UI review. No teacher extras."""
    module = module_of(record)
    payload = {
        "ok": True,
        "id": record.get("id"),
        "module": module,
        "module_label": module_label(module),
        "mode": (record.get("mode") or "full"),
        "mode_label": mode_label(module, record.get("mode")),
        "timestamp": record.get("timestamp") or "",
        "when": format_shanghai(record.get("timestamp")),
        "time_used_seconds": record.get("time_used_seconds") or 0,
        "duration": duration_label(record.get("time_used_seconds")),
        "auto_submitted": bool(record.get("auto_submitted")),
    }
    if module == "reading":
        detail = reading_detail_view(record, paper or {}, keys or {})
        payload.update(
            {
                "score": detail.get("score"),
                "total": detail.get("total"),
                "score_label": detail.get("score_label"),
                "band_label": detail.get("band_label"),
                "part_times": detail.get("part_times") or [],
                "answers": _answer_map(record),
                "flags": record.get("flags") or [],
                "paper": paper or {},
                "questions": _slim_question_rows(detail.get("questions") or []),
                "mistake_count": detail.get("mistake_count") or 0,
                "total_questions": detail.get("total_questions") or 0,
            }
        )
        return payload

    task1, task2, prompt_set = writing_prompts_for(record, prompts_data or {})
    set_payload = None
    if prompt_set:
        set_payload = {
            "id": prompt_set.get("id"),
            "title": prompt_set.get("title"),
            "task1": task1,
            "task2": task2,
        }
    payload.update(
        {
            "prompt_set_id": record.get("prompt_set_id") or "",
            "set": set_payload,
            "task1_text": record.get("task1_text") or "",
            "task2_text": record.get("task2_text") or "",
            "task1_word_count": int(record.get("task1_word_count") or 0),
            "task2_word_count": int(record.get("task2_word_count") or 0),
        }
    )
    return payload
