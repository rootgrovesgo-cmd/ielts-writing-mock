"""Original classroom fan-art pixel Pikachus used as a student-progress gallery.

Each pose is an original chibi drawing in a chunky 8-bit/16-bit grid, not a
copy of any official Pokémon artwork. Letters in a sprite: Y yellow, D gold
shadow, R red, K charcoal, B brown, W white highlight. '.' is empty and is
not part of the silhouette. Lit figures are full colour; unlit figures are
a gray silhouette. Official Poké Ball marks are not used; original hearts
and sparkles are decorative only.
"""

from __future__ import annotations

COLOR_LETTERS = frozenset("YDRKBW")

# Oldest completed set is assigned the first pose; later sets walk this order
# and wrap when the student has more attempts than poses.
POSES: dict[str, tuple[str, ...]] = {
    "stand": (
        "....KK........KK..",
        "...KYYK......KYYK.",
        "...KYYY......YYYK.",
        "....YYYY....YYYY..",
        "....YYYYYYYYYYYY..",
        "....YYWKYYYYWKYY..",
        "....RRKKYYYYKKRR..",
        "....RRRYYYYYYRRR..",
        "....YRRYYYKYYYRR..",
        "....DYYYYYYYYYYD..",
        "...YYYYYYYYYYYY...",
        "..YYYYYYYYYYYYYBY.",
        "..YYDYYYYYYYYDYYY.",
        "...DYYYYYYYYYD..YY",
        "...DDYYYYYYYYD...Y",
        "....YY......YY.YYY",
        "....KK......KK...Y",
        "....KK......KK..YY",
    ),
    "cheer": (
        "YY..................YY",
        "YYK................KYY",
        ".YY....KK......KK..YY.",
        ".YY...KYYK....KYYK.YY.",
        "..Y...KYYY....YYYK.Y..",
        "Y.....YYWKYYYYWKYY...Y",
        "Y.....RRKKYYYYKKRR...Y",
        ".Y....RRRYYYYYYRRR..Y.",
        ".Y....YRRYYYKYYYRR..Y.",
        "..Y...DYYYYYYYYYYD.Y..",
        "..Y..YYYYYYYYYYYYYYY..",
        "...YYYYYYYYYYYYYYYYY..",
        "....YYYYYYYYYYYYYYYBY.",
        "....YYDYYYYYYYYDYYYYY.",
        ".....DYYYYYYYYYD...YY.",
        ".....YY.......YY....Y.",
        ".....KK.......KK...YY.",
        ".....KK.......KK..YY..",
    ),
    "wink": (
        ".....KK......KK...",
        "....KYYK....KYYK..",
        "....KYYY....YYYK..",
        ".....YYYYYYYYYY...",
        ".....YKKYYYYWKYY..",
        ".....RRKYYYYKKRR..",
        ".....RRRYYYYYRRR..",
        ".....YRRYYKKYYRR..",
        ".....DYYYYYYYYYD..",
        "....YYYYYYYYYYYY..",
        "...YYYYYYYYYYYYBY.",
        "...YYDYYYYYYYDYYY.",
        "....DYYYYYYYYD..YY",
        "....DDYYYYYYYD...Y",
        ".....YY.....YY.YYY",
        ".....KK.....KK...Y",
        ".....KK.....KK..YY",
    ),
    "laugh": (
        "....KK........KK..",
        "...KYYK......KYYK.",
        "...KYYY......YYYK.",
        "....YYYYYYYYYYYY..",
        "....YYKYYYYYYKYY..",
        "....RKYKYYYYKYKR..",
        "....RRRYYYYYYRRR..",
        "....YRRKKKKKKRRY..",
        "....DYYYYYYYYYYD..",
        "...YYYYYYYYYYYY...",
        "..YYYYYYYYYYYYYBY.",
        "..YYDYYYYYYYYDYYY.",
        "...DYYYYYYYYYD..YY",
        "...DDYYYYYYYYD...Y",
        "....YY......YY.YYY",
        "....KK......KK...Y",
        "....KK......KK..YY",
    ),
    "peek": (
        "KYYK..............",
        "KYYY..............",
        "YYYYK.............",
        "YYWKYY............",
        "RRKKYYY...........",
        "RRRYYYY...........",
        "YRRYYKYY..........",
        "DYYYYYYY..........",
        "YYYYYYYY..........",
        "YDYYYYY...........",
        "YYYYYY............",
        "YY................",
        "KK................",
        "KK................",
    ),
    "sit": (
        "......KK......KK....",
        ".....KYYK....KYYK...",
        ".....KYYY....YYYK...",
        "......YYYYYYYYYY....",
        "......YYWKYYWKYY....",
        "......RRKKYYKKRR....",
        "......RRRYYYYYRR....",
        "......YRRYYKYYRR....",
        ".....DYYYYYYYYYYD...",
        "....YYYYYYYYYYYYYY..",
        "...YYYDYYYYYYYYDYYBY",
        "...YYYYYYYYYYYYYD.YY",
        "....DYYYYYYYYYYYY.Y.",
        "....KKYYYYYYYYKK.YY.",
        "....KK........KK.Y..",
        ".................YY.",
    ),
    "jump": (
        ".....KK........KK...",
        "....KYYK......KYYK..",
        "KK..KYYY......YYYK.K",
        "YYK.YYYYYYYYYYYYYYKY",
        ".YYYYYWKYYYYWKYYYYY.",
        "..YYYRRKKYYYYKKRRY..",
        "...YYRRRYYYYYRRRYY..",
        "....YYRRYYKYYYRR....",
        "....DYYYYYYYYYYD..Y.",
        "...YYYYYYYYYYYYYYBYY",
        "...YYDYYYYYYYYDYY.Y.",
        "....DYYYYYYYYYD...Y.",
        "....YY.......YY..YY.",
        "....KK.......KK.....",
        "....KK.......KK.....",
        "....................",
        "....................",
        "....................",
    ),
    "hold": (
        "....KK........KK..",
        "...KYYK......KYYK.",
        "...KYYY......YYYK.",
        "....YYYYYYYYYYYY..",
        "....YYWKYYYYWKYY..",
        "....RRKKYYYYKKRR..",
        "....RRRYYYYYYRRR..",
        "....YRRYYYKYYYRR..",
        "....DYYYYYYYYYYD..",
        "...YYYYKKKKKKYYY..",
        "..YYYKKWWWWWWKYYBY",
        "..YYDKWWRWRWWKDYYY",
        "...DYKWWRRRWWKD..Y",
        "...DDKKKKKKKKKD..Y",
        "....YY......YY.YYY",
        "....KK......KK...Y",
        "....KK......KK..YY",
    ),
    "look_left": (
        "..KK......KK......",
        ".KYYK....KYYK.....",
        ".KYYY....YYYY.....",
        "..YYYYYYYYYYY.....",
        "..YWKYYYKYYYY.....",
        "..RKKYYYRRYYYY....",
        "..RRRYYYYRRYYY....",
        "..YRRYKYYYYYYD....",
        "..DYYYYYYYYYYY....",
        ".YYYYYYYYYYYYY....",
        "YYYYYYYYYYYYYYB...",
        "YYDYYYYYYYYDYYY...",
        ".DYYYYYYYYYD..YY..",
        ".DDYYYYYYYYD...Y..",
        "..KK.....KK...YY..",
        "..KK.....KK..YY...",
    ),
    "look_right": (
        "......KK......KK..",
        ".....KYYK....KYYK.",
        ".....YYYY....YYYK.",
        ".....YYYYYYYYYYY..",
        ".....YYYYKYYYWKY..",
        "....YYYYRRYYYKKR..",
        "....YYYRRYYYYRRR..",
        "....DYYYYYYKYRRY..",
        "....YYYYYYYYYYYD..",
        "....YYYYYYYYYYYY..",
        "...BYYYYYYYYYYYYY.",
        "...YYYDYYYYYYYYDYY",
        "..YY..DYYYYYYYYD..",
        "..Y...DYYYYYYYYDD.",
        "..YY...KK.....KK..",
        "...YY..KK.....KK..",
    ),
    "wave": (
        "...........KK..KK.....",
        "..........KYYKYYYK....",
        "....KK....KYYYYYYYKK..",
        "...KYYK....YYYYYYYYYK.",
        "...KYYY....YYYYYYYYYY.",
        "....YYYYYYYYYWKYYYYY..",
        "....YYYYYYYYYKKRRYYY..",
        "....YYWKYYYYYYYRRRYY..",
        "....RRKKYYYYKYYYRR....",
        "....RRRYYYYYYYYYYD....",
        "....YRRYYYYYYYYYYY....",
        "....DYYYYYYYYYYYYBY...",
        "...YYYYYYYYYYYYDYYY...",
        "...YYDYYYYYYYYYD..YY..",
        "....DYYYYYYYYYYD...Y..",
        "....YY.......YY...YY..",
        "....KK.......KK....Y..",
        "....KK.......KK...YY..",
    ),
    "shy": (
        ".....KK......KK...",
        "....KYYK....KYYK..",
        "....KYYY....YYYK..",
        ".....YYYYYYYYYY...",
        ".....YYYKYYKYYY...",
        "...RRYRRYYYYRRRRR.",
        "..YYYRRRYYYYRRRYYY",
        "..YYYYRRYKKYRRYYYY",
        "...YDYYYYYYYYYYD..",
        "....YYYYYYYYYYYY..",
        "....YYYYYYYYYYYBY.",
        "....YDYYYYYYYDYYY.",
        ".....DYYYYYYYD..YY",
        ".....DYYYYYYYD...Y",
        ".....YY.....YY.YYY",
        ".....KK.....KK...Y",
        ".....KK.....KK..YY",
    ),
    "walk": (
        "........KK........",
        ".......KYYK.......",
        ".......KYYY.......",
        "......YYYYYY......",
        "......YYWKYY......",
        "......YRRKKY......",
        "Y....YYYYYKY......",
        "YY...DYYYYYY......",
        "YYY.YYYYYYYY......",
        "Y..BYYYYYYYY......",
        "...YYDYYYYYY......",
        "....YYYYYYYY......",
        ".....YY...YY......",
        ".....KK...KK......",
        "..........KK......",
    ),
    "sleep": (
        "................KK......",
        "...............KYYK.....",
        "..............KYYYY.....",
        "....YYYYYYYYYYYYYYY.....",
        "...YYYYYYYYYYYYKKYY.....",
        "..DYYYYYYYYYYYYRRKYY....",
        "..YYYYYYYYYYYYYRRRYY....",
        "...DYYYYYYYYYYYYKYYYBY..",
        "....YYYYYYYYYYYYYYYYYYY.",
        "....KK.........KK...YY..",
        "....KK..............Y...",
    ),
}

DECOS: dict[str, tuple[str, ...]] = {
    "heart": (
        ".RR.RR.",
        "RRRRRRR",
        "RRRRRRR",
        ".RRRRR.",
        "..RRR..",
        "...R...",
    ),
    "sparkle": (
        "...Y...",
        "...Y...",
        "Y..Y..Y",
        ".YYYYY.",
        "Y..Y..Y",
        "...Y...",
        "...Y...",
    ),
    "ball": (
        "..DDD..",
        ".DYYYD.",
        "DYYYYYD",
        "DYYWYYD",
        "DYYYYYD",
        ".DYYYD.",
        "..DDD..",
    ),
}

# Visual rhythm for the collage: mixed sizes, with a small overlapping pile
# toward the later figures (bottom-right in a wrapping flex layout).
_SIZE_CYCLE = ("md", "sm", "lg", "sm", "md", "xs", "lg", "md", "sm", "md", "sm", "xs", "md", "lg")
_NUDGE_CYCLE = (0, 6, -4, 8, 2, -8, 4, 0, -6, 5, 3, -3, 7, -5)
_DECO_LAYOUT = (
    {"kind": "heart", "slot": "nw"},
    {"kind": "heart", "slot": "ne"},
    {"kind": "sparkle", "slot": "n"},
    {"kind": "sparkle", "slot": "e"},
    {"kind": "ball", "slot": "sw"},
    {"kind": "ball", "slot": "se"},
)


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
    """Build the records-page collage.

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
    if not 12 <= len(POSES) <= 16:
        raise RuntimeError(f"Expected 12–16 Pikachu poses, found {len(POSES)}")
    seen: set[tuple[str, ...]] = set()
    for name, rows in POSES.items():
        widths = {len(line) for line in rows}
        if len(widths) != 1:
            raise RuntimeError(f"Pikachu pose {name!r} rows must all be the same width")
        if not rows or not rows[0]:
            raise RuntimeError(f"Pikachu pose {name!r} is empty")
        letters = {ch for line in rows for ch in line if ch != "."}
        bad = letters - COLOR_LETTERS
        if bad:
            raise RuntimeError(f"Pikachu pose {name!r} has invalid colors {bad}")
        if "Y" not in letters or "K" not in letters or "R" not in letters:
            raise RuntimeError(f"Pikachu pose {name!r} is missing core colors")
        key = tuple(rows)
        if key in seen:
            raise RuntimeError(f"Pikachu pose {name!r} is a duplicate of another pose")
        seen.add(key)
        sprite_cells(rows, lit=True)
    for name, rows in DECOS.items():
        widths = {len(line) for line in rows}
        if len(widths) != 1:
            raise RuntimeError(f"Pikachu deco {name!r} rows must all be the same width")
        letters = {ch for line in rows for ch in line if ch != "."}
        bad = letters - COLOR_LETTERS
        if bad:
            raise RuntimeError(f"Pikachu deco {name!r} has invalid colors {bad}")
        sprite_cells(rows, lit=True)


_validate()
