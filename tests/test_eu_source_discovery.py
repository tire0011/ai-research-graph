import datetime as dt
import unittest
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
        result = discover(self.config, fetch=self.fetch, now=self.now)
        self.assertEqual(len(result["candidates"]), 3)
        self.assertEqual(len(result["verified_references"]), 2)
        self.assertTrue(all(c["verification_status"] == "unknown" for c in result["candidates"]))
        self.assertFalse(result["errors"])
        again = discover(self.config, fetch=self.fetch, now=self.now, previous=result)
        self.assertFalse(any(c["new"] for c in again["candidates"]))

    def test_partial_failure(self):
        def fetch(url):
            if "api.github.com" in url:
                raise TimeoutError()
            return self.fetch(url)
        result = discover(self.config, fetch=fetch, now=self.now)
        self.assertTrue(result["errors"])
        self.assertTrue(result["candidates"])

    def test_pagination(self):
        def fetch(url):
            if "api.github.com" in url and "page=1" in url:
                return [{"full_name": f"Example/repo{i}"} for i in range(30)]
            return []
        result = discover(self.config, fetch=fetch, now=self.now)
        self.assertEqual(result["requests"], 4)
        self.assertEqual(len(result["candidates"]), 30)
