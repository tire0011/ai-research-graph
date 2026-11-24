import datetime as dt
import unittest
from unittest.mock import patch

from discovered_source_triage import analyze, MAX_METADATA


class DiscoveredSourceTriageTests(unittest.TestCase):
    now = dt.datetime(2026, 11, 24, tzinfo=dt.timezone.utc)
    config = {"schema": 1, "actor": "tester", "max_issues_per_repo": 15,
              "candidate_checks_per_repo": 3, "max_new_suggestions": 5,
              "repositories": [{"repo": "Known/seed", "area": "research", "region": "EU"},
                               {"repo": "Another/seed", "area": "research", "region": "EU"}]}

    def snapshot(self, names):
        return {"schema": 2, "retrieved_at": self.now.isoformat(),
                "candidates": [{"url": "https://github.com/" + name, "evidence": []}
                               for name in names]}

    def fetch(self, url):
        owner, name = url.split("/")[-2:]
        return {"full_name": owner + "/" + name, "owner": {"login": owner},
                "description": "Multilingual dataset evaluation benchmark", "topics": ["nlp"],
                "license": {"spdx_id": "MIT"}, "has_issues": True,
                "pushed_at": "2026-11-23T00:00:00Z"}

    @patch("discovered_source_triage.build")
    def test_existing_pipeline_and_evidence(self, build):
        build.return_value = {"errors": [], "new_top5": [
            {"repository": "known/new", "labels": ["help wanted"], "title": "Fix parser",
             "issue_url": "https://github.com/known/new/issues/1"}]}
        result = analyze(self.config, self.snapshot(["Known/seed", "Known/new", "Unknown/new"]),
                         self.fetch, now=self.now)
        self.assertEqual(result["pool_size"], 2)
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0]["invitation_status"], "public_issue_label")
        self.assertEqual(result["tasks"][0]["affiliation_status"], "curated_owner_context_only")
        unknown = next(r for r in result["metadata"] if r["repo"] == "unknown/new")
        self.assertEqual(unknown["affiliation_status"], "unknown")
        self.assertEqual(result["topic_hypotheses"][0]["status"], "unverified_topic_overlap")
        self.assertIn("evaluation", result["topic_hypotheses"][0]["shared_areas"])
        self.assertEqual(len(result["topic_hypotheses"][0]["evidence"]), 2)
        scoped = build.call_args.args[0]
        self.assertTrue(all("UNVERIFIED" in r["region"] for r in scoped["repositories"]))
        self.assertEqual(len(self.config["repositories"]), 2)

    @patch("discovered_source_triage.build")
    def test_identity_gate_and_missing_license_does_not_hide_tasks(self, build):
        build.return_value = {"errors": [], "new_top5": [{"repository": "unknown/nolicense", "labels": [], "title": "Inspect issue", "issue_url": "https://github.com/unknown/nolicense/issues/1"}]}
        def fetch(url):
            row = self.fetch(url)
            if url.endswith("/bad"):
                row["full_name"] = "unrelated/repo"
            elif url.endswith("/nolicense"):
                row["license"] = None
            elif url.endswith("/archived"):
                row["archived"] = True
            return row
        result = analyze(self.config, self.snapshot(["known/bad", "unknown/nolicense", "third/archived"]),
                         fetch, now=self.now)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["issue_repositories"], ["unknown/nolicense"])
        self.assertEqual(result["tasks"][0]["reuse_status"], "license_review_required")
        self.assertIsNone(result["tasks"][0]["license_spdx"])
        self.assertEqual(result["filter_counts"]["unknown_license_among_topical"], 1)
        build.assert_called_once()

    @patch("discovered_source_triage.build")
    def test_rotation_and_distinct_owners(self, build):
        build.return_value = {"errors": [], "new_top5": []}
        names = [f"known/repo{i:02}" for i in range(30)] + ["unknown/one"]
        snapshot = self.snapshot(names)
        first = analyze(self.config, snapshot, self.fetch, now=self.now)
        self.assertEqual(len(first["selected"]), MAX_METADATA)
        self.assertIn("https://github.com/unknown/one", first["selected"])
        second = analyze(self.config, snapshot, self.fetch, previous=first,
                         now=self.now + dt.timedelta(days=7))
        self.assertFalse(set(first["selected"]) & set(second["selected"]))
        self.assertEqual(len(second["selected"]), MAX_METADATA)
        self.assertEqual(len(second["last_attempt"]), 2 * MAX_METADATA)
        self.assertEqual(len(first["last_attempt"]), MAX_METADATA)

    @patch("discovered_source_triage.build")
    def test_single_owner_still_reviews_issues(self, build):
        build.return_value = {"errors": [], "new_top5": []}
        result = analyze(self.config, self.snapshot(["known/new"]), self.fetch, now=self.now)
        self.assertEqual(result["tasks"], [])
        self.assertIsNotNone(result["issue_review"])
        self.assertTrue(build.call_args.kwargs["allow_single_owner"])
        self.assertEqual(result["topic_hypotheses"], [])

    @patch("discovered_source_triage.build")
    def test_topical_overlap_does_not_require_issues_or_license(self, build):
        def fetch(url):
            row = self.fetch(url)
            row["license"] = None
            row["has_issues"] = False
            return row
        result = analyze(self.config, self.snapshot(["known/one", "unknown/two"]),
                         fetch, now=self.now)
        self.assertEqual(len(result["topic_hypotheses"]), 1)
        self.assertEqual(result["issue_repositories"], [])
        self.assertEqual(result["filter_counts"]["technical_signals"], 2)
        build.assert_not_called()
