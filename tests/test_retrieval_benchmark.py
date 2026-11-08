import unittest

import retrieval_benchmark as rb


def node(id_, type_, title, description=""):
    return {"id": id_, "type": type_, "title": title,
            "description": description, "url": "https://example.org/" + id_}


class RetrievalBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "timestamp_utc": "2026-11-08", "nodes": [
                node("github:a", "issue", "Experiment", "paper arxiv:2506.04178"),
                node("hf:dataset:alpha", "dataset", "Alpha source", "arxiv:2506.04178"),
                node("hf:dataset:beta", "dataset", "Beta unrelated"),
                node("openaire:paper", "research_product", "Referenced paper"),
                node("hf:model:model", "model", "Model HPLT"),
            ],
            "edges": [
                {"source": "github:a", "target": "hf:dataset:alpha", "status": "explicit_reference"},
                {"source": "github:a", "target": "hf:dataset:beta", "status": "candidate"},
                {"source": "github:a", "target": "openaire:paper", "status": "identifier_match"},
                {"source": "hf:dataset:alpha", "target": "openaire:paper", "status": "identifier_match"},
            ],
            "external_hf_card_references": [
                {"source": "hf:model:model", "target_type": "dataset", "declared_id": "HPLT/HPLT4.0"}
            ],
            "external_hf_target_checks": [
                {"target_type": "dataset", "declared_id": "HPLT/HPLT4.0", "status": "inaccessible"}
            ],
        }

    def test_explicit_ignores_name_only_candidate(self):
        case = {"anchor_id": "github:a", "kind": "explicit", "target_type": "dataset",
                "question": "Which Alpha source dataset is referenced?"}
        found = rb.graph_candidates(rb.graph_index(self.graph), case)
        self.assertEqual(found, ["hf:dataset:alpha"])

    def test_shared_identifier_bridge_is_not_training_proof(self):
        case = {"anchor_id": "github:a", "kind": "shared_citation", "target_type": "dataset",
                "question": "Which Alpha source shares a scholarly citation?"}
        found = rb.graph_candidates(rb.graph_index(self.graph), case)
        self.assertEqual(found, ["hf:dataset:alpha"])

    def test_unverified_card_abstention(self):
        case = {"id": "unverified", "anchor_id": "hf:model:model", "kind": "unverified_declaration",
                "target_type": "dataset", "declared_id": "HPLT/HPLT4.0",
                "question": "Was HPLT used in training?"}
        self.assertEqual(rb.declaration_status(self.graph, case), "inaccessible")
        evaluation = rb.evaluate(self.graph, [case], repetitions=1)
        self.assertEqual(evaluation["cases"][0]["status"], "abstained")
        self.assertEqual(evaluation["targets"], 0)

    def test_recall_counts_expected_artifacts_not_just_search_hits(self):
        case = {"id": "positive", "anchor_id": "github:a", "kind": "explicit",
                "target_type": "dataset", "question": "Which Alpha source dataset is referenced?",
                "expected_ids": ["hf:dataset:alpha", "hf:dataset:missing"]}
        result = rb.evaluate(self.graph, [case], repetitions=1)
        self.assertEqual(result["targets"], 2)
        self.assertEqual(result["graph_recalled"], 1)
        self.assertIn("Plain-text source-record search", rb.markdown(result))

    def test_missing_anchor_is_not_counted_as_zero_recall(self):
        case = {"id": "missing", "anchor_id": "github:missing", "kind": "explicit",
                "target_type": "dataset", "question": "Which dataset?",
                "expected_ids": ["hf:dataset:alpha"]}
        result = rb.evaluate(self.graph, [case], repetitions=1)
        self.assertEqual(result["targets"], 0)
        self.assertEqual(result["cases"][0]["status"], "missing_anchor")


if __name__ == "__main__":
    unittest.main()
