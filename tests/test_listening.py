#!/usr/bin/env python3
"""Unit and smoke tests for Academic Listening marking and routes."""

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
import listening_scoring as ls  # noqa: E402
import app as appmod  # noqa: E402
import student_portal as sp  # noqa: E402

OFFICIAL = ls.official_answers()

FORBIDDEN = (
    "pellam",
    "bitumen became the standard",
    "merrow's threshold model",
    "westmere community apiary, my name is rowan hale",
    "fraser, have you got a minute",
)

STUDENT_PATHS = [
    ROOT / "prompts" / "listening_set_a.json",
    ROOT / "templates" / "listening.html",
    ROOT / "templates" / "hub.html",
    ROOT / "static" / "listening.js",
    ROOT / "static" / "listening.css",
]


class ScoringTests(unittest.TestCase):
    def test_keys_cover_forty_questions(self):
        self.assertEqual(set(OFFICIAL), set(range(1, 41)))
        self.assertEqual(len(OFFICIAL), 40)

    def test_perfect_key_scores_40_band_9(self):
        result = ls.score_paper({str(q): a for q, a in OFFICIAL.items()}, mode="full")
        self.assertEqual(result["score"], 40)
        self.assertEqual(result["total"], 40)
        self.assertEqual(result["band_estimate"], 9)
        self.assertTrue(all(row["ok"] for row in result["marking"]))

    def test_blank_paper_scores_zero(self):
        result = ls.score_paper({}, mode="full")
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["total"], 40)
        self.assertEqual(result["band_estimate"], 0.0)
        self.assertTrue(all(not row["ok"] for row in result["marking"]))

    def test_case_and_listed_alternative(self):
        answers = {str(q): a for q, a in OFFICIAL.items()}
        answers["5"] = "pellam"
        answers["9"] = "£30"
        answers["11"] = "b"
        result = ls.score_paper(answers, mode="full")
        by_q = {row["q"]: row for row in result["marking"]}
        self.assertTrue(by_q[5]["ok"])
        self.assertTrue(by_q[9]["ok"], by_q[9])
        self.assertTrue(by_q[11]["ok"])
        self.assertEqual(result["score"], 40)

    def test_word_limit_violation_is_wrong(self):
        result = ls.score_paper({1: "poetry books"}, mode="full")
        by_q = {row["q"]: row for row in result["marking"]}
        self.assertFalse(by_q[1]["ok"])
        # The official one-word answer still passes.
        result2 = ls.score_paper({1: "poetry"}, mode="full")
        by_q2 = {row["q"]: row for row in result2["marking"]}
        self.assertTrue(by_q2[1]["ok"])

    def test_choose_two_either_order_and_partial(self):
        # Official 17-18 are B and D. Reversed order still scores 2.
        result = ls.score_paper({17: "D", 18: "B"}, mode="full")
        by_q = {row["q"]: row for row in result["marking"]}
        self.assertTrue(by_q[17]["ok"])
        self.assertTrue(by_q[18]["ok"])
        self.assertEqual(result["score"], 2)
        # One of two correct.
        result2 = ls.score_paper({17: "B", 18: "C"}, mode="full")
        by_q2 = {row["q"]: row for row in result2["marking"]}
        self.assertTrue(by_q2[17]["ok"])
        self.assertFalse(by_q2[18]["ok"])
        self.assertEqual(result2["score"], 1)
        # Duplicate official letter scores 1.
        result3 = ls.score_paper({17: "B", 18: "B"}, mode="full")
        by_q3 = {row["q"]: row for row in result3["marking"]}
        self.assertEqual(sum(1 for row in (by_q3[17], by_q3[18]) if row["ok"]), 1)
        self.assertEqual(result3["score"], 1)
        # Both wrong.
        result4 = ls.score_paper({17: "A", 18: "C"}, mode="full")
        self.assertEqual(result4["score"], 0)

    def test_section_only_has_no_band(self):
        answers = {str(q): OFFICIAL[q] for q in range(1, 11)}
        result = ls.score_paper(answers, mode="section1")
        self.assertEqual(result["score"], 10)
        self.assertEqual(result["total"], 10)
        self.assertIsNone(result["band_estimate"])

    def test_band_table_samples(self):
        self.assertEqual(ls.band_for_score(39), 9.0)
        self.assertEqual(ls.band_for_score(37), 8.5)
        self.assertEqual(ls.band_for_score(32), 7.5)
        self.assertEqual(ls.band_for_score(30), 7.0)
        self.assertEqual(ls.band_for_score(26), 6.5)
        self.assertEqual(ls.band_for_score(0, 10), None)


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

        paper = json.loads((ROOT / "prompts" / "listening_set_a.json").read_text(encoding="utf-8"))
        dumped = json.dumps(paper)
        self.assertNotIn("explanation", dumped)
        self.assertNotIn("transcript", dumped.lower())
        self.assertNotIn("correct_answer", dumped)
        self.assertNotIn('"answer": "Pellam"', dumped)
        self.assertNotIn('"answer": "poetry"', dumped)
        self.assertNotIn('"answer": "bitumen"', dumped)

    def test_paper_has_cambridge20_test1_shape(self):
        paper = ls.load_paper()
        self.assertEqual(paper["id"], "set-a")
        self.assertEqual(len(paper["sections"]), 4)
        sections = {s["id"]: s for s in paper["sections"]}

        s1 = sections[1]["groups"]
        self.assertEqual(len(s1), 1)
        self.assertEqual(s1[0]["type"], "notes_table")
        self.assertEqual((s1[0]["from"], s1[0]["to"]), (1, 10))
        self.assertEqual(len(s1[0]["table"]["headers"]), 4)
        self.assertEqual(len(s1[0]["table"]["rows"]), 3)
        self.assertTrue(any("ONE WORD AND/OR A NUMBER" in line for line in s1[0]["instructions"]))

        types2 = [g["type"] for g in sections[2]["groups"]]
        self.assertEqual(types2, ["mcq", "choose_two", "choose_two"])
        self.assertEqual((sections[2]["groups"][0]["from"], sections[2]["groups"][0]["to"]), (11, 16))
        self.assertEqual((sections[2]["groups"][1]["from"], sections[2]["groups"][1]["to"]), (17, 18))
        self.assertEqual((sections[2]["groups"][2]["from"], sections[2]["groups"][2]["to"]), (19, 20))

        types3 = [g["type"] for g in sections[3]["groups"]]
        self.assertEqual(types3, ["choose_two", "choose_two", "choose_two", "mcq"])
        self.assertEqual((sections[3]["groups"][0]["from"], sections[3]["groups"][0]["to"]), (21, 22))
        self.assertEqual((sections[3]["groups"][1]["from"], sections[3]["groups"][1]["to"]), (23, 24))
        self.assertEqual((sections[3]["groups"][2]["from"], sections[3]["groups"][2]["to"]), (25, 26))
        self.assertEqual((sections[3]["groups"][3]["from"], sections[3]["groups"][3]["to"]), (27, 30))

        s4 = sections[4]["groups"]
        self.assertEqual(s4[0]["type"], "notes")
        self.assertEqual((s4[0]["from"], s4[0]["to"]), (31, 40))
        headings = [sec.get("heading") for sec in s4[0]["notes"]["sections"]]
        self.assertEqual(len(headings), 3)
        self.assertTrue(all(headings))
        self.assertTrue(any("ONE WORD ONLY" in line for line in s4[0]["instructions"]))
        dumped = json.dumps(paper)
        self.assertNotIn('"type": "map"', dumped)


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
        appmod.app.config["SECRET_KEY"] = "test-secret-listening"
        self.client = appmod.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def _create_code(self, code="TESTCODE1"):
        return accessmod.create_code(code=code)

    def _start(self, name="Test Candidate", code="TESTCODE1", module="listening", mode="full"):
        return self.client.post(
            "/api/session/start",
            json={
                "candidate_name": name,
                "invite_code": code,
                "module": module,
                "mode": mode,
            },
        )

    def test_health_and_homepage_include_listening(self):
        h = self.client.get("/health")
        self.assertEqual(h.status_code, 200)
        self.assertIn("listening", h.get_json()["modules"])

        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        html = home.get_data(as_text=True)
        self.assertIn("/listening", html)
        self.assertIn("Academic Listening", html)
        self.assertIn("听力模考", html)

        page = self.client.get("/listening")
        self.assertEqual(page.status_code, 200)
        body = page.get_data(as_text=True)
        self.assertIn("Start your listening test", body)
        self.assertIn("Invitation code", body)
        lower = body.lower()
        for word in FORBIDDEN:
            self.assertNotIn(word, lower)
        self.assertNotIn("参考分数", body)

    def test_start_increments_use_count_once_like_other_modules(self):
        rec = self._create_code()
        started = self._start()
        self.assertEqual(started.status_code, 200)
        self.assertTrue(started.get_json()["ok"])
        self.assertEqual(started.get_json()["module"], "listening")
        codes = accessmod.list_codes()
        self.assertEqual(codes[0]["use_count"], 1)
        users = accessmod.list_users()
        self.assertEqual(users[0]["listening_started"], 1)
        self.assertEqual(users[0].get("listening_submitted") or 0, 0)
        self.assertEqual(users[0]["reading_started"], 0)

        # A second start consumes one more use, same as reading/writing.
        again = self._start()
        self.assertEqual(again.status_code, 200)
        codes = accessmod.list_codes()
        self.assertEqual(codes[0]["use_count"], 2)
        users = accessmod.list_users()
        self.assertEqual(users[0]["listening_started"], 2)
        # Existing users without listening_* fields must still be readable.
        self.assertEqual(int(users[0].get("listening_started") or 0), 2)
        self.assertEqual(rec["code"], "TESTCODE1")

    def test_paper_and_audio_require_session_and_hide_keys(self):
        denied = self.client.get("/api/listening/paper")
        self.assertEqual(denied.status_code, 403)
        audio_denied = self.client.get("/api/listening/audio/1")
        self.assertEqual(audio_denied.status_code, 403)

        self._create_code()
        started = self._start()
        self.assertEqual(started.status_code, 200)

        res = self.client.get("/api/listening/paper")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["id"], "set-a")
        raw = res.get_data(as_text=True).lower()
        for word in FORBIDDEN:
            self.assertNotIn(word, raw)
        self.assertNotIn("explanation", raw)
        self.assertNotIn("transcript", raw)
        self.assertEqual(len(data["sections"]), 4)

        audio = self.client.get("/api/listening/audio/1")
        audio_path = ROOT / "static" / "audio" / "listening_set_a" / "section1.mp3"
        if audio_path.is_file():
            self.assertEqual(audio.status_code, 200)
            self.assertTrue((audio.headers.get("Content-Type") or "").startswith("audio/mpeg"))
            self.assertGreater(len(audio.get_data()), 1000)
            self.assertNotIn(b"PELLAM", audio.get_data()[:200])
        else:
            self.assertEqual(audio.status_code, 404)
        bad = self.client.get("/api/listening/audio/9")
        self.assertEqual(bad.status_code, 404)

    def test_submit_scores_alternative_and_word_limit_without_leaking_keys(self):
        self._create_code()
        started = self._start()
        self.assertEqual(started.status_code, 200)
        answers = {str(q): a for q, a in OFFICIAL.items()}
        answers["9"] = "£30"
        answers["1"] = "poetry books"
        res = self.client.post(
            "/api/listening/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "full",
                "prompt_set_id": "set-a",
                "answers": answers,
                "duration_seconds": 1800,
                "time_remaining_seconds": 100,
                "time_used_seconds": 1700,
                "part_times": {"1": 400, "2": 400, "3": 450, "4": 450},
                "auto_submitted": False,
            },
        )
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["score"], 39)
        self.assertEqual(data["total"], 40)
        self.assertEqual(data["band_estimate"], 9)
        self.assertEqual(data["time_used_seconds"], 1700)
        self.assertEqual(data["part_times"]["4"], 450)
        self.assertNotIn("marking", data)
        self.assertNotIn("answers", data)
        self.assertNotIn("explanation", data)
        raw = res.get_data(as_text=True).lower()
        for word in FORBIDDEN:
            self.assertNotIn(word, raw)
        self.assertNotIn("解析", res.get_data(as_text=True))
        self.assertNotIn("标准答案", res.get_data(as_text=True))
        self.assertNotIn("transcript", raw)

        sid = data["id"]
        saved = json.loads((appmod.SUBMISSIONS_DIR / f"{sid}.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["module"], "listening")
        self.assertEqual(saved["score"], 39)
        by_q = {row["q"]: row for row in saved["marking"]}
        self.assertTrue(by_q[9]["ok"])
        self.assertFalse(by_q[1]["ok"])

    def test_section_only_submit_has_no_band(self):
        self._create_code()
        started = self._start(mode="section2")
        self.assertEqual(started.status_code, 200)
        answers = {str(q): OFFICIAL[q] for q in range(11, 21)}
        res = self.client.post(
            "/api/listening/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "section2",
                "answers": answers,
                "duration_seconds": 400,
                "time_used_seconds": 350,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["score"], 10)
        self.assertEqual(data["total"], 10)
        self.assertIsNone(data["band_estimate"])
        self.assertNotIn("marking", data)

    def test_review_flags_are_rejected(self):
        self._create_code()
        self.assertEqual(self._start().status_code, 200)
        for flag in ("review", "review_mode", "review_sid", "attempt_review"):
            res = self.client.post(
                "/api/listening/submit",
                json={
                    "candidate_name": "Test Candidate",
                    flag: True,
                    "mode": "full",
                    "answers": {"1": "KERRIDGE"},
                },
            )
            self.assertEqual(res.status_code, 403, flag)
            body = res.get_json()
            self.assertFalse(body["ok"])
            self.assertEqual(body["error"], "回顾模式不可交卷")
            self.assertNotIn("score", body)

    def test_unauthenticated_review_html_goes_to_me(self):
        guest = appmod.app.test_client()
        res = guest.get("/me/submission/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        location = res.headers.get("Location", "")
        self.assertIn("/me", location)
        self.assertNotIn("/admin/login", location)

    def test_other_user_review_is_404_and_owner_gets_keys_after_submit(self):
        self._create_code(code="SHARED1")
        started = self._start(name="Ada Student", code="SHARED1")
        self.assertEqual(started.status_code, 200)
        res = self.client.post(
            "/api/listening/submit",
            json={
                "candidate_name": "Ada Student",
                "mode": "full",
                "answers": {str(q): a for q, a in OFFICIAL.items()},
                "duration_seconds": 1800,
                "time_used_seconds": 1600,
            },
        )
        self.assertEqual(res.status_code, 200)
        sid = res.get_json()["id"]

        owner = self.client.get(f"/api/me/submission/{sid}")
        self.assertEqual(owner.status_code, 200)
        payload = owner.get_json()
        self.assertEqual(payload["module"], "listening")
        self.assertEqual(payload["score"], 40)
        self.assertTrue(payload["questions"])
        self.assertTrue(payload["questions"][0]["correct"])
        self.assertTrue(payload["questions"][0]["explanation"])
        self.assertIn("1", payload.get("transcripts") or {})
        self.assertIn("Fraser", json.dumps(payload["transcripts"]))
        self.assertEqual(sp.module_of({"module": "listening"}), "listening")

        review_html = self.client.get(f"/me/submission/{sid}")
        self.assertEqual(review_html.status_code, 200)
        self.assertIn("listening.js", review_html.get_data(as_text=True))
        mistakes = self.client.get(f"/me/submission/{sid}/review")
        self.assertEqual(mistakes.status_code, 200)

        home = self.client.get("/me")
        # After exam start the session is a student session, so /me is available.
        if home.status_code == 200:
            html = home.get_data(as_text=True)
            self.assertIn("听力", html)
            self.assertIn("40/40", html)

        other = appmod.app.test_client()
        accessmod.create_code(code="OTHER01")
        other.post(
            "/api/session/start",
            json={
                "candidate_name": "Other Student",
                "invite_code": "OTHER01",
                "module": "listening",
                "mode": "full",
            },
        )
        stolen = other.get(f"/api/me/submission/{sid}")
        self.assertEqual(stolen.status_code, 404)
        self.assertNotIn("KERRIDGE", stolen.get_data(as_text=True))
        stolen_html = other.get(f"/me/submission/{sid}")
        self.assertEqual(stolen_html.status_code, 404)
        self.assertNotEqual(stolen_html.status_code, 403)


if __name__ == "__main__":
    unittest.main()
