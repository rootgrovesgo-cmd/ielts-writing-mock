"""Server-side IELTS Academic Listening marking and band conversion."""

from __future__ import annotations

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
KEYS_PATH = BASE_DIR / "prompts" / "listening_keys.json"
PAPER_PATH = BASE_DIR / "prompts" / "listening_set_a.json"

# Official Listening conversion varies by paper. This widely used table is a
# reference only, for a full 40-question Academic Listening test.
BAND_TABLE = (
    (39, 40, 9.0),
    (37, 38, 8.5),
    (35, 36, 8.0),
    (32, 34, 7.5),
    (30, 31, 7.0),
    (26, 29, 6.5),
    (23, 25, 6.0),
    (18, 22, 5.5),
    (16, 17, 5.0),
    (13, 15, 4.5),
    (10, 12, 4.0),
    (8, 9, 3.5),
    (6, 7, 3.0),
    (4, 5, 2.5),
    (3, 3, 2.0),
    (2, 2, 1.5),
    (1, 1, 1.0),
    (0, 0, 0.0),
)

SECTION_MODES = {
    "section1": 1,
    "section2": 2,
    "section3": 3,
    "section4": 4,
}

_WRAP_PUNCT = "\"'`“”‘’.,;:!?()[]{}<>«»"

_CHOICE_TYPES = {"mcq", "matching", "map", "choose_two"}

# Tokens treated as a number (not a word) for IELTS word-limit checks.
_NUMBER_RE = re.compile(
    r"""^
    (?:£|\$|€)?
    \+?
    \d+(?:[./:\-]\d+)*
    (?:st|nd|rd|th)?
    (?:%|p|am|pm)?
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Phone-like runs of digits with spaces or hyphens, counted as one number.
_PHONE_RE = re.compile(r"^\+?\d[\d\s\-]{5,}\d$")


def load_keys(path: Path | None = None) -> dict:
    with (path or KEYS_PATH).open(encoding="utf-8") as f:
        return json.load(f)


def load_paper(path: Path | None = None) -> dict:
    target = path or PAPER_PATH
    if not target.exists():
        return {"id": "set-a", "sections": [], "check_seconds": 120}
    with target.open(encoding="utf-8") as f:
        return json.load(f)


def official_answers(keys: dict | None = None) -> dict[int, str]:
    data = keys or load_keys()
    questions = data.get("questions") or data
    out: dict[int, str] = {}
    for q, meta in questions.items():
        out[int(q)] = meta["answer"] if isinstance(meta, dict) else str(meta)
    return out


def official_alternatives(keys: dict | None = None) -> dict[int, list[str]]:
    data = keys or load_keys()
    questions = data.get("questions") or data
    out: dict[int, list[str]] = {}
    for q, meta in questions.items():
        if isinstance(meta, dict):
            alts = meta.get("alternatives") or []
            out[int(q)] = [str(a) for a in alts]
        else:
            out[int(q)] = []
    return out


def question_types(keys: dict | None = None) -> dict[int, str]:
    data = keys or load_keys()
    questions = data.get("questions") or data
    out: dict[int, str] = {}
    for q, meta in questions.items():
        out[int(q)] = meta.get("type", "notes") if isinstance(meta, dict) else "notes"
    return out


def question_limits(keys: dict | None = None) -> dict[int, dict]:
    data = keys or load_keys()
    questions = data.get("questions") or data
    out: dict[int, dict] = {}
    for q, meta in questions.items():
        if isinstance(meta, dict) and isinstance(meta.get("word_limit"), dict):
            out[int(q)] = dict(meta["word_limit"])
    return out


def section_durations(paper: dict | None = None) -> dict[int, int]:
    data = paper or load_paper()
    out: dict[int, int] = {}
    for section in data.get("sections") or []:
        try:
            sid = int(section.get("id"))
        except (TypeError, ValueError):
            continue
        audio = section.get("audio") or {}
        try:
            out[sid] = max(0, int(audio.get("duration_seconds") or 0))
        except (TypeError, ValueError):
            out[sid] = 0
    return out


def check_seconds(paper: dict | None = None) -> int:
    data = paper or load_paper()
    try:
        return max(0, int(data.get("check_seconds") or 120))
    except (TypeError, ValueError):
        return 120


def mode_question_numbers(mode: str) -> list[int]:
    key = (mode or "full").strip().lower()
    if key in SECTION_MODES:
        start = (SECTION_MODES[key] - 1) * 10 + 1
        return list(range(start, start + 10))
    return list(range(1, 41))


def duration_for_mode(mode: str, paper: dict | None = None) -> int:
    """Seconds allowed for a mode, derived from generated audio length.

    Full test = sum of the four section recordings + a 2-minute check after
    the audio has ended. Each section recording already includes the usual
    'look at the questions' and 30-second check silences. Section-only mode
    uses that section's audio length only (no extra 2-minute check, no band).
    """
    data = paper or load_paper()
    durations = section_durations(data)
    key = (mode or "full").strip().lower()
    if key in SECTION_MODES:
        return int(durations.get(SECTION_MODES[key]) or 0)
    return int(sum(durations.get(i, 0) for i in range(1, 5)) + check_seconds(data))


def mode_label(mode: str, paper: dict | None = None) -> str:
    key = (mode or "full").strip().lower()
    seconds = duration_for_mode(key, paper)
    minutes = max(1, round(seconds / 60)) if seconds else 0
    if key == "full":
        return f"Full test · about {minutes} min · Questions 1–40"
    if key in SECTION_MODES:
        sid = SECTION_MODES[key]
        start = (sid - 1) * 10 + 1
        end = start + 9
        return f"Section {sid} only · about {minutes} min · Q{start}–{end}"
    return key


def modes_info(paper: dict | None = None) -> dict:
    data = paper or load_paper()
    info = {
        "full": {
            "questions": list(range(1, 41)),
            "seconds": duration_for_mode("full", data),
            "label": mode_label("full", data),
        }
    }
    for key in SECTION_MODES:
        info[key] = {
            "questions": mode_question_numbers(key),
            "seconds": duration_for_mode(key, data),
            "label": mode_label(key, data),
        }
    return info


# Exposed like reading_scoring.MODES, but seconds come from the paper audio.
MODES = modes_info()


def refresh_modes(paper: dict | None = None) -> dict:
    """Reload mode durations after audio metadata is updated."""
    global MODES
    MODES = modes_info(paper)
    return MODES


def normalize_answer(raw: str | None) -> str:
    """Trim, collapse whitespace, strip wrapping punctuation/quotes."""
    text = (raw or "").strip()
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = text.strip(_WRAP_PUNCT + " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_number_token(token: str) -> bool:
    compact = token.strip()
    if not compact:
        return False
    if _PHONE_RE.match(compact):
        return True
    return bool(_NUMBER_RE.match(compact.replace(" ", ""))) if " " not in compact else bool(
        _PHONE_RE.match(compact)
    )


def tokenize_answer(raw: str | None) -> list[str]:
    text = normalize_answer(raw)
    if not text:
        return []
    # Keep a phone-like run as a single token if the whole answer is a phone.
    if _PHONE_RE.match(text):
        return [text]
    return text.split()


def count_words_and_numbers(raw: str | None) -> tuple[int, int]:
    words = 0
    numbers = 0
    for token in tokenize_answer(raw):
        if _is_number_token(token):
            numbers += 1
        else:
            words += 1
    return words, numbers


def exceeds_word_limit(raw: str | None, limit: dict | None) -> bool:
    if not limit or not normalize_answer(raw):
        return False
    try:
        max_words = int(limit.get("max_words") or 0)
    except (TypeError, ValueError):
        max_words = 0
    if max_words <= 0:
        return False
    allow_number = bool(limit.get("allow_number", True))
    words, numbers = count_words_and_numbers(raw)
    if words > max_words:
        return True
    if numbers and not allow_number:
        return True
    # "AND/OR A NUMBER" allows a single number plus up to max_words words.
    if numbers > 1:
        return True
    return False


def canonicalize(raw: str | None, qtype: str) -> str:
    """Normalize a student response for comparison with the official key."""
    text = normalize_answer(raw)
    if not text:
        return ""
    if qtype in _CHOICE_TYPES:
        if re.fullmatch(r"[A-Ia-i]", text):
            return text.upper()
        return text.upper()
    # Form / notes: case-insensitive; strip a final full stop already handled.
    collapsed = text.lower()
    collapsed = collapsed.replace("£", "")
    collapsed = re.sub(r"\s+", " ", collapsed).strip()
    # Hyphen / space variants of the same compound are compared later via
    # listed alternatives; keep hyphen here so unlisted variants do not pass.
    return collapsed


def _canonical_variants(text: str, qtype: str) -> set[str]:
    base = canonicalize(text, qtype)
    if not base:
        return set()
    out = {base, base.replace("-", " "), base.replace(" ", "-")}
    # Dates such as 18th may also be written 18.
    out.add(re.sub(r"(\d+)(?:st|nd|rd|th)\b", r"\1", base))
    # Times 2:15 / 2.15
    out.add(base.replace(":", "."))
    out.add(base.replace(".", ":"))
    # Currency already stripped of £ in canonicalize; drop trailing 'pounds'.
    out.add(re.sub(r"\s*pounds$", "", base).strip())
    # Collapse spaces in phone numbers for comparison.
    out.add(base.replace(" ", "").replace("-", ""))
    return {item for item in out if item}


def answers_equal(student: str | None, official: str, qtype: str, alternatives: list[str] | None = None) -> bool:
    left = _canonical_variants(student, qtype)
    if not left:
        return False
    rights = _canonical_variants(official, qtype)
    for alt in alternatives or []:
        rights |= _canonical_variants(alt, qtype)
    return bool(left & rights)


def band_for_score(score: int, total: int = 40) -> float | None:
    """Return an Academic Listening band for a full 40-question paper only."""
    if total != 40:
        return None
    score = max(0, min(int(score), 40))
    for lo, hi, band in BAND_TABLE:
        if lo <= score <= hi:
            return band
    return 0.0



def choose_two_pairs(keys: dict | None = None) -> list[tuple[tuple[int, int], list[str]]]:
    """Return unique choose-two pairs and their official letters."""
    data = keys or load_keys()
    questions = data.get("questions") or data
    seen: set[tuple[int, int]] = set()
    pairs: list[tuple[tuple[int, int], list[str]]] = []
    for meta in questions.values() if isinstance(questions, dict) else []:
        if not isinstance(meta, dict) or meta.get("type") != "choose_two":
            continue
        pair = meta.get("pair") or []
        if len(pair) != 2:
            continue
        try:
            left, right = int(pair[0]), int(pair[1])
        except (TypeError, ValueError):
            continue
        key = (min(left, right), max(left, right))
        if key in seen:
            continue
        seen.add(key)
        official: list[str] = []
        for qn in key:
            item = questions.get(str(qn)) or questions.get(qn) or {}
            answer = item.get("answer") if isinstance(item, dict) else item
            official.append("" if answer is None else str(answer))
        pairs.append((key, official))
    return pairs


def _mark_choose_two_pair(student_vals: list[str], official: list[str]) -> list[bool]:
    """Order-insensitive set marking: {A,E}=2, {A} or {A,C}=1, {A,A}=1, {B,C}=0."""
    remaining = [canonicalize(item, "choose_two") for item in official]
    remaining = [item for item in remaining if item]
    oks: list[bool] = []
    for raw in student_vals:
        letter = canonicalize(raw, "choose_two")
        if letter and letter in remaining:
            remaining.remove(letter)
            oks.append(True)
        else:
            oks.append(False)
    return oks


def score_paper(
    answers: dict,
    mode: str = "full",
    keys: dict | None = None,
) -> dict:
    """Mark a set of answers. `answers` keys may be int or str."""
    key_data = keys or load_keys()
    official = official_answers(key_data)
    types = question_types(key_data)
    alts = official_alternatives(key_data)
    limits = question_limits(key_data)
    mode_key = (mode or "full").strip().lower()
    if mode_key not in MODES and mode_key not in SECTION_MODES and mode_key != "full":
        mode_key = "full"
    questions = mode_question_numbers(mode_key)
    total = len(questions)

    raw_answers = {}
    for k, v in (answers or {}).items():
        try:
            raw_answers[int(k)] = "" if v is None else str(v)
        except (TypeError, ValueError):
            continue

    pair_ok: dict[int, bool] = {}
    pair_correct: dict[int, str] = {}
    for (left, right), official_pair in choose_two_pairs(key_data):
        display = ", ".join(
            canonicalize(item, "choose_two") or str(item) for item in official_pair
        )
        pair_correct[left] = display
        pair_correct[right] = display
        oks = _mark_choose_two_pair(
            [raw_answers.get(left, ""), raw_answers.get(right, "")],
            official_pair,
        )
        pair_ok[left], pair_ok[right] = oks[0], oks[1]

    marking = []
    score = 0
    for q in questions:
        student = raw_answers.get(q, "")
        correct = official[q]
        qtype = types.get(q, "notes")
        limit = limits.get(q)
        if q in pair_ok:
            ok = pair_ok[q]
            correct = pair_correct.get(q, correct)
        elif exceeds_word_limit(student, limit):
            ok = False
        else:
            ok = answers_equal(student, correct, qtype, alts.get(q) or [])
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

    band = band_for_score(score, total) if mode_key == "full" and total == 40 else None
    return {
        "score": score,
        "total": total,
        "band_estimate": band,
        "marking": marking,
        "mode": mode_key if mode_key in {*SECTION_MODES, "full"} else "full",
    }


def format_band(band: float | None) -> str | None:
    if band is None:
        return None
    if float(band).is_integer():
        return str(int(band))
    return str(band)


def transcripts(keys: dict | None = None) -> dict[str, str]:
    data = keys or load_keys()
    raw = data.get("transcripts") or {}
    out: dict[str, str] = {}
    for key, text in raw.items():
        out[str(key)] = "" if text is None else str(text)
    return out
