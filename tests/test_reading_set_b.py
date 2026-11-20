#!/usr/bin/env python3
"""Tests for Academic Reading Set B and multi-set loading/scoring."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import access as accessmod  # noqa: E402
import app as appmod  # noqa: E402
import explain_format  # noqa: E402
import reading_review as rr  # noqa: E402
import reading_scoring as rs  # noqa: E402
import report_pdf  # noqa: E402

PAPER_PATH = ROOT / "prompts" / "reading_set_b.json"
KEYS_PATH = ROOT / "prompts" / "reading_keys_set_b.json"

FORBIDDEN_OFFICIAL = (
    "fienberg",
    "adrian hunt",
    "rick bonney",
    "dr carlson",
    "schrag",
    "kasting",
    "in praise of amateurs",
    "preferred tv",
    "london underground",
    "london's underground",
)

STUDENT_PATHS = [
    PAPER_PATH,
    ROOT / "templates" / "reading.html",
    ROOT / "static" / "reading.js",
    ROOT / "static" / "reading.css",
]

WORD_RANGES = {
    1: (880, 950),
    2: (880, 980),
    3: (900, 1050),
}

TITLES = {
    1: "The development of the Manchester Ship Canal",
    2: "The case for volunteer river monitors",
    3: "What kept early Earth unfrozen",
}


def load_paper() -> dict:
    return json.loads(PAPER_PATH.read_text(encoding="utf-8"))


def load_keys() -> dict:
    return json.loads(KEYS_PATH.read_text(encoding="utf-8"))


def official_from_keys(keys: dict) -> dict[int, str]:
    return {int(q): meta["answer"] for q, meta in keys["questions"].items()}


def word_limit_from_group(group: dict) -> int | None:
    return rs.word_limit_from_instructions(group.get("instructions"))


class SetBPaperTests(unittest.TestCase):
    def setUp(self):
        self.paper = load_paper()
        self.keys = load_keys()

    def test_paper_identity_and_shape(self):
        self.assertEqual(self.paper["id"], "set-b")
        self.assertEqual(self.paper["title"], "Set B")
        self.assertEqual(self.paper["subtitle"], "Academic Reading")
        self.assertIn("instructions", self.paper)
        self.assertEqual(len(self.paper["passages"]), 3)
        self.assertEqual(len(self.paper["groups"]), 7)

    def test_forty_unique_questions_and_ranges(self):
        nums: list[int] = []
        expected = [
            ("q1-6", "notes", 1, 1, 6),
            ("q7-14", "tfng", 1, 7, 14),
            ("q15-22", "summary", 2, 15, 22),
            ("q23-27", "matching_features", 2, 23, 27),
            ("q28-33", "matching_info", 3, 28, 33),
            ("q34-36", "tfng", 3, 34, 36),
            ("q37-40", "summary", 3, 37, 40),
        ]
        for group, (gid, gtype, passage, lo, hi) in zip(self.paper["groups"], expected, strict=True):
            self.assertEqual(group["id"], gid)
            self.assertEqual(group["type"], gtype)
            self.assertEqual(group["passage"], passage)
            self.assertEqual(group["from"], lo)
            self.assertEqual(group["to"], hi)
            nums.extend(range(lo, hi + 1))
        self.assertEqual(nums, list(range(1, 41)))
        self.assertEqual(len(set(nums)), 40)

    def test_titles_word_counts_and_lettered_passage3(self):
        for passage in self.paper["passages"]:
            words = " ".join(passage["paragraphs"]).split()
            lo, hi = WORD_RANGES[passage["id"]]
            self.assertEqual(passage["title"], TITLES[passage["id"]])
            self.assertTrue(
                lo <= len(words) <= hi,
                f"{passage['title']}: {len(words)} not in {lo}–{hi}",
            )
            if passage["id"] == 3:
                self.assertTrue(passage.get("lettered"))
                self.assertEqual(len(passage["paragraphs"]), 8)
            else:
                self.assertFalse(bool(passage.get("lettered")))

    def test_student_json_has_no_keys_or_official_names(self):
        dumped = json.dumps(self.paper)
        self.assertNotIn("explanation", dumped)
        self.assertNotIn("stem_keywords", dumped)
        self.assertNotIn("correct_answer", dumped)
        for label in ("题干关键词", "原文定位", "关键词替换", "判定点"):
            self.assertNotIn(label, dumped)
        self.assertNotRegex(dumped, r'"answer"\s*:')
        lower = dumped.lower()
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lower, word)
        for path in STUDENT_PATHS:
            text = path.read_text(encoding="utf-8").lower()
            for word in FORBIDDEN_OFFICIAL:
                self.assertNotIn(word, text, f"{word!r} in {path}")

    def test_completion_answers_in_passage_and_word_limits(self):
        questions = self.keys["questions"]
        by_passage = {p["id"]: " ".join(p["paragraphs"]) for p in self.paper["passages"]}
        for group in self.paper["groups"]:
            if group["type"] not in {"notes", "summary"}:
                continue
            limit = word_limit_from_group(group)
            self.assertIsNotNone(limit, group["id"])
            source = by_passage[group["passage"]]
            for q in range(group["from"], group["to"] + 1):
                answer = questions[str(q)]["answer"]
                self.assertLessEqual(len(answer.split()), limit, q)
                self.assertIsNotNone(
                    re.search(r"(?i)\b" + re.escape(answer) + r"\b", source),
                    f"Q{q} {answer!r} not in passage {group['passage']}",
                )

    def test_choice_answers_are_valid(self):
        questions = self.keys["questions"]
        tfng_vals = {"TRUE", "FALSE", "NOT GIVEN"}
        tfng_seen: set[str] = set()
        for group in self.paper["groups"]:
            for q in range(group["from"], group["to"] + 1):
                meta = questions[str(q)]
                self.assertEqual(meta["type"], group["type"])
                answer = meta["answer"]
                if group["type"] == "tfng":
                    self.assertIn(answer, tfng_vals)
                    tfng_seen.add(answer)
                elif group["type"] == "matching_features":
                    self.assertIn(answer, group["options"])
                elif group["type"] == "matching_info":
                    self.assertRegex(answer, r"^[A-H]$")
        # Across both TFNG groups, all three values appear; P1 alone already has all three.
        self.assertEqual(tfng_seen, tfng_vals)
        p1_tfng = {questions[str(q)]["answer"] for q in range(7, 15)}
        self.assertTrue({"TRUE", "FALSE", "NOT GIVEN"} <= p1_tfng)
        p3_tfng = {questions[str(q)]["answer"] for q in range(34, 37)}
        self.assertGreater(len(p3_tfng), 1)

    def test_keys_have_forty_explanations(self):
        self.assertEqual(self.keys["set_id"], "set-b")
        questions = self.keys["questions"]
        self.assertEqual(sorted(int(q) for q in questions), list(range(1, 41)))
        for q, meta in questions.items():
            self.assertTrue(meta.get("explanation"), q)
            self.assertTrue(meta.get("answer"), q)
            self.assertTrue(meta.get("type"), q)

    def test_helpers_load_set_b(self):
        paper = rr.load_paper_for_set("set-b")
        keys = rr.load_keys_for_set("set-b")
        self.assertIsNotNone(paper)
        self.assertEqual(paper["id"], "set-b")
        self.assertEqual(keys["set_id"], "set-b")
        self.assertEqual(len(keys["questions"]), 40)
        self.assertEqual(rr.keys_path_for_set("set-a"), rs.KEYS_PATH)
        self.assertEqual(rr.keys_path_for_set("set-b"), KEYS_PATH)
        self.assertIsNone(rr.load_paper_for_set("set-zz"))
        self.assertIsNone(rr.load_keys_for_set("set-zz"))


class SetBScoringTests(unittest.TestCase):
    def setUp(self):
        self.paper = load_paper()
        self.keys = load_keys()
        self.official = official_from_keys(self.keys)

    def test_perfect_script_scores_40_band_9(self):
        result = rs.score_paper(
            {str(q): a for q, a in self.official.items()},
            mode="full",
            keys=self.keys,
            paper=self.paper,
        )
        self.assertEqual(result["score"], 40)
        self.assertEqual(result["total"], 40)
        self.assertEqual(result["band_estimate"], 9)
        self.assertTrue(all(row["ok"] for row in result["marking"]))

    def test_passage1_mode_marks_fourteen_questions(self):
        answers = {str(q): self.official[q] for q in range(1, 15)}
        result = rs.score_paper(answers, mode="passage1", keys=self.keys, paper=self.paper)
        self.assertEqual(result["total"], 14)
        self.assertEqual(result["score"], 14)
        self.assertIsNone(result["band_estimate"])
        self.assertEqual([row["q"] for row in result["marking"]], list(range(1, 15)))
        # Without the paper, passage1 remains the Set A range of 13.
        default = rs.score_paper(answers, mode="passage1", keys=self.keys)
        self.assertEqual(default["total"], 13)

    def test_word_limit_rejects_extra_words(self):
        answers = {str(q): a for q, a in self.official.items()}
        answers["19"] = "repeated visits each year"
        answers["38"] = "molecular hydrogen gas"
        result = rs.score_paper(answers, mode="full", keys=self.keys, paper=self.paper)
        by_q = {row["q"]: row for row in result["marking"]}
        self.assertFalse(by_q[19]["ok"])
        self.assertFalse(by_q[38]["ok"])
        self.assertEqual(result["score"], 38)

    def test_set_a_keys_do_not_mark_set_b_perfectly(self):
        result = rs.score_paper(
            {str(q): a for q, a in self.official.items()},
            mode="full",
            keys=rs.load_keys(),
            paper=self.paper,
        )
        self.assertLess(result["score"], 40)


class SetBRouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        appmod.DATA_DIR = base / "data"
        appmod.SUBMISSIONS_DIR = appmod.DATA_DIR / "submissions"
        appmod.INDEX_PATH = appmod.DATA_DIR / "index.json"
        accessmod.bind(appmod.DATA_DIR)
        appmod.ensure_storage()
        appmod.app.config["TESTING"] = True
        appmod.app.config["SECRET_KEY"] = "test-secret"
        self.client = appmod.app.test_client()
        self.official = official_from_keys(load_keys())

    def tearDown(self):
        self.tmp.cleanup()

    def _start(self, name="Test Candidate", code="TESTCODE1", mode="full"):
        accessmod.create_code(code=code)
        return self.client.post(
            "/api/session/start",
            json={
                "candidate_name": name,
                "invite_code": code,
                "module": "reading",
                "mode": mode,
            },
        )

    def test_paper_api_default_is_set_a_and_set_b_has_no_keys(self):
        self._start()
        default = self.client.get("/api/reading/paper")
        self.assertEqual(default.status_code, 200)
        self.assertEqual(default.get_json()["id"], "set-a")
        raw = default.get_data(as_text=True).lower()
        self.assertNotIn("explanation", raw)

        res = self.client.get("/api/reading/paper?set=set-b")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["id"], "set-b")
        self.assertEqual(len(data["passages"]), 3)
        self.assertEqual(len(data["groups"]), 7)
        body = res.get_data(as_text=True)
        lower = body.lower()
        self.assertNotIn("explanation", lower)
        self.assertNotIn("stem_keywords", lower)
        self.assertNotIn("correct_answer", lower)
        for label in ("题干关键词", "原文定位", "关键词替换", "判定点"):
            self.assertNotIn(label, body)
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lower)
        missing = self.client.get("/api/reading/paper?set=set-zz")
        self.assertEqual(missing.status_code, 404)

        listing = self.client.get("/api/reading/sets")
        self.assertEqual(listing.status_code, 200)
        ids = [item["id"] for item in listing.get_json()]
        self.assertEqual(ids, ["set-a", "set-b", "set-c", "set-d", "set-e"])

    def test_submit_uses_set_b_keys_and_ranges(self):
        self._start()
        res = self.client.post(
            "/api/reading/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "full",
                "prompt_set_id": "set-b",
                "answers": {str(q): a for q, a in self.official.items()},
                "duration_seconds": 3600,
                "time_remaining_seconds": 120,
                "time_used_seconds": 3480,
                "part_times": {"1": 700, "2": 1100, "3": 1680},
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["score"], 40)
        self.assertEqual(data["total"], 40)
        self.assertEqual(data["band_estimate"], 9)
        self.assertNotIn("marking", data)
        self.assertNotIn("explanation", res.get_data(as_text=True).lower())

        sid = data["id"]
        saved = json.loads((appmod.SUBMISSIONS_DIR / f"{sid}.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["prompt_set_id"], "set-b")
        self.assertEqual(saved["score"], 40)
        self.assertEqual(len(saved["marking"]), 40)

        # The same answers scored with Set A keys would not be a perfect paper,
        # but submit used the submission's prompt_set_id.
        wrong = rs.score_paper(
            saved["answers"],
            mode="full",
            keys=rs.load_keys(),
            paper=load_paper(),
        )
        self.assertLess(wrong["score"], 40)

        payload = appmod.attempt_review_payload(saved)
        self.assertEqual(payload["paper"]["id"], "set-b")
        self.assertEqual(len(payload["questions"]), 40)
        self.assertTrue(all(row.get("correct") for row in payload["questions"]))

    def test_submit_passage1_only_marks_fourteen(self):
        self._start(mode="passage1")
        res = self.client.post(
            "/api/reading/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "passage1",
                "prompt_set_id": "set-b",
                "answers": {str(q): self.official[q] for q in range(1, 15)},
                "duration_seconds": 1200,
                "time_used_seconds": 900,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["score"], 14)
        self.assertEqual(data["total"], 14)
        self.assertIsNone(data["band_estimate"])

    def test_setup_page_lists_set_b(self):
        page = self.client.get("/reading")
        self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        self.assertIn('value="set-b"', html)
        self.assertIn("Set B · Academic Reading", html)
        lower = html.lower()
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lower)



READING_LABELS = ("题干关键词：", "原文定位：", "关键词替换：", "判定点：")
READING_FIELDS = ("stem_keywords", "locate", "paraphrase", "judgment")
TRAP_RE = re.compile(r"不要误填|不要误选|不可填|不能选|不要选|不可选|不能填|不要填")

FROZEN_SET_B_ANSWERS = {
    1: "Liverpool",
    2: "dues",
    3: "landowners",
    4: "Parliament",
    5: "cuttings",
    6: "contractor",
    7: "TRUE",
    8: "FALSE",
    9: "NOT GIVEN",
    10: "TRUE",
    11: "FALSE",
    12: "NOT GIVEN",
    13: "FALSE",
    14: "TRUE",
    15: "history",
    16: "role",
    17: "review",
    18: "rely",
    19: "repeated visits",
    20: "outdoor activity",
    21: "amateur",
    22: "share credit",
    23: "A",
    24: "C",
    25: "A",
    26: "B",
    27: "D",
    28: "C",
    29: "H",
    30: "D",
    31: "G",
    32: "E",
    33: "C",
    34: "TRUE",
    35: "FALSE",
    36: "NOT GIVEN",
    37: "methane",
    38: "molecular hydrogen",
    39: "photochemical destruction",
    40: "reducing atmosphere",
}

FROZEN_SET_B_TYPES = {
    1: "notes",
    2: "notes",
    3: "notes",
    4: "notes",
    5: "notes",
    6: "notes",
    7: "tfng",
    8: "tfng",
    9: "tfng",
    10: "tfng",
    11: "tfng",
    12: "tfng",
    13: "tfng",
    14: "tfng",
    15: "summary",
    16: "summary",
    17: "summary",
    18: "summary",
    19: "summary",
    20: "summary",
    21: "summary",
    22: "summary",
    23: "matching_features",
    24: "matching_features",
    25: "matching_features",
    26: "matching_features",
    27: "matching_features",
    28: "matching_info",
    29: "matching_info",
    30: "matching_info",
    31: "matching_info",
    32: "matching_info",
    33: "matching_info",
    34: "tfng",
    35: "tfng",
    36: "tfng",
    37: "summary",
    38: "summary",
    39: "summary",
    40: "summary",
}


class SetBExplanationFormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys = load_keys()
        cls.questions = cls.keys["questions"]

    def test_answers_and_types_unchanged(self):
        self.assertEqual(self.keys.get("set_id"), "set-b")
        self.assertEqual(set(self.questions), {str(q) for q in range(1, 41)})
        for num, answer in FROZEN_SET_B_ANSWERS.items():
            meta = self.questions[str(num)]
            self.assertEqual(meta["answer"], answer, num)
            self.assertEqual(meta["type"], FROZEN_SET_B_TYPES[num], num)

    def test_each_item_has_structured_reading_parts(self):
        for num in range(1, 41):
            meta = self.questions[str(num)]
            for field in READING_FIELDS:
                self.assertTrue(str(meta.get(field) or "").strip(), f"Q{num} missing {field}")
            text = meta.get("explanation") or ""
            for label in READING_LABELS:
                self.assertIn(label, text, f"Q{num} explanation missing {label}")
            self.assertEqual(text, explain_format.compose_explanation(meta), num)
            self.assertTrue(explain_format.has_structured_parts(meta), num)
            parts = explain_format.explanation_parts(meta)
            for field in READING_FIELDS:
                self.assertEqual(parts.get(field), str(meta[field]).strip(), (num, field))
            self.assertNotIn("prediction", parts)

    def test_explanations_have_no_trap_phrases(self):
        for num in range(1, 41):
            meta = self.questions[str(num)]
            blob = "\n".join(
                [meta.get("explanation") or ""] + [str(meta.get(field) or "") for field in READING_FIELDS]
            )
            self.assertIsNone(TRAP_RE.search(blob), f"Q{num} still has a distractor warning")

    def test_explain_format_renders_four_chinese_labels(self):
        html = explain_format.explanation_html(self.questions["1"])
        self.assertIn('class="q-explain-parts"', html)
        for label in ("题干关键词", "原文定位", "关键词替换", "判定点"):
            self.assertIn(f'<h5 class="explain-label">{label}</h5>', html)
        self.assertIn("<strong>Liverpool</strong>", html)
        self.assertNotIn("**Liverpool**", html)
        # Must be structured blocks, not one escaped paragraph.
        self.assertFalse(html.startswith("<p>"))

        from_text = explain_format.explanation_html(self.questions["1"]["explanation"])
        self.assertIn('class="q-explain-parts"', from_text)
        self.assertIn("题干关键词", from_text)
        self.assertIn("判定点", from_text)

        xml = report_pdf.explanation_xml(self.questions["1"]["explanation"])
        for label in READING_LABELS:
            self.assertIn(label, xml)
        self.assertIn("<b>", xml)
        self.assertIn("<br/>", xml)
        self.assertNotIn("**Liverpool**", xml)

    def test_plain_explanation_still_falls_back_to_a_paragraph(self):
        html = explain_format.explanation_html("定位第三段，答案是 sand。")
        self.assertEqual(html, "<p>定位第三段，答案是 sand。</p>")
        self.assertNotIn("q-explain-parts", html)


if __name__ == "__main__":
    unittest.main()
