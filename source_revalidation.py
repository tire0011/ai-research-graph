"""Recheck dated research claims against original public GitHub pull requests.

This small, read-only evidence gate identifies stale PR-status assumptions
before anyone recommends duplicate code, collaboration, or GPU evaluations.
No claims of saved time or graph superiority are inferred.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from opportunity_discovery import get_json


PR_URL = re.compile(
    r"https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/"
    r"(?P<repo>[A-Za-z0-9_.-]+)/pull/(?P<number>[1-9]\d*)\Z"
)
ALLOWED_STATES = {"open", "closed", "merged"}
MAX_CHECKS = 10


def sha256(data: object) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def pull_state(source: dict) -> str:
    """Closed and merged are different research milestones."""
    state = source.get("state")
    merged = source.get("merged_at")
    if state not in {"open", "closed"}:
        raise ValueError("Invalid GitHub PR state")
    if merged is not None:
        if state != "closed":
            raise ValueError("Inconsistent GitHub merged PR state")
        return "merged"
    return state


def date_of(value: str) -> dt.date:
    if not isinstance(value, str):
        raise ValueError("Missing evidence timestamp")
    return dt.date.fromisoformat(value[:10])


def audit(manifest: dict, fetch=get_json, *, checked_at: str | None = None) -> dict:
    if manifest.get("schema_version") != 1 or manifest.get("kind") != "public_pr_status_revalidation":
        raise ValueError("Unsupported manifest schema")
    records = manifest.get("records")
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_CHECKS:
        raise ValueError("Expected 1..10 review records")

    checked_at = checked_at or dt.datetime.now(dt.timezone.utc).isoformat()
    date_of(checked_at)
    seen_ids, seen_urls, cases = set(), set(), []
    for item in records:
        if not isinstance(item, dict):
            raise ValueError("Malformed manifest record")
        stable_id, url = item.get("id"), item.get("url")
        if not isinstance(stable_id, str) or not stable_id.strip() or stable_id in seen_ids:
            raise ValueError("Invalid or duplicate review ID")
        if not isinstance(url, str):
            raise ValueError("Missing PR URL")
        parsed = PR_URL.fullmatch(url)
        if not parsed or url.casefold() in seen_urls:
            raise ValueError("Invalid or duplicate PR URL")
        seen_ids.add(stable_id)
        seen_urls.add(url.casefold())

        old = item.get("prior_status")
        if old not in ALLOWED_STATES:
            raise ValueError("Unknown prior PR state")
        prior_date = date_of(item.get("prior_review_date"))
        if prior_date > date_of(checked_at):
            raise ValueError("Prior review cannot be in the future")
        origin = item.get("origin")
        if not isinstance(origin, str) or not origin or origin.startswith("/") or ".." in Path(origin).parts:
            raise ValueError("Missing or unsafe original research reference")

        owner, repo, number = parsed.group("owner", "repo", "number")
        api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
        response = fetch(api)
        if not isinstance(response, dict):
            raise ValueError(f"Invalid PR response for {url}")
        # A network failure or inaccessible source is never treated as "unchanged".
        if response.get("html_url", "").casefold() != url.casefold() or response.get("number") != int(number):
            raise ValueError(f"Unverifiable PR identity for {url}")
        current = pull_state(response)
        merged_at = response.get("merged_at")
        closed_at = response.get("closed_at")
        updated_at = response.get("updated_at")
        if not updated_at:
            raise ValueError(f"Missing PR update date for {url}")
        date_of(updated_at)

        if current == old:
            verdict = "unchanged"
        elif old == "open" and current in {"merged", "closed"}:
            transition_at = merged_at if current == "merged" else closed_at
            if not transition_at:
                raise ValueError(f"Missing closing transition for {url}")
            verdict = ("verified_status_change_after_prior_review"
                       if date_of(transition_at) > prior_date
                       else "source_claim_disagreement")
        else:
            verdict = "source_claim_disagreement"
        cases.append({
            "id": stable_id,
            "url": url,
            "api_url": api,
            "origin": origin,
            "prior_review_date": prior_date.isoformat(),
            "prior_status": old,
            "live_status": current,
            "live_updated_at": updated_at,
            "live_merged_at": merged_at,
            "status": verdict,
            "requires_human_review": verdict != "unchanged",
            "change_is_research_benefit": False,
            "automatic_outreach": False,
        })
    return {
        "schema_version": 1,
        "kind": "pr_source_freshness_audit",
        "checked_at_utc": checked_at,
        "manifest_sha256": sha256(manifest),
        "status": "complete",
        "cases": cases,
        "summary": {
            "selected": len(cases),
            "source_verified": len(cases),
            "unchanged": sum(c["status"] == "unchanged" for c in cases),
            "changed_since_prior_review": sum(
                c["status"] == "verified_status_change_after_prior_review" for c in cases),
            "claim_disagreements": sum(c["status"] == "source_claim_disagreement" for c in cases),
            "confirmed_graph_advantage": False,
            "measured_time_saved": None,
        },
        "limitations": [
            "Purposefully chosen review claims, not a representative population",
            "Only public GitHub PR status; issue comments, code and scientific claims not revalidated",
            "Correct source status can also be recovered by ordinary direct GitHub lookup",
            "No automatic outreach, PR changes, metric improvements or verified cost savings",
        ],
    }


def render_markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Dated PR-status source revalidation",
        "",
        f"Source check: {report['checked_at_utc']}. Original research notes are preserved.",
        "",
        f"Verified **{summary['source_verified']}/{summary['selected']}** PR identities; "
        f"**{summary['changed_since_prior_review']}** status change(s) since the "
        "corresponding old review. This is not evidence of a graph speedup.",
        "",
        "| Primary PR | Prior observation | Current source status | Decision |",
        "| --- | --- | --- | --- |",
    ]
    for c in report["cases"]:
        lines.append(
            f"| [#{c['url'].rsplit('/', 1)[-1]}]({c['url']}) | "
            f"{c['prior_status']} ({c['prior_review_date']}) | {c['live_status']} | "
            f"{c['status']} |")
    lines.extend([
        "",
        "A change means **review the existing recommendation**, not automatically",
        "contact anyone or implement a new feature. Direct source lookup remains",
        "a valid baseline. No realized research benefit has been measured.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--markdown", type=Path)
    args = ap.parse_args()

    # Never clobber a previous scientific checkpoint.
    for path in (args.output, args.markdown):
        if path is not None and path.exists():
            ap.error(f"Output already exists: {path}")

    result = audit(json.loads(args.manifest.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    if args.markdown is not None:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(result), encoding="utf-8")
    print(f"Checked {result['summary']['source_verified']} PRs; "
          f"{result['summary']['changed_since_prior_review']} changed")


if __name__ == "__main__":
    main()
