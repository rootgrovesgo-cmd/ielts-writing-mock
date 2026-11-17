"""Highest-three average widget for the student records page.

Eligible scores are the same set collected by ``student_portal.growth_stack_scores``:
reading and listening official/reference bands, and writing teacher bands only.
Hidden writing ``official_score`` values and speaking scores are ignored.

The headline number is the unrounded-to-band average of the highest three
individual papers (or of all papers if the student has fewer than three),
shown to two decimal places so a small improvement is visible.
"""

from __future__ import annotations

import html
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

TITLE = "最高三项平均分"
TOP_N = 3

MODULE_LABELS = {
    "writing": "写作",
    "reading": "阅读",
    "listening": "听力",
}

EMPTY_MESSAGE = "完成一次练习，这里就会亮起来"
EMPTY_HINT = "每一次认真作答，都会在这里被看见。"

RISE_MESSAGE = "又进步了一点，继续保持"
RISE_THREE_MESSAGE = "三项成绩都到齐了，继续保持"
STEADY_ONE_MESSAGE = "已经有了第一次成绩，继续就好"
STEADY_TWO_MESSAGE = "两项成绩已经在了，继续保持"
STEADY_THREE_MESSAGE = "这是目前最高的三次成绩，继续保持"

_WRITING_TEACHER_KEYS = ("teacher_band", "teacher_score", "writing_teacher")
_READING_LISTENING_KEYS = (
    "band_estimate",
    "band",
    "reference_band",
    "official_band",
    "band_label",
)
_IGNORE_KEYS = frozenset({
    "official_score",
    "writing_official",
    "writing_official_score",
    "speaking",
    "speaking_band",
    "speaking_score",
})

_CSS_PATH = Path(__file__).resolve().parent / "static" / "top_average.css"
_CENTS = Decimal("0.01")


def parse_half_band(value) -> float | None:
    """Return an IELTS half-band in 0–9, or None if missing or invalid.

    Non-half-bands such as 7.2 are ignored. Booleans are rejected so True
    is not read as 1.0.
    """
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if number < 0 or number > 9:
        return None
    if abs(number * 2 - round(number * 2)) > 1e-9:
        return None
    return round(number * 2) / 2


def format_band(band) -> str | None:
    """Format a half-band with one decimal, e.g. '7.0'."""
    value = parse_half_band(band)
    if value is None:
        return None
    return f"{value:.1f}"


def format_average(value: Decimal | None) -> str | None:
    """Format an average to two decimal places, e.g. '6.17'."""
    if value is None:
        return None
    quantized = Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)
    return f"{quantized:.2f}"


def average_of(bands: list[float]) -> Decimal | None:
    """Equal average of ``bands``, quantized to two decimal places."""
    if not bands:
        return None
    total = sum((Decimal(str(band)) for band in bands), Decimal("0"))
    return (total / Decimal(len(bands))).quantize(_CENTS, rounding=ROUND_HALF_UP)


def _first_band(data: dict, keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key in _IGNORE_KEYS:
            continue
        parsed = parse_half_band(data.get(key))
        if parsed is not None:
            return parsed
    return None


def _meta_from(item: dict | None) -> dict:
    if not item:
        return {"timestamp": "", "teacher_scored_at": ""}
    return {
        "timestamp": str(item.get("timestamp") or ""),
        "teacher_scored_at": str(item.get("teacher_scored_at") or ""),
    }


def _entry(module: str, band: float, item: dict | None = None) -> dict:
    row = {"module": module, "band": band}
    row.update(_meta_from(item))
    return row


def _module_of(item: dict) -> str:
    return str(item.get("module") or item.get("kind") or "").strip().lower()


def eligible_entries(scores=None) -> list[dict]:
    """Collect usable paper scores, preserving input order.

    Each entry is ``{module, band, timestamp, teacher_scored_at}``. Speaking
    rows and ``official_score`` values are never included. A bare writing
    number is treated as the teacher band.
    """
    found: list[dict] = []
    if scores is None or scores == "":
        return found
    if isinstance(scores, (list, tuple)):
        for part in scores:
            found.extend(eligible_entries(part))
        return found
    if not isinstance(scores, dict):
        parsed = parse_half_band(scores)
        if parsed is not None:
            found.append(_entry("", parsed))
        return found

    module = _module_of(scores)
    if module == "speaking":
        return found
    if module == "writing":
        band = _first_band(scores, _WRITING_TEACHER_KEYS)
        if band is not None:
            found.append(_entry("writing", band, scores))
        return found
    if module:
        band = _first_band(scores, _READING_LISTENING_KEYS)
        if band is not None:
            found.append(_entry(module, band, scores))
        return found

    for key in ("reading", "listening"):
        if key not in scores:
            continue
        value = scores[key]
        if isinstance(value, dict):
            found.extend(eligible_entries({**value, "module": key}))
        else:
            parsed = parse_half_band(value)
            if parsed is not None:
                found.append(_entry(key, parsed, scores))

    if "writing" in scores:
        value = scores["writing"]
        if isinstance(value, dict):
            found.extend(eligible_entries({**value, "module": "writing"}))
        else:
            parsed = parse_half_band(value)
            if parsed is not None:
                found.append(_entry("writing", parsed, scores))

    for key in _WRITING_TEACHER_KEYS:
        if key == "writing" or key not in scores:
            continue
        parsed = parse_half_band(scores.get(key))
        if parsed is not None:
            found.append(_entry("writing", parsed, scores))

    return found


def _effective_time(entry: dict) -> str:
    if (entry.get("module") or "") == "writing":
        return str(entry.get("teacher_scored_at") or entry.get("timestamp") or "")
    return str(entry.get("timestamp") or "")


def _chronological(entries: list[dict]) -> list[dict]:
    """Oldest first. Ties keep input order, treated as chronological."""
    decorated = []
    for index, entry in enumerate(entries):
        time = _effective_time(entry)
        decorated.append((time == "", time, index, entry))
    decorated.sort(key=lambda item: (item[0], item[1], item[2]))
    return [item[3] for item in decorated]


def _top_entries(entries: list[dict], n: int = TOP_N) -> list[dict]:
    """Highest ``n`` papers; ties prefer the more recent paper."""
    if not entries:
        return []
    chrono = _chronological(entries)
    recency = {id(entry): index for index, entry in enumerate(chrono)}
    ranked = sorted(
        entries,
        key=lambda entry: (-entry["band"], -recency.get(id(entry), 0)),
    )
    return ranked[:n]


def _count_line(total: int, used: int) -> str:
    if total <= 0:
        return ""
    if used == 1:
        return "已计入 1 次成绩，再完成两次会更稳"
    if used == 2:
        return "已计入 2 次成绩，再完成一次会更稳"
    if total <= TOP_N:
        return f"已计入 {used} 次成绩"
    return f"从 {total} 次成绩中取最高三次"


def _message(count: int, improved: bool, just_reached_three: bool) -> str:
    if count == 0:
        return EMPTY_MESSAGE
    if improved and just_reached_three:
        return RISE_THREE_MESSAGE
    if improved:
        return RISE_MESSAGE
    if count == 1:
        return STEADY_ONE_MESSAGE
    if count == 2:
        return STEADY_TWO_MESSAGE
    return STEADY_THREE_MESSAGE


def snapshot(scores=None) -> dict:
    """Compute the widget model for a collection of eligible scores."""
    entries = eligible_entries(scores)
    used = _top_entries(entries)
    current = average_of([row["band"] for row in used])
    delta = None
    improved = False
    just_reached_three = False

    history = _chronological(entries)
    if history:
        running: list[dict] = []
        last_rise_index = None
        previous_at_rise = None
        counts_at_rise = (0, 0)
        for index, entry in enumerate(history):
            before = average_of([row["band"] for row in _top_entries(running)])
            before_n = min(len(running), TOP_N)
            running.append(entry)
            after = average_of([row["band"] for row in _top_entries(running)])
            if before is not None and after is not None and after > before:
                last_rise_index = index
                previous_at_rise = before
                counts_at_rise = (before_n, min(len(running), TOP_N))
        # Only show a delta when the most recent eligible paper raised the average.
        if last_rise_index == len(history) - 1 and previous_at_rise is not None and current is not None:
            change = current - previous_at_rise
            if change > 0:
                delta = change
                improved = True
                just_reached_three = counts_at_rise == (2, 3)

    parts = [
        {
            "module": row["module"],
            "module_label": MODULE_LABELS.get(row["module"], ""),
            "band": row["band"],
            "band_label": format_band(row["band"]) or "",
        }
        for row in used
    ]
    count = len(used)
    average_label = format_average(current)
    delta_label = format_average(delta) if delta is not None else None
    return {
        "title": TITLE,
        "empty": count == 0,
        "count": count,
        "total": len(entries),
        "average": current,
        "average_label": average_label,
        "delta": delta,
        "delta_label": delta_label,
        "improved": improved,
        "message": _message(count, improved, just_reached_three),
        "hint": EMPTY_HINT if count == 0 else "",
        "count_line": _count_line(len(entries), count),
        "parts": parts,
    }


def _widget_css() -> str:
    try:
        return _CSS_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def render(scores=None) -> str:
    """Return a self-contained HTML widget for the highest-three average."""
    data = snapshot(scores)
    css = _widget_css()
    empty_cls = " is-empty" if data["empty"] else ""
    improved_cls = " is-improved" if data["improved"] else ""
    attrs = [f'class="top-average{empty_cls}{improved_cls}"']
    attrs.append(f'data-count="{data["count"]}"')
    if data["average_label"]:
        attrs.append(f'data-average="{html.escape(data["average_label"], quote=True)}"')
    if data["delta_label"]:
        attrs.append(f'data-delta="{html.escape(data["delta_label"], quote=True)}"')
    aria_bits = [data["title"]]
    if data["empty"]:
        aria_bits.append(data["message"])
    else:
        aria_bits.append(data["average_label"] or "")
        if data["delta_label"]:
            aria_bits.append(f"比上次高 {data['delta_label']}")
        aria_bits.append(data["message"])
    aria = "，".join(bit for bit in aria_bits if bit)
    parts = [
        f'<aside {" ".join(attrs)} aria-label="{html.escape(aria, quote=True)}">',
    ]
    if css.strip():
        parts.append(f"<style>\n{css}\n</style>")
    parts.append('<p class="top-average-eyebrow">Top three average</p>')
    parts.append(f'<h2 class="top-average-title">{html.escape(data["title"])}</h2>')
    if data["empty"]:
        parts.append(
            f'<p class="top-average-message">{html.escape(data["message"])}</p>'
        )
        if data["hint"]:
            parts.append(f'<p class="top-average-hint">{html.escape(data["hint"])}</p>')
    else:
        parts.append(
            f'<p class="top-average-value">{html.escape(data["average_label"] or "")}</p>'
        )
        if data["delta_label"]:
            parts.append(
                f'<p class="top-average-delta">比上次高 {html.escape(data["delta_label"])}</p>'
            )
        parts.append(
            f'<p class="top-average-message">{html.escape(data["message"])}</p>'
        )
        parts.append('<ul class="top-average-parts">')
        for item in data["parts"]:
            label = item["module_label"]
            band = item["band_label"]
            text = f"{label} {band}".strip()
            mod_attr = ""
            if item["module"]:
                mod_attr = f' data-module="{html.escape(item["module"], quote=True)}"'
            parts.append(
                f'<li class="top-average-part"{mod_attr}>'
                f"{html.escape(text)}</li>"
            )
        parts.append("</ul>")
        if data["count_line"]:
            parts.append(
                f'<p class="top-average-count">{html.escape(data["count_line"])}</p>'
            )
    parts.append("</aside>")
    return "\n".join(parts)
