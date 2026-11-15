import copy
import json
import unittest
from pathlib import Path

from paired_decision_evidence import audit, digest


def packet():
    issue = "https://github.com/OpenEuroLLM/Taskboard/issues/3"
    anchor = "github:OpenEuroLLM/Taskboard#3"
    return {
        "schema_version": 1, "kind": "frozen_identical_source_packet",
        "cases": [
            {"case_id": "X1", "anchor_id": anchor, "url": issue,
             "body": "The task was proposed.", "updated_at": "2026-11-15",
             "comments": [{"url": issue + "#issuecomment-5",
                           "body": "The experiment is done.",
                           "updated_at": "2026-11-15"}],
             "graph_snapshot": {"explicit_edges": []}}
        ],
    }


class PairedDecisionEvidenceTests(unittest.TestCase):
    def test_equal_source_digest_and_facts(self):
        result = audit(packet())
        case = result["cases"][0]
        self.assertTrue(case["identical_original_evidence"])
        self.assertEqual(case["primary_source_records_per_arm"], 2)
        self.assertEqual(case["public_comments_per_arm"], 1)
        self.assertEqual(case["source_sha256"], case["graph_primary_source_sha256"])
        self.assertFalse(result["summary"]["decision_accuracy_measured"])
        self.assertIsNone(case["human_time_saved"])

    def test_graph_reference_hint_does_not_add_hidden_source(self):
        data = packet()
        data["cases"][0]["graph_snapshot"]["explicit_edges"] = [{
            "source": data["cases"][0]["anchor_id"],
            "target": "github:OpenEuroLLM/Taskboard#4",
            "status": "explicit_task_reference",
        }]
        result = audit(data)
        self.assertEqual(result["summary"]["graph_structural_hints"], 1)
        self.assertEqual(result["cases"][0]["extra_original_sources_from_graph"], 0)
        self.assertTrue(result["cases"][0]["identical_original_evidence"])

    def test_rejects_incomplete_or_invalid_source_packets(self):
        data = packet()
        data["cases"][0]["comments"][0]["url"] = "https://evil.invalid/source"
        with self.assertRaisesRegex(ValueError, "Unattributed"):
            audit(data)

        data = packet()
        data["cases"][0]["graph_snapshot"].pop("explicit_edges")
        with self.assertRaisesRegex(ValueError, "graph-edge"):
            audit(data)

        data = packet()
        data["cases"][0]["body"] = None
        with self.assertRaisesRegex(ValueError, "body"):
            audit(data)

        data = packet()
        data["cases"].append(copy.deepcopy(data["cases"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            audit(data)

    def test_real_frozen_selection_remains_unchanged(self):
        path = Path(__file__).resolve().parents[1] / "studies" / "decision_pilot_20261115" / "FROZEN_EVIDENCE.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        result = audit(data)
        self.assertEqual(result["summary"]["case_count"], 3)
        self.assertEqual(result["summary"]["total_comment_records_per_arm"], 15)
        self.assertEqual(result["summary"]["graph_structural_hints"], 0)
        self.assertEqual(result["summary"]["identical_evidence_cases"], 3)
        self.assertEqual(digest(data), result["frozen_input_sha256"])


if __name__ == "__main__":
    unittest.main()
