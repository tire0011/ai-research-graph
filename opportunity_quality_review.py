"""Inspectable, source-pinned human review of opportunity discovery.

An open issue or lexical match is never evidence that a maintainer is inviting
outside contributions. Reviews are editorial and expire on source updates.
This code deliberately does not learn weights from the small reviewed cohort.
"""

from __future__ import annotations

import re
from collections import Counter

URL = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/issues/[1-9]\d*$")
DECISIONS = {
    "needs_maintainer_direction",
    "existing_solution_offered",
    "maintainer_metadata_request",
    "reporter_has_proposed_fix",
    "experiment_already_queued",
    "needs_implementation_scope",
    "plausible_small_contribution",
    "requires_specialized_resources",
    "maintainer_confirmed_contribution",
}


def validate(ledger: dict) -> None:
    if not isinstance(ledger, dict) or ledger.get("schema") != 1:
        raise ValueError("Unknown quality review schema")
    graph, baseline, reviews = (
        ledger.get("graph_top5"), ledger.get("title_baseline_top5"),
        ledger.get("reviews"),
    )
    if not (isinstance(graph, list) and isinstance(baseline, list)
            and len(graph) == 5 and len(baseline) == 5
            and isinstance(reviews, list)):
        raise ValueError("Expected frozen five-by-five review")
    for group in (graph, baseline):
        if any(not isinstance(url, str) or not URL.fullmatch(url) for url in group):
            raise ValueError("Invalid selection issue URL")
        if len(group) != len(set(group)):
            raise ValueError("Duplicate selection issue URL")
    if len(reviews) != len(set(graph) | set(baseline)):
        raise ValueError("Missing review decisions for frozen union")
    seen = set()
    for item in reviews:
        if not isinstance(item, dict):
            raise ValueError("Invalid manual review row")
        url = item.get("issue_url")
        if not isinstance(url, str) or not URL.fullmatch(url) or url in seen:
            raise ValueError("Invalid or duplicate reviewed issue")
        seen.add(url)
        if (item.get("verdict") not in DECISIONS
                or type(item.get("contribution_fit_tier")) is not int
                or not 0 <= item["contribution_fit_tier"] <= 3):
            raise ValueError("Unrecognized review classification")
        if (not isinstance(item.get("source_updated_at"), str)
                or not item["source_updated_at"].endswith("Z")
                or type(item.get("source_comment_count")) is not int
                or item["source_comment_count"] < 0
                or not item.get("explanation")
                or not isinstance(item.get("evidence_urls"), list)
                or url not in item["evidence_urls"]
                or any(not isinstance(link, str)
                       or not link.startswith("https://github.com/")
                       for link in item["evidence_urls"])):
            raise ValueError("Review missing source evidence or snapshot")
    if seen != (set(graph) | set(baseline)):
        raise ValueError("Review rows do not match frozen input selections")


def frozen_comparison(ledger: dict) -> dict:
    """Descriptive same-pool comparison; labels were reviewed non-blind."""
    validate(ledger)
    by_url = {row["issue_url"]: row for row in ledger["reviews"]}

    def score(urls):
        values = [by_url[url]["contribution_fit_tier"] for url in urls]
        return {
            "reviewed": len(values),
            "plausible_or_better": sum(v >= 2 for v in values),
            "maintainer_confirmed": sum(v == 3 for v in values),
            "needs_clarification_or_less": sum(v < 2 for v in values),
        }

    return {
        "graph_heuristic_top5": score(ledger["graph_top5"]),
        "same_pool_title_only_top5": score(ledger["title_baseline_top5"]),
        "unique_issues_reviewed": len(by_url),
        "method": "one_non_blinded_review_of_same_source_pool_not_a_precision_estimate",
        "claims_of_graph_superiority_supported": False,
        "confirmed_free_contributions": sum(
            row["contribution_fit_tier"] == 3 for row in ledger["reviews"]
        ),
    }


def annotate(discovery: dict, ledger: dict) -> dict:
    """Add transparent review states; keep original discovery untouched.

    Historical manual labels apply only while GitHub's issue updated_at is
    unchanged and the issue still has a verified new state. Otherwise mark
    stale and abstain. Non-reviewed new issues remain unassessed, never ready.
    """
    validate(ledger)
    by_url = {row["issue_url"]: row for row in ledger["reviews"]}
    cards = []
    for item in discovery["all_reviewed"]:
        card = dict(item)
        url = card["issue_url"]
        label = by_url.get(url)
        status = card["state"]["status"]
        if not label:
            quality = {"status": "unreviewed", "tier": None,
                       "reason": "no_manual_actionability_review"}
        elif status != "new":
            quality = {"status": "state_supersedes_review", "tier": None,
                       "reason": "live_github_state_is_not_new"}
        elif (card["updated_at"] != label["source_updated_at"]
              or card.get("comment_count") != label["source_comment_count"]):
            quality = {"status": "stale_review", "tier": None,
                       "reason": "source_changed_since_manual_review",
                       "evidence_urls": label["evidence_urls"]}
        else:
            quality = {
                "status": "manual_review_current",
                "tier": label["contribution_fit_tier"],
                "verdict": label["verdict"],
                "reason": label["explanation"],
                "evidence_urls": label["evidence_urls"],
            }
        card["quality_review"] = quality
        cards.append(card)

    plausible = [row for row in cards
                 if row["state"]["status"] == "new"
                 and row["quality_review"]["status"] == "manual_review_current"
                 and row["quality_review"]["tier"] >= 2][:5]
    unreviewed = [row for row in cards
                  if row["state"]["status"] == "new"
                  and row["quality_review"]["status"] in {"unreviewed", "stale_review"}]
    return {
        "schema": 1,
        "comparison": frozen_comparison(ledger),
        "source_run": ledger["frozen_run_url"],
        "quality_shortlist": plausible,
        "new_needing_human_review": unreviewed[:5],
        "annotated_candidates": cards,
        "review_status_counts": dict(Counter(
            c["quality_review"]["status"] for c in cards)),
        "limitations": [
            "Frozen comparison is unblinded, subjective and limited to eight unique issues.",
            "The title-only baseline shares the same candidate pool; it is NOT a full GitHub search baseline.",
            "No tier-2 record is maintainer-confirmed or proven quick to implement.",
            "Reviews are source-version-bound; changed or missing cases require review again.",
            "Unreviewed tasks must never be described as confirmed actionable.",
        ],
    }


def markdown(result: dict) -> str:
    comp = result["comparison"]
    lines = [
        "# Contribution quality — source-pinned human review", "",
        "**This is a manual, non-blinded pilot, not proof of graph superiority.**",
        f"Frozen discovery: {result['source_run']}", "",
        "| Frozen ranking | Reviewed | Plausible scoped code contributions | Confirmed by maintainers |",
        "| --- | ---: | ---: | ---: |",
    ]
    for key, title in (("graph_heuristic_top5", "Existing heuristic"),
                       ("same_pool_title_only_top5", "Same-pool title baseline")):
        row = comp[key]
        lines.append(f"| {title} | {row['reviewed']} | {row['plausible_or_better']} | "
                     f"{row['maintainer_confirmed']} |")
    lines += ["", "## Manually plausible tasks (still require maintainer approval)", ""]
    if not result["quality_shortlist"]:
        lines.append("None verified as a plausible scoped contribution in the current sampled set.")
    for c in result["quality_shortlist"]:
        lines.append(f"- [{c['repository']}#{c['issue_number']}: {c['title']}]({c['issue_url']})"
                     f" — {c['quality_review']['reason']}")
    lines += ["", "## New tasks not yet independently checked for actionability", ""]
    if not result["new_needing_human_review"]:
        lines.append("None in this bounded sample.")
    for c in result["new_needing_human_review"]:
        lines.append(f"- [{c['repository']}#{c['issue_number']}: {c['title']}]({c['issue_url']})"
                     f" — {c['quality_review']['reason']}")
    lines += ["", "## Review coverage", ""]
    for status, count in sorted(result["review_status_counts"].items()):
        lines.append(f"- {status}: {count}")
    lines += ["", "## Limitations", ""]
    for limitation in result["limitations"]:
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"
