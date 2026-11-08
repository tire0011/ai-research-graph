"""Compare precomputed graph joins with plain-text search of the SAME snapshot.

This measures retrieval over already downloaded metadata, not live API latency,
human research time, LLM answer quality, or the value of an MCP server.
"""

import argparse
import datetime as dt
import json
import re
import statistics
import time
from collections import defaultdict
from pathlib import Path


STOP = {"which", "what", "does", "with", "from", "that", "this", "same", "the", "are", "and", "can", "how", "into", "have"}
TOP_K = 10


def tokens(query):
    return {term for term in re.findall(r"[a-z0-9]+", query.casefold())
            if len(term) >= 4 and term not in STOP}


def rank(nodes, question, limit=TOP_K, require_match=True):
    terms = tokens(question)

    def score(node):
        title = node.get("title", "").casefold()
        body = (node.get("description", "") or "").casefold()
        return 3 * sum(term in title for term in terms) + sum(term in body for term in terms)

    return [node["id"] for node in sorted(nodes, key=lambda n: (-score(n), n["id"]))
            if not require_match or score(node) > 0][:limit]


def graph_index(graph):
    nodes = {node["id"]: node for node in graph["nodes"]}
    outgoing, incoming = defaultdict(list), defaultdict(list)
    for edge in graph["edges"]:
        outgoing[edge["source"]].append(edge)
        incoming[edge["target"]].append(edge)
    return nodes, outgoing, incoming


def graph_candidates(index, case):
    nodes, outgoing, incoming = index
    anchor = case["anchor_id"]
    kind = case["kind"]
    if kind == "unverified_declaration":
        return []  # A declaration without a verified target is NOT a dependency.
    if kind == "explicit":
        candidates = {edge["target"] for edge in outgoing[anchor]
                      if edge["status"] == "explicit_reference"}
    elif kind == "shared_citation":
        papers = {edge["target"] for edge in outgoing[anchor]
                  if edge["status"] == "identifier_match"}
        candidates = {edge["source"] for paper in papers for edge in incoming[paper]
                      if edge["status"] == "identifier_match" and edge["source"] != anchor}
    else:
        raise ValueError(f"Unknown benchmark case kind: {kind}")
    return rank([nodes[id_] for id_ in candidates if id_ in nodes and
                 nodes[id_]["type"] == case["target_type"]], case["question"], require_match=False)


def text_candidates(graph, case):
    """No edges or cross-source joins: plain lexical search across source records."""
    candidates = [node for node in graph["nodes"]
                  if node["type"] == case["target_type"] and node["id"] != case["anchor_id"]]
    return rank(candidates, case["question"])


def declaration_status(graph, case):
    if case["kind"] != "unverified_declaration":
        return None
    match = lambda item: (item.get("declared_id", "").casefold() == case["declared_id"].casefold()
                          and item.get("target_type") == case["target_type"])
    refs = [ref for ref in graph.get("external_hf_card_references", [])
            if match(ref) and ref.get("source") == case["anchor_id"]]
    checks = [check for check in graph.get("external_hf_target_checks", []) if match(check)]
    if not refs or not checks:
        return "missing_source_evidence"
    return checks[0]["status"]


def median_ms(function, repetitions):
    samples = []
    for _ in range(repetitions):
        start = time.perf_counter()
        function()
        samples.append(1000 * (time.perf_counter() - start))
    return round(statistics.median(samples), 4)


def evaluate(graph, cases, repetitions=31):
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    begin = time.perf_counter()
    index = graph_index(graph)
    index_ms = round(1000 * (time.perf_counter() - begin), 4)
    results = []
    for case in cases:
        if case["anchor_id"] not in index[0]:
            results.append({"id": case["id"], "kind": case["kind"], "status": "missing_anchor"})
            continue
        if case["kind"] == "unverified_declaration":
            status = declaration_status(graph, case)
            results.append({"id": case["id"], "kind": case["kind"],
                            "status": "abstained" if status in {"inaccessible", "not_publicly_found", "rate_limited", "fetch_failed"}
                            else "needs_review", "source_lookup_status": status})
            continue
        graph_ids = graph_candidates(index, case)
        text_ids = text_candidates(graph, case)
        expected = case["expected_ids"]
        results.append({
            "id": case["id"], "kind": case["kind"], "status": "evaluated",
            "expected_ids": expected, "graph_hits": [id_ for id_ in expected if id_ in graph_ids],
            "text_hits": [id_ for id_ in expected if id_ in text_ids],
            "graph_top10": graph_ids, "text_top10": text_ids,
            "graph_median_ms": median_ms(lambda: graph_candidates(index, case), repetitions),
            "text_median_ms": median_ms(lambda: text_candidates(graph, case), repetitions),
        })
    evaluated = [case for case in results if case["status"] == "evaluated"]
    total = sum(len(case["expected_ids"]) for case in evaluated)
    return {
        "snapshot_utc": graph.get("timestamp_utc"),
        "evaluated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "nodes": len(graph["nodes"]), "edges": len(graph["edges"]),
        "index_build_ms": index_ms, "repetitions": repetitions, "top_k": TOP_K,
        "targets": total,
        "graph_recalled": sum(len(case["graph_hits"]) for case in evaluated),
        "text_recalled": sum(len(case["text_hits"]) for case in evaluated),
        "cases": results,
    }


def markdown(result):
    lines = [
        "# Cross-platform research retrieval: controlled comparison", "",
        f"Snapshot: `{result['snapshot_utc']}` UTC, **{result['nodes']} nodes**, **{result['edges']} edges**.",
        f"Scored {result['targets']} curated target artifacts in a top-{result['top_k']} shortlist.", "",
        "| Method | Found curated artifacts |", "| --- | ---: |",
        f"| Evidence graph | {result['graph_recalled']}/{result['targets']} |",
        f"| Plain-text source-record search | {result['text_recalled']}/{result['targets']} |", "",
        "Both methods use the **same captured source records** and receive the question and the source type. "
        "The graph also uses its previously computed, source-attributed edges. "
        "The plain-text baseline searches node titles/descriptions without traversing edges.", "",
        "**Important:** This is a small, intentionally curated *retrieval* check, not a held-out scientific benchmark, "
        "live GitHub/HF search, end-to-end human timing, proof of model training, or evidence that an MCP service is beneficial.", "",
        f"Graph index construction: {result['index_build_ms']:.4f} ms. "
        f"Each query timing is the median of {result['repetitions']} in-memory runs (no network).", "",
        "| Question | Graph targets | Text targets | Graph ms | Text ms |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for case in result["cases"]:
        if case["status"] != "evaluated":
            lines.extend(["", f"- **{case['id']}**: {case['status']} "
                          f"({case.get('source_lookup_status', 'no anchor')}); no positive retrieval score."])
            continue
        n = len(case["expected_ids"])
        lines.append(f"| {case['id']} | {len(case['graph_hits'])}/{n} | "
                     f"{len(case['text_hits'])}/{n} | {case['graph_median_ms']:.4f} | "
                     f"{case['text_median_ms']:.4f} |")
    lines.extend(["", "## Interpretation", "",
                  "A found artifact is not proof of scientific use. Citation joins indicate shared references; "
                  "declared metadata records remain declarations. Compare longer, genuinely unseen research questions "
                  "and include live source-search latency and researcher judgments before proposing a production MCP.", ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default="results/snapshot.json")
    parser.add_argument("--cases", default="retrieval_cases.json")
    parser.add_argument("--output", default="results")
    args = parser.parse_args(argv)
    graph = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    result = evaluate(graph, cases)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "retrieval_benchmark.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "RETRIEVAL_BENCHMARK.md").write_text(markdown(result), encoding="utf-8")
    print(f"Evidence graph {result['graph_recalled']}/{result['targets']}; text baseline {result['text_recalled']}/{result['targets']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
