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


def exact_reference(haystack: str, needle: str) -> re.Match | None:
    """Match full HF repository IDs/URLs, not prefixes of longer identifiers."""
    return re.search(r"(?<![a-z0-9_-])" + re.escape(needle) + r"(?![a-z0-9_-])", haystack, re.IGNORECASE)


def matching_context(text: str, match: re.Match, radius: int = 75) -> str:
    return " ".join(text[max(0, match.start() - radius):match.end() + radius].split())


def name_only_match(text: str, slug: str, owner: str) -> re.Match | None:
    """Ignore slug mentions that clearly refer to a different HF namespace."""
    foreign_references = re.finditer(
        r"(?<![a-z0-9_-])([a-z0-9_.-]+)/" + re.escape(slug) + r"(?![a-z0-9_-])",
        text, re.IGNORECASE,
    )
    if any(match.group(1).casefold() != owner.casefold() for match in foreign_references):
        return None
    pattern = re.compile(r"(?<![a-z0-9_-])" + re.escape(slug) + r"(?![a-z0-9_-])", re.IGNORECASE)
    for match in pattern.finditer(text):
        preceding = text[max(0, match.start() - 110):match.start()]
        namespace = re.search(r"([a-z0-9_.-]+)/$", preceding, re.IGNORECASE)
        if namespace and namespace.group(1).casefold() != owner.casefold():
            continue
        return match
    return None


def links_between(nodes: list[dict]) -> list[dict]:
    """Cross-source references only; these do not assert scientific dependency."""
    edges = []
    github = [node for node in nodes if node["id"].startswith("github:")]
    other = [node for node in nodes if node["id"].startswith("hf:")]
    for issue in github:
        body = issue["title"] + "\n" + issue.get("description", "")
        for asset in other:
            direct_url = asset["url"].rstrip("/")
            bare_id = asset["title"]
            slug = bare_id.split("/", 1)[-1]
            owner = bare_id.split("/", 1)[0]
            url_match = exact_reference(body, direct_url)
            id_match = exact_reference(body, bare_id)
            slug_match = name_only_match(body, slug, owner) if len(slug) >= 9 else None
            match = url_match or id_match or slug_match
            if not match:
                continue
            evidence_type = "url" if url_match else ("repository_id" if id_match else "name_only")
            edges.append({
                "source": issue["id"], "target": asset["id"],
                "status": "explicit_reference" if (url_match or id_match) else "candidate",
                "evidence_type": evidence_type,
                "evidence": match.group(),
                "context": matching_context(body, match),
                "reason": "Source mentions a specific HF resource" if (url_match or id_match) else "Name overlap only; manual confirmation required",
            })
    return edges


def quality_profile(nodes: list[dict], edges: list[dict]) -> dict:
    ids = [node["id"] for node in nodes]
    unique = set(ids)
    pairs = [(edge["source"], edge["target"]) for edge in edges]
    github = [node for node in nodes if node["id"].startswith("github:")]
    return {
        "duplicate_node_ids": len(ids) - len(unique),
        "duplicate_edge_pairs": len(pairs) - len(set(pairs)),
        "edges_with_missing_endpoints": sum(edge["source"] not in unique or edge["target"] not in unique for edge in edges),
        "github_open_issues": sum(node["type"] == "issue" and node.get("state") == "open" for node in github),
        "github_closed_issues": sum(node["type"] == "issue" and node.get("state") == "closed" for node in github),
        "github_open_prs": sum(node["type"] == "pull_request" and node.get("state") == "open" for node in github),
        "github_closed_prs": sum(node["type"] == "pull_request" and node.get("state") == "closed" for node in github),
        "missing_update_timestamps": sum(not node.get("updated_at") for node in nodes),
    }


def report(nodes: list[dict], links: list[dict], errors: dict[str, str], snapshot: str, total_openaire: int | None):
    counts = {kind: sum(node["type"] == kind for node in nodes) for kind in ("issue", "pull_request", "model", "dataset", "research_product")}
    explicit = [edge for edge in links if edge["status"] == "explicit_reference"]
    candidates = [edge for edge in links if edge["status"] == "candidate"]
    profile = quality_profile(nodes, links)
    lines = [
        "# OpenEuroLLM research graph – exploratory snapshot", "",
        f"Collected: `{snapshot}` (UTC). Source: public APIs, read-only.", "",
        "## Coverage", "",
        *[f"- {key}: **{value}** records" for key, value in counts.items()],
        f"- OpenAIRE keyword-search total (not project coverage): **{total_openaire if total_openaire is not None else 'unavailable'}**", "",
        f"- GitHub open issues / closed issues: **{profile['github_open_issues']} / {profile['github_closed_issues']}**",
        f"- GitHub open PRs / closed PRs: **{profile['github_open_prs']} / {profile['github_closed_prs']}**", "",
        "## Cross-platform evidence", "",
        f"- Explicit URL/ID mentions (not semantic proof): **{len(explicit)}**",
        f"- Name-only candidates, NOT confirmed: **{len(candidates)}**", "",
        "| GitHub task | Hugging Face resource | Evidence | Matched text |", "| --- | --- | --- | --- |",
    ]
    index = {node["id"]: node for node in nodes}
    for edge in (explicit + candidates)[:50]:
        source, target = index[edge["source"]], index[edge["target"]]
        evidence = edge["evidence"].replace("|", "\\|").replace("`", "'")[:120]
        lines.append(f"| [#{source['id'].rsplit('#', 1)[-1]}]({source['url']}) | [{target['title']}]({target['url']}) | {edge['evidence_type']} | `{evidence}` |")
    if not links:
        lines.append("| No observed cross-source references | – | – | – |")
    lines.extend(["", "## Automated quality checks", ""])
    for name, value in profile.items():
        lines.append(f"- {name.replace('_', ' ')}: **{value}**")
    lines.extend(["", "## Source errors / incomplete coverage", ""])
    lines.extend(f"- `{name}`: {message}" for name, message in errors.items())
    if not errors:
        lines.append("- No source errors encountered.")
    lines.extend(["", "## Interpretation", "", "This is a discovery probe, **not** a complete research knowledge graph. An explicit reference proves the artifact was mentioned, not that it was used, validated or scientifically related. Name-only candidates remain unverified. OpenAIRE keyword search is not an exhaustive count of project research products. Missing timestamps mean the source did not provide freshness metadata.", ""])
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
    profile = quality_profile(nodes, edges)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp_utc": snapshot, "nodes": nodes, "edges": edges, "errors": errors, "openaire_search_total": openaire_total, "quality": profile}
    (output / "snapshot.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "REPORT.md").write_text(report(nodes, edges, errors, snapshot, openaire_total), encoding="utf-8")
    print(f"Collected {len(nodes)} records, {len(edges)} potential links, {len(errors)} source errors")
    return 0 if nodes else 1


if __name__ == "__main__":
    sys.exit(main())
