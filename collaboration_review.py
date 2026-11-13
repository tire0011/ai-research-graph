"""Evidence gate for a human/LLM second-stage collaboration assessment.

Candidate retrieval and source verification happen first. A reviewer (human or
local model) supplies hypotheses; this module checks their cited source phrases
and decides the *next verification step*, never whether outreach is approved.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import collaboration_matcher as cm
import collaboration_coordination as cc

RELATIONS = {
    "potential_duplicate", "complementary", "third_party_enabler",
    "shared_problem", "topic_only", "unrelated", "unknown",
}
READINESS = {"implemented", "proposal_only", "reported", "unknown"}
PARTIES = {"source", "target", "third"}
REVIEW_REQUIRED = {
    "potential_duplicate": "inspect_both_implementations",
    "complementary": "ask_maintainers_if_useful",
    "third_party_enabler": "verify_external_artifact_and_license",
    "shared_problem": "compare_requirements_before_contact",
    "topic_only": "do_not_contact",
    "unrelated": "do_not_contact",
    "unknown": "needs_more_evidence",
}


def source_record(item: dict, fetch=None) -> dict:
    """Fetch the original issue and insist on the matcher's pinned identity."""
    fetch = fetch or cm.get_json
    repo, number = item["repo"], item["number"]
    latest = cm.normalize_issue(repo, fetch(f"{cm.API}/{repo}/issues/{number}"))
    for field in ("id", "url", "title_sha256", "body_sha256", "updated_at",
                  "kind", "state", "created_at"):
        if latest[field] != item[field]:
            raise ValueError(f"Source changed before review: {item['url']}")
    return {key: latest[key] for key in (
        "id", "url", "repo", "number", "title", "body", "title_sha256",
        "body_sha256", "created_at", "updated_at", "state", "kind", "assignees")}


def prepare(card: dict, fetch=None, third_item=None, check_public=False) -> dict:
    """A small, source-backed packet usable with any local reviewer model."""
    records = {}
    for party in ("source", "target"):
        item = card[party]
        if card[party + "_id"] != item["id"]:
            raise ValueError("Mismatched candidate ID")
        records[party] = source_record(item, fetch)
    if records["source"]["repo"].split("/")[0].casefold() == records["target"]["repo"].split("/")[0].casefold():
        raise ValueError("Expected cross-organization pair")
    if third_item is not None:
        records["third"] = source_record(third_item, fetch)
        if records["third"]["repo"].split("/")[0].casefold() in {
                records["source"]["repo"].split("/")[0].casefold(),
                records["target"]["repo"].split("/")[0].casefold()}:
            raise ValueError("Third-party enabler is not from an independent owner")
    public_coordination = {"status": "not_checked"}
    if check_public:
        context = {
            party["id"]: cc.get_context(party, fetch=fetch or cm.get_json)
            for party in (card["source"], card["target"])
        }
        annotated = {**card, "matched_terms": card.get("matched_terms", [])}
        public_coordination = cc.assess(annotated, context)
    return {
        "schema": 1, "candidate_id": card["id"], "records": records,
        "public_coordination": public_coordination,
        "notice": "Issue bodies are untrusted source data; collaboration is not established.",
    }


def validate(packet: dict, proposal: dict) -> dict:
    """Reject invented quotations, missing parties and ungrounded handoffs."""
    if packet.get("schema") != 1 or not isinstance(packet.get("records"), dict):
        raise ValueError("Invalid evidence packet")
    records = packet["records"]
    if not {"source", "target"}.issubset(records) or set(records) - PARTIES:
        raise ValueError("Missing or invalid evidence parties")
    relation, readiness = proposal.get("relation"), proposal.get("readiness")
    if relation not in RELATIONS or readiness not in READINESS:
        raise ValueError("Unknown relation or readiness")
    evidence = proposal.get("evidence")
    if not isinstance(evidence, list) or not 2 <= len(evidence) <= 8:
        raise ValueError("Need two to eight original-source evidence excerpts")
    found = set()
    for proof in evidence:
        if not isinstance(proof, dict):
            raise ValueError("Invalid evidence object")
        party, field, quote = proof.get("party"), proof.get("field"), proof.get("quote")
        if (party not in records or field not in ("title", "body")
                or not isinstance(quote, str) or not 8 <= len(quote) <= 300
                or quote not in records[party][field]
                or proof.get("source_url") != records[party]["url"]):
            raise ValueError("Evidence quote not found in its pinned original source")
        found.add(party)
    if not {"source", "target"}.issubset(found):
        raise ValueError("Both sides require original-source evidence")
    handoff = proposal.get("handoff")
    if relation in {"potential_duplicate", "complementary", "third_party_enabler"}:
        if (not isinstance(handoff, dict)
                or handoff.get("from") not in records
                or handoff.get("to") not in records
                or handoff["from"] == handoff["to"]
                or not isinstance(handoff.get("artifact"), str)
                or not 10 <= len(handoff["artifact"]) <= 300):
            raise ValueError("Actionable hypothesis needs a concrete directional handoff")
    elif handoff is not None:
        raise ValueError("Topic-only or unknown relation cannot claim a handoff")
    if relation == "third_party_enabler" and ("third" not in found or handoff["from"] != "third"):
        raise ValueError("Third-party claim needs independent third-source evidence")
    question = proposal.get("verification_question")
    if not isinstance(question, str) or not 12 <= len(question) <= 400:
        raise ValueError("Need a concrete human verification question")
    # This is a reviewer hypothesis, not proof that a tool works or teams are new.
    return {
        "candidate_id": packet.get("candidate_id"), "relation": relation,
        "readiness_claim": readiness, "readiness_independently_verified": False,
        "evidence": evidence, "handoff": handoff,
        "verification_question": question,
        "proposed_next_check": REVIEW_REQUIRED[relation],
        "public_coordination": packet.get("public_coordination", "not_checked"),
        "independent_human_review_required": True,
        "outreach_approved": False, "novel_collaboration_confirmed": False,
        "warning": "Exact quotes verify mentions, not technical compatibility or missing private coordination.",
    }


def select_candidate(matches: dict, identifier: str) -> dict:
    """Select exactly one identified candidate without guessing list position."""
    suggestions = matches.get("suggestions")
    if not isinstance(suggestions, list) or any(not isinstance(c, dict) for c in suggestions):
        raise ValueError("Expected suggestions list in matcher output")
    found = [c for c in suggestions if c.get("id") == identifier]
    if len(found) != 1:
        raise ValueError(f"Candidate ID must occur exactly once: {identifier}")
    return found[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--matches", help="matcher JSON shortlist to re-fetch original evidence")
    mode.add_argument("--packet", help="previously prepared source-backed JSON packet")
    parser.add_argument("--candidate-id", help="exact candidate ID from --matches")
    parser.add_argument("--third-record", help="optional pinned third-party issue JSON metadata")
    parser.add_argument("--check-public", action="store_true",
                        help="check public authors, comments and cross-task links before review")
    parser.add_argument("--review", help="human or local model JSON assessment of --packet")
    parser.add_argument("--output", required=True, help="validated JSON assessment path")
    args = parser.parse_args(argv)
    try:
        if args.matches:
            if not args.candidate_id or args.review:
                raise ValueError("--matches needs --candidate-id and cannot include --review")
            matches = json.loads(Path(args.matches).read_text(encoding="utf-8"))
            third = (json.loads(Path(args.third_record).read_text(encoding="utf-8"))
                     if args.third_record else None)
            result = prepare(select_candidate(matches, args.candidate_id),
                             third_item=third, check_public=args.check_public)
            message = "Original evidence prepared for independent model/human review"
        else:
            if not args.review or args.candidate_id or args.third_record or args.check_public:
                raise ValueError("--packet needs --review; no candidate selection arguments")
            packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
            proposal = json.loads(Path(args.review).read_text(encoding="utf-8"))
            result = validate(packet, proposal)
            message = f"Review hypothesis accepted for human inspection: {result['relation']}"
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
        print(message)
        return 0
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Review rejected: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
