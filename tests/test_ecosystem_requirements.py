"""Offline, deterministic checks for multi-requirement platform reporting."""

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import ecosystem_requirements as er


class EcosystemRequirementTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(Path("ecosystem_sources.json").read_text(encoding="utf-8"))

    def test_every_requirement_has_separate_report_and_combined_matrix(self):
        result = er.build(self.registry)
        self.assertEqual(len(result["platforms"]), 4)
        self.assertEqual(len(result["requirements"]), 6)
        self.assertEqual(result["matrix"]["human_agent_coordination"]["eosc_arena"],
                         "planned")
        self.assertEqual(len(result["cross_project_cases"]), 3)
        self.assertFalse(result["novel_collaboration_confirmed"])
        with tempfile.TemporaryDirectory() as directory:
            paths = er.write_reports(result, Path(directory))
            self.assertEqual(len(paths), 14)
            summary = (Path(directory) / "OVERVIEW.md").read_text(encoding="utf-8")
            self.assertIn("Known relationships", summary)
            self.assertIn("not duplicate engineering work", summary)
            self.assertIn("human_agent_coordination.md", summary)
            self.assertIn("Arena-Hard v2 / contamination exclusion", summary)
            self.assertEqual(json.loads((Path(directory) / "interop.json").read_text())
                             ["requirement"]["id"], "interop")
            human = json.loads((Path(directory) / "human_agent_coordination.json").read_text())
            self.assertEqual([x["id"] for x in human["cross_project_cases"]],
                             ["model_card_provenance"])

    def test_one_unassessed_status_is_not_an_absence_claim(self):
        data = deepcopy(self.registry)
        data["observations"] = [x for x in data["observations"] if not (
            x["platform"] == "aiod" and x["requirement"] == "provenance")]
        result = er.build(data)
        self.assertEqual(result["matrix"]["provenance"]["aiod"], "not_assessed")
        _, markdown = er.requirement_report(result, next(
            r for r in result["requirements"] if r["id"] == "provenance"))
        self.assertIn("not proof of absence", markdown)

    def test_duplicate_evidence_rejected(self):
        data = deepcopy(self.registry)
        data["observations"].append(data["observations"][0])
        with self.assertRaisesRegex(ValueError, "duplicate evidence"):
            er.build(data)

    def test_unsupported_status_rejected(self):
        data = deepcopy(self.registry)
        data["observations"][0]["status"] = "implemented_and_tested"
        with self.assertRaisesRegex(ValueError, "Invalid or duplicate evidence"):
            er.build(data)

    def test_existing_relation_cannot_point_to_unlisted_platform(self):
        data = deepcopy(self.registry)
        data["known_relations"][0]["to"] = "new_undocumented_project"
        with self.assertRaisesRegex(ValueError, "Invalid supported platform relation"):
            er.build(data)

    def test_case_must_reference_known_requirement(self):
        data = deepcopy(self.registry)
        data["cross_project_cases"][0]["requirements"].append("imaginary")
        with self.assertRaisesRegex(ValueError, "Invalid cross-project case"):
            er.build(data)

    def test_report_is_deterministic(self):
        result = er.build(self.registry)
        with tempfile.TemporaryDirectory() as directory:
            er.write_reports(result, Path(directory))
            once = (Path(directory) / "comparison.json").read_bytes()
            er.write_reports(result, Path(directory))
            self.assertEqual((Path(directory) / "comparison.json").read_bytes(), once)


if __name__ == "__main__":
    unittest.main()
