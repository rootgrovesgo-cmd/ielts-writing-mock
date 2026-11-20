#!/usr/bin/env python3
"""Tests for Academic Listening Set C and multi-set loading/scoring."""

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
import listening_scoring as ls  # noqa: E402

PAPER_PATH = ROOT / "prompts" / "listening_set_c.json"
KEYS_PATH = ROOT / "prompts" / "listening_keys_set_c.json"
AUDIO_DIR = ROOT / "static" / "audio" / "listening_set_c"
SET_A_AUDIO_DIR = ROOT / "static" / "audio" / "listening_set_a"
SET_B_AUDIO_DIR = ROOT / "static" / "audio" / "listening_set_b"

FORBIDDEN_OFFICIAL = (
    "海外真题",
    "10.11",
    "第19号",
    "harbour city",
    "bayswater",
    "helendale",
    "central street",
    "mount fago",
    "mount herto",
    "birds in new zealand",
    "jill",
)

STUDENT_PATHS = [
    PAPER_PATH,
    ROOT / "templates" / "listening.html",
    ROOT / "templates" / "hub.html",
    ROOT / "static" / "listening.js",
    ROOT / "static" / "listening.css",
]

LABELS = ("预测：", "考点与原文逻辑替换：", "跟音：")
INTERFERENCE = ("不要填", "不要选", "不能选", "不可填")


def load_paper() -> dict:
    return json.loads(PAPER_PATH.read_text(encoding="utf-8"))


def load_keys() -> dict:
    return json.loads(KEYS_PATH.read_text(encoding="utf-8"))


def official_from_keys(keys: dict) -> dict[int, str]:
    return {int(q): meta["answer"] for q, meta in keys["questions"].items()}


def _set_c_script_text() -> str:
    sys.path.insert(0, str(ROOT / "tools"))
    from listening_script_set_c import SECTIONS  # noqa: WPS433

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
        r"^(Gareth|Callie|Mara Ellison|Keira|Felix|Professor Rhea Coldwell|Narrator):\s*",
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


class SetListTests(unittest.TestCase):
    def test_list_includes_set_c_as_third_id(self):
        sets = ls.list_listening_sets()
        ids = [item["id"] for item in sets]
        self.assertEqual(ids[:2], ["set-a", "set-b"])
        self.assertEqual(ids, ["set-a", "set-b", "set-c", "set-d"])
        self.assertEqual(ls.load_paper_for_set("set-c")["id"], "set-c")
        self.assertEqual(appmod.normalize_listening_set_id("set-c"), "set-c")
        default_paper = ls.load_paper()
        self.assertEqual(default_paper["id"], "set-a")


class SetCPaperTests(unittest.TestCase):
    def setUp(self):
        self.paper = load_paper()
        self.keys = load_keys()

    def test_paper_identity_and_question_forms(self):
        self.assertEqual(self.paper["id"], "set-c")
        self.assertEqual(self.paper["title"], "Set C · Academic Listening")
        self.assertEqual(self.paper["check_seconds"], 120)
        self.assertEqual(len(self.paper["sections"]), 4)
        sections = {s["id"]: s for s in self.paper["sections"]}

        types1 = [g["type"] for g in sections[1]["groups"]]
        self.assertEqual(types1, ["notes", "notes_table"])
        g1, g2 = sections[1]["groups"]
        self.assertEqual((g1["from"], g1["to"]), (1, 5))
        self.assertTrue(any("NO MORE THAN TWO WORDS AND/OR A NUMBER" in line for line in g1["instructions"]))
        self.assertEqual(g1["word_limit"], {"max_words": 2, "allow_number": True})
        self.assertEqual((g2["from"], g2["to"]), (6, 10))
        self.assertEqual(g2["type"], "notes_table")
        self.assertTrue(any("ONE WORD AND/OR A NUMBER" in line for line in g2["instructions"]))
        self.assertEqual(g2["word_limit"], {"max_words": 1, "allow_number": True})
        self.assertEqual(g2["table"]["headers"], ["Ticket", "Cash", "Travel card"])
        self.assertEqual(len(g2["table"]["rows"]), 4)

        types2 = [g["type"] for g in sections[2]["groups"]]
        self.assertEqual(types2, ["mcq", "choose_two", "choose_two"])
        g11, g17, g19 = sections[2]["groups"]
        self.assertEqual((g11["from"], g11["to"]), (11, 16))
        self.assertEqual(len(g11["items"]), 6)
        self.assertEqual((g17["from"], g17["to"]), (17, 18))
        self.assertTrue(any("TWO" in line for line in g17["instructions"]))
        self.assertIn("NOT", g17["stem"])
        self.assertEqual(len(g17["options"]), 5)
        self.assertEqual((g19["from"], g19["to"]), (19, 20))
        self.assertTrue(any("TWO" in line for line in g19["instructions"]))
        self.assertEqual(len(g19["options"]), 5)

        types3 = [g["type"] for g in sections[3]["groups"]]
        self.assertEqual(types3, ["mcq", "matching"])
        g21, g26 = sections[3]["groups"]
        self.assertEqual((g21["from"], g21["to"]), (21, 25))
        self.assertEqual(len(g21["items"]), 5)
        self.assertEqual((g26["from"], g26["to"]), (26, 30))
        self.assertEqual(len(g26["legend"]), 6)
        self.assertEqual([item["key"] for item in g26["legend"]], list("ABCDEF"))
        self.assertEqual([item["q"] for item in g26["items"]], [26, 27, 28, 29, 30])

        s4 = sections[4]["groups"]
        self.assertEqual(s4[0]["type"], "notes")
        self.assertEqual((s4[0]["from"], s4[0]["to"]), (31, 40))
        self.assertTrue(any("ONE WORD ONLY" in line for line in s4[0]["instructions"]))
        self.assertEqual(s4[0]["word_limit"], {"max_words": 1, "allow_number": False})

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
        self.assertNotIn("预测", dumped)
        lower = dumped.lower()
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lower, word)
        for path in STUDENT_PATHS:
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            for word in FORBIDDEN_OFFICIAL:
                self.assertNotIn(word, lowered, f"{word!r} in {path}")

    def test_start_page_html_contains_set_c(self):
        html = (ROOT / "templates" / "listening.html").read_text(encoding="utf-8")
        self.assertIn("Set C · Academic Listening", html)
        self.assertIn('value="set-c"', html)
        self.assertIn('value="set-a"', html)
        self.assertIn('value="set-b"', html)

    def test_localstorage_key_is_set_specific(self):
        js = (ROOT / "static" / "listening.js").read_text(encoding="utf-8")
        self.assertIn('return "ielts-listening-" + id', js)
        self.assertIn("function storageKey(setId)", js)

    def test_keys_have_structured_explanations_and_transcripts(self):
        self.assertEqual(self.keys["set_id"], "set-c")
        questions = self.keys["questions"]
        self.assertEqual(sorted(int(q) for q in questions), list(range(1, 41)))
        for q, meta in questions.items():
            self.assertTrue(meta.get("answer"), q)
            self.assertTrue(meta.get("type"), q)
            for field in ("prediction", "logic", "audio_quote", "explanation"):
                self.assertTrue(str(meta.get(field) or "").strip(), f"Q{q} missing {field}")
            text = meta["explanation"]
            for label in LABELS:
                self.assertIn(label, text, f"Q{q} missing {label}")
            self.assertEqual(text, explain_format.compose_explanation(meta), q)
            for phrase in INTERFERENCE:
                self.assertNotIn(phrase, text, f"Q{q} has {phrase}")
                self.assertNotIn(phrase, meta.get("logic") or "", f"Q{q} logic has {phrase}")
        transcripts = self.keys.get("transcripts") or {}
        self.assertEqual(set(transcripts), {"1", "2", "3", "4"})
        for sid, text in transcripts.items():
            self.assertGreater(len(text.split()), 100, sid)
            self.assertIn("Narrator:", text)

    def test_audio_quotes_come_from_set_c_script_and_pairs_differ(self):
        script = _set_c_script_text()
        self.assertIn("The first bus actually departs at eight fifteen", script)
        questions = self.keys["questions"]
        for num in range(1, 41):
            quote = questions[str(num)]["audio_quote"]
            self.assertTrue(
                _quote_has_script_span(quote, script),
                f"Q{num} audio_quote is not drawn from the Set C script: {quote[:180]}",
            )
        for left, right in ((17, 18), (19, 20)):
            a = questions[str(left)]
            b = questions[str(right)]
            self.assertEqual(a.get("pair"), [left, right])
            self.assertEqual(b.get("pair"), [left, right])
            self.assertNotEqual(a["logic"], b["logic"], (left, right))
            self.assertNotEqual(a["audio_quote"], b["audio_quote"], (left, right))
            self.assertTrue(a["answer"] in a["logic"], left)
            self.assertTrue(b["answer"] in b["logic"], right)

    def test_blank_word_limits_on_keys(self):
        questions = self.keys["questions"]
        for q in range(1, 6):
            self.assertEqual(questions[str(q)]["word_limit"], {"max_words": 2, "allow_number": True}, q)
        for q in range(6, 11):
            self.assertEqual(questions[str(q)]["word_limit"], {"max_words": 1, "allow_number": True}, q)
        for q in range(31, 41):
            self.assertEqual(questions[str(q)]["word_limit"], {"max_words": 1, "allow_number": False}, q)


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

    def test_choose_two_order_partial_and_repeats(self):
        # Official 17-18 are B and D. Any order scores 2.
        result = ls.score_paper({"17": "D", "18": "B"}, mode="full", keys=self.keys)
        by_q = {row["q"]: row for row in result["marking"]}
        self.assertTrue(by_q[17]["ok"])
        self.assertTrue(by_q[18]["ok"])
        self.assertEqual(result["score"], 2)
        self.assertEqual(by_q[17]["correct"], "B, D")
        result2 = ls.score_paper({"17": "B", "18": "A"}, mode="full", keys=self.keys)
        self.assertEqual(result2["score"], 1)
        result3 = ls.score_paper({"17": "B", "18": "B"}, mode="full", keys=self.keys)
        self.assertEqual(result3["score"], 1)
        result4 = ls.score_paper({"17": "A", "18": "C"}, mode="full", keys=self.keys)
        self.assertEqual(result4["score"], 0)

    def test_matching_and_mcq_letters(self):
        answers = {"21": "B", "26": "A", "27": "B", "28": "C", "29": "D", "30": "E"}
        result = ls.score_paper(answers, mode="full", keys=self.keys)
        self.assertEqual(result["score"], 6)
        wrong = ls.score_paper({"21": "A", "26": "F"}, mode="full", keys=self.keys)
        self.assertEqual(wrong["score"], 0)

    def test_listed_alternatives_and_word_limit(self):
        answers = {str(q): a for q, a in self.official.items()}
        answers["4"] = "r12"
        answers["6"] = "£5.80"
        answers["10"] = "program"
        answers["32"] = "Summer"
        result = ls.score_paper(answers, mode="full", keys=self.keys)
        self.assertEqual(result["score"], 40)
        over = ls.score_paper({31: "sea grass beds"}, mode="full", keys=self.keys)
        by_q = {row["q"]: row for row in over["marking"]}
        self.assertFalse(by_q[31]["ok"])
        number_blocked = ls.score_paper({33: "1996"}, mode="full", keys=self.keys)
        by_q = {row["q"]: row for row in number_blocked["marking"]}
        self.assertFalse(by_q[33]["ok"])


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
        appmod.app.config["SECRET_KEY"] = "test-secret-listening-c"
        self.client = appmod.app.test_client()
        self.keys = load_keys()
        self.official = official_from_keys(self.keys)

    def tearDown(self):
        self.tmp.cleanup()

    def _create_code(self, code="TESTCODEC"):
        return accessmod.create_code(code=code)

    def _start(self, name="Test Candidate", code="TESTCODEC", module="listening", mode="full"):
        return self.client.post(
            "/api/session/start",
            json={
                "candidate_name": name,
                "invite_code": code,
                "module": module,
                "mode": mode,
            },
        )

    def test_sets_endpoint_includes_set_c(self):
        denied = self.client.get("/api/listening/sets")
        self.assertEqual(denied.status_code, 403)
        self._create_code()
        self.assertEqual(self._start().status_code, 200)
        res = self.client.get("/api/listening/sets")
        self.assertEqual(res.status_code, 200)
        ids = [item["id"] for item in res.get_json()]
        self.assertEqual(ids, ["set-a", "set-b", "set-c", "set-d"])
        default = self.client.get("/api/listening/paper")
        self.assertEqual(default.status_code, 200)
        self.assertEqual(default.get_json()["id"], "set-a")

    def test_paper_and_audio_require_session_hide_keys_and_are_not_other_sets(self):
        denied = self.client.get("/api/listening/paper?set=set-c")
        self.assertEqual(denied.status_code, 403)
        audio_denied = self.client.get("/api/listening/audio/1?set=set-c")
        self.assertEqual(audio_denied.status_code, 403)

        self._create_code()
        self.assertEqual(self._start().status_code, 200)

        res = self.client.get("/api/listening/paper?set=set-c")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["id"], "set-c")
        raw = res.get_data(as_text=True)
        lowered = raw.lower()
        self.assertNotIn("explanation", raw)
        self.assertNotIn("transcript", lowered)
        self.assertNotIn('"answer":', raw)
        self.assertNotIn("预测", raw)
        self.assertNotIn("考点与原文逻辑替换", raw)
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lowered, word)
        self.assertIn("Langridge", raw)
        self.assertNotIn("Hartwell", raw)
        self.assertNotIn("Pellam", raw)
        self.assertNotIn("Ink & Timber", raw)

        missing = self.client.get("/api/listening/paper?set=set-z")
        self.assertEqual(missing.status_code, 404)

        audio_c = self.client.get("/api/listening/audio/1?set=set-c")
        path_c = AUDIO_DIR / "section1.mp3"
        self.assertTrue(path_c.is_file(), "Set C section1.mp3 must be generated")
        self.assertEqual(audio_c.status_code, 200)
        self.assertTrue((audio_c.headers.get("Content-Type") or "").startswith("audio/mpeg"))
        body_c = audio_c.get_data()
        self.assertGreater(len(body_c), 1000)
        self.assertEqual(len(body_c), path_c.stat().st_size)
        for other_dir in (SET_A_AUDIO_DIR, SET_B_AUDIO_DIR):
            other = other_dir / "section1.mp3"
            if other.is_file():
                self.assertNotEqual(body_c[:4000], other.read_bytes()[:4000], other_dir)

    def test_submit_set_c_stores_id_and_uses_set_c_keys(self):
        self._create_code()
        self.assertEqual(self._start().status_code, 200)
        answers = {str(q): a for q, a in self.official.items()}
        # A Set A / wrong answer must not be marked correct against Set C keys.
        answers["1"] = "poetry"
        res = self.client.post(
            "/api/listening/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "full",
                "prompt_set_id": "set-c",
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
        self.assertEqual(saved["prompt_set_id"], "set-c")
        self.assertEqual(saved["module"], "listening")
        self.assertEqual(saved["score"], 39)
        by_q = {row["q"]: row for row in saved["marking"]}
        self.assertFalse(by_q[1]["ok"])
        self.assertEqual(by_q[1]["correct"].lower(), "8.15")

        review = self.client.get(f"/api/me/submission/{sid}")
        self.assertEqual(review.status_code, 200)
        payload = review.get_json()
        dumped = json.dumps(payload.get("paper") or payload, ensure_ascii=False)
        self.assertIn("Kelmara", dumped)
        transcripts = json.dumps(payload.get("transcripts") or {}, ensure_ascii=False)
        self.assertIn("Langridge", transcripts)
        self.assertNotIn("Fraser", transcripts)
        self.assertNotIn("Hartwell", transcripts)
        self.assertNotIn("Pellam", transcripts)


class AudioFileTests(unittest.TestCase):
    def test_set_c_audio_files_exist_and_durations_are_recorded(self):
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
