import unittest
from unittest.mock import patch

from research_graph import (
    enrich_publications, exact_reference, identifiers_in, links_between, normalized,
    openaire_node, quality_profile, report, scholarly_links,
)


class ResearchGraphTests(unittest.TestCase):
    def setUp(self):
        self.asset = {
            "id": "hf:dataset:openeurollm/prelude-base-eval-scores", "type": "dataset",
            "title": "openeurollm/prelude-base-eval-scores",
            "url": "https://huggingface.co/datasets/openeurollm/prelude-base-eval-scores",
        }

    def issue(self, body):
        return {"id": "github:OpenEuroLLM/Taskboard#445", "type": "issue", "title": "evaluation", "description": body, "url": "https://github.com/OpenEuroLLM/Taskboard/issues/445"}

    def test_explicit_hf_link_is_recorded(self):
        result = links_between([self.issue(f"See {self.asset['url']}"), self.asset])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "explicit_reference")
        self.assertEqual(result[0]["evidence_type"], "url")
        self.assertIn("huggingface.co", result[0]["context"])

    def test_exact_hf_id_is_recorded(self):
        result = links_between([self.issue("openeurollm/prelude-base-eval-scores"), self.asset])
        self.assertEqual(result[0]["status"], "explicit_reference")
        self.assertEqual(result[0]["evidence_type"], "repository_id")

    def test_name_only_is_not_verified(self):
        result = links_between([self.issue("Update prelude-base-eval-scores plot"), self.asset])
        self.assertEqual(result[0]["status"], "candidate")

    def test_generic_model_name_does_not_match(self):
        self.assertEqual(links_between([self.issue("Evaluate Prelude") , self.asset]), [])

    def test_cross_source_only(self):
        self.assertEqual(links_between([self.issue("See another issue")]), [])

    def test_rejects_tokenizer_prefix_false_positive(self):
        older = {"id": "hf:model:openeurollm/tokenizer-256k", "type": "model", "title": "openeurollm/tokenizer-256k", "url": "https://huggingface.co/openeurollm/tokenizer-256k"}
        newer = {"id": "hf:model:openeurollm/tokenizer-256k-v2", "type": "model", "title": "openeurollm/tokenizer-256k-v2", "url": "https://huggingface.co/openeurollm/tokenizer-256k-v2"}
        edges = links_between([self.issue("See https://huggingface.co/openeurollm/tokenizer-256k-v2"), older, newer])
        self.assertEqual([edge["target"] for edge in edges], [newer["id"]])

    def test_rejects_model_prefix_of_dataset(self):
        model = {"id": "hf:model:openeurollm/prelude-base", "type": "model", "title": "openeurollm/prelude-base", "url": "https://huggingface.co/openeurollm/prelude-base"}
        result = links_between([self.issue(self.asset["url"]), model, self.asset])
        self.assertEqual([edge["target"] for edge in result], [self.asset["id"]])

    def test_repo_id_followed_by_slash_is_valid(self):
        self.assertIsNotNone(exact_reference("openeurollm/foo/resolve/main", "openeurollm/foo"))

    def test_foreign_hf_namespace_not_a_candidate(self):
        model = {"id": "hf:model:openeurollm/OLMo-3-7B-Think-SFT", "type": "model", "title": "openeurollm/OLMo-3-7B-Think-SFT", "url": "https://huggingface.co/openeurollm/OLMo-3-7B-Think-SFT"}
        self.assertEqual(links_between([self.issue("See https://huggingface.co/allenai/OLMo-3-7B-Think-SFT"), model]), [])
        self.assertEqual(links_between([self.issue("[OLMo-3-7B-Think-SFT](https://huggingface.co/allenai/OLMo-3-7B-Think-SFT)"), model]), [])

    def test_duplicate_and_orphan_checks(self):
        a = self.issue("issue")
        profile = quality_profile([a, a], [{"source": a["id"], "target": "missing"}])
        self.assertEqual(profile["duplicate_node_ids"], 1)
        self.assertEqual(profile["edges_with_missing_endpoints"], 1)

    def test_normalizer(self):
        self.assertEqual(normalized("Prelude Base/Eval Scores"), "prelude-base-eval-scores")

    def test_report_exposes_failures(self):
        output = report([], [], {"OpenAIRE": "timeout"}, "2026-11-07", None)
        self.assertIn("OpenAIRE", output)
        self.assertIn("unavailable", output)

    def test_scholarly_ids_are_explicit_and_version_normalized(self):
        text = 'See https://arxiv.org/pdf/2609.24797v2 and arxiv:2609.24797; https://doi.org/10.48550/arXiv.2609.24797.'
        self.assertEqual(identifiers_in(text), {
            "arxiv": ["2609.24797"], "doi": ["10.48550/arxiv.2609.24797"],
        })
        self.assertEqual(identifiers_in("version 2609.24797 and model 1.3B"), {"arxiv": [], "doi": []})

    def test_openaire_pid_is_extracted_with_http_url(self):
        paper = openaire_node({
            "id": "doi_dedup___::abc", "mainTitle": "Complex KDA", "type": "publication",
            "pids": [{"scheme": "doi", "value": "10.48550/arXiv.2609.24797"}],
            "instances": [{"urls": ["https://arxiv.org/abs/2609.24797"]}],
        })
        self.assertEqual(paper["url"], "https://arxiv.org/abs/2609.24797")
        self.assertEqual(paper["identifiers"]["arxiv"], ["2609.24797"])

    def test_five_models_link_to_same_publication_by_arxiv(self):
        paper = openaire_node({
            "id": "complex-kda", "mainTitle": "Complex KDA",
            "pids": [{"scheme": "arXiv", "value": "2609.24797"}],
        })
        assets = [{
            "id": f"hf:model:openeurollm/complex-kda-{i}", "type": "model",
            "title": f"openeurollm/complex-kda-{i}",
            "url": f"https://huggingface.co/openeurollm/complex-kda-{i}",
            "description": '{"tags": ["arxiv:2609.24797"]}',
        } for i in range(5)]
        edges = scholarly_links([paper, *assets])
        self.assertEqual(len(edges), 5)
        self.assertTrue(all(edge["status"] == "identifier_match" for edge in edges))
        self.assertTrue(all(edge["target"] == paper["id"] for edge in edges))
        self.assertEqual(quality_profile([paper, *assets], edges)["duplicate_edge_pairs"], 0)

    def test_no_spurious_scholarly_matches(self):
        paper = openaire_node({"id": "p1", "pids": [{"scheme": "arXiv", "value": "2609.24797"}]})
        issue = self.issue("An unrelated model named complex-kda")
        self.assertEqual(scholarly_links([paper, issue]), [])

    def test_bounded_openaire_enrichment_reports_missing_coverage(self):
        issues = []
        for i in range(3):
            node = self.issue(f"see https://arxiv.org/abs/2501.0000{i}")
            node["id"] += f"-{i}"
            node["identifiers"] = identifiers_in(node["description"])
            node["state"] = "open"
            issues.append(node)
        errors = {}
        with patch("research_graph.openaire_by_arxiv", return_value=[openaire_node({"id": "pub"})]) as mocked:
            products = enrich_publications(issues, errors, limit=2)
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(len(products), 2)
        self.assertIn("Sampled 2 of 3", errors["OpenAIRE citation coverage"])

    def test_report_separates_scholarly_edges(self):
        paper = openaire_node({"id": "abc", "mainTitle": "Paper", "pids": [{"scheme": "arXiv", "value": "2609.24797"}]})
        issue = self.issue("see arxiv:2609.24797")
        edges = scholarly_links([paper, issue])
        text = report([paper, issue], edges, {}, "2026-11-07", 1)
        self.assertIn("Shared scholarly identifiers (arXiv/DOI): **1**", text)
        self.assertIn("2609.24797", text)


if __name__ == "__main__":
    unittest.main()
