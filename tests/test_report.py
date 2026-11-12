#!/usr/bin/env python3
"""Teacher-only PDF answer report tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from shutil import which

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import access as accessmod  # noqa: E402
import app as appmod  # noqa: E402
import report_pdf  # noqa: E402
import reading_scoring as rs  # noqa: E402

TEST_ADMIN_USER = "TestAdmin"
TEST_ADMIN_PASS = "test-access-pass-9f3c"
ADMIN_ENV = (
    "IELTS_ADMIN_USERNAME",
    "IELTS_ADMIN_PASSWORD",
    "IELTS_ADMIN_PASSWORD_HASH",
)


class ReportPdfTests(unittest.TestCase):
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
        appmod.app.config["SECRET_KEY"] = "test-secret-report"
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

    def _set_admin(self, user=TEST_ADMIN_USER, password=TEST_ADMIN_PASS):
        self._clear_admin_env()
        os.environ["IELTS_ADMIN_USERNAME"] = user
        os.environ["IELTS_ADMIN_PASSWORD"] = password

    def _login_admin(self):
        return self.client.post(
            "/admin/login",
            data={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASS},
        )

    def _create_code(self, code="TESTCODE1", note="小何"):
        return accessmod.create_code(code=code, note=note)

    def _start(self, name="HE", code="TESTCODE1", module="reading", mode="full"):
        return self.client.post(
            "/api/session/start",
            json={
                "candidate_name": name,
                "invite_code": code,
                "module": module,
                "mode": mode,
            },
        )

    def _submit_reading(self, name="HE", answers=None, part_times=None):
        payload_answers = {str(q): a for q, a in rs.official_answers().items()}
        if answers is not None:
            payload_answers = answers
        payload = {
            "candidate_name": name,
            "mode": "full",
            "prompt_set_id": "set-a",
            "answers": payload_answers,
            "duration_seconds": 3600,
            "time_remaining_seconds": 1372,
            "time_used_seconds": 2228,
            "paused_total_seconds": 0,
            "auto_submitted": False,
        }
        if part_times is not None:
            payload["part_times"] = part_times
        else:
            payload["part_times"] = {"1": 600, "2": 800, "3": 828}
        res = self.client.post(
            "/api/reading/submit",
            json=payload,
        )
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        return res.get_json()["id"]

    def _submit_writing(self, name="Writer"):
        res = self.client.post(
            "/api/submit",
            json={
                "candidate_name": name,
                "mode": "task1",
                "prompt_set_id": "set-a",
                "task1_text": "This is a short writing sample about a chart.",
                "task2_text": "",
                "duration_seconds": 1200,
                "time_remaining_seconds": 10,
                "time_used_seconds": 1190,
            },
        )
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        return res.get_json()["id"]

    def _pdf_text(self, data: bytes) -> str:
        pdftotext = which("pdftotext")
        if not pdftotext:
            self.fail("pdftotext (poppler-utils) is required to verify PDF text")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as fh:
            fh.write(data)
            path = fh.name
        try:
            return subprocess.check_output(
                [pdftotext, "-layout", path, "-"],
                text=True,
            )
        finally:
            Path(path).unlink(missing_ok=True)

    def test_format_duration(self):
        self.assertEqual(report_pdf.format_duration(None), "—")
        self.assertEqual(report_pdf.format_duration(0), "0s")
        self.assertEqual(report_pdf.format_duration(12), "12s")
        self.assertEqual(report_pdf.format_duration(59), "59s")
        self.assertEqual(report_pdf.format_duration(60), "1min0s")
        self.assertEqual(report_pdf.format_duration(72), "1min12s")
        self.assertEqual(report_pdf.format_duration(2228), "37min8s")
        self.assertEqual(report_pdf.format_duration(1372), "22min52s")
        self.assertEqual(report_pdf.format_duration(3480), "58min0s")
        self.assertEqual(
            report_pdf.part_times_summary({"1": 600, "2": 800, "3": 828}),
            "Passage 1 10min0s · Passage 2 13min20s · Passage 3 13min48s",
        )
        self.assertIsNone(report_pdf.part_times_summary(None))
        self.assertIsNone(report_pdf.part_times_summary({}))

    def test_filename_pattern(self):
        name = report_pdf.report_filename(
            {
                "module": "reading",
                "candidate_name": "HE",
                "timestamp": "2026-11-12T16:43:06+08:00",
            }
        )
        self.assertEqual(name, "reading-HE-20261112-report.pdf")
        chinese = report_pdf.report_filename(
            {
                "module": "reading",
                "candidate_name": "小何",
                "timestamp": "2026-11-12T16:43:06+08:00",
            }
        )
        self.assertEqual(chinese, "reading-小何-20261112-report.pdf")

    def test_unauthenticated_request_is_rejected(self):
        self._create_code()
        started = self._start()
        self.assertEqual(started.status_code, 200)
        sid = self._submit_reading()
        res = self.client.get(f"/admin/submission/{sid}/report.pdf")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/admin/login", res.headers.get("Location", ""))

    def test_student_cannot_download_report(self):
        self._create_code()
        started = self._start()
        self.assertEqual(started.status_code, 200)
        sid = self._submit_reading()
        # Same student session, no admin login.
        res = self.client.get(f"/admin/submission/{sid}/report.pdf")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/admin/login", res.headers.get("Location", ""))
        self.assertFalse((res.headers.get("Content-Type") or "").startswith("application/pdf"))

    def test_admin_can_download_reading_report(self):
        self._set_admin()
        self._create_code()
        started = self._start(name="HE")
        self.assertEqual(started.status_code, 200)
        answers = {str(q): a for q, a in rs.official_answers().items()}
        answers["1"] = "wrong"
        sid = self._submit_reading(name="HE", answers=answers)

        self._login_admin()
        detail = self.client.get(f"/admin/submission/{sid}")
        self.assertEqual(detail.status_code, 200)
        html = detail.get_data(as_text=True)
        self.assertIn("逐题批改", html)
        self.assertIn("下载 PDF 报告", html)
        self.assertIn(f"/admin/submission/{sid}/report.pdf", html)

        res = self.client.get(f"/admin/submission/{sid}/report.pdf")
        self.assertEqual(res.status_code, 200)
        self.assertTrue((res.headers.get("Content-Type") or "").startswith("application/pdf"))
        disposition = res.headers.get("Content-Disposition", "")
        self.assertIn("attachment", disposition)
        self.assertIn("reading-HE-", disposition)
        self.assertIn("-report.pdf", disposition)

        data = res.get_data()
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertIn(b"/FontFile2", data)
        self.assertGreater(len(data), 2000)

        text = self._pdf_text(data)
        self.assertIn("Rosette Exclusive Mock Exam", text)
        self.assertIn("答题报告", text)
        self.assertIn("HE", text)
        saved = json.loads((appmod.SUBMISSIONS_DIR / f"{sid}.json").read_text(encoding="utf-8"))
        self.assertIn(f"{saved['score']}/{saved['total']}", text)
        self.assertGreaterEqual(saved["total"] or 0, 1)
        self.assertIn("正确", text)
        self.assertIn("错误", text)
        self.assertIn("sand", text)
        self.assertIn("题号", text)
        self.assertIn("学生作答", text)
        self.assertIn("标准答案", text)
        self.assertIn("仅供教师使用", text)
        # Bundled CJK font must actually paint Chinese, not tofu.
        self.assertIn("考生", text)
        self.assertIn("阅读", text)
        self.assertIn("逐题批改", text)
        self.assertIn("生成时间", text)
        self.assertIn("37min8s", text)
        self.assertIn("22min52s", text)
        self.assertIn("暂停累计 0s", text)
        self.assertNotIn("2228s", text)
        self.assertNotIn("1372s", text)
        self.assertIn("各部分用时", text)
        self.assertIn("Passage 1 10min0s", text)
        self.assertIn("Passage 2 13min20s", text)
        self.assertIn("Passage 3 13min48s", text)

        self.assertIn("37min8s", html)
        self.assertIn("22min52s", html)
        self.assertNotIn("2228s", html)
        self.assertNotIn("1372s", html)
        self.assertIn("各部分用时", html)
        self.assertIn("Passage 1 10min0s", html)

    def test_writing_report_has_metadata_and_essay_only(self):
        self._set_admin()
        self._create_code()
        started = self._start(name="Writer", module="writing", mode="task1")
        self.assertEqual(started.status_code, 200)
        sid = self._submit_writing(name="Writer")

        self._login_admin()
        detail = self.client.get(f"/admin/submission/{sid}")
        self.assertEqual(detail.status_code, 200)
        html = detail.get_data(as_text=True)
        self.assertNotIn("逐题批改", html)
        self.assertIn("下载 PDF 报告", html)

        res = self.client.get(f"/admin/submission/{sid}/report.pdf")
        self.assertEqual(res.status_code, 200)
        data = res.get_data()
        self.assertTrue(data.startswith(b"%PDF"))
        text = self._pdf_text(data)
        self.assertIn("Writer", text)
        self.assertIn("写作", text)
        self.assertIn("This is a short writing sample about a chart.", text)
        self.assertIn("Task 1", text)
        self.assertNotIn("逐题批改", text)
        self.assertIn("19min50s", text)
        self.assertIn("10s", text)
        self.assertNotIn("1190s", text)

        self.assertIn("19min50s", html)
        self.assertNotIn("1190s", html)

    def test_old_reading_submission_without_part_times_still_renders(self):
        self._set_admin()
        self._create_code()
        started = self._start()
        self.assertEqual(started.status_code, 200)
        sid = self._submit_reading()
        path = appmod.SUBMISSIONS_DIR / f"{sid}.json"
        saved = json.loads(path.read_text(encoding="utf-8"))
        saved.pop("part_times", None)
        path.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")

        self._login_admin()
        detail = self.client.get(f"/admin/submission/{sid}")
        self.assertEqual(detail.status_code, 200)
        html = detail.get_data(as_text=True)
        self.assertIn("37min8s", html)
        self.assertNotIn("各部分用时", html)
        self.assertNotIn("2228s", html)

        res = self.client.get(f"/admin/submission/{sid}/report.pdf")
        self.assertEqual(res.status_code, 200)
        text = self._pdf_text(res.get_data())
        self.assertIn("37min8s", text)
        self.assertNotIn("各部分用时", text)
        self.assertNotIn("2228s", text)

    def test_missing_submission_is_404_for_admin(self):
        self._set_admin()
        self._login_admin()
        res = self.client.get("/admin/submission/does-not-exist/report.pdf")
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
