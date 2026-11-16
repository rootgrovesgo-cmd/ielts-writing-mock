"""Original classroom fan-art pixel plant-sprout creatures used as a student-progress gallery.

Each pose is an original chibi drawing in a chunky 8-bit/16-bit grid, not a
copy of any official artwork. Letters in a sprite: T light teal body, S body
shadow, L leaf, G darker leaf and spots, K charcoal outline, W white
highlight. '.' is empty and is not part of the silhouette. Lit figures are
full colour; unlit figures are a gray silhouette. Official ball marks are
not used; original leaves, sparkles, dew, and spiral doodles are decorative
only.

The Rainie invite-code theme on the student records page may be referred to
in student-facing copy as 妙蛙种子, in the same classroom-fan-art tone as the
Pikachu gallery.
"""

from __future__ import annotations

COLOR_LETTERS = frozenset("TSLGKW")

# Invite code string that unlocks this gallery. Match the code text, not the
# typed display name. Comparison is case-insensitive.
RAINIE_INVITE_CODE = "rainie"

# Oldest completed set is assigned the first pose; later sets walk this order
# and wrap when the student has more attempts than poses.
POSES: dict[str, tuple[str, ...]] = {
    "sit": (
        "......LLLLLL......",
        ".....LLGLLGLL.....",
        "....LLGLLLLGLL....",
        ".....LLLLLLLL.....",
        "....KTKKKKKKTK....",
        "...KTTTTTTTTTTK...",
        "..KTWTTTTTTTTWTK..",
        "..KTKKTTTTTTKKTK..",
        "...KTTTTWWTTTTK...",
        "...KKKTTTTTTKKK...",
        "..KT.KTTTTTTK.TK..",
        "..KTTKSSSSSSKTTK..",
        "...KK.K....K.KK...",
        "....KK......KK....",
    ),
    "sleep": (
        "...........LLLLLL.....",
        ".........LLGLLLLLL....",
        ".......KKLLLLLLLLLL...",
        "......KTTTKLLLLLLL....",
        ".....KTKKTTTKLLLL.....",
        ".....KTTTTWWTTK.......",
        "....KKTTTTTTTTKK......",
        "...KT.KSSSSSSKTK......",
        "...KTT.KK..KK.K.......",
        "....KK......KK........",
    ),
    "lookback": (
        "......LLLLLLLL......",
        ".....LLGLLLLGLL.....",
        "....LLGLLLLLLGLL....",
        ".....LLLLLLLLLL.....",
        "...KKKLLLLLLL.......",
        "..KTTTKLLL..........",
        "..KTWKTTK...........",
        "..KTTTTTTK..........",
        "...KTTWWTTK.........",
        "..KK.KTTTTKK........",
        ".KT..KTTTT.TK.......",
        ".KTT.KSSSS.TTK......",
        "..KK..K..K..KK......",
        "...KK......KK.......",
    ),
    "stand": (
        ".....LLLLLL.....",
        "....LLGLLGLL....",
        "...LLGLLLLGLL...",
        "....LLLLLLLL....",
        "....KTKKKKTK....",
        "...KTTTTTTTTK...",
        "..KTWTTTTTTWTK..",
        "..KTKKTTTTKKTK..",
        "...KTTTTWWTTTK..",
        "...KKKTTTTKKK...",
        "...KT.KSSK.TK...",
        "...KTTK..KTTK...",
        "....KK....KK....",
    ),
    "walk_left": (
        ".........LLLLLL.....",
        "........LLGLLGLL....",
        ".......LLLLLLLLL....",
        "....KKKK.LLLLLL.....",
        "...KTTTTKLLLLL......",
        "..KT.WKTTK..........",
        "..KTTTTTTK..........",
        "..KKTTTWWKK.........",
        ".KT.KTTTT.K.........",
        ".KTTKSSK.KK.........",
        "..KK..K.KK..........",
        "......KK..KK........",
        ".......K...K........",
    ),
    "walk_right": (
        ".....LLLLLL.........",
        "....LLGLLGLL........",
        "....LLLLLLLLL.......",
        ".....LLLLLL.KKKK....",
        "......LLLLLKTTTTK...",
        "..........KTTKW.TK..",
        "..........KTTTTTTK..",
        ".........KKWWTTTKK..",
        ".........K.TTTTK.TK.",
        ".........KK.KSSKTTK.",
        "..........KK.K..KK..",
        "........KK..KK......",
        "........K...K.......",
    ),
    "reach": (
        "......LLLLLL......",
        ".....LLGLLGLL.....",
        "....LLLLLLLLLL....",
        "K....KKKKKKKK.....",
        "KK..KTTTTTTTTK....",
        ".TKKTWTTTTTTWTK...",
        ".KTKTKKTTTTKKTK...",
        "..K.KTTTTWWTTTK...",
        "....KKKTTTTKKK....",
        "...KT.KTTTT.TK....",
        "...KTTKSSSSKTTK...",
        "....KK.K..K.KK....",
        ".....KK....KK.....",
    ),
    "tumble": (
        ".....KK....KK.....",
        "....KTTK..KTTK....",
        "....KTTK.KK.TTK...",
        ".....KTTKTTKTTK...",
        "......KTTTTTTK....",
        ".....KSKTTTTKSK...",
        "....LLLLTTTTLLLL..",
        "...LLGLLLLLLLGLLL.",
        "....LLLLLLLLLLLL..",
        ".....KTTTTTTTTK...",
        ".....KTKKTTKKTK...",
        "......KTWTTWTTK...",
        ".......KTTTTTK....",
        "........KKKKK.....",
    ),
    "lie": (
        ".........LLLLLLLL.......",
        "........LLGLLLLGLL......",
        "...KKKKKLLLLLLLLLLL.....",
        "..KTTTTTKLLLLLLLLL......",
        ".KT.WKTTTK.LLLLL........",
        ".KTTTTWWTTK.............",
        ".KSSSSTTTTTKK..KK.......",
        "..KK.KK...K.KTTK........",
        "...........KK.KK........",
    ),
    "rear": (
        ".....LLLLLLLL.....",
        "....LLGLLLLGLL....",
        "...LLGLLLLLLGLL...",
        "...LLLLLLLLLLLL...",
        "....GLLLLLLLLG....",
        ".....LLLLLLLL.....",
        "......KTTTTK......",
        ".....KTSSSSTK.....",
        "....KSSKSSKSSK....",
        "....KK.K..K.KK....",
        ".....KK....KK.....",
        "......K....K......",
    ),
    "seed": (
        ".....LL.....",
        "....LGLL....",
        "...LLGLLL...",
        "....KKKK....",
        "...KTTTTK...",
        "..KTWTTWTK..",
        "..KTKTTKTK..",
        "...KTTWTTK..",
        "...KTTTTTK..",
        "....KKKKK...",
    ),
    "peek": (
        "LLLLL...........",
        "LLGLLLL.........",
        "LLLLLLLL........",
        ".KKKKKKL........",
        "KTTTTTTK........",
        "KTWTTTTK........",
        "KTKKTTTK........",
        ".KTTWWTKK.......",
        "KK.KKK.TK.......",
        ".KTTK..K........",
    ),
    "shy": (
        "......LLLLLL......",
        ".....LLGLLGLL.....",
        "....LLLLLLLLLL....",
        ".....KKKKKKKK.....",
        "....KTTTTTTTTK....",
        "...KTT.TTTT.TTK...",
        "...KT.KKTTKK.TK...",
        "....KTT.WW.TTK....",
        ".....KKTTTTKK.....",
        "......KSSSSK......",
        "......KK..KK......",
        "......KK..KK......",
    ),
    "happy": (
        "......LLLLLL......",
        ".....LLGLLGLL.....",
        "....LLGLLLLGLL....",
        ".....LLLLLLLL.....",
        "....KTKKKKKKTK....",
        "...KTTTTTTTTTTK...",
        "..KT.KKTTTTKK.TK..",
        "..KTT..TTTT..TTK..",
        "...KTTTWWWWTTTK...",
        "...KKKTTTTTTKKK...",
        "..KT.KTTTTTTK.TK..",
        "..KTTKSSSSSSKTTK..",
        "...KK.K....K.KK...",
        "....KK......KK....",
    ),
    "stretch": (
        "...........LLLLLLLL.......",
        "..........LLGLLLLGLL......",
        ".........LLLLLLLLLLLL.....",
        "...KKKKKKLLLLLLLLLL.......",
        "..KTTTTTTKLLLLLLLL........",
        ".KT.WKTTTTKLLLLL..........",
        "KTTTTTTWWTTK..............",
        ".KSSSSSSTTTTKKK.KK........",
        "KK..........KKTTK.........",
        "K............KK...........",
    ),
    "curl": (
        "......LLLLL.....",
        ".....LLGLLLLL...",
        "....LLLLLLLLL...",
        "...KKLLLLLLLL...",
        "..KTTTKLLLLLL...",
        ".KTKKTTTK.LLL...",
        ".KTTTTWWTK......",
        ".KSSSTTTTTK.....",
        "..KK.KK.KKK.....",
        "...KK...........",
    ),
}

DECOS: dict[str, tuple[str, ...]] = {
    "leaf": (
        "..G..",
        ".GLG.",
        "GLLLG",
        ".GLLG",
        "..GL.",
        "...G.",
    ),
    "sparkle": (
        "...W...",
        "...L...",
        "W..L..W",
        ".WLLLW.",
        "W..L..W",
        "...L...",
        "...W...",
    ),
    "spiral": (
        "..KKK.",
        ".K...K",
        "K...K.",
        "K.KK..",
        "K.....",
        ".K..K.",
        "..KK..",
    ),
    "dew": (
        "..W.",
        ".WTW",
        ".STW",
        "..S.",
    ),
}

# Visual rhythm for a mint sticker-sheet collage: mixed sizes, light tilts,
# and a small overlapping pile toward the later figures.
_SIZE_CYCLE = ("md", "sm", "lg", "sm", "md", "xs", "lg", "md", "sm", "md", "sm", "xs", "md", "lg", "sm", "md")
_NUDGE_CYCLE = (0, 8, -5, 6, -3, 4, -7, 2, 5, -4, 7, -2, 3, -6, 1, 4)
_TILT_CYCLE = (0, -7, 5, -3, 8, -5, 2, -8, 4, 6, -4, 3, -6, 7, -2, 5)
_NUDGE_X_CYCLE = (0, -6, 5, -3, 7, 2, -8, 4, -2, 6, -5, 3, -4, 8, 1, -7)
_DECO_LAYOUT = (
    {"kind": "spiral", "slot": "nw"},
    {"kind": "sparkle", "slot": "n"},
    {"kind": "leaf", "slot": "ne"},
    {"kind": "dew", "slot": "e"},
    {"kind": "leaf", "slot": "w"},
    {"kind": "sparkle", "slot": "sw"},
    {"kind": "spiral", "slot": "se"},
    {"kind": "dew", "slot": "s"},
)


def is_rainie_code(code: str | None) -> bool:
    """True when the invite *code string* is Rainie, in any casing."""
    return (code or "").strip().casefold() == RAINIE_INVITE_CODE


def pose_ids() -> tuple[str, ...]:
    """Stable pose order used when lighting figures oldest-first."""
    return tuple(POSES)


def pose_count() -> int:
    """Number of distinct poses in the gallery."""
    return len(POSES)


def sprite_cells(sprite: tuple[str, ...] | list[str], *, lit: bool) -> dict:
    """Rasterise one ASCII sprite into template cells."""
    rows = tuple(sprite)
    if not rows:
        raise ValueError("Sprite must have at least one row")
    cols = len(rows[0])
    cells: list[dict] = []
    for row, line in enumerate(rows):
        if len(line) != cols:
            raise ValueError(f"Sprite row {row} is {len(line)} wide, expected {cols}")
        for color in line:
            if color == ".":
                cells.append({"empty": True, "lit": False, "color": ""})
                continue
            if color not in COLOR_LETTERS:
                raise ValueError(f"Unknown sprite color {color!r}")
            cells.append({"empty": False, "lit": bool(lit), "color": color})
    return {
        "cols": cols,
        "rows": len(rows),
        "cells": cells,
    }


def gallery(attempts: list[dict] | None = None) -> dict:
    """Build the records-page mint collage.

    ``attempts`` must already be in oldest-first order. Each item may
    include ``caption`` (shown under a lit figure) and ``id``.
    The gallery always shows every distinct pose as a silhouette, then
    grows and reuses poses when there are more completed sets than poses.
    """
    items = list(attempts or [])
    ids = pose_ids()
    n_poses = len(ids)
    lit_n = len(items)
    total = max(n_poses, lit_n)
    figures: list[dict] = []
    for index in range(total):
        pose = ids[index % n_poses]
        is_lit = index < lit_n
        item = items[index] if is_lit else {}
        raster = sprite_cells(POSES[pose], lit=is_lit)
        figures.append({
            "pose": pose,
            "lit": is_lit,
            "caption": (item.get("caption") or "") if is_lit else "",
            "attempt_id": item.get("id") if is_lit else None,
            "size": _SIZE_CYCLE[index % len(_SIZE_CYCLE)],
            "cluster": _is_cluster(index, total, n_poses),
            "nudge": _NUDGE_CYCLE[index % len(_NUDGE_CYCLE)],
            "nudge_x": _NUDGE_X_CYCLE[index % len(_NUDGE_X_CYCLE)],
            "tilt": _TILT_CYCLE[index % len(_TILT_CYCLE)],
            **raster,
        })
    decos = []
    for deco in _DECO_LAYOUT:
        raster = sprite_cells(DECOS[deco["kind"]], lit=True)
        decos.append({
            "kind": deco["kind"],
            "slot": deco["slot"],
            **raster,
        })
    return {
        "theme": "sprout",
        "figures": figures,
        "decos": decos,
        "lit": lit_n,
        "total": total,
        "poses": n_poses,
        "complete": lit_n >= n_poses,
    }


def _is_cluster(index: int, total: int, n_poses: int) -> bool:
    if total < 6:
        return False
    pile_start = max(n_poses - 4, total - 4)
    return index >= pile_start


def _validate() -> None:
    if not 14 <= len(POSES) <= 18:
        raise RuntimeError(f"Expected 14–18 sprout poses, found {len(POSES)}")
    seen: set[tuple[str, ...]] = set()
    for name, rows in POSES.items():
        widths = {len(line) for line in rows}
        if len(widths) != 1:
            raise RuntimeError(f"Sprout pose {name!r} rows must all be the same width")
        if not rows or not rows[0]:
            raise RuntimeError(f"Sprout pose {name!r} is empty")
        letters = {ch for line in rows for ch in line if ch != "."}
        bad = letters - COLOR_LETTERS
        if bad:
            raise RuntimeError(f"Sprout pose {name!r} has invalid colors {bad}")
        if "T" not in letters or "K" not in letters or "L" not in letters:
            raise RuntimeError(f"Sprout pose {name!r} is missing core colors")
        key = tuple(rows)
        if key in seen:
            raise RuntimeError(f"Sprout pose {name!r} is a duplicate of another pose")
        seen.add(key)
        sprite_cells(rows, lit=True)
    for name, rows in DECOS.items():
        widths = {len(line) for line in rows}
        if len(widths) != 1:
            raise RuntimeError(f"Sprout deco {name!r} rows must all be the same width")
        letters = {ch for line in rows for ch in line if ch != "."}
        bad = letters - COLOR_LETTERS
        if bad:
            raise RuntimeError(f"Sprout deco {name!r} has invalid colors {bad}")
        # Decorative marks must not resemble official red-and-white balls.
        if name in {"ball", "pokeball"}:
            raise RuntimeError("Sprout decorations must not include official-looking balls")
        sprite_cells(rows, lit=True)


_validate()
