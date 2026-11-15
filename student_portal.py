"""Student portal helpers: owned-attempt lists and post-submit review views."""

from __future__ import annotations

import math
import re
from datetime import datetime
from html import escape
from typing import Any

import access
import reading_scoring as rs
import listening_scoring as ls
import reading_review as rr
import report_pdf

MODULE_LABELS = {
    "writing": "写作",
    "reading": "阅读",
    "listening": "听力",
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
    "listening": {
        "full": "完整测试",
        "section1": "Section 1",
        "section2": "Section 2",
        "section3": "Section 3",
        "section4": "Section 4",
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



def set_label(prompt_set_id: str | None) -> str:
    """Human set name, e.g. set-a → Set A."""
    token = (prompt_set_id or "").strip().lower()
    if not token:
        return "Set"
    if token.startswith("set-"):
        suffix = token[4:]
        if suffix.isalpha() and 1 <= len(suffix) <= 3:
            return f"Set {suffix.upper()}"
        if suffix.isdigit():
            return f"Set {suffix}"
    return token.replace("-", " ").title()


def parse_teacher_band(raw) -> float | None:
    """Parse a 0–9 IELTS band in 0.5 steps. Empty is None; invalid raises ValueError."""
    text = "" if raw is None else str(raw).strip()
    if not text:
        return None
    try:
        value = float(text)
    except (TypeError, ValueError) as exc:
        raise ValueError("分数须为 0 到 9 之间的 0.5 档。") from exc
    quantized = round(value * 2) / 2
    if abs(value - quantized) > 1e-9 or quantized < 0 or quantized > 9:
        raise ValueError("分数须为 0 到 9 之间的 0.5 档。")
    return quantized


def format_teacher_band(band) -> str | None:
    if band is None or band == "":
        return None
    try:
        value = float(band)
    except (TypeError, ValueError):
        return None
    if value.is_integer():
        return str(int(value))
    return str(value)


def writing_teacher_band(item: dict | None):
    if not item:
        return None
    for key in ("teacher_band", "teacher_score"):
        if item.get(key) not in (None, ""):
            try:
                return parse_teacher_band(item.get(key))
            except ValueError:
                continue
    return None


def attempt_caption(item: dict) -> str:
    """Set + score line shown under a lit Pikachu and on the attempt card."""
    module = module_of(item)
    head = f"{module_label(module)} {set_label(item.get('prompt_set_id'))}"
    mode = (item.get("mode") or "full").strip().lower()
    if mode and mode != "full":
        head = f"{head} · {mode_label(module, mode)}"
    if module in {"reading", "listening"}:
        parts = [head]
        score = item.get("score")
        total = item.get("total")
        if score is not None and total is not None:
            parts.append(f"{score}/{total}")
        band_fn = ls.format_band if module == "listening" else rs.format_band
        band = band_fn(item.get("band_estimate"))
        if band:
            parts.append(band)
        return " · ".join(parts)
    band = format_teacher_band(writing_teacher_band(item))
    if band:
        return f"{head} · {band}"
    return f"{head} · 待评分"


def module_of(record: dict | None) -> str:
    if not record:
        return "writing"
    mod = (record.get("module") or "").strip().lower()
    if mod in {"reading", "listening"}:
        return mod
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
    """True if this submission belongs to the logged-in student.

    Invitation codes are issued one per student, so a record with an
    invite_code_id is owned by whoever is logged in with that same code,
    regardless of the typed candidate name. Records that predate invite
    codes may still match by user_id. A name-only match is kept only
    when neither side has an invite_code_id, so coded sessions cannot
    claim an uncoded paper by typed name alone.
    """
    if not record or not ident:
        return False
    code_id = ident.get("invite_code_id")
    rec_code = record.get("invite_code_id")
    if code_id and rec_code:
        return str(code_id) == str(rec_code)
    uid = ident.get("user_id")
    rec_uid = record.get("user_id")
    if uid and rec_uid and str(uid) == str(rec_uid):
        return True
    if rec_code or code_id:
        # A coded session must not claim an uncoded paper by name alone,
        # and a coded paper is never shown without a matching code.
        return False
    rec_name = access.normalize_name(record.get("candidate_name"))
    ident_name = access.normalize_name(ident.get("candidate_name"))
    return bool(rec_name) and rec_name == ident_name


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
    if module in {"reading", "listening"}:
        score = item.get("score")
        total = item.get("total")
        if score is not None and total is not None:
            score_label = f"{score}/{total}"
        band_fn = ls.format_band if module == "listening" else rs.format_band
        band = band_fn(item.get("band_estimate"))
    teacher_band = writing_teacher_band(item) if module == "writing" else None
    summary = {
        "id": item.get("id"),
        "module": module,
        "module_label": module_label(module),
        "mode": item.get("mode") or "full",
        "mode_label": mode_label(module, item.get("mode")),
        "prompt_set_id": item.get("prompt_set_id") or "",
        "set_label": set_label(item.get("prompt_set_id")),
        "timestamp": item.get("timestamp") or "",
        "when": format_shanghai(item.get("timestamp")),
        "duration": duration_label(item.get("time_used_seconds")),
        "score_label": score_label,
        "band_label": band,
        "teacher_band": teacher_band,
        "teacher_band_label": format_teacher_band(teacher_band) if module == "writing" else None,
        "task1_word_count": item.get("task1_word_count") if module == "writing" else None,
        "task2_word_count": item.get("task2_word_count") if module == "writing" else None,
        "auto_submitted": bool(item.get("auto_submitted")),
    }
    summary["caption"] = attempt_caption({**item, **summary})
    return summary


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
    if task.get("table") and task.get("line_chart"):
        return (
            '<div class="combined-visual">'
            f"{_render_table(task['table'])}{_render_line_chart(task['line_chart'])}"
            "</div>"
        )
    if task.get("line_chart"):
        return _render_line_chart(task["line_chart"])
    if task.get("flowchart"):
        return _render_flowchart(task["flowchart"])
    if task.get("pie_charts"):
        return _render_pie_charts(task["pie_charts"])
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
    caption = table.get("caption") or table.get("title") or ""
    parts = ['<div class="table-wrap"><table class="data">']
    if caption:
        parts.append(f"<caption>{escape(str(caption))}</caption>")
    parts.append("<thead><tr>")
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
    if chart.get("yMax") is not None:
        max_val = float(chart["yMax"])
    else:
        max_val = max(values) if values else 1
    width, height = 560, 280
    pad_l, pad_b, pad_t, pad_r = 48, 40, 24, 20
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    colors = ["#5c6b73", "#a67c52", "#6f8f7a", "#7d8b99", "#8a6a9a"]
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


def _fmt_svg(n: float) -> str:
    return f"{round(float(n), 3):.3f}".rstrip("0").rstrip(".")


def _hex_luminance(color: str) -> float:
    raw = str(color or "").lstrip("#")
    if len(raw) != 6:
        return 0.0
    channels = [int(raw[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def _lin(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (_lin(channel) for channel in channels)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _pie_label_fill(color: str, outside: bool) -> str:
    if outside:
        return "#111111"
    return "#111111" if _hex_luminance(color) >= 0.35 else "#ffffff"


def _render_pie_charts(data: dict) -> str:
    categories = (data or {}).get("categories") or []
    charts = (data or {}).get("charts") or []
    unit = (data or {}).get("unit") or "%"
    colors = ["#1a1a1a", "#4a4a4a", "#8a8a8a", "#c8c8c8", "#ffffff"]
    size, cx, cy, radius = 220, 110, 110, 80
    pies = []
    for chart in charts:
        values = [float(v) for v in (chart.get("values") or [])]
        total = sum(values) or 1
        angle = -math.pi / 2
        slices = []
        labels = []
        for i, value in enumerate(values):
            frac = value / total
            start, end = angle, angle + frac * 2 * math.pi
            angle = end
            if value <= 0:
                continue
            color = colors[i % len(colors)]
            x1 = cx + radius * math.cos(start)
            y1 = cy + radius * math.sin(start)
            x2 = cx + radius * math.cos(end)
            y2 = cy + radius * math.sin(end)
            large_arc = 1 if frac > 0.5 else 0
            slices.append(
                f'<path d="M {_fmt_svg(cx)},{_fmt_svg(cy)} L {_fmt_svg(x1)},{_fmt_svg(y1)} '
                f'A {radius},{radius} 0 {large_arc} 1 {_fmt_svg(x2)},{_fmt_svg(y2)} Z" '
                f'fill="{color}" stroke="#222" stroke-width="1"/>'
            )
            mid = (start + end) / 2
            # Keep labels on the slice except when a wedge is too thin to fit text.
            outside = frac < 0.03
            label_r = radius * (1.18 if outside else 0.62)
            lx = cx + label_r * math.cos(mid)
            ly = cy + label_r * math.sin(mid)
            fill = _pie_label_fill(color, outside)
            number = str(int(value)) if float(value).is_integer() else str(value)
            font_size = 9 if (not outside and value < 10) else 11
            labels.append(
                f'<text x="{_fmt_svg(lx)}" y="{_fmt_svg(ly)}" text-anchor="middle" '
                f'dominant-baseline="middle" font-size="{font_size}" font-weight="600" fill="{fill}">'
                f"{escape(number + str(unit))}</text>"
            )
        aria = escape(str(chart.get("label") or "Pie chart"))
        pies.append(
            f'<div class="pie-chart">'
            f'<div class="pie-chart-label">{escape(str(chart.get("label") or ""))}</div>'
            f'<svg viewBox="0 0 {size} {size}" role="img" aria-label="{aria}">'
            f'{"".join(slices)}{"".join(labels)}</svg></div>'
        )
    legend = "".join(
        f'<span><i class="swatch" style="background:{colors[i % len(colors)]}"></i>'
        f"{escape(str(cat))}</span>"
        for i, cat in enumerate(categories)
    )
    title = ""
    if (data or {}).get("title"):
        title = f'<div class="pie-charts-title">{escape(str(data["title"]))}</div>'
    return (
        f'<div class="chart-wrap pie-charts">{title}'
        f'<div class="pie-charts-row">{"".join(pies)}</div>'
        f'<div class="legend">{legend}</div></div>'
    )


def _flowchart_num(value) -> str:
    number = float(value)
    if number == int(number):
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def _flowchart_wrap_text(text: str, max_chars: int = 22) -> list[str]:
    words = str(text or "").split()
    if not words:
        return []
    lines = [words[0]]
    for word in words[1:]:
        trial = f"{lines[-1]} {word}"
        if len(trial) <= max_chars:
            lines[-1] = trial
        else:
            lines.append(word)
    return lines


def _flowchart_kind(step: dict, index: int) -> str:
    label = str((step or {}).get("label") or "").lower()
    mapping = (
        ("collection", "collection"),
        ("sorting", "sorting"),
        ("washing", "washing"),
        ("shred", "washing"),
        ("melting", "melting"),
        ("pellet", "melting"),
        ("manufactur", "manufacturing"),
        ("distribution", "distribution"),
    )
    for needle, kind in mapping:
        if needle in label:
            return kind
    fallback = (
        "collection",
        "sorting",
        "washing",
        "melting",
        "manufacturing",
        "distribution",
    )
    if 0 <= index < len(fallback):
        return fallback[index]
    return "collection"


_FLOWCHART_BOTTLE = {
    "sm": (6, 2, 4, 5, 10, 16),
    "md": (6, 3, 4, 6, 12, 20),
    "lg": (8, 3, 4, 7, 14, 24),
}


def _flowchart_bottle(
    x: float,
    y: float,
    size: str = "md",
    fill: str = "#f4f4f4",
    rotate: float = 0,
) -> str:
    cw, ch, nw, nh, bw, bh = _FLOWCHART_BOTTLE[size]
    body_y = y - bh
    neck_y = body_y - nh
    cap_y = neck_y - ch
    inner = (
        f'<rect x="{_flowchart_num(x - cw / 2)}" y="{_flowchart_num(cap_y)}" width="{_flowchart_num(cw)}" height="{_flowchart_num(ch)}" rx="1" fill="#444" stroke="#222" stroke-width="1"/>'
        f'<rect x="{_flowchart_num(x - nw / 2)}" y="{_flowchart_num(neck_y)}" width="{_flowchart_num(nw)}" height="{_flowchart_num(nh)}" fill="{fill}" stroke="#222" stroke-width="1"/>'
        f'<rect x="{_flowchart_num(x - bw / 2)}" y="{_flowchart_num(body_y)}" width="{_flowchart_num(bw)}" height="{_flowchart_num(bh)}" rx="2" fill="{fill}" stroke="#222" stroke-width="1.3"/>'
    )
    if rotate:
        return (
            f'<g transform="rotate({_flowchart_num(rotate)} {_flowchart_num(x)} {_flowchart_num(y)})">'
            f"{inner}</g>"
        )
    return f"<g>{inner}</g>"


def _flowchart_art(kind: str) -> str:
    bottle = _flowchart_bottle
    if kind == "collection":
        return (
            '<line x1="16" y1="76" x2="144" y2="76" stroke="#222" stroke-width="1.2"/>'
            + bottle(36, 48, "md", "#f7f7f7")
            + bottle(52, 50, "sm", "#e4e4e4")
            + '<path d="M22,38 L28,76 L64,76 L70,38 Z" fill="#d0d0d0" stroke="#222" stroke-width="1.5"/>'
            + '<line x1="20" y1="38" x2="72" y2="38" stroke="#222" stroke-width="2"/>'
            + '<rect x="84" y="48" width="50" height="28" fill="#e6e6e6" stroke="#222" stroke-width="1.5"/>'
            + '<line x1="97" y1="48" x2="97" y2="76" stroke="#222" stroke-width="1.2"/>'
            + '<line x1="109" y1="48" x2="109" y2="76" stroke="#222" stroke-width="1.2"/>'
            + '<line x1="121" y1="48" x2="121" y2="76" stroke="#222" stroke-width="1.2"/>'
            + bottle(100, 76, "sm", "#fafafa")
            + bottle(116, 76, "md", "#d8d8d8")
        )
    if kind == "sorting":
        return (
            '<line x1="16" y1="76" x2="144" y2="76" stroke="#222" stroke-width="1.2"/>'
            '<rect x="16" y="58" width="128" height="6" fill="#d6d6d6" stroke="#222" stroke-width="1.3"/>'
            '<line x1="22" y1="64" x2="22" y2="76" stroke="#222" stroke-width="1.3"/>'
            '<line x1="138" y1="64" x2="138" y2="76" stroke="#222" stroke-width="1.3"/>'
            '<line x1="80" y1="26" x2="80" y2="58" stroke="#222" stroke-width="1.2" stroke-dasharray="3 2"/>'
            + bottle(40, 58, "md", "#ffffff")
            + bottle(58, 58, "md", "#f2f2f2")
            + bottle(102, 58, "md", "#c4c4c4")
            + bottle(122, 58, "lg", "#a8a8a8")
            + '<rect x="28" y="66" width="40" height="10" rx="1" fill="#f3f3f3" stroke="#222" stroke-width="1.2"/>'
            + '<rect x="92" y="66" width="40" height="10" rx="1" fill="#cfcfcf" stroke="#222" stroke-width="1.2"/>'
        )
    if kind == "washing":
        return (
            '<line x1="14" y1="80" x2="146" y2="80" stroke="#222" stroke-width="1.2"/>'
            '<path d="M14,50 L18,70 Q40,82 62,70 L66,50" fill="#d9d9d9" stroke="#222" stroke-width="1.5"/>'
            '<ellipse cx="40" cy="50" rx="26" ry="8" fill="#f4f4f4" stroke="#222" stroke-width="1.3"/>'
            + bottle(42, 64, "sm", "#f7f7f7", rotate=-26)
            + '<path d="M24,28 C24,28 20,34 20,36 A4,4 0 0 0 28,36 C28,34 24,28 24,28 Z" fill="#f4f4f4" stroke="#222" stroke-width="1"/>'
            + '<path d="M54,20 C54,20 51,25 51,27 A3,3 0 0 0 57,27 C57,25 54,20 54,20 Z" fill="#f4f4f4" stroke="#222" stroke-width="1"/>'
            + '<path d="M90,16 L82,28 L146,28 L138,16 Z" fill="#e8e8e8" stroke="#222" stroke-width="1.4"/>'
            + '<rect x="90" y="28" width="48" height="24" fill="#d0d0d0" stroke="#222" stroke-width="1.5"/>'
            + '<rect x="106" y="36" width="16" height="6" fill="#fff" stroke="#222" stroke-width="1.2"/>'
            + '<line x1="98" y1="32" x2="110" y2="48" stroke="#222" stroke-width="1.3"/>'
            + '<line x1="114" y1="32" x2="126" y2="48" stroke="#222" stroke-width="1.3"/>'
            + '<polygon points="94,58 102,56 104,68 92,66" fill="#d8d8d8" stroke="#222" stroke-width="1"/>'
            + '<polygon points="110,56 120,54 122,66 108,64" fill="#c8c8c8" stroke="#222" stroke-width="1"/>'
            + '<polygon points="126,60 136,58 134,72 124,70" fill="#e0e0e0" stroke="#222" stroke-width="1"/>'
            + '<polygon points="104,70 114,68 116,80 102,78" fill="#d0d0d0" stroke="#222" stroke-width="1"/>'
        )
    if kind == "melting":
        return (
            '<line x1="16" y1="80" x2="144" y2="80" stroke="#222" stroke-width="1.2"/>'
            '<rect x="22" y="20" width="52" height="42" fill="#d4d4d4" stroke="#222" stroke-width="1.5"/>'
            '<ellipse cx="48" cy="20" rx="26" ry="7" fill="#c4c4c4" stroke="#222" stroke-width="1.4"/>'
            '<ellipse cx="48" cy="28" rx="18" ry="5" fill="#f2f2f2" stroke="#222" stroke-width="1.1"/>'
            '<path d="M32,76 Q26,68 32,60 Q38,68 32,76 Z" fill="#f0f0f0" stroke="#222" stroke-width="1.2"/>'
            '<path d="M48,78 Q40,66 48,54 Q56,66 48,78 Z" fill="#e6e6e6" stroke="#222" stroke-width="1.2"/>'
            '<path d="M64,76 Q58,68 64,60 Q70,68 64,76 Z" fill="#f0f0f0" stroke="#222" stroke-width="1.2"/>'
            '<path d="M74,40 H88 V52" fill="none" stroke="#222" stroke-width="2"/>'
            '<line x1="88" y1="52" x2="88" y2="60" stroke="#222" stroke-width="1.4" stroke-dasharray="2 2"/>'
            '<rect x="76" y="60" width="64" height="16" fill="#eeeeee" stroke="#222" stroke-width="1.3"/>'
            '<circle cx="86" cy="68" r="4" fill="#c8c8c8" stroke="#222" stroke-width="1"/>'
            '<circle cx="98" cy="68" r="4" fill="#d4d4d4" stroke="#222" stroke-width="1"/>'
            '<circle cx="110" cy="68" r="4" fill="#c0c0c0" stroke="#222" stroke-width="1"/>'
            '<circle cx="122" cy="68" r="4" fill="#d8d8d8" stroke="#222" stroke-width="1"/>'
            '<circle cx="134" cy="68" r="4" fill="#bcbcbc" stroke="#222" stroke-width="1"/>'
        )
    if kind == "manufacturing":
        return (
            '<line x1="12" y1="80" x2="148" y2="80" stroke="#222" stroke-width="1.2"/>'
            '<path d="M18,22 L14,12 L54,12 L50,22 Z" fill="#e4e4e4" stroke="#222" stroke-width="1.4"/>'
            '<rect x="10" y="22" width="48" height="40" fill="#d2d2d2" stroke="#222" stroke-width="1.5"/>'
            '<circle cx="34" cy="42" r="10" fill="#f3f3f3" stroke="#222" stroke-width="1.3"/>'
            '<circle cx="34" cy="42" r="3" fill="#c0c0c0" stroke="#222" stroke-width="1"/>'
            '<line x1="18" y1="62" x2="18" y2="80" stroke="#222" stroke-width="1.4"/>'
            '<line x1="50" y1="62" x2="50" y2="80" stroke="#222" stroke-width="1.4"/>'
            '<rect x="58" y="52" width="90" height="6" fill="#c8c8c8" stroke="#222" stroke-width="1.3"/>'
            '<circle cx="64" cy="58" r="4" fill="#f0f0f0" stroke="#222" stroke-width="1.1"/>'
            '<circle cx="140" cy="58" r="4" fill="#f0f0f0" stroke="#222" stroke-width="1.1"/>'
            '<line x1="70" y1="62" x2="70" y2="80" stroke="#222" stroke-width="1.3"/>'
            '<line x1="136" y1="62" x2="136" y2="80" stroke="#222" stroke-width="1.3"/>'
            + bottle(78, 52, "sm", "#ffffff")
            + '<rect x="92" y="34" width="20" height="18" rx="1" fill="#e8e8e8" stroke="#222" stroke-width="1.2"/>'
            + '<path d="M92,40 Q97,37 102,40 Q107,43 112,40" fill="none" stroke="#222" stroke-width="1.1"/>'
            + '<path d="M92,46 Q97,43 102,46 Q107,49 112,46" fill="none" stroke="#222" stroke-width="1.1"/>'
            + '<rect x="122" y="34" width="20" height="18" fill="#e0e0e0" stroke="#222" stroke-width="1.2"/>'
            + '<line x1="122" y1="40" x2="142" y2="40" stroke="#222" stroke-width="1.1"/>'
            + '<line x1="132" y1="34" x2="132" y2="52" stroke="#222" stroke-width="1.1"/>'
        )
    # distribution (default)
    return (
        '<line x1="12" y1="80" x2="148" y2="80" stroke="#222" stroke-width="1.2"/>'
        '<rect x="12" y="52" width="26" height="28" fill="#e6e6e6" stroke="#222" stroke-width="1.3"/>'
        '<line x1="12" y1="61" x2="38" y2="61" stroke="#222" stroke-width="1.1"/>'
        '<line x1="25" y1="52" x2="25" y2="80" stroke="#222" stroke-width="1.1"/>'
        '<rect x="18" y="32" width="26" height="22" fill="#f0f0f0" stroke="#222" stroke-width="1.3"/>'
        '<line x1="18" y1="40" x2="44" y2="40" stroke="#222" stroke-width="1.1"/>'
        '<line x1="31" y1="32" x2="31" y2="54" stroke="#222" stroke-width="1.1"/>'
        '<rect x="56" y="28" width="58" height="32" fill="#d8d8d8" stroke="#222" stroke-width="1.5"/>'
        '<line x1="70" y1="28" x2="70" y2="60" stroke="#222" stroke-width="1.1"/>'
        '<line x1="86" y1="28" x2="86" y2="60" stroke="#222" stroke-width="1.1"/>'
        '<line x1="102" y1="28" x2="102" y2="60" stroke="#222" stroke-width="1.1"/>'
        '<path d="M114,38 L134,38 L144,50 L144,60 L114,60 Z" fill="#c8c8c8" stroke="#222" stroke-width="1.5"/>'
        '<rect x="122" y="42" width="16" height="10" fill="#fff" stroke="#222" stroke-width="1.1"/>'
        '<circle cx="74" cy="68" r="8" fill="#444" stroke="#222" stroke-width="1.3"/>'
        '<circle cx="74" cy="68" r="3" fill="#eee" stroke="#222" stroke-width="1"/>'
        '<circle cx="128" cy="68" r="8" fill="#444" stroke="#222" stroke-width="1.3"/>'
        '<circle cx="128" cy="68" r="3" fill="#eee" stroke="#222" stroke-width="1"/>'
    )


_FLOW_COL_W = 160
_FLOW_ART_H = 84
_FLOW_COL_GAP = 48
_FLOW_ROW_H = 136
_FLOW_ROW_GAP = 30
_FLOW_PAD_X = 16
_FLOW_PAD_Y = 8


def _flowchart_layout(count: int) -> tuple[int, int, list[tuple[int, int]], list[tuple[int, int, int, int]]]:
    if count == 6:
        cells = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 2), (1, 2)]
        width = _FLOW_PAD_X * 2 + _FLOW_COL_W * 2 + _FLOW_COL_GAP
        rows = 3
    else:
        cells = [(0, i) for i in range(count)]
        width = _FLOW_PAD_X * 2 + _FLOW_COL_W
        rows = max(count, 1)
    height = (
        _FLOW_PAD_Y * 2
        + rows * _FLOW_ROW_H
        + max(rows - 1, 0) * _FLOW_ROW_GAP
    )
    origins = []
    for col, row in cells:
        origins.append(
            (
                _FLOW_PAD_X + col * (_FLOW_COL_W + _FLOW_COL_GAP),
                _FLOW_PAD_Y + row * (_FLOW_ROW_H + _FLOW_ROW_GAP),
            )
        )
    arrows = []
    for i in range(count - 1):
        col1, row1 = cells[i]
        col2, row2 = cells[i + 1]
        x1, y1 = origins[i]
        x2, y2 = origins[i + 1]
        if row1 == row2:
            mid_y = y1 + 42
            if col2 > col1:
                arrows.append((x1 + _FLOW_COL_W, mid_y, x2, mid_y))
            else:
                arrows.append((x1, mid_y, x2 + _FLOW_COL_W, mid_y))
        else:
            ax = x1 + 80
            arrows.append((ax, y1 + _FLOW_ROW_H, ax, y2))
    return width, height, origins, arrows


def _flowchart_arrow(x1: int, y1: int, x2: int, y2: int, size: int = 7) -> str:
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) >= abs(dy):
        direction = 1 if dx > 0 else -1
        line = (
            f'<line x1="{x1}" y1="{y1}" x2="{x2 - direction * size}" y2="{y2}" '
            f'stroke="#222" stroke-width="1.6"/>'
        )
        head = (
            f'<polygon points="{x2},{y2} {x2 - direction * size},{y2 - 5} '
            f'{x2 - direction * size},{y2 + 5}" fill="#222" stroke="#222" stroke-width="0.5"/>'
        )
    else:
        direction = 1 if dy > 0 else -1
        line = (
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2 - direction * size}" '
            f'stroke="#222" stroke-width="1.6"/>'
        )
        head = (
            f'<polygon points="{x2},{y2} {x2 - 5},{y2 - direction * size} '
            f'{x2 + 5},{y2 - direction * size}" fill="#222" stroke="#222" stroke-width="0.5"/>'
        )
    return line + head


def _render_flowchart(flow: dict) -> str:
    steps = (flow or {}).get("steps") or []
    width, height, origins, arrows = _flowchart_layout(len(steps))
    shapes = []
    for i, step in enumerate(steps):
        x, y = origins[i]
        kind = _flowchart_kind(step, i)
        shapes.append(f'<g class="flowchart-scene" transform="translate({x} {y})">')
        shapes.append(_flowchart_art(kind))
        label = escape(str(step.get("label") or ""))
        shapes.append(
            f'<text x="80" y="100" text-anchor="middle" font-size="11" font-weight="700" '
            f'font-family="Arial, Helvetica, sans-serif" fill="#111">{label}</text>'
        )
        detail_lines = _flowchart_wrap_text(str(step.get("detail") or ""))
        for line_i, line in enumerate(detail_lines):
            yy = 112 + line_i * 11
            shapes.append(
                f'<text x="80" y="{yy}" text-anchor="middle" font-size="9" '
                f'font-family="Arial, Helvetica, sans-serif" fill="#555">{escape(line)}</text>'
            )
        shapes.append("</g>")
    for arrow in arrows:
        shapes.append(_flowchart_arrow(*arrow))
    title = ""
    if flow and flow.get("title"):
        title = f'<div class="flowchart-title">{escape(str(flow["title"]))}</div>'
    return (
        f'<div class="chart-wrap flowchart-wrap">{title}'
        f'<div class="flowchart flowchart-comic">'
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Process diagram">'
        f'{"".join(shapes)}</svg></div></div>'
    )


_TASK2_RUBRIC_RE = re.compile(
    r"(?i)^\s*(?:"
    r"Give reasons for your answer\b.*|"
    r"Write at least 250 words\.?"
    r")\s*$"
)


def _is_task2_rubric_line(line: str) -> bool:
    return bool(_TASK2_RUBRIC_RE.match(line or ""))


def format_task2_instruction(text: str | None) -> str:
    """Escape a Task 2 prompt and bold the question, not the standard rubric lines."""
    raw = "" if text is None else str(text)
    if not raw:
        return ""
    lines = raw.split("\n")
    idx = next((i for i, line in enumerate(lines) if _is_task2_rubric_line(line)), None)
    if idx is None:
        return f'<strong class="task2-question">{escape(raw)}</strong>'
    question = "\n".join(lines[:idx]).rstrip()
    rest = "\n".join(lines[idx:])
    parts = []
    if question:
        parts.append(f'<strong class="task2-question">{escape(question)}</strong>')
    if rest:
        parts.append(escape(rest))
    return "\n\n".join(parts) if question and rest else "".join(parts)


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
        "task2_instruction": format_task2_instruction((task2 or {}).get("instruction") or ""),
        "task2_text": record.get("task2_text") or "",
        "task2_word_count": int(record.get("task2_word_count") or 0),
    }


def _answer_map(record: dict) -> dict[str, str]:
    answers = record.get("answers") or {}
    if not isinstance(answers, dict):
        return {}
    return {str(k): ("" if v is None else str(v)) for k, v in answers.items()}


def _marking_by_q(record: dict, keys: dict | None = None, module: str | None = None) -> dict[int, dict]:
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
    scorer = ls if (module or module_of(record)) == "listening" else rs
    result = scorer.score_paper(_answer_map(record), mode=mode, keys=keys)
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


def _question_range(mode: str, module: str = "reading", paper: dict | None = None) -> set[int]:
    if (module or "reading") == "listening":
        return set(ls.mode_question_numbers(mode))
    return set(rs.mode_question_numbers(mode, paper))


def _parts_to_stem(parts: list, qnum: int) -> str | None:
    if not any(isinstance(p, dict) and p.get("q") == qnum for p in parts):
        return None
    bits: list[str] = []
    for part in parts:
        if isinstance(part, str):
            bits.append(part)
        elif isinstance(part, dict) and "q" in part:
            prefix = part.get("prefix") or ""
            bits.append(f"{prefix}______")
    return "".join(bits).strip()


def _walk_notes_for_q(node: Any, qnum: int) -> str | None:
    if isinstance(node, dict):
        parts = node.get("parts")
        if isinstance(parts, list):
            found = _parts_to_stem(parts, qnum)
            if found:
                return found
        for key in ("sections", "items", "children", "notes", "table", "rows", "lines", "cells"):
            found = _walk_notes_for_q(node.get(key), qnum)
            if found:
                return found
    elif isinstance(node, list):
        found = _parts_to_stem(node, qnum)
        if found:
            return found
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
        elif gtype == "table":
            ctx["stem"] = _walk_notes_for_q(group.get("table"), qnum) or ""
            title = (group.get("table") or {}).get("title")
            if title:
                ctx["notes_title"] = title
        elif gtype == "summary":
            summary = group.get("summary") or {}
            ctx["stem"] = _parts_to_stem(summary.get("parts") or [], qnum) or ""
            title = summary.get("title")
            if title:
                ctx["notes_title"] = title
        elif gtype in {"choose_two", "choose_three"}:
            ctx["stem"] = group.get("stem") or ""
            if group.get("options"):
                ctx["options"] = group.get("options")
        else:
            for item in group.get("items") or []:
                if item.get("q") == qnum:
                    ctx["stem"] = item.get("stem") or ""
                    if item.get("options"):
                        ctx["options"] = item.get("options")
                    break
            if gtype == "matching_endings" and group.get("endings"):
                ctx["endings"] = group.get("endings")
            if gtype == "matching_features" and group.get("options") and not ctx["options"]:
                ctx["options"] = group.get("options")
            if group.get("legend"):
                ctx["legend"] = group.get("legend")
        return ctx
    return {"q": qnum, "type": "", "heading": "", "instructions": [], "stem": "", "passage": None}


def _is_blank(answer: str | None) -> bool:
    return not (answer or "").strip()


def listening_question_context(paper: dict, qnum: int) -> dict:
    """Stem and surrounding context from a listening paper (no keys)."""
    for section in paper.get("sections") or []:
        for group in section.get("groups") or []:
            start, end = group.get("from"), group.get("to")
            if start is None or end is None or not (start <= qnum <= end):
                continue
            ctx = {
                "q": qnum,
                "type": group.get("type") or "",
                "heading": group.get("heading") or "",
                "instructions": list(group.get("instructions") or []),
                "section": section.get("id"),
                "stem": "",
                "options": None,
                "legend": None,
            }
            gtype = group.get("type")
            if gtype in {"notes", "notes_table"}:
                source = group.get("notes") if gtype == "notes" else group.get("table")
                ctx["stem"] = _walk_notes_for_q(source, qnum) or ""
                title = (source or {}).get("title")
                if title:
                    ctx["notes_title"] = title
            elif gtype in {"choose_two", "choose_three"}:
                ctx["stem"] = group.get("stem") or ""
                if group.get("options"):
                    ctx["options"] = group.get("options")
            elif gtype == "form":
                for row in group.get("rows") or []:
                    if row.get("q") == qnum:
                        ctx["stem"] = row.get("label") or ""
                        break
            else:
                for item in group.get("items") or []:
                    if item.get("q") == qnum:
                        ctx["stem"] = item.get("stem") or ""
                        if item.get("options"):
                            ctx["options"] = item.get("options")
                        break
                if group.get("legend"):
                    ctx["legend"] = group.get("legend")
                if group.get("options") and not ctx["options"]:
                    ctx["choice_letters"] = list(group.get("options") or [])
            return ctx
    return {"q": qnum, "type": "", "heading": "", "instructions": [], "stem": ""}


def _question_rows(
    record: dict,
    paper: dict,
    keys: dict,
    *,
    mistakes_only: bool,
    module: str | None = None,
) -> list[dict]:
    mode = (record.get("mode") or "full").strip().lower()
    module = module or module_of(record)
    allowed = _question_range(mode, module, paper=paper)
    answers = _answer_map(record)
    marking = _marking_by_q(record, keys, module=module)
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
        if module == "listening":
            ctx = listening_question_context(paper, q)
        else:
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
    allowed = _question_range(mode, paper=paper)
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
                    "lettered": bool(passage.get("lettered")),
                    "paragraphs": list(passage.get("paragraphs") or []),
                }
            )
    return out


def _groups_for_detail(paper: dict, record: dict, keys: dict) -> list[dict]:
    mode = (record.get("mode") or "full").strip().lower()
    allowed = _question_range(mode, paper=paper)
    rows_by_q = {row["q"]: row for row in _question_rows(record, paper, keys, mistakes_only=False)}
    groups = []
    for group in paper.get("groups") or []:
        start, end = group.get("from"), group.get("to")
        if start is None or end is None:
            continue
        qnums = [q for q in range(start, end + 1) if q in allowed]
        if not qnums:
            continue
        notes_title = (group.get("notes") or {}).get("title") or ""
        if group.get("type") == "summary":
            notes_title = (group.get("summary") or {}).get("title") or notes_title
        elif group.get("type") == "table":
            notes_title = (group.get("table") or {}).get("title") or notes_title
        entry = {
            "id": group.get("id"),
            "heading": group.get("heading") or "",
            "instructions": list(group.get("instructions") or []),
            "type": group.get("type") or "",
            "passage": group.get("passage"),
            "notes_title": notes_title,
            "layout_html": "",
            "questions": [rows_by_q[q] for q in qnums if q in rows_by_q],
        }
        if group.get("type") == "table":
            official = rs.official_answers(keys)
            entry["layout_html"] = reading_table_html(group, _answer_map(record), official)
        groups.append(entry)
    return groups


def part_time_pills(record: dict, *, part_label: str | None = None) -> list[dict]:
    times = record.get("part_times") or {}
    if not isinstance(times, dict):
        return []
    mode = (record.get("mode") or "full").strip().lower()
    module = module_of(record)
    if part_label is None:
        part_label = "Section" if module == "listening" else "Passage"
    if mode in {"passage1", "section1"}:
        keys = ("1",)
    elif mode in {"passage2", "section2"}:
        keys = ("2",)
    elif mode in {"passage3", "section3"}:
        keys = ("3",)
    elif mode == "section4":
        keys = ("4",)
    elif module == "listening":
        keys = ("1", "2", "3", "4")
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
                "label": f"{part_label} {key} {duration_label(seconds) if has_any else '本题卷未记录'}",
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
    allowed = _question_range(mode, paper=paper)
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



def _escape(text: Any) -> str:
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _fill_parts_html(parts: list, answers: dict[str, str], official: dict[int, str]) -> str:
    bits: list[str] = []
    for part in parts:
        if isinstance(part, dict) and part.get("q") is not None:
            qn = int(part["q"])
            prefix = _escape(part.get("prefix") or "")
            student = (answers.get(str(qn)) or answers.get(qn) or "").strip()
            correct = official.get(qn) or ""
            shown = _escape(student or "______")
            bits.append(
                f'{prefix}<span class="filled-blank" data-q="{qn}">'
                f'<span class="qnum">{qn}</span> {shown}</span>'
            )
            if correct:
                bits.append(f' <span class="muted">（标准答案：{_escape(correct)}）</span>')
        else:
            bits.append(_escape(part))
    return "".join(bits)



def reading_table_html(
    group: dict,
    answers: dict | None = None,
    official: dict[int, str] | None = None,
) -> str:
    """Render a reading completion table with gaps filled, not raw JSON."""
    table = group.get("table") or {}
    answers = {str(k): ("" if v is None else str(v)) for k, v in (answers or {}).items()}
    official = official or {}
    parts = ['<div class="table-wrap reading-table-wrap">']
    title = table.get("title") or ""
    if title:
        parts.append(f'<div class="notes-title">{_escape(title)}</div>')
    parts.append('<table class="completion-table notes-table data"><thead><tr>')
    for header in table.get("headers") or []:
        parts.append(f"<th>{_escape(header)}</th>")
    parts.append("</tr></thead><tbody>")
    for row in table.get("rows") or []:
        cells = row.get("cells") if isinstance(row, dict) else row
        parts.append("<tr>")
        for cell in cells or []:
            if isinstance(cell, dict) and cell.get("parts") is not None:
                line_parts = cell.get("parts") or []
            elif isinstance(cell, list):
                line_parts = cell
            else:
                line_parts = [cell]
            parts.append(f"<td>{_fill_parts_html(line_parts, answers, official)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def notes_table_html(
    group: dict,
    answers: dict | None = None,
    official: dict[int, str] | None = None,
) -> str:
    """Render a listening notes table with answers filled, not raw JSON."""
    table = group.get("table") or {}
    answers = {str(k): ("" if v is None else str(v)) for k, v in (answers or {}).items()}
    official = official or {}
    parts = ['<div class="notes-table-wrap">']
    title = table.get("title") or ""
    if title:
        parts.append(f'<div class="notes-title">{_escape(title)}</div>')
    parts.append('<table class="notes-table data"><thead><tr>')
    for header in table.get("headers") or []:
        parts.append(f"<th>{_escape(header)}</th>")
    parts.append("</tr></thead><tbody>")
    for row in table.get("rows") or []:
        parts.append("<tr>")
        for cell in row or []:
            lines = cell if isinstance(cell, list) else [cell]
            parts.append("<td>")
            for line in lines:
                line_parts = line if isinstance(line, list) else [line]
                parts.append(f'<div class="cell-line">{_fill_parts_html(line_parts, answers, official)}</div>')
            parts.append("</td>")
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def listening_layout_blocks(paper: dict, record: dict, keys: dict | None = None) -> list[dict]:
    """Teacher/PDF-friendly layouts (notes tables) with answers filled."""
    official = ls.official_answers(keys)
    answers = _answer_map(record)
    blocks: list[dict] = []
    for section in paper.get("sections") or []:
        for group in section.get("groups") or []:
            if group.get("type") != "notes_table":
                continue
            blocks.append(
                {
                    "heading": group.get("heading") or f"Section {section.get('id')}",
                    "title": (group.get("table") or {}).get("title") or "",
                    "html": notes_table_html(group, answers, official),
                    "table": group.get("table") or {},
                }
            )
    return blocks


def listening_detail_view(record: dict, paper: dict, keys: dict) -> dict:
    """Post-submit listening review for the owner: paper, answers, keys, transcript."""
    mode = (record.get("mode") or "full").strip().lower()
    score = record.get("score")
    total = record.get("total")
    questions = _question_rows(record, paper, keys, mistakes_only=False, module="listening")
    mistakes = [row for row in questions if not row["ok"] or row["student_blank"]]
    return {
        "module": "listening",
        "module_label": "听力",
        "mode_label": mode_label("listening", mode),
        "set_title": paper.get("title") or record.get("prompt_set_id") or "",
        "when": format_shanghai(record.get("timestamp")),
        "duration": duration_label(record.get("time_used_seconds")),
        "auto_submitted": bool(record.get("auto_submitted")),
        "score": score,
        "total": total,
        "score_label": f"{score}/{total}" if score is not None and total is not None else None,
        "band_label": ls.format_band(record.get("band_estimate")),
        "part_times": part_time_pills(record, part_label="Section"),
        "questions": questions,
        "mistake_count": len(mistakes),
        "total_questions": len(questions),
        "transcripts": ls.transcripts(keys),
        "layout_blocks": listening_layout_blocks(paper, record, keys),
    }


def listening_mistakes_view(record: dict, paper: dict, keys: dict) -> dict:
    """Wrong and unanswered listening items, with the student's answer, key, and 解析."""
    mode = (record.get("mode") or "full").strip().lower()
    mistakes = _question_rows(record, paper, keys, mistakes_only=True, module="listening")
    allowed = _question_range(mode, "listening")
    return {
        "module": "listening",
        "module_label": "听力",
        "mode_label": mode_label("listening", mode),
        "when": format_shanghai(record.get("timestamp")),
        "duration": duration_label(record.get("time_used_seconds")),
        "score": record.get("score"),
        "total": record.get("total"),
        "score_label": (
            f"{record.get('score')}/{record.get('total')}"
            if record.get("score") is not None and record.get("total") is not None
            else None
        ),
        "band_label": ls.format_band(record.get("band_estimate")),
        "mistakes": mistakes,
        "mistake_count": len(mistakes),
        "total_questions": len(allowed),
        "all_correct": len(mistakes) == 0,
        "transcripts": ls.transcripts(keys),
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
                "review_highlights": rr.review_highlights(record, paper=paper),
            }
        )
        return payload
    if module == "listening":
        detail = listening_detail_view(record, paper or {}, keys or {})
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
                "transcripts": detail.get("transcripts") or {},
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
