"""Format teacher/student explanations, including listening and reading layouts."""

from __future__ import annotations

import html
import re
from typing import Any, Mapping

# Display order and labels for structured listening explanations.
LISTENING_PARTS: tuple[tuple[str, str], ...] = (
    ("prediction", "预测"),
    ("logic", "考点与原文逻辑替换"),
    ("audio_quote", "跟音"),
)

# Display order and labels for structured reading explanations.
READING_PARTS: tuple[tuple[str, str], ...] = (
    ("stem_keywords", "题干关键词"),
    ("locate", "原文定位"),
    ("paraphrase", "关键词替换"),
    ("judgment", "判定点"),
)

# Backward-compatible alias used by older listening callers.
PARTS = LISTENING_PARTS

_ALL_PARTS = LISTENING_PARTS + READING_PARTS
_LABEL_TO_KEY = {label: key for key, label in _ALL_PARTS}
_LABEL_RE = re.compile(
    r"(?:^|\n)(预测|考点与原文逻辑替换|跟音|题干关键词|原文定位|关键词替换|判定点)[：:]",
)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_LEADIN_RE = re.compile(r"^跟音[：:]\s*")


def _has_schema_fields(source: Mapping[str, Any], schema: tuple[tuple[str, str], ...]) -> bool:
    return any(str(source.get(key) or "").strip() for key, _ in schema)


def _schema_from_parsed(parsed: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    has_reading = any((parsed.get(key) or "").strip() for key, _ in READING_PARTS)
    has_listening = any((parsed.get(key) or "").strip() for key, _ in LISTENING_PARTS)
    if has_reading and not has_listening:
        return READING_PARTS
    return LISTENING_PARTS


def explanation_schema(source: Any) -> tuple[tuple[str, str], ...]:
    """Return the part-label table that applies to this explanation."""
    if isinstance(source, Mapping):
        has_reading = _has_schema_fields(source, READING_PARTS)
        has_listening = _has_schema_fields(source, LISTENING_PARTS)
        if has_reading and not has_listening:
            return READING_PARTS
        if has_listening and not has_reading:
            return LISTENING_PARTS
        parsed = parse_labeled_explanation(source.get("explanation") or "")
        return _schema_from_parsed(parsed)
    return _schema_from_parsed(parse_labeled_explanation(source or ""))


def explanation_parts(source: Any) -> dict[str, str]:
    """Return structured parts from a key object or composed text."""
    schema = explanation_schema(source)
    if isinstance(source, Mapping):
        parts = {key: str(source.get(key) or "").strip() for key, _ in schema}
        if any(parts.values()):
            if not all(parts.values()):
                parsed = parse_labeled_explanation(source.get("explanation") or "")
                for key, value in parsed.items():
                    if key in parts and not parts[key]:
                        parts[key] = value
            if "audio_quote" in parts:
                parts["audio_quote"] = _LEADIN_RE.sub("", parts["audio_quote"]).strip()
            return parts
        parsed = parse_labeled_explanation(source.get("explanation") or "")
        return {key: parsed.get(key) or "" for key, _ in schema}
    parsed = parse_labeled_explanation(source or "")
    return {key: parsed.get(key) or "" for key, _ in schema}


def parse_labeled_explanation(text: str) -> dict[str, str]:
    """Split a composed explanation into labeled listening and/or reading parts."""
    empty = {key: "" for key, _ in _ALL_PARTS}
    value = (text or "").strip()
    if not value:
        return empty
    matches = list(_LABEL_RE.finditer(value))
    if not matches:
        return empty
    out = dict(empty)
    for index, match in enumerate(matches):
        label = match.group(1)
        key = _LABEL_TO_KEY.get(label)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(value)
        chunk = value[start:end].strip()
        if key == "audio_quote":
            chunk = _LEADIN_RE.sub("", chunk).strip()
        if key:
            out[key] = chunk
    return out


def compose_explanation(source: Any) -> str:
    """Build the labeled plain-text explanation used by older consumers."""
    parts = explanation_parts(source)
    lines: list[str] = []
    for key, label in explanation_schema(source):
        value = (parts.get(key) or "").strip()
        if value:
            lines.append(f"{label}：{value}")
    return "\n".join(lines)


def has_structured_parts(source: Any) -> bool:
    parts = explanation_parts(source)
    return any(parts.values())


def format_inline(text: str) -> str:
    """Escape text, then restore **bold** as <strong>."""
    escaped = html.escape(text or "")
    return _BOLD_RE.sub(r"<strong>\1</strong>", escaped)


def explanation_html(source: Any) -> str:
    """Safe HTML for a labeled layout, or a single paragraph fallback."""
    parts = explanation_parts(source)
    if not any(parts.values()):
        raw = (
            source
            if isinstance(source, str)
            else (source or {}).get("explanation")
            if isinstance(source, Mapping)
            else ""
        )
        text = str(raw or "").strip()
        if not text:
            return ""
        return f"<p>{html.escape(text)}</p>"
    blocks: list[str] = []
    for key, label in explanation_schema(source):
        value = (parts.get(key) or "").strip()
        if not value:
            continue
        blocks.append(
            '<div class="explain-part explain-'
            + key
            + '">'
            + f'<h5 class="explain-label">{html.escape(label)}</h5>'
            + f"<p>{format_inline(value)}</p>"
            + "</div>"
        )
    return '<div class="q-explain-parts">' + "".join(blocks) + "</div>"
