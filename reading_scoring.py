"""Server-side IELTS Academic Reading marking and band conversion."""

from __future__ import annotations

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
KEYS_PATH = BASE_DIR / "prompts" / "reading_keys.json"
PAPER_PATH = BASE_DIR / "prompts" / "reading_set_a.json"

# Full Academic Reading conversion (40-question test only).
BAND_TABLE = (
    (39, 40, 9.0),
    (37, 38, 8.5),
    (35, 36, 8.0),
    (33, 34, 7.5),
    (30, 32, 7.0),
    (27, 29, 6.5),
    (23, 26, 6.0),
    (19, 22, 5.5),
    (15, 18, 5.0),
    (13, 14, 4.5),
    (10, 12, 4.0),
    (8, 9, 3.5),
    (6, 7, 3.0),
    (4, 5, 2.5),
    (3, 3, 2.0),
    (2, 2, 1.5),
    (1, 1, 1.0),
    (0, 0, 0.0),
)

MODES = {
    "full": {"questions": list(range(1, 41)), "seconds": 60 * 60, "label": "Full test · 60 min"},
    "passage1": {"questions": list(range(1, 14)), "seconds": 20 * 60, "label": "Passage 1 · 20 min"},
    "passage2": {"questions": list(range(14, 27)), "seconds": 20 * 60, "label": "Passage 2 · 20 min"},
    "passage3": {"questions": list(range(27, 41)), "seconds": 20 * 60, "label": "Passage 3 · 20 min"},
}

_WRAP_PUNCT = "\"'`“”‘’.,;:!?()[]{}<>«»"

# Longer aliases first so "NOTGIVEN" is not misread.
_ALIASES = {
    "not given": "NOT GIVEN",
    "notgiven": "NOT GIVEN",
    "not-given": "NOT GIVEN",
    "not_given": "NOT GIVEN",
    "ng": "NOT GIVEN",
    "true": "TRUE",
    "t": "TRUE",
    "false": "FALSE",
    "f": "FALSE",
    "yes": "YES",
    "y": "YES",
    "no": "NO",
    "n": "NO",
}

_CHOICE_TYPES = {"tfng", "ynng", "mcq", "matching_endings"}


def load_keys(path: Path | None = None) -> dict:
    with (path or KEYS_PATH).open(encoding="utf-8") as f:
        return json.load(f)


def load_paper(path: Path | None = None) -> dict:
    with (path or PAPER_PATH).open(encoding="utf-8") as f:
        return json.load(f)


def official_answers(keys: dict | None = None) -> dict[int, str]:
    data = keys or load_keys()
    questions = data.get("questions") or data
    out: dict[int, str] = {}
    for q, meta in questions.items():
        out[int(q)] = meta["answer"] if isinstance(meta, dict) else str(meta)
    return out


def question_types(keys: dict | None = None) -> dict[int, str]:
    data = keys or load_keys()
    questions = data.get("questions") or data
    out: dict[int, str] = {}
    for q, meta in questions.items():
        out[int(q)] = meta.get("type", "notes") if isinstance(meta, dict) else "notes"
    return out


def normalize_answer(raw: str | None) -> str:
    """Trim, collapse whitespace, strip wrapping punctuation/quotes."""
    text = (raw or "").strip()
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = text.strip(_WRAP_PUNCT + " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def canonicalize(raw: str | None, qtype: str) -> str:
    """Normalize a student response for comparison with the official key."""
    text = normalize_answer(raw)
    if not text:
        return ""
    if qtype in _CHOICE_TYPES:
        compact = text.lower().replace(" ", "")
        spaced = text.lower()
        if spaced in _ALIASES:
            return _ALIASES[spaced]
        if compact in _ALIASES:
            return _ALIASES[compact]
        # Single letters A–F (and a–f)
        if re.fullmatch(r"[A-Fa-f]", text):
            return text.upper()
        return text.upper()
    # Notes: case-insensitive exact word after normalization; no spelling fuzz.
    return text.lower()


def answers_equal(student: str | None, official: str, qtype: str) -> bool:
    left = canonicalize(student, qtype)
    right = canonicalize(official, qtype)
    if not left:
        return False
    return left == right


def band_for_score(score: int, total: int = 40) -> float | None:
    """Return an Academic Reading band for a full 40-question paper only."""
    if total != 40:
        return None
    score = max(0, min(int(score), 40))
    for lo, hi, band in BAND_TABLE:
        if lo <= score <= hi:
            return band
    return 0.0


def mode_question_numbers(mode: str) -> list[int]:
    info = MODES.get(mode) or MODES["full"]
    return list(info["questions"])


def score_paper(
    answers: dict,
    mode: str = "full",
    keys: dict | None = None,
) -> dict:
    """Mark a set of answers. `answers` keys may be int or str."""
    key_data = keys or load_keys()
    official = official_answers(key_data)
    types = question_types(key_data)
    questions = mode_question_numbers(mode)
    total = len(questions)

    raw_answers = {}
    for k, v in (answers or {}).items():
        try:
            raw_answers[int(k)] = "" if v is None else str(v)
        except (TypeError, ValueError):
            continue

    marking = []
    score = 0
    for q in questions:
        student = raw_answers.get(q, "")
        correct = official[q]
        qtype = types[q]
        ok = answers_equal(student, correct, qtype)
        if ok:
            score += 1
        marking.append(
            {
                "q": q,
                "student": normalize_answer(student),
                "correct": correct,
                "ok": ok,
            }
        )

    band = band_for_score(score, total) if mode == "full" and total == 40 else None
    return {
        "score": score,
        "total": total,
        "band_estimate": band,
        "marking": marking,
        "mode": mode if mode in MODES else "full",
    }


def format_band(band: float | None) -> str | None:
    if band is None:
        return None
    if float(band).is_integer():
        return str(int(band))
    return str(band)
