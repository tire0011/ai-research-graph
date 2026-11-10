"""Read-only cross-platform research metadata probe (stdlib only)."""

from __future__ import annotations

import argparse
import base64
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

from impact_enrichment import github_comments_for_selected, selected_issue_ids, source_claim_edges


GITHUB_REPOS = ("OpenEuroLLM/Taskboard", "OpenEuroLLM/oellm-eval", "OpenEuroLLM/oellm-autoexp")
GITHUB_DATA_REPO = "OpenEuroLLM/training-data-collection"
HF_ORG = "openeurollm"
UA = "ai-research-graph/0.1 (public metadata research probe)"
MAX_ARXIV_LOOKUPS = 80
MAX_ARXIV_BATCH_SIZE = 40  # OpenAIRE permits OR lists (up to 50 values per field).
MAX_EXTERNAL_HF_LOOKUPS = 40
MAX_GITHUB_METADATA_FILES = 32  # Bounded pilot, not a full code search.
MAX_GITHUB_DATASET_CHECKS = 12
MAX_GITHUB_METADATA_BYTES = 100_000
HF_DATASET_URL_PATTERN = re.compile(
    r"https://huggingface\.co/datasets/([\w.-]+/[\w.-]+)(?=$|[/?#\s\"'<>])",
    re.IGNORECASE,
)
WANDB_RUN_URL_PATTERN = re.compile(
    r"https://wandb\.ai/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)/runs/([a-zA-Z0-9_-]{6,32})"
    r"(?=$|[/?#\s\"'<>\]\),;])",
    re.IGNORECASE,
)
GITHUB_TASK_URL_PATTERN = re.compile(
    r"https://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)/(issues|pull)/([1-9]\d*)"
    r"(?=$|[/?#\s\"'<>,;:.\]\)])", re.IGNORECASE,
)
GITHUB_QUALIFIED_TASK_PATTERN = re.compile(
    r"(?<![\w./-])([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)#([1-9]\d*)(?![\w-])"
)
GITHUB_LOCAL_TASK_PATTERN = re.compile(r"(?<![\w/#])#([1-9]\d*)(?![\w-])")
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
    if max_pages < 1:
        raise ValueError("max_pages must be positive")
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
    else:
        raise ValueError(f"GitHub issues for {repo} hit the {max_pages}-page cap; refusing incomplete inventory")
    return issues


def dataset_urls_in_source(content: str) -> list[dict]:
    """Exact public HF dataset URLs only; no slug or implied training inference."""
    matches = []
    seen = set()
    for match in HF_DATASET_URL_PATTERN.finditer(content):
        repo_id = match.group(1)
        if repo_id.casefold() in seen:
            continue
        seen.add(repo_id.casefold())
        matches.append({
            "declared_id": repo_id, "evidence": match.group(0),
            "context": content[content.rfind("\n", 0, match.start()) + 1:
                               content.find("\n", match.end()) if "\n" in content[match.end():] else len(content)].strip()[:300],
        })
    return matches


def github_metadata_inventory(repo: str, *, token: str | None = None,
                              max_files: int = MAX_GITHUB_METADATA_FILES) -> tuple[list[dict], list[dict], list[dict], dict]:
    """Inspect a bounded set of version-pinned YAML manifests and adjacent script paths."""
    details = fetch_json(f"https://api.github.com/repos/{repo}", token=token)
    branch = details["default_branch"]
    commit = fetch_json(f"https://api.github.com/repos/{repo}/commits/{urllib.parse.quote(branch, safe='')}", token=token)
    commit_sha = commit["sha"]
    tree_sha = commit["commit"]["tree"]["sha"]
    tree_data = fetch_json(f"https://api.github.com/repos/{repo}/git/trees/{tree_sha}?recursive=1", token=token)
    if tree_data.get("truncated"):
        raise ValueError(f"Git tree for {repo} was truncated: cannot safely select metadata files")
    entries = {item["path"]: item for item in tree_data["tree"] if item.get("type") == "blob"}
    candidates = [path for path in entries if re.fullmatch(r"flag/[^/]+/metadata\.ya?ml", path)]
    # Keep the running case visible while sampling other manifests deterministically.
    ordered = sorted(candidates, key=lambda path: ("/openthoughts-3/" not in path, path))
    selected = ordered[:max_files]
    nodes, references, colocated = [], [], []
    seen_scripts = set()
    for path in selected:
        if entries[path].get("size", MAX_GITHUB_METADATA_BYTES + 1) > MAX_GITHUB_METADATA_BYTES:
            continue
        url = f"https://api.github.com/repos/{repo}/contents/{urllib.parse.quote(path, safe='/')}?ref={commit_sha}"
        data = fetch_json(url, token=token)
        if data.get("encoding") != "base64" or not isinstance(data.get("content"), str):
            raise ValueError(f"Unexpected GitHub contents response for {repo}/{path}")
        source = base64.b64decode(data["content"], validate=False).decode("utf-8")
        hits = dataset_urls_in_source(source)
        if not hits:
            continue
        source_id = f"github_file:{repo}/{path}"
        nodes.append({
            "id": source_id, "type": "source_file", "title": path,
            "url": f"https://github.com/{repo}/blob/{commit_sha}/{path}",
            "repository": repo, "commit_sha": commit_sha, "blob_sha": entries[path]["sha"],
            "description": "GitHub YAML manifest with explicit dataset URL; not proof of training use",
            "updated_at": None,
        })
        for hit in hits:
            references.append({"source": source_id, "target_type": "dataset", **hit})
        directory = path.rsplit("/", 1)[0]
        for suffix in ("etc/textify.py", "etc/textify.slurm"):
            script_path = f"{directory}/{suffix}"
            if script_path not in entries:
                continue
            script_id = f"github_file:{repo}/{script_path}"
            if script_id in seen_scripts:
                continue
            seen_scripts.add(script_id)
            nodes.append({
                "id": script_id, "type": "processing_script", "title": script_path,
                "url": f"https://github.com/{repo}/blob/{commit_sha}/{script_path}",
                "repository": repo, "commit_sha": commit_sha, "blob_sha": entries[script_path]["sha"],
                "description": "Processing script found in the same directory; execution not verified",
                "updated_at": None,
            })
            colocated.append({
                "source": script_id, "target": source_id,
                "status": "co_located_source_code", "relationship": "located_in_dataset_directory",
                "evidence_type": "repository_path", "evidence": script_path,
                "context": f"Version-pinned path alongside {path}",
                "reason": "Co-location only; no claim this script executed or produced a training artifact",
            })
    statistics = {"repository": repo, "commit_sha": commit_sha, "candidate_manifests": len(candidates),
                  "selected_manifests": len(selected), "manifests_with_dataset_url":
                  sum(node["type"] == "source_file" for node in nodes),
                  "sample_limited": len(candidates) > len(selected),
                  "skipped_oversized": sum(entries[path].get("size", MAX_GITHUB_METADATA_BYTES + 1) > MAX_GITHUB_METADATA_BYTES for path in selected)}
    return nodes, references, colocated, statistics


def resolve_github_dataset_declarations(nodes: list[dict], references: list[dict],
                                        limit: int = MAX_GITHUB_DATASET_CHECKS) -> tuple[list[dict], list[dict], list[dict]]:
    """Verify external dataset identities; keep unverified declarations distinct."""
    known = {node["title"].casefold(): node for node in nodes if node["type"] == "dataset"}
    additions, checks, edges = [], [], []
    checked = {}
    for ref in references:
        repo_id = ref["declared_id"]
        key = repo_id.casefold()
        if key not in known and key not in checked:
            if len(checked) >= limit:
                checked[key] = {"status": "not_checked_limit"}
            else:
                try:
                    verified = external_hf_asset("dataset", repo_id)
                    if verified["title"].casefold() not in known:
                        additions.append(verified)
                        known[verified["title"].casefold()] = verified
                    checked[key] = {"status": "verified_public", "canonical_id": verified["title"]}
                except urllib.error.HTTPError as exc:
                    checked[key] = {"status": "not_publicly_found" if exc.code == 404 else
                                    "inaccessible" if exc.code in (401, 403) else
                                    "rate_limited" if exc.code == 429 else "http_error", "http_status": exc.code}
                except (ValueError, urllib.error.URLError, TimeoutError) as exc:
                    checked[key] = {"status": "fetch_failed", "error": str(exc)[:160]}
        check = checked[key] if key in checked else {"status": "indexed", "canonical_id": known[key]["title"]}
        checks.append({"source": ref["source"], "declared_id": repo_id, **check})
        resolved_id = check.get("canonical_id", repo_id).casefold()
        target = known.get(resolved_id)
        if target:
            edges.append({
                "source": ref["source"], "target": target["id"],
                "status": "declared_source_file", "relationship": "declares_dataset",
                "evidence_type": "dataset_url", "evidence": ref["evidence"],
                "context": ref["context"], "reason": "Dataset URL declared in versioned source code; not proof of model training",
                "target_verification": check["status"],
            })
    return additions, checks, edges


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


def github_task_references(nodes: list[dict]) -> tuple[list[dict], list[dict]]:
    """Resolve literal GitHub task references within the indexed task inventory.

    A reference is evidence of a *mention*, not a dependency or completed work.
    Unindexed targets remain diagnostics, never dangling graph edges.
    """
    tasks = {node["id"].casefold(): node for node in nodes
             if node.get("type") in ("issue", "pull_request") and node["id"].startswith("github:")}
    edges, unresolved = [], []
    seen = set()
    for source in tasks.values():
        repository = source.get("repository") or source["id"][len("github:"):].rsplit("#", 1)[0]
        body = source.get("title", "") + "\n" + (source.get("description") or "")
        claims = []
        occupied = []
        for match in GITHUB_TASK_URL_PATTERN.finditer(body):
            owner, repo, kind, number = match.groups()
            claims.append((match, f"{owner}/{repo}", number, f"github_{kind}_url"))
            occupied.append(match.span())
        for match in GITHUB_QUALIFIED_TASK_PATTERN.finditer(body):
            if any(start <= match.start() < end for start, end in occupied):
                continue
            owner, repo, number = match.groups()
            claims.append((match, f"{owner}/{repo}", number, "repository_issue_number"))
            occupied.append(match.span())
        for match in GITHUB_LOCAL_TASK_PATTERN.finditer(body):
            if any(start <= match.start() < end for start, end in occupied):
                continue
            claims.append((match, repository, match.group(1), "same_repo_issue_number"))
        for match, target_repo, number, evidence_type in sorted(claims, key=lambda row: row[0].start()):
            target_id = f"github:{target_repo}#{number}"
            pair = (source["id"].casefold(), target_id.casefold())
            if pair in seen or pair[0] == pair[1]:
                continue
            seen.add(pair)
            reference = {
                "source": source["id"], "reference": match.group(),
                "expected_target": target_id, "evidence_type": evidence_type,
                "context": matching_context(body, match),
            }
            target = tasks.get(target_id.casefold())
            if target is None:
                unresolved.append({**reference, "reason": "target_not_indexed"})
                continue
            edges.append({
                "source": source["id"], "target": target["id"],
                "status": "explicit_task_reference", "relationship": "references_task",
                "evidence_type": evidence_type, "evidence": match.group(),
                "context": reference["context"],
                "reason": "Literal GitHub task mention; not a dependency, implementation, or validation claim",
            })
    return edges, unresolved


def linked_experiment_runs(nodes: list[dict]) -> tuple[list[dict], list[dict]]:
    """Extract concrete W&B run links; do not treat project dashboards as runs."""
    known = {node["id"] for node in nodes}
    added, edges = [], []
    seen_edges = set()
    for source in nodes:
        if source["type"] not in ("issue", "pull_request"):
            continue
        body = source.get("title", "") + "\n" + source.get("description", "")
        for match in WANDB_RUN_URL_PATTERN.finditer(body):
            entity, project, run_id = match.groups()
            uri = f"https://wandb.ai/{entity}/{project}/runs/{run_id}"
            target_id = f"wandb_run:{entity.casefold()}/{project.casefold()}/{run_id.casefold()}"
            pair = (source["id"], target_id)
            if pair in seen_edges:
                continue
            seen_edges.add(pair)
            if target_id not in known:
                added.append({
                    "id": target_id, "type": "experiment_run_ref", "title": f"{project}/{run_id}",
                    "url": uri, "description": "Run URL asserted by GitHub issue; public access and metrics not independently verified",
                    "verification": "source_link_only", "updated_at": None,
                })
                known.add(target_id)
            edges.append({
                "source": source["id"], "target": target_id, "status": "explicit_run_reference",
                "relationship": "links_experiment_run", "evidence_type": "wandb_run_url",
                "evidence": uri, "context": matching_context(body, match),
                "reason": "GitHub task directly links one W&B run; run accessibility and numeric claims not independently verified",
            })
    return added, edges


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
    # A task may legitimately both mention another task and explicitly declare
    # a dependency on it. Deduplicate typed relationships, not bare endpoints.
    pairs = [(edge["source"], edge["target"], edge.get("status")) for edge in edges]
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
           total_openaire: int | None, external_checks: list[dict] | None = None,
           code_scan: dict | None = None, code_checks: list[dict] | None = None,
           unresolved_task_references: list[dict] | None = None,
           comment_collection: dict | None = None):
    counts = {kind: sum(node["type"] == kind for node in nodes) for kind in
              ("issue", "pull_request", "model", "dataset", "research_product", "source_file", "processing_script", "experiment_run_ref")}
    explicit = [edge for edge in links if edge["status"] == "explicit_reference"]
    candidates = [edge for edge in links if edge["status"] == "candidate"]
    scholarly = [edge for edge in links if edge["status"] == "identifier_match"]
    declared = [edge for edge in links if edge["status"] in ("declared_metadata", "declared_metadata_redirect")]
    source_declarations = [edge for edge in links if edge["status"] == "declared_source_file"]
    colocated_scripts = [edge for edge in links if edge["status"] == "co_located_source_code"]
    run_references = [edge for edge in links if edge["status"] == "explicit_run_reference"]
    task_references = [edge for edge in links if edge["status"] == "explicit_task_reference"]
    declared_dependencies = [edge for edge in links if edge["status"] == "author_declared_dependency"]
    reported_blockers = [edge for edge in links if edge["status"] == "reported_blocker"]
    comment_records = [node for node in nodes if node["type"] == "issue_comment"]
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
        f"- GitHub YAML manifest declarations to indexed/verified datasets: **{len(source_declarations)}**",
        f"- Processing script paths co-located with those manifests: **{len(colocated_scripts)}**", "",
        f"- Concrete W&B run URLs in GitHub tasks (source links only): **{len(run_references)}**", "",
        f"- Literal GitHub issue/PR cross-references to indexed tasks: **{len(task_references)}**",
        f"- GitHub issue/PR references without an indexed target: **{len(unresolved_task_references or [])}**", "",
        f"- Public comments on selected issues, individually source-hashed: **{len(comment_records)}**",
        f"- Explicitly author-declared task dependencies: **{len(declared_dependencies)}**",
        f"- Commenter-reported OOM failure statements: **{len(reported_blockers)}**", "",
        "GitHub task links are **textual mentions only**; they do not prove a dependency, completed implementation, or validated experiment.", "",
        "| GitHub task | Hugging Face resource | Evidence | Matched text |", "| --- | --- | --- | --- |",
    ]
    index = {node["id"]: node for node in nodes}
    for edge in (explicit + candidates)[:50]:
        source, target = index[edge["source"]], index[edge["target"]]
        evidence = edge["evidence"].replace("|", "\\|").replace("`", "'")[:120]
        lines.append(f"| [#{source['id'].rsplit('#', 1)[-1]}]({source['url']}) | [{target['title']}]({target['url']}) | {edge['evidence_type']} | `{evidence}` |")
    if not explicit and not candidates:
        lines.append("| No observed cross-source references | – | – | – |")
    lines.extend(["", "## GitHub issue / pull request references", "",
                  "Only exact issue numbers and GitHub task URLs count; every target is present in the indexed snapshot.", "",
                  "| Referencing task | Mentioned task | Literal text |", "| --- | --- | --- |"])
    for edge in task_references[:70]:
        source, target = index[edge["source"]], index[edge["target"]]
        evidence = edge["evidence"].replace("|", "\\|").replace("`", "'")
        lines.append(f"| [{source['id']}]({source['url']}) | [{target['id']}]({target['url']}) | `{evidence}` |")
    if not task_references:
        lines.append("| No in-snapshot references observed | – | – |")
    if len(task_references) > 70:
        lines.append(f"\nShowing the first 70 of {len(task_references)} task links; all are in snapshot.json.")
    lines.extend(["", "## Scoped GitHub comment and dependency evidence", "",
                  "Comments are collected only for the ten preselected change-impact issues, not all GitHub tasks. "
                  "Each comment is a separate node with a public URL, original text, update timestamp and SHA256. "
                  "A labeled Dependencies section is an **author declaration**, not verified causal blocking. "
                  "An OOM comment is a **report of failure**, not a reproduced failure or a quantified speedup.", ""])
    if comment_collection:
        lines.append(f"- Comment collection: `{comment_collection.get('status', 'unknown')}`; "
                     f"selected issues: **{comment_collection.get('selected_issues', 'unavailable')}**.\n")
    for edge in declared_dependencies[:20]:
        lines.append(f"- Declared dependency: [{edge['source']}]({edge['source_url']}) → "
                     f"[{edge['target']}]({index[edge['target']]['url']}) "
                     f"(`{edge['evidence_type']}`).")
    for edge in reported_blockers[:20]:
        lines.append(f"- Reported failure: [original comment]({edge['source_url']}) on "
                     f"[{edge['target']}]({index[edge['target']]['url']}) "
                     f"(`{edge['evidence']}`).")
    if not declared_dependencies and not reported_blockers:
        lines.append("- No supported dependency or OOM claim in the bounded source inventory.")
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
    lines.extend(["", "## GitHub dataset source declarations", "",
                  "Manifest declarations are version-pinned source-code evidence, **not** proof of actual training, data inclusion or completed evaluation. Co-located script paths are not proof of script execution.", ""])
    if code_scan:
        lines.extend([
            f"- Scanned repository: [{code_scan['repository']}](https://github.com/{code_scan['repository']}/tree/{code_scan['commit_sha']})",
            f"- Selected manifests: **{code_scan['selected_manifests']}** of **{code_scan['candidate_manifests']}** candidates (bounded sample)",
            f"- Manifests with explicit HF dataset URLs: **{code_scan['manifests_with_dataset_url']}**",
            f"- Manifests skipped due to size limit: **{code_scan['skipped_oversized']}**",
            f"- Selection was truncated: **{str(code_scan['sample_limited']).lower()}**", "",
        ])
    lines.extend(["| GitHub source manifest | Public HF dataset | Evidence |", "| --- | --- | --- |"])
    for edge in source_declarations[:40]:
        source, target = index[edge["source"]], index[edge["target"]]
        lines.append(f"| [{source['title']}]({source['url']}) | [{target['title']}]({target['url']}) | `{edge['relationship']}` (`{edge['target_verification']}`) |")
    if not source_declarations:
        lines.append("| No verified dataset link observed in scanned manifests | – | – |")
    if code_checks is not None:
        unresolved_source = [check for check in code_checks if check["status"] not in ("verified_public", "indexed")]
        lines.append(f"\nUnverified GitHub manifest dataset targets: **{len(unresolved_source)}** (details in `snapshot.json`; missing verification is not evidence of nonexistence).")
    if colocated_scripts:
        lines.extend(["", "Adjacent script paths (existence only): " + ", ".join(
            f"[{index[edge['source']]['title']}]({index[edge['source']]['url']})" for edge in colocated_scripts[:15])])
    lines.extend(["", "## Experiment run links from GitHub tasks", "",
                  "Only concrete W&B `/runs/<id>` URLs qualify. A project dashboard, a code config or a loss value in an issue does **not** by itself establish a completed run or independently verified measurements.", "",
                  "| GitHub task | Linked W&B run | Verification |", "| --- | --- | --- |"])
    for edge in run_references[:25]:
        source, target = index[edge["source"]], index[edge["target"]]
        lines.append(f"| [{source['title'].replace('|', '\\|')}]({source['url']}) | [{target['title']}]({target['url']}) | `{target['verification']}` |")
    if not run_references:
        lines.append("| No concrete run URL found in indexed tasks | – | – |")
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
    lines.extend(["", "## Interpretation", "", "This is a discovery probe, **not** a complete research knowledge graph. A shared persistent identifier connects metadata records to the same publication; it does not establish that an implementation is correct or scientifically dependent on that publication. Hugging Face `base_model` and `datasets` fields are publisher-declared metadata, not independently reproduced lineage. GitHub source-code dataset declarations and co-located scripts prove neither training nor successful execution. W&B run URLs are source-declared links, not independently inspected run logs or validated metrics. Explicit mentions are references only; name-only candidates remain unverified. OpenAIRE keyword search and bounded arXiv citation lookups are not an exhaustive count of project research. Unresolved citation IDs are not evidence that a publication does not exist. Missing timestamps mean the source did not provide freshness metadata.", ""])
    return "\n".join(lines)


def incomplete_essential_sources(errors: dict[str, str]) -> list[str]:
    """Prevent an incomplete API response from replacing the last good CI snapshot."""
    critical = set(GITHUB_REPOS) | {"Hugging Face models", "Hugging Face datasets",
                                    "Hugging Face external lookup", "OpenAIRE", "GitHub source manifests",
                                    "GitHub source dataset lookup", "GitHub selected issue comments"}
    return sorted(name for name in errors if name in critical or name.startswith("OpenAIRE arXiv batch"))


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
    code_scan: dict | None = None
    code_checks: list[dict] | None = None
    code_edges: list[dict] = []
    comment_nodes: list[dict] = []
    comment_edges: list[dict] = []
    comment_collection: dict | None = None
    if args.fixture:
        fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        nodes = fixture["nodes"]
        external_checks = fixture.get("external_hf_target_checks")
        external_card_refs = fixture.get("external_hf_card_references") or hf_card_declarations(nodes)[1]
        code_scan = fixture.get("github_code_scan")
        code_checks = fixture.get("github_code_target_checks")
        code_edges = fixture.get("github_code_edges", [])
        comment_nodes = [node for node in nodes if node.get("type") == "issue_comment"]
        comment_collection = fixture.get("github_comment_collection")
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
            source_nodes, source_refs, adjacent, code_scan = github_metadata_inventory(
                GITHUB_DATA_REPO, token=os.getenv("GITHUB_TOKEN"))
            nodes.extend(source_nodes)
            more_nodes, code_checks, declared_edges = resolve_github_dataset_declarations(nodes, source_refs)
            nodes.extend(more_nodes)
            code_edges = declared_edges + adjacent
            unresolved = [check for check in code_checks if check["status"] in
                          ("rate_limited", "http_error", "fetch_failed")]
            if unresolved:
                errors["GitHub source dataset lookup"] = f"{len(unresolved)} target(s) not completely checked; see github_code_target_checks"
        except (KeyError, ValueError, UnicodeError, urllib.error.URLError, TimeoutError) as exc:
            errors["GitHub source manifests"] = str(exc)
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
        try:
            selected = selected_issue_ids(Path(__file__).with_name("impact_cases.json"))
            comment_nodes, comment_edges = github_comments_for_selected(
                nodes, selected, fetch_json, token=os.getenv("GITHUB_TOKEN"))
            nodes.extend(comment_nodes)
            comment_collection = {"status": "complete", "selected_issues": len(selected),
                                  "fetched_comments": len(comment_nodes)}
        except (KeyError, ValueError, OSError, TimeoutError) as exc:
            errors["GitHub selected issue comments"] = str(exc)
            comment_collection = {"status": "source_error", "selected_issues": "unavailable",
                                  "fetched_comments": None}
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
    run_nodes, run_edges = linked_experiment_runs(nodes)
    nodes.extend(run_nodes)
    task_edges, unresolved_tasks = github_task_references(nodes)
    claim_edges = source_claim_edges(nodes, comment_nodes, task_edges)
    edges = (links_between(nodes) + scholarly_links(nodes) + internal_card_edges + code_edges +
             run_edges + task_edges + comment_edges + claim_edges)
    profile = quality_profile(nodes, edges)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp_utc": snapshot, "nodes": nodes, "edges": edges,
               "external_hf_card_references": external_card_refs,
               "external_hf_target_checks": external_checks,
               "github_code_scan": code_scan, "github_code_target_checks": code_checks,
               "unresolved_github_task_references": unresolved_tasks,
               "github_comment_collection": comment_collection,
               "errors": errors, "openaire_search_total": openaire_total,
               "quality": profile, "citation_coverage": citation_coverage(nodes, edges)}
    (output / "snapshot.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "REPORT.md").write_text(report(nodes, edges, errors, snapshot, openaire_total,
                                              external_checks, code_scan, code_checks, unresolved_tasks,
                                              comment_collection), encoding="utf-8")
    critical_errors = incomplete_essential_sources(errors)
    print(f"Collected {len(nodes)} records, {len(edges)} evidenced/candidate edges, {len(errors)} source errors")
    if critical_errors:
        print(f"Incomplete essential sources: {', '.join(critical_errors)}; refusing to publish this snapshot", file=sys.stderr)
    return 0 if nodes and not critical_errors else 1


if __name__ == "__main__":
    sys.exit(main())
