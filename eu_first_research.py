"""EU-first source discovery pilot; geographic evidence is not scientific relevance."""
import argparse
import datetime as dt
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import HTTPError
import xml.etree.ElementTree as ET

import arxiv_source_discovery as arxiv
import publication_organizations as org
from publication_openaire import API, ID
from research_graph import fetch_json, openaire_node
from research_mechanisms import EXCLUDED as KNOWN, fetch_batch

# Exclude previously reviewed papers from the new prospective cohort.
EXCLUDED=KNOWN | {"2611.15241","2611.27486","2611.28660","2611.31015","2611.30627","2611.28706"}

TOPICS=("large language model","AI agent","quantum machine learning","model compression")
MAX_PAGE=20
MAX_ANCHORS=20
MAX_GLOBAL=10

def query(topic, now):
    if topic not in TOPICS:
        raise ValueError("unsupported topic")
    since=(now-dt.timedelta(days=180)).date().isoformat()
    return API+"?"+urlencode({"filter":"type:publication,has_arxiv:true,authorships.countries:"+"|".join(sorted(org.EU))+",from_publication_date:"+since+",title_and_abstract.search:"+topic,
                             "page_size":MAX_PAGE,"sort":"publication_date:desc","select":"id,pids,mainTitle,publicationDate,organizations,authors"})

def discover(now, fetch=None):
    candidates={};coverage=[];errors=[]
    for topic in TOPICS:
        url=query(topic,now)
        try:
            payload=(fetch or (lambda u:fetch_json(u,timeout=25)))(url)
            rows,total=payload["results"],payload["header"]["numFound"]
            if not isinstance(rows,list) or type(total) is not int or not len(rows)<=min(MAX_PAGE,total) or (total and not rows):
                raise ValueError("invalid page")
            for row in rows:
                node=openaire_node(row)
                for pid in node["identifiers"]["arxiv"]:
                    if ID.fullmatch(pid) and pid not in EXCLUDED:
                        record=candidates.setdefault(pid,{"id":pid,"title":node["title"],"observations":[]})
                        record["observations"].append({"openaire_id":row.get("id"),"source_url":url,
                            "topic":topic,"organizations":row.get("organizations") or [],
                            "status":"eu_country_filter_candidate"})
            coverage.append({"topic":topic,"returned":len(rows),"total":total,"source_url":url})
        except (OSError,ValueError,TypeError,KeyError,AttributeError) as e:
            errors.append({"topic":topic,"error":type(e).__name__,**({"http_status":e.code} if isinstance(e,HTTPError) else {})})
        if fetch is None:time.sleep(1)
    return {"candidates":candidates,"coverage":coverage,"errors":errors}

def rank_ids(ids):
    return sorted(ids,key=lambda x:hashlib.sha256(("eu-first-v1:"+x).encode()).hexdigest())

def versions(ids, fetch=arxiv.fetch_atom):
    if not 1<=len(ids)<=20 or len(set(ids))!=len(ids) or any(not ID.fullmatch(i) for i in ids):
        raise ValueError("invalid arXiv batch")
    url=arxiv.API+"?"+urlencode({"id_list":",".join(ids),"max_results":len(ids)})
    total,start,rows=arxiv.parse_atom(fetch(url))
    if start!=0 or total!=len(rows) or len(rows)>len(ids):
        raise ValueError("invalid version response")
    out={}
    for p in rows:
        if p["id"] not in ids or p["id"] in out or not org.VERSION.fullmatch(p["version_id"]) or p["version_id"].rsplit("v",1)[0]!=p["id"]:
            raise ValueError("identity mismatch")
        out[p["id"]]=p
    return out

def geography(paper, state):
    """Paper-level source plus ROR: conservative candidate evidence, never inferred nationality."""
    record=state.get("papers",{}).get(paper["id"],{})
    if record.get("version_id")!=paper["version_id"]:
        return {"status":"unknown","evidence":[]}
    evidence=[]
    for a in record.get("affiliations",[]):
        countries=set(a.get("countries",[]))
        if (a.get("status")=="registry_match_candidate" and org.ROR_ID.fullmatch(a.get("ror_id",""))
                and a.get("raw_affiliation") in record.get("raw_affiliations",[])
                and a.get("publication_source_url") in {"https://arxiv.org/html/"+paper["version_id"],"https://arxiv.org/abs/"+paper["version_id"]}
                and a.get("source_url","").startswith(org.ROR_API+"?") and countries):
            evidence.append(a)
    eu=[a for a in evidence if set(a["countries"])<=org.EU]
    # Multi-country registry records with both EU and non-EU locations do not
    # establish the actual affiliation site. Preserve them for review.
    if eu:
        return {"status":"eu_evidence_candidate","evidence":evidence}
    if evidence and not record.get("affiliations_truncated") and len(evidence)==len(record.get("raw_affiliations",[])) and all(not set(a["countries"])&org.EU for a in evidence):
        return {"status":"non_eu_evidence_candidate","evidence":evidence}
    return {"status":"unknown","evidence":evidence}

def classify_pair(a,b):
    if a==b=="eu_evidence_candidate":return "eu_eu_candidate"
    if "eu_evidence_candidate" in (a,b):
        return "eu_global_candidate" if "non_eu_evidence_candidate" in (a,b) else "eu_unknown"
    return "background_only"

def select(papers, state, global_papers, *, anchors=20, global_limit=10):
    if not 1<=anchors<=MAX_ANCHORS or not 0<=global_limit<=MAX_GLOBAL:
        raise ValueError("invalid cohort budget")
    all_papers={p["id"]:p for p in [*global_papers,*papers] if p["id"] not in EXCLUDED}
    classified={p["id"]:geography(p,state) for p in all_papers.values()}
    eu=rank_ids([i for i in all_papers if classified[i]["status"]=="eu_evidence_candidate" and set(all_papers[i].get("categories",[]))&{"cs.AI","cs.CL","cs.LG"}])[:anchors]
    global_ids=rank_ids([p["id"] for p in global_papers if p["id"] in all_papers and classified[p["id"]]["status"]!="eu_evidence_candidate" and set(p.get("categories",[]))&{"cs.AI","cs.CL","cs.LG"}])[:global_limit]
    selected=[{"id":i,"version_id":all_papers[i]["version_id"],"geography":classified[i]} for i in dict.fromkeys(eu+global_ids)]
    return {"schema":1,"requested_eu":anchors,"eu_candidates":len(eu),"independently_verified_eu":0,
            "global_comparators":len(set(global_ids)),"selected":selected,
            "geography_counts":{s:sum(x["status"]==s for x in classified.values()) for s in ("eu_evidence_candidate","non_eu_evidence_candidate","unknown")},
            "limitations":["ROR matches and author-reported affiliations are evidence candidates, not independent verification.",
                           "Global comparator can have unknown geography; never infer non-EU from missing evidence.",
                           "No global-global pair eligible for EU-action shortlist."]}

def run(snapshot,now,*,previous=None):
    discovery=discover(now)
    previous=previous or {}
    old=previous.get("versioned_papers",{})
    pool={**old}
    # Bounded rotation: prefer unseen candidate identities, then stable hash order.
    ids=rank_ids(discovery["candidates"])
    todo=sorted(ids,key=lambda i:i in pool)[:20]
    errors=list(discovery["errors"])
    if todo:
        try:pool.update(versions(todo))
        except (OSError,ValueError,TypeError,ET.ParseError) as e:errors.append({"stage":"arxiv_versions","error":type(e).__name__})
    # Existing resolver has version-aware cache and bounded requests.
    prior=previous.get("organization_state") or snapshot.get("organization_discovery",{})
    orgstate=org.resolve(list(pool.values()),now,previous=prior,max_papers=12,max_ror=32)
    cohort=select(list(pool.values()),orgstate,snapshot["publication_discovery"]["papers"])
    cohort["snapshot_retrieved_at"]=snapshot["retrieved_at"]
    return {"schema":1,"retrieved_at":now.isoformat(),"discovery":discovery,"versioned_papers":pool,
            "organization_state":orgstate,"cohort":cohort,"errors":errors+orgstate["errors"]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot",required=True);p.add_argument("--output",required=True);p.add_argument("--previous")
    a=p.parse_args();snap=json.loads(Path(a.snapshot).read_text(encoding="utf-8"))
    prev=json.loads(Path(a.previous).read_text(encoding="utf-8")) if a.previous else None
    result=run(snap,dt.datetime.now(dt.timezone.utc),previous=prev)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    (out/"eu_first.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    (out/"selection.json").write_text(json.dumps(result["cohort"],indent=2,ensure_ascii=False),encoding="utf-8")
    c=result["cohort"]
    print("EU-first coverage:",json.dumps({"discovered":len(result["discovery"]["candidates"]),"versioned":len(result["versioned_papers"]),
        "eu_candidates":c["eu_candidates"],"independently_verified_eu":0,"global_comparators":c["global_comparators"],"errors":len(result["errors"]),"diagnostics":result["errors"]}))
    print("OpenAIRE pages:",json.dumps(result["discovery"]["coverage"]))
    return 2 if not result["versioned_papers"] else 0

if __name__=="__main__":raise SystemExit(main())
