"""Compare hypothesis retrieval on identical abstracts, using validated mechanism fields."""
import itertools
import re
import math
from collections import Counter
from collaboration_matcher import tokens
from research_mechanisms import key, validate

def compare(packets, extraction, limit=10):
    if not 1 <= limit <= 20:
        raise ValueError("invalid pair budget")
    docs={p["id"]:p for p in packets}
    if len(docs)!=len(packets):
        raise ValueError("duplicate paper version")
    raw={i:tokens(" ".join(s["text"] for d in p["evidence"] for s in d["sections"])) for i,p in docs.items()}
    semantic={}
    for p in packets:
        k=key(p,extraction["provider"],extraction["model"])
        cached=extraction["cache"].get(k)
        if cached is not None:
            fields=validate(cached["answer"],p)["fields"]
            semantic[p["id"]]={f:tokens(v["text"]) for f,v in fields.items() if v is not None}
    df=Counter(t for terms in raw.values() for t in terms)
    idf={t:1+math.log((len(raw)+1)/(n+1)) for t,n in df.items()}
    baseline=[]; structured=[]
    for a,b in itertools.combinations(sorted(docs),2):
        shared=raw[a]&raw[b]
        if shared:baseline.append({"pair":[a,b],"score":sum(idf[t] for t in sorted(shared))})
        if a not in semantic or b not in semantic:continue
        sa,sb=semantic[a],semantic[b]
        # A question/measurement bridge plus an explicitly supported mechanism or intervention.
        common=sa.get("question",set())&sb.get("question",set())
        measures=sa.get("measurement",set())&sb.get("measurement",set())
        ma=sa.get("mechanism",set())|sa.get("intervention",set())
        mb=sb.get("mechanism",set())|sb.get("intervention",set())
        if not (common or measures) or not ma or not mb:continue
        score=len(common)+len(measures)+len(ma&mb)
        structured.append({"pair":[a,b],"score":score,"question_terms":sorted(common),"measurement_terms":sorted(measures),"mechanism_terms":sorted(ma&mb)})
    rank=lambda x:sorted(x,key=lambda y:(-y["score"],y["pair"]))[:limit]
    return {"schema":1,"paper_count":len(docs),"extracted_paper_count":len(semantic),
            "baseline":rank(baseline),"structured":rank(structured),"review_only":True,
            "limitations":["Structured ranker is a heuristic over model-extracted text, not semantic proof.",
                           "Same source corpus, but extraction may abstain; measure missingness.",
                           "Pair hypotheses need separate model/human assessment and a falsifiable experiment."]}

def cases(packets,comparison):
    docs={p["id"]:p for p in packets}
    pairs=sorted({tuple(x["pair"]) for arm in ("baseline","structured") for x in comparison[arm]})
    return [{"id":a+"--"+b,"question":"Compare the research questions, mechanisms, experimental conditions and measurement contracts. Is there a concrete falsifiable cross-paper experiment? Distinguish explicit citations, overlap, and unsupported hypotheses.",
             "evidence":[{"id":f"e{i+1}","url":docs[v]["evidence"][0]["url"],"revision":v,
                          "text":"".join(s["text"] for s in docs[v]["evidence"][0]["sections"])}
                         for i,v in enumerate((a,b))]} for a,b in pairs]
