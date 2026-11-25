import datetime as dt
import unittest
import urllib.error
from eu_source_discovery import canonical, discover

class SourceDiscoveryTests(unittest.TestCase):
    config = {"repositories": [{"repo": "Example/seed"}]}
    now = dt.datetime(2026, 11, 24, tzinfo=dt.timezone.utc)

    def fetch(self, url):
        if "api.github.com" in url:
            return [{"full_name": "Example/new", "homepage": "https://huggingface.co/datasets/other/data"}]
        if "/api/models" in url:
            return [{"id": "Example/model", "cardData": {"url": "https://github.com/Example/new"}}]
        return []

    def test_canonical(self):
        self.assertEqual(canonical("https://github.com/Example/New.git"), ("repository", "example/new"))
        self.assertIsNone(canonical("https://evil.example/Example/New"))

    def test_explicit_links_and_repeat(self):
        result = discover(self.config, fetch=self.fetch, now=self.now, max_follow=0)
        self.assertEqual(len(result["candidates"]), 3)
        self.assertEqual(len(result["verified_references"]), 2)
        self.assertTrue(all(c["verification_status"] == "unknown" for c in result["candidates"]))
        self.assertFalse(result["errors"])
        again = discover(self.config, fetch=self.fetch, now=self.now, max_follow=0, previous=result)
        self.assertFalse(any(c["new"] for c in again["candidates"]))

    def test_partial_failure(self):
        def fetch(url):
            if "api.github.com" in url:
                raise TimeoutError()
            return self.fetch(url)
        result = discover(self.config, fetch=fetch, now=self.now, max_follow=0)
        self.assertTrue(result["errors"])
        self.assertTrue(result["candidates"])

    def test_pagination(self):
        def fetch(url):
            if "api.github.com" in url and "page=1" in url:
                return [{"full_name": f"Example/repo{i}"} for i in range(30)]
            return []
        result = discover(self.config, fetch=fetch, now=self.now, max_follow=0)
        self.assertEqual(result["requests"], 4)
        self.assertEqual(len(result["candidates"]), 30)

    def test_cumulative_state_and_recursive_frontier(self):
        def fetch(url):
            if "/orgs/" in url:
                return [{"full_name": "Example/new", "homepage": "https://huggingface.co/other/model"}]
            if url.endswith("/api/models/other/model"):
                return {"id": "other/model", "cardData": {"url": "https://github.com/third/repo"}}
            if url.endswith("/repos/third/repo"):
                return {"full_name": "third/repo", "homepage": "https://huggingface.co/other/model"}
            return []
        first = discover(self.config, fetch=fetch, now=self.now, max_follow=1)
        self.assertFalse(first["errors"])
        self.assertEqual(first["pending"], ["https://github.com/third/repo"])
        self.assertEqual(first["expanded"], {"https://huggingface.co/other/model": "confirmed_public_metadata"})
        second = discover(self.config, fetch=fetch, previous=first,
                          now=self.now + dt.timedelta(days=7), max_follow=1)
        self.assertFalse(second["errors"])
        self.assertEqual(second["pending"], [])
        self.assertEqual(len(second["expanded"]), 2)
        self.assertEqual(len(second["verified_references"]), 3)
        self.assertFalse(any(x["new"] for x in second["candidates"]))
        self.assertEqual(second["new_reference_count"], 1)
        third = discover(self.config, fetch=lambda _: [], previous=second,
                         now=self.now + dt.timedelta(days=14), max_follow=1)
        self.assertEqual(len(third["candidates"]), 3)
        self.assertEqual(len(third["verified_references"]), 3)
        self.assertEqual(third["new_reference_count"], 0)
        self.assertFalse(any(x["new"] for x in third["candidates"]))
        self.assertEqual(first["pending"], ["https://github.com/third/repo"])

    def test_missing_target_does_not_block_other_candidates(self):
        def fetch(url):
            if "/orgs/" in url:
                return [{"full_name": "Example/new", "homepage": "https://github.com/other/missing"}]
            if "/repos/" in url:
                raise urllib.error.HTTPError(url, 404, "not found", None, None)
            return []
        result = discover(self.config, fetch=fetch, now=self.now)
        self.assertFalse(result["errors"])
        self.assertEqual(result["expanded"]["https://github.com/other/missing"], "not_found")
        target = next(x for x in result["candidates"] if x["url"].endswith("/missing"))
        self.assertEqual(target["detail_status"], "not_found")
        self.assertNotIn("identity_status", target)

    def test_failed_detail_retains_frontier(self):
        def fetch(url):
            if "/orgs/" in url:
                return [{"full_name": "Example/new", "homepage": "https://github.com/other/repo"}]
            if "/repos/" in url:
                raise TimeoutError()
            return []
        result = discover(self.config, fetch=fetch, now=self.now)
        self.assertTrue(result["errors"])
        self.assertEqual(result["pending"], ["https://github.com/other/repo"])
        self.assertEqual(result["expanded"], {})

    def test_old_schema_migration_and_reserved_paths(self):
        old = discover(self.config, fetch=self.fetch, now=self.now, max_follow=0)
        old["schema"] = 1
        old.pop("pending")
        result = discover(self.config, fetch=lambda _: [], previous=old, now=self.now, max_follow=0)
        self.assertEqual(set(result["pending"]), {"https://github.com/example/new",
                                                    "https://huggingface.co/datasets/other/data"})
        self.assertIsNone(canonical("https://github.com/topics/llm"))
        self.assertIsNone(canonical("https://huggingface.co/spaces/example"))
        self.assertEqual(canonical("https://huggingface.co/example/model.git"),
                         ("model", "example/model.git"))

    def test_human_referral_and_connection_review_remain_distinct(self):
        source = "https://github.com/example/seed/issues/1"
        config = {**self.config, "review_referrals": [
            {"id": "audit", "source_url": source,
             "urls": ["https://github.com/auditor/audits/tree/main/paper", "https://review.example.org/report"],
             "scope": "external quality tool; EU affiliation unverified", "review_only": True}],
            "connection_reviews": [{"id": "paper:example", "status": "already_handled", "note": "User reported"}]}
        result = discover(config, fetch=lambda _: [], now=self.now, max_follow=0)
        self.assertEqual(result["connection_reviews"], config["connection_reviews"])
        self.assertEqual(result["review_referrals"], config["review_referrals"])
        self.assertEqual(result["pending"], ["https://github.com/auditor/audits"])
        edge = result["verified_references"][0]
        self.assertEqual(edge["verification_status"], "human_reviewed")
        self.assertEqual(edge["source"], source)
        self.assertTrue(result["candidates"][0]["review_only"])
        self.assertIsNone(result["web_discovery"])
        again = discover(config, fetch=lambda _: [], now=self.now, previous=result, max_follow=0)
        self.assertEqual(again["new_reference_count"], 0)
        self.assertFalse(again["candidates"][0]["new"])
