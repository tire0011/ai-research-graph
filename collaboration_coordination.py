"""Read-only public coordination evidence for collaboration-matcher suggestions.

Shared GitHub participants/links mean existing public context. Lack of such
evidence NEVER proves two teams are not already collaborating elsewhere.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

from opportunity_discovery import get_json

API = "https://api.github.com/repos"
MAX_COMMENTS = 100
ID = re.compile(r"^github:([\w.-]+/[\w.-]+)#([1-9]\d*)$")
LOGIN = re.compile(r"^[A-Za-z\d](?:[A-Za-z\d-]{0,37}[A-Za-z\d])?$")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def identity(item):
    match = ID.fullmatch(item.get("id", ""))
    if not match or match.group(1) != item.get("repo") or int(match.group(2)) != item.get("number"):
        raise ValueError("Invalid matcher source identity")
    if item.get("kind") not in ("issue", "pull_request"):
        raise ValueError("Invalid item kind")
    return match.group(1), int(match.group(2))


def assert_same(item, data):
    repo, num = identity(item)
    url = f"https://github.com/{repo}/{'pull' if item['kind'] == 'pull_request' else 'issues'}/{num}"
    if (data.get("number") != num or data.get("html_url") != url
            or data.get("state") != item["state"] or data.get("updated_at") != item["updated_at"]
            or digest(data.get("title") or "") != item["title_sha256"]
            or digest(data.get("body") or "") != item["body_sha256"]
            or ("pull_request" in data) != (item["kind"] == "pull_request")):
        raise ValueError("Source changed while checking public coordination: " + url)


def people(data, comments):
    users = {}
    def add(login, role, url):
        if not isinstance(login, str) or not LOGIN.fullmatch(login):
            return
        if login.casefold().endswith("-bot"):
            return
        x = users.setdefault(login.casefold(), {"login": login, "roles": set(), "urls": set()})
        x["roles"].add(role)
        x["urls"].add(url)
    issue_url = data["html_url"]
    add((data.get("user") or {}).get("login"), "author", issue_url)
    for x in data.get("assignees") or []:
        if isinstance(x, dict):
            add(x.get("login"), "assignee", issue_url)
    for comment in comments:
        add((comment.get("user") or {}).get("login"), "commenter", comment["html_url"])
    return users


def get_context(item, fetch=get_json):
    repo, num = identity(item)
    api = f"{API}/{repo}/issues/{num}"
    first = fetch(api)
    assert_same(item, first)
    count = first.get("comments")
    if type(count) is not int or not 0 <= count <= MAX_COMMENTS:
        raise ValueError("Cannot check all comments for " + api)
    comments = []
    if count:
        comments = fetch(f"{api}/comments?per_page=100&page=1")
        if not isinstance(comments, list) or len(comments) != count:
            raise ValueError("Incomplete GitHub comment list: " + api)
        for comment in comments:
            if (not isinstance(comment, dict)
                    or not isinstance(comment.get("body"), (str, type(None)))
                    or not comment.get("html_url", "").startswith(item["url"] + "#issuecomment-")):
                raise ValueError("Invalid GitHub comment: " + api)
    second = fetch(api)
    assert_same(item, second)
    if second.get("comments") != count:
        raise ValueError("Comments changed while checking " + api)
    return {
        "item": item, "people": people(first, comments), "comment_count": count,
        "texts": [(item["url"], first.get("body") or "")]
                 + [(c["html_url"], c.get("body") or "") for c in comments],
    }


def reference(text, item, direct):
    repo, num = identity(item)
    if direct:
        patterns = [
            rf"https://github\.com/{re.escape(repo)}/(?:issues|pull)/{num}(?!\d)",
            rf"(?<![\w./-]){re.escape(repo)}#{num}(?!\d)",
        ]
    else:
        patterns = [rf"https://github\.com/{re.escape(repo)}(?:/|(?=[\s)>#?]|$))"]
    return any(re.search(p, text, re.I) for p in patterns)


def assess(card, context):
    a, b = context[card["source_id"]], context[card["target_id"]]
    common = sorted(set(a["people"]) & set(b["people"]))
    shared = [
        {"login": a["people"][name]["login"],
         "source_roles": sorted(a["people"][name]["roles"]),
         "target_roles": sorted(b["people"][name]["roles"]),
         "source_urls": sorted(a["people"][name]["urls"]),
         "target_urls": sorted(b["people"][name]["urls"])}
        for name in common
    ]
    refs = []
    for src, target in ((a, b), (b, a)):
        for url, text in src["texts"]:
            direct = reference(text, target["item"], True)
            if direct or reference(text, target["item"], False):
                refs.append({
                    "source_url": url, "target_url":
                        target["item"]["url"] if direct else
                        f"https://github.com/{target['item']['repo']}",
                    "type": "direct_task_link" if direct else "repository_link",
                    "text_sha256": digest(text),
                })
    if any(x["type"] == "direct_task_link" for x in refs):
        signal = "direct_task_link"
    elif shared:
        signal = "shared_public_participants"
    elif refs:
        signal = "same_repository_mentioned"
    else:
        signal = "no_direct_public_link_observed"
    return {
        "id": card["id"], "source": card["source"]["url"], "target": card["target"]["url"],
        "technical_terms": [x["term"] for x in card["matched_terms"]],
        "public_coordination_signal": signal,
        "shared_people": shared, "references": refs,
        "comments_source": a["comment_count"], "comments_target": b["comment_count"],
        "new_collaboration_confirmed": False, "requires_human_review": True,
    }


def build(matches, fetch=get_json):
    cards = matches.get("suggestions")
    if not isinstance(cards, list) or len(cards) > 100:
        raise ValueError("Invalid matcher shortlist")
    items = {}
    for card in cards:
        for role, key in (("source", "source_id"), ("target", "target_id")):
            item = card[role]
            identity(item)
            if item["id"] != card[key]:
                raise ValueError("Mismatched matcher source ID")
            if item["id"] in items and items[item["id"]] != item:
                raise ValueError("Conflicting repeated matcher metadata")
            items[item["id"]] = item
    contexts = {key: get_context(item, fetch) for key, item in sorted(items.items())}
    pairs = [assess(card, contexts) for card in cards]
    kinds = ("direct_task_link", "shared_public_participants",
             "same_repository_mentioned", "no_direct_public_link_observed")
    return {
        "schema": 1, "status": "public_evidence_only",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_matcher_run": matches.get("generated_at_utc"),
        "source_items_rechecked": len(items), "pairs_checked": len(pairs),
        "comments_read": sum(c["comment_count"] for c in contexts.values()),
        "counts": {k: sum(p["public_coordination_signal"] == k for p in pairs) for k in kinds},
        "pairs": pairs,
        "limitations": "Inspects only public GitHub authors, assignees, issue comments and direct links. "
                       "No PR code review comments, private channels, Mattermost, team memberships, "
                       "offline discussions or actual task reuse verification. Shared people and links "
                       "are evidence of context, not proof of successful collaboration. "
                       "No public link is not evidence of a new collaboration. No external posts.",
    }


def markdown(result):
    c = result["counts"]
    lines = ["# Collaboration Matcher — public coordination context", "",
             "**No outreach. No automatic assertion of new collaboration.**", "",
             f"{result['pairs_checked']} shortlisted pairs, "
             f"{result['source_items_rechecked']} original tasks rechecked, "
             f"{result['comments_read']} comments inspected.", "",
             f"Direct task links: {c['direct_task_link']}; "
             f"shared participants: {c['shared_public_participants']}; "
             f"broader repo links: {c['same_repository_mentioned']}; "
             f"no directly visible link: {c['no_direct_public_link_observed']}.", "",
             "**No directly visible link** is *unknown*, not proof of novel collaboration.", ""]
    for i, row in enumerate(result["pairs"], 1):
        lines += [
            f"## {i}. [Active task]({row['source']}) ↔ [Prior task]({row['target']})", "",
            f"- Observation: {row['public_coordination_signal']}",
            f"- Technical terms: {', '.join(row['technical_terms']) or 'none'}",
            f"- Public participants in both: "
            f"{', '.join('@'+p['login'] for p in row['shared_people']) or 'none found'}",
            f"- Issue comments inspected: {row['comments_source']} / {row['comments_target']}",
        ]
        for ref in row["references"][:4]:
            lines.append(f"- [{ref['type']}]({ref['source_url']}) to {ref['target_url']} "
                         f"(source SHA256 {ref['text_sha256']})")
        lines += ["- Next: manually check relevance and whether these people already cooperate.", ""]
    lines += ["## Limitations", "", result["limitations"], ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matches", default="results/collaboration_matches.json")
    parser.add_argument("--output", default="results")
    args = parser.parse_args(argv)
    try:
        matches = json.loads(Path(args.matches).read_text(encoding="utf-8"))
        result = build(matches)
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=True)
        (output / "collaboration_coordination.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (output / "COLLABORATION_COORDINATION.md").write_text(
            markdown(result), encoding="utf-8")
        print(f"Coordination: {result['pairs_checked']} pairs; "
              f"{result['source_items_rechecked']} original sources rechecked")
        return 0
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Coordination audit failed before publishing: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
