"""No-network tests for AIoD metadata ↔ GitHub lexical review queue."""

import unittest
from copy import deepcopy

import aiod_catalogue_probe as aiod
import aiod_cross_compare as cross


class CrossCompareTests(unittest.TestCase):
    def setUp(self):
        self.aiod = aiod.collect("projects", limit=2, fetch=lambda _: [{
            "identifier": 77, "name": "Long context model evaluation",
            "description_plain": "Long context state tracking evaluation tools",
        }])
        self.github = {"timestamp_utc": "2026-11-11T10:00:00Z", "nodes": [{
            "id": "github:OpenEuroLLM/Taskboard#392", "type": "issue",
            "title": "Long context extension of prelude final checkpoint",
            "description": "Train longer context models and evaluate context capacity",
            "state": "open", "url": "https://github.com/OpenEuroLLM/Taskboard/issues/392",
        }, {
            "id": "github:OpenEuroLLM/Taskboard#1", "type": "issue",
            "title": "Collect dataset languages", "description": "Preprocess data",
            "state": "closed", "url": "https://github.com/OpenEuroLLM/Taskboard/issues/1",
        }]}

    def test_keeps_lexical_overlap_unreviewed_with_original_links(self):
        result = cross.compare(self.aiod, self.github)
        self.assertEqual(result["open_github_tasks"], 1)
        self.assertEqual(len(result["candidates"]), 1)
        candidate = result["candidates"][0]
        self.assertIn("context", candidate["shared_terms"])
        self.assertEqual(candidate["classification"], "unreviewed_lexical_overlap")
        self.assertFalse(result["novel_collaboration_confirmed"])
        self.assertIn("Review-only", cross.markdown(result))

    def test_unrelated_work_produces_no_matches(self):
        self.aiod["nodes"][0]["title"] = "Botanical planting assistance"
        self.aiod["nodes"][0]["description"] = "Fungal biodiversity"
        self.assertEqual(cross.compare(self.aiod, self.github)["total_lexical_candidates"], 0)

    def test_rejects_non_sampled_or_unverified_asset(self):
        bad = deepcopy(self.aiod)
        bad["status"] = "source_error"
        with self.assertRaises(ValueError):
            cross.compare(bad, self.github)
        bad = deepcopy(self.aiod)
        bad["nodes"][0]["type"] = "unverified_person"
        with self.assertRaises(ValueError):
            cross.compare(bad, self.github)

    def test_duplicate_work_is_not_inferred_from_shared_terms(self):
        result = cross.compare(self.aiod, self.github)
        self.assertEqual(result["candidates"][0]["existing_coordination"], "unknown")
        self.assertEqual(result["outreach"], "none")

    def test_same_external_url_does_not_double_count_candidates(self):
        duplicate = deepcopy(self.aiod["nodes"][0])
        duplicate["id"] = "aiod:v2:projects:another-id"
        duplicate["original_url_claim"] = "https://source.example.org/project"
        self.aiod["nodes"][0]["original_url_claim"] = duplicate["original_url_claim"]
        self.aiod["nodes"].append(duplicate)
        result = cross.compare(self.aiod, self.github)
        self.assertEqual(result["aiod_nodes"], 2)
        self.assertEqual(result["unique_aiod_claimed_sources"], 1)
        self.assertEqual(result["aiod_possible_aliases_skipped"], 1)
        self.assertEqual(result["total_lexical_candidates"], 1)


if __name__ == "__main__":
    unittest.main()
