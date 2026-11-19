"""Exploratory cross-organization phrase bridge, separate from the technical matcher.

This is a non-blinded discovery aid. Shared phrases are not proof of a useful
handoff, a missing collaboration, or a relationship between the people involved.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import collaboration_matcher as cm

WORD = re.compile(r"[a-z][a-z0-9]*")
STRUCTURAL = {
    "a", "an", "and", "as", "at", "be", "by", "for", "from", "in", "into",
    "is", "it", "of", "on", "or", "our", "the", "their", "this", "to",
    "via", "was", "we", "were", "with", "without", "your",
}


def singular(word: str) -> str:
    """Simple, explicit inflection normalization; not a linguistic stemmer."""
    if len(word) >= 4 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def phrase_spans(text: str):
    """Yield normalized phrase and exact original span using one tokenizer."""
    for clause in re.finditer(r"[^.!?;\n]+", text):
        words = list(WORD.finditer(clause.group().casefold()))
        for a, b in zip(words, words[1:]):
            first, second = singular(a.group()), singular(b.group())
            if (len(first) < 2 or len(second) < 2
                    or first in STRUCTURAL or second in STRUCTURAL
                    or (first in cm.STOP and second in cm.STOP)):
                continue
            yield f"{first} {second}", clause.start() + a.start(), clause.start() + b.end()


def phrases(text: str) -> set[str]:
    """Extract literal adjacent two-word phrases, including domain nouns in cm.STOP."""
    return {p for p, _, _ in phrase_spans(text)}


def phrase_context(issue: dict, phrase: str) -> dict:
    for field in ("title", "body"):
        value = issue[field]
        for key, start, end in phrase_spans(value):
            if key == phrase:
                return {"field": field, "excerpt": " ".join(
                    value[max(0, start - 55):end + 55].split())[:160]}
    raise ValueError(f"No literal original-text evidence for phrase: {phrase}")


def rank(items: list[dict], config: dict, now: dt.datetime) -> tuple[list[dict], dict]:
    maxchars = config["max_body_chars_for_matching"]
    prepared = {
        x["id"]: {
            "title": phrases(x["title"]),
            "all": phrases(x["title"]) | phrases(x["body"][:maxchars]),
            "tokens": cm.tokens(x["title"] + " " + x["body"][:maxchars]),
            "truncated": len(x["body"]) > maxchars,
        } for x in items
    }
    counts = Counter(p for item in prepared.values() for p in item["all"])
    words = Counter(t for item in prepared.values() for t in item["tokens"])
    n = len(items)
    phrase_idf = {p: 1 + math.log((n + 1) / (freq + 1)) for p, freq in counts.items()}
    word_idf = {t: 1 + math.log((n + 1) / (freq + 1)) for t, freq in words.items()}
    active = cm.candidate_documents(items, config, now)
    cards = []
    for source in active:
        src = prepared[source["id"]]
        pool = []
        baseline = []
        for target in items:
            if (source["repo"].split("/")[0].casefold() == target["repo"].split("/")[0].casefold()
                    or cm.date(target["created_at"]) > cm.date(source["created_at"])):
                continue
            tgt = prepared[target["id"]]
            common_tokens = src["tokens"] & tgt["tokens"]
            if common_tokens:
                baseline.append((sum(word_idf[t] for t in common_tokens), target["id"]))
            # Source-title anchor: a concrete named work product, not arbitrary
            # overlap buried in two long descriptions. No hand-picked issue IDs.
            shared = src["title"] & tgt["all"]
            if not shared:
                continue
            candidates = [p for p in shared if phrase_idf[p] >= 2.5]
            if not candidates:
                continue
            best = max(candidates, key=lambda p: (
                phrase_idf[p] * (3.2 if p in tgt["title"] else 2.1), p))
            score = phrase_idf[best] * (3.2 if best in tgt["title"] else 2.1)
            if score < config["min_score"]:
                continue
            pool.append((score, target, best))
        baseline.sort(key=lambda entry: (-entry[0], entry[1]))
        baseline_top1 = baseline[0][1] if baseline else None
        pool.sort(key=lambda entry: (-entry[0], entry[1]["id"]))
        for score, target, phrase in pool[:config["max_suggestions_per_source"]]:
            cards.append({
                "id": f"phrase:{source['id']}->{target['id']}",
                "source_id": source["id"], "target_id": target["id"],
                "source": cm.report_issue(source), "target": cm.report_issue(target),
                "phrase": phrase, "score": round(score, 3),
                "source_evidence": phrase_context(source, phrase),
                "target_evidence": phrase_context(target, phrase),
                "baseline_fulltext_top1_id": baseline_top1,
                "same_as_fulltext_baseline_top1": target["id"] == baseline_top1,
                "ranking_text_truncated": (src["truncated"] or
                                            prepared[target["id"]]["truncated"]),
                "status": "unreviewed_phrase_overlap", "coordination": "unknown",
                "outreach": "none",
            })
    cards.sort(key=lambda c: (-c["score"], c["source_id"], c["target_id"]))
    return cards[:config["max_suggestions"]], {"active_sources": len(active), "items": n}


def build(config, fetch=cm.get_json, now=None):
    cm.validate(config)
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Expected timezone-aware current timestamp")
    items = [item for repo in config["repositories"]
             for item in cm.fetch_issues(repo, config, fetch=fetch)]
    cards, totals = rank(items, config, now)
    rechecked = cm.verify_shortlist(cards, {x["id"]: x for x in items}, fetch=fetch)
    return {
        "schema": 1, "status": "exploratory_not_blinded_review_only",
        "generated_at_utc": now.isoformat(), "repositories": config["repositories"],
        "items_indexed": totals["items"], "active_sources": totals["active_sources"],
        "original_sources_rechecked": rechecked, "suggestions": cards,
        "suggestions_count": len(cards), "outreach": "none",
        "limitations": (
            "Two-word lexical phrases with source-title anchors are an exploratory recall "
            "extension, not semantic understanding or proof of complementary needs. "
            "The candidate was found manually before this method was developed: "
            "no holdout accuracy, discovery novelty, or improvement is claimed. "
            "Same-input lexical baseline is a comparator, not independent human judgment. "
            "Public issue titles/bodies only; comments, private coordination, "
            "author identities and acceptance criteria need human review. No outreach."
        ),
    }


def markdown(result):
    lines = [
        "# Experimental concept-phrase bridge — human review only", "",
        f"{result['suggestions_count']} candidates from {result['items_indexed']} issues/PRs "
        f"({result['active_sources']} recent active sources); "
        f"{result['original_sources_rechecked']} original sources rechecked.", "",
        "**Not a measured discovery success.** A common phrase is not a demonstrated "
        "technical handoff, and no visible link would not prove absent collaboration.", "",
    ]
    for i, c in enumerate(result["suggestions"], 1):
        s, t = c["source"], c["target"]
        lines.extend([
            f"## {i}. [{s['title']}]({s['url']}) ↔ [{t['title']}]({t['url']})", "",
            f"- Phrase: `{c['phrase']}`; heuristic score: {c['score']}",
            f"- Source: {c['source_evidence']['field']} — «{c['source_evidence']['excerpt']}»",
            f"- Target: {c['target_evidence']['field']} — «{c['target_evidence']['excerpt']}»",
            f"- Exact source body hashes: `{s['body_sha256']}`, `{t['body_sha256']}`",
            f"- Full-text baseline top-1: `{c['baseline_fulltext_top1_id']}`; "
            f"same: {c['same_as_fulltext_baseline_top1']}",
            "- Human verification: inspect tasks, actual code, people and public coordination.", "",
        ])
    lines.extend(["## Limitations", "", result["limitations"], ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default="collaboration_sources.json")
    parser.add_argument("--output", default="results")
    args = parser.parse_args(argv)
    try:
        config = json.loads(Path(args.sources).read_text(encoding="utf-8"))
        result = build(config)
        folder = Path(args.output)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "concept_phrase_bridges.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (folder / "CONCEPT_PHRASE_BRIDGES.md").write_text(markdown(result), encoding="utf-8")
        print(f"Phrase bridges: {result['suggestions_count']} review-only candidates")
        return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f"Phrase bridge aborted: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
