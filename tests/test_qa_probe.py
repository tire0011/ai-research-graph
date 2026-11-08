import unittest

from qa_probe import evaluate, examine_case, markdown_report


class QuestionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.github_id = "github:example/task#1"
        self.hf_id = "hf:dataset:example/data"
        self.paper_id = "openaire:paper"
        self.graph = {"timestamp_utc": "2026-11-08T00:00:00Z", "nodes": [
            {"id": self.github_id, "title": "Investigate dataset", "type": "issue", "url": "https://github.com/example/task/issues/1"},
            {"id": self.hf_id, "title": "example/data", "type": "dataset", "url": "https://huggingface.co/datasets/example/data"},
            {"id": self.paper_id, "title": "A paper", "type": "research_product", "url": "https://arxiv.org/abs/2501.01234", "identifiers": {"arxiv": ["2501.01234"]}},
        ], "edges": [
            {"source": self.github_id, "target": self.paper_id, "status": "identifier_match", "evidence_type": "arxiv", "evidence": "2501.01234"},
            {"source": self.hf_id, "target": self.paper_id, "status": "identifier_match", "evidence_type": "arxiv", "evidence": "2501.01234"},
        ]}
        self.case = {"id": "sample", "question": "Do both cite this paper?", "kind": "shared_citation",
                     "arxiv": "2501.01234", "github_id": self.github_id, "hf_id": self.hf_id}

    def test_exact_citation_bridge_produces_cited_evidence(self):
        result = examine_case(self.graph, self.case)
        self.assertTrue(result["passed"])
        self.assertEqual(result["relationship"], "shared_paper_citation")
        self.assertEqual(len(result["sources"]), 3)
        self.assertIn("no direct dataset usage", result["limits"].lower())
        summary = markdown_report(evaluate(self.graph, [self.case]))
        self.assertIn("1/1", summary)
        self.assertIn("https://arxiv.org/abs/2501.01234", summary)

    def test_missing_or_wrong_identifier_cannot_be_invented(self):
        self.graph["edges"][1]["evidence"] = "2501.01235"
        result = examine_case(self.graph, self.case)
        self.assertFalse(result["passed"])
        self.assertEqual(result["sources"], [])

    def test_inaccessible_card_must_be_treated_as_unverified(self):
        model = {"id": "hf:model:example/model", "title": "example/model", "type": "model",
                 "url": "https://huggingface.co/example/model"}
        self.graph["nodes"].append(model)
        self.graph["external_hf_card_references"] = [{"source": model["id"], "target_type": "dataset",
            "declared_id": "missing/dataset", "target_url": "https://huggingface.co/datasets/missing/dataset"}]
        self.graph["external_hf_target_checks"] = [{"target_type": "dataset", "declared_id": "missing/dataset", "status": "inaccessible"}]
        case = {"id": "unverified", "kind": "publisher_declaration_check", "question": "Was it used?",
                "hf_id": model["id"], "target_type": "dataset", "declared_id": "missing/dataset",
                "expected_lookup_status": "inaccessible"}
        result = examine_case(self.graph, case)
        self.assertTrue(result["passed"])
        self.assertIn("cannot", result["limits"].lower())
        self.graph["edges"].append({"source": model["id"], "target": "hf:dataset:missing/dataset",
                                    "status": "declared_metadata", "evidence": "missing/dataset"})
        self.assertFalse(examine_case(self.graph, case)["passed"])
        self.graph["external_hf_target_checks"][0]["status"] = "verified_public"
        refreshed = examine_case(self.graph, case)
        self.assertTrue(refreshed["passed"])
        self.assertTrue(refreshed["status_changed_from_baseline"])
        self.assertEqual(refreshed["relationship"], "publisher_declaration_to_public_target")


if __name__ == "__main__":
    unittest.main()
