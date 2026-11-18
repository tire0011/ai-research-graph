import unittest
from pr_opportunity_gate import evaluate

URL = "https://github.com/example/repo/issues/1"

class OpportunityGateTests(unittest.TestCase):
    def test_missing_evidence_blocks(self):
        result = evaluate({"title": "Fix issue"})
        self.assertEqual(result["status"], "investigate")
        self.assertIn("reproduction", result["blockers"])

    def test_complete_candidate(self):
        fields = ("problem", "reproduction", "code_location", "expected_impact", "maintainer_signal")
        candidate = {"title": "Fix", "evidence": {k: URL for k in fields},
                     "scores": {k: 3 for k in ("reach", "reproducibility", "maintainer", "feasibility", "no_overlap")},
                     "maintainer_approved": True}
        result = evaluate(candidate)
        self.assertEqual(result["status"], "ready_for_pr")
        self.assertEqual(result["score_lower_bound"], 100)
        candidate["existing_pr"] = True
        self.assertEqual(evaluate(candidate)["status"], "investigate")

    def test_unknown_not_zero(self):
        result = evaluate({"title": "Maybe", "scores": {"reach": 3}})
        self.assertEqual(result["score_coverage_percent"], 30)
        self.assertEqual(result["score_lower_bound"], 30)

    def test_invalid_evidence(self):
        with self.assertRaises(ValueError):
            evaluate({"title": "x", "evidence": {"problem": "made-up"}})

    def test_invalid_score(self):
        with self.assertRaises(ValueError):
            evaluate({"title": "x", "scores": {"reach": 4}})
