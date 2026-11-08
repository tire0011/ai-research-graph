import hashlib
import unittest
from pathlib import Path

from impact_enrichment import (github_comments_for_selected, selected_issue_ids,
                               source_claim_edges)
from research_graph import github_task_references, incomplete_essential_sources, quality_profile, report


def task(number, body=""):
    repo = "OpenEuroLLM/Taskboard"
    return {"id": f"github:{repo}#{number}", "type": "issue", "title": f"Task {number}",
            "repository": repo, "description": body,
            "url": f"https://github.com/{repo}/issues/{number}", "updated_at": "fixed"}


def comment(comment_id, body):
    return {"id": comment_id, "body": body, "updated_at": "fixed",
            "html_url": f"https://github.com/OpenEuroLLM/Taskboard/issues/433#issuecomment-{comment_id}",
            "user": {"login": "researcher"}}


class ImpactEnrichmentTests(unittest.TestCase):
    def test_selected_issue_ids_from_reviewed_manifest(self):
        ids = selected_issue_ids(Path(__file__).resolve().parents[1] / "impact_cases.json")
        self.assertEqual(len(ids), 10)
        self.assertIn("github:OpenEuroLLM/Taskboard#433", ids)

    def test_comment_nodes_are_source_hashed_and_linked(self):
        issue = task(433)
        contents = [comment(6121054773, "Feature ready; DPO fails due to OOM issues on LUMI")]
        nodes, edges = github_comments_for_selected([issue], [issue["id"]],
                                                    lambda *_args, **_kwargs: contents)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["id"], "github_comment:OpenEuroLLM/Taskboard#6121054773")
        self.assertEqual(nodes[0]["body_sha256"], hashlib.sha256(contents[0]["body"].encode()).hexdigest())
        self.assertEqual(edges[0]["status"], "source_comment")
        self.assertEqual(quality_profile([issue, *nodes], edges)["edges_with_missing_endpoints"], 0)
        claims = source_claim_edges([issue, *nodes], nodes, [])
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["status"], "reported_blocker")
        self.assertIn("neither independently", claims[0]["reason"])

    def test_explicit_dependency_separate_from_reference(self):
        source, upstream = task(391, "__Dependencies__\nIssue #432, required for comparison"), task(432)
        refs, _ = github_task_references([source, upstream])
        self.assertEqual(len(refs), 1)
        deps = source_claim_edges([source, upstream], [], refs)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0]["status"], "author_declared_dependency")
        self.assertEqual(deps[0]["target"], upstream["id"])
        self.assertEqual(len(deps[0]["source_sha256"]), 64)
        self.assertEqual(quality_profile([source, upstream], refs + deps)["duplicate_edge_pairs"], 0)
        rendered = report([source, upstream], refs + deps, {}, "fixed", None,
                          comment_collection={"status": "complete", "selected_issues": 2})
        self.assertIn("author-declared task dependencies: **1**", rendered)

    def test_generic_reference_and_negated_dependency_not_upgraded(self):
        upstream = task(432)
        for body in ("See #432", "__Dependencies__\nN/A, see #432 for context",
                     "This is not blocked by #432", "We are discussing #432's results",
                     "__Dependencies__\nRelated: https://github.com/OpenEuroLLM/Taskboard/issues/432",
                     "__Dependencies__\n- Other input\n- Downstream: further experiment #432"):
            with self.subTest(body=body):
                source = task(391, body)
                refs, _ = github_task_references([source, upstream])
                self.assertEqual(source_claim_edges([source, upstream], [], refs), [])

    def test_explicit_phrase_without_heading_counts_as_claim(self):
        source, upstream = task(391, "This run depends on #432."), task(432)
        refs, _ = github_task_references([source, upstream])
        self.assertEqual(len(source_claim_edges([source, upstream], [], refs)), 1)

    def test_no_oom_claim_from_ordinary_quality_comment(self):
        issue = task(442)
        nodes, _ = github_comments_for_selected([issue], [issue["id"]],
                                                lambda *_a, **_k: [comment(77, "Accuracy rose to 84.6%")])
        self.assertEqual(source_claim_edges([issue, *nodes], nodes, []), [])

    def test_comment_pagination_limit_is_failure_not_zero(self):
        issue = task(433)
        values = [comment(i, "public") for i in range(1, 101)]
        with self.assertRaisesRegex(ValueError, "pagination limit"):
            github_comments_for_selected([issue], [issue["id"]],
                                         lambda *_a, **_k: values, max_pages=1)

    def test_missing_issue_and_failed_api_are_explicit_errors(self):
        issue = task(433)
        with self.assertRaisesRegex(ValueError, "absent"):
            github_comments_for_selected([], [issue["id"]], lambda *_a, **_k: [])
        def failure(*_args, **_kwargs):
            raise TimeoutError("GitHub comments unavailable")
        with self.assertRaises(TimeoutError):
            github_comments_for_selected([issue], [issue["id"]], failure)
        self.assertEqual(incomplete_essential_sources({"GitHub selected issue comments": "timeout"}),
                         ["GitHub selected issue comments"])

    def test_malformed_comment_and_duplicate_ids_rejected(self):
        issue = task(433)
        with self.assertRaisesRegex(ValueError, "Invalid comment"):
            github_comments_for_selected([issue], [issue["id"]],
                                         lambda *_a, **_k: [{"id": "not-an-id", "body": "Hi"}])
        repeated = [comment(1, "First"), comment(1, "Duplicate")]
        with self.assertRaisesRegex(ValueError, "Duplicate comment"):
            github_comments_for_selected([issue], [issue["id"]],
                                         lambda *_a, **_k: repeated)


if __name__ == "__main__":
    unittest.main()
