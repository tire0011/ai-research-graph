"""Conservative state checks for opportunities discovered from public GitHub tasks.

A cross-referenced PR is evidence of activity, not proof a task was fixed.
This module never posts, claims a task, or infers scientific benefit.
"""

from __future__ import annotations

import re
from urllib.parse import urlencode

ISSUE_URL = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/issues/([1-9]\d*)")
PR_API = re.compile(r"https://api\.github\.com/repos/([\w.-]+)/([\w.-]+)/pulls/([1-9]\d*)")
PAGE_SIZE = 100
MAX_TIMELINE_PAGES = 3
MAX_LINKED_PRS = 5

FOLLOW_UP_FEEDBACK = {"reviewed", "proposal_prepared", "published", "response_received"}


def related_pull_requests(fetch, issue_url: str) -> list[dict]:
    """Read the bounded timeline and verify cross-referenced PRs live.

    Failure or incomplete pagination must become needs_review at the caller,
    never a new recommendation. Cross-references may be merely textual.
    """
    match = ISSUE_URL.fullmatch(issue_url)
    if match is None:
        raise ValueError("Invalid GitHub issue URL")
    owner, repo, number = match.groups()
    api = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/timeline"
    links: set[str] = set()
    for page in range(1, MAX_TIMELINE_PAGES + 1):
        query = urlencode({"per_page": PAGE_SIZE, "page": page})
        events = fetch(f"{api}?{query}")
        if not isinstance(events, list):
            raise ValueError("Invalid GitHub issue timeline response")
        for event in events:
            if not isinstance(event, dict):
                raise ValueError("Invalid GitHub timeline event")
            if event.get("event") != "cross-referenced":
                continue
            source = event.get("source") or {}
            if not isinstance(source, dict):
                raise ValueError("Invalid cross-reference source")
            item = source.get("issue") or {}
            if not isinstance(item, dict):
                raise ValueError("Invalid cross-reference issue")
            pr = item.get("pull_request")
            if pr is None:
                continue
            url = pr.get("url") if isinstance(pr, dict) else None
            if not isinstance(url, str) or not PR_API.fullmatch(url):
                raise ValueError("Invalid cross-referenced PR URL")
            links.add(url)
            if len(links) > MAX_LINKED_PRS:
                raise ValueError("Too many linked PRs to verify")
        if len(events) < PAGE_SIZE:
            break
    else:
        raise ValueError("Issue timeline pagination cap reached")

    result = []
    for url in sorted(links):
        pull = fetch(url)
        if not isinstance(pull, dict):
            raise ValueError("Invalid linked PR response")
        match = PR_API.fullmatch(url)
        assert match is not None
        owner, repo, number = match.groups()
        expected_url = f"https://github.com/{owner}/{repo}/pull/{number}"
        if pull.get("html_url") != expected_url or pull.get("state") not in {"open", "closed"}:
            raise ValueError("Linked PR identity or state mismatch")
        author = (pull.get("user") or {}).get("login")
        if author is not None and not isinstance(author, str):
            raise ValueError("Invalid linked PR author")
        result.append({
            "url": expected_url,
            "state": pull["state"],
            "merged": bool(pull.get("merged_at")),
            "author": author,
        })
    return result


def classify(issue: dict, comments: list[dict], linked_prs: list[dict] | None,
             *, actor: str | None, feedback_state: str = "new",
             validation_error: str | None = None) -> dict:
    """Give a reason and original evidence links for a conservative state."""
    url = issue.get("html_url")
    if not isinstance(url, str) or not ISSUE_URL.fullmatch(url):
        raise ValueError("Missing canonical issue URL")
    if issue.get("state") not in {"open", "closed"}:
        raise ValueError("Unknown issue state")
    if not isinstance(comments, list):
        raise ValueError("Invalid issue comments")
    if feedback_state not in {"new", "reviewed", "proposal_prepared", "published",
                              "response_received", "resolved", "dismissed"}:
        raise ValueError("Unknown feedback state")
    if actor is not None and not re.fullmatch(r"[A-Za-z\d](?:[A-Za-z\d-]{0,37}[A-Za-z\d])?", actor):
        raise ValueError("Invalid GitHub account")
    if any(not isinstance(comment, dict) for comment in comments):
        raise ValueError("Invalid issue comment")

    def verdict(status: str, reason: str, evidence: list[str] | None = None) -> dict:
        return {"status": status, "reason": reason, "evidence_urls": evidence or [url]}

    if issue["state"] == "closed":
        return verdict("closed_or_resolved", "github_issue_closed_not_proof_of_fix")
    if feedback_state == "resolved":
        return verdict("closed_or_resolved", "human_feedback_resolved_not_github_verified")
    if feedback_state == "dismissed":
        return verdict("dismissed", "human_feedback_dismissed")
    if feedback_state in FOLLOW_UP_FEEDBACK:
        return verdict("follow_up", "prior_human_feedback")

    user = (actor or "").casefold()
    creator = (issue.get("user") or {}).get("login")
    if actor and isinstance(creator, str) and creator.casefold() == user:
        return verdict("follow_up", "actor_created_issue")
    for comment in comments:
        commenter = (comment.get("user") or {}).get("login")
        if actor and isinstance(commenter, str) and commenter.casefold() == user:
            evidence = comment.get("html_url")
            return verdict("follow_up", "actor_commented",
                           [evidence] if isinstance(evidence, str) else [url])

    assigned = [
        item.get("login") for item in issue.get("assignees", [])
        if isinstance(item, dict) and isinstance(item.get("login"), str)
    ]
    if actor and user in {login.casefold() for login in assigned}:
        return verdict("follow_up", "actor_assigned")

    if linked_prs is not None:
        if not isinstance(linked_prs, list):
            raise ValueError("Invalid linked PRs")
        for pr in linked_prs:
            if not isinstance(pr, dict) or pr.get("state") not in {"open", "closed"}:
                raise ValueError("Invalid linked PR status")
            if not isinstance(pr.get("url"), str) or not pr["url"].startswith("https://github.com/"):
                raise ValueError("Invalid linked PR evidence")
            if actor and isinstance(pr.get("author"), str) and pr["author"].casefold() == user:
                return verdict("follow_up", "actor_cross_referenced_pr", [pr["url"]])

    if validation_error or linked_prs is None:
        return verdict("needs_review", "pr_context_unavailable")
    open_prs = [pr["url"] for pr in linked_prs if pr["state"] == "open"]
    if open_prs:
        return verdict("in_progress", "open_cross_referenced_pr_not_proof_of_fix", open_prs)
    if linked_prs:
        return verdict("needs_review", "closed_cross_referenced_pr_not_proof_of_fix",
                       [pr["url"] for pr in linked_prs])
    if assigned:
        return verdict("in_progress", "issue_assigned_activity_unconfirmed")
    return verdict("new", "open_unassigned_no_observed_actor_or_pr_activity")
