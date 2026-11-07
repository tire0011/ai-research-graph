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
MAX_ARXIV_LOOKUPS = 80
MAX_ARXIV_BATCH_SIZE = 40  # OpenAIRE permits OR lists (up to 50 values per field).
MAX_EXTERNAL_HF_LOOKUPS = 40
ARXIV_PATTERN = re.compile(
    r"(?:arxiv\s*:\s*|arxiv\.org/(?:abs|pdf|html)/)(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?(?![a-z0-9.])",
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
        mirror = re.fullmatch(r"10\.48550/arxiv\.(\d{4}\.\d{4,5})", value)
        if mirror:
            arxiv.add(mirror.group(1))
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


def external_hf_asset(kind: str, repo_id: str) -> dict:
    """Confirm one publicly reachable Hub repo; the publisher's claims remain unverified."""
    if kind not in ("model", "dataset") or not re.fullmatch(r"[\w.-]+/[\w.-]+", repo_id):
        raise ValueError(f"Invalid HF reference: {kind}/{repo_id}")
    path = "models" if kind == "model" else "datasets"
    safe_id = "/".join(urllib.parse.quote(part, safe="") for part in repo_id.split("/"))
    data = fetch_json(f"https://huggingface.co/api/{path}/{safe_id}?full=true&cardData=true", timeout=30)
    canonical = data.get("id") if isinstance(data, dict) else None
    if not isinstance(canonical, str) or not re.fullmatch(r"[\w.-]+/[\w.-]+", canonical):
        raise ValueError(f"Hugging Face returned an invalid repository ID for {repo_id}: {canonical}")
    if data.get("private"):
        raise ValueError(f"Private repository was unexpectedly returned for {repo_id}")
    card = json.dumps(data.get("cardData") or {}, ensure_ascii=False)
    node = {
        "id": f"hf:{kind}:{canonical}", "type": kind, "title": canonical,
        "url": f"https://huggingface.co/{'datasets/' if kind == 'dataset' else ''}{canonical}",
        "description": card[:20000],
        "identifiers": identifiers_in(card + " " + " ".join(data.get("tags") or [])),
        "updated_at": data.get("lastModified"),
        "is_external": True, "verification": "api_confirmed_public_metadata",
    }
    if canonical.casefold() != repo_id.casefold():
        node["resolved_from_alias"] = repo_id
    return node


def openaire_products(search: str = "OpenEuroLLM"):
    query = urllib.parse.urlencode({"search": search, "page_size": 100})
    data = fetch_json(f"https://api.openaire.eu/graph/v4/research-products?{query}", timeout=25)
    return ([openaire_node(item) for item in data.get("results", [])], data.get("header", {}).get("numFound"))


def openaire_by_arxiv_batch(arxiv_ids: list[str]) -> list[dict]:
    """Look up multiple exact IDs in one OpenAIRE OR filter request."""
    if not arxiv_ids or len(arxiv_ids) > MAX_ARXIV_BATCH_SIZE:
        raise ValueError("Expected 1–40 arXiv IDs")
    query = urllib.parse.urlencode({"filter": "ids.arxiv:" + "|".join(arxiv_ids), "page_size": 100})
    data = fetch_json(f"https://api.openaire.eu/graph/v4/research-products?{query}", timeout=60)
    return [openaire_node(item) for item in data.get("results", [])]


def enrich_publications(nodes: list[dict], errors: dict[str, str], limit: int = MAX_ARXIV_LOOKUPS) -> list[dict]:
    """Resolve explicit GitHub/HF citations with small, bounded OR-filter batches."""
    current = {value for node in nodes if node["type"] == "research_product" for value in node.get("identifiers", {}).get("arxiv", [])}
    candidates: set[str] = set()
    for node in nodes:
        if node["type"] not in ("issue", "pull_request", "model", "dataset"):
            continue
        for value in node.get("identifiers", {}).get("arxiv", []):
            if value not in current:
                candidates.add(value)
    ordered = sorted(candidates)
    selected = ordered[:limit]
    if len(ordered) > len(selected):
        errors["OpenAIRE citation coverage"] = f"Queried {len(selected)} of {len(ordered)} unmatched GitHub/HF arXiv IDs (limit {limit})"
    found = []
    for index in range(0, len(selected), MAX_ARXIV_BATCH_SIZE):
        batch = selected[index:index + MAX_ARXIV_BATCH_SIZE]
        try:
            found.extend(openaire_by_arxiv_batch(batch))
        except (ValueError, urllib.error.URLError, TimeoutError) as exc:
            errors[f"OpenAIRE arXiv batch {index // MAX_ARXIV_BATCH_SIZE + 1}"] = f"IDs {', '.join(batch)}: {exc}"
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
            # Never create weak name-only matches for newly discovered external repos.
            slug_match = name_only_match(body, slug, owner) if len(slug) >= 9 and not asset.get("is_external") else None
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


def hf_card_declarations(nodes: list[dict], aliases: dict[tuple[str, str], str] | None = None) -> tuple[list[dict], list[dict]]:
    """Read only explicit HF model-card fields; do not guess training lineage."""
    assets = {(node["type"], node["title"].casefold()): node for node in nodes if node["type"] in ("model", "dataset")}
    edges, outside = [], []
    # Deliberately one hop only: do not recursively crawl the external models.
    for model in (node for node in nodes if node["type"] == "model" and not node.get("is_external")):
        try:
            card = json.loads(model.get("description") or "{}")
        except (ValueError, TypeError):
            continue
        if not isinstance(card, dict):
            continue
        for field, target_kind in (("base_model", "model"), ("datasets", "dataset")):
            values = card.get(field) or []
            if isinstance(values, str):
                values = [values]
            if not isinstance(values, list):
                continue
            seen = set()
            for raw_value in values:
                if not isinstance(raw_value, str):
                    continue
                reference = raw_value.strip()
                # Model-card fields normally contain 'namespace/repo' IDs.
                if not re.fullmatch(r"[\w.-]+/[\w.-]+", reference) or reference.casefold() in seen:
                    continue
                seen.add(reference.casefold())
                target = assets.get((target_kind, reference.casefold()))
                resolved_alias = (aliases or {}).get((target_kind, reference.casefold())) if not target else None
                if resolved_alias:
                    target = assets.get((target_kind, resolved_alias.casefold()))
                if target and target["id"] != model["id"]:
                    edges.append({
                        "source": model["id"], "target": target["id"],
                        "status": "declared_metadata_redirect" if resolved_alias else "declared_metadata",
                        "evidence_type": field,
                        "evidence": reference,
                        "context": f"Hugging Face model-card field {field}: {reference}",
                        "reason": "HF API resolves the declared ID to a canonical repository; lineage not independently verified" if resolved_alias else
                                  "Source card declares a resource; independent lineage verification not performed",
                        **({"canonical_id": target["title"]} if resolved_alias else {}),
                    })
                elif not target:
                    outside.append({
                        "source": model["id"], "target_type": target_kind,
                        "declared_id": reference, "evidence_type": field,
                        "target_url": f"https://huggingface.co/{'datasets/' if target_kind == 'dataset' else ''}{reference}",
                        "verification": "not_fetched_outside_indexed_inventory",
                    })
    return edges, outside


def verify_external_hf_references(references: list[dict], limit: int = MAX_EXTERNAL_HF_LOOKUPS) -> tuple[list[dict], list[dict]]:
    """Resolve only one-hop card references, bounded and without credentials."""
    unique = {(ref["target_type"], ref["declared_id"].casefold()): ref["declared_id"] for ref in references}
    ordered = sorted(unique)
    checks = []
    confirmed = []
    for kind, folded_id in ordered[limit:]:
        checks.append({"target_type": kind, "declared_id": unique[(kind, folded_id)], "status": "not_checked_limit"})
    selected = ordered[:limit]
    if not selected:
        return confirmed, checks
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(external_hf_asset, kind, unique[(kind, folded_id)]): (kind, folded_id) for kind, folded_id in selected}
        for job in as_completed(jobs):
            kind, folded_id = jobs[job]
            repo_id = unique[(kind, folded_id)]
            check = {"target_type": kind, "declared_id": repo_id}
            try:
                node = job.result()
                confirmed.append(node)
                status = "verified_redirect" if node.get("resolved_from_alias") else "verified_public"
                check.update({"status": status, "node_id": node["id"]})
                if status == "verified_redirect":
                    check["canonical_id"] = node["title"]
            except urllib.error.HTTPError as exc:
                check.update({"status": "not_publicly_found" if exc.code == 404 else
                              "inaccessible" if exc.code in (401, 403) else
                              "rate_limited" if exc.code == 429 else "http_error", "http_status": exc.code})
            except (ValueError, urllib.error.URLError, TimeoutError) as exc:
                check.update({"status": "fetch_failed", "error": str(exc)[:160]})
            checks.append(check)
    return confirmed, sorted(checks, key=lambda check: (check["target_type"], check["declared_id"].casefold()))


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


def citation_coverage(nodes: list[dict], edges: list[dict]) -> dict:
    """Coverage among explicitly cited IDs, not recall against all research."""
    referenced: set[str] = set()
    published: set[str] = set()
    source_types = ("issue", "pull_request", "model", "dataset")
    by_type = {}
    linked = {edge["source"] for edge in edges if edge["status"] == "identifier_match"}
    for kind in source_types:
        items = [node for node in nodes if node["type"] == kind]
        cited = [node for node in items if any((node.get("identifiers") or {}).values())]
        by_type[kind] = {"records": len(items), "with_identifier": len(cited),
                         "linked_to_openaire": sum(node["id"] in linked for node in cited)}
        for node in cited:
            referenced.update((node.get("identifiers") or {}).get("arxiv", []))
    for node in nodes:
        if node["type"] == "research_product":
            published.update((node.get("identifiers") or {}).get("arxiv", []))
    per_paper: dict[str, set[str]] = {}
    kind_by_id = {node["id"]: node["type"] for node in nodes}
    for edge in edges:
        if edge["status"] == "identifier_match":
            group = "github" if kind_by_id[edge["source"]] in ("issue", "pull_request") else "hf"
            per_paper.setdefault(edge["target"], set()).add(group)
    return {
        "referenced_unique_arxiv_ids": len(referenced),
        "resolved_unique_arxiv_ids": len(referenced & published),
        "unresolved_arxiv_ids": sorted(referenced - published),
        "by_source_type": by_type,
        "publications_bridging_github_and_hf": sum(groups == {"github", "hf"} for groups in per_paper.values()),
    }


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


def report(nodes: list[dict], links: list[dict], errors: dict[str, str], snapshot: str,
           total_openaire: int | None, external_checks: list[dict] | None = None):
    counts = {kind: sum(node["type"] == kind for node in nodes) for kind in ("issue", "pull_request", "model", "dataset", "research_product")}
    explicit = [edge for edge in links if edge["status"] == "explicit_reference"]
    candidates = [edge for edge in links if edge["status"] == "candidate"]
    scholarly = [edge for edge in links if edge["status"] == "identifier_match"]
    declared = [edge for edge in links if edge["status"] in ("declared_metadata", "declared_metadata_redirect")]
    resolved_aliases = {
        (check["target_type"], check["declared_id"].casefold()): check["canonical_id"]
        for check in (external_checks or []) if check["status"] == "verified_redirect"
    }
    _, outside_cards = hf_card_declarations(nodes, aliases=resolved_aliases)
    verified_external = [node for node in nodes if node.get("is_external")]
    declared_in_org = [edge for edge in declared if edge["status"] != "declared_metadata_redirect" and
                       not next(node for node in nodes if node["id"] == edge["target"]).get("is_external")]
    declared_verified = len(declared) - len(declared_in_org)
    profile = quality_profile(nodes, links)
    coverage = citation_coverage(nodes, links)
    lines = [
        "# OpenEuroLLM research graph – exploratory snapshot", "",
        f"Collected: `{snapshot}` (UTC). Source: public APIs, read-only.", "",
        "## Coverage", "",
        *[f"- {key}: **{value}** records" for key, value in counts.items()],
        f"- Of HF models/datasets, publicly verified one-hop targets outside the initial inventory: **{len(verified_external)}**",
        f"- OpenAIRE keyword-search total (not project coverage): **{total_openaire if total_openaire is not None else 'unavailable'}**", "",
        f"- GitHub open issues / closed issues: **{profile['github_open_issues']} / {profile['github_closed_issues']}**",
        f"- GitHub open PRs / closed PRs: **{profile['github_open_prs']} / {profile['github_closed_prs']}**", "",
        "## Evidenced relationships", "",
        f"- Explicit URL/ID mentions (not semantic proof): **{len(explicit)}**",
        f"- Name-only candidates, NOT confirmed: **{len(candidates)}**",
        f"- Shared scholarly identifiers (arXiv/DOI): **{len(scholarly)}**",
        f"- HF model-card declarations to indexed/verified targets: **{len(declared)}**", "",
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
    for edge in scholarly[:100]:
        source, target = index[edge["source"]], index[edge["target"]]
        lines.append(f"| [{source['title'].replace('|', '\\|')}]({source['url']}) | [{target['title'].replace('|', '\\|')}]({target['url']}) | `{edge['evidence_type']}:{edge['evidence']}` |")
    if not scholarly:
        lines.append("| No shared identifiers observed | – | – |")
    if len(scholarly) > 100:
        lines.append(f"\nShowing the first 100 of {len(scholarly)} scholarly edges; all are in snapshot.json.")
    lines.extend(["", "## Hugging Face card declarations", "",
        "These are explicit **metadata claims** made by model publishers; model ancestry and dataset usage have not been independently reproduced.", "",
        f"- Declared links inside initial HF inventory: **{len(declared_in_org)}**",
        f"- Declared links to API-verified one-hop targets: **{declared_verified}**",
        f"- Of these, links resolved through verified HF canonical IDs: **{sum(edge['status'] == 'declared_metadata_redirect' for edge in declared)}**",
        f"- Declared references still unresolved in this graph: **{len(outside_cards)}**", "",
        "| HF model | Declared field | Referenced asset |", "| --- | --- | --- |"])
    for edge in declared[:100]:
        source, target = index[edge["source"]], index[edge["target"]]
        lines.append(f"| [{source['title']}]({source['url']}) | `{edge['evidence_type']}` | [{target['title']}]({target['url']}) |")
    if not declared:
        lines.append("| No in-org declarations found | – | – |")
    if external_checks is not None:
        stats = {status: sum(check["status"] == status for check in external_checks)
                 for status in ("verified_public", "verified_redirect", "not_publicly_found", "inaccessible", "rate_limited", "http_error", "fetch_failed", "not_checked_limit")}
        lines.extend(["", "### Verification of one-hop Hugging Face targets", "",
            f"Distinct referenced target IDs checked/recorded: **{len(external_checks)}**",
            *[f"- {status.replace('_', ' ')}: **{count}**" for status, count in stats.items() if count],
            "", "Verified means the public HF API returned that repository, **not** that its model-card lineage claim has been independently reproduced. HTTP 404 means *not publicly found*, which may include private or removed repositories."])
        redirects = [check for check in external_checks if check["status"] == "verified_redirect"]
        if redirects:
            lines.extend(["", "| Declared ID | Canonical ID returned by HF API |", "| --- | --- |"])
            for check in redirects:
                lines.append(f"| `{check['declared_id']}` | `{check['canonical_id']}` |")
        unresolved = [check for check in external_checks if check["status"] not in ("verified_public", "verified_redirect")]
        if unresolved:
            lines.extend(["", "| Unverified target | Result |", "| --- | --- |"])
            for check in unresolved[:25]:
                lines.append(f"| `{check['declared_id']}` ({check['target_type']}) | {check['status']} |")
    bridges = []
    for paper in (node for node in nodes if node["type"] == "research_product"):
        incoming = [edge for edge in scholarly if edge["target"] == paper["id"]]
        gh = next((index[edge["source"]] for edge in incoming if index[edge["source"]]["type"] in ("issue", "pull_request")), None)
        hf = next((index[edge["source"]] for edge in incoming if index[edge["source"]]["type"] in ("model", "dataset")), None)
        if gh and hf:
            bridges.append((gh, paper, hf))
    lines.extend(["", "## Three-platform publication bridges", "",
        "These are shared citations, **not** proof of direct model/task dependence.", "",
        "| GitHub task | Referenced publication | Hugging Face artifact |", "| --- | --- | --- |"])
    for gh, paper, hf in bridges[:20]:
        lines.append(f"| [{gh['title'].replace('|', '\\|')}]({gh['url']}) | [{paper['title'].replace('|', '\\|')}]({paper['url']}) | [{hf['title'].replace('|', '\\|')}]({hf['url']}) |")
    if not bridges:
        lines.append("| No shared publication observed | – | – |")
    lines.extend(["", "## Citation lookup completeness", "",
        f"- Unique arXiv IDs explicitly cited by GitHub/HF: **{coverage['referenced_unique_arxiv_ids']}**",
        f"- Resolved to OpenAIRE records: **{coverage['resolved_unique_arxiv_ids']}**",
        f"- Not resolved by OpenAIRE responses: **{len(coverage['unresolved_arxiv_ids'])}**",
        f"- Publications cited by both GitHub and Hugging Face: **{coverage['publications_bridging_github_and_hf']}**", "",
        "| Source type | Records | With DOI/arXiv ID | Linked to OpenAIRE |",
        "| --- | ---: | ---: | ---: |"])
    for kind, metrics in coverage["by_source_type"].items():
        lines.append(f"| {kind} | {metrics['records']} | {metrics['with_identifier']} | {metrics['linked_to_openaire']} |")
    if coverage["unresolved_arxiv_ids"]:
        lines.extend(["", "Unresolved cited arXiv IDs (missing from this OpenAIRE response, **not** necessarily unpublished): " +
            ", ".join(f"[{value}](https://arxiv.org/abs/{value})" for value in coverage["unresolved_arxiv_ids"])])
    if errors:
        lines.append("\nCoverage may also be limited by API errors listed below.")
    lines.extend(["", "## Automated quality checks", ""])
    for name, value in profile.items():
        lines.append(f"- {name.replace('_', ' ')}: **{value}**")
    lines.extend(["", "## Source errors / incomplete coverage", ""])
    lines.extend(f"- `{name}`: {message}" for name, message in errors.items())
    if not errors:
        lines.append("- No source errors encountered.")
    lines.extend(["", "## Interpretation", "", "This is a discovery probe, **not** a complete research knowledge graph. A shared persistent identifier connects metadata records to the same publication; it does not establish that an implementation is correct or scientifically dependent on that publication. Hugging Face `base_model` and `datasets` fields are publisher-declared metadata, not independently reproduced lineage. Explicit mentions are references only; name-only candidates remain unverified. OpenAIRE keyword search and bounded arXiv citation lookups are not an exhaustive count of project research. Unresolved citation IDs are not evidence that a publication does not exist. Missing timestamps mean the source did not provide freshness metadata.", ""])
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
    external_checks: list[dict] | None = None
    external_card_refs: list[dict] = []
    if args.fixture:
        fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        nodes = fixture["nodes"]
        external_checks = fixture.get("external_hf_target_checks")
        external_card_refs = fixture.get("external_hf_card_references") or hf_card_declarations(nodes)[1]
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
        _, external_card_refs = hf_card_declarations(nodes)
        verified, external_checks = verify_external_hf_references(external_card_refs)
        existing_hf = {node["id"].casefold() for node in nodes}
        for verified_node in verified:
            if verified_node["id"].casefold() not in existing_hf:
                nodes.append(verified_node)
                existing_hf.add(verified_node["id"].casefold())
        failed_targets = [check for check in external_checks if check["status"] in
                          ("rate_limited", "http_error", "fetch_failed", "not_checked_limit")]
        if failed_targets:
            errors["Hugging Face external lookup"] = f"{len(failed_targets)} target(s) not completely checked; see external_hf_target_checks"
        try:
            products, openaire_total = openaire_products()
            nodes.extend(products)
        except (ValueError, urllib.error.URLError, TimeoutError) as exc:
            errors["OpenAIRE"] = str(exc)
        # OpenAIRE's keyword index is incomplete; batch-resolve cited arXiv IDs
        # across GitHub and Hugging Face using exact persistent identifiers.
        found = enrich_publications(nodes, errors)
        existing = {node["id"] for node in nodes}
        for product in found:
            if product["id"] not in existing:
                nodes.append(product)
                existing.add(product["id"])
    aliases = {
        (check["target_type"], check["declared_id"].casefold()): check["canonical_id"]
        for check in (external_checks or []) if check["status"] == "verified_redirect"
    }
    internal_card_edges, _ = hf_card_declarations(nodes, aliases=aliases)
    if external_checks is not None:
        by_target = {(check["target_type"], check["declared_id"].casefold()): check for check in external_checks}
        for reference in external_card_refs:
            check = by_target.get((reference["target_type"], reference["declared_id"].casefold()))
            if check:
                reference["verification"] = check["status"]
                if check.get("node_id"):
                    reference["verified_node_id"] = check["node_id"]
                if check.get("canonical_id"):
                    reference["canonical_id"] = check["canonical_id"]
    edges = links_between(nodes) + scholarly_links(nodes) + internal_card_edges
    profile = quality_profile(nodes, edges)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp_utc": snapshot, "nodes": nodes, "edges": edges,
               "external_hf_card_references": external_card_refs,
               "external_hf_target_checks": external_checks,
               "errors": errors, "openaire_search_total": openaire_total,
               "quality": profile, "citation_coverage": citation_coverage(nodes, edges)}
    (output / "snapshot.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "REPORT.md").write_text(report(nodes, edges, errors, snapshot, openaire_total, external_checks), encoding="utf-8")
    print(f"Collected {len(nodes)} records, {len(edges)} evidenced/candidate edges, {len(errors)} source errors")
    return 0 if nodes else 1


if __name__ == "__main__":
    sys.exit(main())
