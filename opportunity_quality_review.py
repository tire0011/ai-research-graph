"""Inspectable, source-pinned human review of opportunity discovery.

An open issue or lexical match is never evidence that a maintainer is inviting
outside contributions. Reviews are editorial and expire on source updates.
This code deliberately does not learn weights from the small reviewed cohort.
"""

from __future__ import annotations

import re
import urllib.error
from collections import Counter

URL = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/issues/[1-9]\d*$")
VERDICT = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
RUN_URL = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/actions/runs/[1-9]\d*$")

SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[\w.-]+/[\w.-]+$")


def review_rows(ledger: dict) -> list[dict]:
    """Historical comparison remains frozen; later cohorts are additive."""
    rows = list(ledger["reviews"])
    for cohort in ledger.get("additional_cohorts", []):
        rows.extend(cohort["reviews"])
    return rows


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
    original = {item.get("issue_url") for item in reviews if isinstance(item, dict)}
    if original != set(graph) | set(baseline):
        raise ValueError("Original comparison rows changed or incomplete")

    cohorts = ledger.get("additional_cohorts", [])
    if not isinstance(cohorts, list) or len(cohorts) > 20:
        raise ValueError("Invalid number of additional review cohorts")
    for cohort in cohorts:
        if (not isinstance(cohort, dict)
                or not isinstance(cohort.get("run_url"), str)
                or not RUN_URL.fullmatch(cohort["run_url"])
                or not isinstance(cohort.get("description"), str)
                or not cohort["description"]
                or not isinstance(cohort.get("review_date"), str)
                or not isinstance(cohort.get("reviews"), list)
                or not 1 <= len(cohort["reviews"]) <= 25):
            raise ValueError("Invalid additional review cohort")

    seen = set()
    for item in review_rows(ledger):
        if not isinstance(item, dict):
            raise ValueError("Invalid manual review row")
        url = item.get("issue_url")
        if not isinstance(url, str) or not URL.fullmatch(url) or url in seen:
            raise ValueError("Invalid or duplicate reviewed issue")
        seen.add(url)
        verdict = item.get("verdict")
        tier = item.get("contribution_fit_tier")
        if (not isinstance(verdict, str) or not VERDICT.fullmatch(verdict)
                or type(tier) is not int or not 0 <= tier <= 3):
            raise ValueError("Unrecognized review classification")
        if tier == 3 and verdict != "maintainer_confirmed_contribution":
            raise ValueError("Tier 3 requires explicit maintainer confirmation")
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


    rechecks = ledger.get("code_rechecks", [])
    if not isinstance(rechecks, list) or len(rechecks) > 10:
        raise ValueError("Invalid number of source-code rechecks")
    rechecked = set()
    for correction in rechecks:
        if not isinstance(correction, dict):
            raise ValueError("Invalid code recheck")
        url = correction.get("issue_url")
        if not isinstance(url, str) or url not in seen or url in rechecked:
            raise ValueError("Code recheck must reference a unique reviewed issue")
        rechecked.add(url)
        repo, sha = correction.get("code_repo"), correction.get("code_head_sha")
        tier = correction.get("contribution_fit_tier")
        verdict = correction.get("verdict")
        evidence = correction.get("evidence_urls")
        if (not isinstance(repo, str) or not REPO.fullmatch(repo)
                or not isinstance(sha, str) or not SHA.fullmatch(sha)
                or not isinstance(verdict, str) or not VERDICT.fullmatch(verdict)
                or type(tier) is not int or tier not in (0, 1, 2)
                or not isinstance(evidence, list) or url not in evidence
                or not any(f"/blob/{sha}/" in link for link in evidence
                           if isinstance(link, str))
                or not correction.get("explanation")
                or not isinstance(correction.get("issue_updated_at"), str)
                or type(correction.get("issue_comment_count")) is not int):
            raise ValueError("Code recheck missing source evidence or valid tier")


def fetch_code_heads(ledger: dict, fetch) -> dict[str, str]:
    """Fetch default-branch HEAD for code-pinned reviews; fail closed."""
    validate(ledger)
    found = {}
    for row in ledger.get("code_rechecks", []):
        repo = row["code_repo"]
        if repo in found:
            continue
        try:
            commits = fetch(f"https://api.github.com/repos/{repo}/commits?per_page=1")
            if (isinstance(commits, list) and commits
                    and isinstance(commits[0], dict)
                    and isinstance(commits[0].get("sha"), str)
                    and SHA.fullmatch(commits[0]["sha"])):
                found[repo] = commits[0]["sha"]
        except (ValueError, TypeError, KeyError, OSError, urllib.error.URLError, TimeoutError):
            pass
    return found


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


def annotate(discovery: dict, ledger: dict, *, code_heads=None) -> dict:
    """Add transparent review states; keep original discovery untouched.

    Historical manual labels apply only while GitHub's issue updated_at is
    unchanged and the issue still has a verified new state. Otherwise mark
    stale and abstain. Non-reviewed new issues remain unassessed, never ready.
    """
    validate(ledger)
    by_url = {row["issue_url"]: row for row in review_rows(ledger)}
    corrections = {row["issue_url"]: row for row in ledger.get("code_rechecks", [])}
    code_heads = {} if code_heads is None else code_heads
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
        correction = corrections.get(url)
        if correction and status == "new":
            if (card["updated_at"] != correction["issue_updated_at"]
                    or card.get("comment_count") != correction["issue_comment_count"]):
                quality = {"status": "stale_review", "tier": None,
                           "reason": "issue_changed_after_code_recheck",
                           "evidence_urls": correction["evidence_urls"]}
            elif code_heads.get(correction["code_repo"]) != correction["code_head_sha"]:
                quality = {"status": "code_revision_unverified", "tier": None,
                           "reason": "default_branch_changed_or_code_check_failed",
                           "evidence_urls": correction["evidence_urls"]}
            else:
                quality = {"status": "manual_code_review_current",
                           "tier": correction["contribution_fit_tier"],
                           "verdict": correction["verdict"],
                           "reason": correction["explanation"],
                           "evidence_urls": correction["evidence_urls"]}
        card["quality_review"] = quality
        cards.append(card)

    plausible = [row for row in cards
                 if row["state"]["status"] == "new"
                 and row["quality_review"]["status"] in {"manual_review_current",
                                                          "manual_code_review_current"}
                 and row["quality_review"]["tier"] >= 2][:5]
    unreviewed = [row for row in cards
                  if row["state"]["status"] == "new"
                  and row["quality_review"]["status"] in {"unreviewed", "stale_review",
                                                         "code_revision_unverified"}]
    return {
        "schema": 1,
        "comparison": frozen_comparison(ledger),
        "source_run": ledger["frozen_run_url"],
        "additional_review_cohorts": len(ledger.get("additional_cohorts", [])),
        "code_rechecks": len(ledger.get("code_rechecks", [])),
        "verified_code_heads": code_heads,
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
            "Code-dependent corrections require a matching live source repository HEAD.",
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
