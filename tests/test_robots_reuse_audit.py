"""Offline tests for the HPLT robots.txt reuse trace and pinned Git source checks."""

import base64
import json
import unittest
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import robots_reuse_audit as audit


class FakeGitHub:
    def __init__(self, cases, *, alter_blob=False, drop_phrase=False, edit_issue=False):
        self.head = "a" * 40
        self.files = {}
        self.issues = {}
        self.calls = []
        self.issue_reads = {}
        self.alter_blob = alter_blob
        self.drop_phrase = drop_phrase
        self.edit_issue = edit_issue
        for source in cases["sources"]:
            repo = source["repo"]
            if source["kind"] == "file":
                content = "Documented pipeline step: " + source["phrase"] + "\nmore implementation detail\n"
                raw = content.encode("utf-8")
                self.files[(repo, source["path"])] = {
                    "raw": raw, "sha": audit.git_blob_sha(raw)
                }
            else:
                key = (repo, source["number"])
                self.issues[key] = {
                    "number": source["number"], "title": "Some workflow task",
                    "body": "The project proposes to " + source["phrase"] + ".",
                    "state": "open", "updated_at": "2026-11-10T00:00:00Z",
                    "closed_at": None, "comments": 0,
                    "html_url": "https://github.com/" + repo + "/issues/" + str(source["number"])
                }

    def __call__(self, url):
        self.calls.append(url)
        parsed = urlparse(url)
        assert parsed.path.startswith("/repos/"), url
        rest = parsed.path[len("/repos/"):]
        repo = "/".join(rest.split("/")[:2])
        tail = rest.split("/")[2:]
        if tail[0] == "branches":
            return {"commit": {"sha": self.head}}
        if tail[:2] == ["git", "trees"]:
            rows = [
                {"type": "blob", "path": path, "sha": v["sha"], "size": len(v["raw"])}
                for (r, path), v in self.files.items() if r == repo
            ]
            return {"truncated": False, "tree": rows}
        if tail[0] == "contents":
            path = "/".join(tail[1:])
            row = self.files[(repo, path)]
            raw = row["raw"] + (b"changed" if self.alter_blob else b"")
            assert parse_qs(parsed.query)["ref"][0] == self.head
            return {"type": "file", "encoding": "base64",
                    "content": base64.b64encode(raw).decode("ascii"),
                    "sha": row["sha"]}
        if tail[0] == "issues":
            number = int(tail[1])
            key = (repo, number)
            self.issue_reads[key] = self.issue_reads.get(key, 0) + 1
            out = deepcopy(self.issues[key])
            if self.edit_issue and self.issue_reads[key] == 2:
                out["body"] += " recently changed"
            if self.drop_phrase:
                out["body"] = "Different description altogether."
            return out
        raise ValueError("Unexpected GitHub endpoint: " + url)


class RobotsReuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(Path("robots_reuse_cases.json").read_text(encoding="utf-8"))

    def test_registry_is_bounded(self):
        self.assertTrue(audit.validate(self.cases))
        self.assertEqual(len(self.cases["sources"]), 12)
        self.assertGreaterEqual(len(self.cases["review_checks"]), 5)

    def test_audited_chain_has_stable_pinned_sources_and_no_automated_claim_of_fix(self):
        fake = FakeGitHub(self.cases)
        data = audit.build(self.cases, fake)
        self.assertEqual(data["sources_verified"], 12)
        self.assertEqual(data["pinned_repositories"], 3)
        self.assertEqual(data["duplicate_work"], "not_established")
        self.assertTrue(all(p["verified"] == "literal_match_in_source"
                            and p["runtime_behavior_verified"] is False
                            for p in data["evidence"]))
        self.assertTrue(all(p["head_sha"] == "a" * 40 for p in data["evidence"]
                            if p["source_kind"] == "pinned_git_file"))
        self.assertTrue(all(v == 2 for v in fake.issue_reads.values()))
        self.assertEqual(sum("/branches/" in x for x in fake.calls), 3)
        report = audit.markdown(data)
        self.assertIn("allowed.zst", report)
        self.assertIn("NOT", report.upper())

    def test_pinned_git_file_identity_is_verified(self):
        with self.assertRaisesRegex(ValueError, "Content does not match pinned Git tree"):
            audit.build(self.cases, FakeGitHub(self.cases, alter_blob=True))

    def test_missing_original_phrase_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Required literal source evidence absent"):
            audit.build(self.cases, FakeGitHub(self.cases, drop_phrase=True))

    def test_changed_issue_body_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Issue changed during audit"):
            audit.build(self.cases, FakeGitHub(self.cases, edit_issue=True))

    def test_registry_rejects_duplicate_and_unbounded_sources(self):
        dup = deepcopy(self.cases)
        dup["sources"].append(deepcopy(dup["sources"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate source"):
            audit.validate(dup)
        many = deepcopy(self.cases)
        many["sources"] *= 3
        with self.assertRaisesRegex(ValueError, "bounded source"):
            audit.validate(many)

    def test_issue_title_only_evidence_is_supported(self):
        cases = deepcopy(self.cases)
        issue = next(s for s in cases["sources"] if s["id"] == "existing-opt-out-task")
        fake = FakeGitHub(cases)
        fake.issues[(issue["repo"], issue["number"])]["title"] = issue["phrase"]
        fake.issues[(issue["repo"], issue["number"])]["body"] = "Text describes background only."
        result = audit.build(cases, fake)
        evidence = next(e for e in result["evidence"] if e["id"] == issue["id"])
        self.assertEqual(evidence["evidence_field"], "title")
        self.assertEqual(evidence["issue_state"], "open")
        self.assertEqual(evidence["sha256"], audit.hashlib.sha256(issue["phrase"].encode()).hexdigest())


if __name__ == "__main__":
    unittest.main()
