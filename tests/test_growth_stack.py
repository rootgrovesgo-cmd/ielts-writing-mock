#!/usr/bin/env python3
"""Growth-stack band mapping, lighting, sprites, and HTML render."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import growth_stack as gs  # noqa: E402


class StageMapTests(unittest.TestCase):
    def test_eight_stages_bottom_up(self):
        self.assertEqual(gs.stage_count(), 8)
        self.assertEqual(len(gs.STAGES), 8)
        self.assertEqual(len(gs.stage_ids()), 8)
        self.assertEqual(gs.STAGES, (5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0))
        self.assertEqual(
            gs.stage_ids(),
            ("duck", "turtle", "egg", "sprout", "pink", "lizard", "fox", "mouse"),
        )

    def test_mapping_of_each_half_band(self):
        expected_counts = {
            5.5: 1,
            6.0: 2,
            6.5: 3,
            7.0: 4,
            7.5: 5,
            8.0: 6,
            8.5: 7,
            9.0: 8,
        }
        for band, count in expected_counts.items():
            flags = gs.lit_stages(band)
            with self.subTest(band=band):
                self.assertEqual(len(flags), 8)
                self.assertEqual(sum(flags), count)
                self.assertEqual(flags, tuple(i < count for i in range(8)))
                # Inclusive: this stage and every lower one are lit.
                self.assertTrue(flags[count - 1])
                if count < 8:
                    self.assertFalse(flags[count])

    def test_inclusive_fill_aliases(self):
        for raw in (7, 7.0, "7", "7.0", " 7.0 "):
            self.assertEqual(gs.lit_stages(raw), (True, True, True, True, False, False, False, False), msg=repr(raw))
        for raw in (6, 6.0, "6"):
            self.assertEqual(gs.lit_stages(raw)[:2], (True, True), msg=repr(raw))
            self.assertFalse(any(gs.lit_stages(raw)[2:]))

    def test_seven_lights_four(self):
        flags = gs.lit_stages(7.0)
        self.assertEqual(sum(flags), 4)
        self.assertEqual(flags, (True, True, True, True, False, False, False, False))
        lit_ids = [sid for sid, lit in zip(gs.STAGE_IDS, flags) if lit]
        self.assertEqual(lit_ids, ["duck", "turtle", "egg", "sprout"])

    def test_nine_lights_all(self):
        for raw in (9, 9.0, "9", "9.0"):
            flags = gs.lit_stages(raw)
            self.assertEqual(flags, (True,) * 8, msg=repr(raw))

    def test_below_five_point_five_empty(self):
        for raw in (0, 0.0, 1, 4.5, 5, 5.0, "5.0", "4.5"):
            flags = gs.lit_stages(raw)
            self.assertEqual(flags, (False,) * 8, msg=repr(raw))
            self.assertEqual(gs.status_text(raw), "待成长", msg=repr(raw))

    def test_missing_and_invalid_empty(self):
        for raw in (None, "", "  ", "band", "eight", 7.2, 7.25, 7.1, 8.2, 9.5, 10, -1, "7.2", True, False):
            flags = gs.lit_stages(raw)
            self.assertEqual(flags, (False,) * 8, msg=repr(raw))
            self.assertIsNone(gs._parse_half_band(raw), msg=repr(raw))
            self.assertEqual(gs.status_text(raw), "暂无评分", msg=repr(raw))


class BestBandTests(unittest.TestCase):
    def test_missing_scores_empty(self):
        for scores in (None, "", [], {}, [None, "", "x"], {"speaking": 9.0}):
            self.assertIsNone(gs.best_growth_band(scores), msg=repr(scores))
            self.assertEqual(gs.lit_stages(gs.best_growth_band(scores)), (False,) * 8)

    def test_best_of_reading_listening_and_teacher_writing(self):
        scores = {
            "reading": 6.5,
            "listening": 7.0,
            "writing": 6.0,
            "speaking": 9.0,
            "official_score": 9.0,
        }
        self.assertEqual(gs.best_growth_band(scores), 7.0)

        rows = [
            {"module": "reading", "band_estimate": 6.5},
            {"module": "listening", "band": 7.0},
            {"module": "writing", "teacher_band": 6.0, "official_score": 9.0},
            {"module": "speaking", "band": 8.5, "band_estimate": 8.5},
        ]
        self.assertEqual(gs.best_growth_band(rows), 7.0)

    def test_writing_official_score_ignored(self):
        self.assertIsNone(gs.best_growth_band({"official_score": 9.0}))
        self.assertIsNone(gs.best_growth_band({
            "module": "writing",
            "official_score": 9.0,
            "band_estimate": 8.5,
            "band": 8.0,
        }))
        self.assertEqual(
            gs.best_growth_band({
                "module": "writing",
                "teacher_band": 6.0,
                "official_score": 9.0,
                "teacher_score": "",
            }),
            6.0,
        )
        self.assertEqual(
            gs.best_growth_band({
                "writing": {"official_score": 9.0, "teacher_band": 5.5},
                "speaking": 9.0,
            }),
            5.5,
        )
        self.assertEqual(
            gs.best_growth_band([
                {"module": "writing", "official_score": 9.0},
                {"module": "reading", "band_estimate": 6.5},
            ]),
            6.5,
        )

    def test_speaking_ignored_even_as_best(self):
        self.assertEqual(
            gs.best_growth_band({"reading": 6.0, "speaking": 9.0, "speaking_band": 9.0}),
            6.0,
        )
        self.assertIsNone(gs.best_growth_band({"module": "speaking", "band": 8.0}))

    def test_plain_list_of_bands(self):
        self.assertEqual(gs.best_growth_band([5.5, 6.0, "7.5"]), 7.5)
        self.assertIsNone(gs.best_growth_band([7.2, 9.5, "nope"]))

    def test_nested_reading_and_teacher_keys(self):
        self.assertEqual(
            gs.best_growth_band({
                "reading": {"band_estimate": 6.5, "official_score": 9.0},
                "listening": {"reference_band": 6.0},
                "teacher_band": 8.0,
            }),
            8.0,
        )


class SpriteTests(unittest.TestCase):
    BANNED = (
        "pikachu",
        "pokemon",
        "pokémon",
        "poké",
        "poke ball",
        "pokeball",
        "charmander",
        "squirtle",
        "bulbasaur",
        "jigglypuff",
        "togepi",
        "eevee",
        "psyduck",
        "nintendo",
    )

    def test_each_stage_has_distinct_svg(self):
        self.assertEqual(len(gs._STAGE_DRAW), 8)
        seen = set()
        for stage_id in gs.STAGE_IDS:
            with self.subTest(stage_id=stage_id):
                lit = gs.stage_svg(stage_id, lit=True)
                unlit = gs.stage_svg(stage_id, lit=False)
                self.assertIn("<svg", lit)
                self.assertIn("<svg", unlit)
                self.assertIn('class="growth-stack-svg is-lit"', lit)
                self.assertIn('class="growth-stack-svg is-unlit"', unlit)
                self.assertNotEqual(lit, unlit)
                self.assertIn(gs.UNLIT_FILL, unlit)
                self.assertNotIn("image-rendering:pixelated", lit)
                self.assertNotIn("image-rendering: pixelated", lit)
                self.assertNotIn(lit, seen)
                seen.add(lit)

    def test_gallery_has_eight_top_down_stages(self):
        data = gs.gallery(7.0)
        self.assertEqual(data["total"], 8)
        self.assertEqual(len(data["stages"]), 8)
        self.assertEqual(data["lit"], 4)
        self.assertFalse(data["empty"])
        self.assertEqual(data["band"], 7.0)
        self.assertEqual(data["band_label"], "7.0")
        self.assertEqual(data["title"], "成长进度")
        self.assertEqual(data["status"], "当前最高 7.0")
        ids = [s["id"] for s in data["stages"]]
        self.assertEqual(ids, list(reversed(gs.STAGE_IDS)))
        self.assertEqual(ids[0], "mouse")
        self.assertEqual(ids[-1], "duck")
        lit_ids = [s["id"] for s in data["stages"] if s["lit"]]
        self.assertEqual(lit_ids, ["sprout", "egg", "turtle", "duck"])
        current = [s["id"] for s in data["stages"] if s["current"]]
        self.assertEqual(current, ["sprout"])
        for fig in data["stages"]:
            self.assertIn("<svg", fig["svg"])
            if fig["lit"]:
                self.assertIn("is-lit", fig["svg"])
                self.assertNotEqual(fig["svg"], gs.stage_svg(fig["id"], lit=False))
            else:
                self.assertIn("is-unlit", fig["svg"])
                self.assertIn(gs.UNLIT_FILL, fig["svg"])

    def test_gallery_from_scores_and_empty_state(self):
        data = gs.gallery(scores={"reading": 8.0, "official_score": 9.0, "speaking": 9.0})
        self.assertEqual(data["band"], 8.0)
        self.assertEqual(data["lit"], 6)
        empty = gs.gallery(scores=None)
        self.assertTrue(empty["empty"])
        self.assertIsNone(empty["band"])
        self.assertEqual(empty["status"], "暂无评分")
        self.assertEqual(sum(1 for s in empty["stages"] if s["lit"]), 0)
        waiting = gs.gallery(band=5.0)
        self.assertTrue(waiting["empty"])
        self.assertEqual(waiting["status"], "待成长")


class RenderTests(unittest.TestCase):
    def test_render_marks_lit_and_unlit(self):
        markup = gs.render(7.0)
        self.assertIn("成长进度", markup)
        self.assertIn("当前最高 7.0", markup)
        self.assertIn('class="growth-stack"', markup)
        self.assertIn('data-band="7.0"', markup)
        self.assertNotIn("image-rendering: pixelated", markup)
        self.assertNotIn("image-rendering:pixelated", markup)
        self.assertEqual(markup.count("<svg"), 8)
        self.assertEqual(markup.count('<li class="growth-stack-stage '), 8)
        self.assertEqual(markup.count('<li class="growth-stack-stage is-lit'), 4)
        self.assertEqual(markup.count('<li class="growth-stack-stage is-unlit'), 4)
        self.assertIn('data-stage="sprout"', markup)
        self.assertIn("is-current", markup)
        self.assertIn("暂无评分", gs.render(None))
        self.assertIn("待成长", gs.render(5.0))
        self.assertIn("is-empty", gs.render(None))
        self.assertNotIn("/tmp/growth-ref", markup)
        self.assertNotIn("stack.png", markup)
        lowered = markup.lower()
        for name in SpriteTests.BANNED:
            self.assertNotIn(name, lowered)

    def test_css_is_illustration_not_pixel_grid(self):
        css = (ROOT / "static" / "growth_stack.css").read_text(encoding="utf-8")
        self.assertNotIn("image-rendering: pixelated", css)
        self.assertNotIn("image-rendering:pixelated", css)
        self.assertNotIn("growth-stack-cell", css)
        self.assertNotIn("grid-auto-rows: 4px", css)
        self.assertNotIn("width: 4px", css)
        self.assertNotIn("height: 4px", css)
        self.assertIn("background: #f3e6b0", css)
        source = Path(gs.__file__).read_text(encoding="utf-8")
        self.assertIn("never", source.lower())
        self.assertNotIn("/tmp/growth-ref", source)
        self.assertNotIn("stack.png", css)
        self.assertNotIn("stack.png", source)
        lowered = (css + chr(10) + source).lower()
        for name in SpriteTests.BANNED:
            self.assertNotIn(name, lowered)


if __name__ == "__main__":
    unittest.main()
