"""Read-only cross-platform research metadata probe (stdlib only)."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


GITHUB_REPOS = ("OpenEuroLLM/Taskboard", "OpenEuroLLM/oellm-eval", "OpenEuroLLM/oellm-autoexp")
HF_ORG = "openeurollm"
UA = "ai-research-graph/0.1 (public metadata research probe)"


def fetch_json(url: str, *, token: str | None = None, timeout: int = 20):
    headers = {"Accept": "application/json", "User-Agent": UA}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def github_issues(repo: str, *, token: str | None = None, max_pages: int = 10):
    issues = []
    for page in range(1, max_pages + 1):
        query = urllib.parse.urlencode({"state": "all", "per_page": 100, "page": page})
        batch = fetch_json(f"https://api.github.com/repos/{repo}/issues?{query}", token=token)
        if not isinstance(batch, list):
            raise ValueError(f"Unexpected GitHub response for {repo}: {type(batch)}")
        for item in batch:
            issues.append({
                "id": f"github:{repo}#{item['number']}",
                "type": "pull_request" if "pull_request" in item else "issue",
                "title": item.get("title", ""),
                "url": item["html_url"],
                "description": item.get("body") or "",
                "state": item.get("state", ""),
                "updated_at": item.get("updated_at"),
                "repository": repo,
            })
        if len(batch) < 100:
            break
    return issues


def huggingface_assets(org: str, kind: str):
    if kind not in ("models", "datasets"):
        raise ValueError(kind)
    query = urllib.parse.urlencode({"author": org, "limit": 1000, "full": "true", "cardData": "true"})
    data = fetch_json(f"https://huggingface.co/api/{kind}?{query}")
    if not isinstance(data, list):
        raise ValueError(f"Unexpected Hugging Face {kind} response")
    prefix = "model" if kind == "models" else "dataset"
    return [{
        "id": f"hf:{prefix}:{item['id']}",
        "type": prefix,
        "title": item["id"],
        "url": f"https://huggingface.co/{'datasets/' if prefix == 'dataset' else ''}{item['id']}",
        "description": json.dumps(item.get("cardData") or {}, ensure_ascii=False)[:20000],
        "updated_at": item.get("lastModified"),
    } for item in data]


def openaire_products(search: str = "OpenEuroLLM"):
    query = urllib.parse.urlencode({"search": search, "page_size": 100})
    data = fetch_json(f"https://api.openaire.eu/graph/v4/research-products?{query}", timeout=25)
    return ([{
        "id": "openaire:" + str(item.get("id") or item.get("mainTitle")),
        "type": "research_product",
        "title": item.get("mainTitle") or "",
        "url": str(item.get("id") or ""),
        "description": "",
        "updated_at": None,
        "research_type": item.get("type"),
    } for item in data.get("results", [])], data.get("header", {}).get("numFound"))


def normalized(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")


def links_between(nodes: list[dict]) -> list[dict]:
    """Cross-source links only. Never turn fuzzy matches into verified facts."""
    edges = []
    github = [node for node in nodes if node["id"].startswith("github:")]
    other = [node for node in nodes if node["id"].startswith("hf:")]
    for issue in github:
        body = issue["title"] + "\n" + issue.get("description", "")
        body_lower = body.lower()
        body_normalized = normalized(body)
        for asset in other:
            direct_url = asset["url"].lower().rstrip("/")
            bare_id = asset["title"].lower()
            slug = normalized(asset["title"].split("/", 1)[-1])
            if direct_url in body_lower or bare_id in body_lower:
                edges.append({"source": issue["id"], "target": asset["id"], "status": "verified", "reason": "explicit URL or repository ID in source text"})
            elif len(slug) >= 9 and slug in body_normalized:
                edges.append({"source": issue["id"], "target": asset["id"], "status": "candidate", "reason": "asset name mentioned; requires review"})
    return edges


def report(nodes: list[dict], links: list[dict], errors: dict[str, str], snapshot: str, total_openaire: int | None):
    counts = {kind: sum(node["type"] == kind for node in nodes) for kind in ("issue", "pull_request", "model", "dataset", "research_product")}
    verified = [edge for edge in links if edge["status"] == "verified"]
    candidates = [edge for edge in links if edge["status"] == "candidate"]
    lines = [
        "# OpenEuroLLM research graph – exploratory snapshot", "",
        f"Collected: `{snapshot}` (UTC). Source: public APIs, read-only.", "",
        "## Coverage", "",
        *[f"- {key}: **{value}** records" for key, value in counts.items()],
        f"- OpenAIRE keyword-search total (not project coverage): **{total_openaire if total_openaire is not None else 'unavailable'}**", "",
        "## Cross-platform evidence", "",
        f"- Explicit URL/ID mentions: **{len(verified)}**", f"- Name-only candidates, NOT verified: **{len(candidates)}**", "",
        "| GitHub task | Hugging Face resource | Evidence |", "| --- | --- | --- |",
    ]
    index = {node["id"]: node for node in nodes}
    for edge in (verified + candidates)[:40]:
        source, target = index[edge["source"]], index[edge["target"]]
        lines.append(f"| [#{source['id'].rsplit('#', 1)[-1]}]({source['url']}) | [{target['title']}]({target['url']}) | {edge['status']} |")
    if not links:
        lines.append("| No observed cross-source references | – | – |")
    lines.extend(["", "## Source errors / incomplete coverage", ""])
    lines.extend(f"- `{name}`: {message}" for name, message in errors.items())
    if not errors:
        lines.append("- No source errors encountered.")
    lines.extend(["", "## Interpretation", "", "This is a discovery probe, **not** a complete research knowledge graph. The OpenAIRE search is keyword-based; missing search hits do not establish missing scholarly records. No AI-inferred links are presented as facts.", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results")
    parser.add_argument("--fixture", help="Read a local JSON input instead of querying APIs (offline tests)")
    args = parser.parse_args(argv)
    snapshot = dt.datetime.now(dt.timezone.utc).isoformat()
    errors: dict[str, str] = {}
    nodes: list[dict] = []
    openaire_total = None
    if args.fixture:
        fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        nodes = fixture["nodes"]
    else:
        for repo in GITHUB_REPOS:
            try:
                nodes.extend(github_issues(repo, token=os.getenv("GITHUB_TOKEN")))
            except (ValueError, urllib.error.URLError, TimeoutError) as exc:
                errors[repo] = str(exc)
        for kind in ("models", "datasets"):
            try:
                nodes.extend(huggingface_assets(HF_ORG, kind))
            except (ValueError, urllib.error.URLError, TimeoutError) as exc:
                errors[f"Hugging Face {kind}"] = str(exc)
        try:
            products, openaire_total = openaire_products()
            nodes.extend(products)
        except (ValueError, urllib.error.URLError, TimeoutError) as exc:
            errors["OpenAIRE"] = str(exc)
    edges = links_between(nodes)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp_utc": snapshot, "nodes": nodes, "edges": edges, "errors": errors, "openaire_search_total": openaire_total}
    (output / "snapshot.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "REPORT.md").write_text(report(nodes, edges, errors, snapshot, openaire_total), encoding="utf-8")
    print(f"Collected {len(nodes)} records, {len(edges)} potential links, {len(errors)} source errors")
    return 0 if nodes else 1


if __name__ == "__main__":
    sys.exit(main())
