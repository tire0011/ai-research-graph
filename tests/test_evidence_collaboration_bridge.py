import base64
import datetime as dt
import hashlib
import unittest
from unittest.mock import patch

from checkpaper_evidence import collect, read_blob, parse_audit
from discovered_collaboration_review import contact_review, prepare_discovered

NOW = dt.datetime(2026,11,25,tzinfo=dt.timezone.utc)
PATH = "2026/2611.26540-aura/README.md"
AUDIT = """# Sample
## Paper
- arXiv: [2611.26540v1](https://arxiv.org/abs/2611.26540v1)
## Findings
Example claim.
## Reproduce
python verify.py
## Status
[Asked the authors](https://github.com/kyutai-labs/aura/issues/1).
"""
def blob(path,text):
    raw=text.encode()
    return {"path":path,"type":"file","encoding":"base64","size":len(raw),
            "content":base64.b64encode(raw).decode(),
            "sha":hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()}

class EvidenceTests(unittest.TestCase):
    def test_version_and_source(self):
        row=parse_audit(PATH,AUDIT,"a"*40,NOW.isoformat())
        self.assertEqual(row["paper_version"],"2611.26540v1")
        self.assertFalse(row["scientific_validity_verified"])
        self.assertFalse(row["audit_script_executed"])
        self.assertEqual(row["author_response_links"],["https://github.com/kyutai-labs/aura/issues/1"])
        self.assertEqual(parse_audit(PATH,AUDIT.replace("26540v1","26540"),"a"*40,NOW.isoformat())["status"],"unsupported_or_unversioned")

    def test_blob_integrity_and_failure_retention(self):
        def fetch(url):
            if url.endswith("/contents/README.md"):
                return blob("README.md","[AURA](2026/2611.26540-aura/)")
            return blob(PATH,AUDIT)
        first=collect(NOW,fetch)
        self.assertEqual(len(first["records"]),1)
        def bad(url):
            if url.endswith("/contents/README.md"):
                return fetch(url)
            return {**fetch(url),"sha":"0"*40}
        second=collect(NOW+dt.timedelta(days=7),bad,previous=first)
        self.assertTrue(second["errors"])
        self.assertEqual(first["records"],second["records"])
        self.assertEqual(second["coverage"],"partial")

    def test_contact_pair_exact_and_reversed(self):
        config={"connection_reviews":[{"id":"a-b","status":"contacted","github_owners":["a","b"]}]}
        self.assertTrue(contact_review(config,"B","A")["suppress_outreach"])
        self.assertFalse(contact_review(config,"A","C")["suppress_outreach"])

    @patch("discovered_collaboration_review.cr.prepare")
    @patch("discovered_collaboration_review.cm.rank_pairs")
    def test_reuse_ranker_and_keep_suppressed(self, rank, prepare):
        rank.return_value=([{"id":"one","source":{"repo":"a/r"},"target":{"repo":"b/r"}},
                            {"id":"two","source":{"repo":"a/r"},"target":{"repo":"c/r"}}],{})
        prepare.return_value={"schema":1}
        config={"connection_reviews":[{"id":"a-b","status":"contacted","github_owners":["a","b"]}]}
        metadata=[{"repo":owner+"/r","status":"review_only","has_issues":True,"recent_push":True,
                   "technical_signals":{"inference":["inference"]}} for owner in ["a","b","c"]]
        result=prepare_discovered(config,metadata,lambda _:[],now=NOW)
        self.assertEqual(len(result["suppressed_contact_candidates"]),1)
        self.assertEqual(result["packets"][0]["candidate"]["id"],"two")
        self.assertFalse(result["packets"][0]["outreach_approved"])
        prepare.assert_called_once()
