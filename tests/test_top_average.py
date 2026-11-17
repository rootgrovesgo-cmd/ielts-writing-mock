#!/usr/bin/env python3
"""Highest-three average math, copy, eligibility, and HTML render."""

from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import top_average as ta  # noqa: E402


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
    "叠叠乐",
    "成长进度",
    "暂无评分",
    "待成长",
    "当前最高",
)


def scored(*rows):
    """Build timestamped eligible rows in chronological order."""
    out = []
    for index, row in enumerate(rows, start=1):
        item = dict(row)
        item.setdefault("timestamp", f"2026-11-0{index}T09:00:00+08:00")
        out.append(item)
    return out


class ParseBandTests(unittest.TestCase):
    def test_half_bands_and_aliases(self):
        for raw, expected in (
            (7, 7.0),
            (7.0, 7.0),
            ("7", 7.0),
            ("7.0", 7.0),
            (" 6.5 ", 6.5),
            (0, 0.0),
            (9, 9.0),
        ):
            self.assertEqual(ta.parse_half_band(raw), expected, msg=repr(raw))

    def test_missing_and_invalid_rejected(self):
        for raw in (None, "", "  ", "band", "eight", 7.2, 7.25, 7.1, 8.2, 9.5, 10, -1, "7.2", True, False):
            self.assertIsNone(ta.parse_half_band(raw), msg=repr(raw))


class EligibilityTests(unittest.TestCase):
    def test_missing_scores_empty(self):
        for scores in (None, "", [], {}, [None, "", "x"], {"speaking": 9.0}):
            self.assertEqual(ta.eligible_entries(scores), [], msg=repr(scores))
            data = ta.snapshot(scores)
            self.assertTrue(data["empty"], msg=repr(scores))
            self.assertIsNone(data["average"])

    def test_writing_official_score_ignored(self):
        self.assertEqual(ta.eligible_entries({"official_score": 9.0}), [])
        self.assertEqual(
            ta.eligible_entries({
                "module": "writing",
                "official_score": 9.0,
                "band_estimate": 8.5,
                "band": 8.0,
            }),
            [],
        )
        entries = ta.eligible_entries({
            "module": "writing",
            "teacher_band": 6.0,
            "official_score": 9.0,
            "teacher_score": "",
        })
        self.assertEqual([row["band"] for row in entries], [6.0])
        self.assertEqual(
            [row["band"] for row in ta.eligible_entries({
                "writing": {"official_score": 9.0, "teacher_band": 5.5},
                "speaking": 9.0,
            })],
            [5.5],
        )
        self.assertEqual(
            [row["module"] for row in ta.eligible_entries([
                {"module": "writing", "official_score": 9.0},
                {"module": "reading", "band_estimate": 6.5},
            ])],
            ["reading"],
        )

    def test_speaking_ignored_even_as_best(self):
        entries = ta.eligible_entries({"reading": 6.0, "speaking": 9.0, "speaking_band": 9.0})
        self.assertEqual([(row["module"], row["band"]) for row in entries], [("reading", 6.0)])
        self.assertEqual(ta.eligible_entries({"module": "speaking", "band": 8.0}), [])

    def test_plain_list_of_bands(self):
        bands = [row["band"] for row in ta.eligible_entries([5.5, 6.0, "7.5"])]
        self.assertEqual(bands, [5.5, 6.0, 7.5])
        self.assertEqual(ta.eligible_entries([7.2, 9.5, "nope"]), [])

    def test_nested_reading_and_teacher_keys(self):
        entries = ta.eligible_entries({
            "reading": {"band_estimate": 6.5, "official_score": 9.0},
            "listening": {"reference_band": 6.0},
            "teacher_band": 8.0,
        })
        self.assertEqual(
            [(row["module"], row["band"]) for row in entries],
            [("reading", 6.5), ("listening", 6.0), ("writing", 8.0)],
        )


class AverageMathTests(unittest.TestCase):
    def test_example_six_seventeen_then_six_thirty_three(self):
        first = ta.snapshot([6.0, 6.0, 6.5])
        self.assertEqual(first["average_label"], "6.17")
        self.assertEqual(first["count"], 3)
        self.assertEqual([part["band_label"] for part in first["parts"]], ["6.5", "6.0", "6.0"])
        # The latest 6.5 raised the average from 6.00, so a positive delta is shown.
        self.assertEqual(first["delta_label"], "0.17")
        self.assertTrue(first["improved"])

        improved = ta.snapshot([6.0, 6.0, 6.5, 6.5])
        self.assertEqual(improved["average_label"], "6.33")
        self.assertEqual(improved["delta_label"], "0.16")
        self.assertEqual([part["band_label"] for part in improved["parts"]], ["6.5", "6.5", "6.0"])
        self.assertTrue(improved["improved"])

    def test_average_uses_highest_three_individual_papers(self):
        data = ta.snapshot([
            {"module": "reading", "band_estimate": 6.0},
            {"module": "reading", "band_estimate": 7.0},
            {"module": "listening", "band_estimate": 6.5},
            {"module": "listening", "band_estimate": 5.5},
            {"module": "writing", "teacher_band": 8.0},
        ])
        self.assertEqual(data["average_label"], "7.17")
        self.assertEqual(
            [(part["module"], part["band_label"]) for part in data["parts"]],
            [("writing", "8.0"), ("reading", "7.0"), ("listening", "6.5")],
        )
        self.assertIn("从 5 次成绩中取最高三次", data["count_line"])

    def test_one_and_two_scores_still_show_average(self):
        one = ta.snapshot([{"module": "reading", "band_estimate": 6.5}])
        self.assertEqual(one["average_label"], "6.50")
        self.assertEqual(one["count"], 1)
        self.assertEqual(one["count_line"], "已计入 1 次成绩，再完成两次会更稳")
        self.assertFalse(one["empty"])
        self.assertFalse(one["improved"])
        self.assertIsNone(one["delta"])

        two = ta.snapshot([
            {"module": "reading", "band_estimate": 6.0, "timestamp": "2026-11-01T09:00:00+08:00"},
            {"module": "listening", "band_estimate": 6.5, "timestamp": "2026-11-02T09:00:00+08:00"},
        ])
        self.assertEqual(two["average_label"], "6.25")
        self.assertEqual(two["count_line"], "已计入 2 次成绩，再完成一次会更稳")
        self.assertEqual(two["delta_label"], "0.25")
        self.assertEqual(two["message"], ta.RISE_MESSAGE)

    def test_positive_delta_only(self):
        dropped = ta.snapshot([7.0, 7.0, 5.0])
        self.assertEqual(dropped["average_label"], "6.33")
        self.assertFalse(dropped["improved"])
        self.assertIsNone(dropped["delta"])
        self.assertNotIn("低", dropped["message"])
        self.assertNotIn("下降", dropped["message"])

        unchanged = ta.snapshot([6.5, 6.5, 6.0, 5.5])
        self.assertEqual(unchanged["average_label"], "6.33")
        self.assertIsNone(unchanged["delta"])
        self.assertFalse(unchanged["improved"])

    def test_delta_uses_displayed_averages(self):
        # 6.17 -> 6.33 must show +0.16, not the raw 0.166... rounded to 0.17.
        data = ta.snapshot([6.0, 6.0, 6.5, 6.5])
        self.assertEqual(data["average"], Decimal("6.33"))
        self.assertEqual(data["delta"], Decimal("0.16"))

    def test_teacher_writing_and_reference_scores_only(self):
        data = ta.snapshot({
            "reading": 6.5,
            "listening": 7.0,
            "writing": 6.0,
            "speaking": 9.0,
            "official_score": 9.0,
        })
        self.assertEqual(data["average_label"], "6.50")
        self.assertEqual({part["module"] for part in data["parts"]}, {"reading", "listening", "writing"})


class CopyAndRenderTests(unittest.TestCase):
    def test_empty_state_is_warm_and_inviting(self):
        data = ta.snapshot(None)
        self.assertEqual(data["title"], "最高三项平均分")
        self.assertEqual(data["message"], "完成一次练习，这里就会亮起来")
        self.assertEqual(data["hint"], "每一次认真作答，都会在这里被看见。")
        markup = ta.render(None)
        self.assertIn("最高三项平均分", markup)
        self.assertIn("完成一次练习，这里就会亮起来", markup)
        self.assertIn('class="top-average is-empty"', markup)
        self.assertEqual(Path(ta._CSS_PATH).name, "top_average.css")
        self.assertNotIn("growth-stack", markup)
        self.assertNotIn("成长进度", markup)
        self.assertNotIn("暂无评分", markup)
        self.assertNotIn("growth_stack.css", markup)
        for name in BANNED:
            self.assertNotIn(name, markup.lower() if name.isascii() else markup)

    def test_render_shows_components_delta_and_two_decimals(self):
        markup = ta.render([6.0, 6.0, 6.5, 6.5])
        self.assertIn("6.33", markup)
        self.assertIn('data-average="6.33"', markup)
        self.assertIn('data-delta="0.16"', markup)
        self.assertIn("比上次高 0.16", markup)
        self.assertIn("又进步了一点，继续保持", markup)
        self.assertIn("6.5", markup)
        self.assertIn("6.0", markup)
        self.assertIn('class="top-average is-improved"', markup)
        self.assertIn("top-average-value", markup)
        self.assertNotIn("成长进度", markup)
        self.assertNotIn("暂无评分", markup)
        self.assertNotIn("growth-stack", markup)
        lowered = markup.lower()
        for name in BANNED:
            self.assertNotIn(name, lowered if name.isascii() else markup)

    def test_count_lines_and_rise_to_three(self):
        markup = ta.render(scored(
            {"module": "reading", "band_estimate": 6.0},
            {"module": "listening", "band_estimate": 6.0},
            {"module": "writing", "teacher_band": 6.5},
        ))
        self.assertIn("6.17", markup)
        self.assertIn("已计入 3 次成绩", markup)
        self.assertIn("三项成绩都到齐了，继续保持", markup)
        self.assertIn("阅读 6.0", markup)
        self.assertIn("听力 6.0", markup)
        self.assertIn("写作 6.5", markup)

        one = ta.render({"module": "reading", "band_estimate": 6.5})
        self.assertIn("6.50", one)
        self.assertIn("已计入 1 次成绩，再完成两次会更稳", one)
        self.assertIn("阅读 6.5", one)
        self.assertNotIn("比上次高", one)

    def test_css_is_inlined_and_has_no_totem(self):
        css = (ROOT / "static" / "top_average.css").read_text(encoding="utf-8")
        markup = ta.render([6.5])
        self.assertIn(".top-average-value", css)
        self.assertIn("tabular-nums", css)
        self.assertIn(css.strip()[:40], markup)
        self.assertNotIn("growth-stack", css)
        self.assertNotIn("image-rendering: pixelated", css)
        self.assertNotIn("叠叠乐", css)
        source = Path(ta.__file__).read_text(encoding="utf-8")
        lowered = (css + "\n" + source + "\n" + markup).lower()
        for name in BANNED:
            hay = lowered if name.isascii() else (css + source + markup)
            self.assertNotIn(name, hay)


if __name__ == "__main__":
    unittest.main()
