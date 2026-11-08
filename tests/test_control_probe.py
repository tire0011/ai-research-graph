import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import benchmark_probe as bp
import control_probe as cp


def entry(step, score, task, metric, row_idx):
    return {
        "row_idx": row_idx,
        "source_file": "scores.parquet",
        "source_file_row_idx": row_idx,
        "row": {
            "model": bp.MODEL, "task": task, "metric": metric,
            "step": float(step), "score": score,
            "task_config": {"task": task}, "num_fewshot": 0,
            "eval_suite": "suite", "n_samples": 7983 if task == "coqa_gen" else 100,
        },
    }


def source(rows):
    return {"rows": rows, "scan_truncated": False,
            "revision_sha": "f" * 40, "last_modified": "today",
            "source_files": [{"path": "scores.parquet"}]}


class ControlTests(unittest.TestCase):
    def test_matched_checkpoint_control_deltas(self):
        rows = []
        for task, metric, scores in [
            ("coqa_gen", "f1", [.320, .745, .507]),
            ("coqa_mc", "acc", [.856, .861, .847]),
            ("squad_gen", "f1", [.901, .905, .899]),
        ]:
            for step, score in zip([1092000, 1094400, 1096800], scores):
                rows.append(entry(step, score, task, metric, len(rows)))
        result = cp.compare_controls(source(rows))
        self.assertEqual(result["status"], "comparable")
        aligned = result["aligned"]
        self.assertEqual(aligned["common_checkpoints"], 3)
        self.assertEqual(aligned["coqa_peak_pair"], [1092000, 1094400])
        self.assertAlmostEqual(
            aligned["controls_at_coqa_peak"]["coqa_mc_acc"]["delta"], .005)
        self.assertAlmostEqual(
            aligned["series"]["coqa_gen_f1"]["median_absolute_delta"], .3315)
        self.assertAlmostEqual(
            aligned["series"]["squad_gen_f1"]["median_absolute_delta"], .005)

    def test_only_shared_steps_are_compared(self):
        rows = []
        for task, metric, values in [
            ("coqa_gen", "f1", [(10, .1), (20, .8), (30, .7)]),
            ("coqa_mc", "acc", [(10, .5), (30, .6)]),
            ("squad_gen", "f1", [(10, .8), (30, .9)]),
        ]:
            for step, score in values:
                rows.append(entry(step, score, task, metric, len(rows)))
        aligned = cp.compare_controls(source(rows))["aligned"]
        self.assertEqual(aligned["common_steps"], [10, 30])
        self.assertAlmostEqual(aligned["series"]["coqa_gen_f1"]["median_absolute_delta"], .6)

    def test_quality_issue_blocks_cross_task_inference(self):
        rows = []
        for task, metric in [("coqa_gen", "f1"), ("coqa_mc", "acc"), ("squad_gen", "f1")]:
            rows.extend([entry(10, .4, task, metric, len(rows)),
                         entry(20, .5, task, metric, len(rows) + 1)])
        rows[3]["row"]["task_config"] = {"changed": True}
        result = cp.compare_controls(source(rows))
        self.assertEqual(result["status"], "quality_blocked")
        self.assertIsNone(result["aligned"])
        self.assertIn("inconsistent_task_config",
                      result["profiles"]["coqa_mc_acc"]["problems"])

    def test_missing_control_blocks_inference(self):
        rows = [entry(10, .1, "coqa_gen", "f1", 0),
                entry(20, .2, "coqa_gen", "f1", 1)]
        result = cp.compare_controls(source(rows))
        self.assertEqual(result["status"], "quality_blocked")
        self.assertEqual(result["profiles"]["squad_gen_f1"]["status"], "insufficient_rows")

    def test_source_failure_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            last_good = Path(folder) / "PRELUDE_CONTROLS.md"
            last_good.write_text("last known good\n")
            with patch.object(cp, "parquet_scores", side_effect=ValueError("offline")):
                self.assertEqual(cp.main(["--output", folder]), 1)
            payload = json.loads((Path(folder) / "prelude_controls_error.json").read_text())
            self.assertEqual(payload["status"], "source_error")
            self.assertIn("No scientific comparison", (Path(folder) / "PRELUDE_CONTROLS_ERROR.md").read_text())
            self.assertEqual(last_good.read_text(), "last known good\n")
            self.assertFalse((Path(folder) / "prelude_controls.json").exists())


if __name__ == "__main__":
    unittest.main()
