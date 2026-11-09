"""Bounded, evidence-linked comparison of European AI project repositories.

Read-only GitHub API pilot. Shared terms are NOT proof of duplicate work.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com/repos"
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
MAX_README_BYTES = 300_000


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_json(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ai-research-graph-cross-project"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as res:
                return json.load(res)
        except (urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code < 500 and exc.code not in (408, 429):
                raise
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def validate_registry(registry):
    repos = registry.get("repositories")
    pairs = registry.get("pairs")
    if (not isinstance(repos, list) or len(repos) < 2 or len(repos) > 30
            or any(not isinstance(r, str) or not REPO_RE.fullmatch(r) for r in repos)
            or len(set(x.casefold() for x in repos)) != len(repos)):
        raise ValueError("Invalid bounded repository registry")
    if not isinstance(pairs, list) or not pairs or len(pairs) > 30:
        raise ValueError("Invalid comparison pairs")
    seen = set()
    for p in pairs:
        if (not isinstance(p, dict) or p.get("id") in seen
                or p.get("a") not in repos or p.get("b") not in repos
                or p["a"].split("/")[0].casefold() == p["b"].split("/")[0].casefold()
                or not isinstance(p.get("theme"), str)
                or not isinstance(p.get("question"), str)
                or not isinstance(p.get("terms"), list) or not p["terms"]
                or any(not isinstance(s, str) or len(s) < 3 for s in p["terms"])):
            raise ValueError(f"Invalid pair: {p}")
        seen.add(p["id"])
    for link in registry.get("documented_relationships", []):
        if (not link.get("source_url", "").startswith("https://")
                or link.get("verification") != "editorial_official_source_not_rechecked_by_audit"):
            raise ValueError("Unverifiable editorial relationship")


def fetch_readme(repo, fetch=get_json):
    """Fetch README twice and fail closed if it changes before publication."""
    url = f"{API}/{repo}/readme"
    def load():
        item = fetch(url)
        encoded = item.get("content")
        if item.get("encoding") != "base64" or not isinstance(encoded, str):
            raise ValueError(f"Missing readable README for {repo}")
        raw = base64.b64decode(encoded, validate=False)
        if len(raw) > MAX_README_BYTES:
            raise ValueError(f"README exceeds pilot limit: {repo}")
        body = raw.decode("utf-8")
        html = item.get("html_url") or ""
        if not html.startswith(f"https://github.com/{repo}/"):
            raise ValueError(f"README source URL is unexpected: {repo}")
        return body, html, item.get("sha")
    first = load()
    second = load()
    if first != second:
        raise ValueError(f"README drift during audit: {repo}")
    return {"body": first[0], "url": first[1], "github_blob_sha": first[2],
            "sha256": sha256(first[0])}


def fetch_repositories(registry, fetch=get_json):
    result = {}
    for name in registry["repositories"]:
        meta = fetch(f"{API}/{name}")
        if (meta.get("full_name", "").casefold() != name.casefold()
                or meta.get("archived") is None
                or not meta.get("html_url", "").startswith(f"https://github.com/{name}")):
            raise ValueError(f"Repository unavailable or renamed: {name}")
        readme = fetch_readme(name, fetch)
        result[name] = {
            "full_name": name, "url": meta["html_url"],
            "description": meta.get("description") or "",
            "is_fork": bool(meta.get("fork")),
            "fork_parent": (meta.get("parent") or {}).get("full_name"),
            "archived": meta["archived"], "pushed_at": meta.get("pushed_at"),
            "readme": readme,
        }
    return result


def evidence_for(repo, term):
    """Return an original-source excerpt with a content hash, or no match."""
    body = repo["readme"]["body"]
    pos = body.casefold().find(term.casefold())
    if pos >= 0:
        context = " ".join(body[max(0, pos - 70): pos + len(term) + 70].split())
        return {"term": term, "source_url": repo["readme"]["url"],
                "sha256": repo["readme"]["sha256"], "excerpt": context[:210],
                "origin": "README"}
    desc = repo["description"]
    pos = desc.casefold().find(term.casefold())
    if pos >= 0:
        return {"term": term, "source_url": repo["url"], "sha256": sha256(desc),
                "excerpt": desc, "origin": "repository_description"}
    return None


def compare(pair, repos):
    a, b = repos[pair["a"]], repos[pair["b"]]
    matching = []
    for term in pair["terms"]:
        left, right = evidence_for(a, term), evidence_for(b, term)
        if left and right:
            matching.append({"term": term, "a": left, "b": right})
    # Cross-repo hyperlinks are a source-backed sign of awareness/reuse, not proof of collaboration.
    links = []
    for src, dst in ((a, b), (b, a)):
        target = dst["url"].casefold()
        body = src["readme"]["body"].casefold()
        if target in body:
            links.append({"source": src["full_name"], "target": dst["full_name"],
                          "source_url": src["readme"]["url"],
                          "sha256": src["readme"]["sha256"],
                          "mentioned_repo_url": dst["url"]})
    category = ("explicit_repository_reference" if links else
                "shared_topic_terms" if matching else "unconfirmed_topic_hypothesis")
    return {
        "id": pair["id"], "theme": pair["theme"], "question": pair["question"],
        "repository_a": a["full_name"], "repository_b": b["full_name"],
        "source_a": a["readme"]["url"], "source_b": b["readme"]["url"],
        "repo_pushed_a": a["pushed_at"], "repo_pushed_b": b["pushed_at"],
        "shared_terms": matching[:8], "direct_references": links,
        "classification": category, "duplicate_work": "not_established",
        "next_step": "Human must inspect current issues, code paths, licences and already shared dependencies before claiming redundancy.",
        "outreach": "none",
    }


def build(registry, fetch=get_json):
    validate_registry(registry)
    repos = fetch_repositories(registry, fetch)
    comparisons = [compare(p, repos) for p in registry["pairs"]]
    return {
        "status": "read_only_human_review", "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": registry["scope"], "repositories_checked": len(repos),
        "pairs_checked": len(comparisons),
        "comparisons": comparisons,
        "documented_relationships": registry.get("documented_relationships", []),
        "limitations": "Manually curated bounded pair sample, original README/metadata evidence only. "
                       "Shared terms, cross-links and editorially documented collaboration are distinct. "
                       "No code similarity test, no issue-level duplicate verification, no outreach.",
    }


def markdown(result):
    lines = [
        "# European AI cross-project overlap — exploratory pilot", "",
        "**Read-only and review-only.** "
        "Shared topics are not proof of duplicate work or wasted effort.", "",
        f"Audited **{result['repositories_checked']}** public repositories, "
        f"**{result['pairs_checked']}** curated cross-organization pairs.", "",
        "## Documented cooperation (editorial source references)", "",
        "These official reports are curated context; the automated audit does not revalidate their web content.", "",
    ]
    for link in result["documented_relationships"]:
        lines.append(f"- **{' ↔ '.join(link['projects'])}:** {link['summary']} "
                     f"[Original public source]({link['source_url']}).")
    lines.extend(["", "## Repo-to-repo comparisons", ""])
    for row in result["comparisons"]:
        lines += [
            f"### {row['theme']}: [{row['repository_a']}]({row['source_a']}) "
            f"↔ [{row['repository_b']}]({row['source_b']})", "",
            f"- Status: **{row['classification']}**; duplicate work: **NOT established**.",
            f"- What to investigate: {row['question']}",
            f"- Last repository push: {row['repository_a']} {row['repo_pushed_a']}; "
            f"{row['repository_b']} {row['repo_pushed_b']}.",
        ]
        for link in row["direct_references"]:
            lines.append(f"- [Explicit repository link]({link['source_url']}): "
                         f"{link['source']} references {link['mentioned_repo_url']} "
                         f"(source SHA256 \`{link['sha256']}\`).")
        for term in row["shared_terms"]:
            lines.append(f"- Shared text \`{term['term']}\`: "
                         f"[A]({term['a']['source_url']}) "
                         f"(\`{term['a']['excerpt'].replace(chr(96), chr(39))}\`, "
                         f"SHA256 \`{term['a']['sha256']}\`); "
                         f"[B]({term['b']['source_url']}) "
                         f"(\`{term['b']['excerpt'].replace(chr(96), chr(39))}\`, "
                         f"SHA256 \`{term['b']['sha256']}\`).")
        lines.extend([f"- Required next check: {row['next_step']}", ""])
    lines.extend(["## Boundaries", "", result["limitations"], "",
                  "No code was compared automatically; even an explicit cross-repo URL only proves "
                  "that the URL is mentioned in the README. Do not contact project maintainers "
                  "without separate human approval."])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default="cross_project_sources.json")
    parser.add_argument("--output", default="results")
    args = parser.parse_args(argv)
    try:
        registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
        report = build(registry)
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        (out / "cross_project.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (out / "CROSS_PROJECT.md").write_text(markdown(report), encoding="utf-8")
        print(f"Cross-project pilot: {report['pairs_checked']} pairs across {report['repositories_checked']} repos")
        return 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, urllib.error.URLError) as exc:
        print(f"Cross-project audit aborted; no report published: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
