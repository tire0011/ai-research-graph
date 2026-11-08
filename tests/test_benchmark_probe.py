import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import benchmark_probe as bp


def row(step, score, index=0, **changes):
    data = {
        "step": step, "score": score, "model": bp.MODEL,
        "task": bp.TASK, "metric": bp.METRIC,
        "task_config": {"output_type": "generate_until"},
        "num_fewshot": 0, "eval_suite": "base",
    }
    data.update(changes)
    return {"row_idx": index, "row": data}


def source(rows, **changes):
    data = {
        "rows": rows, "scan_truncated": False,
        "model": bp.MODEL, "task": bp.TASK, "metric": bp.METRIC,
    }
    data.update(changes)
    return data


class ScoreTests(unittest.TestCase):
    def test_checkpoint_step_parser(self):
        self.assertEqual(bp.step_number("iter_1,092,000"), 1092000)
        self.assertEqual(bp.step_number(1094400), 1094400)
        self.assertEqual(bp.step_number(1094400.0), 1094400)
        self.assertEqual(bp.step_number("1,094,400.0"), 1094400)
        self.assertIsNone(bp.step_number("main"))
        self.assertIsNone(bp.step_number(None))
        self.assertIsNone(bp.step_number(10.1))

    def test_adjacent_changes_only_within_one_group(self):
        records = [
            row(1092000, 0.320, 0), row(1094400, 0.745, 1),
            row(1096800, 0.507, 2), row(1099200, 0.733, 3),
        ]
        profile = bp.assess_scores(source(records))
        self.assertEqual(profile["status"], "comparable")
        self.assertEqual(profile["comparisons"]["adjacent_pairs"], 3)
        self.assertAlmostEqual(profile["comparisons"]["median_absolute_delta"], .238)
        self.assertAlmostEqual(profile["comparisons"]["largest_absolute_delta"], .425)
        self.assertEqual(profile["comparisons"]["largest_change"]["from_step"], 1092000)

    def test_duplicate_checkpoint_blocks_comparison(self):
        profile = bp.assess_scores(source([row(10, .2), row(10, .4, 1)]))
        self.assertEqual(profile["status"], "quality_blocked")
        self.assertIn("duplicate_checkpoint_steps", profile["problems"])

    def test_eval_config_difference_blocks_comparison(self):
        profile = bp.assess_scores(source([
            row(10, .2), row(20, .4, 1, task_config={"different": True}),
        ]))
        self.assertIn("inconsistent_task_config", profile["problems"])
        self.assertIsNone(profile["comparisons"])

    def test_invalid_score_blocks_comparison(self):
        profile = bp.assess_scores(source([row(10, .2), row(20, None, 1)]))
        self.assertEqual(profile["invalid_row_indices"], [1])
        self.assertIn("invalid_or_missing_scores", profile["problems"])

    def test_other_task_blocks_comparison(self):
        profile = bp.assess_scores(source([row(10, .2), row(20, .4, 1, task="other")]))
        self.assertIn("unexpected_model_task_metric", profile["problems"])

    def test_truncation_blocks_comparison(self):
        profile = bp.assess_scores(source([row(10, .2), row(20, .4, 1)],
                                          scan_truncated=True))
        self.assertIn("source_filter_limit_reached", profile["problems"])


class SourceTests(unittest.TestCase):
    def test_pinned_parquet_source_records_file_provenance(self):
        fixture = [
            row(10, .2)["row"],
            row(15, .5, model="unrelated")["row"],
            row(20, .4)["row"],
        ]

        class Table:
            def __init__(self, records):
                self.records = records

            def to_pydict(self):
                return {name: [r.get(name) for r in self.records]
                        for name in ("model", "task", "metric")}

            def to_pylist(self):
                return self.records

        class FakeParquet:
            schema_arrow = SimpleNamespace(
                names=list(fixture[0]),
                field=lambda name: SimpleNamespace(type="float64" if name == "score" else "string"),
            )
            metadata = SimpleNamespace(num_rows=3, row_group=lambda i: SimpleNamespace(num_rows=3))
            num_row_groups = 1

            def __init__(self, _):
                pass

            def read_row_group(self, index, columns):
                return Table([{name: r[name] for name in columns} for r in fixture])

        def fetch(url):
            if "/tree/" in url:
                return [{"type": "file", "path": "scores.parquet"}]
            return {"sha": "a" * 40, "lastModified": "today"}

        arrow_module = ModuleType("pyarrow")
        arrow_module.__path__ = []
        arrow_module.__version__ = "test"
        parquet_module = ModuleType("pyarrow.parquet")
        parquet_module.ParquetFile = FakeParquet
        arrow_module.parquet = parquet_module
        modules = {"pyarrow": arrow_module, "pyarrow.parquet": parquet_module}
        with patch.dict(sys.modules, modules):
            data = bp.parquet_scores(fetch=fetch, download=lambda url: b"fake parquet")
        self.assertEqual(data["source_method"], "pinned_source_parquet")
        self.assertEqual(len(data["rows"]), 2)
        self.assertEqual([r["source_file_row_idx"] for r in data["rows"]], [0, 2])
        self.assertEqual(data["source_files"][0]["matched_rows"], 2)
        self.assertEqual(data["parquet_reader"], "pyarrow test")
        self.assertEqual(bp.assess_scores(data)["status"], "comparable")

    def test_filter_url_and_revision_provenance(self):
        calls = []

        def fetch(url):
            calls.append(url)
            if "/api/datasets/" in url:
                return {"sha": "f" * 40, "lastModified": "2026-11-08"}
            if "/splits?" in url:
                return {"splits": [{"config": "default", "split": "train"}]}
            if "/filter?" in url:
                return {
                    "features": [{"name": col} for col in bp.REQUIRED],
                    "rows": [row(10, .2), row(20, .4, 1)],
                }
            raise AssertionError(url)

        data = bp.filtered_scores(fetch=fetch)
        self.assertEqual(data["revision_sha"], "f" * 40)
        self.assertEqual(len(data["rows"]), 2)
        self.assertFalse(data["scan_truncated"])
        self.assertEqual(len(data["filter_urls"]), 1)
        params = parse_qs(urlsplit(data["filter_urls"][0]).query)
        self.assertEqual(params["dataset"], [bp.DATASET])
        self.assertEqual(params["where"], [
            '"model"=\'prelude_anneal2t\' AND "task"=\'coqa_gen\' AND "metric"=\'f1\''
        ])
        self.assertEqual(sum("/api/datasets/" in u for u in calls), 2)

    def test_revision_drift_aborts(self):
        revisions = iter(["a" * 40, "b" * 40])

        def fetch(url):
            if "/api/datasets/" in url:
                return {"sha": next(revisions)}
            if "/splits?" in url:
                return {"splits": [{"config": "default", "split": "train"}]}
            return {"features": [{"name": name} for name in bp.REQUIRED], "rows": []}

        with self.assertRaisesRegex(ValueError, "revision changed"):
            bp.filtered_scores(fetch=fetch)

    def test_full_page_flags_truncation(self):
        def fetch(url):
            if "/api/datasets/" in url:
                return {"sha": "a" * 40}
            if "/splits?" in url:
                return {"splits": [{"config": "default", "split": "train"}]}
            return {
                "features": [{"name": col} for col in bp.REQUIRED],
                "rows": [row(i, .2, i) for i in range(bp.PAGE_SIZE)],
            }

        data = bp.filtered_scores(fetch=fetch, pages=1)
        self.assertTrue(data["scan_truncated"])
        self.assertIn("source_filter_limit_reached",
                      bp.assess_scores(source(data["rows"], scan_truncated=True))["problems"])

    def test_source_error_report_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path(directory) / "PRELUDE_EVAL.md"
            previous.write_text("last known good\n")
            with patch.object(bp, "parquet_scores", side_effect=ValueError("not available")):
                self.assertEqual(bp.main(["--output", directory]), 1)
            payload = json.loads((Path(directory) / "prelude_eval_error.json").read_text())
            report = (Path(directory) / "PRELUDE_EVAL_ERROR.md").read_text()
            self.assertEqual(payload["status"], "source_error")
            self.assertIn("no scores were analyzed", report)
            self.assertEqual(previous.read_text(), "last known good\n")
            self.assertFalse((Path(directory) / "prelude_eval.json").exists())

    def test_retry_transient_timeout_then_success(self):
        calls, delays = [], []

        def source():
            calls.append(True)
            if len(calls) < 3:
                raise TimeoutError("temporary")
            return {"status": "recovered"}

        self.assertEqual(bp.retry_transient(source, sleep=delays.append),
                         {"status": "recovered"})
        self.assertEqual(len(calls), 3)
        self.assertEqual(delays, [1, 2])

    def test_retry_transient_exhausted_and_permanent_http_error(self):
        calls, delays = [], []

        def unavailable():
            calls.append(True)
            raise urllib.error.URLError("offline")

        with self.assertRaises(urllib.error.URLError):
            bp.retry_transient(unavailable, sleep=delays.append)
        self.assertEqual(len(calls), 3)
        self.assertEqual(delays, [1, 2])

        bad_request = urllib.error.HTTPError("https://example.org", 404, "missing", {}, None)
        with self.assertRaises(urllib.error.HTTPError):
            bp.retry_transient(lambda: (_ for _ in ()).throw(bad_request), sleep=delays.append)
        self.assertEqual(delays, [1, 2])


if __name__ == "__main__":
    unittest.main()
