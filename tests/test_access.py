#!/usr/bin/env python3
"""Access control tests: admin login, invitation codes, and student sessions."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import access as accessmod  # noqa: E402
import app as appmod  # noqa: E402

# Throwaway credentials used only in tests. Not production values.
TEST_ADMIN_USER = "TestAdmin"
TEST_ADMIN_PASS = "test-access-pass-9f3c"
ADMIN_ENV = (
    "IELTS_ADMIN_USERNAME",
    "IELTS_ADMIN_PASSWORD",
    "IELTS_ADMIN_PASSWORD_HASH",
)


class AccessTestCase(unittest.TestCase):
    def setUp(self):
        self._env_backup = {key: os.environ.get(key) for key in ADMIN_ENV}
        self._clear_admin_env()
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        appmod.DATA_DIR = base / "data"
        appmod.SUBMISSIONS_DIR = appmod.DATA_DIR / "submissions"
        appmod.INDEX_PATH = appmod.DATA_DIR / "index.json"
        accessmod.bind(appmod.DATA_DIR)
        appmod.ensure_storage()
        appmod.app.config["TESTING"] = True
        appmod.app.config["SECRET_KEY"] = "test-secret-access"
        self.client = appmod.app.test_client()

    def tearDown(self):
        self._clear_admin_env()
        for key, value in self._env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def _clear_admin_env(self):
        for key in ADMIN_ENV:
            os.environ.pop(key, None)

    def _set_admin(self, user=TEST_ADMIN_USER, password=TEST_ADMIN_PASS, pw_hash=None):
        self._clear_admin_env()
        if user:
            os.environ["IELTS_ADMIN_USERNAME"] = user
        if pw_hash:
            os.environ["IELTS_ADMIN_PASSWORD_HASH"] = pw_hash
        elif password:
            os.environ["IELTS_ADMIN_PASSWORD"] = password

    def _login_admin(self, user=TEST_ADMIN_USER, password=TEST_ADMIN_PASS, **kwargs):
        return self.client.post(
            "/admin/login",
            data={"username": user, "password": password},
            **kwargs,
        )

    def _start(self, name="Ada Student", code="CLASS01", module="writing", mode="full"):
        return self.client.post(
            "/api/session/start",
            json={
                "candidate_name": name,
                "invite_code": code,
                "module": module,
                "mode": mode,
            },
        )


class AdminAuthTests(AccessTestCase):
    def test_login_fails_when_env_unset(self):
        res = self._login_admin()
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("用户名或密码错误", html)
        # Still cannot reach the portal.
        portal = self.client.get("/admin")
        self.assertEqual(portal.status_code, 302)
        self.assertIn("/admin/login", portal.headers.get("Location", ""))

    def test_wrong_credentials_fail_with_generic_error(self):
        self._set_admin()
        wrong_user = self._login_admin(user="NotTheAdmin")
        self.assertEqual(wrong_user.status_code, 200)
        self.assertIn("用户名或密码错误", wrong_user.get_data(as_text=True))

        wrong_pass = self._login_admin(password="wrong-password")
        self.assertEqual(wrong_pass.status_code, 200)
        self.assertIn("用户名或密码错误", wrong_pass.get_data(as_text=True))

    def test_login_succeeds_with_env_credentials(self):
        self._set_admin()
        res = self._login_admin(follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.headers.get("Location", "").endswith("/admin"))
        portal = self.client.get("/admin")
        self.assertEqual(portal.status_code, 200)
        self.assertIn("学生答卷列表", portal.get_data(as_text=True))

    def test_old_default_password_does_not_work(self):
        # Fail closed when env is missing, even with the former default password.
        res = self._login_admin(password="ielts2026")
        self.assertEqual(res.status_code, 200)
        self.assertIn("用户名或密码错误", res.get_data(as_text=True))

        # Also rejected when a real admin account is configured.
        self._set_admin()
        res2 = self._login_admin(password="ielts2026")
        self.assertEqual(res2.status_code, 200)
        self.assertIn("用户名或密码错误", res2.get_data(as_text=True))
        portal = self.client.get("/admin")
        self.assertEqual(portal.status_code, 302)

    def test_password_hash_is_accepted(self):
        self._set_admin(
            password=None,
            pw_hash=generate_password_hash(TEST_ADMIN_PASS),
        )
        res = self._login_admin(follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        portal = self.client.get("/admin")
        self.assertEqual(portal.status_code, 200)


class InviteAndSessionTests(AccessTestCase):
    def test_start_requires_name_and_code(self):
        accessmod.create_code(code="CLASS01")
        no_name = self._start(name="")
        self.assertEqual(no_name.status_code, 400)
        self.assertEqual(no_name.get_json()["error"], "请输入姓名")

        no_code = self.client.post(
            "/api/session/start",
            json={"candidate_name": "Ada Student", "module": "writing", "mode": "full"},
        )
        self.assertEqual(no_code.status_code, 400)
        self.assertEqual(no_code.get_json()["error"], "请输入邀请码")

    def test_invalid_disabled_and_exhausted_codes_fail(self):
        accessmod.create_code(code="CLASS01")
        bad = self._start(code="NO-SUCH")
        self.assertEqual(bad.status_code, 403)
        self.assertEqual(bad.get_json()["error"], "邀请码无效或已失效")

        rec = accessmod.create_code(code="CLOSED01")
        accessmod.set_code_enabled(rec["id"], False)
        disabled = self._start(code="CLOSED01")
        self.assertEqual(disabled.status_code, 403)
        self.assertEqual(disabled.get_json()["error"], "邀请码无效或已失效")

        accessmod.create_code(code="ONCEONLY", max_uses=1)
        first = self._start(code="ONCEONLY")
        self.assertEqual(first.status_code, 200)
        second = self._start(name="Other Student", code="ONCEONLY")
        self.assertEqual(second.status_code, 403)
        self.assertEqual(second.get_json()["error"], "邀请码无效或已失效")

    def test_valid_code_records_user_and_log(self):
        rec = accessmod.create_code(code="Class01", note="Morning class")
        res = self._start(code="class01", module="reading", mode="passage1")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["candidate_name"], "Ada Student")

        users = accessmod.list_users()
        self.assertEqual(len(users), 1)
        user = users[0]
        self.assertEqual(user["name"], "Ada Student")
        self.assertEqual(user["invite_code_id"], rec["id"])
        self.assertEqual(user["start_count"], 1)
        self.assertEqual(user["reading_started"], 1)
        self.assertEqual(user["writing_started"], 0)

        codes = accessmod.list_codes()
        self.assertEqual(codes[0]["use_count"], 1)

        events = accessmod.list_events()
        starts = [ev for ev in events if ev.get("action") == "start"]
        self.assertEqual(len(starts), 1)
        self.assertEqual(starts[0]["candidate_name"], "Ada Student")
        self.assertEqual(starts[0]["invite_code_id"], rec["id"])
        self.assertEqual(starts[0]["module"], "reading")

    def test_submit_without_session_is_rejected(self):
        writing = self.client.post(
            "/api/submit",
            json={"candidate_name": "Ada Student", "task1_text": "hello"},
        )
        self.assertEqual(writing.status_code, 403)
        self.assertFalse(writing.get_json()["ok"])

        reading = self.client.post(
            "/api/reading/submit",
            json={"candidate_name": "Ada Student", "mode": "full", "answers": {"1": "sand"}},
        )
        self.assertEqual(reading.status_code, 403)
        self.assertFalse(reading.get_json()["ok"])

        listening = self.client.post(
            "/api/listening/submit",
            json={"candidate_name": "Ada Student", "mode": "full", "answers": {"1": "KERRIDGE"}},
        )
        self.assertEqual(listening.status_code, 403)
        self.assertFalse(listening.get_json()["ok"])

    def test_paper_and_prompts_require_session(self):
        prompts = self.client.get("/api/prompts")
        self.assertEqual(prompts.status_code, 403)
        paper = self.client.get("/api/reading/paper")
        self.assertEqual(paper.status_code, 403)
        listening_paper = self.client.get("/api/listening/paper")
        self.assertEqual(listening_paper.status_code, 403)
        listening_audio = self.client.get("/api/listening/audio/1")
        self.assertEqual(listening_audio.status_code, 403)

        accessmod.create_code(code="CLASS01")
        started = self._start(module="writing")
        self.assertEqual(started.status_code, 200)
        prompts_ok = self.client.get("/api/prompts")
        self.assertEqual(prompts_ok.status_code, 200)
        self.assertIn("sets", prompts_ok.get_json())

    def test_admin_creates_code_then_student_appears_in_users(self):
        self._set_admin()
        login = self._login_admin()
        self.assertEqual(login.status_code, 302)

        created = self.client.post(
            "/admin/invites/create",
            data={"code": "NEWCLASS", "note": "Evening", "max_uses": "10"},
            follow_redirects=True,
        )
        self.assertEqual(created.status_code, 200)
        html = created.get_data(as_text=True)
        self.assertIn("NEWCLASS", html)
        self.assertIn("Evening", html)

        # A separate student client uses the new code.
        student = appmod.app.test_client()
        start = student.post(
            "/api/session/start",
            json={
                "candidate_name": "Lin Student",
                "invite_code": "newclass",
                "module": "writing",
                "mode": "full",
            },
        )
        self.assertEqual(start.status_code, 200)

        users_page = self.client.get("/admin?tab=users")
        self.assertEqual(users_page.status_code, 200)
        users_html = users_page.get_data(as_text=True)
        self.assertIn("Lin Student", users_html)
        self.assertIn("NEWCLASS", users_html)
        self.assertIn("Evening", users_html)

        # After a writing submit, the user row should show a submission link.
        submit = student.post(
            "/api/submit",
            json={
                "candidate_name": "Lin Student",
                "mode": "task1",
                "prompt_set_id": "set-a",
                "task1_text": "hello world",
                "task2_text": "",
                "duration_seconds": 1200,
                "time_remaining_seconds": 10,
            },
        )
        self.assertEqual(submit.status_code, 200)
        sid = submit.get_json()["id"]
        users_after = self.client.get("/admin?tab=users").get_data(as_text=True)
        self.assertIn(sid, users_after)
        self.assertIn("1 份交卷", users_after)

    def test_no_enabled_codes_blocks_start(self):
        res = self._start()
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json()["error"], "邀请码无效或已失效")


if __name__ == "__main__":
    unittest.main()
