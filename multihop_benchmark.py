"""Audited two-hop GitHub-task -> GitHub-task -> Hugging Face references.

All claims are about literal source links. Neither path existence nor a common
publication establishes training, implementation or experimental correctness.
"""

import argparse
import datetime as dt
import hashlib
import json
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

from holdout_study import read_issue
from research_questions_benchmark import source_references


def explicit_hf_targets(text, hf_nodes):
    """Find complete published Hub URLs/IDs in raw task text, without edges."""
    found = set()
    for asset in hf_nodes:
        title = asset["title"]
        url = asset["url"].rstrip("/")
        for needle in (url, title):
            if re.search(r"(?<![a-z0-9_-])" + re.escape(needle) + r"(?![a-z0-9_-])",
                         text, flags=re.IGNORECASE):
                found.add(asset["id"])
                break
    return found


def graph_paths(edges, anchor):
    """Only two explicit links, with the intermediate node represented by an ID."""
    next_tasks = {e["target"] for e in edges if e["source"] == anchor
                  and e["status"] == "explicit_task_reference"}
    return sorted({(task, e["target"]) for task in next_tasks for e in edges
                   if e["source"] == task and e["status"] == "explicit_reference"
                   and e["target"].startswith("hf:")})


def follow_source_paths(nodes, anchor):
    """Text-source alternative: inspect the source then open every linked task.

    Does not read graph edges or precomputed link inventories.
    """
    lookup = {node["id"].casefold(): node for node in nodes}
    source = lookup[anchor.casefold()]
    known_tasks = {id_ for id_, node in lookup.items()
                   if node["type"] in ("issue", "pull_request") and id_.startswith("github:")}
    hf_nodes = [node for node in nodes if node["id"].startswith("hf:")]
    refs = source_references(source.get("title", "") + "\n" + (source.get("description") or ""),
                             source["repository"], known_tasks)
    paths = set()
    for target_id in refs:
        task = lookup[target_id]
        for hf_id in explicit_hf_targets(task.get("title", "") + "\n" + (task.get("description") or ""), hf_nodes):
            paths.add((task["id"], hf_id))
    return sorted(paths), refs


def timed_ms(fn, repeats):
    values = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        values.append((time.perf_counter() - start) * 1000)
    return round(statistics.median(values), 4)


def audit_source(node, fetch, cache):
    if node["id"] in cache:
        return cache[node["id"]]
    repo, number = node["id"][len("github:"):].rsplit("#", 1)
    original = fetch(repo, int(number))
    if (original.get("updated_at") != node.get("updated_at") or
            original["body"] != (node.get("description") or "")):
        raise ValueError(f"Original GitHub body changed since graph snapshot: {node['id']}")
    cache[node["id"]] = hashlib.sha256(original["body"].encode("utf-8")).hexdigest()
    return cache[node["id"]]


def evaluate(graph, study, *, fetch=read_issue, repeats=11):
    if repeats < 1:
        raise ValueError("repeats must be positive")
    nodes, edges = graph["nodes"], graph["edges"]
    by_id = {n["id"]: n for n in nodes}
    digest_cache = {}
    rows = []
    cases = study["cases"]
    if len({c["anchor_id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate case source anchor")
    for case in cases:
        anchor = case["anchor_id"]
        row = {"id": case["id"], "cohort": case["cohort"], "anchor_id": anchor,
               "expected_paths": case["expected_paths"]}
        try:
            if anchor not in by_id:
                raise ValueError(f"Missing source task: {anchor}")
            source = by_id[anchor]
            row["source_url"] = source["url"]
            row["question"] = ("Which indexed HF artifacts are explicitly mentioned by GitHub tasks "
                               f"cited in '{source['title']}'?")
            row["source_sha256"] = audit_source(source, fetch, digest_cache)
            text_paths, first_hop_refs = follow_source_paths(nodes, anchor)
            row["first_hop_tasks"] = first_hop_refs
            for task_id in first_hop_refs:
                task = by_id[task_id] if task_id in by_id else next(
                    (n for n in nodes if n["id"].casefold() == task_id), None)
                if task is None:
                    raise ValueError(f"Task disappeared from indexed snapshot: {task_id}")
                audit_source(task, fetch, digest_cache)
            expected = sorted(tuple(path) for path in case["expected_paths"])
            if text_paths != expected:
                raise ValueError(f"Frozen source-text annotation differs: expected={expected}, found={text_paths}")
            actual = graph_paths(edges, anchor)
            row["graph_paths"] = [list(p) for p in actual]
            row["source_follow_paths"] = [list(p) for p in text_paths]
            row["graph_exact"] = actual == expected
            row["source_follow_exact"] = text_paths == expected
            row["graph_lookup_ms"] = timed_ms(lambda: graph_paths(edges, anchor), repeats)
            row["source_follow_lookup_ms"] = timed_ms(lambda: follow_source_paths(nodes, anchor), repeats)
            row["status"] = "evaluated"
        except (KeyError, ValueError, TimeoutError, OSError) as exc:
            row.update({"status": "source_error", "error": f"{type(exc).__name__}: {exc}"})
        rows.append(row)

    summary = {}
    for cohort in ("all", "positive", "negative"):
        group = [r for r in rows if r["status"] == "evaluated" and
                 (cohort == "all" or r["cohort"] == cohort)]
        summary[cohort] = {
            "cases": len(group), "graph_exact": sum(r["graph_exact"] for r in group),
            "source_follow_exact": sum(r["source_follow_exact"] for r in group),
            "correct_graph_abstentions": sum(not r["expected_paths"] and not r["graph_paths"] for r in group),
            "reference_paths": sum(len(r["expected_paths"]) for r in group),
            "graph_median_ms": round(statistics.median(r["graph_lookup_ms"] for r in group), 4) if group else None,
            "source_follow_median_ms": round(statistics.median(
                r["source_follow_lookup_ms"] for r in group), 4) if group else None,
        }
    return {"status": "completed" if len(rows) == sum(r["status"] == "evaluated" for r in rows) else "source_error",
            "snapshot_utc": graph.get("timestamp_utc"),
            "evaluated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source_bodies_verified": len(digest_cache), "source_sha256": digest_cache,
            "selection": study["selection"], "selected": len(cases),
            "evaluated": sum(r["status"] == "evaluated" for r in rows),
            "repetitions": repeats, "summary": summary, "cases": rows}


def markdown(result):
    lines = ["# Two-hop research evidence: graph versus source-following", "",
             f"Snapshot: `{result['snapshot_utc']}`. Checked: **{result['evaluated']}/{result['selected']}** "
             f"case sources; original GitHub task bodies verified: **{result['source_bodies_verified']}**. "
             f"Status: `{result['status']}`.", "",
             "## Exact evidence paths", "",
             "| Cohort | Cases | Explicit 2-hop paths | Graph correct | Follow-source correct | Graph ms | Follow-source ms |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for cohort, d in result["summary"].items():
        lines.append(f"| {cohort} | {d['cases']} | {d['reference_paths']} | "
                     f"{d['graph_exact']}/{d['cases']} | {d['source_follow_exact']}/{d['cases']} | "
                     f"{d['graph_median_ms']} | {d['source_follow_median_ms']} |")
    lines.extend(["", "Lookup times are in-memory medians after snapshot collection and graph construction. "
                  "They exclude original source fetches, index construction, parsing at ingestion, "
                  "human research and review time; do **not** treat them as an end-to-end speedup.", "",
                  "The source-following baseline navigates the same two hops from raw snapshot text, "
                  "without reading graph edges. It is deliberately allowed to follow links, so a graph advantage "
                  "cannot be manufactured by denying the baseline the second hop.", "",
                  "## Per-question original-source evidence", "",
                  "| Anchor task | Gold paths | Graph matches | Text-follow matches | Explicit first-hop task IDs |",
                  "| --- | ---: | --- | --- | --- |"])
    for r in result["cases"]:
        if r["status"] != "evaluated":
            lines.append(f"| `{r['anchor_id']}` | error | – | – | {r['error'].replace('|', '\\|')} |")
        else:
            refs = ", ".join(f"`{item}`" for item in r["first_hop_tasks"]) or "none"
            lines.append(f"| [{r['anchor_id']}]({r['source_url']}) | {len(r['expected_paths'])} | "
                         f"{r['graph_exact']} | {r['source_follow_exact']} | {refs} |")
    lines.extend(["", "## Scientific limits", "",
                  "This small, deliberately selected sample is **not blind** and overrepresents known link paths. "
                  "Gold paths were frozen after inspecting explicit source metadata and are checked again "
                  "against the current original GitHub bodies. A link between tasks means only a textual mention; "
                  "a second link to Hugging Face means the intermediate task explicitly mentions a model/dataset. "
                  "Neither proves usage, model training, experimental success or causality. "
                  "Negative cases are absence of this exact path pattern in the bounded snapshot, "
                  "not proof of absence of real-world relationships.", "",
                  "This benchmark isolates **cross-source link traversal**; the preceding twenty-question "
                  "experiment measured **finding the source task**. An actual researcher workflow would need "
                  "both, plus independently evaluated AI answer quality and provenance completeness.", ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default="results/snapshot.json")
    parser.add_argument("--cases", default="multihop_cases.json")
    parser.add_argument("--output", default="results")
    args = parser.parse_args(argv)
    graph = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    result = evaluate(graph, cases)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    failed = result["status"] != "completed"
    stem = "multihop_error" if failed else "multihop_evidence"
    title = "MULTIHOP_ERROR" if failed else "MULTIHOP_EVIDENCE"
    (out / f"{stem}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / f"{title}.md").write_text(markdown(result), encoding="utf-8")
    print(f"Two-hop source audit: {result['evaluated']}/{result['selected']}, "
          f"status={result['status']}, verified original bodies={result['source_bodies_verified']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
