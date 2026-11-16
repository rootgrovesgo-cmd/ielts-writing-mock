"""Original classroom totem used as a growth progress bar.

Eight stacked chibi creatures are drawn as soft rounded inline SVG, not
copied from any official artwork or sprite sheet. Lighting fills inclusive
half-bands from the bottom (5.5) up to the student's best usable score, with
9.0 as the capstone at the top. Unlit figures are a single grey silhouette.
Official marks and logos are not used.

Usable scores are reading official/reference bands, listening official/reference
bands, and writing teacher bands only. Hidden writing official scores and
speaking scores are ignored.
"""

from __future__ import annotations

import html
from pathlib import Path

# Bottom-up order. A best band of 7.0 lights the first four stages.
STAGES: tuple[float, ...] = (5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0)
STAGE_IDS: tuple[str, ...] = (
    "duck",
    "turtle",
    "egg",
    "sprout",
    "pink",
    "lizard",
    "fox",
    "mouse",
)

TITLE = "成长进度"
EMPTY_STATUS = "暂无评分"
WAITING_STATUS = "待成长"

UNLIT_FILL = "#c4bdb4"
INK = "#3a342c"

_WRITING_TEACHER_KEYS = ("teacher_band", "teacher_score", "writing_teacher")
_READING_LISTENING_KEYS = (
    "band_estimate",
    "band",
    "reference_band",
    "official_band",
    "score",
)
_IGNORE_KEYS = frozenset({
    "official_score",
    "writing_official",
    "writing_official_score",
    "speaking",
    "speaking_band",
    "speaking_score",
})

_CSS_PATH = Path(__file__).resolve().parent / "static" / "growth_stack.css"


def stage_count() -> int:
    """Number of totem stages (always 8)."""
    return len(STAGES)


def stage_ids() -> tuple[str, ...]:
    """Stable bottom-up stage ids, matching STAGES."""
    return STAGE_IDS


def _parse_half_band(value) -> float | None:
    """Return an IELTS half-band in 0–9, or None if missing or invalid.

    Non-half-bands such as 7.2 are ignored, matching the fireworks rule.
    Booleans are rejected so True is not read as 1.0.
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
    value = _parse_half_band(band)
    if value is None:
        return None
    return f"{value:.1f}"


def _first_band(data: dict, keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key in _IGNORE_KEYS:
            continue
        parsed = _parse_half_band(data.get(key))
        if parsed is not None:
            return parsed
    return None


def _bands_from(item) -> list[float]:
    """Collect usable module bands from a number, list, or dict."""
    found: list[float] = []
    if item is None or item == "":
        return found
    if isinstance(item, (list, tuple)):
        for part in item:
            found.extend(_bands_from(part))
        return found
    if not isinstance(item, dict):
        parsed = _parse_half_band(item)
        if parsed is not None:
            found.append(parsed)
        return found

    module = str(item.get("module") or item.get("kind") or "").strip().lower()
    if module == "speaking":
        return found
    if module == "writing":
        band = _first_band(item, _WRITING_TEACHER_KEYS)
        if band is not None:
            found.append(band)
        return found
    if module:
        band = _first_band(item, _READING_LISTENING_KEYS)
        if band is not None:
            found.append(band)
        return found

    for key in ("reading", "listening"):
        if key not in item:
            continue
        value = item[key]
        if isinstance(value, dict):
            found.extend(_bands_from({**value, "module": key}))
        else:
            parsed = _parse_half_band(value)
            if parsed is not None:
                found.append(parsed)

    if "writing" in item:
        value = item["writing"]
        if isinstance(value, dict):
            found.extend(_bands_from({**value, "module": "writing"}))
        else:
            parsed = _parse_half_band(value)
            if parsed is not None:
                found.append(parsed)

    for key in _WRITING_TEACHER_KEYS:
        if key == "writing" or key not in item:
            continue
        parsed = _parse_half_band(item.get(key))
        if parsed is not None:
            found.append(parsed)

    if not found:
        band = _first_band(item, _READING_LISTENING_KEYS)
        if band is not None:
            found.append(band)
    return found


def best_growth_band(scores=None) -> float | None:
    """Best usable band among reading, listening, and writing teacher scores.

    Accepts a single half-band, a list of half-bands or score dicts, or a
    dict of module bands. ``official_score`` and speaking values are never
    used. A bare ``writing`` number is treated as the teacher band. Returns
    None when nothing usable is present.
    """
    found = _bands_from(scores)
    return max(found) if found else None


def lit_stages(band) -> tuple[bool, ...]:
    """Inclusive bottom-up lighting flags for the eight stages.

    A band of 7.0 returns four True values then four False. Missing scores,
    non-half-bands, and values below 5.5 return eight False flags.
    """
    value = _parse_half_band(band)
    if value is None:
        return (False,) * len(STAGES)
    return tuple(stage <= value + 1e-9 for stage in STAGES)


def status_text(band) -> str:
    """Short status line for the widget header."""
    value = _parse_half_band(band)
    if value is None:
        return EMPTY_STATUS
    if value < STAGES[0]:
        return WAITING_STATUS
    return f"当前最高 {format_band(value)}"


def _c(lit: bool, color: str) -> str:
    return color if lit else UNLIT_FILL


def _svg(inner: str, *, lit: bool) -> str:
    cls = "growth-stack-svg is-lit" if lit else "growth-stack-svg is-unlit"
    return (
        f'<svg class="{cls}" viewBox="0 0 200 160" focusable="false" '
        f'aria-hidden="true" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'
    )


def _ink(lit: bool) -> str:
    return _c(lit, INK)


def _face(cx: float, cy: float, *, lit: bool, eye_dx: float = 13, dazed: bool = False,
          blush: str | None = None, mouth: str = "smile") -> str:
    """Shared simple face: two eyes, optional blush, a small mouth."""
    ink = _ink(lit)
    white = _c(lit, "#fffef8")
    parts: list[str] = []
    # Eyes: white + pupil. Dazed looks slightly unsynced.
    offsets = ((-eye_dx, -1 if dazed else 0), (eye_dx, 1 if dazed else 0))
    pupils = ((-1, -1 if not dazed else 1), (1, 0))
    for (ox, oy), (px, py) in zip(offsets, pupils):
        parts.append(
            f'<ellipse cx="{cx + ox}" cy="{cy + oy}" rx="7.2" ry="8.2" fill="{white}" stroke="{ink}" stroke-width="1.6"/>'
        )
        parts.append(
            f'<circle cx="{cx + ox + px}" cy="{cy + oy + py}" r="3.1" fill="{ink}"/>'
        )
        parts.append(
            f'<circle cx="{cx + ox + px + 1.2}" cy="{cy + oy + py - 1.4}" r="1.1" fill="{white}"/>'
        )
    if blush:
        b = _c(lit, blush)
        parts.append(f'<ellipse cx="{cx - 22}" cy="{cy + 10}" rx="6" ry="3.2" fill="{b}" opacity=".85"/>')
        parts.append(f'<ellipse cx="{cx + 22}" cy="{cy + 10}" rx="6" ry="3.2" fill="{b}" opacity=".85"/>')
    if mouth == "smile":
        parts.append(
            f'<path d="M{cx - 7} {cy + 12} Q{cx} {cy + 18} {cx + 7} {cy + 12}" '
            f'fill="none" stroke="{ink}" stroke-width="2" stroke-linecap="round"/>'
        )
    elif mouth == "open":
        tongue = _c(lit, "#e56a62")
        dark = _c(lit, "#8a3d32")
        parts.append(
            f'<ellipse cx="{cx}" cy="{cy + 16}" rx="10" ry="7.5" fill="{dark}" stroke="{ink}" stroke-width="1.6"/>'
        )
        parts.append(f'<ellipse cx="{cx}" cy="{cy + 19}" rx="6" ry="3.4" fill="{tongue}"/>')
    elif mouth == "dot":
        parts.append(f'<circle cx="{cx}" cy="{cy + 13}" r="2.1" fill="{ink}"/>')
    elif mouth == "wobble":
        parts.append(
            f'<path d="M{cx - 6} {cy + 13} Q{cx - 2} {cy + 16} {cx + 2} {cy + 13} Q{cx + 5} {cy + 11} {cx + 8} {cy + 14}" '
            f'fill="none" stroke="{ink}" stroke-width="2" stroke-linecap="round"/>'
        )
    return "".join(parts)


def _duck_svg(lit: bool) -> str:
    ink = _ink(lit)
    yellow = _c(lit, "#f3d04e")
    shade = _c(lit, "#e2b63c")
    bill = _c(lit, "#e89a3a")
    bill_d = _c(lit, "#d07e28")
    bang = _c(lit, "#d6554d")
    feet = _c(lit, "#3a342c")
    inner = (
        f'<ellipse cx="104" cy="148" rx="40" ry="7" fill="{_c(lit, "#e8d89a")}" opacity=".45"/>'
        # bang
        f'<rect x="28" y="28" width="6.5" height="22" rx="3" fill="{bang}"/>'
        f'<circle cx="31.2" cy="57" r="4" fill="{bang}"/>'
        # body and head
        f'<ellipse cx="108" cy="118" rx="46" ry="30" fill="{yellow}" stroke="{ink}" stroke-width="2.2"/>'
        f'<ellipse cx="108" cy="72" rx="40" ry="36" fill="{yellow}" stroke="{ink}" stroke-width="2.2"/>'
        f'<ellipse cx="92" cy="124" rx="16" ry="10" fill="{shade}" opacity=".55"/>'
        # wings
        f'<ellipse cx="64" cy="116" rx="12" ry="9" fill="{shade}" stroke="{ink}" stroke-width="1.8"/>'
        f'<ellipse cx="152" cy="116" rx="12" ry="9" fill="{shade}" stroke="{ink}" stroke-width="1.8"/>'
        # bill
        f'<ellipse cx="108" cy="88" rx="16" ry="8" fill="{bill}" stroke="{ink}" stroke-width="1.7"/>'
        f'<ellipse cx="108" cy="90" rx="10" ry="3.2" fill="{bill_d}"/>'
        # feet
        f'<ellipse cx="90" cy="146" rx="10" ry="5" fill="{feet}"/>'
        f'<ellipse cx="126" cy="146" rx="10" ry="5" fill="{feet}"/>'
        + _face(108, 66, lit=lit, eye_dx=12, dazed=True, mouth="wobble")
    )
    return _svg(inner, lit=lit)


def _turtle_svg(lit: bool) -> str:
    ink = _ink(lit)
    blue = _c(lit, "#7ec8ea")
    blue_d = _c(lit, "#5aa8cc")
    shell = _c(lit, "#d6c294")
    shell_d = _c(lit, "#b89f6e")
    cream = _c(lit, "#fff6de")
    inner = (
        f'<ellipse cx="100" cy="148" rx="42" ry="7" fill="{_c(lit, "#e8d89a")}" opacity=".45"/>'
        # shell first so head sits in front
        f'<ellipse cx="118" cy="112" rx="44" ry="34" fill="{shell}" stroke="{ink}" stroke-width="2.2"/>'
        f'<ellipse cx="118" cy="108" rx="28" ry="20" fill="{cream}" stroke="{shell_d}" stroke-width="2"/>'
        f'<path d="M96 108 Q118 92 140 108" fill="none" stroke="{shell_d}" stroke-width="1.8" stroke-linecap="round"/>'
        f'<path d="M100 118 Q118 108 136 118" fill="none" stroke="{shell_d}" stroke-width="1.8" stroke-linecap="round"/>'
        # head / body
        f'<ellipse cx="78" cy="96" rx="30" ry="28" fill="{blue}" stroke="{ink}" stroke-width="2.2"/>'
        f'<ellipse cx="78" cy="128" rx="22" ry="16" fill="{blue}" stroke="{ink}" stroke-width="2"/>'
        # flippers and tail
        f'<ellipse cx="60" cy="140" rx="11" ry="6" fill="{blue_d}" stroke="{ink}" stroke-width="1.6"/>'
        f'<ellipse cx="96" cy="140" rx="11" ry="6" fill="{blue_d}" stroke="{ink}" stroke-width="1.6"/>'
        f'<ellipse cx="158" cy="126" rx="10" ry="6" fill="{blue_d}" stroke="{ink}" stroke-width="1.6"/>'
        + _face(76, 90, lit=lit, eye_dx=11, mouth="smile")
    )
    return _svg(inner, lit=lit)


def _egg_svg(lit: bool) -> str:
    ink = _ink(lit)
    cream = _c(lit, "#fff4dc")
    rim = _c(lit, "#c9a56c")
    tuft = _c(lit, "#f3d04e")
    tuft_d = _c(lit, "#d7a83e")
    red = _c(lit, "#d6554d")
    blue = _c(lit, "#5298c6")
    zigzag = (
        "M48 96 L60 84 L74 98 L88 82 L102 98 L116 82 L130 98 L144 84 L152 96 "
        "L152 148 Q100 158 48 148 Z"
    )
    inner = (
        f'<ellipse cx="100" cy="150" rx="38" ry="6" fill="{_c(lit, "#e8d89a")}" opacity=".45"/>'
        # tufts
        f'<ellipse cx="84" cy="36" rx="7" ry="12" fill="{tuft}" stroke="{ink}" stroke-width="1.6"/>'
        f'<ellipse cx="100" cy="30" rx="7" ry="13" fill="{tuft_d}" stroke="{ink}" stroke-width="1.6"/>'
        f'<ellipse cx="116" cy="36" rx="7" ry="12" fill="{tuft}" stroke="{ink}" stroke-width="1.6"/>'
        # upper head
        f'<ellipse cx="100" cy="70" rx="46" ry="42" fill="{cream}" stroke="{ink}" stroke-width="2.2"/>'
        # lower shell with zigzag rim
        f'<path d="{zigzag}" fill="{cream}" stroke="{ink}" stroke-width="2.2" stroke-linejoin="round"/>'
        f'<path d="M48 96 L60 84 L74 98 L88 82 L102 98 L116 82 L130 98 L144 84 L152 96" '
        f'fill="none" stroke="{rim}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        # triangles
        f'<path d="M72 118 L84 142 L60 142 Z" fill="{red}" stroke="{ink}" stroke-width="1.4" stroke-linejoin="round"/>'
        f'<path d="M128 118 L140 142 L116 142 Z" fill="{blue}" stroke="{ink}" stroke-width="1.4" stroke-linejoin="round"/>'
        + _face(100, 72, lit=lit, eye_dx=14, mouth="dot")
    )
    return _svg(inner, lit=lit)


def _sprout_svg(lit: bool) -> str:
    ink = _ink(lit)
    mint = _c(lit, "#91d6be")
    mint_d = _c(lit, "#6fb89f")
    spot = _c(lit, "#62ab92")
    leaf = _c(lit, "#78c25e")
    leaf_d = _c(lit, "#51964c")
    inner = (
        f'<ellipse cx="96" cy="150" rx="40" ry="6" fill="{_c(lit, "#e8d89a")}" opacity=".45"/>'
        # leaf-bulb on the back
        f'<ellipse cx="148" cy="78" rx="22" ry="26" fill="{leaf}" stroke="{ink}" stroke-width="2"/>'
        f'<path d="M148 58 C160 50 170 68 148 90 C126 68 136 50 148 58 Z" fill="{leaf_d}"/>'
        f'<path d="M148 70 C158 66 162 86 148 100 C134 86 138 66 148 70 Z" fill="{leaf}"/>'
        # body
        f'<ellipse cx="92" cy="104" rx="48" ry="44" fill="{mint}" stroke="{ink}" stroke-width="2.2"/>'
        f'<ellipse cx="78" cy="118" rx="16" ry="10" fill="{mint_d}" opacity=".5"/>'
        # spots
        f'<ellipse cx="64" cy="120" rx="6" ry="5" fill="{spot}"/>'
        f'<ellipse cx="86" cy="132" rx="5" ry="4.2" fill="{spot}"/>'
        f'<ellipse cx="114" cy="124" rx="6.5" ry="5" fill="{spot}"/>'
        f'<ellipse cx="70" cy="98" rx="4" ry="3.4" fill="{spot}"/>'
        # feet
        f'<ellipse cx="72" cy="146" rx="11" ry="6" fill="{mint_d}" stroke="{ink}" stroke-width="1.6"/>'
        f'<ellipse cx="112" cy="146" rx="11" ry="6" fill="{mint_d}" stroke="{ink}" stroke-width="1.6"/>'
        + _face(88, 92, lit=lit, eye_dx=13, mouth="smile")
    )
    return _svg(inner, lit=lit)


def _pink_svg(lit: bool) -> str:
    ink = _ink(lit)
    pink = _c(lit, "#f2adb8")
    pink_d = _c(lit, "#d88a98")
    leaf = _c(lit, "#78c25e")
    leaf_d = _c(lit, "#51964c")
    inner = (
        f'<ellipse cx="100" cy="150" rx="36" ry="6" fill="{_c(lit, "#e8d89a")}" opacity=".45"/>'
        # ears
        f'<ellipse cx="68" cy="50" rx="12" ry="16" fill="{pink}" stroke="{ink}" stroke-width="2"/>'
        f'<ellipse cx="132" cy="50" rx="12" ry="16" fill="{pink}" stroke="{ink}" stroke-width="2"/>'
        f'<ellipse cx="68" cy="54" rx="5" ry="7" fill="{pink_d}"/>'
        f'<ellipse cx="132" cy="54" rx="5" ry="7" fill="{pink_d}"/>'
        # body
        f'<circle cx="100" cy="100" r="48" fill="{pink}" stroke="{ink}" stroke-width="2.2"/>'
        # leaf in mouth
        f'<path d="M112 114 C128 104 142 118 128 132 C118 122 116 120 112 114 Z" '
        f'fill="{leaf}" stroke="{ink}" stroke-width="1.6" stroke-linejoin="round"/>'
        f'<path d="M120 116 L128 128" fill="none" stroke="{leaf_d}" stroke-width="1.4" stroke-linecap="round"/>'
        # feet
        f'<ellipse cx="80" cy="146" rx="10" ry="5.5" fill="{pink_d}" stroke="{ink}" stroke-width="1.5"/>'
        f'<ellipse cx="120" cy="146" rx="10" ry="5.5" fill="{pink_d}" stroke="{ink}" stroke-width="1.5"/>'
        + _face(100, 94, lit=lit, eye_dx=14, blush="#f4c4cc", mouth="smile")
    )
    return _svg(inner, lit=lit)


def _lizard_svg(lit: bool) -> str:
    ink = _ink(lit)
    orange = _c(lit, "#e98b55")
    orange_d = _c(lit, "#d3663f")
    belly = _c(lit, "#f5c6a4")
    inner = (
        f'<ellipse cx="100" cy="150" rx="40" ry="6" fill="{_c(lit, "#e8d89a")}" opacity=".45"/>'
        # tail (rounded, not a flame)
        f'<path d="M148 112 Q178 100 182 128 Q160 124 148 120 Z" fill="{orange}" stroke="{ink}" stroke-width="2" stroke-linejoin="round"/>'
        # body
        f'<ellipse cx="100" cy="100" rx="50" ry="44" fill="{orange}" stroke="{ink}" stroke-width="2.2"/>'
        f'<ellipse cx="100" cy="116" rx="26" ry="22" fill="{belly}"/>'
        # arms and feet
        f'<ellipse cx="56" cy="118" rx="10" ry="7" fill="{orange_d}" stroke="{ink}" stroke-width="1.6"/>'
        f'<ellipse cx="144" cy="118" rx="10" ry="7" fill="{orange_d}" stroke="{ink}" stroke-width="1.6"/>'
        f'<ellipse cx="78" cy="144" rx="11" ry="6" fill="{orange_d}" stroke="{ink}" stroke-width="1.6"/>'
        f'<ellipse cx="122" cy="144" rx="11" ry="6" fill="{orange_d}" stroke="{ink}" stroke-width="1.6"/>'
        + _face(100, 86, lit=lit, eye_dx=14, mouth="open")
    )
    return _svg(inner, lit=lit)


def _fox_svg(lit: bool) -> str:
    ink = _ink(lit)
    fur = _c(lit, "#c49662")
    fur_d = _c(lit, "#9a6b3e")
    cream = _c(lit, "#fff6de")
    inner_ear = _c(lit, "#f5c6a4")
    inner = (
        f'<ellipse cx="100" cy="152" rx="40" ry="6" fill="{_c(lit, "#e8d89a")}" opacity=".45"/>'
        # sitting haunches / body first
        f'<ellipse cx="100" cy="126" rx="46" ry="28" fill="{fur}" stroke="{ink}" stroke-width="2.2"/>'
        # ears
        f'<path d="M62 68 L50 24 L86 60 Z" fill="{fur}" stroke="{ink}" stroke-width="2" stroke-linejoin="round"/>'
        f'<path d="M138 68 L150 24 L114 60 Z" fill="{fur}" stroke="{ink}" stroke-width="2" stroke-linejoin="round"/>'
        f'<path d="M64 60 L56 34 L78 58 Z" fill="{inner_ear}"/>'
        f'<path d="M136 60 L144 34 L122 58 Z" fill="{inner_ear}"/>'
        # head
        f'<ellipse cx="100" cy="78" rx="38" ry="32" fill="{fur}" stroke="{ink}" stroke-width="2.2"/>'
        # fluffy cream collar around the neck
        f'<circle cx="68" cy="108" r="13" fill="{cream}" stroke="{ink}" stroke-width="1.5"/>'
        f'<circle cx="86" cy="116" r="13" fill="{cream}" stroke="{ink}" stroke-width="1.5"/>'
        f'<circle cx="100" cy="112" r="14" fill="{cream}" stroke="{ink}" stroke-width="1.5"/>'
        f'<circle cx="114" cy="116" r="13" fill="{cream}" stroke="{ink}" stroke-width="1.5"/>'
        f'<circle cx="132" cy="108" r="13" fill="{cream}" stroke="{ink}" stroke-width="1.5"/>'
        # feet
        f'<ellipse cx="76" cy="148" rx="11" ry="6" fill="{fur_d}" stroke="{ink}" stroke-width="1.6"/>'
        f'<ellipse cx="124" cy="148" rx="11" ry="6" fill="{fur_d}" stroke="{ink}" stroke-width="1.6"/>'
        + _face(100, 76, lit=lit, eye_dx=13, blush="#e7a08a", mouth="smile")
    )
    return _svg(inner, lit=lit)


def _mouse_svg(lit: bool) -> str:
    ink = _ink(lit)
    yellow = _c(lit, "#f3d04e")
    shade = _c(lit, "#e2b63c")
    tip = _c(lit, "#8b5a2e")
    inner_ear = _c(lit, "#f5c6a4")
    cheek = _c(lit, "#d6554d")
    inner = (
        f'<ellipse cx="96" cy="150" rx="38" ry="6" fill="{_c(lit, "#e8d89a")}" opacity=".45"/>'
        # pointed tail (smooth taper, not a zigzag bolt)
        f'<path d="M150 118 C176 110 186 132 168 148 C180 128 164 116 150 120 Z" '
        f'fill="{yellow}" stroke="{ink}" stroke-width="2" stroke-linejoin="round"/>'
        # round ears with brown tips
        f'<circle cx="62" cy="52" r="20" fill="{yellow}" stroke="{ink}" stroke-width="2"/>'
        f'<circle cx="138" cy="52" r="20" fill="{yellow}" stroke="{ink}" stroke-width="2"/>'
        f'<circle cx="62" cy="48" r="11" fill="{tip}"/>'
        f'<circle cx="138" cy="48" r="11" fill="{tip}"/>'
        f'<circle cx="62" cy="52" r="7" fill="{inner_ear}"/>'
        f'<circle cx="138" cy="52" r="7" fill="{inner_ear}"/>'
        # body
        f'<ellipse cx="100" cy="102" rx="52" ry="46" fill="{yellow}" stroke="{ink}" stroke-width="2.2"/>'
        f'<ellipse cx="86" cy="118" rx="14" ry="9" fill="{shade}" opacity=".45"/>'
        # arms / feet
        f'<ellipse cx="58" cy="126" rx="9" ry="7" fill="{shade}" stroke="{ink}" stroke-width="1.6"/>'
        f'<ellipse cx="142" cy="126" rx="9" ry="7" fill="{shade}" stroke="{ink}" stroke-width="1.6"/>'
        f'<ellipse cx="80" cy="146" rx="11" ry="6" fill="{_c(lit, "#3a342c")}"/>'
        f'<ellipse cx="120" cy="146" rx="11" ry="6" fill="{_c(lit, "#3a342c")}"/>'
        # cheeks
        f'<ellipse cx="70" cy="108" rx="8" ry="5.5" fill="{cheek}" opacity=".9"/>'
        f'<ellipse cx="130" cy="108" rx="8" ry="5.5" fill="{cheek}" opacity=".9"/>'
        + _face(100, 92, lit=lit, eye_dx=14, mouth="smile")
    )
    return _svg(inner, lit=lit)


_STAGE_DRAW = {
    "duck": _duck_svg,
    "turtle": _turtle_svg,
    "egg": _egg_svg,
    "sprout": _sprout_svg,
    "pink": _pink_svg,
    "lizard": _lizard_svg,
    "fox": _fox_svg,
    "mouse": _mouse_svg,
}


def stage_svg(stage_id: str, *, lit: bool) -> str:
    """Return the inline SVG for one totem stage."""
    drawer = _STAGE_DRAW.get(stage_id)
    if drawer is None:
        raise ValueError(f"Unknown growth stage {stage_id!r}")
    return drawer(bool(lit))


def gallery(band=None, scores=None) -> dict:
    """Build the vertical totem for a records-page widget.

    If ``band`` is omitted, it is derived from ``scores`` via
    ``best_growth_band``. Stages in the returned list are top-down (9.0
    first) so they can be rendered as a stack.
    """
    if band is not None and band != "":
        resolved = _parse_half_band(band)
    else:
        resolved = best_growth_band(scores)
    flags = lit_stages(resolved)
    stages = []
    current_id = None
    for index in range(len(STAGES) - 1, -1, -1):
        stage_id = STAGE_IDS[index]
        is_lit = flags[index]
        if is_lit and current_id is None:
            current_id = stage_id
        stages.append({
            "id": stage_id,
            "band": STAGES[index],
            "band_label": format_band(STAGES[index]),
            "lit": is_lit,
            "current": False,
            "svg": stage_svg(stage_id, lit=is_lit),
        })
    for item in stages:
        item["current"] = bool(item["lit"] and item["id"] == current_id)
    lit_n = sum(1 for item in stages if item["lit"])
    label = format_band(resolved)
    return {
        "title": TITLE,
        "band": resolved,
        "band_label": label,
        "status": status_text(resolved),
        "empty": lit_n == 0,
        "lit": lit_n,
        "total": len(STAGES),
        "stages": stages,
    }


def _widget_css() -> str:
    try:
        return _CSS_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def render(band=None, scores=None) -> str:
    """Return a self-contained HTML widget for the vertical growth stack."""
    data = gallery(band=band, scores=scores)
    css = _widget_css()
    empty_cls = " is-empty" if data["empty"] else ""
    band_attr = ""
    if data["band_label"]:
        band_attr = f' data-band="{html.escape(data["band_label"], quote=True)}"'
    aria = f'{data["title"]}，{data["status"]}'
    parts = [
        f'<aside class="growth-stack{empty_cls}"{band_attr} '
        f'aria-label="{html.escape(aria, quote=True)}">',
    ]
    if css.strip():
        parts.append(f"<style>\n{css}\n</style>")
    parts.append(f'<h2 class="growth-stack-title">{html.escape(data["title"])}</h2>')
    parts.append(f'<p class="growth-stack-status">{html.escape(data["status"])}</p>')
    parts.append('<ol class="growth-stack-totem">')
    for fig in data["stages"]:
        lit_cls = "is-lit" if fig["lit"] else "is-unlit"
        current_cls = " is-current" if fig["current"] else ""
        lit_words = "已点亮" if fig["lit"] else "未点亮"
        band_label = fig["band_label"] or ""
        parts.append(
            f'<li class="growth-stack-stage {lit_cls}{current_cls}" '
            f'data-stage="{html.escape(fig["id"], quote=True)}" '
            f'data-band="{html.escape(band_label, quote=True)}" '
            f'aria-label="{html.escape(f"{band_label} {lit_words}", quote=True)}">'
        )
        parts.append('<div class="growth-stack-sprite" role="img" aria-hidden="true">')
        parts.append(fig["svg"])
        parts.append("</div>")
        parts.append(f'<span class="growth-stack-stage-band">{html.escape(band_label)}</span>')
        parts.append("</li>")
    parts.append("</ol>")
    parts.append("</aside>")
    return "\n".join(parts)


def _validate() -> None:
    if len(STAGES) != 8 or len(STAGE_IDS) != 8:
        raise RuntimeError("Growth stack must have exactly 8 stages")
    if STAGES != (5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0):
        raise RuntimeError("Growth stack stages must be 5.5 through 9.0")
    if set(_STAGE_DRAW) != set(STAGE_IDS):
        raise RuntimeError("Growth stack drawings must match stage ids")
    seen: set[str] = set()
    for name in STAGE_IDS:
        lit = stage_svg(name, lit=True)
        unlit = stage_svg(name, lit=False)
        if "<svg" not in lit or "<svg" not in unlit:
            raise RuntimeError(f"Growth stage {name!r} is missing an svg")
        if lit == unlit:
            raise RuntimeError(f"Growth stage {name!r} lit and unlit must differ")
        if UNLIT_FILL not in unlit:
            raise RuntimeError(f"Growth stage {name!r} unlit must use the grey silhouette")
        if name in seen:
            raise RuntimeError(f"Growth stage {name!r} is duplicated")
        seen.add(name)
    sample = render(7.0)
    if "<svg" not in sample or "成长进度" not in sample:
        raise RuntimeError("Growth widget render is incomplete")


_validate()
