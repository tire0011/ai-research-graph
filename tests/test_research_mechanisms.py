import unittest
from research_mechanisms import select, validate, extract, key, CONTROL, FIELDS
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
