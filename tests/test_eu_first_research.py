import datetime as dt
import unittest
from eu_first_research import query, discover, geography, classify_pair, select
from research_hypotheses import compare
from semantic_review import case_payload
from research_mechanisms import extract,FIELDS
from urllib.parse import urlsplit,parse_qs

def paper(pid):
    return {"id":pid,"version_id":pid+"v1","categories":["cs.AI"]}

def evidence(p,countries):
    raw="Example University"
    a={"raw_affiliation":raw,"publication_source_url":"https://arxiv.org/html/"+p["version_id"],
       "status":"registry_match_candidate","ror_id":"https://ror.org/012345678",
       "source_url":"https://api.ror.org/v2/organizations?affiliation=Example",
       "countries":countries}
    return {"version_id":p["version_id"],"raw_affiliations":[raw],"affiliations":[a],"affiliations_truncated":False}

class EUFirstTests(unittest.TestCase):
    def test_eu_query_uses_eu27_not_continent(self):
        f=parse_qs(urlsplit(query("AI agent",dt.datetime(2026,11,25,tzinfo=dt.timezone.utc))).query)["filter"][0]
        countries=f.split("authorships.countries:")[1].split(",")[0].split("|")
        self.assertEqual(len(countries),27)
        self.assertIn("DE",countries)
        self.assertNotIn("GB",countries)
        self.assertNotIn("CH",countries)

    def test_registry_candidates_and_unknown(self):
        p=paper("2611.00001")
        for countries,expected in [(["DE"],"eu_evidence_candidate"),(["US"],"non_eu_evidence_candidate"),(["DE","US"],"unknown")]:
            s={"papers":{p["id"]:evidence(p,countries)}}
            self.assertEqual(geography(p,s)["status"],expected)
        self.assertEqual(geography(p,{"papers":{}})["status"],"unknown")
        a=evidence(p,["FR"]);a["version_id"]=p["id"]+"v2"
        self.assertEqual(geography(p,{"papers":{p["id"]:a}})["status"],"unknown")

    def test_country_filter_not_proof(self):
        row={"id":"oa:1","mainTitle":"AI test","pids":[{"scheme":"arxiv","value":"2611.00001"}]}
        result=discover(dt.datetime(2026,11,25,tzinfo=dt.timezone.utc),lambda _:{"header":{"numFound":1},"results":[row]})
        self.assertEqual(len(result["candidates"]),1)
        self.assertEqual(len(result["candidates"]["2611.00001"]["observations"]),4)
        self.assertEqual(result["candidates"]["2611.00001"]["observations"][0]["status"],"eu_country_filter_candidate")
        c=select([paper("2611.00001")],{},[])
        self.assertEqual(c["eu_candidates"],0)

    def test_cohort_no_padding(self):
        p,q=paper("2611.00001"),paper("2611.00002")
        c=select([p],{"papers":{p["id"]:evidence(p,["DE"])}},[q])
        self.assertEqual(c["eu_candidates"],1)
        self.assertEqual(c["independently_verified_eu"],0)
        self.assertEqual(c["global_comparators"],1)
        self.assertEqual(c["selected"][1]["geography"]["status"],"unknown")

    def test_pair_policy_same_for_both_arms(self):
        ps=[case_payload({"id":str(i),"question":"extract","evidence":[{"id":"e1","url":"https://arxiv.org/abs/2611.00001v1","revision":"v1","text":"context recognition benchmark"}]}) for i in range(4)]
        def mock(p):
            return {"fields":{f:{"text":"context recognition benchmark","section_ids":["e1:s001"]} for f in FIELDS}},{}
        e=extract(ps,mock,provider="local",model="fixture")
        g={"0":"eu_evidence_candidate","1":"eu_evidence_candidate","2":"non_eu_evidence_candidate","3":"unknown"}
        c=compare(ps,e,geography=g)
        for arm in ("baseline","structured"):
            pairs=c[arm]
            self.assertEqual(pairs[0]["pair"],["0","1"])
            self.assertEqual(len(pairs),5)
            self.assertNotIn(["2","3"],[p["pair"] for p in pairs])
        self.assertEqual(classify_pair("unknown","unknown"),"background_only")
