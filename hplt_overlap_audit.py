"""Read-only HPLT/OpenEuroLLM code reuse and issue-handoff audit.

A Git blob match proves identical bytes, not shared authorship.
Issue similarities are candidate handoffs, not proof of redundant work.
"""
from __future__ import annotations

import argparse
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
from urllib.parse import quote

API = "https://api.github.com/repos"
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REF = re.compile(r"^[A-Za-z0-9_.-]+$")
SHA = re.compile(r"^[0-9a-f]{40}$")


def digest(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def get_json(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ai-research-graph-hplt-audit"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
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


def validate(cases):
    ids = set()
    for group, limit in (("code_pairs", 8), ("issue_pairs", 20)):
        pairs = cases.get(group)
        if not isinstance(pairs, list) or not 1 <= len(pairs) <= limit:
            raise ValueError("Invalid bounded case list: " + group)
        for pair in pairs:
            identifier = pair.get("id")
            if not isinstance(identifier, str) or identifier in ids:
                raise ValueError("Duplicate or missing case ID")
            ids.add(identifier)
            for side in ("a", "b"):
                src = pair.get(side)
                if not isinstance(src, dict) or not REPO.fullmatch(src.get("repo", "")):
                    raise ValueError("Invalid repository in " + identifier)
                if group == "code_pairs":
                    if not REF.fullmatch(src.get("ref", "")) or not isinstance(src.get("prefix"), str) or not src["prefix"].endswith("/") or ".." in src["prefix"]:
                        raise ValueError("Invalid Git tree scope in " + identifier)
                elif type(src.get("number")) is not int or src["number"] < 1 or not isinstance(src.get("phrase"), str) or len(src["phrase"]) < 3:
                    raise ValueError("Invalid issue selector in " + identifier)
            if pair["a"]["repo"] == pair["b"]["repo"]:
                raise ValueError("Cannot compare the same repository")
    return True


def read_tree(repo, ref, fetch=get_json):
    head = (fetch(f"{API}/{repo}/branches/{quote(ref, safe='')}").get("commit") or {}).get("sha", "")
    if not SHA.fullmatch(head):
        raise ValueError("Cannot pin source ref for " + repo)
    data = fetch(f"{API}/{repo}/git/trees/{head}?recursive=1")
    if data.get("truncated") is not False or not isinstance(data.get("tree"), list) or len(data["tree"]) > 12000:
        raise ValueError("Truncated, oversized or missing Git tree for " + repo)
    files = {}
    for row in data["tree"]:
        if row.get("type") == "blob":
            if not isinstance(row.get("path"), str) or not SHA.fullmatch(row.get("sha", "")):
                raise ValueError("Bad Git tree entry for " + repo)
            files[row["path"]] = {"sha": row["sha"], "size": row.get("size", 0)}
    return {"repo": repo, "head": head, "files": files}


def source_link(tree, path):
    return f"https://github.com/{tree['repo']}/blob/{tree['head']}/{quote(path, safe='/')}"


def compare_code(pair, trees):
    left_key, right_key = pair["a"], pair["b"]
    left = trees[(left_key["repo"], left_key["ref"])]
    right = trees[(right_key["repo"], right_key["ref"])]
    def scoped(tree, prefix):
        return {path[len(prefix):]: (path, info) for path, info in tree["files"].items()
                if path.startswith(prefix) and path[len(prefix):]}
    a = scoped(left, left_key["prefix"])
    b = scoped(right, right_key["prefix"])
    if not a or not b:
        raise ValueError("Empty selected code component in " + pair["id"])
    shared = sorted(set(a) & set(b))
    if len(shared) > 80:
        raise ValueError("Too many shared paths in " + pair["id"])
    files = []
    for suffix in shared:
        pa, va = a[suffix]
        pb, vb = b[suffix]
        equal = va["sha"] == vb["sha"]
        tag = ("identical_nontrivial_file" if equal and va["size"] >= 64 else
               "identical_trivial_file" if equal else "same_relative_path_different_blobs")
        files.append({
            "relative_path": suffix, "a_url": source_link(left, pa),
            "b_url": source_link(right, pb),
            "a_blob_sha": va["sha"], "b_blob_sha": vb["sha"],
            "a_size": va["size"], "b_size": vb["size"],
            "status": tag
        })
    return {
        "id": pair["id"], "question": pair["question"],
        "a_repo": left["repo"], "b_repo": right["repo"],
        "a_head": left["head"], "b_head": right["head"],
        "a_files_in_scope": len(a), "b_files_in_scope": len(b),
        "shared_paths": len(files),
        "identical_nontrivial": sum(f["status"] == "identical_nontrivial_file" for f in files),
        "identical_trivial": sum(f["status"] == "identical_trivial_file" for f in files),
        "different_blobs": sum(f["status"] == "same_relative_path_different_blobs" for f in files),
        "files": files, "duplicate_work": "not_established",
    }


def read_issue(repo, number, fetch=get_json):
    url = f"{API}/{repo}/issues/{number}"
    a, b = fetch(url), fetch(url)
    expected = f"https://github.com/{repo}/issues/{number}"
    for src in (a, b):
        if (src.get("number") != number or src.get("html_url") != expected
                or src.get("state") not in ("open", "closed")
                or not isinstance(src.get("title"), str)
                or not isinstance(src.get("body"), (str, type(None)))
                or "pull_request" in src):
            raise ValueError("Issue metadata invalid: " + expected)
    for key in ("state", "body", "title", "updated_at", "comments", "closed_at"):
        if a.get(key) != b.get(key):
            raise ValueError("Issue changed during audit: " + expected)
    body = a.get("body") or ""
    return {"repo": repo, "number": number, "state": a["state"],
            "title": a["title"], "url": expected, "sha256": digest(body),
            "body": body, "updated_at": a.get("updated_at"),
            "comments_count_unreviewed": a.get("comments", 0)}


def issue_proof(issue, phrase):
    match = re.search(re.escape(phrase), issue["body"], flags=re.I)
    if not match:
        raise ValueError(f"Required phrase absent from {issue['repo']}#{issue['number']}: {phrase}")
    snippet = " ".join(issue["body"][max(0, match.start() - 65):
                                    min(len(issue["body"]), match.end() + 65)].split())
    return {"url": issue["url"], "title": issue["title"], "state": issue["state"],
            "updated_at": issue["updated_at"], "body_sha256": issue["sha256"],
            "phrase": phrase, "excerpt": snippet[:170],
            "comments_count_unreviewed": issue["comments_count_unreviewed"]}


def compare_issue(pair, issues):
    la, lb = pair["a"], pair["b"]
    a = issue_proof(issues[(la["repo"], la["number"])], la["phrase"])
    b = issue_proof(issues[(lb["repo"], lb["number"])], lb["phrase"])
    return {
        "id": pair["id"], "hypothesis": pair["hypothesis"],
        "a": a, "b": b,
        "review_priority": "inspect_prior_work" if a["state"] == "open" and b["state"] == "closed" else "manual_review",
        "duplicate_work": "not_established", "outreach": "none",
    }


def build(cases, fetch=get_json):
    validate(cases)
    tree_keys = sorted({(p[s]["repo"], p[s]["ref"]) for p in cases["code_pairs"] for s in ("a", "b")})
    issue_keys = sorted({(p[s]["repo"], p[s]["number"]) for p in cases["issue_pairs"] for s in ("a", "b")})
    trees = {k: read_tree(*k, fetch=fetch) for k in tree_keys}
    issues = {k: read_issue(*k, fetch=fetch) for k in issue_keys}
    return {
        "status": "read_only_human_review",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": cases["scope"], "pinned_trees": len(trees),
        "unique_issues_checked": len(issues),
        "code_pairs": [compare_code(p, trees) for p in cases["code_pairs"]],
        "issue_pairs": [compare_issue(p, issues) for p in cases["issue_pairs"]],
        "limitations": "Curated pair selection. Git blob hashes establish only byte identity. "
        "Shared paths with different hashes indicate code differences, not necessarily historical provenance. "
        "Original issue descriptions and state re-read; comments, code semantics, licenses and resolution "
        "are NOT validated. No automatic outreach."
    }


def markdown(result):
    lines = ["# HPLT ↔ OpenEuroLLM: source-audited code and issue overlaps", "",
             "**Read-only pilot. Byte-identical files do not establish wasted effort. "
             "Closed issues do not establish reusable fixes.** No external messages sent.", "",
             f"Checked **{result['pinned_trees']}** pinned trees, "
             f"**{result['unique_issues_checked']}** original issues, "
             f"**{len(result['code_pairs'])}** code scopes, "
             f"**{len(result['issue_pairs'])}** cross-project issue pairs.", "",
             "## Pinned Git-file comparisons", ""]
    for c in result["code_pairs"]:
        lines.extend([f"### {c['id']}", "", c["question"], "",
            f"- Sources: {c['a_repo']} at {c['a_head']} versus {c['b_repo']} at {c['b_head']}.",
            f"- Same suffix: **{c['shared_paths']}** paths; "
            f"**{c['identical_nontrivial']}** nontrivial exact files, "
            f"**{c['identical_trivial']}** trivial exact files, "
            f"**{c['different_blobs']}** changed-file blobs.", "",
            "| Component | Source A | Source B | Status |",
            "| --- | --- | --- | --- |"])
        for f in c["files"]:
            lines.append(f"| {f['relative_path']} | [code]({f['a_url']}) | "
                         f"[code]({f['b_url']}) | {f['status']} |")
        lines.append("")
    lines.extend(["## Original issue overlap (human review)", "",
                  "| OpenEuroLLM current task | HPLT historic task | Follow-up |",
                  "| --- | --- | --- |"])
    for i in result["issue_pairs"]:
        a, b = i["a"], i["b"]
        lines.append(f"| [{a['title']}]({a['url']}) ({a['state']}) | "
                     f"[{b['title']}]({b['url']}) ({b['state']}) | {i['review_priority']} |")
    lines.extend(["", "## Source-backed issue observations", ""])
    for i in result["issue_pairs"]:
        lines.extend([f"### {i['id']}", "", i["hypothesis"], ""])
        for key in ("a", "b"):
            p = i[key]
            lines.append(f"- [{key.upper()}: {p['title']}]({p['url']}) — "
                         f"{p['state']}; phrase '{p['phrase']}': "
                         f"'{p['excerpt']}' (body SHA256 {p['body_sha256']}).")
        lines.extend(["- Duplicate implementation: **not established**. "
                      "Issue comments and acceptance criteria require manual verification.", ""])
    lines.extend(["## Method boundaries", "", result["limitations"]])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default="hplt_overlap_cases.json")
    parser.add_argument("--output", default="results")
    args = parser.parse_args(argv)
    try:
        cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
        report = build(cases)
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        (out / "hplt_overlap.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (out / "HPLT_OVERLAP.md").write_text(markdown(report), encoding="utf-8")
        print(f"Verified {len(report['code_pairs'])} Git scopes and {len(report['issue_pairs'])} issue pairs")
        return 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, urllib.error.URLError) as exc:
        print(f"HPLT audit aborted: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
