import json
import unittest
from pathlib import Path
from semantic_review import case_payload, validate_answer, evaluate, collect_cases, completion

CASES = json.loads((Path(__file__).resolve().parents[1] / "studies/semantic_review_pilot/cases.json").read_text(encoding="utf-8"))["cases"]

class SemanticTests(unittest.TestCase):
    def answer(self, packet):
        return {"verdict": "plausible_experiment", "claims": [
            {"claim": "Example", "evidence_id": e["id"], "quote": e["text"].splitlines()[0]}
            for e in packet["evidence"]], "next_test": "Compare controls", "limitations": ["No proven cooperation"]}

    def test_reference_not_sent(self):
        packet = case_payload(CASES[0])
        self.assertNotIn("expected_verdict", packet)
        self.assertNotIn("reference_rationale", packet)
        self.assertEqual(validate_answer(self.answer(packet), packet)["verdict"], "plausible_experiment")

    def test_invented_quote_rejected(self):
        packet = case_payload(CASES[0])
        answer = self.answer(packet)
        answer["claims"][0]["quote"] = "invented"
        with self.assertRaises(ValueError):
            validate_answer(answer, packet)

    def test_positive_requires_two_sources(self):
        packet = case_payload(CASES[0])
        answer = self.answer(packet)
        answer["claims"].pop()
        with self.assertRaises(ValueError):
            validate_answer(answer, packet)

    def test_abstention_and_invalid_response(self):
        def run(packet):
            if packet["id"] == "laion-aura":
                return {}, {}
            return {"verdict": "insufficient_evidence", "claims": [], "next_test": "Read more evidence",
                    "limitations": ["Incomplete"]}, {}
        result = evaluate(CASES, run)
        self.assertEqual(result["records"][0]["status"], "invalid_or_unavailable")
        self.assertEqual(result["provisional_comparison"], {"compared": 2, "agreed": 1})

    def test_local_rejects_non_loopback(self):
        with self.assertRaises(ValueError):
            completion(case_payload(CASES[0]), provider="local", model="test", local_url="https://example.org/v1")

    def test_collection_does_not_follow_untrusted_urls(self):
        calls = []
        cases, errors = collect_cases({"topic_hypotheses": [{"left": "https://evil.example/x/y", "right": "https://github.com/a/b"}]}, lambda u: calls.append(u))
        self.assertEqual(cases, [])
        self.assertEqual(calls, [])
        self.assertEqual(len(errors), 1)
