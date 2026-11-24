"""Offline tests for multi-organization EU AI discovery and conservative states."""

import copy
import unittest
from urllib.parse import urlparse

import eu_opportunity_discovery as d


def registry():
    return {
        "schema": 1, "actor": "tire0011",
        "max_issues_per_repo": 5, "candidate_checks_per_repo": 3,
        "max_new_suggestions": 5,
        "repositories": [
            {"repo": "openaire/iis", "area": "metadata", "region": "EU"},
            {"repo": "OpenEuroLLM/oellm-eval", "area": "evaluation", "region": "EU"},
            {"repo": "kyutai-labs/moshi", "area": "audio", "region": "France"},
        ],
    }


class GitHubFixture:
    def __init__(self):
        self.data = {}
        for repo in ("openaire/iis", "OpenEuroLLM/oellm-eval", "kyutai-labs/moshi"):
            items = []
            for number in range(1, 6):
                item = {
                    "number": number, "state": "open",
                    "title": "Fix reproducible evaluation bug" if number == 1 else
                             f"Document missing test behavior {number}",
                    "body": "Reproduction steps and expected behavior",
                    "updated_at": "2026-11-21T00:00:00Z",
                    "html_url": f"https://github.com/{repo}/issues/{number}",
                    "comments": 0, "assignees": [], "labels": [],
                    "user": {"login": "maintainer"},
                }
                items.append(item)
                self.data[(repo, number)] = item
        self.data[("openaire/iis", 1)]["comments"] = 1
        self.data[("openaire/iis", 1)]["assignees"] = []
        self.data[("openaire/iis", 2)]["assignees"] = [{"login": "someone"}]
        self.data[("openaire/iis", 2)]["labels"] = [{"name": "help wanted"}]
        self.comments = {
            ("openaire/iis", 1): [{
                "html_url": "https://github.com/openaire/iis/issues/1#issuecomment-5",
                "user": {"login": "tire0011"}, "body": "I reviewed this",
            }]
        }
        self.calls = []
        self.partial = False
        self.fail_timeline = False

    def __call__(self, url):
        self.calls.append(url)
        path = urlparse(url).path.split("/")
        repo = "/".join(path[2:4])
        if path[4] == "issues" and len(path) == 5:
            return [copy.deepcopy(self.data[(repo, n)]) for n in range(1, 6)]
        number = int(path[5])
        if len(path) == 6:
            return copy.deepcopy(self.data[(repo, number)])
        if path[6] == "comments":
            return [] if self.partial else copy.deepcopy(self.comments.get((repo, number), []))
        if path[6] == "timeline":
            if self.fail_timeline:
                raise ValueError("unavailable timeline")
            return []
        raise ValueError(f"Unexpected URL: {url}")


class ReviewedSourceExpansionTests(unittest.TestCase):
    def test_source_registry_includes_multiple_european_ai_ecosystems(self):
        import json
        from pathlib import Path
        config = json.loads((Path(__file__).resolve().parents[1] /
                             "eu_opportunity_sources.json").read_text(encoding="utf-8"))
        d.validate(config)
        repos = {row["repo"] for row in config["repositories"]}
        expected = {
            "Helsinki-NLP/OpusFilter",
            "Helsinki-NLP/Tatoeba-Challenge",
            "Pleias/Pleias-RAG-Library",
            "kyutai-labs/hibiki",
            "OpenEuroLLM/JudgeArena",
            "OpenEuroLLM/oellm-autoexp",
        }
        self.assertTrue(expected.issubset(repos))
        self.assertEqual(len(config["repositories"]), 19)
        self.assertGreaterEqual(len({repo.split("/")[0] for repo in repos}), 8)
        self.assertTrue(all(item.get("repository_url") ==
                            "https://github.com/" + item["repo"]
                            for item in config["repositories"]
                            if item["repo"] in expected))


class RegistryTests(unittest.TestCase):
    def test_multi_org_registry_required(self):
        cfg = registry()
        d.validate(cfg)
        cfg["repositories"][2]["repo"] = cfg["repositories"][0]["repo"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            d.validate(cfg)

    def test_single_owner_requires_explicit_opt_in(self):
        cfg = registry()
        cfg["repositories"] = [cfg["repositories"][0]]
        with self.assertRaises(ValueError):
            d.validate(cfg)
        d.validate(cfg, allow_single_owner=True)
        result = d.build(cfg, GitHubFixture(), allow_single_owner=True)
        self.assertEqual(result["sources"], 1)
        self.assertEqual(result["sampled_issues"], 5)

    def test_reject_overlarge_registry_and_fetches(self):
        cfg = registry()
        cfg["candidate_checks_per_repo"] = 101
        with self.assertRaisesRegex(ValueError, "candidate_checks"):
            d.validate(cfg)

    def test_repository_listing_ignores_pull_requests(self):
        repo = "openaire/iis"
        def fetch(_):
            return [
                {"number": 1, "state": "open", "title": "Bug",
                 "body": "broken", "updated_at": "today",
                 "html_url": f"https://github.com/{repo}/issues/1"},
                {"number": 2, "pull_request": {}, "state": "open",
                 "title": "PR", "updated_at": "today",
                 "html_url": f"https://github.com/{repo}/issues/2"},
            ]
        self.assertEqual([x["number"] for x in d.list_recent(fetch, repo, 5)], [1])


class CrossProjectTests(unittest.TestCase):
    def test_existing_comment_is_follow_up_not_new(self):
        result = d.build(registry(), GitHubFixture())
        card = next(c for c in result["all_reviewed"]
                    if c["repository"] == "openaire/iis" and c["issue_number"] == 1)
        self.assertEqual(card["state"]["status"], "follow_up")
        self.assertNotIn(card["issue_url"], [c["issue_url"] for c in result["new_top5"]])

    def test_assigned_issue_not_new(self):
        result = d.build(registry(), GitHubFixture())
        card = next(c for c in result["all_reviewed"]
                    if c["repository"] == "openaire/iis" and c["issue_number"] == 2)
        self.assertEqual(card["state"]["status"], "in_progress")

    def test_new_shortlist_caps_five_and_is_cross_organization(self):
        result = d.build(registry(), GitHubFixture())
        self.assertEqual(result["sources"], 3)
        self.assertEqual(result["sampled_issues"], 15)
        self.assertLessEqual(len(result["new_top5"]), 5)
        self.assertTrue(result["new_top5"])
        self.assertTrue({c["repository"] for c in result["all_reviewed"]}.issuperset(
            {"openaire/iis", "OpenEuroLLM/oellm-eval", "kyutai-labs/moshi"}))
        self.assertEqual(len(result["all_reviewed"]), 9)
        self.assertEqual(result["errors"], [])
        self.assertIn("Same-source plain-title baseline", d.markdown(result))

    def test_incomplete_comment_evidence_never_returns_new(self):
        gh = GitHubFixture()
        gh.partial = True
        result = d.build(registry(), gh)
        c = next(c for c in result["all_reviewed"]
                 if c["repository"] == "openaire/iis" and c["issue_number"] == 1)
        self.assertEqual(c["state"]["status"], "needs_review")
        self.assertTrue(result["errors"])

    def test_missing_pr_context_never_returns_new(self):
        gh = GitHubFixture()
        gh.fail_timeline = True
        result = d.build(registry(), gh)
        self.assertEqual(result["new_top5"], [])
        self.assertTrue(all(c["state"]["status"] == "needs_review"
                            for c in result["all_reviewed"]))

    def test_changed_issue_is_quarantined(self):
        gh = GitHubFixture()
        original = gh.__call__
        def changed(url):
            value = original(url)
            if "/issues/1" in url and "timeline" not in url:
                value["updated_at"] = "changed"
            return value
        result = d.build(registry(), changed)
        self.assertTrue(any(c["state"]["status"] == "needs_review"
                            for c in result["all_reviewed"]))

    def test_old_unassigned_issues_require_fresh_confirmation(self):
        gh = GitHubFixture()
        for number in range(1, 6):
            gh.data[("kyutai-labs/moshi", number)]["updated_at"] = (
                "2024-01-01T00:00:00Z")
        result = d.build(registry(), gh)
        selected = [c for c in result["all_reviewed"]
                    if c["repository"] == "kyutai-labs/moshi"]
        self.assertTrue(selected)
        self.assertTrue(all(c["state"]["status"] == "needs_review"
                            for c in selected))
        self.assertTrue(all(c["state"]["reason"] ==
                            "stale_issue_requires_maintainer_reconfirmation"
                            for c in selected))

    def test_support_questions_are_not_contribution_tasks(self):
        gh = GitHubFixture()
        for number in range(1, 6):
            gh.data[("kyutai-labs/moshi", number)]["labels"] = [
                {"name": "question"}]
        result = d.build(registry(), gh)
        selected = [c for c in result["all_reviewed"]
                    if c["repository"] == "kyutai-labs/moshi"]
        self.assertTrue(selected)
        self.assertTrue(all(c["state"]["reason"] ==
                            "question_not_confirmed_implementation_task"
                            for c in selected))
        self.assertFalse(any(c["repository"] == "kyutai-labs/moshi"
                             for c in result["new_top5"]))

    def test_issue_dates_must_be_timezone_aware(self):
        import datetime as dt
        with self.assertRaises(ValueError):
            d.is_stale("2026-11-21T12:00:00")
        self.assertFalse(d.is_stale(
            "2026-11-20T12:00:00Z",
            now=dt.datetime(2026, 11, 21, tzinfo=dt.timezone.utc)))
        self.assertTrue(d.is_stale(
            "2024-01-01T00:00:00Z",
            now=dt.datetime(2026, 11, 21, tzinfo=dt.timezone.utc)))

    def test_no_writes_or_notifications(self):
        gh = GitHubFixture()
        d.build(registry(), gh)
        self.assertTrue(all(u.startswith("https://api.github.com/repos/") for u in gh.calls))


if __name__ == "__main__":
    unittest.main()
