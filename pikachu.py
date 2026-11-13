"""Original classroom fan-art pixel Pikachu used as a student-progress widget.

The sprite is an original 18×18 chibi drawing, not a copy of any official
Pokémon artwork. Each unlockable block is a cluster of neighboring pixels.
Lighting order: feet and lower body, then belly, cheeks, face, ears, and
finally the lightning tail.
"""

from __future__ import annotations

# Color letters in SPRITE: Y yellow, D gold shadow, R red, K charcoal,
# B brown, W white highlight. '.' is empty and is not part of the silhouette.
SPRITE: tuple[str, ...] = (
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
)

# Lighting order is the list order. Each block is a cluster of (row, col) cells.
BLOCKS: tuple[tuple[tuple[int, int], ...], ...] = (
    (  # 0 left foot
        (16, 4), (16, 5), (17, 4), (17, 5),
    ),
    (  # 1 right foot
        (16, 12), (16, 13), (17, 12), (17, 13),
    ),
    (  # 2 left lower body
        (15, 4), (15, 5),
        (14, 3), (14, 4), (14, 5),
        (13, 3), (13, 4),
    ),
    (  # 3 right lower body
        (15, 12), (15, 13),
        (14, 12), (14, 13),
        (13, 12), (13, 13),
    ),
    (  # 4 lower belly
        (14, 6), (14, 7), (14, 8), (14, 9), (14, 10), (14, 11),
        (13, 5), (13, 6), (13, 7), (13, 8), (13, 9), (13, 10), (13, 11),
    ),
    (  # 5 mid belly
        (12, 5), (12, 6), (12, 7), (12, 8), (12, 9), (12, 10), (12, 11), (12, 12), (12, 13),
    ),
    (  # 6 chest
        (11, 4), (11, 5), (11, 6), (11, 7), (11, 8), (11, 9), (11, 10), (11, 11), (11, 12), (11, 13), (11, 14),
    ),
    (  # 7 upper chest
        (10, 3), (10, 4), (10, 5), (10, 6), (10, 7), (10, 8), (10, 9), (10, 10), (10, 11), (10, 12), (10, 13), (10, 14),
    ),
    (  # 8 left arm
        (11, 2), (11, 3),
        (12, 2), (12, 3), (12, 4),
    ),
    (  # 9 jaw
        (9, 4), (9, 5), (9, 6), (9, 7), (9, 8), (9, 9), (9, 10), (9, 11), (9, 12), (9, 13), (9, 14), (9, 15),
    ),
    (  # 10 left cheek
        (6, 4), (6, 5),
        (7, 4), (7, 5), (7, 6),
        (8, 5), (8, 6),
    ),
    (  # 11 right cheek
        (6, 14), (6, 15),
        (7, 13), (7, 14), (7, 15),
        (8, 14), (8, 15),
    ),
    (  # 12 mouth / lower face
        (8, 4), (8, 7), (8, 8), (8, 9), (8, 10), (8, 11), (8, 12), (8, 13),
    ),
    (  # 13 left eye
        (5, 6), (5, 7),
        (6, 6), (6, 7),
    ),
    (  # 14 right eye
        (5, 12), (5, 13),
        (6, 12), (6, 13),
    ),
    (  # 15 forehead / mid-face
        (4, 4), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10), (4, 11), (4, 12), (4, 13), (4, 14), (4, 15),
        (5, 4), (5, 5), (5, 8), (5, 9), (5, 10), (5, 11), (5, 14), (5, 15),
        (6, 8), (6, 9), (6, 10), (6, 11),
        (7, 7), (7, 8), (7, 9), (7, 10), (7, 11), (7, 12),
    ),
    (  # 16 left ear
        (0, 4), (0, 5),
        (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 3), (2, 4), (2, 5), (2, 6),
        (3, 4), (3, 5), (3, 6), (3, 7),
    ),
    (  # 17 right ear
        (0, 14), (0, 15),
        (1, 13), (1, 14), (1, 15), (1, 16),
        (2, 13), (2, 14), (2, 15), (2, 16),
        (3, 12), (3, 13), (3, 14), (3, 15),
    ),
    (  # 18 tail base
        (11, 15), (11, 16),
        (12, 14), (12, 15), (12, 16),
    ),
    (  # 19 lightning tail tip (last reward)
        (13, 16), (13, 17),
        (14, 17),
        (15, 15), (15, 16), (15, 17),
        (16, 17),
        (17, 16), (17, 17),
    ),
)

_CELL_BLOCK: dict[tuple[int, int], int] = {
    (row, col): index
    for index, cells in enumerate(BLOCKS)
    for row, col in cells
}


def block_count() -> int:
    """Number of unlockable blocks; derived from the sprite grouping."""
    return len(BLOCKS)


def progress(lit: int) -> dict:
    """Build the template model for a silhouette with ``lit`` blocks turned on."""
    total = block_count()
    try:
        raw = int(lit)
    except (TypeError, ValueError):
        raw = 0
    lit_n = max(0, min(raw, total))
    cols = len(SPRITE[0]) if SPRITE else 0
    cells: list[dict] = []
    for row, line in enumerate(SPRITE):
        if len(line) != cols:
            raise ValueError(f"Pikachu sprite row {row} is {len(line)} wide, expected {cols}")
        for col, color in enumerate(line):
            if color == ".":
                cells.append({"empty": True, "lit": False, "color": "", "block": None})
                continue
            block = _CELL_BLOCK.get((row, col))
            if block is None:
                raise ValueError(f"Pikachu sprite cell {(row, col)} is not in any block")
            cells.append({
                "empty": False,
                "lit": block < lit_n,
                "color": color,
                "block": block,
            })
    return {
        "lit": lit_n,
        "total": total,
        "complete": raw >= total,
        "cols": cols,
        "rows": len(SPRITE),
        "cells": cells,
    }


def _validate() -> None:
    filled = {
        (row, col)
        for row, line in enumerate(SPRITE)
        for col, color in enumerate(line)
        if color != "."
    }
    assigned = set(_CELL_BLOCK)
    if filled != assigned:
        missing = filled - assigned
        extra = assigned - filled
        raise RuntimeError(f"Pikachu sprite/blocks mismatch: missing={missing} extra={extra}")
    widths = {len(line) for line in SPRITE}
    if len(widths) != 1:
        raise RuntimeError("Pikachu sprite rows must all be the same width")


_validate()
