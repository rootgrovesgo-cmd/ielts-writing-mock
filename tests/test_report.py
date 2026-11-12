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
import reading_review as rr  # noqa: E402
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

    def _submit_reading(self, name="HE", answers=None, part_times=None, highlights=None):
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
        if highlights is not None:
            payload["highlights"] = highlights
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
        self.assertIn("篇章信息", text)
        self.assertIn("Saving the addax", text)
        self.assertIn("The problems of getting around the city of Ibadan", text)
        self.assertIn("Rethinking Early Cities", text)
        self.assertIn("题材", text)
        self.assertIn("文章类型", text)
        self.assertIn("结构类型", text)
        self.assertIn("撒哈拉濒危羚羊", text)
        self.assertIn("说明文（自然保护", text)
        self.assertIn("问题－解决", text)
        self.assertIn("伊巴丹", text)
        self.assertIn("城市交通", text)
        self.assertIn("早期城市", text)
        self.assertIn("议论文", text)
        self.assertIn("论证型", text)
        self.assertIn("用时 10min0s", text)
        self.assertIn("用时 13min20s", text)
        self.assertIn("用时 13min48s", text)
        self.assertIn("高亮与扫跳评述", text)
        self.assertIn("未保存高亮记录", text)
        self.assertIn("扫读与跳读", text)

        self.assertIn("37min8s", html)
        self.assertIn("22min52s", html)
        self.assertNotIn("2228s", html)
        self.assertNotIn("1372s", html)
        self.assertIn("各部分用时", html)
        self.assertIn("Passage 1 10min0s", html)
        self.assertIn("Passage 2 13min20s", html)
        self.assertIn("Passage 3 13min48s", html)
        self.assertIn("篇章信息", html)
        self.assertIn("Saving the addax", html)
        self.assertIn("高亮与扫跳评述", html)
        self.assertIn("未保存高亮记录", html)
        self.assertNotIn("<mark", html)

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
        self.assertNotIn("各部分用时", html)
        self.assertNotIn("篇章信息", html)
        self.assertNotIn("高亮与扫跳评述", html)

        self.assertNotIn("各部分用时", text)
        self.assertNotIn("篇章信息", text)
        self.assertNotIn("高亮与扫跳评述", text)

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
        self.assertIn("各部分用时", html)
        self.assertIn("本题卷未记录各部分用时", html)
        self.assertNotIn("Passage 1 10min0s", html)
        self.assertNotIn("2228s", html)

        res = self.client.get(f"/admin/submission/{sid}/report.pdf")
        self.assertEqual(res.status_code, 200)
        text = self._pdf_text(res.get_data())
        self.assertIn("37min8s", text)
        self.assertIn("各部分用时", text)
        self.assertIn("本题卷未记录各部分用时", text)
        self.assertIn("本题卷未记录", text)
        self.assertNotIn("Passage 1 10min0s", text)
        self.assertNotIn("2228s", text)
        self.assertIn("篇章信息", text)
        self.assertIn("Saving the addax", text)


    def _mark(self, text):
        return f'<mark class="hl">{text}</mark>'

    def _passage_html(self, passage_id, spans):
        paper = rs.load_paper()
        paragraphs = []
        for item in paper["passages"]:
            if str(item["id"]) == str(passage_id):
                paragraphs = list(item["paragraphs"])
                break
        html_parts = []
        remaining = list(spans)
        for para in paragraphs:
            rendered = para
            still = []
            for span in remaining:
                if span in rendered:
                    rendered = rendered.replace(span, self._mark(span), 1)
                else:
                    still.append(span)
            remaining = still
            html_parts.append(f"<p>{rendered}</p>")
        self.assertFalse(remaining, f"spans not found in passage {passage_id}: {remaining}")
        return "".join(html_parts)

    def test_format_duration_and_part_times_helpers(self):
        self.assertTrue(rr.part_times_recorded({"1": 0, "2": 0, "3": 0}))
        self.assertFalse(rr.part_times_recorded(None))
        self.assertFalse(rr.part_times_recorded({}))
        self.assertEqual(rr.part_time_seconds({"1": 600, "2": 800, "3": 828}, "2"), 800)
        self.assertIsNone(rr.part_time_seconds(None, "1"))

    def test_highlight_parser_ignores_script_and_extracts_marks(self):
        html = (
            "<p>Hello <mark class=\"hl\">Niger</mark>"
            "<script>alert(1)</script>"
            "<mark class=\"hl has-note\">ninety per cent"
            "<span class=\"note-dot\"></span></mark></p>"
        )
        marks = rr.extract_highlight_marks(html)
        self.assertEqual(marks, ["Niger", "ninety per cent"])
        self.assertNotIn("alert", " ".join(marks))

    def test_highlight_review_without_highlights_skips_diagnosis(self):
        review = rr.highlight_review({"module": "reading", "prompt_set_id": "set-a", "mode": "full"})
        self.assertFalse(review["has_highlights"])
        self.assertIn("未保存高亮记录", review["text"])
        self.assertNotIn("呈现出扫读与跳读结合", review["text"])

    def test_highlight_review_balanced_skim_and_scan(self):
        paper = rs.load_paper()
        p1 = paper["passages"][0]["paragraphs"]
        p2 = paper["passages"][1]["paragraphs"]
        p3 = paper["passages"][2]["paragraphs"]
        highlights = {
            "passage": {
                "1": self._passage_html(
                    "1",
                    [
                        p1[0].split(". ")[0] + ".",
                        "Niger",
                        "well over ninety per cent",
                    ],
                ),
                "2": self._passage_html(
                    "2",
                    [
                        p2[0].split(". ")[0] + ".",
                        "okada",
                        "eight million",
                    ],
                ),
                "3": self._passage_html(
                    "3",
                    [
                        p3[0].split(". ")[0] + ".",
                        "Palace-First",
                        "Tell Sefira",
                    ],
                ),
            },
            "questions": f"<p>Look at {self._mark('Adedayo Okunola')} and {self._mark('Ain Tazaght')}.</p>",
        }
        review = rr.highlight_review(
            {
                "module": "reading",
                "prompt_set_id": "set-a",
                "mode": "full",
                "highlights": highlights,
            }
        )
        self.assertTrue(review["has_highlights"])
        self.assertTrue(review["both"])
        self.assertIn("扫读与跳读结合", review["text"])
        self.assertIn("Passage 1", review["text"])
        self.assertIn("题干中另有 2 处标注", review["text"])
        self.assertNotIn("<script", review["text"])
        self.assertNotIn("<mark", review["text"])

    def test_highlight_review_dense_and_concentrated(self):
        paper = rs.load_paper()
        almost_all = paper["passages"][0]["paragraphs"]
        highlights = {
            "passage": {
                "1": "".join(f"<p>{self._mark(para)}</p>" for para in almost_all),
                "2": "<p>Ibadan is large.</p>",
                "3": "<p>Cities changed.</p>",
            }
        }
        review = rr.highlight_review(
            {
                "module": "reading",
                "prompt_set_id": "set-a",
                "mode": "full",
                "highlights": highlights,
            }
        )
        self.assertTrue(review["dense"])
        self.assertTrue(review["concentrated"])
        self.assertIn("高亮过密", review["text"])
        self.assertIn("集中在 Passage 1", review["text"])

    def test_highlight_review_almost_none(self):
        highlights = {"passage": {"1": f"<p>Today the wild population is in {self._mark('Niger')}.</p>"}}
        review = rr.highlight_review(
            {
                "module": "reading",
                "prompt_set_id": "set-a",
                "mode": "full",
                "highlights": highlights,
            }
        )
        self.assertTrue(review["sparse"])
        self.assertIn("极为稀疏", review["text"])
        self.assertNotIn("呈现出扫读与跳读结合", review["text"])

    def test_pdf_and_admin_include_highlight_analysis(self):
        paper = rs.load_paper()
        p1 = paper["passages"][0]["paragraphs"][0]
        first = p1.split(". ")[0] + "."
        highlights = {
            "passage": {
                "1": self._passage_html("1", [first, "Niger", "well over ninety per cent"]),
                "2": self._passage_html(
                    "2",
                    [
                        paper["passages"][1]["paragraphs"][0].split(". ")[0] + ".",
                        "okada",
                    ],
                ),
                "3": self._passage_html(
                    "3",
                    [
                        paper["passages"][2]["paragraphs"][0].split(". ")[0] + ".",
                        "Tell Sefira",
                    ],
                ),
            },
            "questions": (
                f"<p>{self._mark('Adedayo Okunola')}</p>"
                "<script>alert(document.cookie)</script>"
                "<img src=x onerror=alert(1) />"
            ),
        }
        self._set_admin()
        self._create_code()
        started = self._start(name="HE")
        self.assertEqual(started.status_code, 200)
        sid = self._submit_reading(name="HE", highlights=highlights)

        self._login_admin()
        detail = self.client.get(f"/admin/submission/{sid}")
        self.assertEqual(detail.status_code, 200)
        html = detail.get_data(as_text=True)
        self.assertIn("高亮与扫跳评述", html)
        self.assertIn("扫读与跳读结合", html)
        self.assertIn("各部分用时", html)
        self.assertIn("Passage 1 10min0s", html)
        self.assertNotIn("alert(document.cookie)", html)
        self.assertNotIn("onerror=alert", html)
        self.assertNotIn("<script>alert", html)

        res = self.client.get(f"/admin/submission/{sid}/report.pdf")
        self.assertEqual(res.status_code, 200)
        text = self._pdf_text(res.get_data())
        self.assertIn("高亮与扫跳评述", text)
        self.assertIn("扫读与跳读结合", text)
        self.assertIn("篇章信息", text)
        self.assertIn("问题－解决", text)
        self.assertIn("论证型", text)
        self.assertIn("Passage 1 10min0s", text)
        self.assertNotIn("alert(document.cookie)", text)
        self.assertNotIn("未保存高亮记录", text)

    def test_missing_submission_is_404_for_admin(self):
        self._set_admin()
        self._login_admin()
        res = self.client.get("/admin/submission/does-not-exist/report.pdf")
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
