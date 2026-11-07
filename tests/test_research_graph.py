import unittest

from research_graph import exact_reference, links_between, normalized, quality_profile, report


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


if __name__ == "__main__":
    unittest.main()
