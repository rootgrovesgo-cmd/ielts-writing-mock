#!/usr/bin/env python3
"""Speaking practice bank, routes, and invite gating."""

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

BANK_PATH = ROOT / "prompts" / "speaking_sept2026.json"


class SpeakingBankTests(unittest.TestCase):
    def setUp(self):
        with BANK_PATH.open(encoding="utf-8") as fh:
            self.bank = json.load(fh)

    def test_bank_has_part1_part2_and_part3(self):
        part1 = self.bank.get("part1") or []
        part2 = self.bank.get("part2") or []
        self.assertGreaterEqual(len(part1), 15)
        self.assertGreaterEqual(len(part2), 15)
        self.assertTrue(any(t.get("category") == "core" for t in part1))
        core_ids = {t.get("id") for t in part1}
        self.assertIn("p1-work", core_ids)
        self.assertIn("p1-study", core_ids)
        self.assertIn("p1-hometown", core_ids)
        for topic in part1:
            self.assertTrue(topic.get("id"))
            self.assertTrue(topic.get("topic"))
            questions = topic.get("questions") or []
            self.assertGreaterEqual(len(questions), 3, topic.get("id"))
            self.assertTrue(all(isinstance(q, str) and q.strip() for q in questions))
        part3_sets = 0
        for card in part2:
            self.assertTrue(card.get("id"))
            self.assertTrue(str(card.get("title") or "").startswith("Describe"))
            bullets = card.get("bullets") or []
            self.assertGreaterEqual(len(bullets), 3, card.get("id"))
            self.assertLessEqual(len(bullets), 5, card.get("id"))
            part3 = card.get("part3") or []
            self.assertGreaterEqual(len(part3), 2, card.get("id"))
            part3_sets += 1
        self.assertEqual(part3_sets, len(part2))
        self.assertIn("2026", str(self.bank.get("season") or self.bank.get("season_label") or ""))

    def test_bank_does_not_include_sample_answers(self):
        raw = BANK_PATH.read_text(encoding="utf-8").lower()
        for needle in ("sample answer", "band 7", "band 8", "范文"):
            self.assertNotIn(needle, raw)


class SpeakingRouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        appmod.DATA_DIR = base / "data"
        appmod.SUBMISSIONS_DIR = appmod.DATA_DIR / "submissions"
        appmod.INDEX_PATH = appmod.DATA_DIR / "index.json"
        accessmod.bind(appmod.DATA_DIR)
        appmod.ensure_storage()
        appmod.app.config["TESTING"] = True
        appmod.app.config["SECRET_KEY"] = "test-secret-speaking"
        self.client = appmod.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def _start(self, name="Ada Student", code="CLASS01", module="speaking", mode="full"):
        return self.client.post(
            "/api/session/start",
            json={
                "candidate_name": name,
                "invite_code": code,
                "module": module,
                "mode": mode,
            },
        )

    def test_health_includes_speaking(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["ok"])
        self.assertIn("writing", body["modules"])
        self.assertIn("reading", body["modules"])
        self.assertIn("speaking", body["modules"])

    def test_hub_header_is_speaking_entrance_only(self):
        html = self.client.get("/").get_data(as_text=True)
        header = html.split("<main", 1)[0]
        self.assertIn('href="/speaking">口语题库</a>', header)
        self.assertNotIn('href="/admin">Root Login</a>', header)
        after = html.split("<main", 1)[1]
        self.assertIn('href="/admin">Root Login</a>', after)
        self.assertIn('footer-admin">Teacher</a>', html)
        self.assertIn("/writing", html)
        self.assertIn("/reading", html)

    def test_other_teacher_entries_unchanged(self):
        writing = self.client.get("/writing").get_data(as_text=True)
        self.assertIn('href="/admin">Root Login</a>', writing)
        self.assertIn("Teacher", writing)
        reading = self.client.get("/reading").get_data(as_text=True)
        self.assertIn('href="/admin">Root Login</a>', reading)
        login = self.client.get("/admin/login").get_data(as_text=True)
        self.assertIn("教师后台登录", login)
        self.assertIn('name="username"', login)
        self.assertNotIn("口语题库", login)

    def test_speaking_page_is_practice_checkin(self):
        res = self.client.get("/speaking")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("口语题库", html)
        self.assertIn("Invitation code", html)
        self.assertIn("Candidate name", html)
        self.assertIn("Part 1", html)
        self.assertIn("Part 2", html)
        self.assertIn("Part 3", html)
        self.assertIn("不是计分考试", html)
        self.assertNotIn('href="/admin">Root Login</a>', html.split("<footer", 1)[0])
        self.assertIn('footer-admin">Teacher</a>', html)

    def test_bank_requires_invite_session(self):
        blocked = self.client.get("/api/speaking/bank")
        self.assertEqual(blocked.status_code, 403)
        self.assertFalse(blocked.get_json()["ok"])

        accessmod.create_code(code="CLASS01")
        started = self._start()
        self.assertEqual(started.status_code, 200)
        body = started.get_json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["module"], "speaking")

        bank = self.client.get("/api/speaking/bank")
        self.assertEqual(bank.status_code, 200)
        data = bank.get_json()
        self.assertGreaterEqual(len(data.get("part1") or []), 15)
        self.assertGreaterEqual(len(data.get("part2") or []), 15)
        self.assertTrue(all(card.get("part3") for card in data["part2"]))
        users = accessmod.list_users()
        self.assertEqual(users[0]["speaking_started"], 1)

    def test_invalid_code_still_blocked(self):
        accessmod.create_code(code="CLASS01")
        bad = self._start(code="NO-SUCH")
        self.assertEqual(bad.status_code, 403)
        self.assertEqual(bad.get_json()["error"], "邀请码无效或已失效")
        self.assertEqual(self.client.get("/api/speaking/bank").status_code, 403)


if __name__ == "__main__":
    unittest.main()
