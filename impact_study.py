"""Evidence audit of ten candidate changes in OpenEuroLLM research workflows.

This is a purposefully selected case study, not an autonomous priority ranking.
Source text supports a candidate or a reported result, never an inferred speedup.
"""

import argparse
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

from holdout_study import digest, read_issue
from http_util import get_json


def read_comment(repo, comment_id, *, timeout=20):
    """Fetch an individual public comment by immutable GitHub comment ID."""
    url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
    data, _ = get_json(url, user_agent="ai-research-graph-impact", timeout=timeout)
    if data.get("id") != comment_id or not isinstance(data.get("body"), str):
        raise ValueError(f"Comment {comment_id}: invalid body or ID")
    return {"body": data["body"], "updated_at": data.get("updated_at"),
            "url": data.get("html_url", url)}


def evaluate(graph, study, *, fetch_issue=read_issue, fetch_comment=read_comment):
    """Check literal phrases against live bodies/comments and graph parity separately."""
    cases = study["cases"]
    if len(cases) != 10 or len({(case["repo"], case["number"]) for case in cases}) != 10:
        raise ValueError("Expected exactly ten distinct, preselected issues")
    index = {node["id"].casefold(): node for node in graph["nodes"]}
    refs = {(edge["source"].casefold(), edge["target"].casefold()) for edge in graph["edges"]
            if edge["status"] == "explicit_task_reference"}
    declared_dependencies = {(edge["source"].casefold(), edge["target"].casefold())
                             for edge in graph["edges"] if edge["status"] == "author_declared_dependency"}
    reported_blockers = {(edge["source"].casefold(), edge["target"].casefold())
                         for edge in graph["edges"] if edge["status"] == "reported_blocker"}
    issues, comments = {}, {}

    def issue(repo, number):
        key = (repo, number)
        if key not in issues:
            issues[key] = fetch_issue(repo, number)
        return issues[key]

    def comment(repo, comment_id):
        key = (repo, comment_id)
        if key not in comments:
            comments[key] = fetch_comment(repo, comment_id)
        return comments[key]

    rows = []
    for case in cases:
        anchor = f"github:{case['repo']}#{case['number']}"
        row = {"id": case["id"], "anchor_id": anchor,
               "impact_type": case["impact_type"], "evidence_class": case["evidence_class"],
               "candidate": case["candidate"], "next_check": case["next_check"]}
        try:
            src = issue(case["repo"], case["number"])
            row.update({"source_url": src["url"], "source_updated_at": src.get("updated_at"),
                        "source_sha256": digest(src["body"]), "live_state": src.get("state"),
                        "title": src.get("title"),
                        "issue_author": src.get("issue_author"),
                        "assignees": src.get("assignees", [])})
            node = index.get(anchor.casefold())
            row["graph_status"] = ("not_indexed" if node is None else
                                   "exact_parity" if node.get("updated_at") == src.get("updated_at")
                                   and (node.get("description") or "") == src["body"] else "stale_or_changed")
            row["graph_reference_count"] = sum(source == anchor.casefold() for source, _ in refs)
            row["evidence"] = []
            row["graph_comment_evidence"] = {}
            for claim in case["evidence"]:
                if claim["source"] == "body":
                    proof = src
                elif claim["source"] == "comment":
                    proof = comment(case["repo"], claim["comment_id"])
                    graph_id = f"github_comment:{case['repo']}#{claim['comment_id']}"
                    stored = index.get(graph_id.casefold())
                    graph_status = ("not_indexed" if stored is None else
                                    "exact_parity" if stored.get("description") == proof["body"]
                                    and stored.get("updated_at") == proof.get("updated_at")
                                    and stored.get("body_sha256") == digest(proof["body"])
                                    else "stale_or_changed")
                    row["graph_comment_evidence"][graph_id] = graph_status
                else:
                    raise ValueError(f"Unsupported evidence origin: {claim['source']}")
                if claim["needle"].casefold() not in proof["body"].casefold():
                    raise ValueError(f"Supporting phrase missing in {claim['source']}: {claim['needle']!r}")
                row["evidence"].append({"source": claim["source"], "url": proof["url"],
                                        "updated_at": proof.get("updated_at"),
                                        "sha256": digest(proof["body"]),
                                        "matched_text": claim["needle"], "meaning": claim["meaning"]})
            dependency = case.get("dependency")
            if dependency:
                upstream_id = f"github:{dependency['repo']}#{dependency['number']}"
                upstream = issue(dependency["repo"], dependency["number"])
                # Only a literal dependency annotation establishes this relation;
                # a generic #432 cross-reference is never re-labelled as 'blocks'.
                row["declared_dependency"] = {
                    "task_id": upstream_id, "url": upstream["url"],
                    "live_state": upstream.get("state"),
                    "graph_contains_literal_reference": (anchor.casefold(), upstream_id.casefold()) in refs,
                    "graph_contains_author_declared_dependency": (anchor.casefold(), upstream_id.casefold()) in declared_dependencies,
                    "evidence_scope": "literal Dependencies section in the issue body",
                }
            row["graph_reported_blockers"] = [
                comment_id for comment_id in row["graph_comment_evidence"]
                if (comment_id.casefold(), anchor.casefold()) in reported_blockers]
            row["status"] = "evidence_verified"
        except (KeyError, ValueError, OSError, TimeoutError) as exc:
            row.update({"status": "source_error", "error": f"{type(exc).__name__}: {exc}"})
        rows.append(row)

    valid = [row for row in rows if row["status"] == "evidence_verified"]
    return {
        "status": "completed" if len(valid) == 10 else "source_error",
        "evaluated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "snapshot_utc": graph.get("timestamp_utc"), "selection": study["selection"],
        "selected": len(rows), "verified": len(valid), "live_issues_fetched": len(issues),
        "comments_verified": len(comments),
        "source_phrases_verified": sum(len(row["evidence"]) for row in valid),
        "exact_snapshot_parity": sum(row["graph_status"] == "exact_parity" for row in valid),
        "comment_dependent_cases": sum(any(e["source"] == "comment" for e in row["evidence"]) for row in valid),
        "graph_comments_exact": sum(status == "exact_parity" for row in valid
                                    for status in row["graph_comment_evidence"].values()),
        "graph_comments_selected": sum(len(row["graph_comment_evidence"]) for row in valid),
        "graph_author_dependencies_confirmed": sum(
            row.get("declared_dependency", {}).get("graph_contains_author_declared_dependency", False)
            for row in valid),
        "graph_oom_reports_linked": sum(len(row.get("graph_reported_blockers", [])) for row in valid),
        "class_counts": dict(Counter(row["evidence_class"] for row in valid)),
        "cases": rows,
    }


def markdown(result):
    lines = ["# OpenEuroLLM change-impact candidates: ten original-source audits", "",
             f"Graph snapshot: `{result['snapshot_utc']}`. Evaluated: `{result['evaluated_utc']}`. "
             f"Evidence verified: **{result['verified']}/{result['selected']}** cases, "
             f"**{result['source_phrases_verified']}** literal phrases, "
             f"**{result['comments_verified']}** separately fetched comments. "
             f"Status: `{result['status']}`.", "",
             f"Graph source parity for selected comments: **{result['graph_comments_exact']}/"
             f"{result['graph_comments_selected']}**. Author-declared upstream links in the graph: "
             f"**{result['graph_author_dependencies_confirmed']}**; commenter-reported OOM links: "
             f"**{result['graph_oom_reports_linked']}**. These are evidence classifications, "
             f"not independent validation of the asserted dependency or failure.", "",
             "**This is not a speedup ranking.** The ten open issues were purposefully selected "
             "for varied engineering signals. A reported result has not been independently reproduced; "
             "an issue reference does not prove a blocker. Do not sum unlike speed, accuracy and automation claims.", "",
             "## Candidate changes and validation needed", "",
             "| Issue | Source evidence class | Proposed change | Missing proof before impact claim |",
             "| --- | --- | --- | --- |"]
    for row in result["cases"]:
        if row["status"] == "evidence_verified":
            label = f"[{row['anchor_id']}]({row['source_url']})"
        else:
            label = f"`{row['anchor_id']}` (source error: {row['error']})"
        lines.append(f"| {label} | `{row['evidence_class']}` | {row['candidate']} | {row['next_check']} |")
    lines.extend(["", "## Inspectable original-source evidence", ""])
    for row in result["cases"]:
        lines.append(f"### {row['anchor_id']} — {row.get('title', 'unavailable')}")
        lines.append("")
        if row["status"] != "evidence_verified":
            lines.extend([f"Source error: `{row['error']}`.", ""])
            continue
        lines.append(f"Live issue state: `{row.get('live_state')}`. Body versus graph: "
                     f"`{row['graph_status']}`. GitHub task-reference edges from this issue: "
                     f"**{row['graph_reference_count']}**. Issue-body SHA256: `{row['source_sha256']}`.")
        lines.append("")
        for claim in row["evidence"]:
            excerpt = claim["matched_text"].replace("`", "'")
            lines.append(f"- [{claim['source']} evidence]({claim['url']}): `{excerpt}` — {claim['meaning']}")
        if row["graph_comment_evidence"]:
            lines.append("- Source-hashed comment nodes in graph: " + ", ".join(
                f"`{comment_id}` (`{status}`)" for comment_id, status in row["graph_comment_evidence"].items()))
        dependency = row.get("declared_dependency")
        if dependency:
            lines.append(f"- [Explicitly named upstream task]({dependency['url']}): "
                         f"`{dependency['task_id']}` (live state `{dependency['live_state']}`, "
                         f"literal graph reference: `{dependency['graph_contains_literal_reference']}`, "
                         f"declared-dependency edge: `{dependency['graph_contains_author_declared_dependency']}`).")
        lines.append("")
    lines.extend(["## Research validity and next step", "",
                  "- **Measured training throughput**: #385 reports an approximately 9.5% uplift "
                  "for a revised worker assignment, with production acceptance still outstanding. "
                  "The report verifies that the authors made this claim, not its reproducibility.",
                  "- **Evaluation quality, not speed**: #442's comments document a thinking-mode "
                  "accuracy difference; a same-base control is noted as pending. Increased generated "
                  "tokens could make the stronger quality result slower to compute.",
                  "- **Dependency and feasibility**: #391 explicitly lists #432 as an upstream "
                  "task; #433's comment reports a LUMI OOM problem. Neither is evidence of "
                  "a realized speedup.",
                  f"- **Comment coverage boundary**: issue comments in {result['comment_dependent_cases']} cases contain "
                  "essential evidence. The graph now stores source-hashed comments for the ten selected issues "
                  "only; other tasks have not received a complete comment audit. Queries outside this sample "
                  "must inspect original comments or abstain from claiming no known blocker.",
                  "- **Selection bias**: these ten items were selected for promising, different "
                  "signals after seeing issue titles. They are not representative of the "
                  "indexed issue population and cannot establish which project should receive resources.",
                  "- **Impact estimation**: a credible next experiment needs a causal dependency "
                  "relationship, a baseline, a same-configuration intervention, adoption/rollout "
                  "status and an outcome measurement. A graph-edge count alone is not impact.", ""])
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot", default="results/snapshot.json")
    p.add_argument("--cases", default="impact_cases.json")
    p.add_argument("--output", default="results")
    args = p.parse_args(argv)
    graph = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    study = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    result = evaluate(graph, study)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    failed = result["status"] != "completed"
    (out / ("impact_error.json" if failed else "impact_evidence.json")).write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / ("IMPACT_ERROR.md" if failed else "IMPACT_EVIDENCE.md")).write_text(
        markdown(result), encoding="utf-8")
    print(f"Impact audit: {result['verified']}/{result['selected']}, "
          f"comments={result['comments_verified']}, status={result['status']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
