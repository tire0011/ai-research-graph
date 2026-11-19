import hashlib
import unittest

from decision_comment_packet import MAX_ISSUES, build_packet


REPO = "OpenEuroLLM/Taskboard"


def issue(number):
    return {
        "id": f"github:{REPO}#{number}",
        "type": "issue",
        "repository": REPO,
        "title": f"Issue {number}",
        "description": "Brief task description",
        "url": f"https://github.com/{REPO}/issues/{number}",
        "updated_at": "2026-11-14",
    }


def sample_comment(number, body):
    return {
        "id": number, "body": body, "updated_at": "2026-11-15T00:00:00Z",
        "html_url": f"https://github.com/{REPO}/issues/346#issuecomment-{number}",
        "user": {"login": "public-researcher"},
    }


class DecisionPacketTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "timestamp_utc": "frozen",
            "nodes": [issue(346), issue(341), issue(343)],
            "edges": [],
        }

    def test_selected_issue_comment_provenance_and_coverage(self):
        data = [sample_comment(100, "Experiment finished.")] 
        result = build_packet(
            self.graph, [issue(346)["id"]],
            fetch=lambda _url, **_kwargs: data,
        )
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["snapshot_timestamp_utc"], "frozen")
        self.assertEqual(result["comments_retrieved"], 1)
        self.assertEqual(result["issues"][0]["snapshot_comment_edges"], 0)
        self.assertEqual(result["issues"][0]["fetched_public_comments"], 1)
        self.assertEqual(result["issues"][0]["comments"][0]["sha256"],
                         hashlib.sha256(b"Experiment finished.").hexdigest())
        self.assertIn("Experiment finished.", result["issues"][0]["comments"][0]["body"])

    def test_comments_are_assigned_to_correct_issues(self):
        def fetch(url, **_):
            if "/346/comments?" in url:
                return [sample_comment(101, "Evaluation correction requested.")]
            if "/341/comments?" in url:
                return [{**sample_comment(102, "Analysis already done."),
                         "html_url": f"https://github.com/{REPO}/issues/341#issuecomment-102"}]
            raise AssertionError(url)

        result = build_packet(self.graph, [issue(346)["id"], issue(341)["id"]],
                              fetch=fetch)
        self.assertEqual([r["fetched_public_comments"] for r in result["issues"]], [1, 1])
        self.assertEqual(result["issues"][1]["comments"][0]["body"], "Analysis already done.")
        self.assertEqual(result["comments_retrieved"], 2)

    def test_bounded_unknown_duplicate_and_empty_rejected(self):
        with self.assertRaisesRegex(ValueError, "Select between"):
            build_packet(self.graph, [], fetch=lambda *_a, **_k: [])
        with self.assertRaisesRegex(ValueError, "Select between"):
            build_packet(self.graph, [issue(346)["id"]] * (MAX_ISSUES + 1),
                         fetch=lambda *_a, **_k: [])
        with self.assertRaisesRegex(ValueError, "Duplicate issue"):
            build_packet(self.graph, [issue(346)["id"], issue(346)["id"].lower()],
                         fetch=lambda *_a, **_k: [])
        with self.assertRaisesRegex(ValueError, "Not an indexed"):
            build_packet(self.graph, [issue(999)["id"]], fetch=lambda *_a, **_k: [])

    def test_fetch_failure_is_not_an_empty_result(self):
        def fail(*_args, **_kwargs):
            raise TimeoutError("upstream unavailable")

        with self.assertRaisesRegex(TimeoutError, "upstream unavailable"):
            build_packet(self.graph, [issue(346)["id"]], fetch=fail)

    def test_existing_snapshot_comment_edge_not_discarded(self):
        self.graph["edges"].append({
            "source": issue(346)["id"], "target": "github_comment:OpenEuroLLM/Taskboard#1",
            "status": "source_comment",
        })
        result = build_packet(self.graph, [issue(346)["id"]],
                              fetch=lambda *_a, **_k: [])
        self.assertEqual(result["issues"][0]["snapshot_comment_edges"], 1)
        self.assertEqual(result["issues"][0]["fetched_public_comments"], 0)


if __name__ == "__main__":
    unittest.main()
