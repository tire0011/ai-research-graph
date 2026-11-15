"""On-demand, read-only comment evidence for a small list of graph issues.

Reuses impact_enrichment's already-tested comment collector. This gathers
evidence for human review; it never classifies research as duplicate or useful.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

from impact_enrichment import github_comments_for_selected
from research_graph import fetch_json


MAX_ISSUES = 5


def build_packet(snapshot: dict, issue_ids: list[str], *, fetch=fetch_json, token=None) -> dict:
    """Enrich selected indexed issues without modifying the main graph."""
    if not (1 <= len(issue_ids) <= MAX_ISSUES):
        raise ValueError(f"Select between 1 and {MAX_ISSUES} issues")
    if len({value.casefold() for value in issue_ids}) != len(issue_ids):
        raise ValueError("Duplicate issue selection")

    by_id = {n["id"].casefold(): n for n in snapshot["nodes"] if n.get("type") == "issue"}
    selections = []
    for item in issue_ids:
        node = by_id.get(item.casefold())
        if not node:
            raise ValueError(f"Not an indexed issue: {item}")
        selections.append(node)

    comments, edges = github_comments_for_selected(
        snapshot["nodes"], [n["id"] for n in selections], fetch, token=token
    )
    comment_by_issue = defaultdict(list)
    for item in comments:
        comment_by_issue[item["issue_id"].casefold()].append(item)

    old_comment_edges = [
        e for e in snapshot["edges"] if e.get("status") == "source_comment"
    ]
    evidence = []
    for issue in selections:
        cached = [e for e in old_comment_edges
                  if e["source"].casefold() == issue["id"].casefold()]
        retrieved = sorted(comment_by_issue[issue["id"].casefold()],
                           key=lambda c: c["comment_id"])
        evidence.append({
            "issue_id": issue["id"],
            "issue_url": issue["url"],
            "issue_title": issue["title"],
            "snapshot_updated_at": issue.get("updated_at"),
            "snapshot_comment_edges": len(cached),
            "fetched_public_comments": len(retrieved),
            "comments": [
                {"url": c["url"], "id": c["comment_id"], "updated_at": c["updated_at"],
                 "sha256": c["body_sha256"], "body": c["description"]}
                for c in retrieved
            ],
        })

    return {
        "status": "complete",
        "kind": "on_demand_public_comment_evidence",
        "snapshot_timestamp_utc": snapshot.get("timestamp_utc"),
        "issues": evidence,
        "comments_retrieved": len(comments),
        "comment_source_edges_available": len(edges),
        "limitations": [
            "GitHub public comments are attributable claims, not independently verified outcomes",
            "Only selected issues were fetched; missing comments elsewhere are unknown",
            "Issue bodies are from the specified snapshot; live bodies may have changed",
            "No duplicate-work, causality, benefit or cost claims are inferred",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=Path("results/snapshot.json"))
    parser.add_argument("--issue", action="append", required=True,
                        help="Full indexed ID, e.g. github:OpenEuroLLM/Taskboard#346 (repeat)")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))

    if args.output.exists():
        parser.error("Output exists; use a new checkpoint file instead of overwriting evidence")
    # Fail closed: every source must complete before any result is written.
    packet = build_packet(snapshot, args.issue, token=os.environ.get("GITHUB_TOKEN"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".partial")
    if temporary.exists():
        parser.error("Temporary output exists; inspect it before retrying")
    try:
        temporary.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
        temporary.replace(args.output)
    finally:
        if temporary.exists():
            temporary.unlink()
    print(f"Collected {packet['comments_retrieved']} comments for "
          f"{len(packet['issues'])} issues: {args.output}")


if __name__ == "__main__":
    main()
