"""Bounded GitHub-comment and explicit-dependency evidence for research graphs.

Public comments are separate source records. A stated dependency or failure is
an attributable claim, not independently validated causation or acceleration.
"""

import hashlib
import json
import re
import urllib.parse
from pathlib import Path


MAX_COMMENT_TASKS = 10
MAX_COMMENT_PAGES = 3
DEPENDENCY_HEADER = re.compile(r"^\s*(?:#{1,6}\s*)?(?:__|\*\*)?dependencies(?:__|\*\*)?\s*:?\s*$", re.I)
EXPLICIT_FAILURE = re.compile(r"\b(?:fails?|failed|failure)\s+(?:due to|with|from)\s+(?:an?\s+)?(?:OOM|out.of.memory)\b", re.I)


def selected_issue_ids(casebook_path):
    """Freeze bounded coverage; do not imply all repository comments were scanned."""
    study = json.loads(Path(casebook_path).read_text(encoding="utf-8"))
    cases = study["cases"]
    if len(cases) != MAX_COMMENT_TASKS:
        raise ValueError(f"Expected {MAX_COMMENT_TASKS} selected issue cases")
    selected = [f"github:{case['repo']}#{case['number']}" for case in cases]
    if len({id_.casefold() for id_ in selected}) != len(selected):
        raise ValueError("Duplicate selected issue for comment coverage")
    return selected


def github_comments_for_selected(issues, selected_ids, fetch_json, *, token=None,
                                 max_pages=MAX_COMMENT_PAGES):
    """Fetch every public comment in each selected issue, bounded and fail-closed.

    An API error or a full final page is a collection failure, never zero comments.
    """
    if max_pages < 1:
        raise ValueError("max_pages must be positive")
    by_id = {item["id"].casefold(): item for item in issues if item.get("type") == "issue"}
    nodes, edges = [], []
    seen = set()
    for issue_id in selected_ids:
        issue = by_id.get(issue_id.casefold())
        if issue is None:
            raise ValueError(f"Selected issue absent from indexed inventory: {issue_id}")
        repo, number = issue_id.removeprefix("github:").rsplit("#", 1)
        for page in range(1, max_pages + 1):
            query = urllib.parse.urlencode({"per_page": 100, "page": page})
            data = fetch_json(f"https://api.github.com/repos/{repo}/issues/{number}/comments?{query}", token=token)
            if not isinstance(data, list):
                raise ValueError(f"Unexpected comment response for {issue_id}, page {page}")
            for item in data:
                comment_id, body = item.get("id"), item.get("body")
                if not isinstance(comment_id, int) or body is None or not isinstance(body, str):
                    raise ValueError(f"Invalid comment ID/body in {issue_id}, page {page}")
                if not isinstance(item.get("html_url"), str) or not item["html_url"].startswith("https://github.com/"):
                    raise ValueError(f"Comment {comment_id} missing canonical GitHub URL")
                key = (repo.casefold(), comment_id)
                if key in seen:
                    raise ValueError(f"Duplicate comment across pages: {repo}/{comment_id}")
                seen.add(key)
                node_id = f"github_comment:{repo}#{comment_id}"
                nodes.append({
                    "id": node_id, "type": "issue_comment", "title": f"Comment {comment_id} on {issue_id}",
                    "description": body, "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                    "url": item["html_url"], "updated_at": item.get("updated_at"),
                    "repository": repo, "issue_id": issue_id, "comment_id": comment_id,
                    "author": (item.get("user") or {}).get("login"),
                })
                edges.append({"source": issue_id, "target": node_id,
                              "status": "source_comment", "relationship": "has_public_comment",
                              "evidence_type": "github_issue_comment_api", "evidence": item["html_url"],
                              "reason": "Public comment linked to the task, not an endorsed conclusion"})
            if len(data) < 100:
                break
            if page == max_pages:
                raise ValueError(f"Comment pagination limit reached for {issue_id}")
    return nodes, edges


def _dependency_claim(body, literal_reference):
    """Allow only explicit 'Dependencies' sections or 'blocked by/depends on' claims."""
    ref = re.compile(re.escape(literal_reference) + r"(?![\w-])", re.I)
    lines = body.splitlines()
    for line_no, line in enumerate(lines):
        if not DEPENDENCY_HEADER.match(line):
            continue
        section = []
        for next_line in lines[line_no + 1:line_no + 7]:
            if not next_line.strip() or next_line.lstrip().startswith("# "):
                break
            section.append(next_line)
        joined = "\n".join(section)
        if re.match(r"\s*(?:N/?A|none|no dependencies)\b", joined, flags=re.I):
            continue
        for entry in section:
            if re.match(r"\s*(?:[-*]\s*)?(?:related|downstream|see also)\s*:", entry, flags=re.I):
                continue
            if ref.search(entry):
                return "labeled_dependencies_section", (line + "\n" + entry)[:350]
    direct = re.search(r"(?i)\b(?:blocked by|depends on|prerequisite\s*:?)\b[^\n]{0,100}" +
                       re.escape(literal_reference) + r"(?![\w-])", body)
    if direct and not re.search(r"\b(?:not|never)\s*$", body[max(0, direct.start()-12):direct.start()], re.I):
        return "explicit_dependency_phrase", direct.group()[:350]
    return None


def source_claim_edges(issues, comments, task_references):
    """Keep claims at their actual source and strictly separate them from mentions."""
    index = {node["id"]: node for node in issues}
    edges = []
    for edge in task_references:
        source = index.get(edge["source"])
        if not source:
            continue
        claim = _dependency_claim(source.get("description") or "", edge["evidence"])
        if claim:
            kind, evidence = claim
            edges.append({"source": edge["source"], "target": edge["target"],
                          "status": "author_declared_dependency", "relationship": "declares_depends_on",
                          "evidence_type": kind, "evidence": evidence,
                          "source_url": source["url"],
                          "source_sha256": hashlib.sha256((source.get("description") or "").encode("utf-8")).hexdigest(),
                          "reason": "Issue author explicitly declares dependency; not verified blocking or measured impact"})
    for comment in comments:
        match = EXPLICIT_FAILURE.search(comment["description"])
        if match:
            edges.append({"source": comment["id"], "target": comment["issue_id"],
                          "status": "reported_blocker", "relationship": "reports_failure_for",
                          "evidence_type": "explicit_oom_failure_statement", "evidence": match.group(),
                          "source_url": comment["url"],
                          "reason": "Commenter reports an OOM failure; neither independently reproduced nor a task dependency"})
    return edges
