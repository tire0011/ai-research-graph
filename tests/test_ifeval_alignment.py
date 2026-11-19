"""Offline tests: no benchmark download, no model calls, no prompt publication."""
import json
from pathlib import Path
import tempfile
import unittest

from ifeval_alignment import CHECKERS, LANGUAGES, evaluate, fetch_pinned_sources, load_rows


def setup_fixture(directory: Path):
    for lang in LANGUAGES:
        rows = []
        for index, checker in enumerate(CHECKERS, 1):
            rows.append({
                "key": index,
                "prompt": f"Example in {lang} for key {index}",
                "instruction_id_list": [checker],
                "kwargs": [{}],
                "requires_answer_in_source_language": False,
            })
        # An explicit response-language constraint disqualifies the key.
        rows.append({
            "key": 10, "prompt": f"{lang}: answer in language",
            "instruction_id_list": ["punctuation:no_comma"],
            "kwargs": [{}], "requires_answer_in_source_language": lang == "ga",
        })
        # A mismatched checker argument disqualifies another key.
        rows.append({
            "key": 11, "prompt": f"{lang}: at least N placeholders",
            "instruction_id_list": ["detectable_content:number_placeholders"],
            "kwargs": [{"num_placeholders": 2 if lang == "ga" else 3}],
            "requires_answer_in_source_language": False,
        })
        # Key missing in Irish, to verify intersection rather than file lengths.
        if lang != "ga":
            rows.append({
                "key": 12, "prompt": "not in ga",
                "instruction_id_list": ["detectable_format:json_format"],
                "kwargs": [{}], "requires_answer_in_source_language": False,
            })
        (directory / f"{lang}.jsonl").write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n",
            encoding="utf-8"
        )
    (directory / "source.json").write_text(json.dumps({
        lang: {
            "quality": "machine_translated_with_localization" if lang == "ga"
            else "localized_verified" if lang == "fr" else "native_speaker",
            "missing_samples": 1 if lang == "ga" else 0,
            "source": "https://example.test/translated"
        } for lang in LANGUAGES
    }), encoding="utf-8")


class IFEvalAlignmentTests(unittest.TestCase):
    def test_matched_source_criteria_only(self):
        with tempfile.TemporaryDirectory() as d:
            setup_fixture(Path(d))
            report = evaluate(Path(d))
            self.assertEqual(report["shared_keys"], 7)
            self.assertEqual(report["same_instruction_ids"], 7)
            self.assertEqual(report["strict_matching_checker_kwargs_and_no_response_language_constraint"], 5)
            self.assertEqual(report["selected_count"], 5)
            self.assertTrue(all(not row["semantic_equivalence_verified"] for row in report["selected"]))
            self.assertNotIn("Example in", json.dumps(report))

    def test_repeatable_metadata_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            setup_fixture(Path(d))
            first, second = evaluate(Path(d)), evaluate(Path(d))
            self.assertEqual(first, second)
            self.assertEqual(len(first["selected"][0]["prompt_sha256"]["ga"]), 64)

    def test_order_of_kwargs_dict_keys_is_not_semantic(self):
        with tempfile.TemporaryDirectory() as d:
            setup_fixture(Path(d))
            target = Path(d) / "ga.jsonl"
            items = [json.loads(x) for x in target.read_text().splitlines()]
            for x in items:
                if x["key"] == 11:
                    x["kwargs"] = [{"num_placeholders": 3}]
            target.write_text("\n".join(json.dumps(x) for x in items))
            self.assertEqual(evaluate(Path(d))["strict_matching_checker_kwargs_and_no_response_language_constraint"], 6)

    def test_invalid_row_schema(self):
        with tempfile.TemporaryDirectory() as d:
            setup_fixture(Path(d))
            p = Path(d) / "ga.jsonl"
            lines = p.read_text().splitlines()
            x = json.loads(lines[0])
            x["kwargs"] = []
            lines[0] = json.dumps(x)
            p.write_text("\n".join(lines))
            with self.assertRaisesRegex(ValueError, "checker fields"):
                evaluate(Path(d))

    def test_duplicate_id_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            setup_fixture(Path(d))
            p = Path(d) / "de.jsonl"
            p.write_text(p.read_text() + p.read_text().splitlines()[0] + "\n")
            with self.assertRaisesRegex(ValueError, "repeated key"):
                load_rows(p)

    def test_bad_provenance_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            setup_fixture(Path(d))
            p = Path(d) / "source.json"
            meta = json.loads(p.read_text())
            meta["ga"]["quality"] = "unknown"
            p.write_text(json.dumps(meta))
            with self.assertRaisesRegex(ValueError, "provenance"):
                evaluate(Path(d))

    def test_invalid_per_checker(self):
        with tempfile.TemporaryDirectory() as d:
            setup_fixture(Path(d))
            with self.assertRaises(ValueError):
                evaluate(Path(d), per_checker=0)

    def test_no_overwrite_fetch(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileExistsError):
                fetch_pinned_sources(Path(d))


if __name__ == "__main__":
    unittest.main()
