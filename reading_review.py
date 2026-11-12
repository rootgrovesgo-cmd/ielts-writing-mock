"""Teacher-facing passage labels and highlight (skim/scan) review.

Highlights are stored as HTML on the submission, but this module only parses
them as text. Nothing here should be rendered as raw HTML in the admin UI.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

import reading_scoring as rs

BASE_DIR = Path(__file__).resolve().parent
META_PATH = BASE_DIR / "prompts" / "passage_meta.json"

PASSAGE_IDS = ("1", "2", "3")

_STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "from",
    "this",
    "these",
    "those",
    "were",
    "was",
    "are",
    "been",
    "have",
    "has",
    "had",
    "not",
    "but",
    "into",
    "onto",
    "over",
    "under",
    "about",
    "after",
    "before",
    "which",
    "their",
    "there",
    "they",
    "them",
    "than",
    "then",
    "when",
    "what",
    "who",
    "whom",
    "whose",
    "how",
    "why",
    "also",
    "only",
    "more",
    "most",
    "some",
    "such",
    "other",
    "between",
    "among",
    "could",
    "would",
    "should",
    "might",
    "must",
    "will",
    "can",
    "reading",
    "passage",
    "questions",
    "question",
    "complete",
    "notes",
    "below",
    "following",
    "statements",
    "agree",
    "information",
    "given",
    "writer",
    "claims",
    "choose",
    "correct",
    "letter",
    "boxes",
    "answer",
    "sheet",
    "true",
    "false",
    "yes",
}

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]{3,}")
_NUMBER = re.compile(
    r"\d+(?:[.,]\d+)?(?:\s*(?:%|per\s*cent|percent|million|billion|thousand))?",
    re.IGNORECASE,
)
_PROPER = re.compile(
    r"\b(?:[A-Z]{2,}|"
    r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+|"
    r"[A-Z][a-z]{2,})\b"
)

_meta_cache: dict | None = None


def load_passage_meta(path: Path | None = None) -> dict:
    """Load teacher labels keyed by paper id (e.g. set-a)."""
    global _meta_cache
    target = path or META_PATH
    if path is None and _meta_cache is not None:
        return _meta_cache
    if not target.is_file():
        data: dict = {}
    else:
        with target.open(encoding="utf-8") as fh:
            data = json.load(fh) or {}
    if path is None:
        _meta_cache = data
    return data


def paper_path_for_set(set_id: str | None) -> Path | None:
    """Best-effort paper path so a later set can be added beside Set A."""
    token = (set_id or "set-a").strip() or "set-a"
    candidates = [
        BASE_DIR / "prompts" / f"reading_{token.replace('-', '_')}.json",
        BASE_DIR / "prompts" / f"reading-{token}.json",
        BASE_DIR / "prompts" / f"{token}.json",
    ]
    if token == "set-a":
        candidates.insert(0, rs.PAPER_PATH)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    if token == "set-a":
        return rs.PAPER_PATH
    return None


def load_paper_for_set(set_id: str | None) -> dict | None:
    path = paper_path_for_set(set_id)
    if not path:
        return None
    try:
        return rs.load_paper(path)
    except (OSError, json.JSONDecodeError):
        return None


def part_times_recorded(part_times) -> bool:
    """True when the submission actually stored a part_times object."""
    if not isinstance(part_times, dict) or not part_times:
        return False
    for key in PASSAGE_IDS:
        if part_times.get(key) is not None:
            return True
        try:
            if part_times.get(int(key)) is not None:
                return True
        except (TypeError, ValueError):
            continue
    return False


def part_time_seconds(part_times, passage_id: str) -> int | None:
    if not part_times_recorded(part_times):
        return None
    raw = part_times.get(str(passage_id))
    if raw is None:
        try:
            raw = part_times.get(int(passage_id))
        except (TypeError, ValueError):
            raw = None
    if raw is None:
        return None
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return None


def expected_passage_ids(record: dict | None) -> tuple[str, ...]:
    mode = ((record or {}).get("mode") or "full").strip()
    if mode == "passage1":
        return ("1",)
    if mode == "passage2":
        return ("2",)
    if mode == "passage3":
        return ("3",)
    return PASSAGE_IDS


def passage_profiles(record: dict, meta: dict | None = None) -> list[dict]:
    """Teacher labels plus per-passage times for the paper on this submission."""
    set_id = (record.get("prompt_set_id") or "set-a").strip() or "set-a"
    catalog = meta if meta is not None else load_passage_meta()
    set_meta = catalog.get(set_id) or {}
    labels = set_meta.get("passages") or {}
    paper = load_paper_for_set(set_id)
    titles: dict[str, str] = {}
    if paper:
        for item in paper.get("passages") or []:
            pid = str(item.get("id") or "").strip()
            if pid:
                titles[pid] = (item.get("title") or "").strip()

    profiles = []
    part_times = record.get("part_times")
    for pid in expected_passage_ids(record):
        entry = {}
        for key, value in labels.items():
            if str(key) == pid and isinstance(value, dict):
                entry = value
                break
        seconds = part_time_seconds(part_times, pid)
        title = (entry.get("title") or titles.get(pid) or "").strip()
        profiles.append(
            {
                "id": pid,
                "title": title,
                "topic": (entry.get("topic") or "").strip(),
                "genre": (entry.get("genre") or "").strip(),
                "structure": (entry.get("structure") or "").strip(),
                "structure_detail": (entry.get("structure_detail") or "").strip(),
                "time_seconds": seconds,
                "time_recorded": seconds is not None,
            }
        )
    return profiles


class _HighlightParser(HTMLParser):
    """Collect <mark class="hl"> text and ignore script/style payloads."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.marks: list[str] = []
        self._in_mark = 0
        self._ignore = 0
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        name = (tag or "").lower()
        if name in {"script", "style"}:
            self._ignore += 1
            return
        if name == "mark" and self._is_hl(attrs):
            self._in_mark += 1
            if self._in_mark == 1:
                self._buf = []

    def handle_endtag(self, tag: str) -> None:
        name = (tag or "").lower()
        if name in {"script", "style"} and self._ignore:
            self._ignore -= 1
            return
        if name == "mark" and self._in_mark:
            self._in_mark -= 1
            if self._in_mark == 0:
                text = _norm("".join(self._buf))
                if text:
                    self.marks.append(text)

    def handle_data(self, data: str) -> None:
        if self._ignore or not self._in_mark:
            return
        self._buf.append(data or "")

    @staticmethod
    def _is_hl(attrs) -> bool:
        classes = ""
        for key, value in attrs or ():
            if (key or "").lower() == "class":
                classes = value or ""
                break
        return "hl" in classes.split()


def extract_highlight_marks(html: str | None) -> list[str]:
    """Safely pull highlight texts out of stored HTML. Never executes markup."""
    if not html or not isinstance(html, str):
        return []
    parser = _HighlightParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        # Malformed fragments should not break the teacher report.
        return list(parser.marks)
    return list(parser.marks)


def _norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()


def _sentences(text: str) -> list[str]:
    cleaned = _norm(text)
    if not cleaned:
        return []
    parts = [part.strip() for part in _SENTENCE_SPLIT.split(cleaned) if part.strip()]
    return parts or [cleaned]


def _overlap(a: str, b: str) -> int:
    left, right = _norm(a).lower(), _norm(b).lower()
    if not left or not right:
        return 0
    if left in right or right in left:
        return min(len(left), len(right))
    # Shared prefix of reasonable length, e.g. a truncated topic sentence.
    limit = min(len(left), len(right))
    n = 0
    for i in range(limit):
        if left[i] == right[i]:
            n += 1
        else:
            break
    if n >= 24:
        return n
    return 0


def _is_skim(mark: str, anchors: list[str]) -> bool:
    text = _norm(mark)
    if len(text) < 12:
        return False
    for anchor in anchors:
        shared = _overlap(text, anchor)
        if shared >= 20 or (anchor and shared / max(len(anchor), 1) >= 0.5):
            return True
        if anchor and len(text) >= 40 and _overlap(text[:80], anchor[:80]) >= 20:
            return True
    return False


def _token_set(text: str) -> set[str]:
    return {m.group(0).lower() for m in _WORD.finditer(text or "")}


def _is_scan(mark: str, keywords: set[str]) -> bool:
    text = _norm(mark)
    if not text:
        return False
    words = text.split()
    short = len(text) <= 48 or len(words) <= 8
    has_number = bool(_NUMBER.search(text))
    # Mid-span or short proper nouns; ignore a single capital only if the
    # whole highlight is a long sentence starting with one.
    propers = [m.group(0) for m in _PROPER.finditer(text)]
    if not short:
        propers = [p for p in propers if p != words[0] or len(words) <= 8]
    has_proper = bool(propers)
    tokens = _token_set(text)
    has_keyword = bool(tokens & keywords)
    if has_number or has_keyword:
        return True
    if has_proper and (short or len(propers) >= 2):
        return True
    return False


def _collect_keywords(paper: dict | None, passage_id: str) -> set[str]:
    if not paper:
        return set()
    blobs: list[str] = []
    for group in paper.get("groups") or []:
        if str(group.get("passage") or "") != str(passage_id):
            continue
        _walk_strings(group, blobs)
    words: set[str] = set()
    for blob in blobs:
        for match in _WORD.finditer(blob):
            token = match.group(0).lower()
            if token in _STOPWORDS or len(token) < 5:
                continue
            words.add(token)
        for match in _PROPER.finditer(blob):
            words.add(match.group(0).lower())
    return words


def _walk_strings(obj, out: list[str]) -> None:
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for value in obj.values():
            _walk_strings(value, out)
    elif isinstance(obj, list):
        for value in obj:
            _walk_strings(value, out)


def _paragraphs_for(paper: dict | None, passage_id: str) -> list[str]:
    if not paper:
        return []
    for item in paper.get("passages") or []:
        if str(item.get("id") or "") == str(passage_id):
            return [p for p in (item.get("paragraphs") or []) if isinstance(p, str)]
    return []


def _skim_anchors(paragraphs: list[str]) -> list[str]:
    anchors: list[str] = []
    for para in paragraphs:
        sentences = _sentences(para)
        if not sentences:
            continue
        anchors.append(sentences[0])
        if len(sentences) > 1:
            anchors.append(sentences[-1])
        # First dozen words also stand in for a topic-sentence highlight.
        words = _norm(para).split()
        if len(words) >= 8:
            anchors.append(" ".join(words[:12]))
    return anchors


def _highlight_payload(record: dict) -> dict:
    raw = record.get("highlights")
    return raw if isinstance(raw, dict) else {}


def collect_highlight_stats(record: dict, paper: dict | None = None) -> dict:
    """Structured skim/scan stats for one reading submission."""
    set_id = (record.get("prompt_set_id") or "set-a").strip() or "set-a"
    paper = paper if paper is not None else load_paper_for_set(set_id)
    payload = _highlight_payload(record)
    passage_html = payload.get("passage") or payload.get("passages") or {}
    if not isinstance(passage_html, dict):
        passage_html = {}
    question_marks = extract_highlight_marks(payload.get("questions") if isinstance(payload.get("questions"), str) else "")

    expected = expected_passage_ids(record)
    passages: dict[str, dict] = {}
    total_marks = 0
    total_hl_chars = 0
    total_skim = 0
    total_scan = 0

    for pid in expected:
        html = passage_html.get(pid, passage_html.get(int(pid) if pid.isdigit() else pid, ""))
        if not isinstance(html, str):
            html = ""
        marks = extract_highlight_marks(html)
        paragraphs = _paragraphs_for(paper, pid)
        source = " ".join(paragraphs)
        source_len = max(len(_norm(source)), 1)
        anchors = _skim_anchors(paragraphs)
        keywords = _collect_keywords(paper, pid)
        skim = sum(1 for mark in marks if _is_skim(mark, anchors))
        scan = sum(1 for mark in marks if _is_scan(mark, keywords))
        hl_chars = sum(len(mark) for mark in marks)
        density = min(hl_chars / source_len, 1.0) if marks else 0.0
        passages[pid] = {
            "marks": marks,
            "count": len(marks),
            "chars": hl_chars,
            "density": density,
            "skim": skim,
            "scan": scan,
            "source_len": source_len,
        }
        total_marks += len(marks)
        total_hl_chars += hl_chars
        total_skim += skim
        total_scan += scan

    has_highlights = total_marks > 0 or bool(question_marks)
    return {
        "has_highlights": has_highlights,
        "question_marks": question_marks,
        "question_count": len(question_marks),
        "passages": passages,
        "total_marks": total_marks,
        "total_chars": total_hl_chars,
        "total_skim": total_skim,
        "total_scan": total_scan,
        "expected": expected,
        "mode": (record.get("mode") or "full").strip() or "full",
    }


def _pct(density: float) -> str:
    pct = int(round(density * 100))
    return f"{pct}%"


def _passage_spread_sentence(stats: dict) -> str:
    bits = []
    for pid in stats["expected"]:
        info = stats["passages"][pid]
        if info["count"] == 0:
            bits.append(f"Passage {pid}（无）")
        else:
            bits.append(
                f"Passage {pid}（{info['count']} 处，约占该篇 {_pct(info['density'])}）"
            )
    return "、".join(bits)


def highlight_review(record: dict, paper: dict | None = None) -> dict:
    """Return teacher-facing Chinese commentary. Never includes raw HTML."""
    if (record.get("module") or "").strip().lower() != "reading":
        return {
            "has_highlights": False,
            "paragraphs": [],
            "text": "",
            "stats": {},
        }

    stats = collect_highlight_stats(record, paper=paper)
    if not stats["has_highlights"]:
        text = "本题卷未保存高亮记录，无法根据标注判断考生是否运用了扫读与跳读结合的策略。"
        return {
            "has_highlights": False,
            "paragraphs": [text],
            "text": text,
            "stats": stats,
        }

    paragraphs: list[str] = []
    q_bit = ""
    if stats["question_count"]:
        q_bit = f"；题干中另有 {stats['question_count']} 处标注"

    if stats["total_marks"]:
        paragraphs.append(
            f"本题卷在文章中共保存高亮 {stats['total_marks']} 处，分布为"
            f"{_passage_spread_sentence(stats)}{q_bit}。"
        )
    else:
        paragraphs.append(
            f"本题卷的文章中没有保存高亮，题干中有 {stats['question_count']} 处标注。"
        )

    densities = [stats["passages"][pid]["density"] for pid in stats["expected"]]
    overall = 0.0
    source_total = sum(stats["passages"][pid]["source_len"] for pid in stats["expected"])
    if source_total:
        overall = min(stats["total_chars"] / source_total, 1.0)

    sparse = stats["total_marks"] <= 2 and overall < 0.03 and stats["total_chars"] < 80
    dense = any(d >= 0.45 for d in densities) or overall >= 0.40
    concentrated = False
    concentrated_id = None
    if stats["mode"] == "full" and stats["total_chars"] > 0 and len(stats["expected"]) > 1:
        ranked = sorted(
            stats["expected"],
            key=lambda pid: stats["passages"][pid]["chars"],
            reverse=True,
        )
        top = ranked[0]
        share = stats["passages"][top]["chars"] / max(stats["total_chars"], 1)
        others_empty = all(
            stats["passages"][pid]["count"] == 0 or stats["passages"][pid]["density"] < 0.02
            for pid in ranked[1:]
        )
        if share >= 0.7 and others_empty:
            concentrated = True
            concentrated_id = top

    skim_n = stats["total_skim"]
    scan_n = stats["total_scan"]
    both = skim_n > 0 and scan_n > 0

    if sparse and not stats["question_count"]:
        paragraphs.append(
            "高亮极为稀疏，仅有零星标注，不足以据此判断考生是否有意识地结合了扫读与跳读。"
        )
    elif not stats["total_marks"] and stats["question_count"]:
        paragraphs.append(
            "仅见题干关键词标注，未见文章中的勾画，较难判断考生在正文中如何结合扫读与跳读；题干标注本身更接近跳读定位。"
        )
    else:
        pieces = []
        if skim_n:
            pieces.append(
                f"有 {skim_n} 处落在段落首句、尾句或主题句附近，更接近扫读（扫读抓取段意）"
            )
        if scan_n:
            pieces.append(
                f"有 {scan_n} 处是对地名、数据、专有名词或题干关键词的较短标注，更接近跳读（跳读定位细节）"
            )
        if both:
            pattern = (
                "从位置和内容看，"
                + "；".join(pieces)
                + "。整体上呈现出扫读与跳读结合的痕迹"
            )
        elif skim_n:
            pattern = (
                "从位置和内容看，"
                + "；".join(pieces)
                + "。整体更偏向扫读，跳读定位的痕迹不明显"
            )
        elif scan_n:
            pattern = (
                "从位置和内容看，"
                + "；".join(pieces)
                + "。整体更偏向跳读，对段落主旨句的扫读勾画不多"
            )
        else:
            pattern = (
                "已有标注，但既不明显集中在段落首尾或主题句，也不典型地落在数字、专有名词等定位信息上，"
                "策略倾向不够清晰，不宜强作扫跳结合的判断"
            )
        if dense:
            pattern += (
                "。同时，部分篇章高亮过密，更像通篇涂画，选择性和指向性不足，"
                "教师可提醒学生控制勾画范围，避免以画代读"
            )
        elif not sparse:
            pattern += "。各处密度总体适中，未见通篇涂画"
        pattern += "。"
        paragraphs.append(pattern)

        if concentrated and concentrated_id:
            paragraphs.append(
                f"高亮明显集中在 Passage {concentrated_id}，其余篇章几乎没有标注，"
                "时间分配或阅读策略可能不够均衡。"
            )

    text = "\n\n".join(paragraphs)
    return {
        "has_highlights": True,
        "paragraphs": paragraphs,
        "text": text,
        "stats": stats,
        "sparse": sparse,
        "dense": dense,
        "concentrated": concentrated,
        "both": both,
    }


def highlight_review_text(record: dict, paper: dict | None = None) -> str:
    return highlight_review(record, paper=paper).get("text") or ""
