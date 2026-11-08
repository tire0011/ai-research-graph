import json
import unittest
from pathlib import Path

import impact_study as impact


def fixture():
    study = json.loads(Path("impact_cases.json").read_text(encoding="utf-8"))
    nodes, body_lookup, comment_lookup = [], {}, {}
    for case in study["cases"]:
        repo, number = case["repo"], case["number"]
        body = "\n".join(e["needle"] for e in case["evidence"] if e["source"] == "body")
        node = {"id": f"github:{repo}#{number}", "type": "issue", "title": case["id"],
                "repository": repo, "description": body, "updated_at": "fixed", "state": "open",
                "url": f"https://github.com/{repo}/issues/{number}"}
        nodes.append(node)
        body_lookup[(repo, number)] = {"body": body, "updated_at": "fixed",
                                       "title": case["id"], "state": "open", "url": node["url"]}
        for e in case["evidence"]:
            if e["source"] == "comment":
                key = repo, e["comment_id"]
                comment_lookup.setdefault(key, []).append(e["needle"])
    comments = {key: {"body": "\n".join(needles), "updated_at": "fixed",
                      "url": f"https://github.com/{key[0]}/issues/1#issuecomment-{key[1]}"}
                for key, needles in comment_lookup.items()}
    graph = {"timestamp_utc": "fixed", "nodes": nodes, "edges": [
        {"source": "github:OpenEuroLLM/Taskboard#391", "target": "github:OpenEuroLLM/Taskboard#432",
         "status": "explicit_task_reference"}]}
    return graph, study, body_lookup, comments


class ImpactStudyTests(unittest.TestCase):
    def test_ten_cases_and_original_source_claims(self):
        graph, study, issues, comments = fixture()
        result = impact.evaluate(graph, study, fetch_issue=lambda repo, num: issues[(repo, num)],
                                 fetch_comment=lambda repo, num: comments[(repo, num)])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["verified"], 10)
        self.assertEqual(result["comments_verified"], len(comments))
        self.assertEqual(result["comment_dependent_cases"], 3)
        self.assertEqual(result["exact_snapshot_parity"], 10)
        self.assertTrue(result["cases"][3]["declared_dependency"]["graph_contains_literal_reference"])
        self.assertIn("not a speedup ranking", impact.markdown(result).lower())

    def test_missing_comment_phrase_is_source_error_not_negative(self):
        graph, study, issues, comments = fixture()
        comments[("OpenEuroLLM/Taskboard", 6121054773)]["body"] = "edited away"
        result = impact.evaluate(graph, study, fetch_issue=lambda repo, num: issues[(repo, num)],
                                 fetch_comment=lambda repo, num: comments[(repo, num)])
        self.assertEqual(result["status"], "source_error")
        self.assertEqual(result["verified"], 9)
        self.assertEqual(result["cases"][5]["status"], "source_error")

    def test_source_parity_distinct_from_evidence_verification(self):
        graph, study, issues, comments = fixture()
        graph["nodes"][0]["updated_at"] = "older"
        result = impact.evaluate(graph, study, fetch_issue=lambda repo, num: issues[(repo, num)],
                                 fetch_comment=lambda repo, num: comments[(repo, num)])
        self.assertEqual(result["verified"], 10)
        self.assertEqual(result["exact_snapshot_parity"], 9)
        self.assertEqual(result["cases"][0]["graph_status"], "stale_or_changed")

    def test_literal_reference_is_not_automatically_dependency(self):
        graph, study, issues, comments = fixture()
        graph["edges"].clear()
        result = impact.evaluate(graph, study, fetch_issue=lambda repo, num: issues[(repo, num)],
                                 fetch_comment=lambda repo, num: comments[(repo, num)])
        self.assertEqual(result["status"], "completed")
        self.assertFalse(result["cases"][3]["declared_dependency"]["graph_contains_literal_reference"])

    def test_duplicate_sample_rejected(self):
        graph, study, _, _ = fixture()
        study["cases"][1]["number"] = study["cases"][0]["number"]
        with self.assertRaisesRegex(ValueError, "ten distinct"):
            impact.evaluate(graph, study)


if __name__ == "__main__":
    unittest.main()
