"""Read-only evidence-backed discovery of 50 independently selected open Taskboard issues.

No GitHub writes, notifications, or inferred scientific gains.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

from opportunity_feedback import read_feedback

REPO = "OpenEuroLLM/Taskboard"
LIMIT = 50
MAX_PAGES = 30
MAX_COMMENTS = 100
GITHUB = "https://api.github.com"
LOGIN = re.compile(r"^[A-Za-z\d](?:[A-Za-z\d-]{0,37}[A-Za-z\d])?$")
SIGNALS = {
    "reported_memory_issue": (
        re.compile(r"\b(?:OOM|out[ -]of[ -]memory|memory exhaustion|runs? out of (?:GPU )?memory)\b", re.I),
        "Reported memory difficulty; reproduce it and locate the failure phase.",
    ),
    "performance_mention": (
        re.compile(r"\b(?:speedup|faster|\d+(?:\.\d+)?\s*%\s*(?:improvement|faster)|\d+(?:\.\d+)?\s*[kKmM]?\s*tokens/s)\b", re.I),
        "Reported performance phrase, not an independently reproduced gain; request comparable measurements.",
    ),
}
DEPENDENCY = re.compile(
    r"(?im)^\s*(?:#{1,4}\s*)?(?:\*\*|__)?dependenc(?:y|ies)(?:\*\*|__)?\s*:?\s*"
    r"(?:\r?\n\s*)?(?:[-*]\s*)?(?:issue\s*)?#(?P<target>[1-9]\d*)\b"
)


def digest(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def get_json(url: str):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ai-research-graph-discovery"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code < 500 and exc.code not in (408, 429):
                raise
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def list_population(fetch=get_json):
    """Exhaust the open issue listing; selection only sees numeric IDs, never bodies."""
    issues = []
    for page in range(1, MAX_PAGES + 1):
        query = urllib.parse.urlencode({"state": "open", "per_page": 100, "page": page})
        batch = fetch(f"{GITHUB}/repos/{REPO}/issues?{query}")
        if not isinstance(batch, list):
            raise ValueError("Invalid GitHub issue listing")
        issues.extend({"number": row["number"]} for row in batch if "pull_request" not in row)
        if len(batch) < 100:
            break
    else:
        raise ValueError("Open-issue population exceeds page cap; refuse biased partial sample")
    if len({x["number"] for x in issues}) != len(issues):
        raise ValueError("Duplicate issue IDs while paging; population changed")
    return issues


def select(population, excluded: set[int], seed: str, limit=LIMIT):
    """ID-hash sample rotating by ISO week, excluding all ten prior impact case studies."""
    candidates = [i["number"] for i in population if i["number"] not in excluded]
    if len(candidates) < limit:
        raise ValueError(f"Only {len(candidates)} eligible open issues; need {limit}")
    return sorted(candidates, key=lambda n: (digest(f"{seed}:{REPO}#{n}"), n))[:limit]


def excerpt(body: str, match: re.Match) -> str:
    return body[max(0, match.start() - 65):min(len(body), match.end() + 65)]


def identify(issue: dict, comments: list[dict]):
    """Literal source phrases only, never measured improvements or inferred blockers."""
    sources = [("issue_body", issue, issue["html_url"])]
    sources += [("issue_comment", c, c["html_url"]) for c in comments]
    found: dict[str, list[dict]] = {}
    for origin, item, url in sources:
        body = item.get("body") or ""
        for kind, (pattern, _) in SIGNALS.items():
            hit = pattern.search(body)
            if hit:
                found.setdefault(kind, []).append({
                    "origin": origin, "source_url": url, "sha256": digest(body),
                    "quote": excerpt(body, hit), "updated_at": item.get("updated_at"),
                    "comment_id": item.get("id") if origin == "issue_comment" else None,
                })
        if origin == "issue_body":
            match = DEPENDENCY.search(body)
            if match and int(match.group("target")) != issue["number"]:
                found.setdefault("declared_dependency", []).append({
                    "origin": origin, "source_url": url, "sha256": digest(body),
                    "quote": body[match.start():match.end()],
                    "updated_at": item.get("updated_at"),
                    "target_issue": int(match.group("target")), "comment_id": None,
                })
    return {kind: proofs[:3] for kind, proofs in found.items()}


def verify_source(issue: dict, proof: dict, fetch=get_json):
    """Independently re-fetch supporting comments and verify exact source SHA and text."""
    if proof["origin"] == "issue_comment":
        record = fetch(f"{GITHUB}/repos/{REPO}/issues/comments/{proof['comment_id']}")
        if record.get("id") != proof["comment_id"]:
            raise ValueError("Comment ID drift")
    else:
        record = issue
    if (digest(record.get("body") or "") != proof["sha256"]
            or record.get("updated_at") != proof["updated_at"]
            or proof["quote"] not in (record.get("body") or "")
            or record.get("html_url") != proof["source_url"]):
        raise ValueError(f"Changed or invalid supporting text at {proof['source_url']}")


def build(fetch=get_json, *, excluded=None, seed=None, feedback=None):
    """Fail closed on stale or incomplete sources before writing reports."""
    excluded = set() if excluded is None else set(excluded)
    seed = seed or dt.datetime.now(dt.timezone.utc).strftime("%G-W%V")
    population = list_population(fetch)
    selected = select(population, excluded, seed)
    feedback = {} if feedback is None else feedback
    cards, verified = [], 0
    for number in selected:
        url = f"{GITHUB}/repos/{REPO}/issues/{number}"
        original = fetch(url)
        if (original.get("number") != number or original.get("state") != "open"
                or "pull_request" in original
                or not isinstance(original.get("body"), (str, type(None)))
                or original.get("html_url") != f"https://github.com/{REPO}/issues/{number}"):
            raise ValueError(f"Invalid or stale selected issue #{number}")
        comments = []
        count = original.get("comments", 0)
        if not isinstance(count, int) or count < 0 or count > MAX_COMMENTS:
            raise ValueError(f"Issue #{number}: unknown or excessive comment count")
        if count:
            comments = fetch(f"{url}/comments?per_page=100&page=1")
            if (not isinstance(comments, list) or len(comments) != count
                    or any(not isinstance(c.get("body"), (str, type(None)))
                           or not isinstance(c.get("id"), int) for c in comments)):
                raise ValueError(f"Issue #{number}: partial comment listing")
        signals = identify(original, comments)
        reread = fetch(url)
        if (reread.get("number") != number or reread.get("state") != "open"
                or reread.get("updated_at") != original.get("updated_at")
                or reread.get("comments") != original.get("comments")
                or digest(reread.get("body") or "") != digest(original.get("body") or "")):
            raise ValueError(f"Issue #{number} changed during source verification")
        verified += 1
        assignees = [a.get("login") for a in reread.get("assignees", [])
                     if isinstance(a, dict) and isinstance(a.get("login"), str)
                     and LOGIN.fullmatch(a["login"])]
        author = (reread.get("user") or {}).get("login")
        contacts = list(dict.fromkeys(assignees))
        basis = "github_assignee"
        if not contacts:
            contacts = [author] if isinstance(author, str) and LOGIN.fullmatch(author) else []
            basis = "issue_author_fallback" if contacts else "unavailable"
        for kind, proofs in sorted(signals.items()):
            for proof in proofs:
                verify_source(reread, proof, fetch)
            key = f"github:{REPO}#{number}:{kind}"
            cards.append({
                "id": key, "issue_number": number, "title": reread.get("title") or "",
                "issue_url": reread["html_url"], "issue_updated_at": reread.get("updated_at"),
                "issue_sha256": digest(reread.get("body") or ""), "kind": kind,
                "claim_scope": "literal source mention; claim not independently verified",
                "verification_needed": ("Check whether linked issue is an actual blocking prerequisite."
                                        if kind == "declared_dependency" else SIGNALS[kind][1]),
                "related_issue_number": proofs[0].get("target_issue"), "evidence": proofs,
                "contacts": contacts, "contact_basis": basis,
                "review_status": feedback.get(key, "new"),
                "communication_status": "human_approval_required", "sent": False,
            })
    cards.sort(key=lambda c: (c["issue_number"], c["kind"]))
    return {
        "schema": 1, "status": "review_only", "seed": seed, "repo": REPO,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "population_open": len(population), "excluded_preselected": sorted(excluded),
        "sampled": len(selected), "verified_issue_reads": verified,
        "selected_issue_numbers": selected, "candidates": cards,
        "signal_counts": dict(Counter(c["kind"] for c in cards)),
        "limitations": "Deterministic, weekly rotating 50-issue sample of currently open tasks; "
                       "heuristic text triage only, not verified impact or a project-wide ranking. "
                       "Human review required before communication; no posts sent.",
    }


def markdown(data):
    lines = [
        "# Research opportunity discovery — human review", "",
        "**Read-only experiment. No messages were sent.** Mentions are evidence for triage, "
        "not proof of a performance gain, confirmed blocker, or available contributor.", "",
        f"Sample: **{data['sampled']}** ID-selected open issues out of "
        f"**{data['population_open']}** open issues, excluding "
        f"**{len(data['excluded_preselected'])}** original cases. Seed: {data['seed']}. "
        f"Source re-reads: **{data['verified_issue_reads']}**.", "",
        f"Found **{len(data['candidates'])}** source-linked review cards across "
        f"**{len(set(c['issue_number'] for c in data['candidates']))}** issues. "
        "No automatic impact ranking.", "",
    ]
    for c in data["candidates"]:
        title = c["title"].replace("\n", " ")
        lines += [
            f"## [{c['issue_number']}: {title}]({c['issue_url']})", "",
            f"- Signal: {c['kind']} — {c['claim_scope']}",
            f"- Required verification: {c['verification_needed']}",
            f"- Manual feedback state: {c['review_status']}",
            f"- Suggested contact (not notified): {', '.join('@' + x for x in c['contacts']) or 'unknown'} "
            f"({c['contact_basis']})", f"- Stable ID: {c['id']}", "- Source excerpts:",
        ]
        for e in c["evidence"]:
            clean = " ".join(e["quote"].split()).replace(chr(96), "'")
            lines.append(f"  - [{e['origin']}]({e['source_url']}): {clean} "
                         f"(SHA256 {e['sha256']})")
        if c["related_issue_number"]:
            lines.append(f"- Explicit dependency mention: "
                         f"[#{c['related_issue_number']}](https://github.com/{REPO}/issues/{c['related_issue_number']}) "
                         "(target status not independently checked).")
        lines.append("")
    lines += ["## Limitations", "", data["limitations"], "",
              "Feedback is human-entered, not automatically verified against GitHub. "
              "Absence from a rotating sample does not indicate an issue is resolved."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--impact-cases", default="impact_cases.json")
    parser.add_argument("--feedback", default="results/opportunity_feedback.jsonl")
    parser.add_argument("--output", default="results")
    parser.add_argument("--seed", default=None)
    args = parser.parse_args(argv)
    try:
        case_data = json.loads(Path(args.impact_cases).read_text(encoding="utf-8"))
        excluded = {int(c["number"]) for c in case_data["cases"] if c["repo"] == REPO}
        if len(excluded) != 10:
            raise ValueError("Expected original ten-case exclusion list")
        result = build(excluded=excluded, seed=args.seed,
                       feedback=read_feedback(Path(args.feedback)))
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        (out / "discovery.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (out / "DISCOVERY.md").write_text(markdown(result), encoding="utf-8")
        print(f"Discovery: {len(result['candidates'])} review cards / {result['sampled']} issues")
        return 0
    except (OSError, ValueError, TypeError, KeyError, urllib.error.URLError) as exc:
        print(f"Discovery failed without publishing: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
