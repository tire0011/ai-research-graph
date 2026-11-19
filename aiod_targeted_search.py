"""Bounded AIoD semantic-index keyword search for five real OpenEuroLLM needs.

The public /search/{asset} endpoint uses Elasticsearch keyword retrieval,
not verified requirement-equivalence, artifact reuse or human coordination.
No notifications, repository writes or model execution.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from aiod_catalogue_probe import API_HOSTS, fetch_json, normalise


ASSETS = ("projects", "datasets", "publications")
MAX_RESULTS = 5
MAX_QUERIES = 15
STOP_TERMS = {"a", "an", "and", "for", "in", "of", "on", "the", "to", "with"}

# Fixed before evaluating AIoD results. These are real issue goals, not
# retrospectively selected matches or positive ground-truth labels.
TARGETS = (
    (445, "Automatic evaluation reporting for model card", "model card"),
    (392, "Long context extension of prelude final checkpoint", "long context"),
    (353, "Discover and Verify Concepts in Preference and Instruction-tuning Datasets",
     "concept discovery"),
    (437, "Synthetic Generation for Multilingual Instruction Tuning",
     "multilingual instruction"),
    (360, "Define Data Compliance Governance Strategy", "data governance"),
)


def words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.casefold())
            if len(w) > 1 and w not in STOP_TERMS}


def search_url(host: str, asset_type: str, query: str, limit: int) -> str:
    if host not in API_HOSTS or asset_type not in ASSETS:
        raise ValueError("Unrecognized official AIoD host or searchable asset type")
    if (not isinstance(query, str) or not 2 <= len(query) <= 80
            or not re.fullmatch(r"[A-Za-z0-9 -]+", query)):
        raise ValueError("Expected short, safe, explicit research query")
    if type(limit) is not int or not 1 <= limit <= MAX_RESULTS:
        raise ValueError("Targeted query must be bounded")
    params = urllib.parse.urlencode({
        "search_query": query, "search_fields": "name", "limit": limit,
        "offset": 0, "get_all": "true", "exact_match": "false",
    })
    return f"{host}/search/{asset_type}?{params}"


def parse_search(body: object, *, asset_type: str, url: str,
                 host: str, limit: int) -> dict:
    if not isinstance(body, dict) or not isinstance(body.get("resources"), list):
        raise ValueError("Unexpected AIoD search envelope; expected resources list")
    hits = body.get("total_hits")
    resources = body["resources"]
    if (type(hits) is not int or hits < 0 or len(resources) > limit
            or type(body.get("offset")) is not int or body["offset"] != 0):
        raise ValueError("Invalid AIoD search count or pagination")
    if len(resources) > hits:
        raise ValueError("Search result count exceeds total hits")
    nodes = [normalise(item, asset_type, host, url) for item in resources]
    if len({n["id"] for n in nodes}) != len(nodes):
        raise ValueError("Duplicate AIoD v2 ID within one search response")
    return {"url": url, "total_hits": hits, "returned": len(nodes),
            "sample_limited": hits > len(nodes), "nodes": nodes}


def run(*, host: str = API_HOSTS[0], limit: int = 5,
        fetch=fetch_json, max_workers: int = 3,
        now: dt.datetime | None = None) -> dict:
    if type(max_workers) is not int or not 1 <= max_workers <= 3:
        raise ValueError("Too many concurrent public API requests")
    if now is None:
        now = dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Expected timezone-aware time")
    jobs = [(issue, title, query, asset)
            for issue, title, query in TARGETS for asset in ASSETS]
    if len(jobs) > MAX_QUERIES:
        raise ValueError("Too many targeted queries")

    def one(job):
        issue, title, query, asset = job
        url = search_url(host, asset, query, limit)
        result = parse_search(fetch(url), asset_type=asset, url=url,
                              host=host, limit=limit)
        return issue, asset, result

    fetched = {}
    # All results must succeed before writing a new report. Errors propagate
    # so an incomplete sample never looks like no relevant research exists.
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(one, job): job for job in jobs}
        for future in as_completed(futures):
            issue, asset, result = future.result()
            fetched[(issue, asset)] = result

    grouped = []
    for issue, title, query in TARGETS:
        pages = [fetched[(issue, asset)] for asset in ASSETS]
        seen, records = set(), []
        for page in pages:
            for node in page["nodes"]:
                # Avoid counting multiple search retrievals or claimed URL
                # aliases as separate independent opportunities *for this issue*.
                identity = node.get("original_url_claim") or node["id"]
                if identity in seen:
                    continue
                seen.add(identity)
                title_terms = sorted(words(query) & words(node["title"]))
                # Keep only identifiers/provenance, not copied full catalogue
                # abstracts. Reviewers can read the original API records.
                records.append({
                    **{k: v for k, v in node.items() if k != "description"},
                    "query_title_terms": title_terms,
                    "relevance_gate": "title_word_overlap_only" if len(title_terms) >= 2
                                      else "weak_keyword_result",
                    "collaboration_classification": "unreviewed",
                    "existing_coordination": "unknown",
                })
        records.sort(key=lambda r: (-len(r["query_title_terms"]), r["id"]))
        grouped.append({
            "github_issue": issue,
            "github_url": f"https://github.com/OpenEuroLLM/Taskboard/issues/{issue}",
            "github_title": title, "search_query": query,
            "asset_queries": [{k: v for k, v in p.items() if k != "nodes"} for p in pages],
            "retrieved_distinct_assets": len(records),
            "title_two_term_candidates": sum(
                r["relevance_gate"] == "title_word_overlap_only" for r in records),
            "candidates": records,
        })
    return {
        "schema": 1, "status": "live_search_retrieval_only",
        "generated_at_utc": now.isoformat(), "api_host": host,
        "github_source": "2026-11-11 live issue state checks, snapshot issue descriptions",
        "query_count": len(jobs), "per_query_limit": limit,
        "targets": grouped, "novel_collaboration_confirmed": False,
        "outreach": "none",
        "limitations": "AIoD search is broad and keyword-based; title overlaps are not "
                       "validated requirement equivalence. Small first-result windows; "
                       "source snapshots do not prove absent collaboration or availability "
                       "of implementation artifacts.",
    }


def markdown(report: dict) -> str:
    lines = ["# Five targeted OpenEuroLLM needs × AIoD search", "",
             f"{report['query_count']} live, bounded GET queries; "
             "retrieval only, **no confirmed new collaboration**.", "",
             "Queries were fixed before viewing AIoD results. Every result "
             "requires technical and coordination review.", ""]
    for target in report["targets"]:
        lines += [f"## [#{target['github_issue']}: {target['github_title']}]"
                  f"({target['github_url']})", "",
                  f"Search phrase: `{target['search_query']}`. "
                  f"{target['retrieved_distinct_assets']} distinct retrieved assets; "
                  f"{target['title_two_term_candidates']} title-level two-term overlaps.", ""]
        for page in target["asset_queries"]:
            lines.append(f"- [Search source]({page['url']}): "
                         f"{page['returned']} returned of {page['total_hits']} "
                         "hits (bounded, not exhaustive).")
        lines.append("")
        for n in target["candidates"][:8]:
            text = ", ".join(n["query_title_terms"]) or "no two-term title match"
            lines.append(f"- **{n['relevance_gate']}**: "
                         f"[{n['title'].replace('|', ' ')}]({n['url']}) "
                         f"({n['asset_type']}; overlap: {text})")
        if not target["candidates"]:
            lines.append("- No results in these bounded queries (not proof of absence).")
        lines.append("")
    lines += ["## Interpretation", "", report["limitations"], "",
              "A human reviewer must establish the requirement, implementation "
              "maturity, transferable artifact, existing coordination and a "
              "plausible next technical handoff. No external messages sent.", ""]
    return "\n".join(lines)


def write_success(report: dict, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "TARGETED_SEARCH_RESULTS.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (folder / "TARGETED_SEARCH_RESULTS.md").write_text(markdown(report), encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=API_HOSTS, default=API_HOSTS[0])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--output", default="results/aiod")
    args = parser.parse_args(argv)
    try:
        report = run(host=args.host, limit=args.limit)
        write_success(report, Path(args.output))
        print(f"AIoD targeted search: {report['query_count']} searches, "
              f"{sum(t['retrieved_distinct_assets'] for t in report['targets'])} "
              "candidate catalogue entries, no novelty claim")
        return 0
    except (OSError, ValueError, TypeError, KeyError, urllib.error.URLError,
            json.JSONDecodeError) as exc:
        print(f"AIoD targeted search source_error (good results preserved): "
              f"{type(exc).__name__}: {str(exc)[:180]}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
