import unittest

from research_graph import links_between, normalized, report


class ResearchGraphTests(unittest.TestCase):
    def setUp(self):
        self.asset = {
            "id": "hf:dataset:openeurollm/prelude-base-eval-scores", "type": "dataset",
            "title": "openeurollm/prelude-base-eval-scores",
            "url": "https://huggingface.co/datasets/openeurollm/prelude-base-eval-scores",
        }

    def issue(self, body):
        return {"id": "github:OpenEuroLLM/Taskboard#445", "type": "issue", "title": "evaluation", "description": body, "url": "https://github.com/OpenEuroLLM/Taskboard/issues/445"}

    def test_explicit_hf_link_is_verified(self):
        result = links_between([self.issue(f"See {self.asset['url']}"), self.asset])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "verified")

    def test_exact_hf_id_is_verified(self):
        result = links_between([self.issue("openeurollm/prelude-base-eval-scores"), self.asset])
        self.assertEqual(result[0]["status"], "verified")

    def test_name_only_is_not_verified(self):
        result = links_between([self.issue("Update prelude-base-eval-scores plot"), self.asset])
        self.assertEqual(result[0]["status"], "candidate")

    def test_generic_model_name_does_not_match(self):
        self.assertEqual(links_between([self.issue("Evaluate Prelude") , self.asset]), [])

    def test_cross_source_only(self):
        self.assertEqual(links_between([self.issue("See another issue")]), [])

    def test_normalizer(self):
        self.assertEqual(normalized("Prelude Base/Eval Scores"), "prelude-base-eval-scores")

    def test_report_exposes_failures(self):
        output = report([], [], {"OpenAIRE": "timeout"}, "2026-11-07", None)
        self.assertIn("OpenAIRE", output)
        self.assertIn("unavailable", output)


if __name__ == "__main__":
    unittest.main()
