"""Compare a graph-assisted view with a source-only view on identical evidence.

This audits *information parity*, not human/LLM decision accuracy. The graph
arm may see explicit metadata edges; both arms must receive byte-identical
original issue and public-comment content. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def audit(frozen: dict) -> dict:
    if frozen.get("schema_version") != 1 or frozen.get("kind") != "frozen_identical_source_packet":
        raise ValueError("Expected frozen source packet v1")
    cases = frozen.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("No cases in frozen packet")

    seen = set()
    results = []
    for case in cases:
        anchor = case["anchor_id"]
        url = case["url"]
        if anchor in seen or not anchor.startswith("github:") or not url.startswith("https://github.com/"):
            raise ValueError("Duplicate or malformed source issue")
        seen.add(anchor)
        if not isinstance(case.get("body"), str):
            raise ValueError(f"Missing source issue body: {anchor}")
        comments = case.get("comments")
        if not isinstance(comments, list):
            raise ValueError(f"Missing comment coverage: {anchor}")

        by_url = set()
        sources = [{"url": url, "type": "issue", "body": case["body"],
                    "source_updated_at": case.get("updated_at")}]
        for item in comments:
            link = item.get("url")
            if not isinstance(link, str) or not link.startswith(url + "#issuecomment-"):
                raise ValueError(f"Unattributed comment for {anchor}")
            if link in by_url or not isinstance(item.get("body"), str):
                raise ValueError(f"Repeated or malformed public comment: {anchor}")
            by_url.add(link)
            sources.append({"url": link, "type": "comment", "body": item["body"],
                            "source_updated_at": item.get("updated_at")})
        sources[1:] = sorted(sources[1:], key=lambda x: x["url"])

        edges = case.get("graph_snapshot", {}).get("explicit_edges")
        if not isinstance(edges, list):
            raise ValueError(f"Missing explicit graph-edge coverage: {anchor}")
        for edge in edges:
            if not isinstance(edge, dict) or anchor not in (edge.get("source"), edge.get("target")):
                raise ValueError(f"Unsupported graph hint for {anchor}")

        # The arms deliberately share exactly the same original evidence.
        source_arm = sources
        graph_arm = list(sources)
        source_fingerprint = digest(source_arm)
        graph_fingerprint = digest(graph_arm)
        if source_fingerprint != graph_fingerprint:
            raise AssertionError("Unequal primary evidence invalidates comparison")

        results.append({
            "case_id": case["case_id"],
            "anchor_id": anchor,
            "primary_source_records_per_arm": len(sources),
            "public_comments_per_arm": len(comments),
            "source_sha256": source_fingerprint,
            "graph_primary_source_sha256": graph_fingerprint,
            "identical_original_evidence": True,
            "graph_structural_hints": len(edges),
            "extra_original_sources_from_graph": 0,
            "independent_decision_quality": None,
            "human_time_saved": None,
        })
    return {
        "schema_version": 1,
        "kind": "paired_evidence_parity_only",
        "frozen_input_sha256": digest(frozen),
        "cases": results,
        "summary": {
            "case_count": len(results),
            "identical_evidence_cases": sum(x["identical_original_evidence"] for x in results),
            "total_comment_records_per_arm": sum(x["public_comments_per_arm"] for x in results),
            "graph_structural_hints": sum(x["graph_structural_hints"] for x in results),
            "evidence_only_graph_advantage_demonstrated": False,
            "decision_accuracy_measured": False,
        },
        "limitations": [
            "A common source packet is not an independently blinded decision test",
            "Graph edge hints are metadata, not extra original-source documents",
            "Any benefit in reasoning with graph structure remains untested",
            "Three selected cases are not representative of a research corpus",
            "No research time, GPU budget, collaboration or scientific gain is measured",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frozen", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    frozen = json.loads(args.frozen.read_text(encoding="utf-8"))
    result = audit(frozen)
    if args.output.exists():
        raise ValueError("Refusing to overwrite a committed evidence checkpoint")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(f"{result['summary']['case_count']} identical source-packet pairs audited")


if __name__ == "__main__":
    main()
