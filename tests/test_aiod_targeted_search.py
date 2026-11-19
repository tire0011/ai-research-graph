"""Offline API-contract and fail-closed tests for targeted AIoD queries."""

import datetime as dt
import json
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest.mock import patch

import aiod_targeted_search as search


NOW = dt.datetime(2026, 11, 11, 9, tzinfo=dt.timezone.utc)


def fake_source(url):
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)["search_query"][0]
    asset_type = parsed.path.rsplit("/", 1)[-1]
    return {
        "total_hits": 13, "limit": 1, "offset": 0,
        "resources": [{"identifier": f"{asset_type}-{query}",
                       "name": f"Research on {query}",
                       "description": {"plain": f"Methods related to {query}"},
                       "same_as": f"https://catalogue.example.org/{asset_type}/{query.replace(' ', '-')}/"}],
    }


class TargetedSearchTests(unittest.TestCase):
    def test_search_uses_official_get_endpoint_and_bounded_title_search(self):
        url = search.search_url("https://api.aiodp.eu", "projects", "model card", 5)
        parsed = urllib.parse.urlparse(url)
        self.assertEqual(parsed.path, "/search/projects")
        params = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(params["search_fields"], ["name"])
        self.assertEqual(params["search_query"], ["model card"])
        self.assertEqual(params["limit"], ["5"])
        self.assertEqual(params["get_all"], ["true"])
        with self.assertRaises(ValueError):
            search.search_url("https://untrusted.example", "projects", "model card", 5)
        with self.assertRaises(ValueError):
            search.search_url("https://api.aiodp.eu", "projects", "model card", 100)

    def test_rejects_unexpected_envelope(self):
        with self.assertRaisesRegex(ValueError, "envelope"):
            search.parse_search([{"identifier": "1"}], asset_type="projects",
                                host="https://api.aiodp.eu", url="test", limit=5)
        with self.assertRaisesRegex(ValueError, "pagination"):
            search.parse_search({"total_hits": 1, "offset": 2, "resources": []},
                                asset_type="projects", host="https://api.aiodp.eu",
                                url="test", limit=5)

    def test_fifteen_queries_fixed_before_results_and_no_collaboration_assertion(self):
        report = search.run(limit=1, fetch=fake_source, max_workers=2, now=NOW)
        self.assertEqual(report["query_count"], 15)
        self.assertEqual(len(report["targets"]), 5)
        self.assertEqual([t["github_issue"] for t in report["targets"]],
                         [445, 392, 353, 437, 360])
        self.assertEqual(report["targets"][0]["title_two_term_candidates"], 3)
        self.assertEqual(report["targets"][0]["retrieved_distinct_assets"], 3)
        self.assertTrue(all(r["collaboration_classification"] == "unreviewed"
                            for t in report["targets"] for r in t["candidates"]))
        self.assertTrue(all("description" not in r
                            for t in report["targets"] for r in t["candidates"]))
        self.assertFalse(report["novel_collaboration_confirmed"])
        self.assertEqual(report["outreach"], "none")

    def test_same_claimed_source_does_not_become_multiple_opportunities(self):
        def duplicated_source(url):
            payload = fake_source(url)
            payload["resources"][0]["same_as"] = "https://source.example.org/one"
            return payload
        report = search.run(limit=1, fetch=duplicated_source, now=NOW)
        self.assertTrue(all(t["retrieved_distinct_assets"] == 1
                            for t in report["targets"]))

    def test_partial_failed_query_leaves_previous_report_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            previous = search.run(limit=1, fetch=fake_source, now=NOW)
            search.write_success(previous, Path(folder))
            old = (Path(folder) / "TARGETED_SEARCH_RESULTS.json").read_bytes()
            def broken(url):
                if "datasets" in url:
                    raise OSError("offline")
                return fake_source(url)
            original_run = search.run
            with patch.object(search, "run", side_effect=lambda **_: original_run(
                limit=1, fetch=broken, now=NOW)):
                self.assertEqual(search.main(["--output", folder]), 1)
            self.assertEqual((Path(folder) / "TARGETED_SEARCH_RESULTS.json").read_bytes(), old)
            self.assertEqual(json.loads(old)["status"], "live_search_retrieval_only")


if __name__ == "__main__":
    unittest.main()
