"""Bounded, evidence-based discovery across a curated set of European open AI repos.

The input registry is reviewed, NOT automatically inferred as "all European AI".
The shortlist is not a claim of project impact or maintainer approval.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.parse
from collections import Counter
from pathlib import Path

from http_util import get_json as shared_get_json
from opportunity_state import classify, related_pull_requests
from opportunity_quality_review import (annotate as annotate_quality,
                                        fetch_code_heads, markdown as quality_markdown)

API = "https://api.github.com"
REPO_RE = re.compile(r"^[\w.-]+/[\w.-]+$")
ACTOR_RE = re.compile(r"^[A-Za-z\d](?:[A-Za-z\d-]{0,37}[A-Za-z\d])?$")
MAX_SOURCES = 40
TERMS = re.compile(r"\b(?:bug|fix|fail(?:ure|ing|ed|s)?|broken|regression|test(?:ing|s)?|"
                   r"benchmark|evaluation|performance|memory|dataset|metadata|"
                   r"compatibility|support|implement|improve|documentation|"
                   r"migration|interopera\w*|reproduc\w*|error|missing|incorrect)\b", re.I)
EVIDENCE_TERMS = re.compile(r"\b(?:reproduc\w*|steps to reproduce|expected behavior|"
                            r"acceptance criteria|test case|traceback|failing tests?)\b", re.I)
VOLUNTEER_LABELS = {"good first issue", "help wanted", "up for grabs", "contributions welcome"}
QUESTION_LABELS = {"question", "support", "discussion", "help"}
FRESHNESS_DAYS = 365


def get_json(url):
    return shared_get_json(url, user_agent="european-open-ai-opportunity-pilot")[0]


def validate(config, *, allow_single_owner=False):
    if config.get("schema") != 1 or not isinstance(config.get("repositories"), list):
        raise ValueError("Unsupported source registry")
    sources = config["repositories"]
    if not (1 if allow_single_owner else 2) <= len(sources) <= MAX_SOURCES:
        raise ValueError("Need a bounded multi-repository registry")
    repos = [x.get("repo") for x in sources if isinstance(x, dict)]
    if (len(repos) != len(sources) or any(not isinstance(x, str) or not REPO_RE.fullmatch(x)
                                         for x in repos) or len(set(repos)) != len(repos)):
        raise ValueError("Invalid or duplicate repositories")
    if not allow_single_owner and len({name.split("/")[0].lower() for name in repos}) < 2:
        raise ValueError("Sources must include multiple organizations")
    for x in sources:
        if not isinstance(x.get("area"), str) or not x["area"].strip() or not x.get("region"):
            raise ValueError("Missing source rationale")
    for key, low, high in (("max_issues_per_repo", 1, 30),
                           ("candidate_checks_per_repo", 1, 5),
                           ("max_new_suggestions", 1, 10)):
        n = config.get(key)
        if type(n) is not int or not low <= n <= high:
            raise ValueError(f"Invalid bound: {key}")
    actor = config.get("actor")
    if not isinstance(actor, str) or not ACTOR_RE.fullmatch(actor):
        raise ValueError("Invalid contributor login")


def list_recent(fetch, repo, limit):
    """Latest updated open issues, explicitly not exhaustive coverage."""
    query = urllib.parse.urlencode({"state": "open", "sort": "updated",
                                    "direction": "desc", "per_page": 100, "page": 1})
    rows = fetch(f"{API}/repos/{repo}/issues?{query}")
    if not isinstance(rows, list):
        raise ValueError(f"Invalid GitHub issue listing for {repo}")
    issues = []
    for item in rows:
        if not isinstance(item, dict) or type(item.get("number")) is not int:
            raise ValueError(f"Bad GitHub row in {repo}")
        if "pull_request" in item:
            continue
        if item.get("state") != "open" or item.get("html_url") != (
                f"https://github.com/{repo}/issues/{item['number']}"):
            raise ValueError(f"Invalid issue identity in {repo}")
        if not isinstance(item.get("title"), str) or not isinstance(item.get("updated_at"), str):
            raise ValueError(f"Missing issue text/timestamp in {repo}")
        issues.append(item)
        if len(issues) == limit:
            break
    return issues


def preliminary_score(item, *, now=None):
    """Transparent, non-scientific triage. Not a proof of an actionable task."""
    text = item["title"] + "\n" + (item.get("body") or "")
    labels = {v.get("name", "").casefold() for v in item.get("labels", [])
              if isinstance(v, dict) and isinstance(v.get("name"), str)}
    score = min(3, len(set(v.group(0).casefold() for v in TERMS.finditer(text))))
    if labels & VOLUNTEER_LABELS:
        score += 3
    if EVIDENCE_TERMS.search(text):
        score += 2
    if item.get("assignees"):
        score -= 2
    if labels & QUESTION_LABELS:
        score -= 4
    try:
        if is_stale(item["updated_at"], now=now):
            score -= 3
    except (ValueError, TypeError):
        score -= 3
    return score


def is_stale(updated_at, *, now=None):
    """Reject old or invalid dates as fresh opportunity evidence."""
    if not isinstance(updated_at, str):
        raise ValueError("Invalid issue update date")
    stamp = dt.datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Missing timezone on issue update")
    current = now or dt.datetime.now(dt.timezone.utc)
    if current.tzinfo is None:
        raise ValueError("Missing timezone for current time")
    if stamp > current + dt.timedelta(days=1):
        raise ValueError("Issue update date in future")
    return current - stamp > dt.timedelta(days=FRESHNESS_DAYS)


def issue_comments(fetch, repo, item):
    """No partial lists: if comments are too many, abstain, not 'new'."""
    count = item.get("comments")
    if type(count) is not int or count < 0 or count > 100:
        raise ValueError("Incomplete or unknown comment count")
    if not count:
        return []
    url = f"{API}/repos/{repo}/issues/{item['number']}/comments?per_page=100&page=1"
    comments = fetch(url)
    if not isinstance(comments, list) or len(comments) != count:
        raise ValueError("Incomplete comment fetch")
    if any(not isinstance(c, dict) or not isinstance(c.get("user"), dict)
           or not isinstance(c.get("user", {}).get("login"), str) for c in comments):
        raise ValueError("Invalid comment authors")
    return comments


def build(config, fetch=get_json, *, now=None, allow_single_owner=False):
    validate(config, allow_single_owner=allow_single_owner)
    actor = config["actor"]
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Current date must be timezone-aware")
    records, errors, examined = [], [], 0
    for source in config["repositories"]:
        repo = source["repo"]
        # Fail per source rather than erase other verified results.
        try:
            issues = list_recent(fetch, repo, config["max_issues_per_repo"])
        except (ValueError, TypeError, KeyError, urllib.error.URLError, TimeoutError) as exc:
            errors.append({"repository": repo, "stage": "list", "error": type(exc).__name__})
            continue
        examined += len(issues)
        pool = sorted(issues, key=lambda i: (-preliminary_score(i, now=now), i["number"]))
        for item in pool[:config["candidate_checks_per_repo"]]:
            url = item["html_url"]
            try:
                # Re-read the original before presenting any recommendation.
                fresh = fetch(f"{API}/repos/{repo}/issues/{item['number']}")
                if (not isinstance(fresh, dict) or fresh.get("html_url") != url or
                        fresh.get("state") != "open" or
                        fresh.get("updated_at") != item.get("updated_at") or
                        fresh.get("body") != item.get("body") or
                        fresh.get("comments") != item.get("comments")):
                    raise ValueError("Source changed or identity mismatch")
                comments = issue_comments(fetch, repo, fresh)
                related = related_pull_requests(fetch, url)
                disposition = classify(fresh, comments, related, actor=actor)
                if disposition["status"] == "new":
                    labels = {x.get("name", "").casefold() for x in fresh.get("labels", [])
                              if isinstance(x, dict) and isinstance(x.get("name"), str)}
                    if labels & QUESTION_LABELS:
                        disposition = {"status": "needs_review",
                                       "reason": "question_not_confirmed_implementation_task",
                                       "evidence_urls": [url]}
                    elif is_stale(fresh["updated_at"], now=now):
                        disposition = {"status": "needs_review",
                                       "reason": "stale_issue_requires_maintainer_reconfirmation",
                                       "evidence_urls": [url]}
            except (ValueError, TypeError, KeyError, urllib.error.URLError, TimeoutError) as exc:
                # Show an unverified candidate only if its GitHub identity is sound.
                errors.append({"repository": repo, "issue_url": url, "stage": "verify",
                               "error": type(exc).__name__})
                disposition = {"status": "needs_review", "reason": "source_or_pr_check_failed",
                               "evidence_urls": [url]}
                related = []
            labels = [x.get("name") for x in item.get("labels", [])
                      if isinstance(x, dict) and isinstance(x.get("name"), str)]
            records.append({
                "repository": repo, "area": source["area"], "issue_number": item["number"],
                "issue_url": url, "title": item["title"], "updated_at": item["updated_at"],
                "comment_count": item.get("comments"),
                "score": preliminary_score(item, now=now), "score_meaning": "rule_based_triage_not_impact",
                "labels": labels, "assignees": [v.get("login") for v in item.get("assignees", [])
                                                 if isinstance(v, dict)],
                "state": disposition, "related_prs": related, "review_only": True,
            })
    records.sort(key=lambda c: (-c["score"], c["repository"], c["issue_number"]))
    suggestions = [c for c in records if c["state"]["status"] == "new"][
        :config["max_new_suggestions"]]
    # Transparent baseline: identical items, title-only keyword score, no graph.
    baseline = sorted(records, key=lambda c: (
        -len(set(v.group(0).lower() for v in TERMS.finditer(c["title"]))),
        c["repository"], c["issue_number"]))
    baseline_new = [c["issue_url"] for c in baseline if c["state"]["status"] == "new"][
        :config["max_new_suggestions"]]
    return {
        "schema": 1, "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "actor": actor, "sources": len(config["repositories"]), "sampled_issues": examined,
        "fully_checked": len(records) - sum(e["stage"] == "verify" for e in errors),
        "candidate_count": len(records), "state_counts": dict(Counter(
            c["state"]["status"] for c in records)),
        "new_top5": suggestions, "same_source_title_baseline_urls": baseline_new,
        "all_reviewed": records, "errors": errors,
        "limitations": [
            "Curated, latest-updated issue sampling, not an exhaustive EU AI index.",
            "Scores are lexical heuristics, not demonstrated impact or graph advantage.",
            "Both rankings use exactly the same collected issue pool and state checks.",
            "A cross-referenced PR or assignment does not prove work is complete.",
            "Support questions and issues unchanged for over a year require maintainer reconfirmation.",
            "No maintainer approval, duplicate-work prevention, time saved, or outreach is claimed.",
        ],
    }


def markdown(result):
    lines = [
        "# European open AI contributor opportunities — read-only pilot", "",
        f"Sources: **{result['sources']} repositories**, sampled **{result['sampled_issues']}** "
        f"open issues; **{result['fully_checked']}** candidates fully checked.",
        f"Contributor: {result['actor']}. Errors: **{len(result['errors'])}**.", "",
        "## Up to five new tasks for human review", "",
    ]
    if not result["new_top5"]:
        lines.append("No verified new tasks in the bounded sample; this does not mean none exist.")
    for c in result["new_top5"]:
        lines.extend([f"- [{c['repository']}#{c['issue_number']}: {c['title']}]({c['issue_url']})",
                      f"  - Area: {c['area']}; reason: {c['state']['reason']}; "
                      "confirm maintainer needs before contributing"])
    lines += ["", "## Same-source plain-title baseline", ""]
    lines += [f"- {url}" for url in result["same_source_title_baseline_urls"]]
    lines += ["", "## Status counts", ""]
    lines += [f"- {key}: {value}" for key, value in sorted(result["state_counts"].items())]
    lines += ["", "## Limitations", ""]
    lines += [f"- {v}" for v in result["limitations"]]
    if result["errors"]:
        lines += ["", "## Incomplete source checks", ""]
        lines += [f"- {v['repository']}: {v['stage']} ({v['error']})"
                  for v in result["errors"]]
    return "\n".join(lines) + "\n"


def source_discovery_usable(expansion):
    """Require fresh successful retrieval, not merely retained historical state."""
    return bool(expansion["listings"] or any(
        item["status"] == "confirmed_public_metadata"
        for item in expansion["detail_checks"]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default="eu_opportunity_sources.json")
    parser.add_argument("--output", default="results/european_ai")
    parser.add_argument("--review-ledger", default=None,
                        help="Optional source-pinned manual actionability review JSON")
    parser.add_argument("--discover-sources", action="store_true")
    parser.add_argument("--previous-candidates", default=None)
    args = parser.parse_args(argv)
    try:
        config = json.loads(Path(args.sources).read_text(encoding="utf-8"))
        source_errors = []
        source_usable = True
        if args.discover_sources:
            from eu_source_discovery import discover, write_report
            previous = json.loads(Path(args.previous_candidates).read_text(encoding="utf-8")) if args.previous_candidates and Path(args.previous_candidates).exists() else None
            expansion = discover(config, previous=previous)
            write_report(expansion, args.output)
            source_errors = expansion["errors"]
            source_usable = source_discovery_usable(expansion)
            for error in source_errors:
                print(f"Source discovery diagnostic: {json.dumps(error)}", file=sys.stderr)
            if source_errors and source_usable:
                print("::warning::Partial source discovery; successful observations retained, see SOURCE_DISCOVERY.md")
            if not source_usable:
                print("Source discovery has no fresh successful retrieval", file=sys.stderr)
        result = build(config)
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        (out / "opportunities.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (out / "OPPORTUNITIES.md").write_text(markdown(result), encoding="utf-8")
        if args.review_ledger:
            ledger = json.loads(Path(args.review_ledger).read_text(encoding="utf-8"))
            reviewed = annotate_quality(result, ledger,
                                        code_heads=fetch_code_heads(ledger, get_json))
            (out / "quality_review.json").write_text(
                json.dumps(reviewed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            (out / "QUALITY_REVIEW.md").write_text(quality_markdown(reviewed), encoding="utf-8")
        print(f"EU AI: {result['sampled_issues']} sampled, {result['candidate_count']} "
              f"triaged, {len(result['new_top5'])} new, {len(result['errors'])} errors")
        return 0 if not result["errors"] and source_usable else 2
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"EU discovery failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
