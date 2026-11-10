"""Trace intended robots.txt reuse between HPLT and OpenEuroLLM, read-only.

Checks original source text at a pinned Git blob or double-read issue.
A keyword proves a source statement, not correctness of robots semantics.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

from hplt_overlap_audit import API, get_json, read_tree, read_issue, issue_proof

REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
BRANCH = re.compile(r"^[A-Za-z0-9_.-]+$")
MAX_BYTES = 100_000


def validate(cases):
    sources = cases.get("sources")
    checks = cases.get("review_checks")
    if not isinstance(sources, list) or not 2 <= len(sources) <= 25:
        raise ValueError("Expected a bounded source list")
    if not isinstance(checks, list) or not 1 <= len(checks) <= 15:
        raise ValueError("Expected a bounded review checklist")
    seen = set()
    for s in sources:
        if not isinstance(s, dict) or not isinstance(s.get("id"), str) or s["id"] in seen:
            raise ValueError("Missing or duplicate source identifier")
        seen.add(s["id"])
        if not REPO.fullmatch(s.get("repo", "")):
            raise ValueError("Invalid source repository")
        if not isinstance(s.get("phrase"), str) or not 3 <= len(s["phrase"]) <= 140:
            raise ValueError("Invalid bounded evidence phrase")
        if not isinstance(s.get("stage"), str) or not isinstance(s.get("meaning"), str):
            raise ValueError("Missing interpretation")
        if s.get("kind") == "file":
            if (not BRANCH.fullmatch(s.get("branch", ""))
                    or not isinstance(s.get("path"), str) or not s["path"]
                    or s["path"].startswith("/") or ".." in s["path"]):
                raise ValueError("Invalid file evidence scope")
        elif s.get("kind") == "issue":
            if type(s.get("number")) is not int or s["number"] <= 0:
                raise ValueError("Invalid issue source number")
        else:
            raise ValueError("Unsupported evidence type")
    if any(not isinstance(c, str) or not 5 <= len(c) <= 350 for c in checks):
        raise ValueError("Invalid manual review check")
    return True


def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def fetch_file(source, tree, fetch):
    path = source["path"]
    entry = tree["files"].get(path)
    if not entry:
        raise ValueError("Pinned file missing: " + tree["repo"] + "/" + path)
    if entry["size"] > MAX_BYTES:
        raise ValueError("Source file exceeds audit size limit")
    ref = tree["head"]
    url = API + "/" + source["repo"] + "/contents/" + quote(path, safe="/") + "?ref=" + ref
    item = fetch(url)
    if (item.get("type") != "file" or item.get("encoding") != "base64"
            or item.get("sha") != entry["sha"]):
        raise ValueError("Source metadata does not match pinned blob for " + path)
    encoded = item.get("content")
    if not isinstance(encoded, str):
        raise ValueError("Missing encoded Git source")
    try:
        raw = base64.b64decode(encoded.replace("\n", ""), validate=True)
        content = raw.decode("utf-8")
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Invalid Git source encoding") from exc
    if len(raw) != entry["size"] or git_blob_sha(raw) != entry["sha"]:
        raise ValueError("Content does not match pinned Git tree")
    return {"body": content,
            "url": f"https://github.com/{source['repo']}/blob/{ref}/{quote(path, safe='/')}",
            "sha256": hashlib.sha256(raw).hexdigest(), "blob_sha": entry["sha"],
            "head_sha": ref, "source_kind": "pinned_git_file"}


def source_proof(source, record):
    body = record["body"]
    phrase = source["phrase"]
    found = re.search(re.escape(phrase), body, re.I)
    if not found:
        raise ValueError("Required literal source evidence absent: " + source["id"])
    excerpt = " ".join(body[max(0, found.start() - 75):
                            min(len(body), found.end() + 75)].split())
    return {
        "id": source["id"], "stage": source["stage"], "interpretation_to_review": source["meaning"],
        "source_kind": record["source_kind"], "repo": source["repo"],
        "url": record["url"], "matched_phrase": phrase, "excerpt": excerpt[:250],
        "sha256": record["sha256"], "head_sha": record.get("head_sha"),
        "git_blob_sha": record.get("blob_sha"), "issue_state": record.get("issue_state"),
        "evidence_field": record.get("evidence_field", "file_content"),
        "verified": "literal_match_in_source", "runtime_behavior_verified": False,
    }


def build(cases, fetch=get_json):
    validate(cases)
    tree_keys = sorted({(s["repo"], s["branch"]) for s in cases["sources"] if s["kind"] == "file"})
    issue_keys = sorted({(s["repo"], s["number"]) for s in cases["sources"] if s["kind"] == "issue"})
    trees = {key: read_tree(*key, fetch=fetch) for key in tree_keys}
    # Each distinct original issue is fetched twice to reject moving sources.
    issues = {key: read_issue(*key, fetch=fetch) for key in issue_keys}
    evidence = []
    for s in cases["sources"]:
        if s["kind"] == "file":
            record = fetch_file(s, trees[(s["repo"], s["branch"])], fetch)
        else:
            issue = issues[(s["repo"], s["number"])]
            proof = issue_proof(issue, s["phrase"])
            record = {
                "body": issue["body"] if proof["evidence_field"] == "body" else issue["title"],
                "url": issue["url"], "sha256": proof["evidence_sha256"],
                "source_kind": "github_issue", "issue_state": issue["state"],
                "evidence_field": proof["evidence_field"],
            }
        evidence.append(source_proof(s, record))
    stages = {e["stage"] for e in evidence}
    if len(stages) < 5:
        raise ValueError("Insufficient pipeline stage evidence")
    return {
        "status": "read_only_human_review",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": cases["scope"],
        "sources_verified": len(evidence),
        "pinned_repositories": len(trees),
        "evidence": evidence,
        "reusable_pipeline_steps": [
            "HPLT Stage 1 extracts robots.txt WARC responses",
            "monotextor-slurm builds an FST index of disallowed site URLs",
            "the annotation stage can create a per-document allowed.zst mask",
            "HPLT Stage 3 consumes the mask only when the file is present",
        ],
        "separate_existing_functionality": "OpenEuroLLM warc2text already processes record-local X-Robots-Tag and HTML robots directives; this does not replace sitewide captured robots.txt processing.",
        "existing_coordination": "The OpenEuroLLM issue explicitly proposes adapting Jaume's earlier step; this is a handoff opportunity, not an independent duplicate implementation.",
        "review_checks": cases["review_checks"],
        "duplicate_work": "not_established",
        "critical_gap_to_validate": "For datasets requiring post-crawl sitewide robots.txt checks, absent allowed.zst currently means the HPLT Stage 3 script omits that filter. Verify intended behavior and test fail-closed policy where required.",
        "limitations": "Static source evidence only. Pinned Git content SHA and original issue text verified. No robots policy correctness, historical capture coverage, runtime tests, licensing or legal assessment. No messages posted.",
    }


def markdown(report):
    lines = [
        "# HPLT robots.txt → OpenEuroLLM: verified reuse trace", "",
        "**Source-linked reuse assessment, not a confirmed code fix or compliance audit.**",
        f"Checked {report['sources_verified']} source excerpts across {report['pinned_repositories']} pinned code repositories.",
        "",
        "## What is already coordinated", "",
        report["existing_coordination"], "",
        "## Reusable stages", "",
    ]
    for stage in report["reusable_pipeline_steps"]:
        lines.append("- " + stage)
    lines += ["", "## Important distinction", "", report["separate_existing_functionality"], "",
              "## Evidence by source", ""]
    for e in report["evidence"]:
        lines.extend([
            "### " + e["stage"] + " — " + e["id"], "",
            "- [Original pinned source](" + e["url"] + ") — " + e["source_kind"],
            "- Matched source phrase: " + e["matched_phrase"],
            "- Exact excerpt: " + " ".join(e["excerpt"].replace("|", "/").split()),
            "- SHA256: " + e["sha256"],
            "- Interpretation for human review: " + e["interpretation_to_review"],
            "- Runtime claim validated: no", "",
        ])
    lines += ["## Highest-priority validation gap", "",
              report["critical_gap_to_validate"], "",
              "## Tests before an external PR", ""]
    lines.extend([str(n) + ". " + x for n, x in enumerate(report["review_checks"], 1)])
    lines.extend(["", "## Boundaries", "", report["limitations"],
                  "Duplicate work: " + report["duplicate_work"] + "."])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default="robots_reuse_cases.json")
    parser.add_argument("--output", default="results")
    args = parser.parse_args(argv)
    try:
        cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
        result = build(cases)
        path = Path(args.output)
        path.mkdir(parents=True, exist_ok=True)
        (path / "robots_reuse.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (path / "ROBOTS_REUSE.md").write_text(markdown(result), encoding="utf-8")
        print(f"Robots reuse: {result['sources_verified']} original-source proofs, review only")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Robots reuse source audit failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
