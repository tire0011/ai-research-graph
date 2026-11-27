import datetime as dt
import unittest
from urllib.error import HTTPError
from publication_organizations import parse_affiliations, parse_ror, resolve
from eu_source_discovery import discover
from test_arxiv_source_discovery import feed, entry

NOW = dt.datetime(2026, 11, 24, tzinfo=dt.timezone.utc)
HTML = """<div class="ltx_authors"><span class="ltx_creator"><span class="ltx_role_affiliation">
Affiliation: Example Lab, <b>Spain</b></span></span></div>
<div class="ltx_role_affiliation">Not in author block</div>"""

def ror(countries=("ES",), chosen=True):
    return {"items": [{"chosen": chosen, "score": .99, "organization": {
        "id": "https://ror.org/012345678", "status": "active",
        "names": [{"types": ["ror_display"], "value": "Example Lab"}],
        "locations": [{"geonames_details": {"country_code": c}} for c in countries]}}]}

def paper(pid="2611.12345", affiliations=()):
    return {"id": pid, "version_id": pid+"v1",
            "authors": [{"name": "Example", "affiliations": list(affiliations)}]}

class OrganizationTests(unittest.TestCase):
    def test_html_only_author_block(self):
        self.assertEqual(parse_affiliations(HTML), ["Example Lab, Spain"])
        with self.assertRaises(ValueError):
            parse_affiliations('<div class="ltx_authors">incomplete')

    def test_ror_ambiguity_and_country(self):
        self.assertEqual(parse_ror(ror(chosen=False))["status"], "unresolved")
        p = ror()
        p["items"] *= 2
        self.assertEqual(parse_ror(p)["status"], "ambiguous")
        self.assertEqual(parse_ror(ror(("CA",)))["eu_location"], "not_listed")
        self.assertEqual(parse_ror(ror(("CA", "ES")))["countries"], ["CA", "ES"])

    def test_html_fallback_and_evidence(self):
        result = resolve([paper()], NOW, html_fetch=lambda _: parse_affiliations(HTML),
                         ror_fetch=lambda _: ror())
        self.assertEqual(result["html_requests"], 1)
        org = result["organizations"]["https://ror.org/012345678"]
        obs = org["observations"][0]
        self.assertEqual(obs["raw_affiliation"], "Example Lab, Spain")
        self.assertTrue(obs["publication_source_url"].endswith("/html/2611.12345v1"))
        self.assertFalse(result["papers"]["2611.12345"]["european_affiliation_verified"])

    def test_cache_and_rotation(self):
        papers = [paper("2611.12345", ["Example Lab"]), paper("2611.12346", ["Example Lab"])]
        first = resolve(papers, NOW, ror_fetch=lambda _: ror(), max_papers=1)
        second = resolve(papers, NOW + dt.timedelta(days=7), previous=first,
                         ror_fetch=lambda _: self.fail("cache should be used"), max_papers=1)
        self.assertEqual(second["selected"], ["2611.12346"])
        self.assertEqual(second["ror_requests"], 0)
        self.assertEqual(len(second["organizations"]["https://ror.org/012345678"]["paper_ids"]), 2)

    def test_failures_and_budget_not_negative_evidence(self):
        def fail(_):
            raise TimeoutError()
        result = resolve([paper()], NOW, html_fetch=fail)
        self.assertTrue(result["errors"])
        self.assertFalse(result["organizations"])
        result = resolve([paper(affiliations=["Example Lab"])], NOW, max_ror=0)
        self.assertEqual(result["papers"]["2611.12345"]["affiliations"][0]["status"], "deferred_budget")

    def test_optional_html_missing_is_not_a_source_failure(self):
        for code in (404, 410):
            with self.subTest(code=code):
                def fail(url):
                    raise HTTPError(url, code, "missing", {}, None)
                result = resolve([paper()], NOW, html_fetch=fail)
                record = result["papers"]["2611.12345"]
                self.assertEqual(record["html_status"], "not_found")
                self.assertEqual(record["html_http_status"], code)
                self.assertFalse(record["european_affiliation_verified"])
                self.assertEqual(result["errors"], [])
                self.assertEqual(result["ror_requests"], 0)

    def test_http_failure_diagnostics_and_next_attempt(self):
        for code in (403, 429, 500, 503):
            with self.subTest(code=code):
                def fail(url):
                    raise HTTPError(url, code, "unavailable", {"Retry-After": "60"}, None)
                result = resolve([paper()], NOW, html_fetch=fail)
                self.assertEqual(result["papers"]["2611.12345"]["html_status"], "unavailable")
                diagnostic = result["errors"][0]
                self.assertEqual(diagnostic["http_status"], code)
                self.assertEqual(diagnostic["retryable"], code != 403)
                self.assertEqual(diagnostic["retry_after"], "60")
                recovered = resolve([paper()], NOW + dt.timedelta(days=1), previous=result,
                                    html_fetch=lambda _: ["Example Lab"], ror_fetch=lambda _: ror())
                self.assertEqual(recovered["errors"], [])
                self.assertTrue(recovered["organizations"])

    def test_ror_http_error_remains_a_source_failure(self):
        def fail(url):
            raise HTTPError(url, 404, "missing", {}, None)
        result = resolve([paper(affiliations=["Example Lab"])], NOW, ror_fetch=fail)
        self.assertEqual(result["errors"][0]["http_status"], 404)
        self.assertEqual(result["papers"]["2611.12345"]["affiliations"][0]["status"], "source_error")

    def test_integration(self):
        result = discover({"repositories": [{"repo": "Example/seed"}],
                           "arxiv_discovery": True, "organization_discovery": True},
                          fetch=lambda _: [], publication_fetch=lambda _: feed(entry()),
                          affiliation_fetch=lambda _: parse_affiliations(HTML), ror_fetch=lambda _: ror(),
                          now=NOW, max_follow=0)
        self.assertFalse(result["errors"])
        self.assertEqual(len(result["organization_discovery"]["organizations"]), 1)
