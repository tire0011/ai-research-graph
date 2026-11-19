"""Offline checks of GitHub coordination context; absence is never proof."""

import unittest
from copy import deepcopy
from urllib.parse import urlparse

from collaboration_matcher import normalize_issue, report_issue
from collaboration_coordination import assess, build, reference


def item(repo, n, *, author, body="", title="WARC metadata", comments=None, assignees=()):
    url = f"https://github.com/{repo}/issues/{n}"
    comments = comments or []
    row = {
        "number": n, "title": title, "body": body, "state": "open",
        "html_url": url, "updated_at": "2026-11-10T06:00:00Z",
        "created_at": "2026-10-01T08:00:00Z", "comments": len(comments),
        "user": {"login": author}, "assignees": [{"login": a} for a in assignees],
    }
    return row, [
        {"user": {"login": person}, "body": text,
         "html_url": f"{url}#issuecomment-{i}"}
        for i, (person, text) in enumerate(comments, 100)
    ]


class FakeGitHub:
    def __init__(self, sources, *, drift=False, incomplete=False):
        self.index = sources
        self.drift = drift
        self.incomplete = incomplete
        self.calls = {}

    def __call__(self, url):
        path = urlparse(url).path
        path = path.removeprefix("/repos/")
        repo = "/".join(path.split("/")[:2])
        num = int(path.split("/")[3])
        key = repo, num
        if path.endswith("/comments"):
            return self.index[key][1][:-1] if self.incomplete else self.index[key][1]
        self.calls[key] = self.calls.get(key, 0) + 1
        data = deepcopy(self.index[key][0])
        if self.drift and self.calls[key] == 2:
            data["body"] += "new text"
        return data


def sample(sources):
    cards = []
    keys = list(sources)
    a, b = keys
    x = report_issue(normalize_issue(a[0], sources[a][0]))
    y = report_issue(normalize_issue(b[0], sources[b][0]))
    cards.append({
        "id": f"match:{x['id']}->{y['id']}",
        "source_id": x["id"], "target_id": y["id"],
        "source": x, "target": y,
        "matched_terms": [{"term": "warc"}],
    })
    return {"generated_at_utc": "2026-11-10T07:00:00Z", "suggestions": cards}


A = "OpenEuroLLM/web-data-processing", 2
B = "hplt-project/HPLT-textpipes", 9


class CoordinationTests(unittest.TestCase):
    def test_shared_person_is_public_context_not_proof_of_success(self):
        sources = {
            A: item(*A, author="nvanva", assignees=("nvanva",)),
            B: item(*B, author="oepen", comments=[("nvanva", "Progress here.")]),
        }
        fake = FakeGitHub(sources)
        result = build(sample(sources), fake)
        self.assertEqual(result["source_items_rechecked"], 2)
        self.assertEqual(result["comments_read"], 1)
        self.assertEqual(result["counts"]["shared_public_participants"], 1)
        p = result["pairs"][0]
        self.assertEqual(p["shared_people"][0]["login"], "nvanva")
        self.assertFalse(p["new_collaboration_confirmed"])
        self.assertTrue(p["requires_human_review"])
        self.assertEqual(fake.calls[A], 2)
        self.assertEqual(fake.calls[B], 2)
        self.assertIn("not proof", result["limitations"].lower())

    def test_explicit_issue_link_is_stronger_than_shared_person(self):
        sources = {
            A: item(*A, author="alice", comments=[
                ("alice", "See https://github.com/hplt-project/HPLT-textpipes/issues/9")
            ]),
            B: item(*B, author="bob"),
        }
        result = build(sample(sources), FakeGitHub(sources))
        p = result["pairs"][0]
        self.assertEqual(p["public_coordination_signal"], "direct_task_link")
        self.assertEqual(p["references"][0]["type"], "direct_task_link")
        self.assertTrue(p["references"][0]["source_url"].endswith("#issuecomment-100"))

    def test_generic_repository_reference_is_not_exact_issue_link(self):
        sources = {
            A: item(*A, author="alice", body="Read https://github.com/hplt-project/HPLT-textpipes/tree/main"),
            B: item(*B, author="bob"),
        }
        report = build(sample(sources), FakeGitHub(sources))
        self.assertEqual(report["pairs"][0]["public_coordination_signal"], "same_repository_mentioned")

    def test_lack_of_observed_public_link_never_asserts_novelty(self):
        sources = {A: item(*A, author="alice"), B: item(*B, author="bob")}
        result = build(sample(sources), FakeGitHub(sources))
        self.assertEqual(result["counts"]["no_direct_public_link_observed"], 1)
        self.assertFalse(result["pairs"][0]["new_collaboration_confirmed"])
        self.assertIn("not evidence of a new", result["limitations"])

    def test_exact_issue_matching_rejects_numeric_prefix(self):
        source = report_issue(normalize_issue(B[0], item(*B, author="bob")[0]))
        self.assertFalse(reference("https://github.com/hplt-project/HPLT-textpipes/issues/90", source, True))
        self.assertTrue(reference("hplt-project/HPLT-textpipes#9", source, True))

    def test_changed_text_fails_before_publishing(self):
        sources = {A: item(*A, author="alice"), B: item(*B, author="bob")}
        with self.assertRaisesRegex(ValueError, "Source changed"):
            build(sample(sources), FakeGitHub(sources, drift=True))

    def test_missing_comment_page_fails_closed(self):
        sources = {
            A: item(*A, author="alice", comments=[("alice", "One"), ("alice", "Two")]),
            B: item(*B, author="bob"),
        }
        with self.assertRaisesRegex(ValueError, "Incomplete GitHub comment list"):
            build(sample(sources), FakeGitHub(sources, incomplete=True))

    def test_duplicate_metadata_mismatch_rejected(self):
        sources = {A: item(*A, author="alice"), B: item(*B, author="bob")}
        report = sample(sources)
        different = deepcopy(report["suggestions"][0])
        different["source"]["updated_at"] = "2026-10-01T00:00:00Z"
        report["suggestions"].append(different)
        with self.assertRaisesRegex(ValueError, "Conflicting repeated"):
            build(report, FakeGitHub(sources))


if __name__ == "__main__":
    unittest.main()
