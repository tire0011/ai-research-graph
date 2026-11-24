import datetime as dt
import unittest
import urllib.parse
from organization_source_expansion import expand, registry_record, research_records
from eu_source_discovery import discover
from test_arxiv_source_discovery import feed, entry
from test_publication_organizations import HTML, ror

NOW = dt.datetime(2026, 11, 24, tzinfo=dt.timezone.utc)
RID = "https://ror.org/012345678"
SITE = "https://research.example.org/"
REPO = "https://github.com/example/research-code"

def state(*ids):
    return {"organizations": {rid: {"observations": [{
        "status": "registry_match_candidate", "ror_id": rid,
        "eu_location": "listed", "paper_id": "2601.12345"}]} for rid in ids}}

def registry(rid=RID, country="ES"):
    return {"id": rid, "status": "active",
            "locations": [{"geonames_details": {"country_code": country}}],
            "links": [{"type": "website", "value": SITE},
                      {"type": "wikipedia", "value": "https://en.wikipedia.org/wiki/Example"},
                      {"type": "website", "value": "https://127.0.0.1/"}]}

def products():
    return {"header": {"numFound": 6}, "results": [{
        "id": "example::research", "mainTitle": "LLM research",
        "pids": [{"scheme": "arxiv", "value": "2601.12345"}],
        "type": "publication", "codeRepositoryUrl": REPO}]}

class OrganizationExpansionTests(unittest.TestCase):
    def test_exact_registry_and_safe_links(self):
        result = registry_record(RID, registry())
        self.assertEqual(result["websites"], [{"url": SITE, "raw": SITE}])
        self.assertEqual(registry_record(RID, registry(country="CA"))["status"], "outside_eu_scope")
        self.assertEqual(registry_record(RID, registry("https://ror.org/012345679"))["status"], "identity_or_status_mismatch")

    def test_referrals_and_query_provenance(self):
        def fetch(url):
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            self.assertIn("authorships.institutions.ror:"+RID, q["filter"][0])
            return products()
        result, refs = expand(state(RID), NOW, registry_fetch=lambda _: registry(), research_fetch=fetch)
        self.assertEqual(result["selected"], [RID])
        self.assertEqual([x[0] for x in refs], [SITE, REPO])
        self.assertEqual(refs[0][1]["source_entity"], RID)
        self.assertEqual(refs[1][1]["source_entity"], "openaire:example::research")
        self.assertTrue(result["organizations"][RID]["research"]["truncated"])

    def test_no_name_guessing_or_non_eu_queries(self):
        data = state(RID)
        data["organizations"][RID]["observations"][0]["eu_location"] = "unknown"
        result, refs = expand(data, NOW, registry_fetch=lambda _: self.fail("not eligible"))
        self.assertFalse(refs)
        self.assertFalse(result["selected"])
        result, refs = expand(state(RID), NOW, registry_fetch=lambda _: registry(country="CA"),
                              research_fetch=lambda _: self.fail("not EU"))
        self.assertFalse(refs)

    def test_rotation_and_preserve_previous_on_error(self):
        rid2 = "https://ror.org/012345679"
        first, _ = expand(state(RID, rid2), NOW, max_organizations=1,
                          registry_fetch=lambda _: registry(), research_fetch=lambda _: products())
        second, _ = expand(state(RID, rid2), NOW, previous=first, max_organizations=1,
                           registry_fetch=lambda _: registry(rid2), research_fetch=lambda _: products())
        self.assertEqual(second["selected"], [rid2])
        def fail(_):
            raise TimeoutError()
        third, refs = expand(state(RID), NOW+dt.timedelta(days=29), previous=second, registry_fetch=fail)
        self.assertFalse(refs)
        self.assertEqual(third["organizations"][RID]["last_attempt_status"], "source_error")
        self.assertEqual(third["organizations"][RID]["registry"], first["organizations"][RID]["registry"])

    def test_bad_research_page(self):
        with self.assertRaises(ValueError):
            research_records({"header": {"numFound": 1}, "results": []})

    def test_recursive_integration_with_existing_web_frontier(self):
        config = {"repositories": [{"repo": "Example/seed"}],
                  "web_seeds": ["https://seed.example.org/"],
                  "arxiv_discovery": True, "organization_discovery": True, "organization_expansion": True}
        def web(url):
            if url == SITE:
                return 200, "text/html", b'<a href="https://research.example.org/project">AI research project</a>', None
            if url == "https://research.example.org/project":
                return 200, "text/html", b'<a href="https://github.com/example/new-tool">Code</a>', None
            return 200, "text/html", b"<html></html>", None
        result = discover(config, now=NOW, fetch=lambda _: [],
                          publication_fetch=lambda _: feed(entry()),
                          affiliation_fetch=lambda _: ["Example Lab, Spain"], ror_fetch=lambda _: ror(),
                          organization_registry_fetch=lambda _: registry(),
                          organization_research_fetch=lambda _: products(), web_fetch=web, max_follow=0)
        self.assertFalse(result["errors"])
        self.assertEqual(result["organization_expansion"]["selected"], [RID])
        self.assertIn("https://research.example.org/project", result["web_discovery"]["sources"])
        urls = {x["url"] for x in result["candidates"]}
        self.assertIn(REPO, urls)
        self.assertIn("https://github.com/example/new-tool", urls)
        self.assertTrue(all(x["review_only"] for x in result["candidates"]))
        self.assertTrue(any(x["source"] == RID and x["target"] == SITE for x in result["web_discovery"]["references"]))
