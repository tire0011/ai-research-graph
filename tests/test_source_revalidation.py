import copy
import unittest

from source_revalidation import audit, pull_state, render_markdown, sha256


def manifest():
    return {
        "schema_version": 1,
        "kind": "public_pr_status_revalidation",
        "records": [
            {
                "id": "arena",
                "url": "https://github.com/OpenEuroLLM/oellm-eval/pull/174",
                "prior_status": "open",
                "prior_review_date": "2026-11-10",
                "origin": "results/COLLABORATION_REVIEW_NEXT_CASES.md",
            },
            {
                "id": "llamafactory",
                "url": "https://github.com/OpenEuroLLM/post-training/pull/65",
                "prior_status": "open",
                "prior_review_date": "2026-11-14",
                "origin": "results/interventions/DECISION_AUDIT_20261114.md",
            },
            {
                "id": "statebench",
                "url": "https://github.com/allenai/olmo-eval/pull/358",
                "prior_status": "merged",
                "prior_review_date": "2026-11-10",
                "origin": "results/COLLABORATION_REVIEW_NEXT_CASES.md",
            },
        ],
    }


def source(url):
    number = int(url.rsplit("/", 1)[-1])
    if number == 174:
        state, merged, closed, updated = "closed", "2026-11-11T13:20:25Z", "2026-11-11T13:20:25Z", "2026-11-11T13:51:04Z"
    elif number == 65:
        state, merged, closed, updated = "open", None, None, "2026-11-09T13:25:34Z"
    else:
        state, merged, closed, updated = "closed", "2026-10-01T18:36:04Z", "2026-10-01T18:36:04Z", "2026-10-01T18:36:05Z"
    return {
        "html_url": url.replace("https://api.github.com/repos/", "https://github.com/")
                      .replace("/pulls/", "/pull/"),
        "number": number, "state": state,
        "merged_at": merged, "closed_at": closed, "updated_at": updated,
    }


class SourceRevalidationTests(unittest.TestCase):
    def check(self, data=None, fetch=source):
        return audit(data or manifest(), fetch=fetch,
                     checked_at="2026-11-15T19:00:00+00:00")

    def test_detects_actual_later_merge_without_claiming_graph_gain(self):
        report = self.check()
        self.assertEqual(report["summary"]["selected"], 3)
        self.assertEqual(report["summary"]["source_verified"], 3)
        self.assertEqual(report["summary"]["changed_since_prior_review"], 1)
        self.assertEqual(report["summary"]["unchanged"], 2)
        self.assertEqual(report["summary"]["claim_disagreements"], 0)
        self.assertEqual(report["cases"][0]["status"],
                         "verified_status_change_after_prior_review")
        self.assertEqual(report["cases"][0]["live_status"], "merged")
        self.assertTrue(report["cases"][0]["requires_human_review"])
        self.assertFalse(report["summary"]["confirmed_graph_advantage"])
        self.assertIsNone(report["summary"]["measured_time_saved"])
        self.assertIn("not evidence of a graph speedup", render_markdown(report))
        self.assertEqual(report["manifest_sha256"], sha256(manifest()))

    def test_prior_claim_disagreement_not_misreported_as_later_change(self):
        data = manifest()
        data["records"][0]["prior_review_date"] = "2026-11-13"  # AFTER merge
        report = self.check(data)
        self.assertEqual(report["cases"][0]["status"], "source_claim_disagreement")
        self.assertEqual(report["summary"]["changed_since_prior_review"], 0)
        self.assertEqual(report["summary"]["claim_disagreements"], 1)

    def test_rejects_partial_fetch_even_if_others_were_verified(self):
        def failing(url):
            if url.endswith("/65"):
                raise TimeoutError("GitHub unavailable")
            return source(url)
        with self.assertRaisesRegex(TimeoutError, "GitHub unavailable"):
            self.check(fetch=failing)

    def test_rejects_identity_confusion(self):
        def wrong_identity(url):
            answer = source(url)
            answer["number"] = 999
            return answer
        with self.assertRaisesRegex(ValueError, "Unverifiable"):
            self.check(fetch=wrong_identity)

    def test_rejects_duplicate_ids_and_urls(self):
        data = manifest()
        data["records"][1]["id"] = "arena"
        with self.assertRaisesRegex(ValueError, "duplicate review ID"):
            self.check(data)
        data = manifest()
        data["records"][1]["url"] = data["records"][0]["url"]
        with self.assertRaisesRegex(ValueError, "duplicate PR URL"):
            self.check(data)

    def test_rejects_unchecked_or_unsafe_sources(self):
        data = manifest()
        data["records"][1]["url"] = "http://malicious.example/pull/2"
        with self.assertRaisesRegex(ValueError, "Invalid or duplicate PR URL"):
            self.check(data)
        data = manifest()
        data["records"][1]["origin"] = "../secrets.txt"
        with self.assertRaisesRegex(ValueError, "unsafe"):
            self.check(data)
        data = manifest()
        data["records"][1]["prior_review_date"] = "2026-11-16"
        with self.assertRaisesRegex(ValueError, "future"):
            self.check(data)

    def test_merge_state_requires_closed(self):
        with self.assertRaisesRegex(ValueError, "Inconsistent"):
            pull_state({"state": "open", "merged_at": "2026-11-11T00:00:00Z"})

    def test_closed_not_merged_not_confused_with_merge(self):
        data = manifest()
        def fetch(url):
            obj = source(url)
            if url.endswith("/174"):
                obj["merged_at"] = None
            return obj
        report = self.check(data, fetch=fetch)
        self.assertEqual(report["cases"][0]["live_status"], "closed")
        self.assertEqual(report["cases"][0]["status"],
                         "verified_status_change_after_prior_review")

    def test_cannot_spoof_merged_with_bad_source(self):
        def malformed(url):
            obj = source(url)
            obj["updated_at"] = None
            return obj
        with self.assertRaisesRegex(ValueError, "Missing PR update date"):
            self.check(fetch=malformed)


if __name__ == "__main__":
    unittest.main()
