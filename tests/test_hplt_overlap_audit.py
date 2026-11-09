"""Offline evidence and fail-closed tests for HPLT/OpenEuroLLM handoff audit."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlparse

import hplt_overlap_audit as audit


class FakeGitHub:
    def __init__(self, config, *, drift_issue=False, truncated=False, missing_phrase=False):
        self.config = config
        self.calls = []
        self.drift_issue = drift_issue
        self.truncated = truncated
        self.missing_phrase = missing_phrase
        self.reads = {}
        self.blobs = {}
        self.issues = {}
        self.head = "a" * 40
        for pair in config["code_pairs"]:
            for side in ("a", "b"):
                item = pair[side]
                self.blobs.setdefault(item["repo"], {})
                if not self.blobs[item["repo"]]:
                    self.blobs[item["repo"]][item["prefix"] + "common.sh"] = ("b" * 40, 128)
                    self.blobs[item["repo"]][item["prefix"] + "different.py"] = (
                        ("c" if side == "a" else "d") * 40, 100
                    )
                    self.blobs[item["repo"]][item["prefix"] + "__init__.py"] = ("e" * 40, 0)
        for pair in config["issue_pairs"]:
            for side in ("a", "b"):
                item = pair[side]
                self.issues.setdefault((item["repo"], item["number"]), {
                    "number": item["number"], "title": f"Task {item['number']}",
                    "body": f"Work on {item['phrase']} and investigate implementation",
                    "state": "open" if side == "a" else "closed",
                    "updated_at": "2026-11-09T00:00:00Z",
                    "closed_at": None if side == "a" else "2025-11-20T00:00:00Z",
                    "comments": 3,
                    "html_url": f"https://github.com/{item['repo']}/issues/{item['number']}",
                })

    def __call__(self, url):
        self.calls.append(url)
        path = urlparse(url).path
        parts = path.removeprefix("/repos/").split("/")
        repo = "/".join(parts[:2])
        if "/branches/" in path:
            return {"commit": {"sha": self.head}}
        if "/git/trees/" in path:
            return {"truncated": self.truncated, "tree": [
                {"type": "blob", "path": p, "sha": sha, "size": size}
                for p, (sha, size) in self.blobs[repo].items()
            ]}
        if "/issues/" in path:
            number = int(parts[-1])
            key = (repo, number)
            self.reads[key] = self.reads.get(key, 0) + 1
            issue = deepcopy(self.issues[key])
            if self.drift_issue and self.reads[key] == 2:
                issue["body"] += " edited after initial read"
            if self.missing_phrase:
                issue["body"] = "unrelated topic"
            return issue
        raise ValueError("Unexpected fake endpoint: " + url)


class HpltOverlapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(Path("hplt_overlap_cases.json").read_text())

    def test_registry_is_explicitly_bounded(self):
        self.assertTrue(audit.validate(self.cases))
        self.assertEqual(len(self.cases["code_pairs"]), 2)
        self.assertEqual(len(self.cases["issue_pairs"]), 5)

    def test_code_reuse_and_historical_issues_are_separate_evidence(self):
        fake = FakeGitHub(self.cases)
        result = audit.build(self.cases, fake)
        self.assertEqual(result["status"], "read_only_human_review")
        self.assertEqual(result["pinned_trees"], 3)
        self.assertEqual(result["unique_issues_checked"], 8)
        self.assertEqual(len(result["code_pairs"]), 2)
        self.assertEqual(len(result["issue_pairs"]), 5)
        for item in result["code_pairs"]:
            self.assertEqual(item["identical_nontrivial"], 1)
            self.assertEqual(item["identical_trivial"], 1)
            self.assertEqual(item["different_blobs"], 1)
            self.assertTrue(all("/blob/" + ("a" * 40) + "/" in f["a_url"] for f in item["files"]))
        for item in result["issue_pairs"]:
            self.assertEqual(item["duplicate_work"], "not_established")
            self.assertEqual(item["review_priority"], "inspect_prior_work")
            self.assertEqual(item["outreach"], "none")
            self.assertEqual(len(item["a"]["body_sha256"]), 64)
        self.assertTrue(all(n == 2 for n in fake.reads.values()))
        report = audit.markdown(result)
        self.assertIn("not established", report.lower())
        self.assertIn("common-crawl-lumio", report)

    def test_no_matching_phrase_refuses_to_report(self):
        with self.assertRaisesRegex(ValueError, "Required phrase absent"):
            audit.build(self.cases, FakeGitHub(self.cases, missing_phrase=True))

    def test_issue_changed_between_reads_refuses_to_report(self):
        with self.assertRaisesRegex(ValueError, "Issue changed"):
            audit.build(self.cases, FakeGitHub(self.cases, drift_issue=True))

    def test_truncated_tree_refuses_to_report(self):
        with self.assertRaisesRegex(ValueError, "Truncated"):
            audit.build(self.cases, FakeGitHub(self.cases, truncated=True))

    def test_duplicate_pair_or_unbounded_case_list_rejected(self):
        broken = deepcopy(self.cases)
        broken["issue_pairs"][1]["id"] = broken["issue_pairs"][0]["id"]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            audit.validate(broken)
        broken = deepcopy(self.cases)
        broken["code_pairs"] *= 9
        with self.assertRaisesRegex(ValueError, "Invalid bounded"):
            audit.validate(broken)

    def test_closed_issue_does_not_imply_fix(self):
        fake = FakeGitHub(self.cases)
        key = ("hplt-project/HPLT-textpipes", 9)
        fake.issues[key]["state"] = "open"
        fake.issues[key]["closed_at"] = None
        result = audit.build(self.cases, fake)
        item = next(x for x in result["issue_pairs"] if x["id"] == "common-crawl-lumio")
        self.assertEqual(item["review_priority"], "manual_review")
        self.assertEqual(item["duplicate_work"], "not_established")


if __name__ == "__main__":
    unittest.main()
