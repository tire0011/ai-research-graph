"""Build inspectable source packets for research QA; no model or API calls.

The program tests that graph metadata supports a cautious answer. Producing the
natural-language answer is a separate LLM step, not simulated here.
"""

import argparse
import datetime as dt
import json
from pathlib import Path


def source_record(node: dict, role: str) -> dict:
    return {"role": role, "id": node["id"], "title": node["title"], "url": node["url"]}


def examine_case(graph: dict, case: dict) -> dict:
    """Verify precise provenance paths, never infer 'trained_on' from a citation."""
    index = {node["id"]: node for node in graph["nodes"]}
    result = {"id": case["id"], "question": case["question"],
              "kind": case["kind"], "passed": False, "sources": []}

    if case["kind"] == "shared_citation":
        arxiv = case["arxiv"]
        papers = [node for node in graph["nodes"]
                  if node["type"] == "research_product" and arxiv in node.get("identifiers", {}).get("arxiv", [])]
        github = index.get(case["github_id"])
        asset = index.get(case["hf_id"])
        for paper in papers:
            required = {case["github_id"], case["hf_id"]}
            observed = {edge["source"] for edge in graph["edges"]
                        if edge["target"] == paper["id"] and edge["status"] == "identifier_match"
                        and edge["evidence_type"] == "arxiv" and edge["evidence"] == arxiv}
            if github and asset and required.issubset(observed):
                result.update({"passed": True, "relationship": "shared_paper_citation",
                               "shared_arxiv_id": arxiv,
                               "sources": [source_record(github, "github_task"),
                                           source_record(paper, "publication"),
                                           source_record(asset, "hf_artifact")],
                               "limits": "The sources cite the same publication. No direct dataset usage, evaluation, or causal dependency is proven."})
                break
        if not result["passed"]:
            result["error"] = "Required exact scholarly ID join or one of its source records is missing"

    elif case["kind"] == "publisher_declaration_check":
        declared_id = case["declared_id"]
        model = index.get(case["hf_id"])
        ref = next((ref for ref in graph.get("external_hf_card_references", [])
                    if ref["source"] == case["hf_id"] and ref["target_type"] == case["target_type"]
                    and ref["declared_id"].casefold() == declared_id.casefold()), None)
        check = next((check for check in graph.get("external_hf_target_checks") or []
                      if check["target_type"] == case["target_type"]
                      and check["declared_id"].casefold() == declared_id.casefold()), None)
        edges = [edge for edge in graph["edges"]
                 if edge["source"] == case["hf_id"] and edge["status"].startswith("declared_metadata")
                 and edge.get("evidence", "").casefold() == declared_id.casefold()]
        if model and ref and check:
            verified = check["status"] in ("verified_public", "verified_redirect")
            consistent = bool(edges) == verified
            if consistent:
                result.update({"passed": True,
                               "relationship": "publisher_declaration_to_public_target" if verified else "unverified_publisher_declaration",
                               "lookup_status": check["status"],
                               "status_changed_from_baseline": check["status"] != case.get("expected_lookup_status", check["status"]),
                               "declared_target": declared_id,
                               "sources": [source_record(model, "publisher_model_card"),
                                           {"role": "api_confirmed_target" if verified else "unverified_target",
                                            "id": edges[0]["target"] if verified else declared_id,
                                            "title": declared_id, "url": ref["target_url"]}],
                               "limits": "The API confirms the declared resource's public identity, not that training used it." if verified else
                                         f"The model card declares this resource, but the Hub lookup is {check['status']}; use cannot be independently confirmed."})
            else:
                result["error"] = "API verification and graph edge disagree; do not answer from inconsistent evidence"
        else:
            result["error"] = "Missing source model, model-card declaration or API lookup result"
    else:
        result["error"] = f"Unknown case kind: {case['kind']}"
    return result


def evaluate(graph: dict, cases: list[dict]) -> dict:
    results = [examine_case(graph, case) for case in cases]
    return {"snapshot_utc": graph.get("timestamp_utc"), "evaluated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "passed": sum(result["passed"] for result in results), "total": len(results), "cases": results}


def markdown_report(evaluation: dict) -> str:
    lines = ["# Research question evidence probe", "",
             "This is **source verification**, not an automated LLM response. The listed evidence is the minimal context an AI agent could receive; a language model must still be evaluated separately.", "",
             f"Graph snapshot: `{evaluation['snapshot_utc']}` UTC. Passed: **{evaluation['passed']}/{evaluation['total']}** evidence checks.", ""]
    for result in evaluation["cases"]:
        lines.extend([f"## {result['id']}", "", f"**Question:** {result['question']}", "",
                      f"**Evidence check:** {'PASS' if result['passed'] else 'FAIL'}", ""])
        if not result["passed"]:
            lines.extend([f"Problem: {result['error']}", ""])
            continue
        lines.append(f"Evidence classification: `{result['relationship']}`" +
                     (f"; arXiv `{result['shared_arxiv_id']}`" if result.get("shared_arxiv_id") else "") + ".")
        lines.append("")
        if result.get("status_changed_from_baseline"):
            lines.extend([f"**Freshness notice:** Target lookup status changed to `{result['lookup_status']}`; the previous AI answer needs re-review.", ""])
        for source in result["sources"]:
            lines.append(f"- {source['role']}: [{source['title']}]({source['url']})")
        lines.extend(["", f"**Limit:** {result['limits']}", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default="results/snapshot.json")
    parser.add_argument("--cases", default="qa_cases.json")
    parser.add_argument("--output", default="results/QA_EVIDENCE.md")
    args = parser.parse_args(argv)
    graph = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    evaluation = evaluate(graph, cases)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown_report(evaluation), encoding="utf-8")
    print(f"Research QA evidence: {evaluation['passed']}/{evaluation['total']} checks passed")
    return 0 if evaluation["passed"] == evaluation["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
