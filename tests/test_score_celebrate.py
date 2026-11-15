#!/usr/bin/env python3
"""Band-to-celebration-tier mapping and hooks on reading/listening results."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import score_celebrate as sc  # noqa: E402


class CelebrationTierTests(unittest.TestCase):
    def test_no_celebration_below_seven(self):
        for band in (None, "", "  ", "band", 0, 1, 5.5, 6, 6.0, 6.5, "6.5"):
            self.assertIsNone(sc.celebration_tier(band), msg=repr(band))

    def test_rejects_non_half_bands(self):
        for band in (7.2, 7.25, 7.1, 8.2, 9.5, 10, -1, "7.2", "eight"):
            self.assertIsNone(sc.celebration_tier(band), msg=repr(band))

    def test_small_fireworks_for_seven(self):
        for band in (7, 7.0, "7", "7.0"):
            self.assertEqual(sc.celebration_tier(band), sc.SMALL_FIREWORKS, msg=repr(band))

    def test_ring_for_seven_point_five(self):
        for band in (7.5, "7.5"):
            self.assertEqual(sc.celebration_tier(band), sc.FIREWORKS_RING, msg=repr(band))

    def test_crown_from_eight_up(self):
        for band in (8, 8.0, 8.5, 9, 9.0, "8", "8.0", "8.5", "9", "9.0"):
            self.assertEqual(sc.celebration_tier(band), sc.FIREWORKS_CROWN, msg=repr(band))

    def test_inclusive_thresholds(self):
        self.assertEqual(sc.celebration_tier(7.0), sc.SMALL_FIREWORKS)
        self.assertIsNone(sc.celebration_tier(6.5))
        self.assertEqual(sc.celebration_tier(7.5), sc.FIREWORKS_RING)
        self.assertEqual(sc.celebration_tier(8.0), sc.FIREWORKS_CROWN)


class FrontendHookTests(unittest.TestCase):
    def _read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_js_keeps_same_thresholds(self):
        js = self._read("static/score_celebrate.js")
        self.assertIn("var SMALL_MIN = 7.0;", js)
        self.assertIn("var RING_MIN = 7.5;", js)
        self.assertIn("var CROWN_MIN = 8.0;", js)
        self.assertIn("function celebrationTier(band)", js)
        self.assertIn("prefers-reduced-motion", js)
        self.assertIn("Skip", js)
        self.assertIn("RING_SPRITE", js)
        self.assertIn("CROWN_SPRITE", js)
        self.assertNotIn("http://", js)
        self.assertNotIn("https://", js)
        self.assertIn("Original 8-bit art only", js)

    def test_reading_and_listening_templates_include_assets(self):
        for rel in ("templates/reading.html", "templates/listening.html"):
            html = self._read(rel)
            with self.subTest(rel=rel):
                self.assertIn("score_celebrate.css", html)
                self.assertIn("score_celebrate.js", html)
                # Load the module before the exam script so play() exists on submit.
                css_at = html.index("score_celebrate.css")
                js_at = html.index("score_celebrate.js")
                exam_js = "reading.js" if "reading.html" in rel else "listening.js"
                self.assertLess(js_at, html.index(exam_js, js_at))
                self.assertLess(css_at, js_at)

    def test_exam_scripts_play_after_submit_result(self):
        for rel in ("static/reading.js", "static/listening.js"):
            js = self._read(rel)
            with self.subTest(rel=rel):
                self.assertIn("window.ScoreCelebrate.play({", js)
                self.assertIn("band: data && data.band_estimate", js)
                self.assertIn("submissionId: data && data.id", js)
                play_at = js.index("ScoreCelebrate.play")
                fn_at = js.index("function renderDoneResult")
                submit_at = js.index("async function submitAnswers")
                self.assertLess(fn_at, play_at)
                self.assertLess(play_at, submit_at)

    def test_not_hooked_on_writing_or_records_pages(self):
        pages = [
            "templates/exam.html",
            "templates/speaking.html",
            "templates/student_home.html",
            "templates/student_detail.html",
            "templates/student_review.html",
            "templates/admin.html",
            "templates/admin_detail.html",
            "templates/hub.html",
        ]
        for rel in pages:
            text = self._read(rel)
            with self.subTest(rel=rel):
                self.assertNotIn("score_celebrate", text)

    def test_css_is_pixelated_and_does_not_block_review(self):
        css = self._read("static/score_celebrate.css")
        self.assertIn("image-rendering: pixelated", css)
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn("body.score-celebrate-on #donePanel", css)
        self.assertIn("z-index: 80", css)
        self.assertIn("score-celebrate-skip", css)


if __name__ == "__main__":
    unittest.main()
