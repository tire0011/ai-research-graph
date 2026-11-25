"""Freeze a small same-input collaboration evaluation cohort, without assigning labels."""
import datetime as dt
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode
import collaboration_matcher as cm

REPOS = ("Helsinki-NLP/OPUS-MT-train", "hplt-project/OpusTrainer",
         "kyutai-labs/moshi-finetune", "LAION-AI/agent-bud-e")
CONFIG = {"source_owners":[x.split("/")[0] for x in REPOS],
          "source_max_age_days":400, "max_body_chars_for_matching":6000,
          "min_score":7,"max_suggestions":1000,"max_suggestions_per_source":1}

def freeze(items, now, config=CONFIG, limit=10):
    if len({x["id"] for x in items}) != len(items):
        raise ValueError("duplicate issue identity")
    active = cm.candidate_documents(items,config,now)
    # Round-robin owners, newest creation first, before any ranking is inspected.
    queues = {o:sorted((x for x in active if x["repo"].split("/")[0]==o),
                       key=lambda x:(cm.date(x["created_at"]),x["id"]),reverse=True)
              for o in sorted(config["source_owners"])}
    selected=[]
    while len(selected)<limit and any(queues.values()):
        for o in queues:
            if queues[o] and len(selected)<limit:
                selected.append(queues[o].pop(0))
    cards,_=cm.rank_pairs(items,config,now)
    by_source={x["source_id"]:x for x in cards}
    docs={x["id"]:cm.tokens(x["title"]+" "+x["body"][:config["max_body_chars_for_matching"]]) for x in items}
    freq=Counter(t for v in docs.values() for t in v)
    idf={t:1+math.log((len(items)+1)/(n+1)) for t,n in freq.items()}
    cases=[]
    for source in selected:
        options=[]
        for target in items:
            if source["repo"].split("/")[0].casefold()==target["repo"].split("/")[0].casefold() or cm.date(target["created_at"])>cm.date(source["created_at"]):
                continue
            shared=docs[source["id"]]&docs[target["id"]]
            if shared:
                options.append((sum(idf[t] for t in sorted(shared)),target["id"]))
        options.sort(key=lambda p:(-p[0],p[1]))
        card=by_source.get(source["id"])
        cases.append({"source_id":source["id"],"technical_target":card["target_id"] if card else None,
                      "technical_terms":[x["term"] for x in card["matched_terms"]] if card else [],
                      "baseline_target":options[0][1] if options else None,
                      "technical_abstained":card is None,"baseline_abstained":not options})
    evidence={x["id"]:x for x in items}
    digest=hashlib.sha256(json.dumps(evidence,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {"schema":1,"frozen_at":now.isoformat(),"config":config,"corpus_sha256":digest,
            "eligible_sources":len(active),"cases":cases,"corpus":evidence,
            "labels":[],"independent_review":"pending",
            "limitations":["Manually chosen repository cohort, not a representative sample or graph-wide evaluation.",
                           "Recent 30 issue/PR records per repository; may be truncated.",
                           "No outcome labels assigned; do not infer superiority from candidate counts."]}

def run(fetch, now):
    items, coverage, errors = [],{},[]
    for repo in REPOS:
        url=f"{cm.API}/{repo}/issues?"+urlencode({"state":"all","per_page":30,"sort":"updated","direction":"desc"})
        try:
            rows=fetch(url)
            if not isinstance(rows,list) or len(rows)>30:
                raise ValueError("invalid page")
            current=[cm.normalize_issue(repo,row) for row in rows]
            items.extend(current)
            coverage[repo]={"count":len(current),"possibly_truncated":len(rows)==30,"source_url":url}
        except (OSError,ValueError,TypeError,KeyError,AttributeError) as exc:
            errors.append({"source":url,"error":type(exc).__name__})
    result=freeze(items,now)
    result.update(coverage=coverage,errors=errors)
    return result

if __name__=="__main__":
    result=run(cm.get_json,dt.datetime.now(dt.timezone.utc))
    out=Path("results/collaboration-evaluation")
    out.mkdir(parents=True,exist_ok=True)
    (out/"frozen_cohort.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print("Evaluation coverage:",json.dumps(result["coverage"]))
    print("Evaluation errors:",json.dumps(result["errors"]))
    print("Evaluation cohort:",json.dumps({k:result[k] for k in ("corpus_sha256","eligible_sources","cases")}))
    if not result["cases"]:
        print("No eligible source cases; evaluation unavailable.")
