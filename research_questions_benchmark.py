"""20-question GitHub task-reference retrieval comparison (stdlib only).

Compares the same title query and source-repository/type scope using:
  - precomputed graph task edges;
  - plain snapshot source-text matching;
  - live GitHub issue/PR title search and search-result body inspection.
No LLM, human-time or scientific-truth claims are made.
"""

from __future__ import annotations

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
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

from holdout_study import read_issue
from retrieval_benchmark import rank


TASK_URL = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/(?:issues|pull)/([1-9]\d*)(?=$|[/?#\s\]>)\.,;:])", re.I)
QUALIFIED = re.compile(r"(?<![\w./-])([\w.-]+)/([\w.-]+)#([1-9]\d*)(?![\w-])")
LOCAL = re.compile(r"(?<![\w/#])#([1-9]\d*)(?![\w-])")
UA = "ai-research-graph-questions/0.1"


def source_references(text: str, repo: str, indexed: set[str]) -> list[str]:
    """Independently parse raw issue-body links, never inspecting graph edges.

    Unindexed targets are outside this experiment's answer vocabulary.
    """
    spans = []
    candidates = []
    for pattern, kind in ((TASK_URL, "url"), (QUALIFIED, "qualified"), (LOCAL, "local")):
        for match in pattern.finditer(text):
            if any(start <= match.start() < end for start, end in spans):
                continue
            spans.append(match.span())
            if kind == "local":
                target = f"github:{repo}#{match.group(1)}"
            else:
                target = f"github:{match.group(1)}/{match.group(2)}#{match.group(3)}"
            if target.casefold() in indexed:
                candidates.append(target.casefold())
    return sorted(set(candidates))


def selected_source(nodes: list[dict], case: dict) -> tuple[list[str], dict | None]:
    """All methods know only the source repository and issue-vs-PR category."""
    anchor_repo = case["anchor_id"].split(":", 1)[1].rsplit("#", 1)[0]
    anchor_type = case["source_type"]
    eligible = [node for node in nodes if node.get("repository", "").casefold() == anchor_repo.casefold()
                and node.get("type") == anchor_type]
    ranked = rank(eligible, case["search_query"], limit=10)
    by_id = {node["id"]: node for node in eligible}
    return ranked, by_id.get(ranked[0]) if ranked else None


def github_title_search(repo: str, kind: str, phrase: str, *, timeout=20) -> dict:
    """Use the public GitHub search API; return errors rather than zero hits on failure."""
    qualifier = "is:issue" if kind == "issue" else "is:pull-request"
    # Punctuation in task titles can be search syntax; tokenize just the frozen query.
    terms = re.findall(r"[\w.-]+", phrase)
    query = f"repo:{repo} {qualifier} in:title " + " ".join(terms)
    url = "https://api.github.com/search/issues?" + urllib.parse.urlencode({"q": query, "per_page": 10})
    headers = {"Accept": "application/vnd.github+json", "User-Agent": UA}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    for attempt in range(3):
        started = time.perf_counter()
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = json.load(response)
            if not isinstance(result.get("items"), list):
                raise ValueError("Search API returned no items array")
            return {"items": result["items"], "total_count": result.get("total_count"),
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                    "query": query}
        except (urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in (408, 429) and exc.code < 500:
                raise
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def sampled_ms(func, repeats=21):
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        func()
        samples.append((time.perf_counter() - started) * 1000)
    return round(statistics.median(samples), 4)


def score(anchor: str, expected: list[str], source_id: str | None, targets: list[str]):
    """A negative case is correct only if the right source was found and no targets returned."""
    source_correct = source_id == anchor
    exact = source_correct and set(targets) == set(expected)
    hits = len(set(expected) & set(targets)) if source_correct else 0
    false_positive = len(set(targets) - set(expected)) if source_correct else len(targets)
    return {"source_top1": source_correct, "exact_answer": exact,
            "true_positives": hits, "false_positives": false_positive,
            "false_negatives": len(expected) - hits,
            "abstention_correct": source_correct and not expected and not targets}


def evaluate(graph: dict, study: dict, *, fetch=read_issue, search=github_title_search,
             repeats=21, delay=2.1, sleep=time.sleep) -> dict:
    nodes = graph["nodes"]
    by_id = {node["id"]: node for node in nodes}
    indexed = {id_.casefold() for id_, node in by_id.items()
               if node.get("type") in ("issue", "pull_request")}
    outgoing = defaultdict(list)
    for edge in graph["edges"]:
        if edge.get("status") == "explicit_task_reference":
            outgoing[edge["source"]].append(edge["target"])
    entries = []
    seen = set()
    for case in study["cases"]:
        case_id, anchor = case["id"], case["anchor_id"]
        if case_id in seen or anchor in seen:
            raise ValueError("Duplicate benchmark case id or source anchor")
        seen.update((case_id, anchor))
        anchor_node = by_id.get(anchor)
        if anchor_node is None or anchor_node.get("type") not in ("issue", "pull_request"):
            raise ValueError(f"Missing GitHub task anchor: {anchor}")
        entries.append({**case, "source_type": anchor_node["type"]})

    rows = []
    for number, case in enumerate(entries):
        anchor = case["anchor_id"]
        node = by_id[anchor]
        repo = node["repository"]
        issue_number = int(anchor.rsplit("#", 1)[1])
        expected = sorted(case["expected_ids"])
        row = {"id": case["id"], "cohort": case["cohort"], "anchor_id": anchor,
               "question": f"Which indexed tasks are explicitly cited by: {node['title']}?",
               "search_query": case["search_query"], "expected_ids": expected,
               "source_url": node["url"]}
        try:
            original = fetch(repo, issue_number)
            if original.get("updated_at") != node.get("updated_at") or original["body"] != (node.get("description") or ""):
                raise ValueError("Live source changed since snapshot: comparison would be stale")
            row["source_sha256"] = hashlib.sha256(original["body"].encode("utf-8")).hexdigest()
            raw_refs = source_references(node.get("title", "") + "\n" + original["body"], repo, indexed)
            if raw_refs != sorted(t.casefold() for t in expected):
                raise ValueError(f"Frozen gold differs from original source text: expected={expected}, found={raw_refs}")
            candidates, best = selected_source(nodes, case)
            row["snapshot_top10"] = candidates
            source_id = best["id"] if best else None
            graph_targets = sorted(outgoing.get(source_id, [])) if best else []
            text_targets = source_references(best.get("title", "") + "\n" + (best.get("description") or ""),
                                             best["repository"], indexed) if best else []
            graph_targets_norm = sorted(x.casefold() for x in graph_targets)
            def graph_lookup():
                _, chosen = selected_source(nodes, case)
                return sorted(outgoing.get(chosen["id"], [])) if chosen else []

            def text_lookup():
                _, chosen = selected_source(nodes, case)
                return source_references(chosen.get("title", "") + "\n" + (chosen.get("description") or ""),
                                         chosen["repository"], indexed) if chosen else []

            row["graph"] = {**score(anchor, [x.casefold() for x in expected], source_id,
                                      graph_targets_norm), "targets": graph_targets,
                            "median_lookup_ms": sampled_ms(graph_lookup, repeats)}
            row["text"] = {**score(anchor, [x.casefold() for x in expected], source_id, text_targets),
                           "targets": text_targets,
                           "median_lookup_ms": sampled_ms(text_lookup, repeats)}
            # Separate search calls to respect GitHub's tighter search quota.
            if number and delay:
                sleep(delay)
            live = search(repo, node["type"], case["search_query"])
            items = live["items"]
            search_ids = [f"github:{repo}#{item['number']}" for item in items]
            first = items[0] if items else None
            search_id = search_ids[0] if search_ids else None
            if first is not None and not isinstance(first.get("body"), str):
                raise ValueError("Search hit omitted issue text; cannot verify answer")
            search_targets = source_references((first.get("title") or "") + "\n" + first["body"],
                                               repo, indexed) if first else []
            row["github_search"] = {**score(anchor, [x.casefold() for x in expected], search_id,
                                               search_targets), "targets": search_targets,
                                    "source_top10": anchor in search_ids, "top10": search_ids,
                                    "latency_ms": live["latency_ms"], "query": live["query"],
                                    "total_results": live["total_count"]}
            row["status"] = "evaluated"
        except (ValueError, KeyError, urllib.error.URLError, TimeoutError) as exc:
            row.update({"status": "source_error", "error": f"{type(exc).__name__}: {exc}"})
        rows.append(row)

    success = all(row["status"] == "evaluated" for row in rows)
    methods = ("graph", "text", "github_search")
    summary = {}
    for cohort in ("all", "random", "reference_rich"):
        group = [row for row in rows if row["status"] == "evaluated" and
                 (cohort == "all" or row["cohort"] == cohort)]
        summary[cohort] = {method: {
            "cases": len(group), "source_top1": sum(row[method]["source_top1"] for row in group),
            "exact_answers": sum(row[method]["exact_answer"] for row in group),
            "correct_abstentions": sum(row[method]["abstention_correct"] for row in group),
            "true_positives": sum(row[method]["true_positives"] for row in group),
            "false_positives": sum(row[method]["false_positives"] for row in group),
            "false_negatives": sum(row[method]["false_negatives"] for row in group),
            "median_ms": round(statistics.median(
                row[method].get("latency_ms", row[method].get("median_lookup_ms")) for row in group), 4) if group else None,
        } for method in methods}
    return {"status": "completed" if success else "source_error",
            "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "snapshot_utc": graph.get("timestamp_utc"), "selection": study["selection"],
            "selected": len(entries), "evaluated": sum(row["status"] == "evaluated" for row in rows),
            "summary": summary, "cases": rows}


def markdown(result):
    rows = ["# Twenty source-grounded GitHub research questions", "",
            f"Snapshot: `{result['snapshot_utc']}`. Verified: **{result['evaluated']}/{result['selected']}**. "
            f"Status: `{result['status']}`.", "",
            "## Exact target-set correctness and correct abstentions", "",
            "| Cohort | Method | Exact answers | Correct no-link answers | Source top-1 | Median lookup (ms) |",
            "| --- | --- | ---: | ---: | ---: | ---: |"]
    labels = {"graph": "Precomputed evidence graph", "text": "Source text (same snapshot)",
              "github_search": "Live GitHub issue/PR search"}
    for cohort in ("all", "random", "reference_rich"):
        for method, data in result["summary"][cohort].items():
            rows.append(f"| {cohort} | {labels[method]} | {data['exact_answers']}/{data['cases']} | "
                        f"{data['correct_abstentions']} | {data['source_top1']}/{data['cases']} | "
                        f"{data['median_ms'] if data['median_ms'] is not None else 'n/a'} |")
    rows.extend(["", "**Do not compare snapshot milliseconds with live GitHub search milliseconds as a speedup.** "
                 "The former has already paid data-collection and graph-indexing costs; the latter includes network latency. "
                 "GitHub search indexing and rate limits may also affect results.", "",
                 "The random cohort was selected by fixed ID hashing without looking at bodies; the second cohort "
                 "was deliberately enriched for reference-bearing tasks and can make the overall score optimistic. "
                 "Frozen expected IDs were curated from source text; this is **not** a blinded human/LLM evaluation. "
                 "All methods have the same repository, source type and title search phrase. "
                 "The graph and text routes inspect captured data; the GitHub method uses live issue/PR search. "
                 "A literal cross-reference does not prove an implementation, experiment or scientific dependency.", "",
                 "## Per-question audit", "",
                 "| Source task and question | Gold links | Graph exact | Text exact | GitHub exact |",
                 "| --- | ---: | --- | --- | --- |"])
    for case in result["cases"]:
        if case["status"] != "evaluated":
            rows.append(f"| {case['id']} — {case['error']} | – | – | – | – |")
            continue
        anchor = f"[{case['anchor_id']}]({case['source_url']})"
        rows.append(f"| {anchor}: {case['question'].split(': ', 1)[-1]} | {len(case['expected_ids'])} | "
                    f"{case['graph']['exact_answer']} | {case['text']['exact_answer']} | "
                    f"{case['github_search']['exact_answer']} |")
    rows.extend(["", "## Interpretation", "",
                 "Primary outcomes are source top-1 accuracy and exact answer-set accuracy, not model-generated "
                 "answer quality. Correct abstention requires identifying the correct source and returning no "
                 "indexed links. Source-body SHA256 and retrieved IDs are in the JSON audit. "
                 "Source failures are not counted as zero and never overwrite the last complete report.",
                 "A useful next experiment needs independently authored, genuinely unseen researcher questions "
                 "and an end-to-end tool-using agent evaluated with source-grounded answer judgments.", ""])
    return "\n".join(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default="results/snapshot.json")
    parser.add_argument("--cases", default="research_question_cases.json")
    parser.add_argument("--output", default="results")
    args = parser.parse_args(argv)
    graph = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    study = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    result = evaluate(graph, study)
    target = Path(args.output)
    target.mkdir(parents=True, exist_ok=True)
    suffix = "_ERROR" if result["status"] != "completed" else ""
    stem = "research_questions_error" if suffix else "research_questions"
    (target / f"{stem}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (target / f"RESEARCH_QUESTIONS{suffix}.md").write_text(markdown(result), encoding="utf-8")
    print(f"Twenty research questions: {result['evaluated']}/{result['selected']} evaluated, "
          f"status={result['status']}")
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
