#!/usr/bin/env python3
"""Tests for Academic Reading Set D (P3 specialist practice, 42 questions)."""

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

PAPER_PATH = ROOT / "prompts" / "reading_set_d.json"
KEYS_PATH = ROOT / "prompts" / "reading_keys_set_d.json"

READING_LABELS = ("题干关键词：", "原文定位：", "关键词替换：", "判定点：")
READING_FIELDS = ("stem_keywords", "locate", "paraphrase", "judgment")
TRAP_RE = re.compile(r"不要误填|不要误选|不可填|不能选|不要选|不可选|不能填|不要填|干扰项")

# Teacher's official key, renumbered 1–42.
FROZEN_ANSWERS = {
    1: "C", 2: "A", 3: "B", 4: "A", 5: "C", 6: "B",
    7: "D", 8: "A", 9: "F", 10: "C",
    11: "C", 12: "B", 13: "D", 14: "A",
    15: "B", 16: "C", 17: "A", 18: "B", 19: "A", 20: "C",
    21: "E", 22: "B", 23: "D", 24: "F",
    25: "B", 26: "D", 27: "A", 28: "C",
    29: "B", 30: "A", 31: "C", 32: "B", 33: "A", 34: "C",
    35: "C", 36: "E", 37: "B", 38: "F",
    39: "D", 40: "C", 41: "A", 42: "B",
}

TITLES = {
    1: "Who should own an orchestra’s sound?",
    2: "What a repair should show",
    3: "Can the countryside afford darkness?",
}

P_HEADINGS = {
    1: {
        "What should a hall make audible?",
        "Who should choose the settings?",
        "What would count as improvement?",
    },
    2: {
        "What survives in a repaired object?",
        "Should the new parts stand out?",
        "How should a repair be assessed?",
    },
    3: {
        "What exactly is being restored?",
        "How should a trial be arranged?",
        "What would justify expansion?",
    },
}

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


def load_paper() -> dict:
    return json.loads(PAPER_PATH.read_text(encoding="utf-8"))


def load_keys() -> dict:
    return json.loads(KEYS_PATH.read_text(encoding="utf-8"))


def official_from_keys(keys: dict) -> dict[int, str]:
    return {int(q): meta["answer"] for q, meta in keys["questions"].items()}


def passage_body_text(passage: dict) -> str:
    parts = []
    for para in passage.get("paragraphs") or []:
        if isinstance(para, dict):
            continue
        parts.append(str(para))
    return " ".join(parts)


class SetDPaperTests(unittest.TestCase):
    def setUp(self):
        self.paper = load_paper()
        self.keys = load_keys()

    def test_paper_identity_and_shape(self):
        self.assertEqual(self.paper["id"], "set-d")
        self.assertEqual(self.paper["title"], "Set D · P3 高阶专项练习")
        self.assertEqual(self.paper["subtitle"], "Academic Reading")
        self.assertIn("instructions", self.paper)
        self.assertEqual(self.paper["instructions"]["time"], "1 hour")
        info = " ".join(self.paper["instructions"]["information"])
        self.assertIn("42 questions", info)
        self.assertIn("one mark", info)
        self.assertEqual(len(self.paper["passages"]), 3)
        self.assertEqual(len(self.paper["groups"]), 9)

    def test_forty_two_unique_questions_and_ranges(self):
        nums: list[int] = []
        expected = [
            ("q1-6", "matching_features", 1, 1, 6),
            ("q7-10", "matching_endings", 1, 7, 10),
            ("q11-14", "mcq", 1, 11, 14),
            ("q15-20", "matching_features", 2, 15, 20),
            ("q21-24", "matching_endings", 2, 21, 24),
            ("q25-28", "mcq", 2, 25, 28),
            ("q29-34", "matching_features", 3, 29, 34),
            ("q35-38", "matching_endings", 3, 35, 38),
            ("q39-42", "mcq", 3, 39, 42),
        ]
        for group, (gid, gtype, passage, lo, hi) in zip(self.paper["groups"], expected, strict=True):
            self.assertEqual(group["id"], gid)
            self.assertEqual(group["type"], gtype)
            self.assertEqual(group["passage"], passage)
            self.assertEqual(group["from"], lo)
            self.assertEqual(group["to"], hi)
            nums.extend(range(lo, hi + 1))
        self.assertEqual(nums, list(range(1, 43)))
        self.assertEqual(len(set(nums)), 42)

    def test_titles_headings_and_not_lettered(self):
        for passage in self.paper["passages"]:
            self.assertEqual(passage["title"], TITLES[passage["id"]])
            self.assertFalse(bool(passage.get("lettered")))
            self.assertEqual(passage["label"], f"READING PASSAGE {passage['id']}")
            headings = [p.get("heading") for p in passage["paragraphs"] if isinstance(p, dict)]
            self.assertEqual(set(headings), P_HEADINGS[passage["id"]])
            self.assertEqual(len(headings), 3)
            body = [p for p in passage["paragraphs"] if isinstance(p, str)]
            self.assertEqual(len(body), 9)
            self.assertGreater(len(passage_body_text(passage).split()), 500)
            lo, hi = {1: (1, 14), 2: (15, 28), 3: (29, 42)}[passage["id"]]
            self.assertIn(f"Questions {lo}–{hi}", passage["time_guidance"])
            self.assertIn(f"Reading Passage {passage['id']}", passage["time_guidance"])

    def test_student_json_has_no_keys_or_official_names(self):
        dumped = json.dumps(self.paper)
        self.assertNotRegex(dumped, r'"explanation"\s*:')
        self.assertNotIn("correct_answer", dumped)
        self.assertNotRegex(dumped, r'"answer"\s*:')
        self.assertNotIn("stem_keywords", dumped)
        lower = dumped.lower()
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lower, word)
        for path in STUDENT_PATHS:
            text = path.read_text(encoding="utf-8").lower()
            for word in FORBIDDEN_OFFICIAL:
                self.assertNotIn(word, text, f"{word!r} in {path}")

    def test_typography_from_source(self):
        dumped = json.dumps(self.paper, ensure_ascii=False)
        self.assertIn("orchestra’s", dumped)
        self.assertIn("listener's grasp", dumped)
        self.assertIn("changes of colour", dumped)
        self.assertIn("beginning ‘A display could’ and ‘Conversely’", dumped)

    def test_choice_answers_are_valid(self):
        questions = self.keys["questions"]
        for group in self.paper["groups"]:
            for q in range(group["from"], group["to"] + 1):
                meta = questions[str(q)]
                self.assertEqual(meta["type"], group["type"])
                answer = meta["answer"]
                if group["type"] == "matching_features":
                    self.assertIn(answer, group["options"])
                elif group["type"] == "matching_endings":
                    self.assertIn(answer, group["endings"])
                elif group["type"] == "mcq":
                    item = next(i for i in group["items"] if i["q"] == q)
                    self.assertIn(answer, item["options"])

    def test_keys_match_teacher_key_and_have_four_fields(self):
        self.assertEqual(self.keys["set_id"], "set-d")
        questions = self.keys["questions"]
        self.assertEqual(sorted(int(q) for q in questions), list(range(1, 43)))
        for num, answer in FROZEN_ANSWERS.items():
            meta = questions[str(num)]
            self.assertEqual(meta["answer"], answer, num)
            self.assertTrue(meta.get("type"), num)
            for field in READING_FIELDS:
                self.assertTrue(str(meta.get(field) or "").strip(), f"Q{num} missing {field}")
            text = meta.get("explanation") or ""
            for label in READING_LABELS:
                self.assertIn(label, text, f"Q{num} explanation missing {label}")
            self.assertEqual(text, explain_format.compose_explanation(meta), num)
            self.assertTrue(re.search(r"[\u4e00-\u9fff]", text), num)
            blob = "\n".join([text] + [str(meta.get(field) or "") for field in READING_FIELDS])
            self.assertIsNone(TRAP_RE.search(blob), f"Q{num} still has a distractor warning")

    def test_helpers_load_set_d(self):
        paper = rr.load_paper_for_set("set-d")
        keys = rr.load_keys_for_set("set-d")
        self.assertIsNotNone(paper)
        self.assertEqual(paper["id"], "set-d")
        self.assertEqual(keys["set_id"], "set-d")
        self.assertEqual(len(keys["questions"]), 42)
        self.assertEqual(rr.keys_path_for_set("set-a"), rs.KEYS_PATH)
        self.assertEqual(rr.keys_path_for_set("set-d"), KEYS_PATH)
        ids = [item["id"] for item in rr.list_reading_sets()]
        self.assertEqual(ids, ["set-a", "set-b", "set-c", "set-d"])
        html = rr.official_passage_html(paper["passages"][0])
        self.assertIn('class="passage-subheading"', html)
        self.assertIn("What should a hall make audible?", html)
        self.assertNotIn("{", html)

    def test_setup_html_and_js_ranges_include_set_d(self):
        html = (ROOT / "templates" / "reading.html").read_text(encoding="utf-8")
        js = (ROOT / "static" / "reading.js").read_text(encoding="utf-8")
        self.assertIn('value="set-d"', html)
        self.assertIn("Set D · P3 高阶专项练习", html)
        self.assertIn('"set-d"', js)
        self.assertIn("full: [1, 42]", js)
        self.assertIn("passage1: [1, 14]", js)
        self.assertIn("passage2: [15, 28]", js)
        self.assertIn("passage3: [29, 42]", js)
        self.assertIn("fullLo", js)
        self.assertNotIn("reading-theme-d", js)
        self.assertNotIn("reading-theme-c", html)
        # Theme remains gated to set-c only.
        self.assertIn('id === "set-c"', js)


class SetDScoringTests(unittest.TestCase):
    def setUp(self):
        self.paper = load_paper()
        self.keys = load_keys()
        self.official = official_from_keys(self.keys)

    def test_modes_for_paper_cover_forty_two(self):
        modes = rs.modes_for_paper(self.paper)
        self.assertEqual(modes["full"]["questions"], list(range(1, 43)))
        self.assertEqual(modes["full"]["seconds"], 60 * 60)
        self.assertEqual(modes["passage1"]["questions"], list(range(1, 15)))
        self.assertEqual(modes["passage2"]["questions"], list(range(15, 29)))
        self.assertEqual(modes["passage3"]["questions"], list(range(29, 43)))
        for key in ("passage1", "passage2", "passage3"):
            self.assertEqual(modes[key]["seconds"], 20 * 60)
        default = rs.modes_for_paper(None)
        self.assertEqual(default["full"]["questions"], list(range(1, 41)))

    def test_perfect_script_scores_42_band_9(self):
        result = rs.score_paper(
            {str(q): a for q, a in self.official.items()},
            mode="full",
            keys=self.keys,
            paper=self.paper,
        )
        self.assertEqual(result["score"], 42)
        self.assertEqual(result["total"], 42)
        self.assertEqual(result["band_estimate"], 9.0)
        self.assertTrue(all(row["ok"] for row in result["marking"]))
        self.assertEqual(rs.band_for_score(42, 42), 9.0)
        self.assertEqual(rs.band_for_score(40, 40), 9.0)
        self.assertEqual(rs.band_for_score(39, 40), 9.0)
        self.assertIsNone(rs.band_for_score(14, 14))

    def test_forty_question_paper_banding_unchanged(self):
        set_a = rs.load_paper()
        keys_a = rs.load_keys()
        official_a = rs.official_answers(keys_a)
        result = rs.score_paper(
            {str(q): a for q, a in official_a.items()},
            mode="full",
            keys=keys_a,
            paper=set_a,
        )
        self.assertEqual(result["score"], 40)
        self.assertEqual(result["total"], 40)
        self.assertEqual(result["band_estimate"], 9.0)
        self.assertEqual(rs.modes_for_paper(set_a)["full"]["questions"], list(range(1, 41)))

    def test_passage_modes_are_unbanded(self):
        answers = {str(q): self.official[q] for q in range(1, 15)}
        result = rs.score_paper(answers, mode="passage1", keys=self.keys, paper=self.paper)
        self.assertEqual(result["total"], 14)
        self.assertEqual(result["score"], 14)
        self.assertIsNone(result["band_estimate"])
        self.assertEqual([row["q"] for row in result["marking"]], list(range(1, 15)))

    def test_set_a_letter_does_not_mark_a_different_set_d_item(self):
        # Set A Q28 is A; Set D Q28 is C. The same letter must not be marked
        # correct just because it coincides on another question.
        answers = {str(q): a for q, a in self.official.items()}
        answers["28"] = "A"
        result = rs.score_paper(answers, mode="full", keys=self.keys, paper=self.paper)
        by_q = {row["q"]: row for row in result["marking"]}
        self.assertFalse(by_q[28]["ok"])
        self.assertEqual(by_q[28]["correct"], "C")
        self.assertEqual(result["score"], 41)
        set_a_keys = rs.load_keys()
        crossed = rs.score_paper(
            {str(q): a for q, a in rs.official_answers(set_a_keys).items()},
            mode="full",
            keys=self.keys,
            paper=self.paper,
        )
        self.assertLess(crossed["score"], 42)
        self.assertFalse(next(row for row in crossed["marking"] if row["q"] == 28)["ok"])


class SetDRouteTests(unittest.TestCase):
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

    def test_unauthenticated_paper_api_is_403(self):
        denied = self.client.get("/api/reading/paper?set=set-d")
        self.assertEqual(denied.status_code, 403)

    def test_paper_api_set_d_has_no_keys(self):
        self._start()
        res = self.client.get("/api/reading/paper?set=set-d")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["id"], "set-d")
        self.assertEqual(len(data["passages"]), 3)
        self.assertEqual(len(data["groups"]), 9)
        body = res.get_data(as_text=True)
        self.assertNotRegex(body, r'"explanation"\s*:')
        self.assertNotIn("correct_answer", body)
        self.assertNotIn("stem_keywords", body)
        for label in ("题干关键词", "原文定位", "关键词替换", "判定点"):
            self.assertNotIn(label, body)
        lower = body.lower()
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lower)

        listing = self.client.get("/api/reading/sets")
        self.assertEqual(listing.status_code, 200)
        ids = [item["id"] for item in listing.get_json()]
        self.assertEqual(ids, ["set-a", "set-b", "set-c", "set-d"])

    def test_submit_uses_set_d_keys_and_ranges(self):
        self._start()
        res = self.client.post(
            "/api/reading/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "full",
                "prompt_set_id": "set-d",
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
        self.assertEqual(data["score"], 42)
        self.assertEqual(data["total"], 42)
        self.assertEqual(data["band_estimate"], 9)
        self.assertNotIn("marking", data)
        self.assertNotIn("explanation", res.get_data(as_text=True).lower())

        sid = data["id"]
        saved = json.loads((appmod.SUBMISSIONS_DIR / f"{sid}.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["prompt_set_id"], "set-d")
        self.assertEqual(saved["score"], 42)
        self.assertEqual(len(saved["marking"]), 42)

        payload = appmod.attempt_review_payload(saved)
        self.assertEqual(payload["paper"]["id"], "set-d")
        self.assertEqual(len(payload["questions"]), 42)
        self.assertTrue(all(row.get("correct") for row in payload["questions"]))

    def test_submit_set_a_answer_does_not_mark_set_d_item(self):
        self._start()
        answers = {str(q): a for q, a in self.official.items()}
        answers["28"] = "A"  # Set A Q28; Set D Q28 is C
        res = self.client.post(
            "/api/reading/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "full",
                "prompt_set_id": "set-d",
                "answers": answers,
                "duration_seconds": 3600,
                "time_used_seconds": 3500,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["score"], 41)
        self.assertEqual(data["total"], 42)
        saved = json.loads(
            (appmod.SUBMISSIONS_DIR / f"{data['id']}.json").read_text(encoding="utf-8")
        )
        self.assertEqual(saved["prompt_set_id"], "set-d")
        by_q = {row["q"]: row for row in saved["marking"]}
        self.assertFalse(by_q[28]["ok"])
        self.assertEqual(by_q[28]["correct"], "C")

    def test_submit_passage1_only_marks_fourteen(self):
        self._start(mode="passage1")
        res = self.client.post(
            "/api/reading/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "passage1",
                "prompt_set_id": "set-d",
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

    def test_setup_page_lists_set_d(self):
        page = self.client.get("/reading")
        self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        self.assertIn('value="set-d"', html)
        self.assertIn("Set D · P3 高阶专项练习", html)
        self.assertNotIn("reading-theme-c", html)
        lower = html.lower()
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lower)


if __name__ == "__main__":
    unittest.main()
