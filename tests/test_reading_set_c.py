#!/usr/bin/env python3
"""Tests for Academic Reading Set C and table / choose-two support."""

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
import reading_review as rr  # noqa: E402
import reading_scoring as rs  # noqa: E402

PAPER_PATH = ROOT / "prompts" / "reading_set_c.json"
KEYS_PATH = ROOT / "prompts" / "reading_keys_set_c.json"

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
    1: (700, 760),
    2: (680, 750),
    3: (790, 860),
}

TITLES = {
    1: "The cooling power of city trees",
    2: "The public grain houses of Lestow",
    3: "What should a public archive forget?",
}

P3_HEADINGS = {
    "What changes when a record goes online?",
    "Should an archive respond to requests for removal?",
    "How should the policy be judged?",
}


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


def word_limit_from_group(group: dict) -> int | None:
    return rs.word_limit_from_instructions(group.get("instructions"))


class SetCPaperTests(unittest.TestCase):
    def setUp(self):
        self.paper = load_paper()
        self.keys = load_keys()

    def test_paper_identity_and_shape(self):
        self.assertEqual(self.paper["id"], "set-c")
        self.assertEqual(self.paper["title"], "Set C")
        self.assertEqual(self.paper["subtitle"], "Academic Reading")
        self.assertIn("instructions", self.paper)
        self.assertEqual(len(self.paper["passages"]), 3)
        self.assertEqual(len(self.paper["groups"]), 9)

    def test_forty_unique_questions_and_ranges(self):
        nums: list[int] = []
        expected = [
            ("q1-6", "table", 1, 1, 6),
            ("q7-13", "tfng", 1, 7, 13),
            ("q14-19", "matching_info", 2, 14, 19),
            ("q20-23", "summary", 2, 20, 23),
            ("q24-25", "choose_two", 2, 24, 25),
            ("q26", "mcq", 2, 26, 26),
            ("q27-32", "matching_features", 3, 27, 32),
            ("q33-36", "matching_endings", 3, 33, 36),
            ("q37-40", "mcq", 3, 37, 40),
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

    def test_titles_word_counts_and_passage_structure(self):
        for passage in self.paper["passages"]:
            words = passage_body_text(passage).split()
            lo, hi = WORD_RANGES[passage["id"]]
            self.assertEqual(passage["title"], TITLES[passage["id"]])
            self.assertTrue(
                lo <= len(words) <= hi,
                f"{passage['title']}: {len(words)} not in {lo}–{hi}",
            )
            if passage["id"] == 2:
                self.assertTrue(passage.get("lettered"))
                self.assertEqual(len(passage["paragraphs"]), 6)
                self.assertTrue(all(isinstance(p, str) for p in passage["paragraphs"]))
            else:
                self.assertFalse(bool(passage.get("lettered")))
            if passage["id"] == 1:
                self.assertEqual(len(passage["paragraphs"]), 7)
            if passage["id"] == 3:
                headings = [
                    p.get("heading")
                    for p in passage["paragraphs"]
                    if isinstance(p, dict)
                ]
                self.assertEqual(set(headings), P3_HEADINGS)
                self.assertEqual(len(headings), 3)
                body = [p for p in passage["paragraphs"] if isinstance(p, str)]
                self.assertEqual(len(body), 11)

    def test_student_json_has_no_keys_or_official_names(self):
        dumped = json.dumps(self.paper)
        self.assertNotRegex(dumped, r'"explanation"\s*:')
        self.assertNotIn("correct_answer", dumped)
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
        by_passage = {p["id"]: passage_body_text(p) for p in self.paper["passages"]}
        for group in self.paper["groups"]:
            if group["type"] not in {"notes", "summary", "table"}:
                continue
            limit = word_limit_from_group(group)
            self.assertIsNotNone(limit, group["id"])
            source = by_passage[group["passage"]]
            for q in range(group["from"], group["to"] + 1):
                answer = questions[str(q)]["answer"]
                self.assertLessEqual(len(answer.split()), limit, q)
                self.assertEqual(len(answer.split()), 1, q)
                self.assertIsNotNone(
                    re.search(r"(?i)\b" + re.escape(answer) + r"\b", source),
                    f"Q{q} {answer!r} not in passage {group['passage']}",
                )

    def test_choice_answers_are_valid(self):
        questions = self.keys["questions"]
        tfng_vals = {"TRUE", "FALSE", "NOT GIVEN"}
        tfng_seen: set[str] = set()
        endings = None
        features = None
        choose_two = None
        for group in self.paper["groups"]:
            if group["type"] == "matching_endings":
                endings = group["endings"]
            if group["type"] == "matching_features":
                features = group["options"]
            if group["type"] == "choose_two":
                choose_two = group
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
                    self.assertRegex(answer, r"^[A-F]$")
                elif group["type"] == "matching_endings":
                    self.assertIn(answer, group["endings"])
                elif group["type"] == "mcq":
                    item = next(i for i in group["items"] if i["q"] == q)
                    self.assertIn(answer, item["options"])
                elif group["type"] == "choose_two":
                    self.assertIn(answer, group["options"])
        self.assertEqual(tfng_seen, tfng_vals)
        self.assertIsNotNone(endings)
        self.assertIsNotNone(features)
        self.assertEqual({questions["24"]["answer"], questions["25"]["answer"]}, {"B", "C"})
        self.assertEqual(questions["24"].get("pair"), [24, 25])
        self.assertEqual(questions["25"].get("pair"), [24, 25])
        self.assertIsNotNone(choose_two)

    def test_keys_have_forty_chinese_explanations(self):
        self.assertEqual(self.keys["set_id"], "set-c")
        questions = self.keys["questions"]
        self.assertEqual(sorted(int(q) for q in questions), list(range(1, 41)))
        for q, meta in questions.items():
            expl = meta.get("explanation") or ""
            self.assertTrue(expl, q)
            self.assertTrue(meta.get("answer"), q)
            self.assertTrue(meta.get("type"), q)
            self.assertTrue(re.search(r"[\u4e00-\u9fff]", expl), q)

    def test_helpers_load_set_c(self):
        paper = rr.load_paper_for_set("set-c")
        keys = rr.load_keys_for_set("set-c")
        self.assertIsNotNone(paper)
        self.assertEqual(paper["id"], "set-c")
        self.assertEqual(keys["set_id"], "set-c")
        self.assertEqual(len(keys["questions"]), 40)
        self.assertEqual(rr.keys_path_for_set("set-a"), rs.KEYS_PATH)
        self.assertEqual(rr.keys_path_for_set("set-c"), KEYS_PATH)
        ids = [item["id"] for item in rr.list_reading_sets()]
        self.assertEqual(ids, ["set-a", "set-b", "set-c", "set-d"])
        html = rr.official_passage_html(paper["passages"][2])
        self.assertIn('class="passage-subheading"', html)
        self.assertIn("What changes when a record goes online?", html)
        self.assertNotIn("{", html)

    def test_set_c_theme_is_scoped(self):
        css = (ROOT / "static" / "reading.css").read_text(encoding="utf-8")
        js = (ROOT / "static" / "reading.js").read_text(encoding="utf-8")
        html = (ROOT / "templates" / "reading.html").read_text(encoding="utf-8")
        self.assertIn(".reading-theme-c", css)
        self.assertIn("body.reading-page.reading-theme-c", css)
        self.assertIn("#f4faf7", css)
        self.assertIn("#5aae8a", css)
        self.assertGreater(css.count("reading-theme-c"), 8)
        self.assertIn("reading-theme-c", js)
        self.assertIn('id === "set-c"', js)
        self.assertIn("applyReadingTheme", js)
        self.assertIn("set-c", js)
        self.assertIn('value="set-c"', html)
        # Theme class is applied in JS for set-c only, not hardcoded on the page root.
        self.assertNotIn("reading-theme-c", html)


class SetCScoringTests(unittest.TestCase):
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

    def test_passage1_mode_marks_thirteen_questions(self):
        answers = {str(q): self.official[q] for q in range(1, 14)}
        result = rs.score_paper(answers, mode="passage1", keys=self.keys, paper=self.paper)
        self.assertEqual(result["total"], 13)
        self.assertEqual(result["score"], 13)
        self.assertIsNone(result["band_estimate"])
        self.assertEqual([row["q"] for row in result["marking"]], list(range(1, 14)))
        default = rs.score_paper(answers, mode="passage1", keys=self.keys)
        self.assertEqual(default["total"], 13)

    def test_word_limit_rejects_extra_words_on_table_and_summary(self):
        answers = {str(q): a for q, a in self.official.items()}
        answers["1"] = "city surfaces"
        answers["20"] = "raised platforms"
        result = rs.score_paper(answers, mode="full", keys=self.keys, paper=self.paper)
        by_q = {row["q"]: row for row in result["marking"]}
        self.assertFalse(by_q[1]["ok"])
        self.assertFalse(by_q[20]["ok"])
        self.assertEqual(result["score"], 38)

    def test_choose_two_either_order_and_partial_credit(self):
        def mark(a24, a25):
            answers = {str(q): a for q, a in self.official.items()}
            answers["24"] = a24
            answers["25"] = a25
            result = rs.score_paper(answers, mode="full", keys=self.keys, paper=self.paper)
            by_q = {row["q"]: row for row in result["marking"]}
            return int(by_q[24]["ok"]) + int(by_q[25]["ok"]), by_q

        score, by_q = mark("B", "C")
        self.assertEqual(score, 2)
        self.assertEqual(by_q[24]["correct"], "B, C")
        self.assertEqual(by_q[25]["correct"], "B, C")

        score, _ = mark("C", "B")
        self.assertEqual(score, 2)

        score, by_q = mark("B", "D")
        self.assertEqual(score, 1)
        self.assertTrue(by_q[24]["ok"])
        self.assertFalse(by_q[25]["ok"])

        score, _ = mark("D", "E")
        self.assertEqual(score, 0)

        score, by_q = mark("B", "B")
        self.assertEqual(score, 1)
        self.assertTrue(by_q[24]["ok"])
        self.assertFalse(by_q[25]["ok"])

    def test_set_a_keys_do_not_mark_set_c_perfectly(self):
        result = rs.score_paper(
            {str(q): a for q, a in self.official.items()},
            mode="full",
            keys=rs.load_keys(),
            paper=self.paper,
        )
        self.assertLess(result["score"], 40)


class SetCRouteTests(unittest.TestCase):
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

    def test_paper_api_set_c_has_no_keys(self):
        self._start()
        res = self.client.get("/api/reading/paper?set=set-c")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["id"], "set-c")
        self.assertEqual(len(data["passages"]), 3)
        self.assertEqual(len(data["groups"]), 9)
        body = res.get_data(as_text=True)
        self.assertNotRegex(body, r'"explanation"\s*:')
        self.assertNotIn("correct_answer", body)
        lower = body.lower()
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lower)

        listing = self.client.get("/api/reading/sets")
        self.assertEqual(listing.status_code, 200)
        ids = [item["id"] for item in listing.get_json()]
        self.assertEqual(ids, ["set-a", "set-b", "set-c", "set-d"])

    def test_submit_uses_set_c_keys_and_ranges(self):
        self._start()
        res = self.client.post(
            "/api/reading/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "full",
                "prompt_set_id": "set-c",
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
        self.assertEqual(saved["prompt_set_id"], "set-c")
        self.assertEqual(saved["score"], 40)
        self.assertEqual(len(saved["marking"]), 40)
        by_q = {row["q"]: row for row in saved["marking"]}
        self.assertEqual(by_q[24]["correct"], "B, C")
        self.assertEqual(by_q[25]["correct"], "B, C")

        payload = appmod.attempt_review_payload(saved)
        self.assertEqual(payload["paper"]["id"], "set-c")
        self.assertEqual(len(payload["questions"]), 40)
        self.assertTrue(all(row.get("correct") for row in payload["questions"]))

    def test_submit_passage1_only_marks_thirteen(self):
        self._start(mode="passage1")
        res = self.client.post(
            "/api/reading/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "passage1",
                "prompt_set_id": "set-c",
                "answers": {str(q): self.official[q] for q in range(1, 14)},
                "duration_seconds": 1200,
                "time_used_seconds": 900,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["score"], 13)
        self.assertEqual(data["total"], 13)
        self.assertIsNone(data["band_estimate"])

    def test_setup_page_lists_set_c(self):
        page = self.client.get("/reading")
        self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        self.assertIn('value="set-c"', html)
        self.assertIn("Set C · Academic Reading", html)
        self.assertNotIn("reading-theme-c", html)
        lower = html.lower()
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lower)


if __name__ == "__main__":
    unittest.main()
