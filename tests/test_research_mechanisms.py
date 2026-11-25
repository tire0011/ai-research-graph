import unittest
from research_mechanisms import select, validate, extract, key, CONTROL, FIELDS, fetch_batch
from research_hypotheses import compare,cases
from semantic_review import case_payload

def packet(i,text):
    return case_payload({"id":i,"question":"extract","evidence":[{"id":"e1","url":"https://arxiv.org/abs/"+i,"revision":i,"text":text}]})

def answer(p):
    return {"fields":{f:({"text":"Context recognition and rule execution","section_ids":[p["evidence"][0]["sections"][0]["section_id"]]} if f in ("question","mechanism") else None) for f in FIELDS}}

class ResearchMechanismTests(unittest.TestCase):
    def test_selection_stable_excludes_controls(self):
        ids=[f"2611.{i:05d}" for i in range(1,30)]+list(CONTROL)
        rows=[{"id":i,"version_id":i+"v1","categories":["cs.AI"]} for i in ids]
        s={"retrieved_at":"now","publication_discovery":{"papers":rows}}
        a=select(s)
        rows.reverse()
        self.assertEqual(a,select(s))
        self.assertEqual(len(a["selected"]),20)
        self.assertFalse(set(CONTROL)&{x["id"] for x in a["selected"]})
    def test_unknown_reference(self):
        p=packet("2611.00001v1","Testing context recognition.")
        a=answer(p);a["fields"]["question"]["section_ids"]=["e1:s999"]
        with self.assertRaises(ValueError):validate(a,p)
    def test_cache_and_model_version(self):
        p=packet("2611.00001v1","Testing context recognition.")
        calls=[]
        def run(x):
            calls.append(x);return answer(x),{}
        first=extract([p],run,provider="local",model="a")
        second=extract([p],run,provider="local",model="a",previous=first)
        self.assertEqual(len(calls),1)
        self.assertTrue(second["records"][0]["cached"])
        self.assertNotEqual(key(p,"local","a"),key(p,"local","b"))
    def test_same_corpus_pair_review(self):
        ps=[packet("2611.00001v1","Context recognition test."),packet("2611.00002v1","Context recognition benchmark.")]
        e=extract(ps,lambda p:(answer(p),{}),provider="local",model="fixture")
        result=compare(ps,e)
        self.assertEqual(result["paper_count"],2)
        self.assertEqual(result["extracted_paper_count"],2)
        self.assertEqual(len(result["structured"]),1)
        self.assertEqual(len(cases(ps,result)),1)

    def test_batch_checks_versions_and_order(self):
        def entry(v):
            return f"<entry><id>https://arxiv.org/abs/{v}</id><title>Title</title><published>2026-11-01T00:00:00Z</published><updated>2026-11-01T00:00:00Z</updated><summary>Research question.</summary></entry>"
        def feed(ids):
            return ('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:os="http://a9.com/-/spec/opensearch/1.1/"><os:totalResults>'+str(len(ids))+'</os:totalResults><os:startIndex>0</os:startIndex>'+''.join(entry(v) for v in ids)+'</feed>').encode()
        ids=["2611.00001v1","2611.00002v1"]
        calls=[]
        def fetch(url):
            calls.append(url)
            return feed(ids[::-1])
        result=fetch_batch(ids,fetch)
        self.assertEqual(set(result),set(ids))
        self.assertEqual(len(calls),1)
        self.assertEqual(result[ids[0]]["evidence"][0]["revision"],ids[0])
        with self.assertRaises(ValueError):
            fetch_batch(ids,lambda _:feed(["2611.00001v2"]))
