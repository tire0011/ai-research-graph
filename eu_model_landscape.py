"""Bounded, offline European AI ecosystem overlay for the existing research graph.

Publisher reports, catalogue entries, and unreviewed hypotheses are NEVER
treated as proof of implementation reuse or new cross-team collaboration.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

SCHEMA = 1
LEVELS = {"publisher_report", "documented_collaboration"}
ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def validate(data: dict) -> None:
    if data.get("schema") != SCHEMA:
        raise ValueError("Unsupported schema")
    projects, infrastructure = data.get("projects"), data.get("infrastructure")
    if not isinstance(projects, list) or not 20 <= len(projects) <= 30:
        raise ValueError("Pilot requires 20-30 projects")
    if not isinstance(infrastructure, list):
        raise ValueError("Infrastructure must be a list")
    ids = []
    for item in projects + infrastructure:
        item_id = item.get("id", "")
        if not isinstance(item_id, str) or not ID_RE.fullmatch(item_id):
            raise ValueError(f"Invalid node id: {item_id}")
        if not item.get("name") or not item.get("url", "").startswith("https://"):
            raise ValueError(f"Missing source-bearing node: {item_id}")
        ids.append(item_id)
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate node id")
    project_ids = {p["id"] for p in projects}
    infra_ids = {p["id"] for p in infrastructure}
    for p in projects:
        if p.get("evidence") not in {"primary_checked", "catalogue_lead"} or not p.get("focus"):
            raise ValueError("Invalid catalogue provenance")
    for fact in data.get("facts", []):
        if (fact.get("from") not in project_ids
                or fact.get("to") not in project_ids | infra_ids
                or fact["from"] == fact["to"]
                or fact.get("level") not in LEVELS
                or not fact.get("source_url", "").startswith("https://")
                or not fact.get("assertion") or not fact.get("relation")):
            raise ValueError(f"Invalid source claim: {fact}")
    seen = set()
    for c in data.get("hypotheses", []):
        if (not c.get("id") or c["id"] in seen
                or c.get("from") not in project_ids
                or c.get("to") not in project_ids
                or c["from"] == c["to"]
                or c.get("status") != "unreviewed_hypothesis"
                or not all(c.get(k) for k in ("question", "smallest_action", "falsifier"))
                or len(c.get("sources", [])) < 2
                or any(not u.startswith("https://") for u in c["sources"])):
            raise ValueError(f"Invalid hypothesis: {c}")
        seen.add(c["id"])


def build(data: dict, snapshot: dict | None = None) -> dict:
    validate(data)
    projects = data["projects"]
    infra = data["infrastructure"]
    node_ids = {x["id"]: f"eu_project:{x['id']}" for x in projects}
    node_ids.update({x["id"]: f"eu_infrastructure:{x['id']}" for x in infra})
    new_nodes = [
        {"id": node_ids[p["id"]], "type": "model_project", "title": p["name"],
         "description": p["focus"], "url": p["url"], "catalogue_evidence": p["evidence"],
         "catalogue_url": data["catalogue_url"]}
        for p in projects
    ] + [
        {"id": node_ids[p["id"]], "type": "research_infrastructure",
         "title": p["name"], "url": p["url"], "description": "Infrastructure named by source reports"}
        for p in infra
    ]
    new_edges = [
        {"source": node_ids[f["from"]], "target": node_ids[f["to"]],
         "relationship": f["relation"], "status": f["level"],
         "evidence_type": "source_report", "evidence": f["assertion"],
         "context": f["source_url"],
         "reason": "Source statement; not independent replication or proof of unlisted collaboration",
         "source_url": f["source_url"]}
        for f in data["facts"]
    ]
    old_nodes = [] if snapshot is None else snapshot["nodes"]
    old_edges = [] if snapshot is None else snapshot["edges"]
    if not isinstance(old_nodes, list) or not isinstance(old_edges, list):
        raise ValueError("Invalid existing snapshot")
    existing_ids = {n["id"] for n in old_nodes}
    if existing_ids.intersection(node_ids.values()):
        raise ValueError("EU overlay node IDs collide with existing graph")
    by_infra = defaultdict(set)
    for f in data["facts"]:
        if f["to"] in {item["id"] for item in infra} and f["relation"] == "reports_training_on":
            by_infra[f["to"]].add(f["from"])
    shared = []
    for infra_id, users in sorted(by_infra.items()):
        ordered = sorted(users)
        for i, left in enumerate(ordered):
            for right in ordered[i + 1:]:
                shared.append({
                    "left": node_ids[left], "right": node_ids[right],
                    "via": node_ids[infra_id],
                    "classification": "common_reported_infrastructure",
                    "interpretation": "Shared resource in public reports, NOT confirmed collaboration"
                })
    hypotheses = [{
        "id": h["id"], "source": node_ids[h["from"]], "target": node_ids[h["to"]],
        "title": h["title"], "question": h["question"],
        "smallest_action": h["smallest_action"], "falsifier": h["falsifier"],
        "source_urls": h["sources"], "status": h["status"],
        "evidence_type": "hypothesis_not_fact"
    } for h in data["hypotheses"]]
    return {
        "schema": 1, "as_of": data["as_of"],
        "source_snapshot_timestamp": None if snapshot is None else snapshot.get("timestamp_utc"),
        "nodes": old_nodes + new_nodes, "edges": old_edges + new_edges,
        "added_counts": {"projects": len(projects), "infrastructure": len(infra),
                         "source_relations": len(new_edges), "hypotheses": len(hypotheses)},
        "inferred_shared_infrastructure": shared,
        "unreviewed_hypotheses": hypotheses,
        "limits": "Catalogue entries are discovery leads; sourced publisher reports do not verify "
                  "execution or novel collaboration. Hypotheses are excluded from factual edges. "
                  "No outbound contact, ranking, saved GPU time, or graph advantage demonstrated."
    }


def report(data: dict, result: dict) -> str:
    project_names = {p["id"]: p["name"] for p in data["projects"]}
    names = {**project_names, **{p["id"]: p["name"] for p in data["infrastructure"]}}
    out = ["# European AI landscape: bounded graph pilot", "",
           f"**Snapshot:** {data['as_of']}; {len(data['projects'])} curated leads, "
           f"{len(data['facts'])} sourced statements, {len(data['hypotheses'])} hypotheses.",
           "", "All catalogue-only entries need independent source revalidation before decisions.",
           "This is a read-only *overlay* and does not change the scheduled graph snapshot.",
           "", "## Source-backed edges", ""]
    for f in data["facts"]:
        out.append(f"- **{names[f['from']]} → {names[f['to']]}** "
                   f"(`{f['level']}`, `{f['relation']}`): {f['assertion']} "
                   f"[source]({f['source_url']})")
    out.extend(["", "## Two-hop shared infrastructure (not collaboration)", ""])
    if result["inferred_shared_infrastructure"]:
        for h in result["inferred_shared_infrastructure"]:
            out.append(f"- {h['left']} ↔ {h['right']} via {h['via']}: {h['interpretation']}")
    else:
        out.append("No shared infrastructure evidenced in the bounded facts.")
    out.extend(["", "## Opportunities needing human review", ""])
    for h in data["hypotheses"]:
        urls = ", ".join(f"[source {i}]({u})" for i, u in enumerate(h["sources"], 1))
        out.extend([f"### {h['title']}", "",
                    f"**Question:** {h['question']}", "",
                    f"**Smallest action:** {h['smallest_action']}", "",
                    f"**Stop condition:** {h['falsifier']}", "", urls, ""])
    out.extend(["## Fair next gate", "",
                "Provide the same frozen primary-source packet to a graph-assisted reviewer "
                "and a plain source/keyword-search reviewer. Compare actionable, correctly "
                "supported decisions (including abstentions), verification effort and misses.",
                "Do not automate outreach or broad crawling before a clear decision benefit is measured.",
                "", "## Discovery catalogue", "",
                f"Initial leads: [{data['catalogue_url']}]({data['catalogue_url']}). "
                "Presence in this catalogue does not imply an official endorsement.", ""])
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default="studies/eu_model_landscape_20261119/sources.json")
    parser.add_argument("--snapshot", help="Optional existing graph snapshot, read only")
    parser.add_argument("--output", default="results/eu_model_landscape_pilot.json")
    parser.add_argument("--report", default="results/EU_MODEL_LANDSCAPE_PILOT.md")
    args = parser.parse_args(argv)
    data = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8")) if args.snapshot else None
    result = build(data, snapshot)
    for destination, value in [
        (Path(args.output), json.dumps(result, indent=2, ensure_ascii=False) + "\n"),
        (Path(args.report), report(data, result))
    ]:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(value, encoding="utf-8")
    print(f"Added {result['added_counts']}; shared infrastructure pairs: "
          f"{len(result['inferred_shared_infrastructure'])}; hypotheses are not facts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
