import json
import tempfile
import unittest
from pathlib import Path

import opportunity_detector as od


def fixture():
    classes = ["reported_speedup_pending_validation", "explicit_upstream_dependency",
               "reported_memory_blocker"] + ["quality_hypothesis"] * 7
    cases = []
    for i, kind in enumerate(classes):
        num = 385 if i == 0 else 391 if i == 1 else 433 if i == 2 else 500 + i
        anchor = f"github:OpenEuroLLM/Taskboard#{num}"
        row = {"anchor_id": anchor, "title": f"Source task {num}",
               "status": "evidence_verified", "graph_status": "exact_parity", "live_state": "open",
               "evidence_class": kind, "source_url": f"https://github.com/OpenEuroLLM/Taskboard/issues/{num}",
               "source_sha256": "a" * 64, "candidate": f"Validate {num}",
               "next_check": f"Reproduce {num}", "issue_author": "Author-One", "assignees": [],
               "evidence": [{"url": f"https://github.com/OpenEuroLLM/Taskboard/issues/{num}",
                             "sha256": "b" * 64, "matched_text": "Original source phrase",
                             "meaning": "Claim reported by the source"}]}
        if i == 0:
            row["assignees"] = ["ReinforcedKnowledge"]
        if i == 1:
            row["declared_dependency"] = {"task_id": "github:OpenEuroLLM/Taskboard#432",
                                          "graph_contains_author_declared_dependency": True}
        if i == 2:
            row["graph_reported_blockers"] = ["github_comment:OpenEuroLLM/Taskboard#6121054773"]
        cases.append(row)
    return {"status": "completed", "selected": 10, "verified": 10,
            "graph_comments_exact": 4, "graph_comments_selected": 4,
            "snapshot_utc": "2026-11-09T00:00:00Z", "cases": cases}


class OpportunityDetectorTests(unittest.TestCase):
    def test_three_typed_proposals_are_source_linked_and_not_sent(self):
        result = od.build(fixture())
        self.assertEqual(result["status"], "review_only")
        self.assertEqual([o["issue_id"].rsplit("#", 1)[-1] for o in result["opportunities"]],
                         ["385", "391", "433"])
        first = result["opportunities"][0]
        self.assertEqual(first["contacts"], ["ReinforcedKnowledge"])
        self.assertEqual(first["contact_basis"], "github_issue_assignee")
        self.assertEqual(first["communication_status"], "human_review_required")
        self.assertFalse(first["sent"])
        self.assertEqual(len(first["evidence"][0]["sha256"]), 64)
        self.assertIn("**human approval required before any outreach**", od.markdown(result))

    def test_author_is_fallback_not_assignee(self):
        result = od.build(fixture())
        second = result["opportunities"][1]
        self.assertEqual(second["contacts"], ["Author-One"])
        self.assertEqual(second["contact_basis"], "issue_author_fallback")
        self.assertEqual(second["related_dependency"], "github:OpenEuroLLM/Taskboard#432")

    def test_unproven_dependency_or_blocker_is_not_a_lead(self):
        data = fixture()
        data["cases"][1]["declared_dependency"]["graph_contains_author_declared_dependency"] = False
        data["cases"][2]["graph_reported_blockers"] = []
        self.assertEqual(len(od.build(data)["opportunities"]), 1)

    def test_closed_issues_are_not_proposed(self):
        data = fixture()
        data["cases"][0]["live_state"] = "closed"
        self.assertEqual(len(od.build(data)["opportunities"]), 2)

    def test_stale_or_partial_audits_fail_closed(self):
        for mutate in (
            lambda d: d.update(status="source_error"),
            lambda d: d.update(graph_comments_exact=3),
            lambda d: d["cases"][0].update(graph_status="stale_or_changed"),
            lambda d: d.update(verified=9),
            lambda d: d["cases"][0]["evidence"][0].update(sha256="not-a-hash"),
        ):
            data = fixture()
            mutate(data)
            with self.assertRaises(ValueError):
                od.build(data)

    def test_cli_writes_only_successful_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "impact.json"
            input_path.write_text(json.dumps(fixture()), encoding="utf-8")
            self.assertEqual(od.main(["--impact", str(input_path), "--output", tmp]), 0)
            self.assertEqual(len(json.loads((Path(tmp) / "opportunities.json").read_text())
                                 ["opportunities"]), 3)
            input_path.write_text(json.dumps({"status": "source_error"}), encoding="utf-8")
            self.assertEqual(od.main(["--impact", str(input_path), "--output", tmp]), 1)


if __name__ == "__main__":
    unittest.main()
