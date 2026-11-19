"""Offline checks for the EU landscape evidence-overlay pilot."""
import copy
import json
import unittest
from pathlib import Path

from eu_model_landscape import build, validate


SOURCE = Path(__file__).resolve().parents[1] / "studies/eu_model_landscape_20261119/sources.json"


class LandscapePilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SOURCE.read_text(encoding="utf-8"))

    def test_project_count_and_identity(self):
        validate(self.data)
        self.assertEqual(len(self.data["projects"]), 25)
        self.assertEqual(len({p["id"] for p in self.data["projects"]}), 25)

    def test_evidence_does_not_promote_hypotheses_to_graph_edges(self):
        result = build(self.data)
        self.assertEqual(len(result["edges"]), 7)
        self.assertEqual(len(result["unreviewed_hypotheses"]), 3)
        self.assertFalse(any(e["status"] == "unreviewed_hypothesis" for e in result["edges"]))
        self.assertTrue(all(e["source_url"].startswith("https://") for e in result["edges"]))

    def test_shared_infrastructure_is_a_two_hop_fact_not_collaboration(self):
        result = build(self.data)
        shared = result["inferred_shared_infrastructure"]
        self.assertEqual(len(shared), 1)
        self.assertEqual({shared[0]["left"], shared[0]["right"]},
                         {"eu_project:olala", "eu_project:luciole"})
        self.assertEqual(shared[0]["via"], "eu_infrastructure:jean_zay")
        self.assertIn("NOT confirmed collaboration", shared[0]["interpretation"])

    def test_existing_snapshot_is_read_only_and_retained(self):
        original = {"timestamp_utc": "2026-11-15T00:00:00+00:00",
                    "nodes": [{"id": "github:example#1", "type": "issue"}],
                    "edges": [{"source": "github:example#1", "target": "hf:x/y"}]}
        frozen = copy.deepcopy(original)
        result = build(self.data, original)
        self.assertEqual(original, frozen)
        self.assertEqual(result["source_snapshot_timestamp"], original["timestamp_utc"])
        self.assertEqual(result["nodes"][0], original["nodes"][0])
        self.assertEqual(result["edges"][0], original["edges"][0])

    def test_rejects_unsupported_fact_and_duplicate_id(self):
        altered = copy.deepcopy(self.data)
        altered["facts"][0]["to"] = "nonexistent"
        with self.assertRaises(ValueError):
            validate(altered)
        altered = copy.deepcopy(self.data)
        altered["projects"][1]["id"] = altered["projects"][0]["id"]
        with self.assertRaises(ValueError):
            validate(altered)

    def test_rejects_source_collision(self):
        with self.assertRaises(ValueError):
            build(self.data, {"nodes": [{"id": "eu_project:olala"}], "edges": []})


if __name__ == "__main__":
    unittest.main()
