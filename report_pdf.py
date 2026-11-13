"""Teacher-only PDF answer reports for reading, listening and writing submissions."""

from __future__ import annotations

import io
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import reading_scoring as rs
import listening_scoring as ls
import reading_review as rr

BASE_DIR = Path(__file__).resolve().parent
FONTS_DIR = BASE_DIR / "static" / "fonts"

TZ_SHANGHAI = timezone(timedelta(hours=8))

# Droid Sans Fallback covers CJK but has no ASCII; DejaVu covers Latin.
CJK_FONT = "ReportCJK"
LATIN_FONT = "ReportLatin"

INK = colors.HexColor("#3f3c3a")
MUTED = colors.HexColor("#8a847c")
HEADER = colors.HexColor("#5c6b73")
LINE = colors.HexColor("#d6d0c8")
CARD = colors.HexColor("#f7f4f0")
OK = colors.HexColor("#6f8f7a")
BAD = colors.HexColor("#a66a6a")
HEADER_INK = colors.HexColor("#f3f0ec")
ROW_OK_BG = colors.HexColor("#eef3ef")
ROW_BAD_BG = colors.HexColor("#f6eeee")

CJK_FONT_CANDIDATES = (
    FONTS_DIR / "DroidSansFallbackFull.ttf",
    Path("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"),
    Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
    Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
    Path("/usr/share/fonts/truetype/arphic/uming.ttc"),
)

LATIN_FONT_CANDIDATES = (
    FONTS_DIR / "DejaVuSans.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
)

_font_ready = False


def _ttc_sc_index(path: Path) -> int:
    """Prefer a Simplified Chinese face inside a TrueType collection."""
    try:
        from fontTools.ttLib import TTCollection
    except ImportError:
        return 0
    try:
        collection = TTCollection(str(path))
    except Exception:
        return 0
    fallback: int | None = None
    for i, font in enumerate(collection.fonts):
        try:
            name = font["name"].getDebugName(1) or font["name"].getDebugName(4) or ""
        except Exception:
            name = ""
        lower = name.lower()
        if any(token in lower for token in ("sc", "simplified", "gb", "hans", "cn")):
            return i
        if any(token in lower for token in ("cjk", "chinese", "hei", "song", "uming", "kai")):
            if fallback is None:
                fallback = i
    return fallback or 0


def _register_ttfont(name: str, candidates: tuple[Path, ...]) -> str | None:
    errors: list[str] = []
    for path in candidates:
        if not path.is_file():
            continue
        sub = _ttc_sc_index(path) if path.suffix.lower() == ".ttc" else 0
        try:
            pdfmetrics.registerFont(TTFont(name, str(path), subfontIndex=sub))
            return str(path)
        except Exception as exc:  # noqa: BLE001 — try the next candidate
            errors.append(f"{path}: {exc}")
            continue
    if errors:
        raise RuntimeError("; ".join(errors))
    return None


def ensure_fonts() -> str:
    """Register CJK and Latin fonts. Returns the CJK font name."""
    global _font_ready, LATIN_FONT
    registered = set(pdfmetrics.getRegisteredFontNames())
    if _font_ready and CJK_FONT in registered and LATIN_FONT in registered:
        return CJK_FONT

    if CJK_FONT not in registered:
        try:
            cjk_path = _register_ttfont(CJK_FONT, CJK_FONT_CANDIDATES)
        except RuntimeError as exc:
            raise RuntimeError(
                "No CJK-capable font found for PDF reports. "
                "Place DroidSansFallbackFull.ttf in static/fonts/ "
                "or install fonts-droid-fallback / fonts-wqy-microhei."
            ) from exc
        if not cjk_path:
            raise RuntimeError(
                "No CJK-capable font found for PDF reports. "
                "Place DroidSansFallbackFull.ttf in static/fonts/ "
                "or install fonts-droid-fallback / fonts-wqy-microhei."
            )

    if LATIN_FONT not in registered:
        latin_path = None
        try:
            latin_path = _register_ttfont(LATIN_FONT, LATIN_FONT_CANDIDATES)
        except RuntimeError:
            latin_path = None
        if not latin_path:
            # Built-in Type1 font covers ASCII / Latin-1 if DejaVu is missing.
            LATIN_FONT = "Helvetica"

    _font_ready = True
    return CJK_FONT


def _is_cjk_char(ch: str) -> bool:
    """Characters that should come from the CJK fallback font."""
    if not ch:
        return False
    code = ord(ch)
    if (
        0x2E80 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0xFE10 <= code <= 0xFE1F
        or 0xFE30 <= code <= 0xFE4F
        or 0xFF00 <= code <= 0xFFEF
        or 0x20000 <= code <= 0x2FAFF
    ):
        return True
    return ch in "、。，；：？！「」『』（）【】《》—…·•、"


def _split_runs(text: str) -> list[tuple[str, str]]:
    if not text:
        return []
    runs: list[tuple[str, str]] = []
    current = CJK_FONT if _is_cjk_char(text[0]) else LATIN_FONT
    buf: list[str] = []
    for ch in text:
        if ch in " \t":
            buf.append(ch)
            continue
        font = CJK_FONT if _is_cjk_char(ch) else LATIN_FONT
        if font != current and buf:
            # Trailing spaces stay with the previous run.
            runs.append((current, "".join(buf)))
            buf = [ch]
            current = font
        else:
            buf.append(ch)
            current = font
    if buf:
        runs.append((current, "".join(buf)))
    return runs


def _escape(text: object) -> str:
    value = "" if text is None else str(text)
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def mixed_xml(text: object, newlines: bool = False) -> str:
    """Escape text and wrap Latin / CJK runs in <font> tags for Paragraphs."""
    value = "" if text is None else str(text)
    if newlines:
        parts = value.split("\n")
        return "<br/>".join(mixed_xml(part, newlines=False) for part in parts)
    runs = _split_runs(value)
    if not runs:
        return ""
    return "".join(f'<font name="{font}">{_escape(chunk)}</font>' for font, chunk in runs)


def draw_mixed_string(canvas, x: float, y: float, text: str, size: float, align: str = "left") -> None:
    ensure_fonts()
    runs = _split_runs(text) or [(LATIN_FONT, "")]
    widths = [canvas.stringWidth(chunk, font, size) for font, chunk in runs]
    total = sum(widths)
    cursor = x
    if align == "right":
        cursor = x - total
    elif align == "center":
        cursor = x - total / 2
    for (font, chunk), width in zip(runs, widths):
        canvas.setFont(font, size)
        canvas.drawString(cursor, y, chunk)
        cursor += width


def report_filename(record: dict) -> str:
    module = _record_module(record)
    raw_name = (record.get("candidate_name") or "candidate").strip() or "candidate"
    safe = re.sub(r"[^\w\u4e00-\u9fff\-]+", "", raw_name, flags=re.UNICODE)
    safe = safe.strip("._-") or "candidate"
    safe = safe[:40]
    ts = str(record.get("timestamp") or "")
    matched = re.match(r"(\d{4})-(\d{2})-(\d{2})", ts)
    date_part = (
        f"{matched.group(1)}{matched.group(2)}{matched.group(3)}"
        if matched
        else datetime.now(TZ_SHANGHAI).strftime("%Y%m%d")
    )
    return f"{module}-{safe}-{date_part}-report.pdf"


def _is_reading(record: dict | None) -> bool:
    if not record:
        return False
    return (record.get("module") or "").strip().lower() == "reading"


def _is_listening(record: dict | None) -> bool:
    if not record:
        return False
    return (record.get("module") or "").strip().lower() == "listening"


def _record_module(record: dict | None) -> str:
    if _is_reading(record):
        return "reading"
    if _is_listening(record):
        return "listening"
    return "writing"


def attach_explanations(record: dict, keys: dict | None = None) -> list[dict]:
    explanations: dict[int, str] = {}
    key_data = keys if keys is not None else rs.load_keys()
    questions = key_data.get("questions") or {}
    for q, meta in questions.items():
        try:
            qn = int(q)
        except (TypeError, ValueError):
            continue
        explanations[qn] = (meta.get("explanation") or "") if isinstance(meta, dict) else ""
    rows = []
    for row in record.get("marking") or []:
        item = dict(row)
        try:
            qn = int(item.get("q") or 0)
        except (TypeError, ValueError):
            qn = 0
        if not (item.get("explanation") or "").strip():
            item["explanation"] = explanations.get(qn, "")
        rows.append(item)
    return rows


def _styles() -> dict[str, ParagraphStyle]:
    ensure_fonts()
    # Default font is CJK; mixed_xml always tags runs explicitly.
    return {
        "section": ParagraphStyle(
            "ReportSection",
            fontName=CJK_FONT,
            fontSize=11,
            leading=16,
            textColor=HEADER,
            spaceBefore=0,
            spaceAfter=6,
        ),
        "meta_value": ParagraphStyle(
            "ReportMetaValue",
            fontName=CJK_FONT,
            fontSize=9.5,
            leading=13,
            textColor=INK,
        ),
        "th": ParagraphStyle(
            "ReportTh",
            fontName=CJK_FONT,
            fontSize=8.5,
            leading=12,
            textColor=HEADER_INK,
            alignment=TA_CENTER,
        ),
        "td": ParagraphStyle(
            "ReportTd",
            fontName=CJK_FONT,
            fontSize=8.5,
            leading=12,
            textColor=INK,
            alignment=TA_LEFT,
        ),
        "td_center": ParagraphStyle(
            "ReportTdCenter",
            fontName=CJK_FONT,
            fontSize=8.5,
            leading=12,
            textColor=INK,
            alignment=TA_CENTER,
        ),
        "ok": ParagraphStyle(
            "ReportOk",
            fontName=CJK_FONT,
            fontSize=8.5,
            leading=12,
            textColor=OK,
            alignment=TA_CENTER,
        ),
        "bad": ParagraphStyle(
            "ReportBad",
            fontName=CJK_FONT,
            fontSize=8.5,
            leading=12,
            textColor=BAD,
            alignment=TA_CENTER,
        ),
        "muted": ParagraphStyle(
            "ReportMuted",
            fontName=CJK_FONT,
            fontSize=8.5,
            leading=12,
            textColor=MUTED,
        ),
        "essay": ParagraphStyle(
            "ReportEssay",
            fontName=CJK_FONT,
            fontSize=10,
            leading=16,
            textColor=INK,
            borderPadding=4,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            fontName=CJK_FONT,
            fontSize=9.5,
            leading=14,
            textColor=INK,
            spaceAfter=3,
        ),
        "profile_title": ParagraphStyle(
            "ReportProfileTitle",
            fontName=CJK_FONT,
            fontSize=9.5,
            leading=13,
            textColor=HEADER,
            spaceBefore=2,
            spaceAfter=2,
        ),
    }



def format_duration(seconds) -> str:
    """Format a duration for students and teachers, e.g. 45min12s.

    Values under one minute are shown as 12s; zero is 0s. None is —.
    """
    if seconds is None or seconds is False:
        return "—"
    try:
        total = int(seconds)
    except (TypeError, ValueError):
        return "—"
    total = max(0, total)
    if total < 60:
        return f"{total}s"
    minutes, rem = divmod(total, 60)
    return f"{minutes}min{rem}s"


def part_times_summary(part_times, label: str = "Passage") -> str | None:
    """Human-readable part times, or None if the field is absent."""
    if not isinstance(part_times, dict) or not part_times:
        return None
    labels = []
    found = False
    keys = ("1", "2", "3", "4") if label == "Section" else ("1", "2", "3")
    for key in keys:
        raw = part_times.get(key, part_times.get(int(key)))
        if raw is None:
            continue
        found = True
        labels.append(f"{label} {key} {format_duration(raw)}")
    if not found:
        return None
    return " · ".join(labels)


def _meta_pairs(record: dict, invite: dict | None) -> list[tuple[str, str]]:
    reading = _is_reading(record)
    listening = _is_listening(record)
    scored = reading or listening
    invite_text = "—"
    if invite:
        code = invite.get("code") or ""
        note = (invite.get("note") or "").strip()
        invite_text = f"{code}（{note}）" if note else (code or "—")
    elif record.get("invite_code_id"):
        invite_text = str(record.get("invite_code_id"))

    if listening:
        subject = "听力"
    elif reading:
        subject = "阅读"
    else:
        subject = "写作"
    pairs: list[tuple[str, str]] = [
        ("考生", (record.get("candidate_name") or "—")),
        ("邀请码", invite_text),
        ("科目", subject),
        ("模式", str(record.get("mode") or "—")),
        ("套卷", str(record.get("prompt_set_id") or "—")),
        ("交卷时间", f"{record.get('timestamp') or '—'}（Asia/Shanghai）"),
    ]
    if scored:
        score = record.get("score")
        total = record.get("total")
        score_text = "—"
        if score is not None and total is not None:
            score_text = f"{score}/{total}"
        band_fn = ls.format_band if listening else rs.format_band
        band = band_fn(record.get("band_estimate"))
        if band:
            band_text = band
        elif record.get("mode") != "full":
            if listening:
                band_text = "—（单部分模式仅记原始分）"
            else:
                band_text = "—（单篇模式仅记原始分）"
        else:
            band_text = "—"
        pairs.append(("成绩", score_text))
        pairs.append(("参考分数", band_text))
    else:
        pairs.append(("Task 1 题", str(record.get("task1_prompt_id") or "—")))
        pairs.append(("Task 2 题", str(record.get("task2_prompt_id") or "—")))
        t1w = record.get("task1_word_count")
        t2w = record.get("task2_word_count")
        pairs.append(
            (
                "词数",
                f"Task 1 {t1w if t1w is not None else 0} 词 · Task 2 {t2w if t2w is not None else 0} 词",
            )
        )

    used = record.get("time_used_seconds")
    remain = record.get("time_remaining_seconds")
    paused = record.get("paused_total_seconds") or 0
    pairs.append(
        (
            "用时",
            (
                f"用时 {format_duration(used)} · 剩余 {format_duration(remain)}"
                f" · 暂停累计 {format_duration(paused)}"
            ),
        )
    )
    if scored:
        part_label = part_times_summary(
            record.get("part_times"),
            label="Section" if listening else "Passage",
        )
        pairs.append(("各部分用时", part_label or "本题卷未记录各部分用时"))
    pairs.append(("自动提交", "是" if record.get("auto_submitted") else "否"))
    pairs.append(("答卷 ID", str(record.get("id") or "—")))
    return pairs


def _meta_table(record: dict, invite: dict | None, styles: dict[str, ParagraphStyle]) -> Table:
    pairs = _meta_pairs(record, invite)
    cells: list[list] = []
    row: list = []
    for label, value in pairs:
        block = Paragraph(
            f"<font color='#8a847c' size='8'>{mixed_xml(label)}</font><br/>{mixed_xml(value)}",
            styles["meta_value"],
        )
        row.append(block)
        if len(row) == 2:
            cells.append(row)
            row = []
    if row:
        row.append("")
        cells.append(row)

    usable = A4[0] - 32 * mm
    table = Table(cells, colWidths=[usable / 2, usable / 2])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CARD),
                ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table



def _plain_parts(parts, answers: dict[str, str], official: dict[int, str]) -> str:
    bits: list[str] = []
    for part in parts or []:
        if isinstance(part, dict) and part.get("q") is not None:
            qn = int(part["q"])
            prefix = part.get("prefix") or ""
            student = (answers.get(str(qn)) or "").strip() or "______"
            correct = official.get(qn) or ""
            bits.append(f"{prefix}[{qn}] {student}")
            if correct:
                bits.append(f"（标准答案：{correct}）")
        else:
            bits.append("" if part is None else str(part))
    return "".join(bits)


def _listening_notes_tables(record: dict, styles: dict[str, ParagraphStyle]) -> list:
    """Filled Section 1 notes table for the teacher PDF."""
    paper = ls.load_paper()
    official = ls.official_answers()
    answers = {}
    raw = record.get("answers") or {}
    if isinstance(raw, dict):
        answers = {str(k): "" if v is None else str(v) for k, v in raw.items()}
    story: list = []
    usable = A4[0] - 32 * mm
    for section in paper.get("sections") or []:
        for group in section.get("groups") or []:
            if group.get("type") != "notes_table":
                continue
            table = group.get("table") or {}
            headers = table.get("headers") or []
            if not headers:
                continue
            title = table.get("title") or group.get("heading") or "Notes"
            story.append(Paragraph(mixed_xml(str(title)), styles["section"]))
            col_w = usable / max(len(headers), 1)
            data = [[Paragraph(mixed_xml(h), styles["th"]) for h in headers]]
            for row in table.get("rows") or []:
                cells = []
                for cell in row or []:
                    lines = cell if isinstance(cell, list) else [cell]
                    chunks = []
                    for line in lines:
                        line_parts = line if isinstance(line, list) else [line]
                        chunks.append(_plain_parts(line_parts, answers, official))
                    cells.append(Paragraph(mixed_xml("\n".join(chunks), newlines=True), styles["td"]))
                while len(cells) < len(headers):
                    cells.append(Paragraph("", styles["td"]))
                data.append(cells[: len(headers)])
            pdf_table = Table(data, colWidths=[col_w] * len(headers))
            pdf_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HEADER),
                        ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_INK),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("GRID", (0, 0), (-1, -1), 0.3, LINE),
                        ("LEFTPADDING", (0, 0), (-1, -1), 3),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("BACKGROUND", (0, 1), (-1, -1), CARD),
                    ]
                )
            )
            story.append(pdf_table)
            story.append(Spacer(1, 5 * mm))
    return story


def _marking_table(rows: list[dict], styles: dict[str, ParagraphStyle]) -> Table:
    usable = A4[0] - 32 * mm
    widths = [14 * mm, 30 * mm, 30 * mm, 16 * mm, usable - 90 * mm]
    header = [
        Paragraph(mixed_xml("题号"), styles["th"]),
        Paragraph(mixed_xml("学生作答"), styles["th"]),
        Paragraph(mixed_xml("标准答案"), styles["th"]),
        Paragraph(mixed_xml("对错"), styles["th"]),
        Paragraph(mixed_xml("解析"), styles["th"]),
    ]
    data = [header]
    style_cmds: list = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 0), (3, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.3, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, row in enumerate(rows, start=1):
        student = (row.get("student") or "").strip() or "（未作答）"
        correct = row.get("correct") if row.get("correct") is not None else row.get("answer") or ""
        ok = bool(row.get("ok"))
        verdict_style = styles["ok"] if ok else styles["bad"]
        data.append(
            [
                Paragraph(mixed_xml(row.get("q") or ""), styles["td_center"]),
                Paragraph(mixed_xml(student, newlines=True), styles["td"]),
                Paragraph(mixed_xml(correct, newlines=True), styles["td"]),
                Paragraph(mixed_xml("正确" if ok else "错误"), verdict_style),
                Paragraph(mixed_xml(row.get("explanation") or "—", newlines=True), styles["td"]),
            ]
        )
        bg = ROW_OK_BG if ok else ROW_BAD_BG
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle(style_cmds))
    return table


def _essay_block(title: str, text: str, styles: dict[str, ParagraphStyle]) -> list:
    body = (text or "").strip() or "（未作答）"
    return [
        Paragraph(mixed_xml(title), styles["section"]),
        Spacer(1, 2 * mm),
        Paragraph(mixed_xml(body, newlines=True), styles["essay"]),
        Spacer(1, 5 * mm),
    ]


def _draw_chrome(canvas, _doc, generated_label: str) -> None:
    canvas.saveState()
    width, height = A4
    ensure_fonts()
    canvas.setFillColor(HEADER)
    canvas.rect(0, height - 18 * mm, width, 18 * mm, fill=1, stroke=0)
    canvas.setFillColor(HEADER_INK)
    draw_mixed_string(canvas, 16 * mm, height - 7.5 * mm, "Rosette Exclusive Mock Exam", 8.5)
    draw_mixed_string(canvas, 16 * mm, height - 14.2 * mm, "答题报告", 13)
    draw_mixed_string(canvas, width - 16 * mm, height - 11 * mm, generated_label, 8, align="right")

    canvas.setFillColor(LINE)
    canvas.rect(0, 0, width, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(INK)
    draw_mixed_string(canvas, 16 * mm, 5 * mm, "仅供教师使用 · 请勿发给学生", 8)
    draw_mixed_string(canvas, width - 16 * mm, 5 * mm, str(canvas.getPageNumber()), 8, align="right")
    canvas.restoreState()



def _format_structure(profile: dict) -> str:
    structure = (profile.get("structure") or "").strip() or "暂未标注"
    detail = (profile.get("structure_detail") or "").strip()
    if detail:
        return f"{structure}。{detail}"
    return structure


def _passage_time_label(profile: dict) -> str:
    if profile.get("time_recorded"):
        return format_duration(profile.get("time_seconds"))
    return "本题卷未记录"


def _passage_overview_story(record: dict, styles: dict[str, ParagraphStyle]) -> list:
    profiles = rr.passage_profiles(record)
    if not profiles:
        return []
    story: list = [
        Paragraph(mixed_xml("篇章信息"), styles["section"]),
        Paragraph(
            mixed_xml("各篇题材、文章类型与结构类型供教师备课参考；各部分用时取自考生在该篇的计时记录。"),
            styles["muted"],
        ),
        Spacer(1, 2 * mm),
    ]
    for profile in profiles:
        title = profile.get("title") or "（无标题）"
        heading = f"Passage {profile['id']}  {title}    用时 {_passage_time_label(profile)}"
        story.append(Paragraph(mixed_xml(heading), styles["profile_title"]))
        topic = (profile.get("topic") or "").strip() or "暂未标注"
        genre = (profile.get("genre") or "").strip() or "暂未标注"
        story.append(Paragraph(mixed_xml(f"题材：{topic}"), styles["body"]))
        story.append(Paragraph(mixed_xml(f"文章类型：{genre}"), styles["body"]))
        story.append(
            Paragraph(mixed_xml(f"结构类型：{_format_structure(profile)}"), styles["body"])
        )
        story.append(Spacer(1, 2 * mm))
    story.append(Spacer(1, 3 * mm))
    return story


def _highlight_review_story(record: dict, styles: dict[str, ParagraphStyle]) -> list:
    review = rr.highlight_review(record)
    paragraphs = review.get("paragraphs") or []
    if not paragraphs:
        return []
    story: list = [
        Paragraph(mixed_xml("高亮与扫跳评述"), styles["section"]),
        Paragraph(
            mixed_xml("依据学生在文章与题干中的高亮所作的教师评述，不发给学生。"),
            styles["muted"],
        ),
        Spacer(1, 2 * mm),
    ]
    for para in paragraphs:
        story.append(Paragraph(mixed_xml(para), styles["body"]))
    story.append(Spacer(1, 5 * mm))
    return story


def build_submission_report(
    record: dict,
    invite: dict | None = None,
    generated_at: datetime | None = None,
) -> bytes:
    """Return a complete A4 PDF as bytes."""
    ensure_fonts()
    styles = _styles()
    generated = generated_at or datetime.now(TZ_SHANGHAI)
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=TZ_SHANGHAI)
    else:
        generated = generated.astimezone(TZ_SHANGHAI)
    generated_label = f"生成时间：{generated.strftime('%Y-%m-%d %H:%M:%S')}（Asia/Shanghai）"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=24 * mm,
        bottomMargin=16 * mm,
        title=f"答题报告 · {record.get('candidate_name') or record.get('id') or ''}",
        author="Rosette Exclusive Mock Exam",
        subject="教师答题报告",
    )

    story: list = [
        Paragraph(mixed_xml("答题记录"), styles["section"]),
        _meta_table(record, invite, styles),
        Spacer(1, 7 * mm),
    ]

    if _is_reading(record):
        story.extend(_passage_overview_story(record, styles))
        story.extend(_highlight_review_story(record, styles))
        rows = attach_explanations(record)
        story.append(Paragraph(mixed_xml("逐题批改"), styles["section"]))
        story.append(
            Paragraph(
                mixed_xml("学生答案对照标准答案；解析仅供教师备课使用。"),
                styles["muted"],
            )
        )
        story.append(Spacer(1, 2 * mm))
        if rows:
            story.append(_marking_table(rows, styles))
        else:
            story.append(Paragraph(mixed_xml("本题卷没有逐题记录。"), styles["muted"]))
    elif _is_listening(record):
        story.extend(_listening_notes_tables(record, styles))
        rows = attach_explanations(record, keys=ls.load_keys())
        story.append(Paragraph(mixed_xml("逐题批改"), styles["section"]))
        story.append(
            Paragraph(
                mixed_xml("学生答案对照标准答案；解析与录音文本仅供教师备课使用。"),
                styles["muted"],
            )
        )
        story.append(Spacer(1, 2 * mm))
        if rows:
            story.append(_marking_table(rows, styles))
        else:
            story.append(Paragraph(mixed_xml("本题卷没有逐题记录。"), styles["muted"]))
        transcripts = ls.transcripts()
        if transcripts:
            story.append(Spacer(1, 6 * mm))
            story.append(Paragraph(mixed_xml("录音文本"), styles["section"]))
            for sid in ("1", "2", "3", "4"):
                text = transcripts.get(sid) or ""
                if not text:
                    continue
                story.extend(
                    _essay_block(f"Section {sid}", text, styles)
                )
    else:
        story.extend(
            _essay_block(
                f"Task 1（{record.get('task1_word_count') or 0} 词）",
                record.get("task1_text") or "",
                styles,
            )
        )
        story.extend(
            _essay_block(
                f"Task 2（{record.get('task2_word_count') or 0} 词）",
                record.get("task2_text") or "",
                styles,
            )
        )

    def chrome(canvas, doc_):
        _draw_chrome(canvas, doc_, generated_label)

    doc.build(story, onFirstPage=chrome, onLaterPages=chrome)
    return buffer.getvalue()
