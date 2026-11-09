"""Convert verified impact evidence into review-only human collaboration proposals.

This is deliberately a bounded triage, not a general impact ranking or a bot.
It never sends messages, creates issues, or infers a measured acceleration.
"""

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path


TRIGGERS = {
    "reported_speedup_pending_validation": ("validate_reported_speedup", "reported, not reproduced"),
    "explicit_upstream_dependency": ("unblock_declared_dependency", "author-declared, not proven blocking"),
    "reported_memory_blocker": ("verify_reported_failure", "commenter-reported, not reproduced"),
}
LOGIN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def build(impact):
    """Fail closed on partial or stale source evidence; never silently rank gaps."""
    cases = impact.get("cases")
    if (impact.get("status") != "completed" or impact.get("verified") != 10 or
            impact.get("selected") != 10 or not isinstance(cases, list) or len(cases) != 10 or
            impact.get("graph_comments_exact") != impact.get("graph_comments_selected")):
        raise ValueError("Impact audit is incomplete or comment evidence differs from sources")
    records = []
    for case in cases:
        if case.get("status") != "evidence_verified" or case.get("graph_status") != "exact_parity":
            raise ValueError(f"Stale or unverified source: {case.get('anchor_id')}")
        kind = case.get("evidence_class")
        if kind not in TRIGGERS or case.get("live_state") != "open":
            continue
        if kind == "explicit_upstream_dependency" and not case.get("declared_dependency", {}).get(
                "graph_contains_author_declared_dependency"):
            continue
        if kind == "reported_memory_blocker" and not case.get("graph_reported_blockers"):
            continue
        if (not SHA256.fullmatch(case.get("source_sha256", "")) or
                not case.get("source_url", "").startswith("https://github.com/")):
            raise ValueError(f"Invalid issue provenance for {case.get('anchor_id')}")
        proof = case.get("evidence") or []
        if not proof or any(not SHA256.fullmatch(e.get("sha256", "")) or
                            not e.get("url", "").startswith("https://github.com/") or
                            not e.get("matched_text") for e in proof):
            raise ValueError(f"Missing source-backed proof for {case.get('anchor_id')}")

        assignees = [login for login in case.get("assignees") or []
                     if isinstance(login, str) and LOGIN.fullmatch(login)]
        author = case.get("issue_author")
        if not assignees and isinstance(author, str) and LOGIN.fullmatch(author):
            contacts, contact_basis = [author], "issue_author_fallback"
        elif assignees:
            contacts, contact_basis = list(dict.fromkeys(assignees)), "github_issue_assignee"
        else:
            contacts, contact_basis = [], "no_public_contact"

        action, claim_scope = TRIGGERS[kind]
        records.append({
            "issue_id": case["anchor_id"], "title": case.get("title") or case["anchor_id"],
            "source_url": case["source_url"], "source_sha256": case["source_sha256"],
            "evidence_class": kind, "opportunity_type": action, "claim_scope": claim_scope,
            "candidate": case["candidate"], "validation_needed": case["next_check"],
            "evidence": [{"url": p["url"], "sha256": p["sha256"],
                          "quoted_phrase": p["matched_text"], "meaning": p["meaning"]} for p in proof],
            "related_dependency": case.get("declared_dependency", {}).get("task_id"),
            "contacts": contacts, "contact_basis": contact_basis,
            "suggested_channel": "existing_github_issue_comment",
            "suggested_question": f"Would a reproducible check help? {case['next_check']}",
            "communication_status": "human_review_required", "sent": False,
        })
    return {"status": "review_only", "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "evidence_snapshot_utc": impact.get("snapshot_utc"),
            "scope": "Three explicit evidence categories within ten purposefully selected Taskboard issues",
            "examined": len(cases), "opportunities": records,
            "limitations": "Not project-wide, not independently measured speedups; no automated outreach"}


def markdown(result):
    lines = ["# Research opportunities for human review", "",
             "**Read-only pilot.** Every finding is derived from the independent ten-issue impact audit. "
             "No GitHub messages, labels or notifications have been sent. "
             "Selection is not a project-wide ranking or a verified acceleration.", "",
             f"Examined **{result['examined']}** purposefully sampled issues; "
             f"**{len(result['opportunities'])}** evidence-triggered proposals.", ""]
    for record in result["opportunities"]:
        lines.extend([f"## [{record['issue_id']}]({record['source_url']}) — {record['title']}", "",
                      f"- Evidence: `{record['evidence_class']}` ({record['claim_scope']}).",
                      f"- Proposed action: {record['candidate']}",
                      f"- Required verification: {record['validation_needed']}",
                      f"- Public contact: {', '.join('@' + login for login in record['contacts']) or 'unavailable'} "
                      f"(`{record['contact_basis']}`; please confirm the appropriate person).",
                      f"- Suggested channel: [existing issue]({record['source_url']}); "
                      "**human approval required before any outreach**.",
                      f"- Draft question for review: {record['suggested_question']}",
                      "- Original-source evidence:"])
        lines.extend(f"  - [{proof['quoted_phrase'].replace(chr(10), ' ')}]({proof['url']}) "
                     f"(SHA256 `{proof['sha256']}`)" for proof in record["evidence"])
        if record["related_dependency"]:
            lines.append(f"- Author-declared upstream task: `{record['related_dependency']}`.")
        lines.append("")
    lines.extend(["## Boundaries", "", result["limitations"],
                  "Source evidence is attributed to issue authors/commenters; its scientific claims remain unverified."])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--impact", default="results/impact_evidence.json")
    parser.add_argument("--output", default="results")
    args = parser.parse_args(argv)
    try:
        study = json.loads(Path(args.impact).read_text(encoding="utf-8"))
        result = build(study)
    except (OSError, KeyError, ValueError, TypeError) as exc:
        print(f"Opportunity detector: source_error ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 1
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "opportunities.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "OPPORTUNITIES.md").write_text(markdown(result), encoding="utf-8")
    print(f"Review proposals: {len(result['opportunities'])} / {result['examined']} source-verified issues")
    return 0


if __name__ == "__main__":
    sys.exit(main())
