#!/usr/bin/env python3
"""Tests for Academic Listening Set B and multi-set loading/scoring."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import access as accessmod  # noqa: E402
import app as appmod  # noqa: E402
import listening_scoring as ls  # noqa: E402

PAPER_PATH = ROOT / "prompts" / "listening_set_b.json"
KEYS_PATH = ROOT / "prompts" / "listening_keys_set_b.json"
AUDIO_DIR = ROOT / "static" / "audio" / "listening_set_b"
SET_A_AUDIO_DIR = ROOT / "static" / "audio" / "listening_set_a"

FORBIDDEN_OFFICIAL = (
    "海外真题",
    "10.11",
    "wilby",
    "tesla room",
    "rooftop pool",
    "airport shuttle",
    "city tours",
    "green street",
    "mill park",
    "hill park",
    "fishing docks",
    "splash-zone",
    "splash zone",
    "louisa may alcott",
    "the inheritance",
    "typhoid",
)

STUDENT_PATHS = [
    PAPER_PATH,
    ROOT / "templates" / "listening.html",
    ROOT / "templates" / "hub.html",
    ROOT / "static" / "listening.js",
    ROOT / "static" / "listening.css",
]


def load_paper() -> dict:
    return json.loads(PAPER_PATH.read_text(encoding="utf-8"))


def load_keys() -> dict:
    return json.loads(KEYS_PATH.read_text(encoding="utf-8"))


def official_from_keys(keys: dict) -> dict[int, str]:
    return {int(q): meta["answer"] for q, meta in keys["questions"].items()}


class SetListTests(unittest.TestCase):
    def test_list_includes_set_a_and_set_b_default_is_set_a(self):
        sets = ls.list_listening_sets()
        ids = [item["id"] for item in sets]
        self.assertEqual(ids[:2], ["set-a", "set-b"])
        self.assertEqual(ids, ["set-a", "set-b", "set-c"])
        self.assertIn("set-a", ids)
        self.assertIn("set-b", ids)
        default_paper = ls.load_paper()
        self.assertEqual(default_paper["id"], "set-a")
        self.assertEqual(appmod.normalize_listening_set_id(None), "set-a")
        self.assertEqual(appmod.normalize_listening_set_id(""), "set-a")


class SetBPaperTests(unittest.TestCase):
    def setUp(self):
        self.paper = load_paper()
        self.keys = load_keys()

    def test_paper_identity_and_1011_like_skeleton(self):
        self.assertEqual(self.paper["id"], "set-b")
        self.assertEqual(self.paper["title"], "Set B · Academic Listening")
        self.assertEqual(self.paper["check_seconds"], 120)
        self.assertEqual(len(self.paper["sections"]), 4)
        sections = {s["id"]: s for s in self.paper["sections"]}

        s1 = sections[1]["groups"]
        self.assertEqual(len(s1), 1)
        self.assertEqual(s1[0]["type"], "notes")
        self.assertEqual((s1[0]["from"], s1[0]["to"]), (1, 10))
        self.assertTrue(any("ONE WORD AND/OR A NUMBER" in line for line in s1[0]["instructions"]))
        self.assertTrue(any("Complete the notes below." in line for line in s1[0]["instructions"]))

        types2 = [g["type"] for g in sections[2]["groups"]]
        self.assertEqual(types2, ["choose_two", "choose_three", "matching"])
        g11, g13, g16 = sections[2]["groups"]
        self.assertEqual((g11["from"], g11["to"]), (11, 12))
        self.assertTrue(any("TWO" in line for line in g11["instructions"]))
        self.assertEqual((g13["from"], g13["to"]), (13, 15))
        self.assertTrue(any("THREE" in line for line in g13["instructions"]))
        self.assertEqual(len(g13["options"]), 6)
        self.assertEqual((g16["from"], g16["to"]), (16, 20))
        self.assertEqual(len(g16["legend"]), 8)
        self.assertEqual([item["q"] for item in g16["items"]], [16, 17, 18, 19, 20])

        types3 = [g["type"] for g in sections[3]["groups"]]
        self.assertEqual(types3, ["mcq", "choose_two", "choose_two"])
        self.assertEqual((sections[3]["groups"][0]["from"], sections[3]["groups"][0]["to"]), (21, 26))
        self.assertEqual(len(sections[3]["groups"][0]["items"]), 6)
        self.assertEqual((sections[3]["groups"][1]["from"], sections[3]["groups"][1]["to"]), (27, 28))
        self.assertEqual((sections[3]["groups"][2]["from"], sections[3]["groups"][2]["to"]), (29, 30))

        s4 = sections[4]["groups"]
        self.assertEqual(s4[0]["type"], "notes")
        self.assertEqual((s4[0]["from"], s4[0]["to"]), (31, 40))
        self.assertTrue(any("ONE WORD ONLY" in line for line in s4[0]["instructions"]))

    def test_forty_questions_and_no_keys_in_student_json(self):
        nums: list[int] = []
        for section in self.paper["sections"]:
            for group in section["groups"]:
                nums.extend(range(group["from"], group["to"] + 1))
        self.assertEqual(nums, list(range(1, 41)))
        dumped = json.dumps(self.paper)
        self.assertNotIn("explanation", dumped)
        self.assertNotIn("transcript", dumped.lower())
        self.assertNotIn("correct_answer", dumped)
        self.assertNotRegex(dumped, r'"answer"\s*:')
        self.assertNotIn("海外真题", dumped)
        self.assertNotIn("10.11", dumped)
        lower = dumped.lower()
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lower, word)
        for path in STUDENT_PATHS:
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            for word in FORBIDDEN_OFFICIAL:
                self.assertNotIn(word, lowered, f"{word!r} in {path}")

    def test_start_page_html_contains_set_b(self):
        html = (ROOT / "templates" / "listening.html").read_text(encoding="utf-8")
        self.assertIn("Set B · Academic Listening", html)
        self.assertIn('value="set-b"', html)
        self.assertIn('value="set-a"', html)

    def test_keys_have_forty_explanations_and_transcripts(self):
        self.assertEqual(self.keys["set_id"], "set-b")
        questions = self.keys["questions"]
        self.assertEqual(sorted(int(q) for q in questions), list(range(1, 41)))
        for q, meta in questions.items():
            self.assertTrue(meta.get("answer"), q)
            self.assertTrue(meta.get("explanation"), q)
            self.assertTrue(meta.get("type"), q)
        transcripts = self.keys.get("transcripts") or {}
        self.assertEqual(set(transcripts), {"1", "2", "3", "4"})
        for sid, text in transcripts.items():
            self.assertGreater(len(text.split()), 100, sid)


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.keys = load_keys()
        self.official = official_from_keys(self.keys)

    def test_perfect_script_scores_40_band_9(self):
        result = ls.score_paper(
            {str(q): a for q, a in self.official.items()},
            mode="full",
            keys=self.keys,
        )
        self.assertEqual(result["score"], 40)
        self.assertEqual(result["total"], 40)
        self.assertEqual(result["band_estimate"], 9)
        self.assertTrue(all(row["ok"] for row in result["marking"]))

    def test_section_only_has_no_band(self):
        answers = {str(q): self.official[q] for q in range(11, 21)}
        result = ls.score_paper(answers, mode="section2", keys=self.keys)
        self.assertEqual(result["score"], 10)
        self.assertEqual(result["total"], 10)
        self.assertIsNone(result["band_estimate"])

    def test_choose_three_order_partial_and_repeats(self):
        # Official 13-15 are A, C, E. Any order scores 3.
        result = ls.score_paper({"13": "E", "14": "A", "15": "C"}, mode="full", keys=self.keys)
        by_q = {row["q"]: row for row in result["marking"]}
        self.assertTrue(by_q[13]["ok"])
        self.assertTrue(by_q[14]["ok"])
        self.assertTrue(by_q[15]["ok"])
        self.assertEqual(result["score"], 3)
        self.assertEqual(by_q[13]["correct"], "A, C, E")
        # Two of three.
        result2 = ls.score_paper({"13": "A", "14": "C", "15": "B"}, mode="full", keys=self.keys)
        self.assertEqual(result2["score"], 2)
        # A repeated letter counts once (A, A, C) -> A and C = 2.
        result3 = ls.score_paper({"13": "A", "14": "A", "15": "C"}, mode="full", keys=self.keys)
        self.assertEqual(result3["score"], 2)
        # Wrong letters score 0.
        result4 = ls.score_paper({"13": "B", "14": "D", "15": "F"}, mode="full", keys=self.keys)
        self.assertEqual(result4["score"], 0)

    def test_choose_two_pairs_still_work_on_both_sets(self):
        set_b = ls.score_paper({"11": "E", "12": "B"}, mode="full", keys=self.keys)
        self.assertEqual(set_b["score"], 2)
        set_b_partial = ls.score_paper({"11": "B", "12": "A"}, mode="full", keys=self.keys)
        self.assertEqual(set_b_partial["score"], 1)
        set_a_keys = ls.load_keys()
        # Set A official 17-18 are B and D.
        set_a = ls.score_paper({"17": "D", "18": "B"}, mode="full", keys=set_a_keys)
        self.assertEqual(set_a["score"], 2)
        set_a_dup = ls.score_paper({"17": "B", "18": "B"}, mode="full", keys=set_a_keys)
        self.assertEqual(set_a_dup["score"], 1)

    def test_listed_alternatives_and_word_limit(self):
        answers = {str(q): a for q, a in self.official.items()}
        answers["4"] = "jewelry"
        answers["5"] = "£85"
        answers["36"] = "color"
        result = ls.score_paper(answers, mode="full", keys=self.keys)
        self.assertEqual(result["score"], 40)
        over = ls.score_paper({31: "small village"}, mode="full", keys=self.keys)
        by_q = {row["q"]: row for row in over["marking"]}
        self.assertFalse(by_q[31]["ok"])


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        appmod.DATA_DIR = base / "data"
        appmod.SUBMISSIONS_DIR = appmod.DATA_DIR / "submissions"
        appmod.INDEX_PATH = appmod.DATA_DIR / "index.json"
        accessmod.bind(appmod.DATA_DIR)
        appmod.ensure_storage()
        appmod.app.config["TESTING"] = True
        appmod.app.config["SECRET_KEY"] = "test-secret-listening-b"
        self.client = appmod.app.test_client()
        self.keys = load_keys()
        self.official = official_from_keys(self.keys)

    def tearDown(self):
        self.tmp.cleanup()

    def _create_code(self, code="TESTCODEB"):
        return accessmod.create_code(code=code)

    def _start(self, name="Test Candidate", code="TESTCODEB", module="listening", mode="full"):
        return self.client.post(
            "/api/session/start",
            json={
                "candidate_name": name,
                "invite_code": code,
                "module": module,
                "mode": mode,
            },
        )

    def test_sets_endpoint_and_default_paper(self):
        denied = self.client.get("/api/listening/sets")
        self.assertEqual(denied.status_code, 403)
        self._create_code()
        self.assertEqual(self._start().status_code, 200)
        res = self.client.get("/api/listening/sets")
        self.assertEqual(res.status_code, 200)
        ids = [item["id"] for item in res.get_json()]
        self.assertEqual(ids[:2], ["set-a", "set-b"])
        self.assertEqual(ids, ["set-a", "set-b", "set-c"])
        default = self.client.get("/api/listening/paper")
        self.assertEqual(default.status_code, 200)
        self.assertEqual(default.get_json()["id"], "set-a")

    def test_paper_and_audio_require_session_hide_keys_and_are_not_set_a(self):
        denied = self.client.get("/api/listening/paper?set=set-b")
        self.assertEqual(denied.status_code, 403)
        audio_denied = self.client.get("/api/listening/audio/1?set=set-b")
        self.assertEqual(audio_denied.status_code, 403)

        self._create_code()
        self.assertEqual(self._start().status_code, 200)

        res = self.client.get("/api/listening/paper?set=set-b")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["id"], "set-b")
        raw = res.get_data(as_text=True)
        lowered = raw.lower()
        self.assertNotIn("explanation", raw)
        self.assertNotIn("transcript", lowered)
        self.assertNotIn('"answer":', raw)
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lowered, word)
        self.assertIn("Hartwell", raw)
        self.assertNotIn("Ink & Timber", raw)
        self.assertNotIn("Pellam", raw)

        missing = self.client.get("/api/listening/paper?set=set-z")
        self.assertEqual(missing.status_code, 404)

        audio_b = self.client.get("/api/listening/audio/1?set=set-b")
        audio_a = self.client.get("/api/listening/audio/1?set=set-a")
        path_b = AUDIO_DIR / "section1.mp3"
        path_a = SET_A_AUDIO_DIR / "section1.mp3"
        self.assertTrue(path_b.is_file(), "Set B section1.mp3 must be generated")
        self.assertEqual(audio_b.status_code, 200)
        self.assertTrue((audio_b.headers.get("Content-Type") or "").startswith("audio/mpeg"))
        body_b = audio_b.get_data()
        self.assertGreater(len(body_b), 1000)
        if path_a.is_file() and audio_a.status_code == 200:
            body_a = audio_a.get_data()
            self.assertNotEqual(body_b[:4000], body_a[:4000])
            self.assertEqual(len(body_b), path_b.stat().st_size)
            self.assertEqual(len(body_a), path_a.stat().st_size)

    def test_submit_set_b_stores_id_and_uses_set_b_keys(self):
        self._create_code()
        self.assertEqual(self._start().status_code, 200)
        answers = {str(q): a for q, a in self.official.items()}
        # A Set A answer must not be marked correct against Set B keys.
        answers["1"] = "poetry"
        res = self.client.post(
            "/api/listening/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "full",
                "prompt_set_id": "set-b",
                "answers": answers,
                "duration_seconds": 1800,
                "time_used_seconds": 1700,
                "part_times": {"1": 400, "2": 400, "3": 450, "4": 450},
            },
        )
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["score"], 39)
        self.assertEqual(data["total"], 40)
        self.assertEqual(data["band_estimate"], 9)
        self.assertNotIn("marking", data)
        sid = data["id"]
        saved = json.loads((appmod.SUBMISSIONS_DIR / f"{sid}.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["prompt_set_id"], "set-b")
        self.assertEqual(saved["module"], "listening")
        self.assertEqual(saved["score"], 39)
        by_q = {row["q"]: row for row in saved["marking"]}
        self.assertFalse(by_q[1]["ok"])
        self.assertEqual(by_q[1]["correct"].lower(), "19th")

        review = self.client.get(f"/api/me/submission/{sid}")
        self.assertEqual(review.status_code, 200)
        payload = review.get_json()
        self.assertIn("Ada Merrin", json.dumps(payload.get("paper") or payload, ensure_ascii=False))
        transcripts = json.dumps(payload.get("transcripts") or {}, ensure_ascii=False)
        self.assertIn("Hartwell", transcripts)
        self.assertNotIn("Fraser", transcripts)
        self.assertNotIn("Pellam", transcripts)


class AudioFileTests(unittest.TestCase):
    def test_set_b_audio_files_exist_and_durations_are_recorded(self):
        paper = load_paper()
        for section in paper["sections"]:
            sid = section["id"]
            path = AUDIO_DIR / f"section{sid}.mp3"
            self.assertTrue(path.is_file(), path)
            self.assertGreater(path.stat().st_size, 1000)
            seconds = int((section.get("audio") or {}).get("duration_seconds") or 0)
            self.assertGreater(seconds, 60, sid)


if __name__ == "__main__":
    unittest.main()
