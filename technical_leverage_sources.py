"""Bounded public GitHub source collection for leverage review; no code execution."""
import base64
import hashlib
import re
from collections import defaultdict
from urllib.parse import quote

from eu_source_discovery import canonical, url_for
from cross_project_audit import fetch_readme

API = "https://api.github.com/repos"
MAX_REPOS = 8
MAX_ISSUES = 3
MAX_COMMENTS = 20
MAX_BYTES = 100_000
MAX_LINKS = 20
MANIFESTS = ("requirements.txt", "pyproject.toml", "package.json")
LINK = re.compile(r"https://(?:github\.com|huggingface\.co)/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+){1,2}(?:/[^\s<>\x22\x27\])},;]*)?", re.I)


def references(repo, text, source_url, kind, stamp):
    """Retain exact URLs and contextual hashes; never infer use from mentions."""
    source = "https://github.com/" + repo.lower()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    found = {}
    for match in LINK.finditer(text):
        raw = match.group().rstrip(".,:")
        key = canonical(raw)
        if not key:
            continue
        target = url_for(key)
        if target == source or target in found:
            continue
        found[target] = {
            "source": source, "target": target, "relationship": "references",
            "verification_status": "verified", "last_seen": stamp,
            "evidence": {"source_entity": source, "source_url": source_url,
                         "excerpt": raw, "type": kind, "sha256": digest,
                         "context": " ".join(text[max(0, match.start()-80):match.end()+80].split())[:300]}}
        if len(found) == MAX_LINKS:
            break
    return list(found.values())


def manifest_dependencies(repo, path, text, url, stamp):
    """Only direct VCS URL declarations, not ordinary package-name guesses."""
    import json
    import tomllib
    values = []
    if path == "requirements.txt":
        values = [line.strip() for line in text.splitlines()
                  if line.strip() and not line.lstrip().startswith(("#", "-r", "--"))]
    elif path == "pyproject.toml":
        data = tomllib.loads(text)
        project = data.get("project", {})
        values = list(project.get("dependencies", []))
        for group in project.get("optional-dependencies", {}).values():
            values.extend(group)
    elif path == "package.json":
        data = json.loads(text)
        for group in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
            values.extend(data.get(group, {}).values())
    output = []
    for value in values:
        if not isinstance(value, str):
            continue
        # Ignore comments and non-VCS links; do not resolve package names to repos.
        value = value.split(" #", 1)[0].strip()
        match = re.search(r"(?:^|@\s*|(?:-e\s+))git\+https://github\.com/[\w.-]+/[\w.-]+", value, re.I)
        if not match:
            continue
        vcs = match.group().split("git+", 1)[-1]
        edges = references(repo, vcs, url, "manifest_vcs_declaration", stamp)
        for edge in edges:
            edge["evidence"]["sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            edge["evidence"]["context"] = value[:300]
        output.extend(edges)
        if len(output) >= MAX_LINKS:
            break
    return output[:MAX_LINKS]


MAX_ARCHIVE_EDGES = 12000
EU_PRIORITY_SLOTS = 6


def select_repos(config, metadata, previous):
    """Reserve six slots for curated EU context; rotate within both cohorts.

    The registry supplies context, not independently verified affiliation.
    Unused slots spill over, and distinct owners are preferred within a run.
    """
    curated = {x["repo"].lower(): x["repo"] for x in config["repositories"]}
    choices = dict(curated)
    choices.update({x["repo"].lower(): x["repo"] for x in metadata
                    if x.get("status") == "review_only" and x.get("recent_push")
                    and x.get("technical_signals")})
    history = (previous or {}).get("last_attempt", {})
    ordered = sorted(choices, key=lambda k: (history.get(k, ""), k))
    selected, owners = [], set()

    def take(keys, until):
        for key in keys:
            if len(selected) >= until:
                break
            owner = key.split("/")[0]
            if owner not in owners:
                owners.add(owner)
                selected.append(choices[key])

    take([k for k in ordered if k in curated], EU_PRIORITY_SLOTS)
    take([k for k in ordered if k not in curated], MAX_REPOS)
    take(ordered, MAX_REPOS)
    return selected


def archive_edges(previous, current):
    """Keep distinct source observations across rotations, bounded by recency.

    Retention is historical, not a claim that a link still exists. Do not
    delete earlier evidence on failed or partial reads. A changed document
    hash replaces the old observation for that same source/target/type.
    """
    old = (previous or {}).get("archive_edges", (previous or {}).get("edges", []))
    merged = {}
    for edge in [*old, *current]:
        proof = edge["evidence"]
        key = (edge["source"], edge["target"], proof["source_url"], proof["type"])
        last = edge.get("last_seen") or ""
        if key not in merged or last >= (merged[key].get("last_seen") or ""):
            merged[key] = {**edge, "first_seen": min(
                edge.get("first_seen") or last,
                merged.get(key, {}).get("first_seen") or last)}
    ordered = sorted(merged.values(), key=lambda e: (
        e.get("last_seen") or "", e["source"], e["target"],
        e["evidence"]["source_url"], e["evidence"]["type"]), reverse=True)
    return ordered[:MAX_ARCHIVE_EDGES], max(0, len(ordered) - MAX_ARCHIVE_EDGES)


def collect(config, metadata, fetch, *, stamp, previous=None):
    selected = select_repos(config, metadata, previous)
    history = dict((previous or {}).get("last_attempt", {}))
    edges, errors, coverage = [], [], []
    def attempt(repo, stage, fn):
        try:
            return fn()
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            errors.append({"repo": repo, "stage": stage, "error": type(exc).__name__})
            return None

    for repo in selected:
        history[repo.lower()] = stamp
        endpoint = f"{API}/{repo}"
        counts = {"repo": repo, "readme": 0, "issues": 0, "comments": 0,
                  "manifests": 0, "truncated": []}
        coverage.append(counts)
        meta = attempt(repo, "identity", lambda: fetch(endpoint))
        if (not isinstance(meta, dict) or meta.get("full_name", "").lower() != repo.lower()
                or meta.get("private") is not False or meta.get("fork") is not False
                or meta.get("archived") is not False or meta.get("disabled")):
            errors.append({"repo": repo, "stage": "identity", "error": "public_identity_not_established"})
            continue
        readme = attempt(repo, "readme", lambda: fetch_readme(repo, fetch))
        if readme:
            counts["readme"] = 1
            edges.extend(references(repo, readme["body"], readme["url"], "readme_reference", stamp))
        def root():
            data = fetch(endpoint + "/contents")
            if not isinstance(data, list):
                raise ValueError("invalid root listing")
            if len(data) >= 1000:
                counts["truncated"].append("root")
            return {x["name"]: x for x in data if x.get("type") == "file"}
        files = attempt(repo, "root", root) or {}
        for path in MANIFESTS:
            if path not in files:
                continue
            def scan_manifest():
                entry = files[path]
                if not 0 <= entry.get("size", MAX_BYTES+1) <= MAX_BYTES:
                    raise ValueError("manifest too large")
                item = fetch(endpoint + "/contents/" + quote(path))
                if (item.get("sha") != entry.get("sha") or item.get("encoding") != "base64"
                        or not item.get("html_url", "").lower().startswith("https://github.com/" + repo.lower() + "/blob/")):
                    raise ValueError("manifest identity or drift")
                raw = base64.b64decode(item["content"])
                if len(raw) > MAX_BYTES:
                    raise ValueError("manifest too large")
                counts["manifests"] += 1
                return manifest_dependencies(repo, path, raw.decode("utf-8"), item["html_url"], stamp)
            edges.extend(attempt(repo, path, scan_manifest) or [])
        def recent():
            rows = fetch(endpoint + f"/issues?state=all&sort=updated&direction=desc&per_page={MAX_ISSUES}")
            if not isinstance(rows, list) or len(rows) > MAX_ISSUES:
                raise ValueError("invalid issue page")
            if len(rows) == MAX_ISSUES:
                counts["truncated"].append("issues")
            return rows
        for issue in attempt(repo, "issues", recent) or []:
            number = issue.get("number")
            expected = f"https://github.com/{repo}/issues/{number}"
            if ("pull_request" in issue or type(number) is not int or number < 1
                    or str(issue.get("html_url", "")).lower() != expected.lower()):
                continue
            counts["issues"] += 1
            body = issue.get("body") or ""
            if isinstance(body, str) and len(body.encode("utf-8")) <= MAX_BYTES:
                edges.extend(references(repo, body, expected, "issue_reference", stamp))
            else:
                counts["truncated"].append(f"issue:{number}")
            if not issue.get("comments"):
                continue
            def comments():
                rows = fetch(endpoint + f"/issues/{number}/comments?per_page={MAX_COMMENTS}")
                if not isinstance(rows, list) or len(rows) > MAX_COMMENTS:
                    raise ValueError("invalid comment page")
                if len(rows) != issue.get("comments"):
                    counts["truncated"].append(f"comments:{number}")
                return rows
            for comment in attempt(repo, f"comments:{number}", comments) or []:
                cid, body = comment.get("id"), comment.get("body")
                url = expected + f"#issuecomment-{cid}"
                if (type(cid) is not int or not isinstance(body, str)
                        or str(comment.get("html_url", "")).lower() != url.lower()):
                    continue
                if len(body.encode("utf-8")) > MAX_BYTES:
                    counts["truncated"].append(f"comment:{cid}")
                    continue
                counts["comments"] += 1
                edges.extend(references(repo, body, url, "public_issue_comment_reference", stamp))
    archive, dropped = archive_edges(previous, edges)
    curated = {x["repo"].lower() for x in config["repositories"]}
    return {"selected": selected, "last_attempt": history, "coverage": coverage,
            "edges": edges, "archive_edges": archive, "archive_dropped": dropped,
            "curated_selected": sum(r.lower() in curated for r in selected),
            "errors": errors,
            "limits": {"repositories": MAX_REPOS, "issues_per_repo": MAX_ISSUES,
                       "comments_per_issue": MAX_COMMENTS, "links_per_document": MAX_LINKS,
                       "archive_edges": MAX_ARCHIVE_EDGES, "curated_priority_slots": EU_PRIORITY_SLOTS},
            "review_only": True}
