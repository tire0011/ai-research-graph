import datetime as dt
import unittest
import urllib.parse
from arxiv_source_discovery import discover_publications, parse_atom
from eu_source_discovery import discover

NOW = dt.datetime(2026, 11, 24, tzinfo=dt.timezone.utc)

def feed(entries="", total=1, start=0):
    return f'''<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
      <opensearch:totalResults>{total}</opensearch:totalResults>
      <opensearch:startIndex>{start}</opensearch:startIndex>
      {entries}</feed>'''.encode()

def entry(version=1, affiliation=""):
    return f'''<entry><id>http://arxiv.org/abs/2601.12345v{version}</id>
    <title>Example research</title><published>2026-11-10T10:00:00Z</published>
    <updated>2026-11-{10+version}T10:00:00Z</updated>
    <author><name>Example Author</name>{affiliation}</author>
    <summary>Code at https://github.com/Example/research.</summary>
    <category term="cs.AI"/></entry>'''

class PublicationTests(unittest.TestCase):
    def test_missing_affiliation_and_links(self):
        _, _, rows = parse_atom(feed(entry()))
        p = rows[0]
        self.assertEqual(p["id"], "2601.12345")
        self.assertEqual(p["affiliation_status"], "unknown")
        self.assertEqual(p["explicit_links"], ["https://github.com/Example/research"])
        self.assertEqual(p["european_relevance"], "unknown")

    def test_affiliation_does_not_prove_europe(self):
        _, _, rows = parse_atom(feed(entry(affiliation="<arxiv:affiliation>Example Lab, Canada</arxiv:affiliation>")))
        self.assertEqual(rows[0]["affiliation_status"], "author_reported")
        self.assertEqual(rows[0]["european_relevance"], "unknown")

    def test_dedup_versions_and_persistence(self):
        first, _ = discover_publications(NOW, fetch=lambda _: feed(entry()))
        second, _ = discover_publications(NOW, previous=first, fetch=lambda _: feed(entry(2)))
        self.assertEqual(len(second["papers"]), 1)
        self.assertEqual(second["papers"][0]["version_id"], "2601.12345v2")
        self.assertFalse(second["papers"][0]["new"])
        empty, _ = discover_publications(NOW, previous=second, fetch=lambda _: feed(total=0))
        self.assertEqual(len(empty["papers"]), 1)

    def test_truncation_and_invalid_feed(self):
        result, _ = discover_publications(NOW, page_size=1, max_pages=1,
                                          fetch=lambda _: feed(entry(), total=2))
        self.assertEqual(result["coverage"], "partial")
        self.assertTrue(all(x["truncated"] for x in result["listings"]))
        invalid, _ = discover_publications(NOW, fetch=lambda _: b"<not-atom/>")
        self.assertTrue(invalid["errors"])
        self.assertEqual(invalid["coverage"], "partial")

    def test_pagination(self):
        def fetch(url):
            start = int(urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["start"][0])
            return feed(entry(start+1), total=2, start=start)
        result, _ = discover_publications(NOW, fetch=fetch, page_size=1, max_pages=2)
        self.assertEqual(result["requests"], 4)
        self.assertEqual(result["papers"][0]["version_id"], "2601.12345v2")

    def test_integration_with_existing_frontier(self):
        result = discover({"repositories": [{"repo": "Example/seed"}], "arxiv_discovery": True},
                          fetch=lambda _: [], publication_fetch=lambda _: feed(entry()),
                          now=NOW, max_follow=0)
        self.assertFalse(result["errors"])
        self.assertEqual(len(result["publication_discovery"]["papers"]), 1)
        self.assertEqual(result["pending"], ["https://github.com/example/research"])
        self.assertEqual(result["verified_references"][0]["relationship"], "references")
        self.assertTrue(result["candidates"][0]["review_only"])
