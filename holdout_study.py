"""Audited issue-based holdout: compare GitHub issue bodies with graph records.

No LLM is asked to answer. A curated claim is tested only for *source support*;
the existence of an issue, citation or reported result does not verify science.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def read_issue(repo, number, *, timeout=20):
    url = f"https://api.github.com/repos/{repo}/issues/{number}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ai-research-graph-holdout"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    for attempt in range(3):
        try:
            begin = time.perf_counter()
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as response:
                data = json.load(response)
            if (data.get("number") != number or "body" not in data or
                    (data["body"] is not None and not isinstance(data["body"], str))):
                raise ValueError("GitHub issue response has missing/mismatched body or number")
            # GitHub uses JSON null for an issue with no description. The graph
            # inventory already normalizes that exact value to an empty string.
            return {"body": data["body"] or "", "updated_at": data.get("updated_at"),
                    "url": data.get("html_url", url),
                    "latency_ms": round(1000 * (time.perf_counter() - begin), 1)}
        except (urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code < 500 and exc.code not in (408, 429):
                raise
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def digest(body):
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def evidence_summary(edges, anchor):
    links = [edge for edge in edges if edge.get("source") == anchor]
    proven_mentions = [edge for edge in links if edge.get("status") in {
        "explicit_reference", "identifier_match", "declared_source_file", "explicit_run_reference"}]
    candidates = [edge for edge in links if edge.get("status") == "candidate"]
    task_refs = [edge for edge in links if edge.get("status") == "explicit_task_reference"]
    return {"sourced_link_count": len(proven_mentions), "candidate_count": len(candidates),
            "sourced_targets": [edge["target"] for edge in proven_mentions],
            "task_reference_count": len(task_refs),
            "task_reference_targets": [edge["target"] for edge in task_refs]}


def evaluate(graph, study, *, fetch=read_issue):
    cases = study["cases"]
    by_id = {node["id"]: node for node in graph["nodes"]}

    def one(case):
        anchor = f"github:{case['repo']}#{case['number']}"
        try:
            source = fetch(case["repo"], case["number"])
        except (ValueError, KeyError, urllib.error.URLError, TimeoutError) as exc:
            return {"id": case["id"], "anchor": anchor, "question": case["question"],
                    "status": "source_error", "error": f"{type(exc).__name__}: {exc}"}
        body = source["body"]
        missing_phrases = [phrase for phrase in case["phrases"] if phrase.casefold() not in body.casefold()]
        node = by_id.get(anchor)
        result = {
            "id": case["id"], "anchor": anchor, "question": case["question"],
            "answer": case["answer"], "evidence_level": case["evidence_level"],
            "source_url": source["url"], "source_updated_at": source["updated_at"],
            "source_sha256": digest(body), "source_latency_ms": source.get("latency_ms"),
            "gold_phrases": case["phrases"], "missing_source_phrases": missing_phrases,
            "issue_crossrefs": sorted(set(re.findall(r"(?<![\w])#([1-9][0-9]+)\b", body))),
        }
        if missing_phrases:
            result["status"] = "annotation_error"
        elif node is None:
            result["status"] = "missing_graph_node"
        elif node.get("updated_at") != source["updated_at"]:
            result["status"] = "stale_graph_node"
        else:
            graph_body = node.get("description") or ""
            result["graph_sha256"] = digest(graph_body)
            result["graph_fact_support"] = all(
                phrase.casefold() in graph_body.casefold() for phrase in case["phrases"])
            result["status"] = "exact_source_parity" if graph_body == body else "body_mismatch"
        result.update(evidence_summary(graph["edges"], anchor))
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(one, cases))
    failures = [row for row in rows if row["status"] in {"source_error", "annotation_error"}]
    return {
        "status": "source_error" if failures else "completed",
        "evaluated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "snapshot_utc": graph.get("timestamp_utc"), "selection": study["selection"],
        "selected": len(rows), "sources_available": sum("source_sha256" in row for row in rows),
        "exact_source_parity": sum(row["status"] == "exact_source_parity" for row in rows),
        "graph_fact_support": sum(row.get("graph_fact_support", False) for row in rows),
        "missing_graph_node": sum(row["status"] == "missing_graph_node" for row in rows),
        "stale_graph_node": sum(row["status"] == "stale_graph_node" for row in rows),
        "linked_issues": sum(row.get("sourced_link_count", 0) > 0 for row in rows),
        "task_linked_issues": sum(row.get("task_reference_count", 0) > 0 for row in rows),
        "task_reference_edges": sum(row.get("task_reference_count", 0) for row in rows),
        "issue_crossrefs": sum(bool(row.get("issue_crossrefs")) for row in rows),
        "latency_median_ms": round(statistics.median(
            [row["source_latency_ms"] for row in rows if row.get("source_latency_ms") is not None]), 1)
            if any(row.get("source_latency_ms") is not None for row in rows) else None,
        "cases": rows,
    }


def markdown(result):
    lines = [
        "# Ten new OpenEuroLLM research questions: source-grounded holdout", "",
        f"Snapshot: `{result['snapshot_utc']}` UTC. Live original issues fetched: "
        f"**{result['sources_available']}/{result['selected']}**.",
        f"Issue bodies identical to the snapshot, at the **same update timestamp**: "
        f"**{result['exact_source_parity']}/{result['selected']}**.",
        f"Questions supported by the graph's retained source phrases: "
        f"**{result['graph_fact_support']}/{result['selected']}**.",
        f"Issues with any cross-platform evidence edge: **{result['linked_issues']}/{result['selected']}**; "
        f"issues with internal `#issue` references in text: **{result['issue_crossrefs']}/{result['selected']}**.",
        f"Issues with resolved, in-snapshot GitHub task-reference edges: "
        f"**{result['task_linked_issues']}/{result['selected']}** "
        f"({result['task_reference_edges']} distinct edges).", "",
        "| Original issue and question | Source body vs graph | Sourced external links | Internal task links |",
        "| --- | --- | ---: | ---: |",
    ]
    for case in result["cases"]:
        label = f"[{case['anchor'].split(':', 1)[1]}]({case.get('source_url', '')})" if case.get("source_url") else case["anchor"]
        lines.append(f"| {label}: {case['question']} | `{case['status']}` | {case.get('sourced_link_count', 'n/a')} | {case.get('task_reference_count', 'n/a')} |")
    lines.extend(["", "## Short, original-source-grounded answers", ""])
    for case in result["cases"]:
        if "answer" not in case:
            lines.extend([f"- **{case['id']}**: source unavailable ({case.get('error', 'unknown')}).", ""])
            continue
        links = ", ".join(case.get("issue_crossrefs", [])) or "none"
        targets = ", ".join(case.get("task_reference_targets", [])) or "none"
        lines.extend([f"- **{case['id']}** (`{case['evidence_level']}`): {case['answer']} "
                      f"[Original issue]({case['source_url']}). Internal issue numbers in its body: {links}. "
                      f"Resolved graph task targets: {targets}."])
    lines.extend(["", "## Meaning and limitations", "",
        "The ten issue IDs were sampled with a fixed deterministic rule **before** inspecting their bodies. "
        "Questions and short answers were annotated afterward and are not blinded or independently judged.",
        "The checks verify exact source text and required supporting phrases; they do NOT test "
        "autonomous language-model answers, scientific truth, or human research time. "
        "The GitHub API is a live source lookup, whereas the graph is a precomputed snapshot: "
        "network latency is not comparable to in-memory lookup latency.",
        "A missing cross-platform edge is a graph coverage gap, not evidence that no real-world "
        "relationship exists. Hypotheses and proposed training mixes are not established results.",
        "An internal GitHub issue/PR cross-reference proves only that its source text mentions an indexed task. "
        "It does not prove a dependency, that a PR was merged, or that a finding was reproduced.",
        "Source-body SHA256, update times, question annotations and graph link targets are retained in the JSON evidence.", ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default="results/snapshot.json")
    parser.add_argument("--cases", default="holdout_cases.json")
    parser.add_argument("--output", default="results")
    args = parser.parse_args(argv)
    graph = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    study = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    result = evaluate(graph, study)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    failed = result["status"] == "source_error"
    suffix = "_ERROR" if failed else ""
    stem = "holdout_evidence_error" if failed else "holdout_evidence"
    (output / f"{stem}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / f"HOLDOUT_EVIDENCE{suffix}.md").write_text(markdown(result), encoding="utf-8")
    print(f"Holdout study: {result['sources_available']}/{result['selected']} sources, "
          f"{result['exact_source_parity']} exact graph copies, {result['linked_issues']} linked issues")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
