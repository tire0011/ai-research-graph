"""Optional AIoD catalogue ↔ GitHub snapshot lexical comparison (review only).

Uses the same simple technical-token baseline as the GitHub matcher. This
cannot infer duplicate work, verified reuse or missing collaboration.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

from collaboration_matcher import tokens


def compare(aiod: dict, snapshot: dict, *, limit: int = 15) -> dict:
    if aiod.get("status") != "sampled_read_only" or aiod.get("schema") != 1:
        raise ValueError("Expected a successful AIoD catalogue probe, not a fixture/error")
    nodes = aiod.get("nodes")
    others = snapshot.get("nodes")
    if (not isinstance(nodes, list) or not isinstance(others, list)
            or type(limit) is not int or not 1 <= limit <= 30):
        raise ValueError("Missing bounded AIoD or snapshot nodes")
    if len(nodes) > 100 or len(others) > 10000:
        raise ValueError("Cross-comparison source exceeds explicit size limits")
    if any(n.get("type") != "catalogue_asset" or not n.get("id", "").startswith("aiod:v2:")
           for n in nodes):
        raise ValueError("Unverified AIoD node in source")
    # Multiple AIoD IDs in one page can claim the same original project URL.
    # Avoid counting those aliases as independent collaboration opportunities.
    unique_nodes, seen_claimed_urls = [], set()
    for node in nodes:
        claimed_url = node.get("original_url_claim")
        if claimed_url and claimed_url in seen_claimed_urls:
            continue
        if claimed_url:
            seen_claimed_urls.add(claimed_url)
        unique_nodes.append(node)
    github = [n for n in others if n.get("type") in ("issue", "pull_request")
              and n.get("id", "").startswith("github:") and n.get("state") == "open"]
    prepared = [(n, tokens(n.get("title", "") + " " + (n.get("description") or "")))
                for n in unique_nodes + github]
    weights = Counter(t for _, ts in prepared for t in ts)
    total = len(prepared)
    idf = {t: 1 + math.log((total + 1) / (freq + 1)) for t, freq in weights.items()}
    candidates = []
    for a in unique_nodes:
        a_title = tokens(a["title"])
        a_all = tokens(a["title"] + " " + a.get("description", ""))
        for b in github:
            b_title = tokens(b.get("title", ""))
            b_all = tokens(b.get("title", "") + " " + (b.get("description") or ""))
            common = a_all & b_all
            anchors = common & (a_title | b_title)
            # Stronger than matching two generic body words, but still only
            # a lexical hypothesis. No training or coordination claim.
            if len(common) < 2 or len(anchors) < 1:
                continue
            score = sum(idf[t] for t in common)
            candidates.append({
                "id": f"aiod_cross:{a['id']}->{b['id']}",
                "aiod_id": a["id"], "aiod_url": a["url"], "aiod_title": a["title"],
                "aiod_metadata_sha256": a["metadata_sha256"],
                "github_id": b["id"], "github_url": b["url"],
                "github_title": b["title"],
                "shared_terms": sorted(common), "score": round(score, 3),
                "classification": "unreviewed_lexical_overlap",
                "existing_coordination": "unknown", "outreach": "none",
            })
    candidates.sort(key=lambda c: (-c["score"], c["id"]))
    return {
        "schema": 1, "status": "exploratory_lexical_baseline_only",
        "aiod_source_generated_at_utc": aiod.get("generated_at_utc"),
        "github_snapshot_generated_at_utc": snapshot.get("timestamp_utc"),
        "aiod_sample_limited": aiod.get("sample_limited"),
        "aiod_nodes": len(nodes), "unique_aiod_claimed_sources": len(unique_nodes),
        "aiod_possible_aliases_skipped": len(nodes) - len(unique_nodes),
        "open_github_tasks": len(github),
        "candidates": candidates[:limit], "total_lexical_candidates": len(candidates),
        "novel_collaboration_confirmed": False, "outreach": "none",
        "limitations": "Not a semantic match and not an independent holdout. Both inputs are "
                       "bounded snapshots. Shared tokens do not establish a useful handoff, "
                       "duplicate code or a new human relationship. Repeated claimed external "
                       "URLs were collapsed within this sample, not resolved as identities. "
                       "Inspect originals and "
                       "the AIoD external-platform identity before any action.",
    }


def markdown(result: dict) -> str:
    lines = ["# AIoD ↔ GitHub cross-source candidates", "",
             f"{len(result['candidates'])} shown / {result['total_lexical_candidates']} "
             f"lexical overlaps from {result['aiod_nodes']} AIoD records "
             f"({result['unique_aiod_claimed_sources']} unique claimed URLs/records) and "
             f"{result['open_github_tasks']} open GitHub tasks.", "",
             "**Review-only lexical comparator, not a detected new collaboration.**", ""]
    for c in result["candidates"]:
        lines += [f"- [{c['aiod_title']}]({c['aiod_url']}) ↔ "
                  f"[{c['github_title']}]({c['github_url']})",
                  f"  - Terms: {', '.join(c['shared_terms'])}; score: {c['score']}; "
                  f"AIoD raw metadata SHA256: `{c['aiod_metadata_sha256']}`"]
    lines += ["", "## Caveats", "", result["limitations"], ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aiod", default="results/aiod/projects.json")
    parser.add_argument("--snapshot", default="results/snapshot.json")
    parser.add_argument("--output", default="results/aiod")
    args = parser.parse_args(argv)
    try:
        source = json.loads(Path(args.aiod).read_text(encoding="utf-8"))
        snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        result = compare(source, snapshot)
        dest = Path(args.output)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "CROSS_SOURCE_CANDIDATES.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (dest / "CROSS_SOURCE_CANDIDATES.md").write_text(markdown(result), encoding="utf-8")
        print(f"AIoD cross-source lexical candidates: {len(result['candidates'])}")
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"AIoD cross-comparison rejected: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
