import json
import unittest
from pathlib import Path
from semantic_review import case_payload, validate_answer, evaluate, collect_cases, completion, ReviewError, safe_model_output
from unittest.mock import patch

CASES = json.loads((Path(__file__).resolve().parents[1] / "studies/semantic_review_pilot/cases.json").read_text(encoding="utf-8"))["cases"]

class SemanticTests(unittest.TestCase):
    def answer(self, packet):
        return {"verdict": "plausible_experiment", "claims": [
            {"claim": "Example", "section_id": e["sections"][0]["section_id"]}
            for e in packet["evidence"]], "next_test": "Compare controls", "limitations": ["No proven cooperation"]}

    def test_reference_not_sent(self):
        packet = case_payload(CASES[0])
        self.assertNotIn("expected_verdict", packet)
        self.assertNotIn("reference_rationale", packet)
        self.assertEqual(validate_answer(self.answer(packet), packet)["verdict"], "plausible_experiment")

    def test_invented_section_rejected(self):
        packet = case_payload(CASES[0])
        answer = self.answer(packet)
        answer["claims"][0]["section_id"] = "invented"
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
        result = evaluate(CASES, run, limit=3)
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

    def test_sections_preserve_original_text_and_are_stable(self):
        packet = case_payload(CASES[0])
        self.assertEqual(packet, case_payload(CASES[0]))
        for doc, source in zip(packet["evidence"], CASES[0]["evidence"]):
            self.assertNotIn("text", doc)
            for section in doc["sections"]:
                self.assertEqual(section["text"], source["text"][section["start"]:section["end"]])

    def test_positive_cannot_cite_same_source_twice(self):
        packet = case_payload(CASES[0])
        answer = self.answer(packet)
        answer["claims"][1]["section_id"] = answer["claims"][0]["section_id"]
        with self.assertRaises(ReviewError) as caught:
            validate_answer(answer, packet)
        self.assertEqual(caught.exception.code, "source_coverage")

    def test_validation_failure_retains_safe_diagnostics(self):
        def run(packet):
            answer = self.answer(packet)
            answer["claims"][0]["section_id"] = "missing"
            return answer, {"model_response": "bounded output", "finish_reason": "stop"}
        record = evaluate(CASES, run, limit=1)["records"][0]
        self.assertEqual(record["error_code"], "unknown_section")
        self.assertEqual(record["diagnostics"]["model_response"], "bounded output")
        self.assertIn("provisional_expected", record)
        self.assertNotIn("answer", record)

    def test_provider_failure_diagnostics_and_redaction(self):
        def run(packet):
            raise ReviewError("invalid_json", "model did not return JSON", {"finish_reason": "stop"})
        record = evaluate(CASES, run, limit=1)["records"][0]
        self.assertEqual(record["error_code"], "invalid_json")
        self.assertEqual(record["diagnostics"]["finish_reason"], "stop")
        with patch.dict("os.environ", {"MISTRAL_API_KEY": "example-secret"}):
            self.assertEqual(safe_model_output("x example-secret"), "x [REDACTED]")
            self.assertEqual(len(safe_model_output("x" * 15000)), 12000)

    def test_benchmark_is_balanced_and_valid(self):
        self.assertEqual(len(CASES), 20)
        self.assertEqual(len({c["id"] for c in CASES}), 20)
        for verdict in ("plausible_experiment", "weak_overlap", "documented_connection", "insufficient_evidence"):
            self.assertEqual(sum(c["expected_verdict"] == verdict for c in CASES), 5)
        for case in CASES:
            case_payload(case)
        result = evaluate(CASES, lambda packet: ({}, {}), limit=20)
        self.assertEqual(result["metrics"], {"attempted": 20, "valid": 0, "labeled": 20, "correct": 0})
