#!/usr/bin/env python3
"""Unit and smoke tests for Academic Reading marking and routes."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import reading_scoring as rs  # noqa: E402
import app as appmod  # noqa: E402

OFFICIAL = {
    1: "sand",
    2: "blood",
    3: "coat",
    4: "horns",
    5: "habitat",
    6: "routes",
    7: "oases",
    8: "FALSE",
    9: "FALSE",
    10: "TRUE",
    11: "NOT GIVEN",
    12: "TRUE",
    13: "NOT GIVEN",
    14: "NOT GIVEN",
    15: "FALSE",
    16: "NOT GIVEN",
    17: "TRUE",
    18: "FALSE",
    19: "lanes",
    20: "boarding",
    21: "wheelchairs",
    22: "fuel",
    23: "flood",
    24: "smartcards",
    25: "gates",
    26: "queues",
    27: "A",
    28: "A",
    29: "D",
    30: "A",
    31: "E",
    32: "F",
    33: "D",
    34: "B",
    35: "NO",
    36: "NOT GIVEN",
    37: "NOT GIVEN",
    38: "YES",
    39: "YES",
    40: "NO",
}

FORBIDDEN = ("saiga", "dar es salaam", "解析", "saving the saiga")

STUDENT_PATHS = [
    ROOT / "prompts" / "reading_set_a.json",
    ROOT / "templates" / "reading.html",
    ROOT / "templates" / "hub.html",
    ROOT / "static" / "reading.js",
    ROOT / "static" / "reading.css",
]


class ScoringTests(unittest.TestCase):
    def test_stored_keys_match_official_paper(self):
        stored = rs.official_answers()
        self.assertEqual(set(stored), set(OFFICIAL))
        self.assertEqual(stored, OFFICIAL)

    def test_perfect_key_scores_40_band_9(self):
        result = rs.score_paper({str(q): a for q, a in OFFICIAL.items()}, mode="full")
        self.assertEqual(result["score"], 40)
        self.assertEqual(result["total"], 40)
        self.assertEqual(result["band_estimate"], 9)
        self.assertTrue(all(row["ok"] for row in result["marking"]))

    def test_blank_paper_scores_zero(self):
        result = rs.score_paper({}, mode="full")
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["total"], 40)
        self.assertEqual(result["band_estimate"], 0)
        self.assertTrue(all(not row["ok"] for row in result["marking"]))

        blankish = {str(q): "   " for q in range(1, 41)}
        result2 = rs.score_paper(blankish, mode="full")
        self.assertEqual(result2["score"], 0)

    def test_case_and_alias_variants(self):
        answers = {
            1: "SAND",
            2: " Blood ",
            3: '"coat"',
            8: "false",
            9: "F",
            10: "True",
            11: "NG",
            12: "T",
            13: "NOTGIVEN",
            24: "Smartcards",
            27: "a",
            35: "n",
            38: "y",
            36: "not given",
        }
        result = rs.score_paper(answers, mode="full")
        by_q = {row["q"]: row for row in result["marking"]}
        for q in answers:
            self.assertTrue(by_q[q]["ok"], f"Q{q} should be correct, got {by_q[q]}")

    def test_no_fuzzy_spelling_on_notes(self):
        result = rs.score_paper({1: "sands", 2: "bloood", 24: "smart cards"}, mode="full")
        by_q = {row["q"]: row for row in result["marking"]}
        self.assertFalse(by_q[1]["ok"])
        self.assertFalse(by_q[2]["ok"])
        self.assertFalse(by_q[24]["ok"])

    def test_tf_not_accepted_for_ynng(self):
        result = rs.score_paper({35: "FALSE", 38: "TRUE"}, mode="full")
        by_q = {row["q"]: row for row in result["marking"]}
        self.assertFalse(by_q[35]["ok"])
        self.assertFalse(by_q[38]["ok"])

    def test_single_passage_has_no_band(self):
        answers = {str(q): OFFICIAL[q] for q in range(1, 14)}
        result = rs.score_paper(answers, mode="passage1")
        self.assertEqual(result["score"], 13)
        self.assertEqual(result["total"], 13)
        self.assertIsNone(result["band_estimate"])

    def test_band_table_samples(self):
        self.assertEqual(rs.band_for_score(39), 9.0)
        self.assertEqual(rs.band_for_score(37), 8.5)
        self.assertEqual(rs.band_for_score(30), 7.0)
        self.assertEqual(rs.band_for_score(23), 6.0)
        self.assertEqual(rs.band_for_score(0, 13), None)


class LeakTests(unittest.TestCase):
    def test_student_files_have_no_teacher_material(self):
        for path in STUDENT_PATHS:
            self.assertTrue(path.exists(), path)
            text = path.read_text(encoding="utf-8")
            lower = text.lower()
            for word in FORBIDDEN:
                self.assertNotIn(word, lower, f"{word!r} found in {path}")
            self.assertNotIn("教师用", text)
            self.assertNotIn("ANSWER KEY", text)

        paper = json.loads((ROOT / "prompts" / "reading_set_a.json").read_text(encoding="utf-8"))
        dumped = json.dumps(paper)
        self.assertNotIn("explanation", dumped)
        self.assertNotIn("correct_answer", dumped)
        # Structured key list must not be present
        self.assertNotIn('"answer": "sand"', dumped)

    def test_passage_word_counts(self):
        paper = rs.load_paper()
        titles = {1: "Saving the addax", 2: "The problems of getting around the city of Ibadan", 3: "Rethinking Early Cities"}
        expected = {1: 908, 2: 891, 3: 1040}
        for p in paper["passages"]:
            words = " ".join(p["paragraphs"]).split()
            self.assertEqual(p["title"], titles[p["id"]])
            self.assertEqual(len(words), expected[p["id"]], p["title"])


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        appmod.DATA_DIR = base / "data"
        appmod.SUBMISSIONS_DIR = appmod.DATA_DIR / "submissions"
        appmod.INDEX_PATH = appmod.DATA_DIR / "index.json"
        appmod.ensure_storage()
        appmod.app.config["TESTING"] = True
        appmod.app.config["SECRET_KEY"] = "test-secret"
        self.client = appmod.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_health_and_pages(self):
        h = self.client.get("/health")
        self.assertEqual(h.status_code, 200)
        body = h.get_json()
        self.assertTrue(body["ok"])
        self.assertIn("reading", body["modules"])

        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        html = home.get_data(as_text=True)
        self.assertIn("/reading", html)
        self.assertIn("/writing", html)
        self.assertNotIn("Start your writing test", html)

        writing = self.client.get("/writing")
        self.assertEqual(writing.status_code, 200)
        self.assertIn("Start your writing test", writing.get_data(as_text=True))

        reading = self.client.get("/reading")
        self.assertEqual(reading.status_code, 200)
        page = reading.get_data(as_text=True)
        self.assertIn("Start your reading test", page)
        self.assertIn("Saving the addax", page)
        lower = page.lower()
        for word in FORBIDDEN:
            self.assertNotIn(word, lower)
        self.assertNotIn("教师用", page)
        # Student page must not embed the teacher key table / explanations
        self.assertNotIn("参考分数", page)
        self.assertNotIn('"answer": "sand"', page)

    def test_student_paper_api_has_no_keys(self):
        res = self.client.get("/api/reading/paper")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["id"], "set-a")
        raw = res.get_data(as_text=True).lower()
        for word in FORBIDDEN:
            self.assertNotIn(word, raw)
        self.assertNotIn("explanation", raw)
        self.assertEqual(len(data["passages"]), 3)
        self.assertEqual(len(data["groups"]), 7)

    def test_submit_requires_name(self):
        res = self.client.post(
            "/api/reading/submit",
            json={"mode": "full", "answers": {"1": "sand"}},
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["ok"])

    def test_submit_success_does_not_return_score(self):
        res = self.client.post(
            "/api/reading/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "full",
                "prompt_set_id": "set-a",
                "answers": {str(q): a for q, a in OFFICIAL.items()},
                "duration_seconds": 3600,
                "time_remaining_seconds": 120,
                "time_used_seconds": 3480,
                "auto_submitted": False,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("id", data)
        self.assertNotIn("score", data)
        self.assertNotIn("band_estimate", data)
        self.assertNotIn("marking", data)

        sid = data["id"]
        saved = json.loads((appmod.SUBMISSIONS_DIR / f"{sid}.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["module"], "reading")
        self.assertEqual(saved["score"], 40)
        self.assertEqual(saved["band_estimate"], 9)
        self.assertEqual(saved["total"], 40)

        index = json.loads(appmod.INDEX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(index["submissions"][0]["module"], "reading")
        self.assertEqual(index["submissions"][0]["score"], 40)

    def test_writing_submit_still_works(self):
        res = self.client.post(
            "/api/submit",
            json={
                "candidate_name": "Writer",
                "mode": "task1",
                "prompt_set_id": "set-a",
                "task1_text": "hello world",
                "task2_text": "",
                "duration_seconds": 1200,
                "time_remaining_seconds": 10,
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["ok"])
        # missing name still 400
        bad = self.client.post("/api/submit", json={"task1_text": "x"})
        self.assertEqual(bad.status_code, 400)


if __name__ == "__main__":
    unittest.main()
