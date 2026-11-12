"""Offline unit tests for independent intervention review."""
import json
import tempfile
import unittest
from pathlib import Path

from research_interventions import case_from, evaluate, prepare, prompt

CASE = {
    "case_id": "sample",
    "question": "Can tool A test artifact B?",
    "facts": ["Tool A exists", "Artifact B exists"],
    "unknowns": ["No direct compatibility run"],
    "evidence_urls": ["https://github.com/example/project/issues/1"],
}

def review(role, family, decision="promising"):
    return {
        "case_id": "sample", "role": role, "model_id": "test/" + family,
        "model_family": family, "decision": decision,
        "evidence_urls": CASE["evidence_urls"],
        "reason": "Proposed only", "testable_claim": "Measured improvement?",
        "falsification_test": "Fixed sample vs baseline; stop if no improvement",
    }

class InterventionReviewTests(unittest.TestCase):
    def test_prompts_independent_and_nonexecuting(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "new"
            prepare(CASE, folder)
            self.assertEqual(len(list(folder.glob("*.prompt.txt"))), 3)
            self.assertIn("Do not see or infer other model answers", prompt(CASE, "skeptic"))
            self.assertFalse((folder / "proposer.json").exists())

    def test_cross_family_requires_human_review(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            for role, family in zip(("proposer", "skeptic", "experimenter"), ("A", "B", "C")):
                (folder / f"{role}.json").write_text(json.dumps(review(role, family)))
            result = evaluate(CASE, folder)
            self.assertEqual(result["gate"], "human_review_only")
            self.assertFalse(result["technical_benefit_verified"])

    def test_skeptic_veto(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            for role in ("proposer", "skeptic", "experimenter"):
                (folder / f"{role}.json").write_text(
                    json.dumps(review(role, role, "reject" if role == "skeptic" else "promising")))
            self.assertEqual(evaluate(CASE, folder)["gate"], "stop_and_investigate")

    def test_same_family_needs_other_model(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            for role in ("proposer", "skeptic", "experimenter"):
                (folder / f"{role}.json").write_text(json.dumps(review(role, "A")))
            self.assertEqual(evaluate(CASE, folder)["gate"], "needs_other_model_family")

    def test_wrong_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            for role in ("proposer", "skeptic", "experimenter"):
                r = review(role, role)
                if role == "skeptic":
                    r["evidence_urls"] = ["https://unrelated.example"]
                (folder / f"{role}.json").write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError, "unknown evidence"):
                evaluate(CASE, folder)

    def test_case_validation(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "case.json"
            path.write_text(json.dumps(CASE))
            self.assertEqual(case_from(path), CASE)
            path.write_text(json.dumps({**CASE, "evidence_urls": ["http://invalid"]}))
            with self.assertRaisesRegex(ValueError, "https"):
                case_from(path)

if __name__ == "__main__":
    unittest.main()
