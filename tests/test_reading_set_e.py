#!/usr/bin/env python3
"""Tests for Academic Reading Set E (original 40-question paper)."""

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

PAPER_PATH = ROOT / "prompts" / "reading_set_e.json"
KEYS_PATH = ROOT / "prompts" / "reading_keys_set_e.json"

READING_LABELS = ("题干关键词：", "原文定位：", "关键词替换：", "判定点：")
READING_FIELDS = ("stem_keywords", "locate", "paraphrase", "judgment")
TRAP_RE = re.compile(r"不要误填|不要误选|不可填|不能选|不要选|不可选|不能填|不要填|干扰项")

FROZEN_ANSWERS = {
    1: "pharmacist",
    2: "glazes",
    3: "insulators",
    4: "moisture",
    5: "temperature",
    6: "notebooks",
    7: "linings",
    8: "FALSE",
    9: "TRUE",
    10: "NOT GIVEN",
    11: "TRUE",
    12: "FALSE",
    13: "NOT GIVEN",
    14: "C",
    15: "A",
    16: "F",
    17: "D",
    18: "pontoons",
    19: "terraces",
    20: "turbines",
    21: "barley",
    22: "lidar",
    23: "E",
    24: "B",
    25: "A",
    26: "D",
    27: "B",
    28: "D",
    29: "C",
    30: "G",
    31: "B",
    32: "B",
    33: "D",
    34: "A",
    35: "E",
    36: "C",
    37: "trout",
    38: "parasites",
    39: "forage",
    40: "mink",
}

TITLES = {
    1: "The industrial ceramics of Nadia Kellerman",
    2: "New uses for abandoned quarries",
    3: "A new role for the beaver",
}

WORD_TARGETS = {1: (700, 850), 2: (800, 920), 3: (850, 980)}

STUDENT_PATHS = [
    PAPER_PATH,
    ROOT / "templates" / "reading.html",
    ROOT / "static" / "reading.js",
    ROOT / "static" / "reading.css",
    ROOT / "README.md",
    ROOT / "reading_review.py",
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


class SetEPaperTests(unittest.TestCase):
    def setUp(self):
        self.paper = load_paper()
        self.keys = load_keys()

    def test_paper_identity_and_shape(self):
        self.assertEqual(self.paper["id"], "set-e")
        self.assertEqual(self.paper["title"], "Set E · Academic Reading")
        self.assertEqual(self.paper["subtitle"], "Academic Reading")
        self.assertIn("instructions", self.paper)
        self.assertEqual(self.paper["instructions"]["time"], "1 hour")
        info = " ".join(self.paper["instructions"]["information"])
        self.assertIn("40 questions", info)
        self.assertIn("one mark", info)
        self.assertEqual(len(self.paper["passages"]), 3)
        self.assertEqual(len(self.paper["groups"]), 8)

    def test_forty_unique_questions_and_ranges(self):
        nums: list[int] = []
        expected = [
            ("q1-7", "notes", 1, 1, 7),
            ("q8-13", "tfng", 1, 8, 13),
            ("q14-17", "matching_info", 2, 14, 17),
            ("q18-22", "notes", 2, 18, 22),
            ("q23-26", "matching_features", 2, 23, 26),
            ("q27-31", "matching_info", 3, 27, 31),
            ("q32-36", "matching_features", 3, 32, 36),
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

    def test_titles_lettering_and_word_counts(self):
        for passage in self.paper["passages"]:
            self.assertEqual(passage["title"], TITLES[passage["id"]])
            self.assertEqual(passage["label"], f"READING PASSAGE {passage['id']}")
            body = [p for p in passage["paragraphs"] if isinstance(p, str)]
            words = len(passage_body_text(passage).split())
            lo, hi = WORD_TARGETS[passage["id"]]
            self.assertGreaterEqual(words, lo, f"Passage {passage['id']} has {words} words")
            self.assertLessEqual(words, hi, f"Passage {passage['id']} has {words} words")
            if passage["id"] == 1:
                self.assertFalse(bool(passage.get("lettered")))
                self.assertEqual(len(body), 7)
                self.assertFalse(any(isinstance(p, dict) for p in passage["paragraphs"]))
            elif passage["id"] == 2:
                self.assertTrue(passage.get("lettered"))
                self.assertEqual(len(body), 6)
            else:
                self.assertTrue(passage.get("lettered"))
                self.assertEqual(len(body), 7)
            qlo, qhi = {1: (1, 13), 2: (14, 26), 3: (27, 40)}[passage["id"]]
            self.assertIn(f"Questions {qlo}–{qhi}", passage["time_guidance"])
            self.assertIn(f"Reading Passage {passage['id']}", passage["time_guidance"])

    def test_student_json_has_no_keys_or_official_names(self):
        dumped = json.dumps(self.paper)
        self.assertNotRegex(dumped, r'"explanation"\s*:')
        self.assertNotIn("correct_answer", dumped)
        self.assertNotRegex(dumped, r'"answer"\s*:')
        self.assertNotIn("stem_keywords", dumped)
        for path in STUDENT_PATHS:
            blob = path.read_text(encoding="utf-8")
            self.assertNotRegex(blob, r'"explanation"\s*:')
            self.assertNotIn("correct_answer", blob)

    def test_typography_and_british_spelling(self):
        dumped = json.dumps(self.paper, ensure_ascii=False)
        self.assertIn("1891–1978", dumped)
        self.assertIn("Kellerman's insistence", dumped)
        self.assertIn("organisation", dumped)
        self.assertIn("neighbouring", dumped)
        self.assertIn("catalogue", dumped)
        self.assertIn("flood-defence", dumped)
        self.assertIn("programme", dumped)
        self.assertIn("favours", dumped)
        self.assertIn("colonise", dumped)
        self.assertNotIn("organization", dumped)
        self.assertNotIn("neighboring", dumped)
        self.assertNotIn("catalog,", dumped.replace("catalogue", ""))
        self.assertNotIn("flood-defense", dumped)
        self.assertNotIn("favors", dumped)

    def test_completion_answers_appear_in_passage(self):
        questions = self.keys["questions"]
        passage_of = {}
        for group in self.paper["groups"]:
            for q in range(group["from"], group["to"] + 1):
                passage_of[q] = group["passage"]
        for q, answer in FROZEN_ANSWERS.items():
            if answer in {"TRUE", "FALSE", "NOT GIVEN"} or re.fullmatch(r"[A-G]", answer):
                continue
            text = passage_body_text(self.paper["passages"][passage_of[q] - 1])
            self.assertIsNotNone(
                re.search(r"(?i)\b" + re.escape(answer) + r"\b", text),
                f"Q{q} {answer!r} not in passage",
            )
            self.assertEqual(questions[str(q)]["answer"], answer)

    def test_choice_answers_are_valid(self):
        questions = self.keys["questions"]
        for group in self.paper["groups"]:
            for q in range(group["from"], group["to"] + 1):
                meta = questions[str(q)]
                self.assertEqual(meta["type"], group["type"])
                answer = meta["answer"]
                if group["type"] == "matching_features":
                    self.assertIn(answer, group["options"])
                elif group["type"] == "matching_info":
                    letters = "ABCDEFG" if group["passage"] == 3 else "ABCDEF"
                    self.assertIn(answer, letters)
                elif group["type"] == "tfng":
                    self.assertIn(answer, {"TRUE", "FALSE", "NOT GIVEN"})

    def test_keys_match_frozen_key_and_have_four_fields(self):
        self.assertEqual(self.keys["set_id"], "set-e")
        questions = self.keys["questions"]
        self.assertEqual(sorted(int(q) for q in questions), list(range(1, 41)))
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

    def test_helpers_load_set_e(self):
        paper = rr.load_paper_for_set("set-e")
        keys = rr.load_keys_for_set("set-e")
        self.assertIsNotNone(paper)
        self.assertIsNotNone(keys)
        self.assertEqual(paper["id"], "set-e")
        self.assertEqual(keys["set_id"], "set-e")
        self.assertEqual(len(keys["questions"]), 40)
        self.assertEqual(rr.keys_path_for_set("set-a"), rs.KEYS_PATH)
        self.assertEqual(rr.keys_path_for_set("set-e"), KEYS_PATH)
        ids = [item["id"] for item in rr.list_reading_sets()]
        self.assertEqual(ids, ["set-a", "set-b", "set-c", "set-d", "set-e"])
        html = rr.official_passage_html(paper["passages"][1])
        self.assertIn('class="para-label">A</strong>', html)
        self.assertIn('class="para-label">F</strong>', html)

        page = (ROOT / "templates" / "reading.html").read_text(encoding="utf-8")
        js = (ROOT / "static" / "reading.js").read_text(encoding="utf-8")
        self.assertIn('value="set-e"', page)
        self.assertIn("Set E · Academic Reading", page)
        self.assertIn('"set-e"', js)
        self.assertIn("full: [1, 40]", js)
        self.assertIn("passage1: [1, 13]", js)
        self.assertIn("passage3: [27, 40]", js)
        self.assertNotIn("reading-theme-e", js)
        self.assertNotIn("reading-theme-c", page)


class SetEScoringTests(unittest.TestCase):
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
        self.assertEqual(result["band_estimate"], 9.0)
        self.assertEqual(rs.band_for_score(40, 40), 9.0)
        self.assertEqual(rs.band_for_score(39, 40), 9.0)
        self.assertEqual(rs.band_for_score(42, 42), 9.0)

    def test_passage_modes_are_unbanded(self):
        answers = {str(q): self.official[q] for q in range(1, 14)}
        result = rs.score_paper(answers, mode="passage1", keys=self.keys, paper=self.paper)
        self.assertEqual(result["score"], 13)
        self.assertEqual(result["total"], 13)
        self.assertIsNone(result["band_estimate"])

    def test_set_d_scaled_banding_still_works(self):
        set_d_paper = rr.load_paper_for_set("set-d")
        set_d_keys = rr.load_keys_for_set("set-d")
        official = official_from_keys(set_d_keys)
        result = rs.score_paper(
            {str(q): a for q, a in official.items()},
            mode="full",
            keys=set_d_keys,
            paper=set_d_paper,
        )
        self.assertEqual(result["score"], 42)
        self.assertEqual(result["total"], 42)
        self.assertEqual(result["band_estimate"], 9.0)

    def test_wrong_set_answer_does_not_mark_set_e_item(self):
        answers = {str(q): a for q, a in self.official.items()}
        answers["8"] = "TRUE"
        result = rs.score_paper(answers, mode="full", keys=self.keys, paper=self.paper)
        self.assertEqual(result["score"], 39)
        self.assertEqual(result["total"], 40)
        self.assertLess(result["score"], 40)


class SetERouteTests(unittest.TestCase):
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
        denied = self.client.get("/api/reading/paper?set=set-e")
        self.assertEqual(denied.status_code, 403)

    def test_paper_api_set_e_has_no_keys(self):
        self._start()
        res = self.client.get("/api/reading/paper?set=set-e")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["id"], "set-e")
        self.assertEqual(len(data["passages"]), 3)
        self.assertEqual(len(data["groups"]), 8)
        body = res.get_data(as_text=True)
        self.assertNotRegex(body, r'"explanation"\s*:')
        self.assertNotIn("correct_answer", body)
        self.assertNotIn("stem_keywords", body)
        for label in ("题干关键词", "原文定位", "关键词替换", "判定点"):
            self.assertNotIn(label, body)
        listing = self.client.get("/api/reading/sets")
        self.assertEqual(listing.status_code, 200)
        ids = [item["id"] for item in listing.get_json()]
        self.assertEqual(ids, ["set-a", "set-b", "set-c", "set-d", "set-e"])

    def test_submit_uses_set_e_keys_and_ranges(self):
        self._start()
        res = self.client.post(
            "/api/reading/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "full",
                "prompt_set_id": "set-e",
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
        self.assertEqual(saved["prompt_set_id"], "set-e")
        self.assertEqual(saved["score"], 40)
        self.assertEqual(len(saved["marking"]), 40)

        payload = appmod.attempt_review_payload(saved)
        self.assertEqual(payload["paper"]["id"], "set-e")
        self.assertEqual(len(payload["questions"]), 40)
        self.assertTrue(all(row.get("correct") for row in payload["questions"]))

    def test_submit_passage1_only_marks_thirteen(self):
        self._start(mode="passage1")
        res = self.client.post(
            "/api/reading/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "passage1",
                "prompt_set_id": "set-e",
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

    def test_setup_page_lists_set_e_without_theme(self):
        page = self.client.get("/reading")
        self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        self.assertIn('value="set-e"', html)
        self.assertIn("Set E · Academic Reading", html)
        self.assertNotIn("reading-theme-c", html)


if __name__ == "__main__":
    unittest.main()
