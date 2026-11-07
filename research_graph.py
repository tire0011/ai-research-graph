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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


GITHUB_REPOS = ("OpenEuroLLM/Taskboard", "OpenEuroLLM/oellm-eval", "OpenEuroLLM/oellm-autoexp")
HF_ORG = "openeurollm"
UA = "ai-research-graph/0.1 (public metadata research probe)"
MAX_ARXIV_LOOKUPS = 12
ARXIV_PATTERN = re.compile(
    r"(?:arxiv\s*:\s*|arxiv\.org/(?:abs|pdf|html)/)(\d{4}\.\d{4,5})(?:v\d+)?(?![\d.])",
    re.IGNORECASE,
)
DOI_PATTERN = re.compile(r"(?<![a-z0-9])10\.\d{4,9}/[^\s\"<>\[\]{}|]+", re.IGNORECASE)


def identifiers_in(text: str) -> dict[str, list[str]]:
    """Extract explicit scholarly IDs only, without guessing from model names."""
    arxiv = {match.group(1) for match in ARXIV_PATTERN.finditer(text)}
    doi = set()
    for match in DOI_PATTERN.finditer(text):
        value = match.group().rstrip(".,;:!?)}'").casefold()
        if value:
            doi.add(value)
    return {"arxiv": sorted(arxiv), "doi": sorted(doi)}


def openaire_node(item: dict) -> dict:
    scholarly = {"arxiv": set(), "doi": set()}
    for pid in item.get("pids") or []:
        scheme = (pid.get("scheme") or "").casefold()
        if scheme in scholarly and pid.get("value"):
            scholarly[scheme].add(pid["value"].casefold().strip())
    for value in list(scholarly["doi"]):
        # This DOI format is specifically the arXiv mirror of a paper.
        match = re.fullmatch(r"10\.48550/arxiv\.(\d{4}\.\d{4,5})", value)
        if match:
            scholarly["arxiv"].add(match.group(1))
    ids = {scheme: sorted(values) for scheme, values in scholarly.items()}
    urls = [url for instance in item.get("instances") or [] for url in instance.get("urls") or [] if isinstance(url, str) and url.startswith("https://")]
    preferred = next((url for url in urls if "arxiv.org/abs/" in url), None)
    if not preferred and ids["doi"]:
        preferred = "https://doi.org/" + ids["doi"][0]
    return {
        "id": "openaire:" + str(item.get("id") or item.get("mainTitle")),
        "type": "research_product",
        "title": item.get("mainTitle") or "",
        "url": preferred or (urls[0] if urls else "https://explore.openaire.eu/"),
        "description": "",
        "identifiers": ids,
        "updated_at": None,
        "research_type": item.get("type"),
    }


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
                "identifiers": identifiers_in("\n".join((item.get("title") or "", item.get("body") or ""))),
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
        "identifiers": identifiers_in(json.dumps(item.get("cardData") or {}, ensure_ascii=False) + " " + " ".join(item.get("tags") or [])),
        "updated_at": item.get("lastModified"),
    } for item in data]


def openaire_products(search: str = "OpenEuroLLM"):
    query = urllib.parse.urlencode({"search": search, "page_size": 100})
    data = fetch_json(f"https://api.openaire.eu/graph/v4/research-products?{query}", timeout=25)
    return ([openaire_node(item) for item in data.get("results", [])], data.get("header", {}).get("numFound"))


def openaire_by_arxiv(arxiv_id: str) -> list[dict]:
    query = urllib.parse.urlencode({"filter": f"ids.arxiv:{arxiv_id}", "page_size": 5})
    data = fetch_json(f"https://api.openaire.eu/graph/v4/research-products?{query}", timeout=25)
    return [openaire_node(item) for item in data.get("results", [])]


def enrich_publications(nodes: list[dict], errors: dict[str, str], limit: int = MAX_ARXIV_LOOKUPS) -> list[dict]:
    """Resolve a bounded sample of GitHub citations; missing coverage stays explicit."""
    current = {value for node in nodes if node["type"] == "research_product" for value in node.get("identifiers", {}).get("arxiv", [])}
    candidates: dict[str, tuple[int, str]] = {}
    for node in nodes:
        if node["type"] not in ("issue", "pull_request"):
            continue
        for value in node.get("identifiers", {}).get("arxiv", []):
            if value not in current:
                # Open issues first; then latest updates. Deterministic selection.
                key = (1 if node.get("state") == "open" else 0, node.get("updated_at") or "")
                if value not in candidates or key > candidates[value]:
                    candidates[value] = key
    ordered = sorted(candidates, key=lambda value: (candidates[value][0], candidates[value][1], value), reverse=True)
    selected = ordered[:limit]
    if len(ordered) > len(selected):
        errors["OpenAIRE citation coverage"] = f"Sampled {len(selected)} of {len(ordered)} unmatched GitHub arXiv IDs (limit {limit}); not exhaustive"
    found = []
    if not selected:
        return found
    with ThreadPoolExecutor(max_workers=3) as executor:
        jobs = {executor.submit(openaire_by_arxiv, value): value for value in selected}
        for job in as_completed(jobs):
            value = jobs[job]
            try:
                found.extend(job.result())
            except (ValueError, urllib.error.URLError, TimeoutError) as exc:
                errors[f"OpenAIRE arXiv {value}"] = str(exc)
    return found


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


def scholarly_links(nodes: list[dict]) -> list[dict]:
    """Shared scholarly identifiers establish a reference, not scientific validity."""
    products = [node for node in nodes if node["type"] == "research_product"]
    consumers = [node for node in nodes if node["type"] in ("issue", "pull_request", "model", "dataset")]
    edges = []
    for source in consumers:
        ids = source.get("identifiers") or identifiers_in(source.get("description", "") + " " + source.get("title", ""))
        for target in products:
            target_ids = target.get("identifiers") or {}
            common = {
                scheme: sorted(set(ids.get(scheme, [])) & set(target_ids.get(scheme, [])))
                for scheme in ("arxiv", "doi")
            }
            match_type = next((scheme for scheme in ("arxiv", "doi") if common[scheme]), None)
            if not match_type:
                continue
            evidence = common[match_type][0]
            edges.append({
                "source": source["id"], "target": target["id"],
                "status": "identifier_match", "evidence_type": match_type,
                "evidence": evidence,
                "context": f"Both public metadata records contain {match_type}:{evidence}",
                "reason": "Shared persistent scholarly ID; not proof of usage, endorsement, or scientific dependence",
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
    scholarly = [edge for edge in links if edge["status"] == "identifier_match"]
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
        f"- Name-only candidates, NOT confirmed: **{len(candidates)}**",
        f"- Shared scholarly identifiers (arXiv/DOI): **{len(scholarly)}**", "",
        "| GitHub task | Hugging Face resource | Evidence | Matched text |", "| --- | --- | --- | --- |",
    ]
    index = {node["id"]: node for node in nodes}
    for edge in (explicit + candidates)[:50]:
        source, target = index[edge["source"]], index[edge["target"]]
        evidence = edge["evidence"].replace("|", "\\|").replace("`", "'")[:120]
        lines.append(f"| [#{source['id'].rsplit('#', 1)[-1]}]({source['url']}) | [{target['title']}]({target['url']}) | {edge['evidence_type']} | `{evidence}` |")
    if not explicit and not candidates:
        lines.append("| No observed cross-source references | – | – | – |")
    lines.extend(["", "## Scholarly identifier matches", "",
        "| Source artifact | OpenAIRE publication | Shared ID |", "| --- | --- | --- |"])
    for edge in scholarly[:50]:
        source, target = index[edge["source"]], index[edge["target"]]
        lines.append(f"| [{source['title'].replace('|', '\\|')}]({source['url']}) | [{target['title'].replace('|', '\\|')}]({target['url']}) | `{edge['evidence_type']}:{edge['evidence']}` |")
    if not scholarly:
        lines.append("| No shared identifiers observed | – | – |")
    lines.extend(["", "## Automated quality checks", ""])
    for name, value in profile.items():
        lines.append(f"- {name.replace('_', ' ')}: **{value}**")
    lines.extend(["", "## Source errors / incomplete coverage", ""])
    lines.extend(f"- `{name}`: {message}" for name, message in errors.items())
    if not errors:
        lines.append("- No source errors encountered.")
    lines.extend(["", "## Interpretation", "", "This is a discovery probe, **not** a complete research knowledge graph. A shared persistent identifier connects metadata records to the same publication; it does not establish that an implementation is correct or scientifically dependent on that publication. Explicit mentions are references only; name-only candidates remain unverified. OpenAIRE keyword search and bounded arXiv citation lookups are not an exhaustive count of project research. Missing timestamps mean the source did not provide freshness metadata.", ""])
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
        # OpenAIRE's keyword index is incomplete; resolve a small sample of explicit
        # arXiv citations from the GitHub issues using exact persistent identifiers.
        found = enrich_publications(nodes, errors)
        existing = {node["id"] for node in nodes}
        for product in found:
            if product["id"] not in existing:
                nodes.append(product)
                existing.add(product["id"])
    edges = links_between(nodes) + scholarly_links(nodes)
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
