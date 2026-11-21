#!/usr/bin/env python3
"""Teacher preview of each student's 我的记录 homepage."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = Path(__file__).resolve().parent
for path in (ROOT, TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import access as accessmod  # noqa: E402
import app as appmod  # noqa: E402
import student_portal as sp  # noqa: E402

from test_student_portal import (  # noqa: E402
    TEST_ADMIN_PASS,
    TEST_ADMIN_USER,
    StudentPortalTestCase,
)


HIDDEN_WRITING_KEYS = (
    *sp.WRITING_SCORE_KEYS,
    *sp.TEACHER_CRITERION_KEYS,
    "teacher_comment",
    "teacher_task1_band",
    "teacher_task2_band",
    "Task Achievement",
    "任务完成",
)


class AdminStudentRecordsTests(StudentPortalTestCase):
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

    def _assert_hidden_teacher_fields(self, text: str, comment: str | None = None):
        for key in HIDDEN_WRITING_KEYS:
            self.assertNotIn(key, text, key)
        if comment:
            self.assertNotIn(comment, text)

    def test_records_tab_follows_invites_and_lists_students(self):
        rec = self._create_code(code="CLASS01", note="A班")
        self._login()
        self._start(module="writing")
        self._submit_writing()

        admin = appmod.app.test_client()
        self.assertEqual(self._login_admin(admin).status_code, 302)

        portal = admin.get("/admin")
        self.assertEqual(portal.status_code, 200)
        html = portal.get_data(as_text=True)
        self.assertIn('href="/admin?tab=invites"', html)
        self.assertIn('href="/admin?tab=records"', html)
        self.assertLess(html.index("邀请码</a>"), html.index("学生记录</a>"))

        invites = admin.get("/admin?tab=invites")
        invites_html = invites.get_data(as_text=True)
        self.assertIn("查看记录主页", invites_html)
        self.assertIn(f'/admin/records/{rec["id"]}', invites_html)

        listing = admin.get("/admin?tab=records")
        self.assertEqual(listing.status_code, 200)
        listing_html = listing.get_data(as_text=True)
        self.assertIn("学生记录", listing_html)
        self.assertIn("CLASS01", listing_html)
        self.assertIn("A班", listing_html)
        self.assertIn("Ada Student", listing_html)
        self.assertIn("1 份", listing_html)
        self.assertIn(f'href="/admin/records/{rec["id"]}"', listing_html)
        self.assertIn("查看记录主页", listing_html)

    def test_admin_can_open_student_records_homepage(self):
        rec = self._create_code(code="CLASS01", note="A班")
        self._login()
        self._start(module="writing")
        writing = self._submit_writing()
        self.assertEqual(writing.status_code, 200)
        writing_sid = writing.get_json()["id"]
        self._start(module="reading")
        reading = self._submit_reading()
        self.assertEqual(reading.status_code, 200)
        reading_sid = reading.get_json()["id"]

        comment = "Task 2 is stronger."
        admin = appmod.app.test_client()
        self._login_admin(admin)
        scored = admin.post(
            f"/admin/submission/{writing_sid}/score",
            data={
                "teacher_task1_ta": "6",
                "teacher_task1_cc": "6",
                "teacher_task1_lr": "6",
                "teacher_task1_gra": "7",
                "teacher_task2_tr": "7",
                "teacher_task2_cc": "7",
                "teacher_task2_lr": "7",
                "teacher_task2_gra": "6",
                "teacher_comment": comment,
            },
            follow_redirects=True,
        )
        self.assertEqual(scored.status_code, 200)

        page = admin.get(f"/admin/records/{rec['id']}")
        self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        self.assertIn("你好，Ada Student", html)
        self.assertIn("我的皮卡丘", html)
        self.assertIn("最高三项平均分", html)
        self.assertIn("教师评分 7", html)
        self.assertIn("查看整卷", html)
        self.assertIn(f"/admin/records/{rec['id']}/submission/{writing_sid}", html)
        self.assertIn(f"/admin/records/{rec['id']}/submission/{reading_sid}", html)
        self.assertIn(f"/admin/records/{rec['id']}/submission/{reading_sid}/review", html)
        self.assertNotIn("/me/submission/", html)
        self.assertNotIn('href="/me/logout"', html)
        self.assertIn("正在查看该学生的「我的记录」主页", html)
        self.assertIn("CLASS01", html)
        self.assertIn("A班", html)
        self._assert_hidden_teacher_fields(html, comment)

        paper = admin.get(f"/admin/records/{rec['id']}/submission/{writing_sid}")
        self.assertEqual(paper.status_code, 200)
        paper_html = paper.get_data(as_text=True)
        self.assertIn("返回我的记录", paper_html)
        self.assertIn(f"/admin/records/{rec['id']}", paper_html)
        self.assertIn(f"/api/admin/submission/{writing_sid}", paper_html)
        self._assert_hidden_teacher_fields(paper_html, comment)

        api = admin.get(f"/api/admin/submission/{writing_sid}")
        self.assertEqual(api.status_code, 200)
        payload = api.get_json()
        raw = api.get_data(as_text=True)
        self.assertTrue(payload.get("ok"))
        for key in (
            "teacher_task1_ta",
            "teacher_task2_tr",
            "teacher_comment",
            "official_score",
            "task1_band",
            "task2_band",
            "band_estimate",
        ):
            self.assertNotIn(key, payload)
            self.assertNotIn(key, raw)
        self.assertNotIn(comment, raw)

    def test_rainie_preview_keeps_sprout_gallery(self):
        rec = self._create_code(code="Rainie", note="Grove")
        self._login(name="Grove Student", code="Rainie")
        self._start(name="Grove Student", code="Rainie", module="writing")
        self._submit_writing(name="Grove Student")

        admin = appmod.app.test_client()
        self._login_admin(admin)
        page = admin.get(f"/admin/records/{rec['id']}")
        self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        self.assertIn("你好，Grove Student", html)
        self.assertIn("我的妙蛙种子", html)
        self.assertIn("sprout-progress", html)
        self.assertNotIn("我的皮卡丘", html)
        self.assertNotIn("pikachu-progress", html)

    def test_unauthenticated_and_student_cannot_open_admin_records(self):
        ada = self._create_code(code="ADA01")
        bob = self._create_code(code="BOB01")
        self._login(name="Ada Student", code="ADA01")
        self._start(name="Ada Student", code="ADA01", module="writing")
        ada_sid = self._submit_writing(name="Ada Student").get_json()["id"]

        outsider = appmod.app.test_client()
        outsider.post(
            "/me/login",
            data={"candidate_name": "Bob Student", "invite_code": "BOB01"},
        )
        outsider.post(
            "/api/session/start",
            json={
                "candidate_name": "Bob Student",
                "invite_code": "BOB01",
                "module": "writing",
                "mode": "full",
            },
        )
        outsider.post(
            "/api/submit",
            json={
                "candidate_name": "Bob Student",
                "mode": "full",
                "prompt_set_id": "set-a",
                "task1_text": "Bob charts.",
                "task2_text": "Bob essay.",
                "duration_seconds": 3600,
                "time_remaining_seconds": 288,
                "time_used_seconds": 3312,
            },
        )

        guest = appmod.app.test_client()
        for path in (
            f"/admin/records/{ada['id']}",
            f"/admin/records/{ada['id']}/submission/{ada_sid}",
            "/admin?tab=records",
        ):
            res = guest.get(path, follow_redirects=False)
            self.assertEqual(res.status_code, 302, path)
            self.assertIn("/admin/login", res.headers.get("Location", ""), path)

        # A logged-in student must not open another student's admin preview,
        # or even their own admin records URL without teacher login.
        for client, cid, sid in (
            (outsider, ada["id"], ada_sid),
            (outsider, bob["id"], ada_sid),
            (self.client, ada["id"], ada_sid),
            (self.client, bob["id"], ada_sid),
        ):
            home = client.get(f"/admin/records/{cid}", follow_redirects=False)
            self.assertEqual(home.status_code, 302, cid)
            self.assertIn("/admin/login", home.headers.get("Location", ""))
            self.assertNotIn("我的皮卡丘", home.get_data(as_text=True))
            paper = client.get(
                f"/admin/records/{cid}/submission/{sid}",
                follow_redirects=False,
            )
            self.assertEqual(paper.status_code, 302, sid)
            self.assertIn("/admin/login", paper.headers.get("Location", ""))

        # Students still only see their own /me records.
        ada_home = self.client.get("/me").get_data(as_text=True)
        self.assertIn("你好，Ada Student", ada_home)
        self.assertIn(f"/me/submission/{ada_sid}", ada_home)
        self.assertNotIn("Bob Student", ada_home)
        self.assertNotIn("admin-preview-bar", ada_home)
        self.assertNotIn("/admin/records/", ada_home)

        bob_home = outsider.get("/me").get_data(as_text=True)
        self.assertIn("你好，Bob Student", bob_home)
        self.assertNotIn("Ada Student", bob_home)
        self.assertNotIn(ada_sid, bob_home)

        # Student-facing APIs still hide teacher score keys.
        admin = appmod.app.test_client()
        self._login_admin(admin)
        admin.post(
            f"/admin/submission/{ada_sid}/score",
            data={
                "teacher_task1_ta": "6",
                "teacher_task1_cc": "6",
                "teacher_task1_lr": "6",
                "teacher_task1_gra": "7",
                "teacher_task2_tr": "7",
                "teacher_task2_cc": "7",
                "teacher_task2_lr": "7",
                "teacher_task2_gra": "6",
                "teacher_comment": "Teacher-only comment.",
            },
        )
        self._login(name="Ada Student", code="ADA01")
        student_page = self.client.get("/me").get_data(as_text=True)
        self._assert_hidden_teacher_fields(student_page, "Teacher-only comment.")
        payload = self.client.get(f"/api/me/submission/{ada_sid}").get_json()
        raw = self.client.get(f"/api/me/submission/{ada_sid}").get_data(as_text=True)
        for key in (
            "teacher_task1_ta",
            "teacher_task2_tr",
            "teacher_comment",
            "official_score",
        ):
            self.assertNotIn(key, payload)
            self.assertNotIn(key, raw)
        self.assertNotIn("Teacher-only comment.", raw)

        # Even a logged-in admin cannot attach another student's paper to the wrong code.
        wrong = admin.get(f"/admin/records/{bob['id']}/submission/{ada_sid}")
        self.assertEqual(wrong.status_code, 404)
        missing = admin.get("/admin/records/does-not-exist")
        self.assertEqual(missing.status_code, 404)
        self.assertIn("未找到该邀请码", missing.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
