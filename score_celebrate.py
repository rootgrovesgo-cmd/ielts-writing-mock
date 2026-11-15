"""Map an official/reference IELTS band to a post-submit celebration tier.

Used by the reading and listening student results screens. Keep the
thresholds in sync with static/score_celebrate.js.
"""

from __future__ import annotations

SMALL_FIREWORKS = "small_fireworks"
FIREWORKS_RING = "fireworks_ring"
FIREWORKS_CROWN = "fireworks_crown"

# Inclusive lower bounds: a higher official band still celebrates.
# 7.0 <= band < 7.5  → small pixel fireworks
# 7.5 <= band < 8.0  → full-screen fireworks + pixel ring
# band >= 8.0        → fireworks + pixel crown
SMALL_MIN = 7.0
RING_MIN = 7.5
CROWN_MIN = 8.0


def _is_half_band(value: float) -> bool:
    """True for official IELTS half-band steps (0, 0.5, …, 9.0)."""
    if value < 0 or value > 9:
        return False
    return abs(value * 2 - round(value * 2)) <= 1e-9


def celebration_tier(band) -> str | None:
    """Return a celebration tier, or None if this score should not animate.

    Accepts official/reference bands as int, float, or numeric string
    (7, 7.0, "7.5"). Non-bands, empty values, and in-between numbers
    such as 7.2 produce None.
    """
    if band is None or band == "":
        return None
    try:
        value = float(band)
    except (TypeError, ValueError):
        return None
    if not _is_half_band(value):
        return None
    if value >= CROWN_MIN:
        return FIREWORKS_CROWN
    if value >= RING_MIN:
        return FIREWORKS_RING
    if value >= SMALL_MIN:
        return SMALL_FIREWORKS
    return None
