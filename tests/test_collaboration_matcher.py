"""Offline tests: cross-organization matches, honest baseline, source drift."""

import datetime as dt
import json
import unittest
from copy import deepcopy
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import collaboration_matcher as cm


NOW = dt.datetime(2026, 11, 10, 10, 0, tzinfo=dt.timezone.utc)


def issue(repo, n, title, body="", *, state="open", created="2026-10-14T10:00:00Z", pr=False):
    kind = "pull" if pr else "issues"
    result = {
        "number": n, "html_url": f"https://github.com/{repo}/{kind}/{n}",
        "title": title, "body": body, "state": state,
        "created_at": created, "updated_at": "2026-11-09T00:00:00Z",
        "assignees": [{"login": "contributor"}], "comments": 0,
    }
    if pr:
        result["pull_request"] = {"url": f"https://api.github.com/repos/{repo}/pulls/{n}"}
    return result


class FakeGitHub:
    def __init__(self, registry, *, drift=False, full_page=False):
        self.items = {r: [] for r in registry["repositories"]}
        self.calls = []
        self.drift = drift
        self.full_page = full_page
        self.items["OpenEuroLLM/web-data-processing"] = [
            issue("OpenEuroLLM/web-data-processing", 7, "robots.txt",
                  "We want to adopt and adapt the previous robots.txt rules."),
            issue("OpenEuroLLM/web-data-processing", 6, "S2-S4 updates",
                  "Add OpenLID v3 integration and GlotLID v3 support."),
        ]
        self.items["hplt-project/HPLT-textpipes"] = [
            issue("hplt-project/HPLT-textpipes", 17,
                  "Coordinate robots.txt filtering",
                  "Earlier work processing captured robots.txt files.",
                  state="closed", created="2025-10-30T12:00:00Z"),
            issue("hplt-project/HPLT-textpipes", 19, "OpenLID v3 run",
                  "Earlier language detector integration.",
                  state="closed", created="2025-10-28T12:00:00Z"),
        ]
        self.items["LAION-AI/CLIP_benchmark"] = [
            issue("LAION-AI/CLIP_benchmark", 50, "Benchmark evaluation",
                  "General model evaluation, but no direct shared components."),
        ]

    def __call__(self, url):
        self.calls.append(url)
        part = urlparse(url)
        rest = part.path.removeprefix("/repos/").split("/")
        repo = "/".join(rest[:2])
        assert repo in self.items, repo
        if len(rest) == 3 and rest[2] == "issues":
            page = int(parse_qs(part.query)["page"][0])
            if self.full_page and repo == "OpenEuroLLM/Taskboard" and page == 1:
                return [issue(repo, i, f"Random item {i}") for i in range(1, 101)]
            return self.items[repo] if page == 1 else []
        if len(rest) == 4 and rest[2] == "issues":
            n = int(rest[3])
            row = deepcopy(next(x for x in self.items[repo] if x["number"] == n))
            if self.drift and n == 17:
                row["body"] += " updated after reading"
            return row
        raise AssertionError("Unknown test endpoint: " + url)


class MatcherTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(Path("collaboration_sources.json").read_text())
        self.config["min_score"] = 4.0

    def test_registry_bounded_and_multiple_organizations(self):
        cm.validate(self.config)
        self.assertEqual(len(self.config["repositories"]), 8)
        invalid = deepcopy(self.config)
        invalid["repositories"] = invalid["repositories"][:1]
        with self.assertRaises(ValueError):
            cm.validate(invalid)

    def test_historic_robots_task_is_found_without_handpicked_issue_pairs(self):
        fake = FakeGitHub(self.config)
        result = cm.build(self.config, fetch=fake, now=NOW)
        self.assertGreaterEqual(result["suggestions_count"], 1)
        pair = next(c for c in result["suggestions"]
                    if c["source"]["number"] == 7
                    and c["target"]["number"] == 17)
        self.assertEqual(pair["source"]["repo"], "OpenEuroLLM/web-data-processing")
        self.assertEqual(pair["target"]["repo"], "hplt-project/HPLT-textpipes")
        self.assertEqual(pair["classification"], "possible_prior_work")
        self.assertEqual(pair["validation"], "unreviewed_candidate_not_confirmed_reusable")
        self.assertEqual(pair["outreach"], "none")
        self.assertTrue(any(t["term"] == "robotstxt" for t in pair["matched_terms"]))
        self.assertTrue(all(t["source"]["excerpt"] and t["target"]["excerpt"]
                            for t in pair["matched_terms"]))
        self.assertGreater(result["shortlisted_sources_rechecked"], 0)
        self.assertEqual(result["human_quality_labels_collected"], 0)
        self.assertTrue(result["baseline"].startswith("unweighted IDF overlap"))

    def test_body_to_title_signal_is_not_lost(self):
        result = cm.build(self.config, fetch=FakeGitHub(self.config), now=NOW)
        pair = next(c for c in result["suggestions"]
                    if c["source"]["number"] == 6
                    and c["target"]["number"] == 19)
        token = next(t for t in pair["matched_terms"] if t["term"] == "openlid")
        self.assertEqual(token["source"]["field"], "body")
        self.assertEqual(token["target"]["field"], "title")

    def test_generic_evaluation_terms_alone_do_not_generate_collaboration(self):
        result = cm.build(self.config, fetch=FakeGitHub(self.config), now=NOW)
        self.assertFalse(any(c["source"]["repo"] == "LAION-AI/CLIP_benchmark"
                             for c in result["suggestions"]))

    def test_closed_pr_must_not_be_called_a_merged_fix(self):
        fake = FakeGitHub(self.config)
        repo = "hplt-project/warc2text-runner"
        fake.items[repo].append(issue(
            repo, 22, "robots.txt URL processing", "Handle robots.txt",
            state="closed", created="2025-06-01T00:00:00Z", pr=True
        ))
        result = cm.build(self.config, fetch=fake, now=NOW)
        pairs = [c for c in result["suggestions"] if c["target"]["kind"] == "pull_request"]
        self.assertTrue(pairs)
        self.assertTrue(all(c["validation"] == "unreviewed_candidate_not_confirmed_reusable"
                            for c in pairs))
        self.assertIn("not necessarily merged", result["limitations"])

    def test_original_issue_changed_before_recheck_aborts(self):
        with self.assertRaisesRegex(ValueError, "changed during audit"):
            cm.build(self.config, fetch=FakeGitHub(self.config, drift=True), now=NOW)

    def test_full_last_page_fails_closed(self):
        fake = FakeGitHub(self.config, full_page=True)
        config = deepcopy(self.config)
        config["max_pages_per_repo"] = 1
        with self.assertRaisesRegex(ValueError, "pagination cap"):
            cm.build(config, fetch=fake, now=NOW)

    def test_old_source_is_not_in_active_cohort(self):
        fake = FakeGitHub(self.config)
        for row in fake.items["OpenEuroLLM/web-data-processing"]:
            row["created_at"] = "2024-01-01T00:00:00Z"
        result = cm.build(self.config, fetch=fake, now=NOW)
        self.assertEqual(result["suggestions_count"], 0)
        self.assertEqual(result["source_candidates"], 1)  # LAION task remains active

    def test_only_cross_organization_pairs_are_suggested(self):
        result = cm.build(self.config, fetch=FakeGitHub(self.config), now=NOW)
        for row in result["suggestions"]:
            self.assertNotEqual(
                row["source"]["repo"].split("/")[0],
                row["target"]["repo"].split("/")[0]
            )

    def test_report_labels_are_not_precision_claims(self):
        result = cm.build(self.config, fetch=FakeGitHub(self.config), now=NOW)
        summary = cm.markdown(result)
        self.assertIn("not an LLM", summary)
        self.assertIn("does not establish improved precision", summary)
        self.assertIn("no messages sent", summary.lower())


if __name__ == "__main__":
    unittest.main()
