"""Read-only exact-ID OpenAIRE enrichment for discovered papers."""
import copy
import datetime as dt
import re
import time
import urllib.parse

from research_graph import fetch_json, openaire_node

API = "https://api.openaire.eu/graph/v4/research-products"
ID = re.compile(r"\d{4}\.\d{4,5}")

def source_url(pid):
    if not ID.fullmatch(pid):
        raise ValueError("unsupported arXiv identifier")
    return API + "?" + urllib.parse.urlencode({
        "filter": "ids.arxiv:" + pid, "page_size": 5,
        "select": "id,pids,mainTitle,type,organizations,projects,collectedFrom"})

def parse_result(pid, payload):
    rows = payload["results"]
    total = payload["header"]["numFound"]
    if not isinstance(rows, list) or type(total) is not int or total < len(rows) or len(rows) > 5 or (total and not rows):
        raise ValueError("invalid OpenAIRE result or pagination")
    records, mismatches = {}, 0
    for row in rows:
        node = openaire_node(row)
        if pid not in node["identifiers"]["arxiv"] or not row.get("id"):
            mismatches += 1
            continue
        # Retain the original source's assertions, including provenance if supplied.
        # No inference of cooperation, funding validation or current affiliation.
        records[row["id"]] = {
            "openaire_id": row["id"], "title": node["title"],
            "identifiers": node["identifiers"],
            "organizations": row.get("organizations") or [],
            "projects": row.get("projects") or [],
            "collected_from": row.get("collectedFrom") or [],
            "relationship": "exact_identifier_match",
            "review_only": True}
        if any(not isinstance(records[row["id"]][k], list) for k in ("organizations", "projects", "collected_from")):
            raise ValueError("unexpected relation schema")
    status = ("matched" if records else "not_indexed" if total == 0 else "unverified_response")
    return {"status": status, "records": sorted(records.values(), key=lambda x: x["openaire_id"]),
            "total": total, "mismatches": mismatches, "truncated": total > len(rows)}

def enrich(papers, now, *, previous=None, fetch=None, max_papers=6):
    if not 0 <= max_papers <= 12:
        raise ValueError("invalid OpenAIRE budget")
    previous = previous or {}
    observations = copy.deepcopy(previous.get("papers", {}))
    stamp = now.isoformat()
    errors, selected = [], []
    # Recent successes (including not indexed) are rechecked after 14 days.
    # Errors retry with the same fair rotation and never overwrite good evidence.
    def eligible(p):
        old = observations.get(p["id"], {})
        last = old.get("attempted_at")
        if not last or old.get("version_id") != p["version_id"]:
            return True
        ttl = 1 if old.get("last_attempt_status") == "source_error" else 14
        return now - dt.datetime.fromisoformat(last) >= dt.timedelta(days=ttl)
    queue = sorted((p for p in papers if ID.fullmatch(p["id"]) and eligible(p)),
                   key=lambda p: (observations.get(p["id"], {}).get("attempted_at", ""), p["id"]))
    for p in queue[:max_papers]:
        pid = p["id"]
        url = source_url(pid)
        if selected and fetch is None:
            time.sleep(1)
        selected.append(pid)
        old = observations.get(pid, {})
        try:
            result = parse_result(pid, (fetch or (lambda u: fetch_json(u, timeout=25)))(url))
            observations[pid] = {**result, "source_url": url, "retrieved_at": stamp,
                                 "attempted_at": stamp, "version_id": p["version_id"],
                                 "last_attempt_status": result["status"]}
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            errors.append({"source": url, "paper_id": pid, "error": type(exc).__name__})
            observations[pid] = {**old, "attempted_at": stamp, "version_id": p["version_id"],
                                 "last_attempt_status": "source_error"}
    return {"schema": 1, "retrieved_at": stamp, "papers": observations,
            "selected": selected, "eligible_count": len(queue), "errors": errors,
            "limitations": ["Exact arXiv identity, not independent validation of OpenAIRE relationships.",
                            "OpenAIRE may reuse the same upstream metadata as arXiv/ROR.",
                            "Not indexed is a timestamped observation, not proof of absence.",
                            "Bounded to modern arXiv identifiers and five records per query."]}
