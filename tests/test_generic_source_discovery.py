import datetime as dt
import json
import socket
import unittest
from unittest.mock import patch

from eu_source_discovery import canonical, discover
from generic_source_discovery import (public_url, public_addresses, PublicFetcher,
                                      parse_document, discover_web)


class GenericSourceDiscoveryTests(unittest.TestCase):
    now = dt.datetime(2026, 11, 24, tzinfo=dt.timezone.utc)
    seed = "https://core.example.org/"

    def run_web(self, fetch, **kwargs):
        return discover_web([self.seed], platform_key=canonical, fetch=fetch,
                            now=self.now, **kwargs)

    def test_public_url_policy(self):
        for url in ("http://example.org/", "https://127.0.0.1/", "https://[::1]/",
                    "https://user:secret@example.org/", "https://example.org:8080/",
                    "https://example.org/?token=secret", "https://localhost/",
                    "https://example.local/", "https://example.org/%0d%0a"):
            self.assertIsNone(public_url(url), url)
        self.assertEqual(public_url("/projects/#one", self.seed),
                         "https://core.example.org/projects/")

    def test_public_dns_policy(self):
        def resolver(*args, **kwargs):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))
                    for ip in ("8.8.8.8", "169.254.169.254")]
        with self.assertRaises(ValueError):
            public_addresses("example.org", resolver=resolver)
        with self.assertRaises(ValueError):
            public_addresses("example.org", resolver=lambda *a, **k: [
                (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::ffff:127.0.0.1", 443, 0, 0))])

    def test_robots_denial_prevents_content_request(self):
        fetcher = PublicFetcher()
        with patch.object(fetcher, "_get", return_value=(
                200, "text/plain", b"User-agent: *\nDisallow: /private\n", None)) as get:
            with self.assertRaises(PermissionError):
                fetcher(self.seed + "private")
            get.assert_called_once_with(self.seed + "robots.txt")

    def test_robots_unavailable_is_retryable(self):
        fetcher = PublicFetcher()
        with patch.object(fetcher, "_get", return_value=(503, "text/plain", b"", None)):
            with self.assertRaises(OSError):
                fetcher(self.seed)

    def test_format_recognition(self):
        fmt, links = parse_document("text/html", b'<link rel="alternate" type="application/rss+xml" href="/feed"/>')
        self.assertEqual(fmt, "html")
        self.assertEqual(links[0][0], "/feed")
        fmt, links = parse_document("application/atom+xml",
                                    b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><link href="https://example.org/research"/></entry></feed>')
        self.assertEqual(fmt, "atom")
        self.assertEqual(links[0][0], "https://example.org/research")
        self.assertEqual(parse_document("application/json", b'{"openapi":"3.0.0","servers":[{"url":"https://example.org/"}]}'),
                         ("openapi", []))
        with self.assertRaises(ValueError):
            parse_document("application/xml", b'<!DOCTYPE rss [<!ENTITY x "a">]><rss>&x;</rss>')

    def test_unknown_source_recursive_cross_platform_integration(self):
        source = "https://unknown.example.org/projects"
        feed = "https://unknown.example.org/feed"
        def fetch_web(url):
            pages = {
                self.seed: (200, "text/html", b'<a href="https://unknown.example.org/projects">AI research project</a>', None),
                source: (200, "text/html", b'<link rel="alternate" type="application/rss+xml" href="/feed"><a href="https://github.com/unknown/model">Code</a>', None),
                feed: (200, "application/rss+xml", b'<rss><channel><item><link>https://huggingface.co/unknown/model</link></item></channel></rss>', None),
            }
            return pages[url]
        def fetch_platform(url):
            if url.endswith("/repos/unknown/model"):
                return {"full_name": "unknown/model"}
            if url.endswith("/api/models/unknown/model"):
                return {"id": "unknown/model"}
            return []
        config = {"repositories": [{"repo": "Example/seed"}], "web_seeds": [self.seed]}
        first = discover(config, fetch=fetch_platform, web_fetch=fetch_web,
                         now=self.now, max_follow=0, max_web_pages=2)
        self.assertFalse(first["web_discovery"]["errors"])
        self.assertIn(feed, first["web_discovery"]["pending"])
        self.assertIn("https://github.com/unknown/model", first["pending"])
        second = discover(config, fetch=fetch_platform, web_fetch=fetch_web, previous=first,
                          now=self.now + dt.timedelta(days=1), max_follow=1, max_web_pages=2)
        self.assertEqual(second["expanded"]["https://github.com/unknown/model"], "confirmed_public_metadata")
        self.assertIn("https://huggingface.co/unknown/model", second["pending"])
        self.assertEqual(second["web_discovery"]["sources"][feed]["format"], "rss")
        self.assertEqual(second["web_discovery"]["references"][1]["evidence"]["excerpt"], "/feed")
        self.assertTrue(all(x["verification_status"] == "unknown" for x in second["candidates"]))
        third = discover(config, fetch=fetch_platform, web_fetch=fetch_web, previous=second,
                         now=self.now + dt.timedelta(days=2), max_follow=1, max_web_pages=2)
        self.assertEqual(third["expanded"]["https://huggingface.co/unknown/model"], "confirmed_public_metadata")
        self.assertEqual(len(third["web_discovery"]["sources"]), 3)
        self.assertEqual(third["web_discovery"]["new_sources"], 0)
        self.assertEqual(first["web_discovery"]["pending"], [feed])

    def test_openapi_proposal_does_not_call_operations(self):
        calls = []
        def fetch(url):
            calls.append(url)
            if url == self.seed:
                return 200, "application/json", b'{"openapi":"3.1.0","servers":[{"url":"https://api.example.org/"}]}', None
            raise AssertionError("unexpected API operation")
        result = self.run_web(fetch)
        self.assertEqual(calls, [self.seed])
        self.assertEqual(result["adapter_proposals"][0]["format"], "openapi")

    def test_transient_error_and_redirect_are_bounded(self):
        def fetch(url):
            if url == self.seed:
                return 302, "text/html", b"", "https://other.example.org/"
            raise TimeoutError()
        result = self.run_web(fetch)
        self.assertEqual(result["pending"], ["https://other.example.org/"])
        self.assertTrue(result["errors"])
        self.assertFalse(result["queue_drained"])

    def test_multiple_sources_can_reference_same_platform_target(self):
        def fetch(url):
            if url == self.seed:
                return 200, "text/html", b'<a href="https://other.example.org/research">Research</a><a href="https://github.com/example/model">Model</a>', None
            return 200, "text/html", b'<a href="https://github.com/example/model">Model</a>', None
        result = self.run_web(fetch)
        self.assertEqual(len(result["platform_refs"]), 2)
