import datetime as dt
import unittest
from publication_openaire import enrich, parse_result, source_url
from eu_source_discovery import discover
from test_arxiv_source_discovery import feed, entry

NOW = dt.datetime(2026, 11, 24, tzinfo=dt.timezone.utc)
PID = "2601.12345"
PAPER = {"id": PID, "version_id": PID+"v1"}

def payload(pid=PID, scheme="arxiv"):
    return {"header": {"numFound": 1}, "results": [{
        "id": "example::record", "mainTitle": "Example research", "type": "publication",
        "pids": [{"scheme": scheme, "value": pid}],
        "organizations": [{"id": "example::org", "legalName": "Example Lab"}],
        "projects": [{"id": "example::grant", "provenance": {"provenance": "Inferred by OpenAIRE"}}]}]}

class OpenAIRETests(unittest.TestCase):
    def test_exact_id_and_doi_alias(self):
        for p in (payload(), payload("10.48550/arxiv."+PID, "doi")):
            result = parse_result(PID, p)
            self.assertEqual(result["status"], "matched")
            self.assertEqual(result["records"][0]["projects"][0]["provenance"]["provenance"], "Inferred by OpenAIRE")
            self.assertTrue(result["records"][0]["review_only"])

    def test_mismatch_and_empty(self):
        self.assertEqual(parse_result(PID, payload("2601.12346"))["status"], "unverified_response")
        self.assertEqual(parse_result(PID, {"header": {"numFound": 0}, "results": []})["status"], "not_indexed")
        with self.assertRaises(ValueError):
            parse_result(PID, {"header": {"numFound": 2}, "results": []})
        with self.assertRaises(ValueError):
            source_url("name OR another")

    def test_preserve_success_on_failure(self):
        first = enrich([PAPER], NOW, fetch=lambda _: payload())
        def fail(_):
            raise TimeoutError()
        second = enrich([PAPER], NOW+dt.timedelta(days=15), previous=first, fetch=fail)
        record = second["papers"][PID]
        self.assertEqual(record["status"], "matched")
        self.assertEqual(record["last_attempt_status"], "source_error")
        self.assertEqual(record["retrieved_at"], first["papers"][PID]["retrieved_at"])

    def test_cache_and_budget(self):
        second_paper = {"id": "2601.12346", "version_id": "2601.12346v1"}
        first = enrich([PAPER, second_paper], NOW, fetch=lambda _: payload(), max_papers=1)
        self.assertEqual(first["selected"], [PID])
        second = enrich([PAPER, second_paper], NOW, previous=first, fetch=lambda _: payload("2601.12346"), max_papers=1)
        self.assertEqual(second["selected"], ["2601.12346"])

    def test_integration(self):
        result = discover({"repositories": [{"repo": "Example/seed"}],
                           "arxiv_discovery": True, "openaire_discovery": True},
                          fetch=lambda _: [], publication_fetch=lambda _: feed(entry()),
                          openaire_fetch=lambda _: payload(), now=NOW, max_follow=0)
        self.assertFalse(result["errors"])
        self.assertEqual(result["openaire_discovery"]["papers"][PID]["status"], "matched")
