#!/usr/bin/env python3
"""Student portal: login, owned-attempt list, post-submit review, and IDOR."""

from __future__ import annotations

import json
import re
import os
import sys
import tempfile
import unittest
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import access as accessmod  # noqa: E402
import app as appmod  # noqa: E402
import student_portal as sp  # noqa: E402
import reading_scoring as rs  # noqa: E402
import listening_scoring as ls  # noqa: E402
import pikachu  # noqa: E402
import sprout  # noqa: E402
import growth_stack as gs  # noqa: E402

# Throwaway credentials used only in tests. Not production values.
TEST_ADMIN_USER = "TestAdmin"
TEST_ADMIN_PASS = "test-portal-pass-7k2q"
ADMIN_ENV = (
    "IELTS_ADMIN_USERNAME",
    "IELTS_ADMIN_PASSWORD",
    "IELTS_ADMIN_PASSWORD_HASH",
)

READING_LEAKS = ("解析", "标准答案", "Saving the addax", "saiga", "sand")


class StudentPortalTestCase(unittest.TestCase):
    def setUp(self):
        self._env_backup = {key: os.environ.get(key) for key in ADMIN_ENV}
        for key in ADMIN_ENV:
            os.environ.pop(key, None)
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        appmod.DATA_DIR = base / "data"
        appmod.SUBMISSIONS_DIR = appmod.DATA_DIR / "submissions"
        appmod.INDEX_PATH = appmod.DATA_DIR / "index.json"
        accessmod.bind(appmod.DATA_DIR)
        appmod.ensure_storage()
        appmod.app.config["TESTING"] = True
        appmod.app.config["SECRET_KEY"] = "test-secret-portal"
        self.client = appmod.app.test_client()

    def tearDown(self):
        for key, value in self._env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def _create_code(self, code="CLASS01", **kwargs):
        return accessmod.create_code(code=code, **kwargs)

    def _login(self, name="Ada Student", code="CLASS01", **kwargs):
        return self.client.post(
            "/me/login",
            data={"candidate_name": name, "invite_code": code},
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

    def _submit_reading(self, name="Ada Student", answers=None, mode="full", **extra):
        payload = {
            "candidate_name": name,
            "mode": mode,
            "prompt_set_id": "set-a",
            "answers": answers if answers is not None else {str(q): a for q, a in rs.official_answers().items()},
            "duration_seconds": 3600,
            "time_remaining_seconds": 120,
            "time_used_seconds": 3480,
            "part_times": {"1": 700, "2": 1100, "3": 1680},
            "auto_submitted": False,
        }
        payload.update(extra)
        return self.client.post("/api/reading/submit", json=payload)

    def _submit_writing(self, name="Ada Student", mode="full"):
        return self.client.post(
            "/api/submit",
            json={
                "candidate_name": name,
                "mode": mode,
                "prompt_set_id": "set-a",
                "task1_text": "The charts compare the town population over sixty years.",
                "task2_text": "Older people often lack accessible exercise programmes.",
                "duration_seconds": 3600,
                "time_remaining_seconds": 288,
                "time_used_seconds": 3312,
            },
        )


class LoginTests(StudentPortalTestCase):
    def test_login_does_not_increment_use_count_or_start_count(self):
        rec = self._create_code()
        res = self._login(follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.headers.get("Location", "").endswith("/me"))

        codes = accessmod.list_codes()
        self.assertEqual(codes[0]["id"], rec["id"])
        self.assertEqual(codes[0]["use_count"], 0)

        users = accessmod.list_users()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["name"], "Ada Student")
        self.assertEqual(users[0]["start_count"], 0)
        self.assertEqual(users[0]["writing_started"], 0)
        self.assertEqual(users[0]["reading_started"], 0)

        events = [ev for ev in accessmod.list_events() if ev.get("action") == "login"]
        self.assertEqual(len(events), 1)
        starts = [ev for ev in accessmod.list_events() if ev.get("action") == "start"]
        self.assertEqual(starts, [])

        # Starting an exam still consumes a use, separately from portal login.
        started = self._start()
        self.assertEqual(started.status_code, 200)
        self.assertEqual(accessmod.list_codes()[0]["use_count"], 1)
        self.assertEqual(accessmod.list_users()[0]["start_count"], 1)

    def test_invalid_and_disabled_codes_are_rejected(self):
        bad = self._login(code="NOPE0001")
        self.assertEqual(bad.status_code, 200)
        html = bad.get_data(as_text=True)
        self.assertIn("邀请码无效或已失效", html)
        self.assertIn("Candidate check-in", html)
        self.assertNotIn("还没有交过卷", html)
        self.assertNotIn("/admin/login", html)

        rec = self._create_code(code="CLOSED01")
        accessmod.set_code_enabled(rec["id"], False)
        disabled = self._login(code="CLOSED01")
        self.assertIn("邀请码无效或已失效", disabled.get_data(as_text=True))
        with self.client.session_transaction() as sess:
            self.assertFalse(sess.get("student_ok"))

    def test_enabled_code_can_login_after_max_uses_exhausted(self):
        self._create_code(code="ONCEONLY", max_uses=1)
        first = self._start(code="ONCEONLY")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(accessmod.list_codes()[0]["use_count"], 1)

        outsider = appmod.app.test_client()
        login = outsider.post(
            "/me/login",
            data={"candidate_name": "Ada Student", "invite_code": "ONCEONLY"},
            follow_redirects=False,
        )
        self.assertEqual(login.status_code, 302)
        self.assertEqual(accessmod.list_codes()[0]["use_count"], 1)
        home = outsider.get("/me")
        self.assertEqual(home.status_code, 200)
        self.assertIn("还没有交过卷", home.get_data(as_text=True))

    def test_existing_session_can_open_me_without_logging_in_again(self):
        self._create_code()
        started = self._start()
        self.assertEqual(started.status_code, 200)
        home = self.client.get("/me")
        self.assertEqual(home.status_code, 200)
        html = home.get_data(as_text=True)
        self.assertIn("你好，Ada Student", html)
        self.assertIn("还没有交过卷", html)
        self.assertNotIn("请输入真实姓名", html)

    def test_logout_clears_only_student_session_keys(self):
        os.environ["IELTS_ADMIN_USERNAME"] = TEST_ADMIN_USER
        os.environ["IELTS_ADMIN_PASSWORD"] = TEST_ADMIN_PASS
        self._create_code()
        self.client.post(
            "/admin/login",
            data={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASS},
        )
        self._login()
        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get("student_ok"))
            self.assertTrue(sess.get("admin_ok"))

        res = self.client.get("/me/logout", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.headers.get("Location", "").endswith("/"))
        with self.client.session_transaction() as sess:
            self.assertNotIn("student_ok", sess)
            self.assertNotIn("student_name", sess)
            self.assertNotIn("student_user_id", sess)
            self.assertNotIn("invite_code_id", sess)
            self.assertNotIn("student_module", sess)
            self.assertTrue(sess.get("admin_ok"))


class ListAndSecurityTests(StudentPortalTestCase):
    def test_unauthenticated_me_shows_student_login_not_admin(self):
        res = self.client.get("/me")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("查看我的记录", html)
        self.assertIn("Invitation code", html)
        self.assertIn("Candidate check-in", html)
        self.assertNotIn("Root Login", html)
        self.assertNotIn("/admin/login", html)
        self.assertNotIn("教师后台登录", html)
        self.assertNotIn("用户名或密码错误", html)
        for word in READING_LEAKS:
            self.assertNotIn(word, html)

        hub = self.client.get("/")
        hub_html = hub.get_data(as_text=True)
        self.assertIn("我的记录", hub_html)
        self.assertIn("/me", hub_html)
        self.assertIn("口语题库", hub_html)
        # Teacher entry stays in the footer/bottom, not beside the student link in a confused way.
        self.assertIn("Root Login", hub_html)
        for word in ("解析", "Saving the addax", "标准答案"):
            self.assertNotIn(word, hub_html)

    def test_empty_list_has_no_exam_traces_or_keys(self):
        self._create_code()
        self._login()
        home = self.client.get("/me")
        html = home.get_data(as_text=True)
        self.assertIn("还没有交过卷", html)
        self.assertIn("/writing", html)
        self.assertIn("/reading", html)
        # Help text may mention 查看整卷; there must be no attempt links yet.
        self.assertNotIn("/me/submission/", html)
        self.assertNotIn('class="attempt-card"', html)
        # Generic copy may mention that explanations appear after submit;
        # the empty account must not include any paper, keys, or stems.
        for word in ("Saving the addax", "saiga", "sand", "定位第", "The addax"):
            self.assertNotIn(word, html)
        # Guessing a set id or a missing submission must 404 without keys.
        for url in (
            "/me/submission/set-a",
            "/me/submission/set-a/review",
            "/me/review/set-a",
            "/me/submission/00000000-0000-0000-0000-000000000000",
        ):
            res = self.client.get(url)
            self.assertEqual(res.status_code, 404, url)
            body = res.get_data(as_text=True)
            self.assertNotIn("解析", body)
            self.assertNotIn("Saving the addax", body)
            self.assertNotIn("sand", body.lower())

        paper = self.client.get("/api/reading/paper")
        # Logged in via portal only, without start_student, has a valid session.
        self.assertEqual(paper.status_code, 200)
        raw = paper.get_data(as_text=True)
        self.assertNotIn("explanation", raw)
        self.assertNotIn("解析", raw)

        api_miss = self.client.get("/api/me/submission/set-a")
        self.assertEqual(api_miss.status_code, 404)
        self.assertNotIn("解析", api_miss.get_data(as_text=True))
        self.assertNotIn("sand", api_miss.get_data(as_text=True).lower())

    def test_same_invite_code_lists_papers_under_either_name(self):
        self._create_code(code="SHARED1")
        ada = self.client
        self._login(name="Ada Student", code="SHARED1")
        self._start(name="Ada Student", code="SHARED1", module="reading")
        ada_sub = self._submit_reading(name="Ada Student", answers={"1": "stone", "8": "TRUE"})
        self.assertEqual(ada_sub.status_code, 200)
        ada_sid = ada_sub.get_json()["id"]

        lin = appmod.app.test_client()
        lin.post(
            "/me/login",
            data={"candidate_name": "Lin Student", "invite_code": "SHARED1"},
        )
        lin.post(
            "/api/session/start",
            json={
                "candidate_name": "Lin Student",
                "invite_code": "SHARED1",
                "module": "writing",
                "mode": "task1",
            },
        )
        lin_write = lin.post(
            "/api/submit",
            json={
                "candidate_name": "Lin Student",
                "mode": "task1",
                "prompt_set_id": "set-a",
                "task1_text": "Lin only wrote task one.",
                "task2_text": "",
                "duration_seconds": 1200,
                "time_used_seconds": 900,
            },
        )
        self.assertEqual(lin_write.status_code, 200)
        lin_sid = lin_write.get_json()["id"]

        ada_list = ada.get("/me").get_data(as_text=True)
        self.assertIn("你好，Ada Student", ada_list)
        self.assertIn("查看整卷", ada_list)
        self.assertIn("查看错题", ada_list)
        self.assertIn(ada_sid, ada_list)
        self.assertIn(lin_sid, ada_list)
        self.assertIn("阅读", ada_list)
        self.assertIn("写作", ada_list)

        ada_open = ada.get(f"/me/submission/{lin_sid}")
        self.assertEqual(ada_open.status_code, 200)
        self.assertIn("REVIEW_CONFIG", ada_open.get_data(as_text=True))

        lin_list = lin.get("/me").get_data(as_text=True)
        self.assertIn("你好，Lin Student", lin_list)
        self.assertIn(lin_sid, lin_list)
        self.assertIn(ada_sid, lin_list)
        self.assertIn("写作", lin_list)
        self.assertIn("查看错题", lin_list)

        lin_open = lin.get(f"/me/submission/{ada_sid}")
        self.assertEqual(lin_open.status_code, 200)
        lin_open_html = lin_open.get_data(as_text=True)
        self.assertIn("REVIEW_CONFIG", lin_open_html)
        lin_review = lin.get(f"/me/submission/{ada_sid}/review")
        self.assertEqual(lin_review.status_code, 200)
        lin_api = lin.get(f"/api/me/submission/{ada_sid}")
        self.assertEqual(lin_api.status_code, 200)
        self.assertIn("stone", lin_api.get_data(as_text=True))

        # Unauthenticated visitors are sent to student login, not admin login, and see no keys.
        guest = appmod.app.test_client()
        unauth = guest.get(f"/me/submission/{ada_sid}", follow_redirects=False)
        self.assertEqual(unauth.status_code, 302)
        location = unauth.headers.get("Location", "")
        self.assertIn("/me", location)
        self.assertNotIn("/admin", location)
        login_page = guest.get(location)
        login_html = login_page.get_data(as_text=True)
        self.assertIn("Invitation code", login_html)
        self.assertIn("记录按邀请码归属", login_html)
        self.assertNotIn("解析", login_html)
        self.assertNotIn("/admin/login", login_html)

    def test_same_typed_name_different_codes_cannot_see_each_other(self):
        self._create_code(code="CODEADA")
        ada = self.client
        self._login(name="Ada Student", code="CODEADA")
        self._start(name="Ada Student", code="CODEADA", module="reading")
        ada_sub = self._submit_reading(name="Ada Student", answers={"1": "stone", "8": "TRUE"})
        self.assertEqual(ada_sub.status_code, 200)
        ada_sid = ada_sub.get_json()["id"]

        self._create_code(code="CODELIN")
        lin = appmod.app.test_client()
        lin.post(
            "/me/login",
            data={"candidate_name": "Ada Student", "invite_code": "CODELIN"},
        )
        lin.post(
            "/api/session/start",
            json={
                "candidate_name": "Ada Student",
                "invite_code": "CODELIN",
                "module": "writing",
                "mode": "task1",
            },
        )
        lin_write = lin.post(
            "/api/submit",
            json={
                "candidate_name": "Ada Student",
                "mode": "task1",
                "prompt_set_id": "set-a",
                "task1_text": "Lin only wrote task one.",
                "task2_text": "",
                "duration_seconds": 1200,
                "time_used_seconds": 900,
            },
        )
        self.assertEqual(lin_write.status_code, 200)
        lin_sid = lin_write.get_json()["id"]

        ada_list = ada.get("/me").get_data(as_text=True)
        self.assertIn(ada_sid, ada_list)
        self.assertNotIn(lin_sid, ada_list)
        self.assertIn("阅读", ada_list)
        self.assertIn('class="mod-badge reading"', ada_list)
        self.assertNotIn('class="mod-badge writing"', ada_list)

        lin_list = lin.get("/me").get_data(as_text=True)
        self.assertIn(lin_sid, lin_list)
        self.assertNotIn(ada_sid, lin_list)
        self.assertIn('class="mod-badge writing"', lin_list)
        self.assertNotIn('class="mod-badge reading"', lin_list)
        self.assertNotIn("查看错题", lin_list)

        stolen = lin.get(f"/me/submission/{ada_sid}")
        self.assertEqual(stolen.status_code, 404)
        stolen_html = stolen.get_data(as_text=True)
        self.assertNotIn("解析", stolen_html)
        self.assertNotIn("stone", stolen_html)

        stolen_review = lin.get(f"/me/submission/{ada_sid}/review")
        self.assertEqual(stolen_review.status_code, 404)
        self.assertNotIn("解析", stolen_review.get_data(as_text=True))

        stolen_api = lin.get(f"/api/me/submission/{ada_sid}")
        self.assertEqual(stolen_api.status_code, 404)
        stolen_api_body = stolen_api.get_data(as_text=True)
        self.assertNotIn("解析", stolen_api_body)
        self.assertNotIn("stone", stolen_api_body)
        self.assertNotIn("explanation", stolen_api_body)


class ReviewContentTests(StudentPortalTestCase):
    def test_reading_detail_after_submit_includes_answers_keys_and_explanations(self):
        self._create_code()
        self._start(module="reading")
        # Mix of correct, wrong, and blank.
        answers = {str(q): a for q, a in rs.official_answers().items()}
        answers["8"] = "TRUE"  # official FALSE
        answers["2"] = ""
        res = self._submit_reading(answers=answers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertNotIn("marking", data)
        self.assertNotIn("explanation", data)
        sid = data["id"]

        home = self.client.get("/me")
        home_html = home.get_data(as_text=True)
        self.assertIn("查看整卷", home_html)
        self.assertIn("查看错题", home_html)
        self.assertIn(sid, home_html)
        self.assertIn(f"{data['score']}/{data['total']}", home_html)
        self.assertIn("58min0s", home_html)

        detail = self.client.get(f"/me/submission/{sid}")
        self.assertEqual(detail.status_code, 200)
        html = detail.get_data(as_text=True)
        self.assertIn("REVIEW_CONFIG", html)
        self.assertIn(sid, html)
        self.assertIn("回顾模式", html)
        self.assertIn("reading-shell", html)
        self.assertIn("passage-pane", html)
        self.assertIn("question-pane", html)
        self.assertIn("reading.js", html)
        self.assertIn("mistakesOnly: false", html)
        # Keys and explanations are not embedded in the page; they come from the owner API.
        self.assertNotIn("定位第", html)
        self.assertNotIn("下载 PDF", html)
        self.assertNotIn("高亮与扫跳评述", html)
        self.assertNotIn("文章类型", html)
        self.assertNotIn("结构类型", html)

        api = self.client.get(f"/api/me/submission/{sid}")
        self.assertEqual(api.status_code, 200)
        payload = api.get_json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["module"], "reading")
        self.assertEqual(payload["answers"]["8"], "TRUE")
        self.assertEqual(payload["answers"]["2"], "")
        self.assertIn("paper", payload)
        self.assertEqual(payload["paper"]["passages"][0]["title"], "Saving the addax")
        by_q = {row["q"]: row for row in payload["questions"]}
        self.assertEqual(by_q[8]["student"], "TRUE")
        self.assertEqual(by_q[8]["correct"], "FALSE")
        self.assertFalse(by_q[8]["ok"])
        self.assertTrue(by_q[8]["explanation"])
        self.assertTrue(by_q[2]["student_blank"])
        self.assertTrue(by_q[1]["ok"])
        self.assertEqual(by_q[1]["correct"], "sand")
        self.assertIn("定位第", by_q[1]["explanation"])
        raw_api = api.get_data(as_text=True)
        self.assertIn("解析", "".join(row["explanation"] and "解析" or "" for row in payload["questions"]) or "解析")
        self.assertIn("explanation", raw_api)

        review = self.client.get(f"/me/submission/{sid}/review")
        self.assertEqual(review.status_code, 200)
        rev = review.get_data(as_text=True)
        self.assertIn("REVIEW_CONFIG", rev)
        self.assertIn("mistakesOnly: true", rev)
        self.assertIn("回顾模式", rev)
        self.assertIn("reading-shell", rev)
        self.assertNotIn("定位第", rev)

        # Result page chrome includes the exam-UI review entrances.
        page = self.client.get("/reading").get_data(as_text=True)
        self.assertNotIn("REVIEW_CONFIG", page)
        self.assertIn("btnReviewMistakes", page)
        self.assertIn("btnReviewPaper", page)
        self.assertIn("Review mistakes", page)
        self.assertIn("Review paper", page)
        js = (ROOT / "static" / "reading.js").read_text(encoding="utf-8")
        self.assertIn("enterAttemptReview", js)
        self.assertIn("lockReviewInputs", js)
        self.assertIn("/me/submission/", js)
        self.assertIn("enterAttemptReview", js)

        blocked = self.client.post(
            "/api/reading/submit",
            json={
                "candidate_name": "Ada Student",
                "mode": "full",
                "answers": {"1": "hack"},
                "review_mode": True,
                "review_sid": sid,
            },
        )
        self.assertEqual(blocked.status_code, 403)
        blocked_body = blocked.get_json()
        self.assertFalse(blocked_body["ok"])
        self.assertIn("回顾模式", blocked_body["error"])
        self.assertNotIn("score", blocked_body)
        self.assertNotIn("marking", blocked_body)

    def test_all_correct_review_is_empty_and_does_not_dump_the_key(self):
        self._create_code()
        self._start(module="reading")
        res = self._submit_reading()
        self.assertEqual(res.status_code, 200)
        sid = res.get_json()["id"]
        review = self.client.get(f"/me/submission/{sid}/review")
        html = review.get_data(as_text=True)
        self.assertIn("mistakesOnly: true", html)
        self.assertIn("回顾模式", html)
        # The HTML shell itself does not dump keys; the API includes them because
        # this attempt was completed, and the client only displays mistakes.
        self.assertNotIn("定位第", html)
        api = self.client.get(f"/api/me/submission/{sid}").get_json()
        self.assertEqual(api["mistake_count"], 0)
        self.assertTrue(all(row["ok"] for row in api["questions"]))
        self.assertIn("sand", api["questions"][0]["correct"])

    def test_review_restores_highlights_but_not_raw_or_scripts(self):
        self._create_code()
        self._start(module="reading")
        phrase = "spiral-horned antelope"
        stem = "Today addax are evenly distributed across Niger and Chad."
        dirty_passage = (
            f'<p>ignored snapshot <mark class="hl">{phrase}</mark></p>'
            '<script>alert(1)</script>'
            '<img src=x onerror="alert(1)">'
        )
        dirty_questions = (
            f'<div class="q-stem-text"><mark class="hl">{stem}</mark></div>'
            "<script>document.cookie</script>"
            '<img src=x onerror="alert(2)">'
        )
        res = self._submit_reading(
            highlights={"passage": {"1": dirty_passage}, "questions": dirty_questions}
        )
        self.assertEqual(res.status_code, 200)
        sid = res.get_json()["id"]

        api = self.client.get(f"/api/me/submission/{sid}")
        self.assertEqual(api.status_code, 200)
        payload = api.get_json()
        rh = payload["review_highlights"]
        self.assertEqual(rh["passage"]["1"], [phrase])
        self.assertEqual(rh["questions"], [stem])
        html1 = rh["passage_html"]["1"]
        self.assertIn(f'<mark class="hl">{phrase}</mark>', html1)
        self.assertTrue(html1.startswith("<p>For centuries"))
        self.assertIn("For centuries the addax", html1)
        raw = api.get_data(as_text=True)
        for banned in ("<script", "</script>", "onerror", "alert(1)", "alert(2)", "document.cookie"):
            self.assertNotIn(banned, html1)
            self.assertNotIn(banned, raw)
        self.assertNotIn("ignored snapshot", raw)
        self.assertNotIn("高亮与扫跳评述", raw)
        self.assertNotIn("文章类型", raw)

        # The exam-UI review shell stays read-only and does not assign stored snapshots.
        page = self.client.get(f"/me/submission/{sid}").get_data(as_text=True)
        self.assertIn("回顾模式", page)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertNotIn("onerror=", page)
        js = (ROOT / "static" / "reading.js").read_text(encoding="utf-8")
        self.assertIn("applyReviewHighlightsTo", js)
        self.assertIn('mark.className = "hl"', js)
        self.assertIn("review_highlights", js)
        self.assertNotIn("restoreQuestionHtml(data", js)
        self.assertNotIn("review_highlights.questions_html", js)

        # Another student cannot read the highlights.
        other = appmod.app.test_client()
        self._create_code(code="OTHERCODE")
        login = other.post(
            "/me/login",
            data={"candidate_name": "Lin Student", "invite_code": "OTHERCODE"},
        )
        self.assertIn(login.status_code, (200, 302))
        stolen = other.get(f"/api/me/submission/{sid}")
        self.assertEqual(stolen.status_code, 404)
        stolen_body = stolen.get_data(as_text=True)
        self.assertNotIn(phrase, stolen_body)
        self.assertNotIn("review_highlights", stolen_body)

    def test_review_without_highlights_has_no_marks(self):
        self._create_code()
        self._start(module="reading")
        res = self._submit_reading()
        self.assertEqual(res.status_code, 200)
        sid = res.get_json()["id"]
        payload = self.client.get(f"/api/me/submission/{sid}").get_json()
        rh = payload["review_highlights"]
        self.assertEqual(rh["passage"], {})
        self.assertEqual(rh["questions"], [])
        for html in (rh.get("passage_html") or {}).values():
            self.assertNotIn("<mark", html)
            self.assertNotIn('class="hl"', html)

    def test_paper_api_and_pre_submit_remain_key_free(self):
        self._create_code()
        self._start(module="reading")
        paper = self.client.get("/api/reading/paper")
        self.assertEqual(paper.status_code, 200)
        raw = paper.get_data(as_text=True)
        self.assertNotIn("explanation", raw)
        self.assertNotIn("解析", raw)
        self.assertNotIn('"answer": "sand"', raw)

        reading_page = self.client.get("/reading").get_data(as_text=True)
        self.assertNotIn("REVIEW_CONFIG", reading_page)
        self.assertNotIn("解析", reading_page)
        self.assertNotIn("Saving the addax", reading_page)

        unauth = appmod.app.test_client().get("/api/me/submission/whatever")
        self.assertIn(unauth.status_code, (401, 404))
        self.assertNotIn("explanation", unauth.get_data(as_text=True))

    def test_writing_detail_has_prompt_and_essay_but_no_official_score(self):
        self._create_code()
        self._start(module="writing")
        res = self._submit_writing()
        self.assertEqual(res.status_code, 200)
        sid = res.get_json()["id"]

        # Even if a later official-score field is stored, the student page must not show it.
        path = appmod.SUBMISSIONS_DIR / f"{sid}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["band_estimate"] = 7.5
        record["official_score"] = 7.0
        record["task1_band"] = 6.5
        path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn("查看整卷", home)
        self.assertNotIn("查看错题", home)
        self.assertIn("55min12s", home)
        # The growth-stack widget always labels stages 5.5–9.0, including 7.5,
        # but a hidden writing official/auto score must not light it or appear
        # as a writing result on 我的记录.
        self.assertNotIn("参考分数", home)
        self.assertNotIn("教师评分 7", home)
        self.assertNotIn("教师评分 7.5", home)
        self.assertIn("待评分", home)
        self.assertIn('class="growth-stack is-empty"', home)
        self.assertIn("暂无评分", home)
        self.assertNotIn("当前最高", home)
        self.assertNotIn("official_score", home)

        detail = self.client.get(f"/me/submission/{sid}")
        self.assertEqual(detail.status_code, 200)
        html = detail.get_data(as_text=True)
        self.assertIn("REVIEW_CONFIG", html)
        self.assertIn("回顾模式", html)
        self.assertIn("exam-shell", html)
        self.assertIn("task1Answer", html)
        self.assertIn("exam.js", html)
        self.assertNotIn("7.5", html)
        self.assertNotIn("official_score", html)
        self.assertNotIn("参考分数", html)
        self.assertNotIn("下载 PDF", html)

        api = self.client.get(f"/api/me/submission/{sid}")
        self.assertEqual(api.status_code, 200)
        payload = api.get_json()
        self.assertEqual(payload["module"], "writing")
        self.assertIn("The bar charts below show the information about the population", payload["set"]["task1"]["instruction"])
        self.assertEqual(payload["set"]["task1"]["image"]["src"], "/static/images/set-a-town-population.png")
        self.assertIn("The charts compare the town population", payload["task1_text"])
        self.assertIn("Older people often lack accessible exercise programmes", payload["task2_text"])
        self.assertNotIn("band_estimate", payload)
        self.assertNotIn("official_score", payload)
        self.assertNotIn("task1_band", payload)
        self.assertNotIn("7.5", api.get_data(as_text=True))
        self.assertNotIn("解析", api.get_data(as_text=True))

        review = self.client.get(f"/me/submission/{sid}/review")
        self.assertEqual(review.status_code, 404)

        blocked = self.client.post(
            "/api/submit",
            json={
                "candidate_name": "Ada Student",
                "mode": "full",
                "task1_text": "should not save",
                "review_mode": True,
            },
        )
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("回顾模式", blocked.get_json()["error"])

        exam_js = (ROOT / "static" / "exam.js").read_text(encoding="utf-8")
        self.assertIn("enterAttemptReview", exam_js)
        self.assertIn("readOnly", exam_js)

    def test_older_record_without_user_id_matches_name_and_code(self):
        rec = self._create_code()
        self._login()
        # Simulate a pre-user_id writing submission for this name + code.
        sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        record = {
            "id": sid,
            "timestamp": "2026-11-01T09:15:00+08:00",
            "candidate_name": "Ada Student",
            "module": "writing",
            "mode": "task2",
            "prompt_set_id": "set-a",
            "task2_text": "Legacy essay without a user id.",
            "task1_text": "",
            "task1_word_count": 0,
            "task2_word_count": 6,
            "time_used_seconds": 12,
            "invite_code_id": rec["id"],
        }
        (appmod.SUBMISSIONS_DIR / f"{sid}.json").write_text(
            json.dumps(record, ensure_ascii=False), encoding="utf-8"
        )
        index = json.loads(appmod.INDEX_PATH.read_text(encoding="utf-8"))
        index.setdefault("submissions", []).insert(
            0,
            {
                "id": sid,
                "timestamp": record["timestamp"],
                "candidate_name": "Ada Student",
                "module": "writing",
                "mode": "task2",
                "task2_word_count": 6,
                "time_used_seconds": 12,
                "invite_code_id": rec["id"],
            },
        )
        appmod.save_index(index)

        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn(sid, home)
        self.assertIn("12s", home)
        detail = self.client.get(f"/me/submission/{sid}")
        self.assertEqual(detail.status_code, 200)
        self.assertIn("REVIEW_CONFIG", detail.get_data(as_text=True))
        api = self.client.get(f"/api/me/submission/{sid}")
        self.assertEqual(api.status_code, 200)
        self.assertIn("Legacy essay without a user id.", api.get_json()["task2_text"])

        # Same invite code with a typo name still opens the legacy paper.
        typo = appmod.app.test_client()
        typo.post(
            "/me/login",
            data={"candidate_name": "Ada Studnt", "invite_code": "CLASS01"},
        )
        typo_home = typo.get("/me").get_data(as_text=True)
        self.assertIn(sid, typo_home)
        typo_detail = typo.get(f"/me/submission/{sid}")
        self.assertEqual(typo_detail.status_code, 200)

    def test_record_without_invite_code_falls_back_to_user_id(self):
        self._create_code()
        self._login()
        users = accessmod.list_users()
        uid = users[0]["id"]

        sid_uid = "bbbbbbbb-bbbb-cccc-dddd-eeeeeeeeeeee"
        record_uid = {
            "id": sid_uid,
            "timestamp": "2026-11-01T09:10:00+08:00",
            "candidate_name": "Old Nickname",
            "module": "writing",
            "mode": "task2",
            "task2_text": "Legacy essay matched only by user id.",
            "task2_word_count": 7,
            "time_used_seconds": 11,
            "user_id": uid,
        }
        sid_name = "cccccccc-bbbb-cccc-dddd-eeeeeeeeeeee"
        record_name = {
            "id": sid_name,
            "timestamp": "2026-11-01T09:11:00+08:00",
            "candidate_name": "Ada Student",
            "module": "writing",
            "mode": "task2",
            "task2_text": "Legacy essay with only a name, no code or user id.",
            "task2_word_count": 6,
            "time_used_seconds": 10,
        }
        self._create_code(code="OTHERCODE")
        outsider = appmod.app.test_client()
        outsider.post(
            "/me/login",
            data={"candidate_name": "Ada Student", "invite_code": "OTHERCODE"},
        )

        index = json.loads(appmod.INDEX_PATH.read_text(encoding="utf-8"))
        for record in (record_uid, record_name):
            (appmod.SUBMISSIONS_DIR / f"{record['id']}.json").write_text(
                json.dumps(record, ensure_ascii=False), encoding="utf-8"
            )
            index.setdefault("submissions", []).insert(0, {
                "id": record["id"],
                "timestamp": record["timestamp"],
                "candidate_name": record["candidate_name"],
                "module": "writing",
                "mode": "task2",
                "task2_word_count": record["task2_word_count"],
                "time_used_seconds": record["time_used_seconds"],
                "user_id": record.get("user_id"),
            })
        appmod.save_index(index)

        # Owner can open the uncoded paper that stores their user_id, even if the typed name differs.
        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn(sid_uid, home)
        self.assertNotIn(sid_name, home)
        self.assertEqual(self.client.get(f"/me/submission/{sid_uid}").status_code, 200)
        self.assertEqual(self.client.get(f"/me/submission/{sid_name}").status_code, 404)

        # A different invite code must not see uncoded papers, even with the same typed name.
        other_home = outsider.get("/me").get_data(as_text=True)
        self.assertNotIn(sid_uid, other_home)
        self.assertNotIn(sid_name, other_home)
        self.assertEqual(outsider.get(f"/me/submission/{sid_uid}").status_code, 404)
        self.assertEqual(outsider.get(f"/me/submission/{sid_name}").status_code, 404)



    def test_owns_record_keys_by_invite_code(self):
        ident = {"user_id": "u1", "candidate_name": "Ada Student", "invite_code_id": "code-a"}
        self.assertTrue(sp.owns_record(
            {"invite_code_id": "code-a", "candidate_name": "Ada Typo", "user_id": "u2"},
            ident,
        ))
        self.assertFalse(sp.owns_record(
            {"invite_code_id": "code-b", "candidate_name": "Ada Student", "user_id": "u1"},
            ident,
        ))
        # Uncoded paper: user_id may match; name alone must not leak to a coded session.
        self.assertTrue(sp.owns_record(
            {"candidate_name": "Old Nickname", "user_id": "u1"},
            ident,
        ))
        self.assertFalse(sp.owns_record(
            {"candidate_name": "Ada Student"},
            ident,
        ))
        # Name fallback only when neither side has an invite code.
        self.assertTrue(sp.owns_record(
            {"candidate_name": "Ada Student"},
            {"candidate_name": "ada student"},
        ))
        self.assertFalse(sp.owns_record(
            {"candidate_name": "Ada Student"},
            {"candidate_name": "Lin Student"},
        ))



class ListeningPortalTests(StudentPortalTestCase):
    def test_module_of_does_not_treat_listening_as_writing(self):
        self.assertEqual(sp.module_of({"module": "listening"}), "listening")
        self.assertEqual(sp.module_label("listening"), "听力")
        self.assertEqual(sp.mode_label("listening", "section3"), "Section 3")
        self.assertEqual(sp.module_of({"module": "writing"}), "writing")
        self.assertEqual(sp.module_of({}), "writing")

    def test_portal_lists_listening_score_and_review_includes_keys(self):
        self._create_code()
        self._start(name="Ada Student", module="listening")
        answers = {str(q): a for q, a in ls.official_answers().items()}
        answers["7"] = ""
        res = self._client_submit_listening(answers)
        self.assertEqual(res.status_code, 200)
        sid = res.get_json()["id"]

        home = self.client.get("/me")
        self.assertEqual(home.status_code, 200)
        html = home.get_data(as_text=True)
        self.assertIn("听力", html)
        self.assertIn("39/40", html)
        self.assertIn(f"/me/submission/{sid}/review", html)

        api = self.client.get(f"/api/me/submission/{sid}")
        self.assertEqual(api.status_code, 200)
        payload = api.get_json()
        self.assertEqual(payload["module"], "listening")
        self.assertTrue(payload["questions"])
        self.assertTrue(any((row.get("explanation") or "") for row in payload["questions"]))
        self.assertIn("1", payload.get("transcripts") or {})
        review = self.client.get(f"/me/submission/{sid}/review")
        self.assertEqual(review.status_code, 200)
        self.assertIn("listening.js", review.get_data(as_text=True))

    def _client_submit_listening(self, answers):
        return self.client.post(
            "/api/listening/submit",
            json={
                "candidate_name": "Ada Student",
                "mode": "full",
                "prompt_set_id": "set-a",
                "answers": answers,
                "duration_seconds": 1800,
                "time_used_seconds": 1500,
            },
        )



class PikachuProgressTests(StudentPortalTestCase):
    def setUp(self):
        super().setUp()
        os.environ["IELTS_ADMIN_USERNAME"] = TEST_ADMIN_USER
        os.environ["IELTS_ADMIN_PASSWORD"] = TEST_ADMIN_PASS

    def _login_admin(self, client=None):
        client = client or self.client
        return client.post(
            "/admin/login",
            data={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASS},
        )

    def _submit_listening(self, name="Ada Student", prompt_set_id="set-a"):
        answers = {str(q): a for q, a in ls.official_answers().items()}
        return self.client.post(
            "/api/listening/submit",
            json={
                "candidate_name": name,
                "mode": "full",
                "prompt_set_id": prompt_set_id,
                "answers": answers,
                "duration_seconds": 1800,
                "time_used_seconds": 1500,
            },
        )

    def _figures(self, html):
        return re.findall(r'<figure\s+class="pikachu-figure([^"]*)"', html)

    def _caption_texts(self, html):
        return re.findall(r'<figcaption class="pikachu-caption">\s*(.*?)\s*</figcaption>', html, flags=re.S)

    def _plain_captions(self, html):
        out = []
        for raw in self._caption_texts(html):
            text = re.sub(r"<[^>]+>", "", raw)
            out.append(" ".join(unescape(text).split()))
        return out

    def _seed_attempts(self, count, rec, name="Ada Student"):
        index = json.loads(appmod.INDEX_PATH.read_text(encoding="utf-8"))
        submissions = index.setdefault("submissions", [])
        modules = ("writing", "reading", "listening")
        for i in range(count):
            sid = f"pika-{i:04d}-bbbb-cccc-dddd-eeeeeeeeeeee"
            module = modules[i % 3]
            set_id = f"set-{chr(ord('a') + (i % 6))}"
            record = {
                "id": sid,
                "timestamp": f"2026-11-{(i % 28) + 1:02d}T09:15:00+08:00",
                "candidate_name": name,
                "module": module,
                "mode": "full",
                "prompt_set_id": set_id,
                "time_used_seconds": 12,
                "invite_code_id": rec["id"],
            }
            if module in {"reading", "listening"}:
                record["score"] = 30 + (i % 10)
                record["total"] = 40
                record["band_estimate"] = 7.0
            (appmod.SUBMISSIONS_DIR / f"{sid}.json").write_text(
                json.dumps(record, ensure_ascii=False), encoding="utf-8"
            )
            index_row = {
                "id": sid,
                "timestamp": record["timestamp"],
                "candidate_name": name,
                "module": module,
                "mode": "full",
                "prompt_set_id": set_id,
                "time_used_seconds": 12,
                "invite_code_id": rec["id"],
            }
            if module in {"reading", "listening"}:
                index_row["score"] = record["score"]
                index_row["total"] = record["total"]
                index_row["band_estimate"] = record["band_estimate"]
            submissions.insert(0, index_row)
        appmod.save_index(index)

    def test_sprite_poses_are_original_grids(self):
        ids = pikachu.pose_ids()
        self.assertGreaterEqual(len(ids), 12)
        self.assertLessEqual(len(ids), 16)
        self.assertEqual(len(ids), len(set(ids)))
        seen = set()
        for name in ids:
            rows = pikachu.POSES[name]
            widths = {len(line) for line in rows}
            self.assertEqual(len(widths), 1, name)
            width = len(rows[0])
            self.assertGreaterEqual(width, 14)
            self.assertLessEqual(width, 24)
            self.assertGreaterEqual(len(rows), 10)
            letters = {ch for line in rows for ch in line if ch != "."}
            self.assertTrue(letters <= pikachu.COLOR_LETTERS, name)
            self.assertTrue({"Y", "K", "R"} <= letters, name)
            key = tuple(rows)
            self.assertNotIn(key, seen)
            seen.add(key)
        # Decorative balls are original baubles, not official Poké Ball marks.
        ball_letters = {ch for line in pikachu.DECOS["ball"] for ch in line if ch != "."}
        self.assertNotIn("R", ball_letters)
        self.assertTrue(ball_letters <= pikachu.COLOR_LETTERS)

    def test_gallery_reuses_poses_when_it_grows(self):
        extra = 3
        attempts = [{"id": f"a{i}", "caption": f"写作 Set A · {i}"} for i in range(pikachu.pose_count() + extra)]
        gallery = pikachu.gallery(attempts)
        self.assertEqual(gallery["lit"], pikachu.pose_count() + extra)
        self.assertEqual(gallery["total"], pikachu.pose_count() + extra)
        self.assertEqual(len(gallery["figures"]), pikachu.pose_count() + extra)
        ids = pikachu.pose_ids()
        self.assertEqual(gallery["figures"][0]["pose"], ids[0])
        self.assertEqual(gallery["figures"][len(ids)]["pose"], ids[0])
        self.assertEqual(gallery["figures"][-1]["pose"], ids[extra - 1])
        self.assertTrue(all(fig["lit"] for fig in gallery["figures"]))
        self.assertTrue(all(
            cell["lit"]
            for fig in gallery["figures"]
            for cell in fig["cells"]
            if not cell["empty"]
        ))

    def test_empty_records_still_show_unlit_gallery(self):
        self._create_code()
        self._login()
        home = self.client.get("/me")
        self.assertEqual(home.status_code, 200)
        html = home.get_data(as_text=True)
        self.assertIn("还没有交过卷", html)
        self.assertIn("开始写作模考", html)
        self.assertIn("pikachu-progress", html)
        self.assertIn("还没有点亮的皮卡丘，每做完一套点亮一只", html)
        self.assertIn("未点亮的像素皮卡丘", html)
        self.assertNotIn("已点亮", html)
        self.assertEqual(self._plain_captions(html), [])
        figures = self._figures(html)
        self.assertEqual(len(figures), pikachu.pose_count())
        self.assertTrue(all("is-unlit" in cls for cls in figures))
        self.assertEqual(html.count("pikachu-cell is-lit"), 0)
        self.assertEqual(self._plain_captions(html), [])

    def test_each_submitted_paper_lights_one_whole_pikachu_oldest_first(self):
        self._create_code()

        self._start(module="writing")
        writing = self._submit_writing()
        self.assertEqual(writing.status_code, 200)
        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn("已点亮 1 只皮卡丘，每做完一套点亮一只", home)
        figures = self._figures(home)
        self.assertEqual(len(figures), pikachu.pose_count())
        self.assertIn("is-lit", figures[0])
        self.assertTrue(all("is-unlit" in cls for cls in figures[1:]))
        self.assertIn("写作 Set A · 待评分", self._plain_captions(home))
        self.assertIn("待评分", home)

        self._start(module="reading")
        reading = self._submit_reading()
        self.assertEqual(reading.status_code, 200)
        reading_payload = reading.get_json()
        reading_caption = f"阅读 Set A · {reading_payload['score']}/{reading_payload['total']} · {rs.format_band(reading_payload['band_estimate'])}"
        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn("已点亮 2 只皮卡丘，每做完一套点亮一只", home)
        figures = self._figures(home)
        self.assertIn("is-lit", figures[0])
        self.assertIn("is-lit", figures[1])
        self.assertTrue(all("is-unlit" in cls for cls in figures[2:]))
        captions = self._plain_captions(home)
        self.assertEqual(captions[0], "写作 Set A · 待评分")
        self.assertEqual(captions[1], reading_caption)
        # Attempt list is newest first, but Pikachus light oldest first.
        writing_pos = home.find("写作 Set A · 待评分")
        reading_pos = home.find(reading_caption)
        list_writing = home.rfind("mod-badge writing")
        list_reading = home.rfind("mod-badge reading")
        self.assertLess(writing_pos, reading_pos)
        self.assertLess(list_reading, list_writing)

        self._start(module="listening")
        listening = self._submit_listening()
        self.assertEqual(listening.status_code, 200)
        listening_payload = listening.get_json()
        listening_caption = f"听力 Set A · {listening_payload['score']}/{listening_payload['total']} · {ls.format_band(listening_payload['band_estimate'])}"
        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn("已点亮 3 只皮卡丘，每做完一套点亮一只", home)
        self.assertIn(listening_caption, self._plain_captions(home))
        self.assertIn("写作", home)
        self.assertIn("阅读", home)
        self.assertIn("听力", home)

    def test_gallery_grows_on_records_page_when_attempts_exceed_poses(self):
        rec = self._create_code()
        self._login()
        extra = 2
        self._seed_attempts(pikachu.pose_count() + extra, rec)
        home = self.client.get("/me").get_data(as_text=True)
        figures = self._figures(home)
        self.assertEqual(len(figures), pikachu.pose_count() + extra)
        self.assertTrue(all("is-lit" in cls for cls in figures))
        self.assertIn(f"已点亮 {pikachu.pose_count() + extra} 只皮卡丘，每做完一套点亮一只", home)
        captions = self._plain_captions(home)
        self.assertEqual(len(captions), pikachu.pose_count() + extra)
        self.assertTrue(any("待评分" in cap for cap in captions))
        self.assertTrue(any(cap.startswith("阅读") and "/40" in cap for cap in captions))

    def test_teacher_writing_score_appears_on_admin_form_and_student_gallery(self):
        self._create_code()
        self._start(module="writing")
        submitted = self._submit_writing()
        self.assertEqual(submitted.status_code, 200)
        sid = submitted.get_json()["id"]

        self._login_admin()
        detail = self.client.get(f"/admin/submission/{sid}")
        self.assertEqual(detail.status_code, 200)
        html = detail.get_data(as_text=True)
        self.assertIn("writing-score-form", html)
        self.assertIn(f'action="/admin/submission/{sid}/score"', html)
        self.assertIn('name="teacher_band"', html)
        self.assertIn("待评分", html)

        saved = self.client.post(
            f"/admin/submission/{sid}/score",
            data={
                "teacher_band": "6.5",
                "teacher_task1_band": "6",
                "teacher_task2_band": "7",
                "teacher_comment": "Task 2 is stronger.",
            },
            follow_redirects=True,
        )
        self.assertEqual(saved.status_code, 200)
        saved_html = saved.get_data(as_text=True)
        self.assertIn("已保存写作评分：6.5。", saved_html)
        self.assertIn("教师评分：6.5", saved_html)
        self.assertIn("Task 1 6", saved_html)
        self.assertIn("Task 2 7", saved_html)
        self.assertIn("Task 2 is stronger.", saved_html)

        record = json.loads((appmod.SUBMISSIONS_DIR / f"{sid}.json").read_text(encoding="utf-8"))
        self.assertEqual(record["teacher_band"], 6.5)
        self.assertEqual(record["teacher_task1_band"], 6.0)
        self.assertEqual(record["teacher_task2_band"], 7.0)
        self.assertEqual(record["teacher_comment"], "Task 2 is stronger.")

        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn("写作 Set A · 6.5", self._plain_captions(home))
        self.assertNotIn("写作 Set A · 待评分", home)
        self.assertIn("教师评分 6.5", home)
        self.assertNotIn("Task 2 is stronger.", home)

    def test_teacher_writing_score_rejects_invalid_values_and_non_writing(self):
        self._create_code()
        self._start(module="writing")
        writing = self._submit_writing()
        writing_sid = writing.get_json()["id"]
        self._start(module="reading")
        reading = self._submit_reading()
        reading_sid = reading.get_json()["id"]

        self._login_admin()
        reading_detail = self.client.get(f"/admin/submission/{reading_sid}").get_data(as_text=True)
        self.assertNotIn("writing-score-form", reading_detail)
        self.assertNotIn('name="teacher_band"', reading_detail)

        refused = self.client.post(
            f"/admin/submission/{reading_sid}/score",
            data={"teacher_band": "7"},
            follow_redirects=True,
        )
        self.assertEqual(refused.status_code, 200)
        self.assertIn("只有写作答卷可以手动评分", refused.get_data(as_text=True))
        reading_record = json.loads((appmod.SUBMISSIONS_DIR / f"{reading_sid}.json").read_text(encoding="utf-8"))
        self.assertNotIn("teacher_band", reading_record)

        invalid = self.client.post(
            f"/admin/submission/{writing_sid}/score",
            data={"teacher_band": "6.25"},
            follow_redirects=True,
        )
        self.assertEqual(invalid.status_code, 200)
        self.assertIn("分数须为 0 到 9 之间的 0.5 档。", invalid.get_data(as_text=True))
        writing_record = json.loads((appmod.SUBMISSIONS_DIR / f"{writing_sid}.json").read_text(encoding="utf-8"))
        self.assertNotIn("teacher_band", writing_record)

        guest = appmod.app.test_client()
        denied = guest.post(
            f"/admin/submission/{writing_sid}/score",
            data={"teacher_band": "8"},
            follow_redirects=False,
        )
        self.assertEqual(denied.status_code, 302)
        self.assertIn("/admin/login", denied.headers.get("Location", ""))
        writing_record = json.loads((appmod.SUBMISSIONS_DIR / f"{writing_sid}.json").read_text(encoding="utf-8"))
        self.assertNotIn("teacher_band", writing_record)


class WritingSetTests(StudentPortalTestCase):
    def test_writing_set_c_renders_comic_flowchart(self):
        prompts = appmod.load_prompts()
        ids = [item.get("id") for item in prompts.get("sets") or []]
        self.assertIn("set-c", ids)
        found = next(item for item in prompts["sets"] if item["id"] == "set-c")
        t1 = found["task1"]
        self.assertEqual(t1["type"], "flowchart")
        self.assertIn("recycling plastic bottles into new products", t1["instruction"])
        self.assertEqual(t1["flowchart"]["title"], "Recycling plastic bottles")
        labels = [
            "Collection",
            "Sorting",
            "Washing & shredding",
            "Melting & pelletising",
            "Manufacturing",
            "Distribution",
        ]
        details = [
            "Used bottles from homes & public bins",
            "By colour and polymer type",
            "Cleaned then cut into flakes",
            "Flakes melted into pellets",
            "New containers, textiles, packaging",
            "Finished goods to retailers",
        ]
        steps = t1["flowchart"]["steps"]
        self.assertEqual([step["label"] for step in steps], labels)
        self.assertEqual([step["detail"] for step in steps], details)

        html = sp.writing_visual_html(t1)
        self.assertIn("chart-wrap flowchart-wrap", html)
        self.assertIn("flowchart-comic", html)
        self.assertIn("<svg", html)
        self.assertIn("Recycling plastic bottles", html)
        visible = " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())
        for label in labels:
            self.assertIn(label, visible)
        for detail in details:
            self.assertIn(detail, visible)
        self.assertNotIn("#2563eb", html)
        self.assertNotIn('rx="10"', html)
        self.assertNotIn('fill="#eff6ff"', html)

        self._create_code()
        self._login()
        api = self.client.get("/api/prompts")
        self.assertEqual(api.status_code, 200)
        payload_ids = [item.get("id") for item in api.get_json().get("sets") or []]
        self.assertEqual(payload_ids, ["set-a", "set-b", "set-c", "set-d", "set-e", "set-f"])

    def test_writing_set_d_combines_table_and_line_chart(self):
        prompts = appmod.load_prompts()
        ids = [item.get("id") for item in prompts.get("sets") or []]
        self.assertIn("set-d", ids)
        found = next(item for item in prompts["sets"] if item["id"] == "set-d")
        self.assertIn("food delivery orders in Australia", found["task1"]["instruction"])
        self.assertIn("ban dangerous sports", found["task2"]["instruction"])
        self.assertNotIn("internet searches in the US", found["task1"]["instruction"])
        html = sp.writing_visual_html(found["task1"])
        self.assertIn("combined-visual", html)
        self.assertIn("Total number of food delivery orders", html)
        self.assertIn("3.2 million", html)
        self.assertIn("QuickBite", html)
        self.assertIn("<svg", html)
        self.assertIn("18 million", html)

        self._create_code()
        self._login()
        api = self.client.get("/api/prompts")
        self.assertEqual(api.status_code, 200)
        payload_ids = [item.get("id") for item in api.get_json().get("sets") or []]
        self.assertEqual(payload_ids, ["set-a", "set-b", "set-c", "set-d", "set-e", "set-f"])

    def test_writing_set_e_renders_three_pie_charts(self):
        prompts = appmod.load_prompts()
        ids = [item.get("id") for item in prompts.get("sets") or []]
        self.assertIn("set-e", ids)
        found = next(item for item in prompts["sets"] if item["id"] == "set-e")
        t1 = found["task1"]["instruction"]
        self.assertIn("free time in 2023", t1)
        self.assertIn("Canada", t1)
        lowered = t1.lower()
        self.assertNotIn("viewership of different tv", lowered)
        self.assertNotIn("tv programme", lowered)
        self.assertNotIn("tv program", lowered)
        self.assertNotIn("10-15", t1)
        self.assertNotIn("16-20", t1)
        self.assertNotIn("21-25", t1)

        pies = found["task1"]["pie_charts"]
        official = [
            [26, 26, 23, 19, 6],
            [14, 15, 30, 23, 18],
            [4, 20, 22, 21, 33],
        ]
        official_sorted = [sorted(combo) for combo in official]
        for chart in pies["charts"]:
            values = list(chart["values"])
            self.assertEqual(sum(values), 100)
            self.assertNotIn(sorted(values), official_sorted)

        t2 = found["task2"]["instruction"]
        self.assertIn("mathematics is the most important subject", t2)
        self.assertIn("Discuss both views", t2)

        html = sp.writing_visual_html(found["task1"])
        self.assertIn("<svg", html)
        self.assertIn("Age 12–17", html)
        self.assertIn("Age 18–24", html)
        self.assertIn("Age 25–34", html)
        for name in ["Team sports", "Video games", "Reading", "Social media", "Outdoor hobbies"]:
            self.assertIn(name, html)
        self.assertIn("32%", html)
        self.assertIn("8%", html)
        self.assertIn("#1a1a1a", html)
        self.assertIn("#4a4a4a", html)
        self.assertIn("#8a8a8a", html)
        self.assertIn("#c8c8c8", html)
        self.assertIn("#ffffff", html)
        self.assertNotIn("#2563eb", html)
        self.assertIn('stroke="#222"', html)

        self._create_code()
        self._login()
        api = self.client.get("/api/prompts")
        self.assertEqual(api.status_code, 200)
        payload_ids = [item.get("id") for item in api.get_json().get("sets") or []]
        self.assertEqual(payload_ids, ["set-a", "set-b", "set-c", "set-d", "set-e", "set-f"])

    def test_task2_instruction_bolds_question_not_rubric(self):
        sample = (
            "Some people think that mathematics is the most important subject "
            "for school children to study, while others believe there are more "
            "important subjects. Discuss both views and give your own opinion.\n\n"
            "Give reasons for your answer and include any relevant examples from "
            "your own knowledge or experience.\n\n"
            "Write at least 250 words."
        )
        html = sp.format_task2_instruction(sample)
        self.assertIn('<strong class="task2-question">', html)
        start = html.find("<strong")
        end = html.find("</strong>")
        self.assertNotEqual(start, -1)
        self.assertNotEqual(end, -1)
        inner = html[start:end]
        self.assertIn("mathematics is the most important subject", inner)
        self.assertIn("Discuss both views and give your own opinion.", inner)
        self.assertNotIn("Write at least 250 words", inner)
        self.assertNotIn("Give reasons for your answer", inner)
        self.assertIn("Write at least 250 words.", html)
        self.assertIn("Give reasons for your answer", html)
        # Rubric stays outside the strong tag, after it.
        self.assertGreater(html.find("Write at least 250 words."), end)

        escaped = sp.format_task2_instruction(
            'A <topic> & "quote"\n\nWrite at least 250 words.'
        )
        self.assertIn("&lt;topic&gt;", escaped)
        self.assertIn("&amp;", escaped)
        self.assertNotIn("<topic>", escaped)

        only_question = sp.format_task2_instruction(
            "To what extent do you agree or disagree?"
        )
        self.assertTrue(only_question.startswith('<strong class="task2-question">'))
        self.assertTrue(only_question.endswith("</strong>"))
        self.assertIn("To what extent do you agree or disagree?", only_question)

        prompts = appmod.load_prompts()
        for item in prompts.get("sets") or []:
            formatted = sp.format_task2_instruction(item["task2"]["instruction"])
            self.assertIn('<strong class="task2-question">', formatted)
            close = formatted.find("</strong>")
            self.assertNotEqual(close, -1)
            self.assertNotIn("Write at least 250 words", formatted[:close])
            self.assertIn("Write at least 250 words", formatted[close:])
            view = sp.writing_view(
                {
                    "mode": "task2",
                    "prompt_set_id": item["id"],
                    "task2_text": "Sample essay.",
                    "task2_word_count": 3,
                },
                prompts,
            )
            self.assertEqual(view["task2_instruction"], formatted)

    def test_writing_set_f_renders_charity_swim_table(self):
        prompts = appmod.load_prompts()
        ids = [item.get("id") for item in prompts.get("sets") or []]
        self.assertIn("set-f", ids)
        found = next(item for item in prompts["sets"] if item["id"] == "set-f")
        t1 = found["task1"]["instruction"]
        self.assertIn("charity swim", t1)
        self.assertIn("Australia", t1)
        self.assertIn("2017 to 2021", t1)
        self.assertNotIn("marathon", t1.lower())
        self.assertNotIn("2008 to 2012", t1)
        self.assertNotIn("Age group 18", t1)
        self.assertNotIn("18-39", t1)
        self.assertNotIn("18–39", t1)

        table = found["task1"]["table"]
        official = {"1,200", "800", "2,000", "1,750", "1,050", "2,800"}
        cells = []
        for row in table["rows"]:
            cells.extend(row)
        self.assertTrue(official.isdisjoint(set(cells)))

        def parse_num(value):
            return int(str(value).replace(",", ""))

        for row in table["rows"]:
            younger, older, total = (parse_num(cell) for cell in row[1:])
            self.assertEqual(younger + older, total)

        t2 = found["task2"]["instruction"]
        self.assertIn("less and less time at home", t2)
        self.assertIn("reasons", t2)
        self.assertIn("effects", t2)

        html = sp.writing_visual_html(found["task1"])
        self.assertIn("<table", html)
        self.assertIn("Participants in a 10-kilometre charity swim in Australia", html)
        self.assertIn("Age group 16–29", html)
        self.assertIn("Age group 30+", html)
        self.assertIn("880", html)
        self.assertIn("2,350", html)

        self._create_code()
        self._login()
        api = self.client.get("/api/prompts")
        self.assertEqual(api.status_code, 200)
        payload_ids = [item.get("id") for item in api.get_json().get("sets") or []]
        self.assertEqual(payload_ids, ["set-a", "set-b", "set-c", "set-d", "set-e", "set-f"])


class AdminPaperViewTests(StudentPortalTestCase):
    def setUp(self):
        super().setUp()
        os.environ["IELTS_ADMIN_USERNAME"] = TEST_ADMIN_USER
        os.environ["IELTS_ADMIN_PASSWORD"] = TEST_ADMIN_PASS

    def _login_admin(self, client=None):
        client = client or self.client
        return client.post(
            "/admin/login",
            data={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASS},
        )

    def _submit_listening(self, name="Ada Student"):
        answers = {str(q): a for q, a in ls.official_answers().items()}
        return self.client.post(
            "/api/listening/submit",
            json={
                "candidate_name": name,
                "mode": "full",
                "prompt_set_id": "set-a",
                "answers": answers,
                "duration_seconds": 1800,
                "time_used_seconds": 1500,
            },
        )

    def test_admin_list_includes_paper_link_after_detail_link(self):
        self._create_code()
        self._start(module="writing")
        writing = self._submit_writing()
        self.assertEqual(writing.status_code, 200)
        writing_sid = writing.get_json()["id"]
        self._start(module="reading")
        reading = self._submit_reading()
        self.assertEqual(reading.status_code, 200)
        reading_sid = reading.get_json()["id"]

        admin = appmod.app.test_client()
        login = self._login_admin(admin)
        self.assertEqual(login.status_code, 302)
        page = admin.get("/admin")
        self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        self.assertIn("查看全文", html)
        self.assertIn("查看详批", html)
        self.assertIn("查看答题页面", html)
        for sid, label in ((writing_sid, "查看全文"), (reading_sid, "查看详批")):
            detail_href = f"/admin/submission/{sid}"
            paper_href = f"/admin/submission/{sid}/paper"
            self.assertIn(detail_href, html)
            self.assertIn(paper_href, html)
            detail_at = html.index(f'href="{detail_href}"')
            paper_at = html.index(f'href="{paper_href}"')
            label_at = html.index(label)
            self.assertLess(detail_at, paper_at, sid)
            self.assertLess(label_at, html.index("查看答题页面", label_at), sid)

        detail = admin.get(f"/admin/submission/{writing_sid}")
        self.assertEqual(detail.status_code, 200)
        detail_html = detail.get_data(as_text=True)
        self.assertIn("查看答题页面", detail_html)
        self.assertIn(f"/admin/submission/{writing_sid}/paper", detail_html)

    def test_admin_can_open_paper_page_and_api_for_each_module(self):
        self._create_code()
        self._start(module="writing")
        writing_sid = self._submit_writing().get_json()["id"]
        self._start(module="reading")
        reading_sid = self._submit_reading().get_json()["id"]
        self._start(module="listening")
        listening_sid = self._submit_listening().get_json()["id"]

        admin = appmod.app.test_client()
        self._login_admin(admin)
        cases = (
            (writing_sid, "writing", "exam.js"),
            (reading_sid, "reading", "reading.js"),
            (listening_sid, "listening", "listening.js"),
        )
        for sid, module, script in cases:
            page = admin.get(f"/admin/submission/{sid}/paper")
            self.assertEqual(page.status_code, 200, module)
            html = page.get_data(as_text=True)
            self.assertIn("REVIEW_CONFIG", html)
            self.assertIn(f"/api/admin/submission/{sid}", html)
            self.assertIn("返回教师后台", html)
            self.assertIn('href="/admin"', html)
            self.assertIn(script, html)
            self.assertNotIn("/api/me/submission/", html)

            api = admin.get(f"/api/admin/submission/{sid}")
            self.assertEqual(api.status_code, 200, module)
            payload = api.get_json()
            self.assertTrue(payload.get("ok"))
            self.assertEqual(payload.get("module"), module)
            if module == "writing":
                self.assertIn("The charts compare the town population", payload.get("task1_text") or "")
            elif module == "reading":
                self.assertTrue(payload.get("questions"))
                self.assertIn("review_highlights", payload)
            else:
                self.assertTrue(payload.get("questions"))
                self.assertIn("1", payload.get("transcripts") or {})

            student_api = self.client.get(f"/api/me/submission/{sid}")
            self.assertEqual(student_api.status_code, 200, module)
            student_page = self.client.get(f"/me/submission/{sid}")
            self.assertEqual(student_page.status_code, 200, module)
            student_html = student_page.get_data(as_text=True)
            self.assertIn("/api/me/submission/", student_html)
            self.assertIn("返回我的记录", student_html)
            self.assertNotIn("/api/admin/submission/", student_html)

        blocked = admin.post(
            "/api/submit",
            json={
                "candidate_name": "Ada Student",
                "mode": "full",
                "task1_text": "should not save",
                "review_mode": True,
            },
        )
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("回顾模式", blocked.get_json()["error"])

    def test_anonymous_and_student_cannot_load_admin_paper(self):
        self._create_code()
        self._start(module="reading")
        sid = self._submit_reading().get_json()["id"]

        guest = appmod.app.test_client()
        paper = guest.get(f"/admin/submission/{sid}/paper", follow_redirects=False)
        self.assertEqual(paper.status_code, 302)
        self.assertIn("/admin/login", paper.headers.get("Location", ""))
        api = guest.get(f"/api/admin/submission/{sid}")
        self.assertEqual(api.status_code, 401)
        body = api.get_json()
        self.assertFalse(body.get("ok"))
        self.assertNotIn("answers", api.get_data(as_text=True))
        self.assertNotIn("explanation", api.get_data(as_text=True))

        student = self.client
        paper = student.get(f"/admin/submission/{sid}/paper", follow_redirects=False)
        self.assertEqual(paper.status_code, 302)
        self.assertIn("/admin/login", paper.headers.get("Location", ""))
        api = student.get(f"/api/admin/submission/{sid}")
        self.assertEqual(api.status_code, 401)
        self.assertNotIn("explanation", api.get_data(as_text=True))

        own = student.get(f"/me/submission/{sid}")
        self.assertEqual(own.status_code, 200)
        own_api = student.get(f"/api/me/submission/{sid}")
        self.assertEqual(own_api.status_code, 200)
        self.assertTrue(own_api.get_json().get("ok"))





class SproutSpriteTests(unittest.TestCase):
    def test_sprite_poses_are_original_grids(self):
        ids = sprout.pose_ids()
        self.assertGreaterEqual(len(ids), 14)
        self.assertLessEqual(len(ids), 18)
        self.assertEqual(len(ids), len(set(ids)))
        seen = set()
        for name in ids:
            rows = sprout.POSES[name]
            widths = {len(line) for line in rows}
            self.assertEqual(len(widths), 1, name)
            width = len(rows[0])
            self.assertGreaterEqual(width, 12)
            self.assertLessEqual(width, 28)
            self.assertGreaterEqual(len(rows), 9)
            letters = {ch for line in rows for ch in line if ch != "."}
            self.assertTrue(letters <= sprout.COLOR_LETTERS, name)
            self.assertTrue({"T", "K", "L"} <= letters, name)
            key = tuple(rows)
            self.assertNotIn(key, seen)
            seen.add(key)
            raster = sprout.sprite_cells(rows, lit=True)
            self.assertGreater(len(raster["cells"]), 0, name)
            self.assertEqual(raster["cols"] * raster["rows"], len(raster["cells"]))
            self.assertTrue(any(not cell["empty"] and cell["lit"] and cell["color"] for cell in raster["cells"]))
        self.assertNotIn("ball", sprout.DECOS)
        self.assertNotIn("pokeball", sprout.DECOS)
        for name, rows in sprout.DECOS.items():
            letters = {ch for line in rows for ch in line if ch != "."}
            self.assertTrue(letters <= sprout.COLOR_LETTERS, name)
            # No red-and-white official-looking balls.
            self.assertFalse({"R", "W"} <= letters and name in {"ball", "pokeball"})

    def test_gallery_reuses_poses_when_it_grows(self):
        extra = 3
        attempts = [{"id": f"a{i}", "caption": f"写作 Set A · {i}"} for i in range(sprout.pose_count() + extra)]
        gallery = sprout.gallery(attempts)
        self.assertEqual(gallery["theme"], "sprout")
        self.assertEqual(gallery["lit"], sprout.pose_count() + extra)
        self.assertEqual(gallery["total"], sprout.pose_count() + extra)
        self.assertEqual(len(gallery["figures"]), sprout.pose_count() + extra)
        ids = sprout.pose_ids()
        self.assertEqual(gallery["figures"][0]["pose"], ids[0])
        self.assertEqual(gallery["figures"][len(ids)]["pose"], ids[0])
        self.assertEqual(gallery["figures"][-1]["pose"], ids[extra - 1])
        self.assertTrue(all(fig["lit"] for fig in gallery["figures"]))
        self.assertTrue(all(
            cell["lit"]
            for fig in gallery["figures"]
            for cell in fig["cells"]
            if not cell["empty"]
        ))
        self.assertTrue(gallery["decos"])
        unlit = sprout.gallery([])
        self.assertEqual(unlit["lit"], 0)
        self.assertEqual(len(unlit["figures"]), sprout.pose_count())
        self.assertTrue(all(not fig["lit"] for fig in unlit["figures"]))

    def test_is_rainie_code_matches_invite_string_only(self):
        self.assertTrue(sprout.is_rainie_code("Rainie"))
        self.assertTrue(sprout.is_rainie_code("rainie"))
        self.assertTrue(sprout.is_rainie_code("RAINIE"))
        self.assertTrue(sprout.is_rainie_code(" Rainie "))
        self.assertFalse(sprout.is_rainie_code("CLASS01"))
        self.assertFalse(sprout.is_rainie_code("Rainie1"))
        self.assertFalse(sprout.is_rainie_code("Rainies"))
        self.assertFalse(sprout.is_rainie_code(""))
        self.assertFalse(sprout.is_rainie_code(None))


class RainieSproutGalleryTests(StudentPortalTestCase):
    def setUp(self):
        super().setUp()
        os.environ["IELTS_ADMIN_USERNAME"] = TEST_ADMIN_USER
        os.environ["IELTS_ADMIN_PASSWORD"] = TEST_ADMIN_PASS

    def _login_admin(self, client=None):
        client = client or self.client
        return client.post(
            "/admin/login",
            data={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASS},
        )

    def _submit_listening(self, name="Ada Student", prompt_set_id="set-a"):
        answers = {str(q): a for q, a in ls.official_answers().items()}
        return self.client.post(
            "/api/listening/submit",
            json={
                "candidate_name": name,
                "mode": "full",
                "prompt_set_id": prompt_set_id,
                "answers": answers,
                "duration_seconds": 1800,
                "time_used_seconds": 1500,
            },
        )

    def _seed_attempts(self, count, rec, name="Ada Student"):
        index = json.loads(appmod.INDEX_PATH.read_text(encoding="utf-8"))
        submissions = index.setdefault("submissions", [])
        modules = ("writing", "reading", "listening")
        for i in range(count):
            sid = f"sprout-{i:04d}-bbbb-cccc-dddd-eeeeeeeeeeee"
            module = modules[i % 3]
            set_id = f"set-{chr(ord('a') + (i % 6))}"
            record = {
                "id": sid,
                "timestamp": f"2026-11-{(i % 28) + 1:02d}T09:15:00+08:00",
                "candidate_name": name,
                "module": module,
                "mode": "full",
                "prompt_set_id": set_id,
                "time_used_seconds": 12,
                "invite_code_id": rec["id"],
            }
            if module in {"reading", "listening"}:
                record["score"] = 30 + (i % 10)
                record["total"] = 40
                record["band_estimate"] = 7.0
            (appmod.SUBMISSIONS_DIR / f"{sid}.json").write_text(
                json.dumps(record, ensure_ascii=False), encoding="utf-8"
            )
            index_row = {
                "id": sid,
                "timestamp": record["timestamp"],
                "candidate_name": name,
                "module": module,
                "mode": "full",
                "prompt_set_id": set_id,
                "time_used_seconds": 12,
                "invite_code_id": rec["id"],
            }
            if module in {"reading", "listening"}:
                index_row["score"] = record["score"]
                index_row["total"] = record["total"]
                index_row["band_estimate"] = record["band_estimate"]
            submissions.insert(0, index_row)
        appmod.save_index(index)

    def _figures(self, html):
        return re.findall(r'<figure\s+class="pikachu-figure([^"]*)"', html)

    def _sprout_figures(self, html):
        return re.findall(r'<figure\s+class="sprout-figure([^"]*)"', html)

    def _sprout_caption_texts(self, html):
        return re.findall(r'<figcaption class="sprout-caption">\s*(.*?)\s*</figcaption>', html, flags=re.S)

    def _sprout_plain_captions(self, html):
        out = []
        for raw in self._sprout_caption_texts(html):
            text = re.sub(r"<[^>]+>", "", raw)
            out.append(" ".join(unescape(text).split()))
        return out

    def _login_rainie(self, code="Rainie", name="Grove Student"):
        rec = self._create_code(code=code)
        self._login(name=name, code=code)
        return rec

    def test_rainie_records_use_sprout_gallery_not_pikachu(self):
        self._login_rainie()
        home = self.client.get("/me")
        self.assertEqual(home.status_code, 200)
        html = home.get_data(as_text=True)
        self.assertIn("sprout-progress", html)
        self.assertIn("我的妙蛙种子", html)
        self.assertIn("还没有点亮的妙蛙种子，每做完一套点亮一只", html)
        self.assertIn("未点亮的像素妙蛙种子", html)
        self.assertNotIn("pikachu-progress", html)
        self.assertNotIn("我的皮卡丘", html)
        self.assertNotIn("还没有点亮的皮卡丘", html)
        figures = self._sprout_figures(html)
        self.assertEqual(len(figures), sprout.pose_count())
        self.assertTrue(all("is-unlit" in cls for cls in figures))
        self.assertEqual(html.count("sprout-cell is-lit"), 0)
        self.assertGreater(html.count("sprout-cell"), 0)
        self.assertEqual(self._sprout_plain_captions(html), [])

    def test_other_invite_code_still_gets_pikachu(self):
        self._create_code(code="CLASS01")
        self._login(name="Rainie", code="CLASS01")
        html = self.client.get("/me").get_data(as_text=True)
        self.assertIn("pikachu-progress", html)
        self.assertIn("我的皮卡丘", html)
        self.assertNotIn("sprout-progress", html)
        self.assertNotIn("我的妙蛙种子", html)
        self.assertEqual(len(self._figures(html)), pikachu.pose_count())

    def test_rainie_code_match_is_case_insensitive(self):
        self._create_code(code="rainie")
        self._login(name="Grove Student", code="RAINIE")
        html = self.client.get("/me").get_data(as_text=True)
        self.assertIn("sprout-progress", html)
        self.assertIn("我的妙蛙种子", html)
        self.assertNotIn("pikachu-progress", html)

    def test_each_submitted_paper_lights_one_sprout_oldest_first(self):
        self._login_rainie()

        self._start(name="Grove Student", code="Rainie", module="writing")
        writing = self._submit_writing(name="Grove Student")
        self.assertEqual(writing.status_code, 200)
        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn("已点亮 1 只妙蛙种子，每做完一套点亮一只", home)
        figures = self._sprout_figures(home)
        self.assertEqual(len(figures), sprout.pose_count())
        self.assertIn("is-lit", figures[0])
        self.assertTrue(all("is-unlit" in cls for cls in figures[1:]))
        self.assertIn("写作 Set A · 待评分", self._sprout_plain_captions(home))
        self.assertIn("/me/submission/" + writing.get_json()["id"], home)

        self._start(name="Grove Student", code="Rainie", module="reading")
        reading = self._submit_reading(name="Grove Student")
        self.assertEqual(reading.status_code, 200)
        reading_payload = reading.get_json()
        reading_caption = f"阅读 Set A · {reading_payload['score']}/{reading_payload['total']} · {rs.format_band(reading_payload['band_estimate'])}"
        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn("已点亮 2 只妙蛙种子，每做完一套点亮一只", home)
        figures = self._sprout_figures(home)
        self.assertIn("is-lit", figures[0])
        self.assertIn("is-lit", figures[1])
        self.assertTrue(all("is-unlit" in cls for cls in figures[2:]))
        captions = self._sprout_plain_captions(home)
        self.assertEqual(captions[0], "写作 Set A · 待评分")
        self.assertEqual(captions[1], reading_caption)
        writing_pos = home.find("写作 Set A · 待评分")
        reading_pos = home.find(reading_caption)
        self.assertLess(writing_pos, reading_pos)

        self._start(name="Grove Student", code="Rainie", module="listening")
        listening = self._submit_listening(name="Grove Student")
        self.assertEqual(listening.status_code, 200)
        listening_payload = listening.get_json()
        listening_caption = f"听力 Set A · {listening_payload['score']}/{listening_payload['total']} · {ls.format_band(listening_payload['band_estimate'])}"
        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn("已点亮 3 只妙蛙种子，每做完一套点亮一只", home)
        self.assertIn(listening_caption, self._sprout_plain_captions(home))

    def test_speaking_does_not_light_a_sprout(self):
        rec = self._login_rainie()
        self._start(name="Grove Student", code="Rainie", module="writing")
        writing = self._submit_writing(name="Grove Student")
        self.assertEqual(writing.status_code, 200)

        index = json.loads(appmod.INDEX_PATH.read_text(encoding="utf-8"))
        sid = "speak-0001-bbbb-cccc-dddd-eeeeeeeeeeee"
        record = {
            "id": sid,
            "timestamp": "2026-11-16T12:00:00+08:00",
            "candidate_name": "Grove Student",
            "module": "speaking",
            "mode": "full",
            "prompt_set_id": "set-a",
            "time_used_seconds": 12,
            "invite_code_id": rec["id"],
        }
        (appmod.SUBMISSIONS_DIR / f"{sid}.json").write_text(
            json.dumps(record, ensure_ascii=False), encoding="utf-8"
        )
        index.setdefault("submissions", []).insert(0, {
            "id": sid,
            "timestamp": record["timestamp"],
            "candidate_name": "Grove Student",
            "module": "speaking",
            "mode": "full",
            "prompt_set_id": "set-a",
            "time_used_seconds": 12,
            "invite_code_id": rec["id"],
        })
        appmod.save_index(index)

        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn("已点亮 1 只妙蛙种子，每做完一套点亮一只", home)
        figures = self._sprout_figures(home)
        self.assertEqual(len(figures), sprout.pose_count())
        lit = [cls for cls in figures if "is-lit" in cls]
        self.assertEqual(len(lit), 1)
        self.assertEqual(self._sprout_plain_captions(home), ["写作 Set A · 待评分"])
        self.assertNotIn(sid, home)

    def test_gallery_grows_on_rainie_records_when_attempts_exceed_poses(self):
        rec = self._login_rainie()
        extra = 2
        self._seed_attempts(sprout.pose_count() + extra, rec, name="Grove Student")
        home = self.client.get("/me").get_data(as_text=True)
        figures = self._sprout_figures(home)
        self.assertEqual(len(figures), sprout.pose_count() + extra)
        self.assertTrue(all("is-lit" in cls for cls in figures))
        self.assertIn(f"已点亮 {sprout.pose_count() + extra} 只妙蛙种子，每做完一套点亮一只", home)
        captions = self._sprout_plain_captions(home)
        self.assertEqual(len(captions), sprout.pose_count() + extra)
        self.assertTrue(any("待评分" in cap for cap in captions))
        self.assertTrue(any(cap.startswith("阅读") and "/40" in cap for cap in captions))
        self.assertNotIn("pikachu-progress", home)

    def test_teacher_writing_score_appears_on_sprout_caption(self):
        self._login_rainie()
        self._start(name="Grove Student", code="Rainie", module="writing")
        submitted = self._submit_writing(name="Grove Student")
        self.assertEqual(submitted.status_code, 200)
        sid = submitted.get_json()["id"]

        self._login_admin()
        saved = self.client.post(
            f"/admin/submission/{sid}/score",
            data={
                "teacher_band": "7.0",
                "teacher_task1_band": "7",
                "teacher_task2_band": "7",
                "teacher_comment": "Clear and organised.",
            },
            follow_redirects=True,
        )
        self.assertEqual(saved.status_code, 200)

        # Re-login as the student; admin login may have cleared the student session.
        self._login(name="Grove Student", code="Rainie")
        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn("写作 Set A · 7", self._sprout_plain_captions(home))
        self.assertNotIn("写作 Set A · 待评分", home)



class GrowthStackScoresTests(unittest.TestCase):
    def test_best_band_uses_teacher_writing_and_reference_scores(self):
        attempts = [
            {"module": "reading", "band_label": "6.5", "band_estimate": 6.5},
            {"module": "listening", "band_label": "7.0"},
            {"module": "writing", "teacher_band": 6.0, "official_score": 9.0},
            {"module": "speaking", "band_estimate": 9.0, "band_label": "9.0"},
            {"module": "writing", "official_score": 8.5},
        ]
        scores = sp.growth_stack_scores(attempts)
        self.assertEqual(gs.best_growth_band(scores), 7.0)
        modules = [row["module"] for row in scores]
        self.assertEqual(modules, ["reading", "listening", "writing"])
        self.assertTrue(all("official_score" not in row for row in scores))

    def test_empty_scores_when_nothing_usable(self):
        self.assertEqual(sp.growth_stack_scores([]), [])
        self.assertEqual(
            sp.growth_stack_scores([
                {"module": "writing"},
                {"module": "speaking", "band_estimate": 9.0},
                {"module": "writing", "official_score": 9.0},
            ]),
            [],
        )
        self.assertIsNone(gs.best_growth_band(sp.growth_stack_scores(None)))


class GrowthStackRecordsTests(StudentPortalTestCase):
    def setUp(self):
        super().setUp()
        os.environ["IELTS_ADMIN_USERNAME"] = TEST_ADMIN_USER
        os.environ["IELTS_ADMIN_PASSWORD"] = TEST_ADMIN_PASS

    def _login_admin(self):
        return self.client.post(
            "/admin/login",
            data={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASS},
        )

    def _add_index_row(self, rec, *, name, module, **fields):
        index = json.loads(appmod.INDEX_PATH.read_text(encoding="utf-8"))
        sid = fields.pop("id", None) or f"{module}-{len(index.get('submissions') or []):04d}-bbbb-cccc-dddd-eeeeeeeeeeee"
        record = {
            "id": sid,
            "timestamp": fields.pop("timestamp", "2026-11-16T09:15:00+08:00"),
            "candidate_name": name,
            "module": module,
            "mode": "full",
            "prompt_set_id": "set-a",
            "time_used_seconds": 12,
            "invite_code_id": rec["id"],
        }
        record.update(fields)
        (appmod.SUBMISSIONS_DIR / f"{sid}.json").write_text(
            json.dumps(record, ensure_ascii=False), encoding="utf-8"
        )
        index_row = {
            "id": sid,
            "timestamp": record["timestamp"],
            "candidate_name": name,
            "module": module,
            "mode": "full",
            "prompt_set_id": "set-a",
            "time_used_seconds": 12,
            "invite_code_id": rec["id"],
        }
        for key in ("score", "total", "band_estimate", "teacher_band", "official_score"):
            if key in record:
                index_row[key] = record[key]
        index.setdefault("submissions", []).insert(0, index_row)
        appmod.save_index(index)
        return sid

    def test_stack_appears_for_normal_code_and_rainie_keeps_galleries(self):
        self._create_code()
        self._login()
        html = self.client.get("/me").get_data(as_text=True)
        self.assertIn('class="growth-stack is-empty"', html)
        self.assertIn("成长进度", html)
        self.assertIn("暂无评分", html)
        self.assertIn("pikachu-progress", html)
        self.assertNotIn("sprout-progress", html)
        self.assertIn("records-progress-row", html)
        self.assertNotIn("growth_stack.css", html)

        rainie = appmod.app.test_client()
        self._create_code(code="Rainie")
        rainie.post(
            "/me/login",
            data={"candidate_name": "Grove Student", "invite_code": "Rainie"},
        )
        rainie_html = rainie.get("/me").get_data(as_text=True)
        self.assertIn('class="growth-stack is-empty"', rainie_html)
        self.assertIn("成长进度", rainie_html)
        self.assertIn("sprout-progress", rainie_html)
        self.assertIn("我的妙蛙种子", rainie_html)
        self.assertNotIn("pikachu-progress", rainie_html)
        self.assertIn("sprout-gallery", rainie_html)

    def test_empty_state_when_no_scores(self):
        rec = self._create_code()
        self._login()
        self._start(module="writing")
        submitted = self._submit_writing()
        self.assertEqual(submitted.status_code, 200)

        html = self.client.get("/me").get_data(as_text=True)
        self.assertIn("成长进度", html)
        self.assertIn("暂无评分", html)
        self.assertIn('class="growth-stack is-empty"', html)
        self.assertNotIn("当前最高", html)
        self.assertEqual(html.count('<li class="growth-stack-stage is-lit'), 0)
        self.assertEqual(html.count('<li class="growth-stack-stage is-unlit'), 8)
        self.assertIn("pikachu-progress", html)
        self.assertIn("写作 Set A · 待评分", html)

        # A speaking paper still leaves the stack empty.
        self._add_index_row(
            rec,
            name="Ada Student",
            module="speaking",
            id="speak-empty-bbbb-cccc-dddd-eeeeeeeeeeee",
            band_estimate=9.0,
        )
        html = self.client.get("/me").get_data(as_text=True)
        self.assertIn('class="growth-stack is-empty"', html)
        self.assertIn("暂无评分", html)
        self.assertNotIn("speak-empty", html)

    def test_best_band_ignores_speaking_and_writing_official_score(self):
        rec = self._create_code()
        self._login()
        self._add_index_row(
            rec,
            name="Ada Student",
            module="writing",
            id="write-off-bbbb-cccc-dddd-eeeeeeeeeeee",
            official_score=9.0,
        )
        self._add_index_row(
            rec,
            name="Ada Student",
            module="reading",
            id="read-band-bbbb-cccc-dddd-eeeeeeeeeeee",
            score=28,
            total=40,
            band_estimate=6.5,
        )
        self._add_index_row(
            rec,
            name="Ada Student",
            module="listening",
            id="listen-band-bbbb-cccc-dddd-eeeeeeeeeeee",
            score=25,
            total=40,
            band_estimate=6.0,
        )
        self._add_index_row(
            rec,
            name="Ada Student",
            module="speaking",
            id="speak-band-bbbb-cccc-dddd-eeeeeeeeeeee",
            band_estimate=9.0,
        )

        html = self.client.get("/me").get_data(as_text=True)
        self.assertIn('class="growth-stack" data-band="6.5"', html)
        self.assertIn("当前最高 6.5", html)
        self.assertEqual(html.count('<li class="growth-stack-stage is-lit'), 3)
        self.assertIn("pikachu-progress", html)
        self.assertNotIn("sprout-progress", html)
        self.assertNotIn("speak-band", html)

        # Teacher writing band becomes the new best; hidden official_score stays ignored.
        writing_path = appmod.SUBMISSIONS_DIR / "write-off-bbbb-cccc-dddd-eeeeeeeeeeee.json"
        record = json.loads(writing_path.read_text(encoding="utf-8"))
        record["teacher_band"] = 8.0
        writing_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        index = json.loads(appmod.INDEX_PATH.read_text(encoding="utf-8"))
        for row in index.get("submissions") or []:
            if row.get("id") == "write-off-bbbb-cccc-dddd-eeeeeeeeeeee":
                row["teacher_band"] = 8.0
        appmod.save_index(index)

        html = self.client.get("/me").get_data(as_text=True)
        self.assertIn('class="growth-stack" data-band="8.0"', html)
        self.assertIn("当前最高 8.0", html)
        self.assertEqual(html.count('<li class="growth-stack-stage is-lit'), 6)
        self.assertIn("写作 Set A · 8", html)


if __name__ == "__main__":
    unittest.main()
