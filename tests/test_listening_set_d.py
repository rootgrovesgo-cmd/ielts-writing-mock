#!/usr/bin/env python3
"""Tests for Academic Listening Set D and multi-set loading/scoring."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
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

PAPER_PATH = ROOT / "prompts" / "listening_set_d.json"
KEYS_PATH = ROOT / "prompts" / "listening_keys_set_d.json"
AUDIO_DIR = ROOT / "static" / "audio" / "listening_set_d"
SET_A_AUDIO_DIR = ROOT / "static" / "audio" / "listening_set_a"
SET_B_AUDIO_DIR = ROOT / "static" / "audio" / "listening_set_b"
SET_C_AUDIO_DIR = ROOT / "static" / "audio" / "listening_set_c"
GENERATOR = ROOT / "tools" / "generate_listening_audio.py"

FORBIDDEN_OFFICIAL = (
    "langridge",
    "kelmara",
    "hartwell",
    "pellam",
    "bayswater",
    "helendale",
)

STUDENT_PATHS = [
    PAPER_PATH,
    ROOT / "templates" / "listening.html",
    ROOT / "templates" / "hub.html",
    ROOT / "static" / "listening.js",
    ROOT / "static" / "listening.css",
    ROOT / "tools" / "listening_script_set_d.py",
    ROOT / "README.md",
]

LABELS = ("预测：", "考点与原文逻辑替换：", "跟音：")
INTERFERENCE = ("不要填", "不要选", "不能选", "不可填")


def load_paper() -> dict:
    return json.loads(PAPER_PATH.read_text(encoding="utf-8"))


def load_keys() -> dict:
    return json.loads(KEYS_PATH.read_text(encoding="utf-8"))


def official_from_keys(keys: dict) -> dict[int, str]:
    return {int(q): meta["answer"] for q, meta in keys["questions"].items()}


def _set_d_script_text() -> str:
    sys.path.insert(0, str(ROOT / "tools"))
    from listening_script_set_d import SECTIONS  # noqa: WPS433

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
        r"^(Tessa|Owen|Duncan Bell|Imogen|Rohan|Dr Sabina Holt|Professor Alec Durrant|Narrator):\s*",
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
    def test_list_includes_set_d_as_fourth_id(self):
        sets = ls.list_listening_sets()
        ids = [item["id"] for item in sets]
        self.assertEqual(ids[:3], ["set-a", "set-b", "set-c"])
        self.assertEqual(ids, ["set-a", "set-b", "set-c", "set-d"])
        self.assertEqual(ls.load_paper_for_set("set-d")["id"], "set-d")
        self.assertEqual(appmod.normalize_listening_set_id("set-d"), "set-d")
        default_paper = ls.load_paper()
        self.assertEqual(default_paper["id"], "set-a")
        self.assertEqual(ls.paper_path_for_set("set-d"), PAPER_PATH)
        self.assertEqual(ls.keys_path_for_set("set-d"), KEYS_PATH)
        self.assertEqual(ls.audio_dir_for_set("set-d"), AUDIO_DIR)


class SetDPaperTests(unittest.TestCase):
    def setUp(self):
        self.paper = load_paper()
        self.keys = load_keys()

    def test_paper_identity_and_question_forms(self):
        self.assertEqual(self.paper["id"], "set-d")
        self.assertEqual(self.paper["title"], "Set D · Academic Listening")
        self.assertEqual(self.paper["check_seconds"], 120)
        self.assertEqual(len(self.paper["sections"]), 4)
        sections = {s["id"]: s for s in self.paper["sections"]}

        types1 = [g["type"] for g in sections[1]["groups"]]
        self.assertEqual(types1, ["notes_table"])
        g1 = sections[1]["groups"][0]
        self.assertEqual((g1["from"], g1["to"]), (1, 10))
        self.assertTrue(any("ONE WORD AND/OR A NUMBER" in line for line in g1["instructions"]))
        self.assertEqual(g1["word_limit"], {"max_words": 1, "allow_number": True})
        self.assertEqual(g1["table"]["headers"], ["Workshop", "Date", "Fee", "What to bring"])
        self.assertEqual(len(g1["table"]["rows"]), 4)

        types2 = [g["type"] for g in sections[2]["groups"]]
        self.assertEqual(types2, ["choose_two", "choose_two", "map"])
        g11, g13, gmap = sections[2]["groups"]
        self.assertEqual((g11["from"], g11["to"]), (11, 12))
        self.assertTrue(any("TWO" in line for line in g11["instructions"]))
        self.assertEqual(len(g11["options"]), 5)
        self.assertEqual((g13["from"], g13["to"]), (13, 14))
        self.assertEqual(len(g13["options"]), 5)
        self.assertEqual((gmap["from"], gmap["to"]), (15, 20))
        self.assertEqual(gmap["options"], list("ABCDEFGH"))
        self.assertEqual([item["q"] for item in gmap["items"]], [15, 16, 17, 18, 19, 20])
        svg = (gmap.get("map") or {}).get("svg") or ""
        self.assertIn("<svg", svg)
        self.assertIn("Holmestead", (gmap.get("map") or {}).get("title") or "")
        self.assertNotIn("<script", svg.lower())
        for letter in "ABCDEFGH":
            self.assertIn(f">{letter}</text>", svg, letter)

        types3 = [g["type"] for g in sections[3]["groups"]]
        self.assertEqual(types3, ["choose_two", "choose_two", "choose_two", "matching"])
        g21, g23, g25, gflow = sections[3]["groups"]
        self.assertEqual((g21["from"], g21["to"]), (21, 22))
        self.assertEqual((g23["from"], g23["to"]), (23, 24))
        self.assertEqual((g25["from"], g25["to"]), (25, 26))
        self.assertEqual((gflow["from"], gflow["to"]), (27, 30))
        self.assertTrue(any("flow-chart" in line.lower() for line in gflow["instructions"]))
        self.assertEqual([item["key"] for item in gflow["legend"]], list("ABCDEFG"))
        self.assertEqual([item["q"] for item in gflow["items"]], [27, 28, 29, 30])
        flow_svg = (gflow.get("diagram") or {}).get("svg") or ""
        self.assertIn("<svg", flow_svg)
        self.assertNotIn("<script", flow_svg.lower())

        s4 = sections[4]["groups"]
        self.assertEqual(s4[0]["type"], "notes")
        self.assertEqual((s4[0]["from"], s4[0]["to"]), (31, 40))
        self.assertTrue(any("ONE WORD ONLY" in line for line in s4[0]["instructions"]))
        self.assertEqual(s4[0]["word_limit"], {"max_words": 1, "allow_number": False})

    def test_forty_questions_and_no_keys_in_student_json(self):
        raw = PAPER_PATH.read_text(encoding="utf-8")
        lowered = raw.lower()
        self.assertNotIn("explanation", raw)
        self.assertNotIn("transcript", lowered)
        self.assertNotIn('"answer":', raw)
        self.assertNotIn("预测", raw)
        self.assertNotIn("考点与原文逻辑替换", raw)
        self.assertNotIn("跟音", raw)
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lowered, word)
        questions = []
        for section in self.paper["sections"]:
            for group in section["groups"]:
                questions.extend(range(group["from"], group["to"] + 1))
        self.assertEqual(questions, list(range(1, 41)))
        self.assertEqual(len(set(questions)), 40)

    def test_student_facing_files_have_no_official_traces(self):
        for path in STUDENT_PATHS + [KEYS_PATH, GENERATOR]:
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotRegex(text, r"(?:cambridge(?: ielts)?|剑)\s*\d+")
            for word in FORBIDDEN_OFFICIAL:
                self.assertNotIn(word, text, f"{path}: {word}")

    def test_start_page_html_contains_set_d(self):
        html = (ROOT / "templates" / "listening.html").read_text(encoding="utf-8")
        self.assertIn("Set D · Academic Listening", html)
        self.assertIn('value="set-d"', html)
        self.assertIn('value="set-a"', html)
        self.assertIn('value="set-b"', html)
        self.assertIn('value="set-c"', html)

    def test_localstorage_key_is_set_specific(self):
        js = (ROOT / "static" / "listening.js").read_text(encoding="utf-8")
        self.assertIn('return "ielts-listening-" + id', js)
        self.assertIn("function storageKey(setId)", js)
        self.assertIn("group.diagram", js)

    def test_keys_have_structured_explanations_and_transcripts(self):
        self.assertEqual(self.keys["set_id"], "set-d")
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

    def test_audio_quotes_come_from_set_d_script_and_pairs_differ(self):
        script = _set_d_script_text()
        self.assertIn("The winter pruning workshop is on the nineteenth of February", script)
        questions = self.keys["questions"]
        for num in range(1, 41):
            quote = questions[str(num)]["audio_quote"]
            self.assertTrue(
                _quote_has_script_span(quote, script),
                f"Q{num} audio_quote is not drawn from the Set D script: {quote[:180]}",
            )
        for left, right in ((11, 12), (13, 14), (21, 22), (23, 24), (25, 26)):
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
        for q in range(1, 11):
            self.assertEqual(questions[str(q)]["word_limit"], {"max_words": 1, "allow_number": True}, q)
        for q in range(31, 41):
            self.assertEqual(questions[str(q)]["word_limit"], {"max_words": 1, "allow_number": False}, q)

    def test_map_and_matching_answers_are_not_a_simple_run(self):
        questions = self.keys["questions"]
        map_letters = [questions[str(q)]["answer"] for q in range(15, 21)]
        self.assertEqual(map_letters, list("FH DACE".replace(" ", "")))
        self.assertNotEqual(map_letters, list("ABCDEF"))
        flow_letters = [questions[str(q)]["answer"] for q in range(27, 31)]
        self.assertEqual(flow_letters, list("BDAG"))
        self.assertNotEqual(flow_letters, list("ABCD"))

    def test_generator_uses_normal_rate_for_set_d_only(self):
        source = GENERATOR.read_text(encoding="utf-8")
        self.assertIn('return SECTIONS, VOICES, out_dir, paper_path, "+0%"', source)
        self.assertIn('choices=["set-a", "set-b", "set-c", "set-d"]', source)
        self.assertNotRegex(source, r"atempo=")
        self.assertNotRegex(source, r"playbackRate\s*=")
        sys.path.insert(0, str(ROOT / "tools"))
        import generate_listening_audio as gen  # noqa: WPS433

        _, _, out_dir, paper_path, rate = gen.script_config("set-d")
        self.assertEqual(rate, "+0%")
        self.assertEqual(out_dir, AUDIO_DIR)
        self.assertEqual(paper_path, PAPER_PATH)
        for other in ("set-a", "set-b", "set-c"):
            _, _, _, _, other_rate = gen.script_config(other)
            self.assertEqual(other_rate, "+25%", other)


class SectionFourRevisionTests(unittest.TestCase):
    ANSWERS = {
        31: "oxygen", 32: "cracks", 33: "slope", 34: "plastic", 35: "birch",
        36: "acidity", 37: "straw", 38: "wells", 39: "methane", 40: "drought",
    }
    # Frozen signatures of Sections 1–3 before the Section 4 revision.
    UNCHANGED = {'paper': '71c4054c5615792d97e6f963dd646f38a75b23d14874d934dbc7898b0df1398d', 'keys': 'd88bbcd434858452457600b026a99a07cf0f7a6c40beba7d6adc40c5008538e2', 'transcripts': 'db4a2b10fef61c4781faf0993ed039175d4b173d2d662f9a1a918146d5f807b1', 'cues': '340364bca1e64a4e5b7fbe59944e6aedf368c9d2dbea269e0c6442dad7ea4b39', 'audio': {'static/audio/listening_set_d/section1.mp3': '88735b1cd3a9473f67586b000727ee7f22d1e0c0380986ad1a209f36d37a33a3', 'static/audio/listening_set_d/section3.mp3': '4add3a992f68511dd18a2f0b198d28c14a5ee140f238f060a07fb3cfe1172c33', 'static/audio/listening_set_d/section2.mp3': 'c592680851fb53e13e2f28e3373bf25fe97e8a5838dfecb301abe164d0d20fad'}}

    @staticmethod
    def signature(obj):
        return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

    def test_sections_one_to_three_have_not_changed(self):
        paper = load_paper()
        keys = load_keys()
        self.assertEqual(self.signature(paper["sections"][:3]), self.UNCHANGED["paper"])
        self.assertEqual(self.signature({q: v for q, v in keys["questions"].items() if int(q) < 31}), self.UNCHANGED["keys"])
        self.assertEqual(self.signature({s: text for s, text in keys["transcripts"].items() if int(s) < 4}), self.UNCHANGED["transcripts"])
        sys.path.insert(0, str(ROOT / "tools"))
        import listening_script_set_d as script
        self.assertEqual(self.signature({str(i): script.SECTIONS[i] for i in (1, 2, 3)}), self.UNCHANGED["cues"])
        for relative, digest in self.UNCHANGED["audio"].items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative)

    def test_ecology_paper_and_exact_sequential_evidence(self):
        paper, keys = load_paper(), load_keys()
        section = paper["sections"][3]
        group = section["groups"][0]
        self.assertIn("raised bog", section["context"])
        self.assertEqual(group["word_limit"], {"max_words": 1, "allow_number": False})
        self.assertEqual((group["type"], group["from"], group["to"]), ("notes", 31, 40))
        self.assertEqual(len(group["notes"]["sections"]), 4)
        blanks = [part["q"] for sub in group["notes"]["sections"] for row in sub["items"] for part in row["parts"] if isinstance(part, dict)]
        self.assertEqual(blanks, list(range(31, 41)))
        transcript = keys["transcripts"]["4"]
        positions = []
        for q, answer in self.ANSWERS.items():
            meta = keys["questions"][str(q)]
            self.assertEqual(meta["answer"], answer)
            self.assertEqual(len(answer.split()), 1)
            quote = meta["audio_quote"].split("“", 1)[1].rsplit("”", 1)[0]
            self.assertIn(quote, transcript, q)
            self.assertIn(answer, quote.lower(), q)
            positions.append(transcript.index(quote))
            for forbidden in ("不要误填", "不要选", "不能选", "干扰项提示"):
                self.assertNotIn(forbidden, meta["explanation"])
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("cinema", transcript.lower())
        self.assertNotIn("cinema", json.dumps(section).lower())

    def test_ecology_scoring_and_plausible_distractors(self):
        keys = load_keys()
        correct = ls.score_paper({str(q): a.upper() for q, a in self.ANSWERS.items()}, mode="section4", keys=keys)
        self.assertEqual((correct["score"], correct["total"]), (10, 10))
        self.assertIsNone(correct["band_estimate"])
        distractors = {
            31: "temperature", 32: "barriers", 33: "length", 34: "timber", 35: "willow",
            36: "convenience", 37: "fertiliser", 38: "sensors", 39: "carbon dioxide", 40: "flooding",
        }
        self.assertEqual(ls.score_paper(distractors, mode="section4", keys=keys)["score"], 0)
        for q, answer in self.ANSWERS.items():
            self.assertEqual(ls.score_paper({q: "the " + answer}, mode="section4", keys=keys)["score"], 0, q)
        singulars = {32: "crack", 38: "well"}
        self.assertEqual(ls.score_paper(singulars, mode="section4", keys=keys)["score"], 0)

    def test_ecology_audio_pauses_normal_rate_and_final_check(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import listening_script_set_d as script
        import generate_listening_audio as gen
        self.assertEqual(script.TTS_RATE, "+0%")
        self.assertEqual(gen.script_config("set-d")[-1], "+0%")
        self.assertEqual([cue[1] for cue in script.SECTION4 if cue[0] == "gap"], [25, 30])
        self.assertEqual(script.LOOK, 25)
        self.assertEqual(script.CHECK, 30)
        self.assertGreater(script.word_counts()[4], 1000)
        paper = load_paper()
        self.assertEqual(paper["check_seconds"], 120)
        audio = AUDIO_DIR / "section4.mp3"
        result = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,sample_rate,channels", "-of", "json", str(audio)
        ], text=True))
        seconds = float(result["format"]["duration"])
        self.assertEqual(round(seconds), paper["sections"][3]["audio"]["duration_seconds"])
        self.assertGreater(seconds, 400)
        self.assertLess(seconds, 600)
        stream = result["streams"][0]
        self.assertEqual(stream["codec_name"], "mp3")
        self.assertEqual(stream["channels"], 1)
        self.assertEqual(stream["sample_rate"], "24000")
        self.assertEqual(ls.duration_for_mode("full", paper), sum(ls.section_durations(paper).values()) + 120)


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
        # Official 11-12 are B and D. Any order scores 2.
        result = ls.score_paper({"11": "D", "12": "B"}, mode="full", keys=self.keys)
        by_q = {row["q"]: row for row in result["marking"]}
        self.assertTrue(by_q[11]["ok"])
        self.assertTrue(by_q[12]["ok"])
        self.assertEqual(result["score"], 2)
        self.assertEqual(by_q[11]["correct"], "B, D")
        result2 = ls.score_paper({"11": "B", "12": "A"}, mode="full", keys=self.keys)
        self.assertEqual(result2["score"], 1)
        result3 = ls.score_paper({"11": "B", "12": "B"}, mode="full", keys=self.keys)
        self.assertEqual(result3["score"], 1)
        result4 = ls.score_paper({"11": "A", "12": "C"}, mode="full", keys=self.keys)
        self.assertEqual(result4["score"], 0)

    def test_map_matching_and_notes(self):
        answers = {"15": "F", "16": "H", "27": "B", "28": "D", "29": "A", "30": "G", "31": "oxygen"}
        result = ls.score_paper(answers, mode="full", keys=self.keys)
        self.assertEqual(result["score"], 7)
        wrong = ls.score_paper({"15": "A", "27": "C", "31": "fees"}, mode="full", keys=self.keys)
        self.assertEqual(wrong["score"], 0)

    def test_listed_alternatives_and_word_limit(self):
        answers = {str(q): a for q, a in self.official.items()}
        answers["1"] = "19th February"
        answers["2"] = "£32"
        answers["7"] = "16.5"
        answers["35"] = "BIRCH"
        result = ls.score_paper(answers, mode="full", keys=self.keys)
        self.assertEqual(result["score"], 40)
        over = ls.score_paper({31: "the supply of oxygen"}, mode="full", keys=self.keys)
        by_q = {row["q"]: row for row in over["marking"]}
        self.assertFalse(by_q[31]["ok"])
        number_blocked = ls.score_paper({33: "2020"}, mode="full", keys=self.keys)
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
        appmod.app.config["SECRET_KEY"] = "test-secret-listening-d"
        self.client = appmod.app.test_client()
        self.keys = load_keys()
        self.official = official_from_keys(self.keys)

    def tearDown(self):
        self.tmp.cleanup()

    def _create_code(self, code="TESTCODED"):
        return accessmod.create_code(code=code)

    def _start(self, name="Test Candidate", code="TESTCODED", module="listening", mode="full"):
        return self.client.post(
            "/api/session/start",
            json={
                "candidate_name": name,
                "invite_code": code,
                "module": module,
                "mode": mode,
            },
        )

    def test_sets_endpoint_includes_set_d(self):
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
        denied = self.client.get("/api/listening/paper?set=set-d")
        self.assertEqual(denied.status_code, 403)
        audio_denied = self.client.get("/api/listening/audio/1?set=set-d")
        self.assertEqual(audio_denied.status_code, 403)

        self._create_code()
        self.assertEqual(self._start().status_code, 200)

        res = self.client.get("/api/listening/paper?set=set-d")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["id"], "set-d")
        raw = res.get_data(as_text=True)
        lowered = raw.lower()
        self.assertNotIn("explanation", raw)
        self.assertNotIn("transcript", lowered)
        self.assertNotIn('"answer":', raw)
        self.assertNotIn("预测", raw)
        self.assertNotIn("考点与原文逻辑替换", raw)
        for word in FORBIDDEN_OFFICIAL:
            self.assertNotIn(word, lowered, word)
        self.assertIn("Willowfen", raw)
        self.assertIn("Holmestead", raw)
        self.assertNotIn("Langridge", raw)
        self.assertNotIn("Hartwell", raw)
        self.assertNotIn("Pellam", raw)
        self.assertNotIn("Kelmara", raw)

        missing = self.client.get("/api/listening/paper?set=set-z")
        self.assertEqual(missing.status_code, 404)

        audio_d = self.client.get("/api/listening/audio/1?set=set-d")
        path_d = AUDIO_DIR / "section1.mp3"
        self.assertTrue(path_d.is_file(), "Set D section1.mp3 must be generated")
        self.assertEqual(audio_d.status_code, 200)
        self.assertTrue((audio_d.headers.get("Content-Type") or "").startswith("audio/mpeg"))
        body_d = audio_d.get_data()
        self.assertGreater(len(body_d), 1000)
        self.assertEqual(len(body_d), path_d.stat().st_size)
        for other_dir in (SET_A_AUDIO_DIR, SET_B_AUDIO_DIR, SET_C_AUDIO_DIR):
            other = other_dir / "section1.mp3"
            if other.is_file():
                self.assertNotEqual(body_d[:4000], other.read_bytes()[:4000], other_dir)

    def test_submit_set_d_stores_id_and_uses_set_d_keys(self):
        self._create_code()
        self.assertEqual(self._start().status_code, 200)
        answers = {str(q): a for q, a in self.official.items()}
        answers["1"] = "poetry"
        res = self.client.post(
            "/api/listening/submit",
            json={
                "candidate_name": "Test Candidate",
                "mode": "full",
                "prompt_set_id": "set-d",
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
        self.assertEqual(saved["prompt_set_id"], "set-d")
        self.assertEqual(saved["module"], "listening")
        self.assertEqual(saved["score"], 39)
        by_q = {row["q"]: row for row in saved["marking"]}
        self.assertFalse(by_q[1]["ok"])
        self.assertIn("february", by_q[1]["correct"].lower())

        review = self.client.get(f"/api/me/submission/{sid}")
        self.assertEqual(review.status_code, 200)
        payload = review.get_json()
        dumped = json.dumps(payload.get("paper") or payload, ensure_ascii=False)
        self.assertIn("Willowfen", dumped)
        transcripts = json.dumps(payload.get("transcripts") or {}, ensure_ascii=False)
        self.assertIn("Willowfen", transcripts)
        self.assertNotIn("Fraser", transcripts)
        self.assertNotIn("Langridge", transcripts)
        self.assertNotIn("Hartwell", transcripts)


class AudioFileTests(unittest.TestCase):
    def test_set_d_audio_files_exist_and_durations_are_recorded(self):
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
