"""Preregistered real GitHub Search API vs source-enriched task triage holdout.

Both methods share the same previously unseen GitHub Search result pool.
No graph superiority, fix completeness, maintainer approval or confirmed
resource fit is inferred from a public issue or from a literal cross-link.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.parse
from pathlib import Path

from eu_opportunity_discovery import is_stale, issue_comments, get_json
from opportunity_quality_review import review_rows
from opportunity_state import classify, related_pull_requests
from research_graph import identifiers_in

API = "https://api.github.com"
ISSUE = re.compile(r"^https://github\.com/([\w.-]+)/([\w.-]+)/issues/([1-9]\d*)$")
GITHUB_REF = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/(?:issues|pull)/[1-9]\d*")
HF = re.compile(r"https://huggingface\.co/(?:datasets/)?[\w.-]+/[\w.-]+")
SOURCE_PATH = re.compile(r"(?<![\w/.])(?:[\w.-]+/){1,6}[\w.-]+\.(?:py|rs|cs|ts|go)\b")
FILENAME = re.compile(r"^(?:[\w.-]+/){1,6}[\w.-]+\.(?:py|rs|cs|ts|go)$")
SHA = re.compile(r"^[0-9a-f]{40}$")
BLOCKER = re.compile(r"\b(?:HPC|Slurm|LUMI|multi.?GPU|multi.?node|GPU.cluster|"
                     r"training.cluster|large.scale.train(?:ing)?|MN5)\b", re.I)
REPRO = re.compile(r"\b(?:reproduc(?:e|ible|tion|ing)|failing.test|traceback|"
                   r"steps.to.reproduce|regression|test.case)\b", re.I)
TASK = re.compile(r"\b(?:fix|implement|add|bug|regression|support|failing|"
                  r"error|test|missing)\b", re.I)
PRIOR_WORK = re.compile(r"\b(?:i (?:already )?fixed|we (?:already )?built|"
                        r"i have implemented|i can (?:open|send) a pr|"
                        r"already implemented|already merged|the runs are queued)\b", re.I)
VOLUNTEER = {"help wanted", "good first issue", "contributions welcome", "up for grabs"}
QUESTION = {"question", "support", "discussion", "help"}


def check_config(cfg: dict, registry: dict) -> None:
    if cfg.get("schema") != 1 or registry.get("schema") != 1:
        raise ValueError("Unsupported study or source schema")
    scope = cfg.get("repository_scope")
    declared = sorted(x["repo"] for x in registry["repositories"])
    if not isinstance(scope, list) or len(scope) != 19 or scope != declared:
        raise ValueError("Repository scope changed: create a separate holdout")
    if cfg.get("search_terms") != ["bug", "test"]:
        raise ValueError("Holdout search terms are frozen")
    for key, low, high in (("repositories_per_query", 2, 5),
                           ("results_per_query", 1, 10),
                           ("max_deep_checks", 5, 30),
                           ("top_k", 3, 5)):
        n = cfg.get(key)
        if type(n) is not int or not low <= n <= high:
            raise ValueError(f"Invalid bounded search parameter {key}")
    if cfg["top_k"] > cfg["max_deep_checks"]:
        raise ValueError("top_k exceeds source review budget")


def search_queries(cfg: dict) -> list[dict]:
    names = cfg["repository_scope"]
    groups = [names[i:i + cfg["repositories_per_query"]]
              for i in range(0, len(names), cfg["repositories_per_query"])]
    plans = []
    for term in cfg["search_terms"]:
        for group_idx, repos in enumerate(groups):
            q = "is:issue is:open " + " ".join("repo:" + name for name in repos) + " " + term
            if len(q) > 256:
                raise ValueError("GitHub Search qualifier too long")
            params = urllib.parse.urlencode({"q": q, "per_page": cfg["results_per_query"]})
            plans.append({"id": f"{term}-group-{group_idx + 1}",
                          "query": q, "url": f"{API}/search/issues?{params}",
                          "repositories": repos})
    return plans


def collect_search(cfg: dict, fetch=get_json) -> dict:
    """Real Github REST /search/issues, not /repos/{repo}/issues."""
    plans = search_queries(cfg)
    per_query, meta = [], []
    allowed = {r.casefold() for r in cfg["repository_scope"]}
    for plan in plans:
        payload = fetch(plan["url"])
        if (not isinstance(payload, dict) or
                payload.get("incomplete_results") is not False or
                type(payload.get("total_count")) is not int or
                not isinstance(payload.get("items"), list)):
            raise ValueError(f"Incomplete GitHub Search API result: {plan['id']}")
        items = payload["items"]
        if len(items) > cfg["results_per_query"]:
            raise ValueError("GitHub Search API exceeded study query budget")
        rows = []
        for rank, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                raise ValueError("Non-object GitHub Search result")
            url = item.get("html_url")
            m = ISSUE.fullmatch(url) if isinstance(url, str) else None
            if (m is None or "/".join(m.groups()[:2]).casefold() not in allowed
                    or "pull_request" in item or item.get("state") != "open"
                    or not isinstance(item.get("updated_at"), str)
                    or not isinstance(item.get("title"), str)
                    or not isinstance(item.get("body"), (str, type(None)))
                    or type(item.get("comments")) is not int):
                raise ValueError("GitHub Search returned malformed or out-of-scope issue")
            if "/".join(m.groups()[:2]).casefold() not in {
                    x.casefold() for x in plan["repositories"]}:
                raise ValueError("GitHub Search returned issue outside its query group")
            rows.append({
                "issue_url": url, "repository": "/".join(m.groups()[:2]),
                "number": int(m.group(3)), "title": item["title"],
                "body": item.get("body") or "", "updated_at": item["updated_at"],
                "comments": item["comments"], "labels": item.get("labels", []),
                "assignees": item.get("assignees", []),
                "source_query": plan["id"], "query_rank": rank,
            })
        meta.append({**plan, "total_count": payload["total_count"],
                     "returned": len(rows), "incomplete_results": False})
        per_query.append(rows)

    # Round-robin the *actual GitHub relevance order within each query*.
    # Same stratified raw pool is subsequently used for both methods.
    baseline, seen = [], set()
    for pos in range(cfg["results_per_query"]):
        for rows in per_query:
            if pos >= len(rows):
                continue
            row = rows[pos]
            if row["issue_url"].casefold() not in seen:
                seen.add(row["issue_url"].casefold())
                baseline.append(row)
    return {"search_queries": meta, "raw_candidates": baseline}


def past_reviews(ledger: dict) -> set[str]:
    # Exact exclusion ONLY; historical tier labels never affect ranking.
    return {r["issue_url"].casefold() for r in review_rows(ledger)}


def extract_context(body: str, comments: list[dict]) -> list[dict]:
    """Explicit typed links; edges mean 'mentioned', not reused or dependent."""
    corpus = body + "\n" + "\n".join(c.get("body") or "" for c in comments)
    edges, seen = [], set()
    ids = identifiers_in(corpus)
    for typ, values in (
        ("github_reference", GITHUB_REF.findall(corpus)),
        ("huggingface_reference", HF.findall(corpus)),
        ("doi_mentioned", ["https://doi.org/" + x for x in ids["doi"]]),
        ("arxiv_mentioned", ["https://arxiv.org/abs/" + x for x in ids["arxiv"]]),
    ):
        for url in values[:10]:
            if url in seen:
                continue
            seen.add(url)
            edges.append({"type": typ, "url": url,
                          "interpretation": "literal_mention_only"})
    return edges[:25]


def confirm_code_links(fetch, repo: str, body: str) -> list[dict]:
    """Bounded source code path existence checks, not proof code must change."""
    paths = list(dict.fromkeys(SOURCE_PATH.findall(body)))[:2]
    found = []
    for path in paths:
        if not FILENAME.fullmatch(path) or ".." in path or len(path) > 160:
            continue
        url = f"{API}/repos/{repo}/contents/{urllib.parse.quote(path, safe='/')}"
        try:
            doc = fetch(url)
        except (ValueError, TypeError, KeyError, OSError, TimeoutError):
            continue
        canonical = f"https://github.com/{repo}/blob/"
        if (isinstance(doc, dict) and doc.get("type") == "file"
                and isinstance(doc.get("sha"), str)
                and SHA.fullmatch(doc["sha"])
                and isinstance(doc.get("html_url"), str)
                and doc["html_url"].casefold().startswith(canonical.casefold())):
            found.append({"type": "repository_code_file", "path": path,
                          "url": doc["html_url"], "blob_sha": doc["sha"],
                          "interpretation": "file_exists_not_verified_fix_location"})
    return found


def resource_fit(issue: dict, comments: list[dict]) -> dict:
    body = (issue.get("title") or "") + "\n" + (issue.get("body") or "")
    labels = {x.get("name", "").casefold() for x in issue.get("labels", [])
              if isinstance(x, dict) and isinstance(x.get("name"), str)}
    extended = body + "\n" + "\n".join(c.get("body") or "" for c in comments)
    reasons = []
    if BLOCKER.search(extended):
        reasons.append("possibly_requires_hpc_or_specialized_infrastructure")
    if labels & QUESTION:
        reasons.append("question_or_discussion_not_scoped_code_task")
    if PRIOR_WORK.search(extended):
        reasons.append("existing_solution_or_contributor_offer_may_be_present")
    return {"status": "needs_human_confirmation" if reasons else "not_obviously_blocked",
            "reasons": reasons, "not_proof_of_local_feasibility": True}


def evidence_score(issue: dict, context: list[dict], files: list[dict]) -> dict:
    """Prespecified evidence ranking, not tuned against previous labels."""
    body = (issue.get("title") or "") + "\n" + (issue.get("body") or "")
    labels = {x.get("name", "").casefold() for x in issue.get("labels", [])
              if isinstance(x, dict) and isinstance(x.get("name"), str)}
    parts = {
        "volunteer_label": 3 if labels & VOLUNTEER else 0,
        "explicit_reproduction": 2 if REPRO.search(body) else 0,
        "implementation_verb": 1 if TASK.search(body) else 0,
        "verified_code_reference": 2 if files else 0,
        "linked_context": 1 if context else 0,
    }
    return {"score": sum(parts.values()), "parts": parts,
            "no_scientific_impact_claim": True}


def inspect(row: dict, cfg: dict, fetch=get_json, *, now=None) -> dict:
    repo, num, url = row["repository"], row["number"], row["issue_url"]
    base = {key: row[key] for key in ("issue_url", "repository", "number",
                                    "title", "updated_at", "source_query", "query_rank")}
    try:
        fresh = fetch(f"{API}/repos/{repo}/issues/{num}")
        if (not isinstance(fresh, dict) or fresh.get("html_url") != url or
                fresh.get("updated_at") != row["updated_at"] or
                fresh.get("body") != row["body"] or
                fresh.get("comments") != row["comments"] or fresh.get("state") != "open"):
            raise ValueError("Source changed since GitHub Search snapshot")
        comments = issue_comments(fetch, repo, fresh)
        linked = related_pull_requests(fetch, url)
        disposition = classify(fresh, comments, linked, actor=cfg["actor"])
        fit = resource_fit(fresh, comments)
        links = extract_context(fresh.get("body") or "", comments)
        paths = confirm_code_links(fetch, repo, fresh.get("body") or "")
        score = evidence_score(fresh, links, paths)
        if is_stale(fresh["updated_at"], now=now):
            disposition = {"status": "needs_review", "reason": "stale_issue",
                           "evidence_urls": [url]}
        return {**base, "verification": "complete",
                "state": disposition, "resource_fit": fit,
                "context_edges": links, "code_files": paths,
                "score": score, "comment_count": len(comments),
                "related_prs": linked}
    except (ValueError, TypeError, KeyError, OSError, TimeoutError) as exc:
        return {**base, "verification": "failed",
                "state": {"status": "needs_review",
                          "reason": "source_context_incomplete",
                          "evidence_urls": [url]},
                "resource_fit": {"status": "unknown"},
                "context_edges": [], "code_files": [],
                "score": {"score": 0, "parts": {}},
                "verification_error": type(exc).__name__}


def build(cfg: dict, registry: dict, ledger: dict, fetch=get_json, *, now=None) -> dict:
    check_config(cfg, registry)
    if not isinstance(cfg.get("actor"), str) or not cfg["actor"]:
        raise ValueError("Missing comparison contributor")
    queries = collect_search(cfg, fetch)
    old = past_reviews(ledger)
    unseen = [x for x in queries["raw_candidates"]
              if x["issue_url"].casefold() not in old]
    batch = unseen[:cfg["max_deep_checks"]]
    baseline_top = [x["issue_url"] for x in batch[:cfg["top_k"]]]
    verified = [inspect(row, cfg, fetch, now=now) for row in batch]
    eligible = [x for x in verified if x["verification"] == "complete"
                and x["state"]["status"] == "new"
                and x["resource_fit"]["status"] == "not_obviously_blocked"]
    # Stable tie break by original GitHub Search arrival order.
    eligible.sort(key=lambda x: -x["score"]["score"])
    graph_top = [x["issue_url"] for x in eligible[:cfg["top_k"]]]
    return {
        "schema": 1, "holdout_date": cfg["date"], "profile": cfg["profile"],
        "question": cfg["question"], "created_at_utc": dt.datetime.now(
            dt.timezone.utc).isoformat(),
        "status": "review_pending",
        "search_queries": queries["search_queries"],
        "raw_search_candidates": len(queries["raw_candidates"]),
        "past_review_exclusions": len(queries["raw_candidates"]) - len(unseen),
        "same_pool_count": len(batch),
        "query_pool_urls": [x["issue_url"] for x in batch],
        "github_search_baseline_top5": baseline_top,
        "graph_enriched_top5": graph_top,
        "deeply_verified": sum(x["verification"] == "complete" for x in verified),
        "all_inspected": verified,
        "comparison": {
            "shared_candidate_pool": True,
            "overlap_at_k": len(set(baseline_top) & set(graph_top)),
            "verified_quality_difference": None,
            "outcome": "needs_independent_method_blinded_task_review",
            "baseline_method": "stratified_real_github_search_api_relevance_order",
            "enriched_method": "same_api_pool_with_verified_issues_pr_context_code_links",
        },
        "limitations": [
            "Graph-enriched method is a typed GitHub-context overlay, not an OpenAIRE-informed graph query.",
            "Both arms share a bounded stratified search pool, so retrieval recall is not tested.",
            "The enrichment method has extra API calls; latency and request budget differ.",
            "A verified file reference is not a verified code-change location.",
            "Lack of an observed HPC signal does not prove no GPU or HPC is required.",
            "No maintainer approval or demonstrated advantage until blind rating is supplied.",
        ],
    }


def blind_sheet(result: dict, cfg: dict) -> dict:
    selected = set(result["github_search_baseline_top5"]) | set(
        result["graph_enriched_top5"])
    by_url = {x["issue_url"]: x for x in result["all_inspected"]}
    rows = []
    for url in selected:
        row = by_url[url]
        rows.append({
            "anonymous_id": hashlib.sha256(
                (cfg["date"] + "|" + url).encode()).hexdigest()[:12],
            "source_url": url, "title": row["title"],
            "rubric": "0=not_new, 1=unclear, 2=plausible_code_task, 3=maintainer_confirmed",
            "rating": None, "rationale": None,
            "reviewer": None,
        })
    rows.sort(key=lambda x: x["anonymous_id"])
    return {"schema": 1, "blinded_to_method": True,
            "instructions": "Reviewer reads each linked live source and code; ratings 0-3 with evidence rationale. Do not show method assignment until ratings finalized.",
            "items": rows, "review_complete": False}


def judge(result: dict, sheet: dict) -> dict:
    """Fail closed on missing human assessments; scores never manufacture labels."""
    if not isinstance(sheet, dict) or sheet.get("blinded_to_method") is not True:
        raise ValueError("Missing method-blind review")
    rows = sheet.get("items")
    if not isinstance(rows, list) or not rows:
        raise ValueError("No blind review rows")
    required = set(result["github_search_baseline_top5"]) | set(
        result["graph_enriched_top5"])
    if {r.get("source_url") for r in rows if isinstance(r, dict)} != required:
        raise ValueError("Blind review sample differs from frozen selections")
    decisions = {}
    for r in rows:
        if (type(r.get("rating")) is not int or r["rating"] not in (0, 1, 2, 3)
                or not isinstance(r.get("rationale"), str) or len(r["rationale"]) < 20
                or not isinstance(r.get("reviewer"), str) or not r["reviewer"].strip()):
            raise ValueError("Review incomplete: cannot claim measurable advantage")
        decisions[r["source_url"]] = r["rating"]
    return {
        "review_method": "manual_method_blinded_labels",
        "github_search_plausible_at5": sum(decisions[x] >= 2 for x in
                                           result["github_search_baseline_top5"]),
        "graph_enriched_plausible_at5": sum(decisions[x] >= 2 for x in
                                           result["graph_enriched_top5"]),
        "count_reviewed": len(rows),
        "confidence": "small_nonrepresentative_holdout_not_a_general_precision_estimate",
    }


def markdown(result: dict) -> str:
    lines = [
        "# Real GitHub Search API versus typed graph-context enrichment", "",
        f"**Question:** {result['question']}", "",
        f"Study state: **{result['status']}**. Sources: {len(result['search_queries'])} "
        f"GitHub Search API calls; same-pool issues: {result['same_pool_count']}, "
        f"deeply verified: {result['deeply_verified']}.", "",
        "| Rank | GitHub Search API | Graph-context-enriched triage |",
        "| --- | --- | --- |",
    ]
    a, b = result["github_search_baseline_top5"], result["graph_enriched_top5"]
    for i in range(max(len(a), len(b))):
        def name(url):
            if not url:
                return "—"
            return f"[{url.rsplit('/', 1)[-1]}]({url})"
        lines.append(f"| {i+1} | {name(a[i] if i < len(a) else None)} | "
                     f"{name(b[i] if i < len(b) else None)} |")
    lines += ["", "**No winner has been established.** "
              "Complete the method-blinded issue assessments before interpreting rank differences.", "",
              "## Recorded query strings", ""]
    lines += [f"- \`{q['query']}\` — returned {q['returned']} of {q['total_count']}"
              for q in result["search_queries"]]
    lines += ["", "## Limits", ""]
    lines += [f"- {x}" for x in result["limitations"]]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="studies/github_search_graph_holdout_20261121/config.json")
    p.add_argument("--registry", default="eu_opportunity_sources.json")
    p.add_argument("--ledger", default="studies/eu_opportunity_quality_20261121/reviews.json")
    p.add_argument("--output", default="results/github_search_graph_holdout")
    args = p.parse_args(argv)
    try:
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
        registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
        ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
        result = build(cfg, registry, ledger)
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=True)
        for name, doc in (
            ("comparison.json", result),
            ("method_blind_review_template.json", blind_sheet(result, cfg)),
        ):
            (output / name).write_text(json.dumps(
                doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (output / "COMPARISON.md").write_text(markdown(result), encoding="utf-8")
        print("GitHub Search / graph context: "
              f"{result['same_pool_count']} held-out issues, "
              f"{result['deeply_verified']} checked; "
              f"baseline {len(result['github_search_baseline_top5'])}, "
              f"graph {len(result['graph_enriched_top5'])}; "
              "independent grading pending")
        if result["deeply_verified"] < 5:
            return 2
        return 0
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"Holdout failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
