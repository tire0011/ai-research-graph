import io
import unittest
import urllib.error
from unittest.mock import patch

import http_util
import research_graph


class HttpUtilTests(unittest.TestCase):
    def test_retries_transient_error_then_returns_json(self):
        calls = [urllib.error.HTTPError("u", 503, "busy", {}, None), io.BytesIO(b'{"ok": 1}')]

        def fake_urlopen(*_a, **_k):
            item = calls.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        with patch("http_util.urllib.request.urlopen", side_effect=fake_urlopen), patch("http_util.time.sleep"):
            data, latency = http_util.get_json("https://api.github.com/x", user_agent="test")
        self.assertEqual(data, {"ok": 1})
        self.assertGreaterEqual(latency, 0)

    def test_client_error_is_not_retried(self):
        error = urllib.error.HTTPError("u", 404, "missing", {}, None)
        with patch("http_util.urllib.request.urlopen", side_effect=error) as opened:
            with self.assertRaises(urllib.error.HTTPError):
                http_util.get_json("https://api.github.com/x", user_agent="test")
        self.assertEqual(opened.call_count, 1)

    def test_github_issue_listing_refuses_silent_truncation(self):
        full_page = [{"number": 1, "title": "", "html_url": "u", "body": ""}] * 100
        with patch("research_graph.fetch_json", return_value=full_page):
            with self.assertRaises(ValueError):
                research_graph.github_issues("o/r", max_pages=2)


if __name__ == "__main__":
    unittest.main()
