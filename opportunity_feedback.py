"""Append-only, human-entered opportunity feedback; no GitHub write actions."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

STATES = ("reviewed", "proposal_prepared", "published", "response_received", "resolved", "dismissed")
URL = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/(?:issues|pull)/\d+(?:#\S+)?$")
ID = re.compile(r"^github:OpenEuroLLM/Taskboard#\d+:(?:reported_memory_issue|performance_mention|declared_dependency)$")
LOGIN = re.compile(r"^[A-Za-z\d](?:[A-Za-z\d-]{0,37}[A-Za-z\d])?$")
ALLOWED = {
    "new": {"reviewed", "dismissed"},
    "reviewed": {"proposal_prepared", "dismissed"},
    "proposal_prepared": {"published", "reviewed", "dismissed"},
    "published": {"response_received", "dismissed"},
    "response_received": {"resolved", "proposal_prepared", "dismissed"},
    "resolved": set(), "dismissed": {"reviewed"},
}


def read_feedback(path: Path) -> dict[str, str]:
    """Replay all events; preserve decisions across changing weekly samples."""
    state: dict[str, str] = {}
    if not path.exists():
        return state
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"Blank feedback log line {n}")
        entry = json.loads(line)
        key, new = entry["opportunity_id"], entry["status"]
        if not ID.fullmatch(key) or new not in STATES:
            raise ValueError(f"Invalid feedback event on line {n}")
        if new not in ALLOWED.get(state.get(key, "new"), set()):
            raise ValueError(f"Invalid feedback transition on line {n}")
        if not isinstance(entry.get("actor"), str) or not LOGIN.fullmatch(entry["actor"]):
            raise ValueError(f"Invalid reviewer on line {n}")
        if new in ("published", "response_received", "resolved") and not URL.fullmatch(entry.get("reference_url", "")):
            raise ValueError(f"A GitHub issue/PR reference is required on line {n}")
        state[key] = new
    return state


def record(path: Path, opportunity_id: str, status: str, actor: str, reference_url="", note=""):
    state = read_feedback(path)
    if not ID.fullmatch(opportunity_id) or status not in ALLOWED.get(state.get(opportunity_id, "new"), set()):
        raise ValueError("Invalid opportunity ID or state transition")
    if not LOGIN.fullmatch(actor):
        raise ValueError("Invalid GitHub reviewer name")
    if status in ("published", "response_received", "resolved") and not URL.fullmatch(reference_url):
        raise ValueError("Published, response and resolved events need an explicit GitHub reference")
    if reference_url and not URL.fullmatch(reference_url):
        raise ValueError("Reference must link to a GitHub issue or pull request")
    if len(note) > 1000 or "\n" in note or "\r" in note:
        raise ValueError("Note must be one line and at most 1000 characters")
    event = {"timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
             "opportunity_id": opportunity_id, "status": status, "actor": actor,
             "reference_url": reference_url, "note": note,
             "evidence_status": "human_entered_not_verified_by_github"}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", default="results/opportunity_feedback.jsonl")
    parser.add_argument("--issue-id", required=True)
    parser.add_argument("--status", required=True, choices=STATES)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--reference-url", default="")
    parser.add_argument("--note", default="")
    args = parser.parse_args(argv)
    try:
        event = record(Path(args.log), args.issue_id, args.status, args.actor, args.reference_url, args.note)
        print(f"Appended human feedback: {event['opportunity_id']} -> {event['status']}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Feedback not recorded: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
