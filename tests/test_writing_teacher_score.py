#!/usr/bin/env python3
"""Official Academic Writing teacher criteria: rounding, weighting, validation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import student_portal as sp  # noqa: E402


class WritingAverageRoundingTests(unittest.TestCase):
    def test_official_boundaries(self):
        self.assertEqual(sp.round_ielts_writing_average(6.0), 6.0)
        self.assertEqual(sp.round_ielts_writing_average(6.24), 6.0)
        self.assertEqual(sp.round_ielts_writing_average(6.25), 6.5)
        self.assertEqual(sp.round_ielts_writing_average(6.5), 6.5)
        self.assertEqual(sp.round_ielts_writing_average(6.74), 6.5)
        self.assertEqual(sp.round_ielts_writing_average(6.75), 7.0)
        self.assertEqual(sp.round_ielts_writing_average(6.875), 7.0)
        self.assertEqual(sp.round_ielts_writing_average(7.0), 7.0)

    def test_task_mean_examples(self):
        # 6, 6, 6, 7 → 6.25 → 6.5
        self.assertEqual(sp.task_band_from_criteria([6, 6, 6, 7]), 6.5)
        # 7, 7, 7, 6 → 6.75 → 7.0
        self.assertEqual(sp.task_band_from_criteria([7, 7, 7, 6]), 7.0)
        self.assertEqual(sp.task_band_from_criteria([6, 6, 6, 6]), 6.0)
        self.assertEqual(sp.task_band_from_criteria([6, 6, 6.5, 6.5]), 6.5)
        self.assertIsNone(sp.task_band_from_criteria([6, 6, 6]))
        self.assertIsNone(sp.task_band_from_criteria([6, 6, 6, None]))


class WritingOverallWeightingTests(unittest.TestCase):
    def test_full_paper_double_weights_task2(self):
        # Task 1 6.5, Task 2 7.0 → (6.5 + 14) / 3 = 6.833... → 7.0
        self.assertEqual(sp.overall_band_from_tasks(6.5, 7.0, "full"), 7.0)
        self.assertEqual(sp.overall_band_from_tasks(6.0, 6.0, "full"), 6.0)
        # 6.0 + 2*6.5 = 19 / 3 = 6.333... → 6.5
        self.assertEqual(sp.overall_band_from_tasks(6.0, 6.5, "full"), 6.5)
        # 7.0 + 2*6.0 = 19 / 3 = 6.333... → 6.5
        self.assertEqual(sp.overall_band_from_tasks(7.0, 6.0, "full"), 6.5)
        self.assertIsNone(sp.overall_band_from_tasks(6.5, None, "full"))
        self.assertIsNone(sp.overall_band_from_tasks(None, 7.0, "full"))

    def test_single_task_modes_use_that_task_band(self):
        self.assertEqual(sp.overall_band_from_tasks(6.5, 9.0, "task1"), 6.5)
        self.assertEqual(sp.overall_band_from_tasks(9.0, 5.5, "task2"), 5.5)
        self.assertIsNone(sp.overall_band_from_tasks(None, 7.0, "task1"))
        self.assertIsNone(sp.overall_band_from_tasks(7.0, None, "task2"))


class ResolveTeacherWritingScoreTests(unittest.TestCase):
    def test_computes_task_and_overall_from_complete_criteria(self):
        result = sp.resolve_teacher_writing_score(
            {
                "teacher_task1_ta": "6",
                "teacher_task1_cc": "6",
                "teacher_task1_lr": "6",
                "teacher_task1_gra": "7",
                "teacher_task2_tr": "7",
                "teacher_task2_cc": "7",
                "teacher_task2_lr": "7",
                "teacher_task2_gra": "6",
                "teacher_band": "5",
                "teacher_comment": "Clear argument.",
            },
            mode="full",
        )
        fields = result["fields"]
        self.assertEqual(fields["teacher_task1_band"], 6.5)
        self.assertEqual(fields["teacher_task2_band"], 7.0)
        self.assertEqual(fields["teacher_band"], 7.0)
        self.assertEqual(fields["teacher_task1_ta"], 6.0)
        self.assertEqual(fields["teacher_task2_tr"], 7.0)
        self.assertTrue(result["computed_overall"])
        self.assertTrue(result["overall_replaced"])
        self.assertEqual(fields["teacher_comment"], "Clear argument.")
        message = sp.teacher_writing_score_flash(result)
        self.assertIn("已保存写作评分：7。", message)
        self.assertIn("未采用手填总分 5。", message)

    def test_overall_only_without_task_bands_stays_manual(self):
        result = sp.resolve_teacher_writing_score(
            {"teacher_band": "6.5", "teacher_comment": "Overall only."},
            mode="full",
        )
        fields = result["fields"]
        self.assertEqual(fields["teacher_band"], 6.5)
        self.assertIsNone(fields["teacher_task1_band"])
        self.assertIsNone(fields["teacher_task2_band"])
        self.assertFalse(result["computed_overall"])
        self.assertEqual(
            sp.teacher_writing_score_flash(result),
            "已保存写作评分：6.5。",
        )

    def test_overall_only_remains_valid(self):
        result = sp.resolve_teacher_writing_score(
            {
                "teacher_band": "6.5",
                "teacher_task1_band": "6",
                "teacher_task2_band": "7",
                "teacher_comment": "Task 2 is stronger.",
            },
            mode="full",
        )
        fields = result["fields"]
        self.assertEqual(fields["teacher_band"], 6.5)
        self.assertEqual(fields["teacher_task1_band"], 6.0)
        self.assertEqual(fields["teacher_task2_band"], 7.0)
        self.assertIsNone(fields["teacher_task1_ta"])
        self.assertIsNone(fields["teacher_task2_tr"])
        # Manual task bands still produce an official overall when both exist.
        self.assertTrue(result["computed_overall"])
        self.assertFalse(result["overall_replaced"])
        self.assertFalse(result["computed_task1"])
        self.assertFalse(result["computed_task2"])
        self.assertEqual(
            sp.teacher_writing_score_flash(result),
            "已保存写作评分：6.5。已按官方规则计算总分。",
        )

    def test_rejects_partial_criteria(self):
        with self.assertRaises(ValueError) as ctx:
            sp.resolve_teacher_writing_score(
                {
                    "teacher_band": "7",
                    "teacher_task1_ta": "6",
                    "teacher_task1_cc": "6",
                    "teacher_task1_lr": "6",
                },
                mode="full",
            )
        self.assertIn("Task 1 请填齐四项", str(ctx.exception))
        self.assertIn("TA、CC、LR、GRA", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            sp.resolve_teacher_writing_score(
                {
                    "teacher_band": "7",
                    "teacher_task2_tr": "7",
                    "teacher_task2_cc": "7",
                },
                mode="full",
            )
        self.assertIn("Task 2 请填齐四项", str(ctx.exception))
        self.assertIn("TR、CC、LR、GRA", str(ctx.exception))

    def test_task1_only_overall_equals_task1_band(self):
        result = sp.resolve_teacher_writing_score(
            {
                "teacher_task1_ta": "5.5",
                "teacher_task1_cc": "6",
                "teacher_task1_lr": "6",
                "teacher_task1_gra": "6.5",
            },
            mode="task1",
        )
        fields = result["fields"]
        self.assertEqual(fields["teacher_task1_band"], 6.0)
        self.assertEqual(fields["teacher_band"], 6.0)
        self.assertIsNone(fields["teacher_task2_band"])
        self.assertTrue(result["computed_overall"])

    def test_task2_only_overall_equals_task2_band(self):
        result = sp.resolve_teacher_writing_score(
            {
                "teacher_task2_tr": "7",
                "teacher_task2_cc": "6.5",
                "teacher_task2_lr": "7",
                "teacher_task2_gra": "6.5",
            },
            mode="task2",
        )
        fields = result["fields"]
        self.assertEqual(fields["teacher_task2_band"], 7.0)  # 28/4 = 7
        self.assertEqual(fields["teacher_band"], 7.0)

    def test_full_paper_with_only_one_task_requires_manual_overall(self):
        with self.assertRaises(ValueError) as ctx:
            sp.resolve_teacher_writing_score(
                {
                    "teacher_task1_ta": "6",
                    "teacher_task1_cc": "6",
                    "teacher_task1_lr": "6",
                    "teacher_task1_gra": "6",
                },
                mode="full",
            )
        self.assertIn("请填写总分", str(ctx.exception))

        result = sp.resolve_teacher_writing_score(
            {
                "teacher_band": "6.5",
                "teacher_task1_ta": "6",
                "teacher_task1_cc": "6",
                "teacher_task1_lr": "6",
                "teacher_task1_gra": "6",
            },
            mode="full",
        )
        fields = result["fields"]
        self.assertEqual(fields["teacher_task1_band"], 6.0)
        self.assertEqual(fields["teacher_band"], 6.5)
        self.assertFalse(result["computed_overall"])

    def test_invalid_criterion_is_rejected(self):
        with self.assertRaises(ValueError):
            sp.resolve_teacher_writing_score(
                {
                    "teacher_task1_ta": "6.25",
                    "teacher_task1_cc": "6",
                    "teacher_task1_lr": "6",
                    "teacher_task1_gra": "6",
                    "teacher_band": "6",
                },
                mode="task1",
            )

    def test_form_context_loads_legacy_and_criteria_records(self):
        legacy = sp.teacher_writing_form_context(
            {"mode": "full", "teacher_band": 6.5, "teacher_task1_band": 6, "teacher_task2_band": 7}
        )
        self.assertEqual(legacy["overall"], 6.5)
        self.assertEqual(legacy["header_task1"], "6")
        self.assertEqual(legacy["header_task2"], "7")
        self.assertEqual(legacy["task1_criteria"][0]["value_label"], "")
        self.assertTrue(legacy["show_task1"])
        self.assertTrue(legacy["show_task2"])

        scored = sp.teacher_writing_form_context(
            {
                "mode": "full",
                "teacher_band": 7.0,
                "teacher_task1_band": 6.5,
                "teacher_task2_band": 7.0,
                "teacher_task1_ta": 6,
                "teacher_task1_cc": 6,
                "teacher_task1_lr": 6,
                "teacher_task1_gra": 7,
                "teacher_task2_tr": 7,
                "teacher_task2_cc": 7,
                "teacher_task2_lr": 7,
                "teacher_task2_gra": 6,
            }
        )
        self.assertEqual(scored["header_task1"], "6.5（TA 6 · CC 6 · LR 6 · GRA 7）")
        self.assertEqual(scored["header_task2"], "7（TR 7 · CC 7 · LR 7 · GRA 6）")

        task1_only = sp.teacher_writing_form_context({"mode": "task1", "teacher_band": 6})
        self.assertTrue(task1_only["show_task1"])
        self.assertFalse(task1_only["show_task2"])


if __name__ == "__main__":
    unittest.main()
