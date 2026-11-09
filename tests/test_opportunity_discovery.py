"""Offline tests of rotating issue selection, source parity and manual status tracking."""

import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import opportunity_discovery as od
import opportunity_feedback as fb


class FakeGitHub:
    def __init__(self):
        self.issues = {}
        self.comments = {}
        for number in range(1, 81):
            self.issues[number] = {
                "number": number, "state": "open", "title": f"Task {number}",
                "html_url": f"https://github.com/{od.REPO}/issues/{number}",
                "body": "Just a regular work item", "updated_at": "unchanged",
                "comments": 0, "assignees": [{"login": "Reviewer"}],
                "user": {"login": "Author"},
            }
        self.issues[19]["body"] = "We measured 9.5% faster in an early comparison."
        self.issues[20]["body"] = "__Dependencies__\nIssue #12"
        self.issues[21]["comments"] = 1
        self.comments[21] = [{
            "id": 777, "body": "DPO fails due to OOM on GPU.",
            "html_url": f"https://github.com/{od.REPO}/issues/21#issuecomment-777",
            "updated_at": "unchanged",
        }]
        self.calls = []
        self.edit_on_reread = False
        self.corrupt_comment_on_reread = False
        self.reads = {}

    def __call__(self, url):
        self.calls.append(url)
        path = urlparse(url).path
        query = parse_qs(urlparse(url).query)
        if path.endswith("/issues"):
            page = int(query["page"][0])
            return [self.issues[i] for i in range(1, 81)] if page == 1 else []
        if path.endswith("/comments/777"):
            result = dict(self.comments[21][0])
            if self.corrupt_comment_on_reread:
                result["body"] = "Edited to remove memory issue"
            return result
        if path.endswith("/comments"):
            issue_number = int(path.split("/")[-2])
            return list(self.comments.get(issue_number, []))
        number = int(path.split("/")[-1])
        self.reads[number] = self.reads.get(number, 0) + 1
        issue = dict(self.issues[number])
        if self.edit_on_reread and self.reads[number] == 2:
            issue["body"] = "Changed after sampling"
        return issue


class DiscoveryTests(unittest.TestCase):
    def test_sample_is_deterministic_rotating_and_excludes_original_cases(self):
        population = od.list_population(FakeGitHub())
        self.assertEqual(len(population), 80)
        selected = od.select(population, {1, 2, 3}, "2026-W46")
        self.assertEqual(selected, od.select(population, {1, 2, 3}, "2026-W46"))
        self.assertEqual(len(selected), 50)
        self.assertTrue({1, 2, 3}.isdisjoint(selected))
        self.assertNotEqual(selected, od.select(population, {1, 2, 3}, "2026-W47"))

    def test_insufficient_population_fails_instead_of_reducing_sample(self):
        with self.assertRaisesRegex(ValueError, "need 50"):
            od.select([{"number": 10}], set(), "seed")

    def test_classifier_keeps_exact_original_phrases(self):
        gh = FakeGitHub()
        speed = od.identify(gh.issues[19], [])["performance_mention"][0]
        self.assertIn(speed["quote"], gh.issues[19]["body"])
        self.assertEqual(speed["sha256"], od.digest(gh.issues[19]["body"]))
        dep = od.identify(gh.issues[20], [])["declared_dependency"][0]
        self.assertEqual(dep["target_issue"], 12)
        mem = od.identify(gh.issues[21], gh.comments[21])["reported_memory_issue"][0]
        self.assertEqual(mem["origin"], "issue_comment")
        self.assertNotIn("performance_mention", od.identify(gh.issues[20], []))

    def test_verified_cards_are_never_sent_and_feedback_is_preserved(self):
        gh = FakeGitHub()
        feedback = {f"github:{od.REPO}#21:reported_memory_issue": "reviewed"}
        result = od.build(gh, seed="2026-W46", feedback=feedback)
        self.assertEqual(result["sampled"], 50)
        self.assertEqual(result["verified_issue_reads"], 50)
        self.assertEqual(len({c["id"] for c in result["candidates"]}), len(result["candidates"]))
        self.assertTrue(all(c["sent"] is False for c in result["candidates"]))
        self.assertTrue(all(c["communication_status"] == "human_approval_required"
                            for c in result["candidates"]))
        self.assertTrue(all(c["review_status"] == feedback.get(c["id"], "new")
                            for c in result["candidates"]))
        self.assertTrue(all(len(e["sha256"]) == 64 for c in result["candidates"]
                            for e in c["evidence"]))
        self.assertIn("No messages were sent", od.markdown(result))
        self.assertTrue(any("/comments/777" in url for url in gh.calls))

    def test_edited_issue_fails_closed(self):
        gh = FakeGitHub()
        gh.edit_on_reread = True
        with self.assertRaisesRegex(ValueError, "changed during source verification"):
            od.build(gh, seed="2026-W46")

    def test_edited_comment_fails_closed(self):
        gh = FakeGitHub()
        gh.corrupt_comment_on_reread = True
        with self.assertRaisesRegex(ValueError, "Changed or invalid"):
            od.build(gh, seed="2026-W46")

    def test_partial_comment_list_fails_closed(self):
        gh = FakeGitHub()
        gh.comments[21] = []
        with self.assertRaisesRegex(ValueError, "partial comment listing"):
            od.build(gh, seed="2026-W46")

    def test_population_pagination_cap_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "page cap"):
            od.list_population(lambda _: [{"number": i} for i in range(100)])


class FeedbackTests(unittest.TestCase):
    def test_human_events_are_append_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            key = f"github:{od.REPO}#433:reported_memory_issue"
            fb.record(path, key, "reviewed", "tire0011", note="Read source")
            fb.record(path, key, "proposal_prepared", "tire0011")
            fb.record(path, key, "published", "tire0011",
                      reference_url=f"https://github.com/{od.REPO}/issues/433#issuecomment-99")
            fb.record(path, key, "response_received", "tire0011",
                      reference_url=f"https://github.com/{od.REPO}/issues/433#issuecomment-100")
            fb.record(path, key, "resolved", "tire0011",
                      reference_url=f"https://github.com/{od.REPO}/issues/433")
            self.assertEqual(fb.read_feedback(path)[key], "resolved")
            self.assertEqual(len(path.read_text().splitlines()), 5)
            with self.assertRaises(ValueError):
                fb.record(path, key, "reviewed", "tire0011")

    def test_published_requires_link_and_prior_human_review(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            key = f"github:{od.REPO}#433:reported_memory_issue"
            with self.assertRaises(ValueError):
                fb.record(path, key, "published", "tire0011")
            fb.record(path, key, "reviewed", "tire0011")
            fb.record(path, key, "proposal_prepared", "tire0011")
            with self.assertRaisesRegex(ValueError, "explicit GitHub reference"):
                fb.record(path, key, "published", "tire0011")
            self.assertEqual(len(path.read_text().splitlines()), 2)

    def test_bad_feedback_log_is_not_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            path.write_text("not json\n")
            with self.assertRaises(ValueError):
                fb.read_feedback(path)


if __name__ == "__main__":
    unittest.main()
