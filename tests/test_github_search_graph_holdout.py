"""Offline contract/regression tests for real GitHub Search API holdout."""

import copy
import datetime as dt
import json
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import github_search_graph_holdout as s

ROOT = Path(__file__).resolve().parents[1]
NOW = dt.datetime(2026, 11, 21, 17, tzinfo=dt.timezone.utc)


def setup():
    cfg = json.loads((ROOT / "studies/github_search_graph_holdout_20261121/config.json")
                     .read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "eu_opportunity_sources.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "studies/eu_opportunity_quality_20261121/reviews.json")
                        .read_text(encoding="utf-8"))
    return cfg, registry, ledger


class API:
    """Complete API fixture; no external requests and no writes."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.issues = {}
        self.urls = []
        self.malformed_search = False
        self.bad_issue = None
        self.fail_timeline = False
        self.blocked_issue = None
        self.prior_work_issue = None
        self.assigned_issue = None

        for k, plan in enumerate(s.search_queries(cfg)):
            repo = plan["repositories"][0]
            number = 900 + k
            url = f"https://github.com/{repo}/issues/{number}"
            row = {
                "html_url": url, "number": number, "state": "open",
                "title": ("Fix failing test in src/score.py" if k == 0
                          else f"Reproduce scoring bug {k}"),
                "body": ("Steps to reproduce. See src/score.py and test case. "
                         "Related https://github.com/example/other/issues/33. "
                         "Dataset https://huggingface.co/datasets/eu/data."),
                "updated_at": "2026-11-18T00:00:00Z",
                "comments": 0, "labels": [], "assignees": [],
                "user": {"login": "maintainer"},
            }
            self.issues[url] = row
            plan["fixture_url"] = url
        self.plans = s.search_queries(cfg)
        for k, p in enumerate(self.plans):
            p["fixture_url"] = list(self.issues)[k]

    def __call__(self, url):
        self.urls.append(url)
        parts = urlparse(url)
        params = parse_qs(parts.query)
        if parts.path == "/search/issues":
            if self.malformed_search:
                return {"total_count": 1, "incomplete_results": True, "items": []}
            query = params.get("q", [""])[0]
            plan = next(p for p in self.plans if p["query"] == query)
            return {"total_count": 1, "incomplete_results": False,
                    "items": [copy.deepcopy(self.issues[plan["fixture_url"]])]}
        if parts.path.endswith("/timeline"):
            if self.fail_timeline:
                raise OSError("rate limit")
            return []
        if parts.path.endswith("/comments"):
            return []
        if "/contents/" in parts.path:
            return {"type": "file", "sha": "b" * 40,
                    "html_url": "https://github.com/" + (
                        "/".join(parts.path.split("/")[2:4])) +
                    "/blob/deadbeef/src/score.py"}
        if "/issues/" in parts.path:
            values = parts.path.split("/")
            repo = "/".join(values[2:4])
            number = values[5]
            link = f"https://github.com/{repo}/issues/{number}"
            doc = copy.deepcopy(self.issues[link])
            if link == self.bad_issue:
                doc["updated_at"] = "2026-11-19T00:00:00Z"
            if link == self.blocked_issue:
                doc["body"] += " This needs HPC / SLURM compute."
            if link == self.prior_work_issue:
                doc["body"] += " I have implemented this."
            if link == self.assigned_issue:
                doc["assignees"] = [{"login": "other"}]
            return doc
        raise ValueError(f"Unexpected API endpoint: {url}")


class StudyContracts(unittest.TestCase):
    def test_preregistered_repos_queries_are_real_github_search(self):
        cfg, registry, ledger = setup()
        s.check_config(cfg, registry)
        self.assertEqual(len(s.search_queries(cfg)), 8)
        self.assertTrue(all(x["url"].startswith(
            "https://api.github.com/search/issues?q=")
            for x in s.search_queries(cfg)))
        self.assertEqual(len(cfg["repository_scope"]), 19)
        self.assertEqual(cfg["search_terms"], ["bug", "test"])

    def test_source_scope_change_rejected(self):
        cfg, registry, _ = setup()
        cfg["repository_scope"] = cfg["repository_scope"][:-1]
        with self.assertRaisesRegex(ValueError, "Repository scope changed"):
            s.check_config(cfg, registry)

    def test_api_incomplete_is_error_not_zero_opportunities(self):
        cfg, _, _ = setup()
        gh = API(cfg)
        gh.malformed_search = True
        with self.assertRaisesRegex(ValueError, "Incomplete GitHub Search API"):
            s.collect_search(cfg, gh)

    def test_identical_retrieval_pool_baseline_and_graph(self):
        cfg, registry, ledger = setup()
        gh = API(cfg)
        result = s.build(cfg, registry, ledger, gh, now=NOW)
        self.assertEqual(result["raw_search_candidates"], 8)
        self.assertEqual(result["same_pool_count"], 8)
        self.assertEqual(result["deeply_verified"], 8)
        self.assertEqual(len(result["github_search_baseline_top5"]), 5)
        self.assertEqual(len(result["graph_enriched_top5"]), 5)
        self.assertTrue(set(result["github_search_baseline_top5"]).issubset(
            result["query_pool_urls"]))
        self.assertTrue(set(result["graph_enriched_top5"]).issubset(
            result["query_pool_urls"]))
        self.assertEqual(result["comparison"]["verified_quality_difference"], None)
        self.assertEqual(result["status"], "review_pending")
        self.assertTrue(any("/search/issues?" in u for u in gh.urls))
        self.assertFalse(any("/issues?state=open" in u for u in gh.urls))
        self.assertEqual(result["past_review_exclusions"], 0)

    def test_already_reviewed_issues_are_excluded_without_loading_labels(self):
        cfg, registry, ledger = setup()
        gh = API(cfg)
        ledger["additional_cohorts"][0]["reviews"][0]["issue_url"] = list(gh.issues)[0]
        # Exclusion is based only on URL; the prior review's tier never enters scoring.
        result = s.build(cfg, registry, ledger, gh, now=NOW)
        self.assertEqual(result["past_review_exclusions"], 1)
        self.assertNotIn(list(gh.issues)[0], result["query_pool_urls"])

    def test_typed_links_do_not_assert_dependencies(self):
        edges = s.extract_context(
            "See https://github.com/eco/repo/issues/5 and "
            "https://huggingface.co/datasets/eco/data, doi:10.1234/foobar",
            [])
        self.assertTrue(edges)
        self.assertTrue(all(x["interpretation"] == "literal_mention_only" for x in edges))

    def test_confirmed_file_path_is_only_existence_not_fix(self):
        cfg, _, _ = setup()
        gh = API(cfg)
        repo = next(iter(gh.issues)).split("/")[3:5]
        x = s.confirm_code_links(gh, "/".join(repo), "Fix src/score.py")
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0]["interpretation"], "file_exists_not_verified_fix_location")

    def test_missing_context_cannot_become_graph_recommendation(self):
        cfg, registry, ledger = setup()
        gh = API(cfg)
        gh.fail_timeline = True
        result = s.build(cfg, registry, ledger, gh, now=NOW)
        self.assertEqual(result["deeply_verified"], 0)
        self.assertEqual(result["graph_enriched_top5"], [])
        self.assertEqual(len(result["github_search_baseline_top5"]), 5)

    def test_changed_issue_source_not_confidently_ranked(self):
        cfg, registry, ledger = setup()
        gh = API(cfg)
        gh.bad_issue = list(gh.issues)[0]
        result = s.build(cfg, registry, ledger, gh, now=NOW)
        bad = next(x for x in result["all_inspected"] if x["issue_url"] == gh.bad_issue)
        self.assertEqual(bad["verification"], "failed")
        self.assertNotIn(gh.bad_issue, result["graph_enriched_top5"])

    def test_native_search_can_rank_issues_with_unavailable_work(self):
        cfg, registry, ledger = setup()
        gh = API(cfg)
        # Source matches must remain exact; mutate the search snapshot itself.
        first = list(gh.issues)[0]
        gh.issues[first]["body"] += " Needs SLURM HPC cluster."
        result = s.build(cfg, registry, ledger, gh, now=NOW)
        self.assertEqual(result["github_search_baseline_top5"][0], first)
        self.assertNotIn(first, result["graph_enriched_top5"])
        self.assertTrue(result["all_inspected"][0]["resource_fit"]["reasons"])

    def test_independent_review_must_be_complete_and_method_blind(self):
        cfg, registry, ledger = setup()
        result = s.build(cfg, registry, ledger, API(cfg), now=NOW)
        sheet = s.blind_sheet(result, cfg)
        self.assertTrue(sheet["blinded_to_method"])
        self.assertTrue(all("method" not in x for x in sheet["items"]))
        with self.assertRaisesRegex(ValueError, "Review incomplete"):
            s.judge(result, sheet)
        for row in sheet["items"]:
            row["rating"] = 2
            row["reviewer"] = "offline-test-reviewer"
            row["rationale"] = "I inspected the issue and found a bounded test request."
        evaluated = s.judge(result, sheet)
        self.assertEqual(evaluated["github_search_plausible_at5"], 5)
        self.assertEqual(evaluated["graph_enriched_plausible_at5"], 5)
        self.assertNotIn("graph_superiority", evaluated)


if __name__ == "__main__":
    unittest.main()
