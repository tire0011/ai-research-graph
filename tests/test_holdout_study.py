import unittest
import io
import json
from unittest.mock import patch

import holdout_study as hs


def case():
    return {"id": "test", "repo": "OpenEuroLLM/Taskboard", "number": 420,
            "question": "What must be compared?", "answer": "Scanned documents",
            "evidence_level": "planned", "phrases": ["scanned documents"]}


def graph(body="scanned documents", updated="2026-11-08"):
    return {"timestamp_utc": "2026-11-08", "nodes": [
        {"id": "github:OpenEuroLLM/Taskboard#420", "type": "issue", "title": "PDF benchmark",
         "description": body, "updated_at": updated}], "edges": []}


def study(cases=None):
    return {"selection": {"seed": "fixed"}, "cases": cases or [case()]}


class HoldoutTests(unittest.TestCase):
    def test_null_github_body_is_legitimate_empty_issue(self):
        body = json.dumps({"number": 7, "body": None, "updated_at": "2026-11-08"}).encode()
        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                self.close()

        with patch("http_util.urllib.request.urlopen", return_value=Response(body)):
            result = hs.read_issue("OpenEuroLLM/Taskboard", 7)
        self.assertEqual(result["body"], "")

    def test_exact_source_parity_and_grounded_answer(self):
        result = hs.evaluate(graph(), study(), fetch=lambda repo, num: {
            "body": "scanned documents", "updated_at": "2026-11-08",
            "url": "https://github.com/OpenEuroLLM/Taskboard/issues/420", "latency_ms": 20})
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["exact_source_parity"], 1)
        self.assertEqual(result["graph_fact_support"], 1)
        self.assertEqual(result["linked_issues"], 0)
        self.assertIn("no real-world", hs.markdown(result))

    def test_source_not_found_is_error_not_zero(self):
        def unavailable(_repo, _num):
            raise TimeoutError("upstream unavailable")

        result = hs.evaluate(graph(), study(), fetch=unavailable)
        self.assertEqual(result["status"], "source_error")
        self.assertEqual(result["sources_available"], 0)
        self.assertEqual(result["cases"][0]["status"], "source_error")

    def test_stale_source_is_not_claimed_as_mismatch(self):
        result = hs.evaluate(graph(updated="older"), study(), fetch=lambda repo, num: {
            "body": "scanned documents", "updated_at": "newer", "url": "https://example.org"})
        self.assertEqual(result["cases"][0]["status"], "stale_graph_node")
        self.assertEqual(result["exact_source_parity"], 0)

    def test_bad_gold_is_diagnosed(self):
        result = hs.evaluate(graph(), study(), fetch=lambda repo, num: {
            "body": "unrelated content", "updated_at": "2026-11-08", "url": "https://example.org"})
        self.assertEqual(result["status"], "source_error")
        self.assertEqual(result["cases"][0]["status"], "annotation_error")

    def test_candidate_not_counted_as_proven_link(self):
        links = hs.evidence_summary([
            {"source": "a", "target": "b", "status": "candidate"},
            {"source": "a", "target": "c", "status": "identifier_match"},
            {"source": "a", "target": "github:OpenEuroLLM/Taskboard#214", "status": "explicit_task_reference"},
        ], "a")
        self.assertEqual(links["sourced_link_count"], 1)
        self.assertEqual(links["candidate_count"], 1)
        self.assertEqual(links["sourced_targets"], ["c"])
        self.assertEqual(links["task_reference_count"], 1)

    def test_internal_task_edges_remain_separate_from_external_links(self):
        specimen = graph("scanned documents; see #214")
        specimen["edges"] = [{"source": "github:OpenEuroLLM/Taskboard#420",
                              "target": "github:OpenEuroLLM/Taskboard#214",
                              "status": "explicit_task_reference"}]
        result = hs.evaluate(specimen, study(), fetch=lambda repo, num: {
            "body": "scanned documents; see #214", "updated_at": "2026-11-08",
            "url": "https://github.com/OpenEuroLLM/Taskboard/issues/420"})
        self.assertEqual(result["linked_issues"], 0)
        self.assertEqual(result["task_linked_issues"], 1)
        self.assertIn("Resolved graph task targets: github:OpenEuroLLM/Taskboard#214", hs.markdown(result))


if __name__ == "__main__":
    unittest.main()
