#!/usr/bin/env python3
"""Set A listening explanations: prediction, paraphrase logic, and audio quotes."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import explain_format  # noqa: E402
import listening_scoring as ls  # noqa: E402

FROZEN_ANSWERS = {
    1: "poetry",
    2: "courtyard",
    3: "academic",
    4: "comics",
    5: "Pellam",
    6: "staircase",
    7: "reviews",
    8: "handmade",
    9: "30",
    10: "average",
    11: "B",
    12: "C",
    13: "B",
    14: "A",
    15: "B",
    16: "C",
    17: "B",
    18: "D",
    19: "C",
    20: "D",
    21: "A",
    22: "C",
    23: "A",
    24: "C",
    25: "A",
    26: "E",
    27: "C",
    28: "B",
    29: "B",
    30: "A",
    31: "bitumen",
    32: "sterile",
    33: "lizards",
    34: "gyms",
    35: "theatre",
    36: "pilot",
    37: "cinemas",
    38: "playground",
    39: "lamps",
    40: "robots",
}

FROZEN_ALTERNATIVES = {
    4: ["comic"],
    5: ["PELLAM"],
    6: ["stair"],
    8: ["hand-made", "hand made"],
    9: ["thirty", "30.00", "£30", "£30.00"],
    33: ["lizard"],
    34: ["gym"],
    35: ["theater"],
    37: ["cinema"],
    38: ["playgrounds"],
    39: ["lights", "lamp", "light"],
    40: ["robot"],
}

FROZEN_PAIRS = {
    17: [17, 18],
    18: [17, 18],
    19: [19, 20],
    20: [19, 20],
    21: [21, 22],
    22: [21, 22],
    23: [23, 24],
    24: [23, 24],
    25: [25, 26],
    26: [25, 26],
}

LABELS = ("预测：", "考点与原文逻辑替换：", "跟音：")


def _keys() -> dict:
    return json.loads((ROOT / "prompts" / "listening_keys.json").read_text(encoding="utf-8"))


def _set_a_script_text() -> str:
    sys.path.insert(0, str(ROOT / "tools"))
    from listening_script import SECTIONS  # noqa: WPS433

    chunks: list[str] = []
    for cues in SECTIONS.values():
        for cue in cues:
            if cue[0] == "say":
                chunks.append(cue[2])
    return "\n".join(chunks)


def _normalize_quote(text: str) -> str:
    value = re.sub(r"\*\*(.+?)\*\*", r"\1", text or "")
    value = value.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    value = re.sub(
        r"^(Fraser|Naomi|Rowan Hale|Lila|Jonah|Professor Bram Ellerby|Narrator):\s*",
        "",
        value,
        flags=re.M,
    )
    value = value.replace('"', " ")
    return re.sub(r"\s+", " ", value).strip()


def _letters(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9']+", " ", text or "")).strip().lower()


def _quote_has_script_span(quote: str, script: str) -> bool:
    words = re.findall(r"[A-Za-z0-9']+", _normalize_quote(quote))
    if len(words) < 6:
        return False
    script_letters = _letters(script)
    for length in range(min(12, len(words)), 5, -1):
        for start in range(0, len(words) - length + 1):
            span = " ".join(words[start : start + length]).lower()
            if span in script_letters:
                return True
    return False


class SetAExplanationStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = _keys()
        cls.questions = cls.data["questions"]

    def test_answers_and_scoring_fields_unchanged(self):
        self.assertEqual(self.data.get("set_id"), "set-a")
        self.assertEqual(set(self.questions), {str(q) for q in range(1, 41)})
        for num, answer in FROZEN_ANSWERS.items():
            meta = self.questions[str(num)]
            self.assertEqual(meta["answer"], answer, num)
            if num in FROZEN_ALTERNATIVES:
                self.assertEqual(meta.get("alternatives"), FROZEN_ALTERNATIVES[num], num)
            else:
                self.assertNotIn("alternatives", meta, num)
            if num in FROZEN_PAIRS:
                self.assertEqual(meta.get("pair"), FROZEN_PAIRS[num], num)
            else:
                self.assertNotIn("pair", meta, num)
        self.assertEqual(ls.official_answers(self.data), FROZEN_ANSWERS)

    def test_each_item_has_three_nonempty_parts_and_composed_labels(self):
        for num in range(1, 41):
            meta = self.questions[str(num)]
            for field in ("prediction", "logic", "audio_quote"):
                self.assertTrue(str(meta.get(field) or "").strip(), f"Q{num} missing {field}")
            text = meta.get("explanation") or ""
            for label in LABELS:
                self.assertIn(label, text, f"Q{num} explanation missing {label}")
            composed = explain_format.compose_explanation(meta)
            self.assertEqual(text, composed, num)

    def test_audio_quotes_come_from_set_a_script(self):
        script = _set_a_script_text()
        self.assertIn("What people actually come in for is the poetry", script)
        for num in range(1, 41):
            quote = self.questions[str(num)]["audio_quote"]
            self.assertTrue(
                _quote_has_script_span(quote, script),
                f"Q{num} audio_quote is not drawn from tools/listening_script.py: {quote[:180]}",
            )

    def test_choose_two_pairs_are_not_identical(self):
        for left, right in ((17, 18), (19, 20), (21, 22), (23, 24), (25, 26)):
            a = self.questions[str(left)]
            b = self.questions[str(right)]
            self.assertNotEqual(a["logic"], b["logic"], (left, right))
            self.assertNotEqual(a["audio_quote"], b["audio_quote"], (left, right))
            self.assertTrue(a["answer"] in a["logic"], left)
            self.assertTrue(b["answer"] in b["logic"], right)

    def test_q1_and_mcq_teach_the_requested_shape(self):
        q1 = self.questions["1"]
        self.assertIn("specialist collection of", q1["prediction"])
        self.assertIn("that's not necessarily why I'd recommend it", q1["logic"])
        self.assertIn("poetry", q1["audio_quote"])
        self.assertIn("Fraser:", q1["audio_quote"])
        q14 = self.questions["14"]
        self.assertIn("MOST", q14["prediction"])
        self.assertIn("calming", q14["logic"])
        self.assertIn("What I value most is how calming it is", q14["audio_quote"])


class ExplanationFormatterTests(unittest.TestCase):
    def test_html_renders_labeled_parts_and_bold(self):
        keys = _keys()
        html = explain_format.explanation_html(keys["questions"]["1"])
        self.assertIn('class="q-explain-parts"', html)
        self.assertIn("预测", html)
        self.assertIn("考点与原文逻辑替换", html)
        self.assertIn("跟音", html)
        self.assertIn("<strong>poetry</strong>", html)
        self.assertNotIn("**poetry**", html)

    def test_plain_explanation_stays_a_paragraph(self):
        html = explain_format.explanation_html("定位第三段，答案是 sand。")
        self.assertEqual(html, "<p>定位第三段，答案是 sand。</p>")
        self.assertNotIn("q-explain-parts", html)

    def test_parse_roundtrip_from_composed_string(self):
        text = (
            "预测：应填名词。\n"
            "考点与原文逻辑替换：原文用 X 替换 Y。\n"
            "跟音：Fraser: “The stock is academic.”"
        )
        parts = explain_format.parse_labeled_explanation(text)
        self.assertEqual(parts["prediction"], "应填名词。")
        self.assertEqual(parts["logic"], "原文用 X 替换 Y。")
        self.assertEqual(parts["audio_quote"], "Fraser: “The stock is academic.”")


class PaperDoesNotLeakExplanationsTests(unittest.TestCase):
    def test_student_paper_json_has_no_explanation_fields(self):
        paper = json.loads((ROOT / "prompts" / "listening_set_a.json").read_text(encoding="utf-8"))
        dumped = json.dumps(paper)
        for field in ("explanation", "prediction", "audio_quote", "考点与原文逻辑替换"):
            self.assertNotIn(field, dumped)

    def test_paper_api_hides_explanation_fields(self):
        import tempfile
        import access as accessmod
        import app as appmod

        tmp = tempfile.TemporaryDirectory()
        prev = (appmod.DATA_DIR, appmod.SUBMISSIONS_DIR, appmod.INDEX_PATH)
        try:
            base = Path(tmp.name)
            appmod.DATA_DIR = base / "data"
            appmod.SUBMISSIONS_DIR = appmod.DATA_DIR / "submissions"
            appmod.INDEX_PATH = appmod.DATA_DIR / "index.json"
            accessmod.bind(appmod.DATA_DIR)
            appmod.ensure_storage()
            appmod.app.config["TESTING"] = True
            client = appmod.app.test_client()
            accessmod.create_code(code="EXPLAIN1")
            started = client.post(
                "/api/session/start",
                json={
                    "candidate_name": "Explain Student",
                    "invite_code": "EXPLAIN1",
                    "module": "listening",
                    "mode": "full",
                },
            )
            self.assertEqual(started.status_code, 200)
            res = client.get("/api/listening/paper")
            self.assertEqual(res.status_code, 200)
            raw = res.get_data(as_text=True)
            for field in ("explanation", "prediction", "audio_quote", "考点与原文逻辑替换", "跟音"):
                self.assertNotIn(field, raw)
        finally:
            appmod.DATA_DIR, appmod.SUBMISSIONS_DIR, appmod.INDEX_PATH = prev
            accessmod.bind(appmod.DATA_DIR)
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
