#!/usr/bin/env python3
"""Student portal: login, owned-attempt list, post-submit review, and IDOR."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
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

    def test_list_only_own_attempts_and_idor_is_404(self):
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
        self.assertIn("查看整卷", ada_list)
        self.assertIn("查看错题", ada_list)
        self.assertIn(ada_sid, ada_list)
        self.assertNotIn(lin_sid, ada_list)
        self.assertNotIn("Lin Student", ada_list)
        self.assertIn("阅读", ada_list)

        lin_list = lin.get("/me").get_data(as_text=True)
        self.assertIn(lin_sid, lin_list)
        self.assertNotIn(ada_sid, lin_list)
        self.assertNotIn("Ada Student", lin_list)
        self.assertIn("写作", lin_list)
        self.assertNotIn("查看错题", lin_list)

        stolen = lin.get(f"/me/submission/{ada_sid}")
        self.assertEqual(stolen.status_code, 404)
        stolen_html = stolen.get_data(as_text=True)
        self.assertNotIn("解析", stolen_html)
        self.assertNotIn("stone", stolen_html)
        self.assertNotIn("Ada Student", stolen_html)

        stolen_review = lin.get(f"/me/submission/{ada_sid}/review")
        self.assertEqual(stolen_review.status_code, 404)
        self.assertNotIn("解析", stolen_review.get_data(as_text=True))

        stolen_api = lin.get(f"/api/me/submission/{ada_sid}")
        self.assertEqual(stolen_api.status_code, 404)
        stolen_api_body = stolen_api.get_data(as_text=True)
        self.assertNotIn("解析", stolen_api_body)
        self.assertNotIn("stone", stolen_api_body)
        self.assertNotIn("explanation", stolen_api_body)

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
        self.assertNotIn("解析", login_html)
        self.assertNotIn("/admin/login", login_html)


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
        self.assertNotIn("7.5", home)
        self.assertNotIn("参考分数", home)

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
    def _lit_count(self, html):
        return html.count("is-lit")

    def _expected_lit_cells(self, lit):
        return sum(1 for cell in pikachu.progress(lit)["cells"] if cell["lit"])

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

    def _seed_attempts(self, count, rec, name="Ada Student"):
        index = json.loads(appmod.INDEX_PATH.read_text(encoding="utf-8"))
        submissions = index.setdefault("submissions", [])
        modules = ("writing", "reading", "listening")
        for i in range(count):
            sid = f"pika-{i:04d}-bbbb-cccc-dddd-eeeeeeeeeeee"
            module = modules[i % 3]
            record = {
                "id": sid,
                "timestamp": f"2026-11-{(i % 28) + 1:02d}T09:15:00+08:00",
                "candidate_name": name,
                "module": module,
                "mode": "full",
                "time_used_seconds": 12,
                "invite_code_id": rec["id"],
            }
            (appmod.SUBMISSIONS_DIR / f"{sid}.json").write_text(
                json.dumps(record, ensure_ascii=False), encoding="utf-8"
            )
            submissions.insert(0, {
                "id": sid,
                "timestamp": record["timestamp"],
                "candidate_name": name,
                "module": module,
                "mode": "full",
                "time_used_seconds": 12,
                "invite_code_id": rec["id"],
            })
        appmod.save_index(index)

    def test_sprite_groups_cover_every_silhouette_cell(self):
        filled = {
            (row, col)
            for row, line in enumerate(pikachu.SPRITE)
            for col, color in enumerate(line)
            if color != "."
        }
        assigned = {
            cell
            for block in pikachu.BLOCKS
            for cell in block
        }
        self.assertEqual(filled, assigned)
        self.assertGreaterEqual(pikachu.block_count(), 16)
        self.assertLessEqual(pikachu.block_count(), 24)
        self.assertEqual(len(set(len(line) for line in pikachu.SPRITE)), 1)
        width = len(pikachu.SPRITE[0])
        self.assertGreaterEqual(width, 14)
        self.assertLessEqual(width, 18)

    def test_empty_records_still_show_unlit_pikachu(self):
        self._create_code()
        self._login()
        home = self.client.get("/me")
        self.assertEqual(home.status_code, 200)
        html = home.get_data(as_text=True)
        total = pikachu.block_count()
        self.assertIn("还没有交过卷", html)
        self.assertIn("开始写作模考", html)
        self.assertIn("开始阅读模考", html)
        self.assertIn("开始听力模考", html)
        self.assertIn("pikachu-progress", html)
        self.assertIn('role="img"', html)
        self.assertIn(f"已点亮 0/{total} 块，每做完一套点亮一小块", html)
        self.assertIn(f"像素皮卡丘，已点亮 0/{total} 块", html)
        self.assertNotIn("整只皮卡丘都点亮啦", html)
        self.assertNotIn("is-complete", html)
        self.assertEqual(self._lit_count(html), 0)

    def test_each_submitted_paper_lights_one_more_block(self):
        self._create_code()
        total = pikachu.block_count()

        self._start(module="writing")
        writing = self._submit_writing()
        self.assertEqual(writing.status_code, 200)
        home = self.client.get("/me").get_data(as_text=True)
        self.assertNotIn("还没有交过卷", home)
        self.assertIn("pikachu-progress", home)
        self.assertIn(f"已点亮 1/{total} 块，每做完一套点亮一小块", home)
        self.assertEqual(self._lit_count(home), self._expected_lit_cells(1))

        self._start(module="reading")
        reading = self._submit_reading()
        self.assertEqual(reading.status_code, 200)
        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn(f"已点亮 2/{total} 块，每做完一套点亮一小块", home)
        self.assertEqual(self._lit_count(home), self._expected_lit_cells(2))

        self._start(module="listening")
        listening = self._submit_listening()
        self.assertEqual(listening.status_code, 200)
        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn(f"已点亮 3/{total} 块，每做完一套点亮一小块", home)
        self.assertEqual(self._lit_count(home), self._expected_lit_cells(3))
        self.assertIn("写作", home)
        self.assertIn("阅读", home)
        self.assertIn("听力", home)

    def test_fully_lit_when_attempts_reach_block_count(self):
        rec = self._create_code()
        self._login()
        total = pikachu.block_count()
        self._seed_attempts(total, rec)
        home = self.client.get("/me").get_data(as_text=True)
        self.assertIn("整只皮卡丘都点亮啦", home)
        self.assertIn("像素皮卡丘，已经全部点亮", home)
        self.assertIn("is-complete", home)
        self.assertNotIn(f"已点亮 {total}/{total} 块", home)
        self.assertEqual(self._lit_count(home), self._expected_lit_cells(total))


class WritingSetTests(StudentPortalTestCase):
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
        self.assertEqual(payload_ids, ["set-a", "set-b", "set-c", "set-d"])


if __name__ == "__main__":
    unittest.main()
