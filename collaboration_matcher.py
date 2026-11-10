"""Cross-organization collaboration matcher — a read-only lexical pilot, not an LLM.

Automatically discover current GitHub issue/PR work and related earlier tasks in
other organizations. Keep a same-input full-text baseline and original evidence.
Candidates require human review; a closed issue/PR does not prove a solved problem.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode

from opportunity_discovery import get_json

API = "https://api.github.com/repos"
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
WORDS = re.compile(r"[a-z][a-z0-9_.+-]{2,}")
STOP = {
    "a", "about", "across", "add", "after", "all", "also", "and", "any",
    "are", "as", "at", "based", "be", "been", "before", "but", "by",
    "can", "change", "changes", "code", "could", "data", "dataset", "datasets",
    "do", "does", "done", "each", "for", "from", "get", "has", "have",
    "how", "if", "in", "into", "is", "it", "its", "make", "model", "models",
    "more", "new", "not", "of", "on", "one", "open", "or", "other", "our",
    "out", "pipeline", "pipelines", "project", "projects", "run", "running",
    "same", "should", "some", "support", "task", "test", "tests", "than",
    "that", "the", "their", "them", "then", "there", "these", "this",
    "through", "to", "tool", "tools", "training", "update", "use", "used",
    "using", "was", "we", "were", "what", "when", "where", "which", "while",
    "with", "work", "would", "you", "your", "issue", "issues", "fix",
    "implementation", "implement", "results", "result", "file", "files",
    "version", "versions", "source", "sources", "text", "evaluation",
    "benchmark", "benchmarks", "performance", "extraction",
}
REWRITES = (
    (re.compile(r"\brobots[\s._-]*txt\b"), "robotstxt"),
    (re.compile(r"\bcommon[\s_-]*crawl\b"), "commoncrawl"),
    (re.compile(r"\blumi[\s_-]*o\b"), "lumio"),
    (re.compile(r"\bopen[\s_-]*lid\b"), "openlid"),
    (re.compile(r"\bglot[\s_-]*lid\b"), "glotlid"),
    (re.compile(r"\bmark[\s_-]*down\b"), "markdown"),
)
MAX_REREADS = 90


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def date(value: str) -> dt.datetime:
    if not isinstance(value, str):
        raise ValueError("Missing GitHub date")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Naive GitHub date")
    return parsed


def tokens(value: str) -> set[str]:
    text = value.casefold()
    for pattern, replacement in REWRITES:
        text = pattern.sub(replacement, text)
    found = set(WORDS.findall(text))
    result = set()
    for word in found:
        if word.endswith("s") and len(word) > 5 and not word.endswith(("ss", "us")):
            word = word[:-1]
        if word not in STOP and len(word) >= 3 and not word.isnumeric():
            result.add(word)
    return result


def validate(config):
    repos = config.get("repositories")
    if (not isinstance(repos, list) or not 2 <= len(repos) <= 15
            or any(not isinstance(r, str) or not REPO.fullmatch(r) for r in repos)
            or len({r.casefold() for r in repos}) != len(repos)
            or len({r.split("/")[0].casefold() for r in repos}) < 2):
        raise ValueError("Invalid or insufficient cross-organization repository registry")
    owners = config.get("source_owners")
    if (not isinstance(owners, list) or not owners
            or any(owner not in {r.split("/")[0] for r in repos} for owner in owners)):
        raise ValueError("Invalid source owner scope")
    expected = {
        "max_pages_per_repo": (1, 20), "page_size": (100, 100),
        "max_body_chars_for_matching": (200, 20000),
        "source_max_age_days": (1, 1000), "max_suggestions": (1, 100),
        "max_suggestions_per_source": (1, 5),
    }
    for key, (lo, hi) in expected.items():
        val = config.get(key)
        if type(val) is not int or not lo <= val <= hi:
            raise ValueError(f"Invalid config limit {key}")
    if (not isinstance(config.get("min_score"), (int, float))
            or not 2 <= config["min_score"] <= 100):
        raise ValueError("Invalid minimum relevance score")


def normalize_issue(repo, row):
    number = row.get("number")
    if type(number) is not int or number < 1:
        raise ValueError(f"Invalid GitHub issue number for {repo}")
    kind = "pull_request" if "pull_request" in row else "issue"
    page = "pull" if kind == "pull_request" else "issues"
    url = f"https://github.com/{repo}/{page}/{number}"
    if (row.get("html_url") != url
            or row.get("state") not in ("open", "closed")
            or not isinstance(row.get("title"), str)
            or not isinstance(row.get("body"), (str, type(None)))
            or not isinstance(row.get("updated_at"), str)):
        raise ValueError(f"Invalid original GitHub issue/PR {repo}#{number}")
    date(row.get("created_at"))
    date(row["updated_at"])
    body = row.get("body") or ""
    people = [a.get("login") for a in row.get("assignees") or []
              if isinstance(a, dict) and isinstance(a.get("login"), str)]
    return {
        "id": f"github:{repo}#{number}", "repo": repo,
        "number": number, "kind": kind, "state": row["state"],
        "url": url, "title": row["title"], "body": body,
        "created_at": row["created_at"], "updated_at": row["updated_at"],
        "title_sha256": hash_text(row["title"]), "body_sha256": hash_text(body),
        "assignees": sorted(set(people)),
    }


def fetch_issues(repo, config, fetch=get_json):
    all_issues = []
    seen = set()
    for page in range(1, config["max_pages_per_repo"] + 1):
        query = urlencode({"state": "all", "per_page": config["page_size"], "page": page})
        batch = fetch(f"{API}/{repo}/issues?{query}")
        if not isinstance(batch, list):
            raise ValueError(f"Invalid GitHub listing from {repo}")
        for row in batch:
            item = normalize_issue(repo, row)
            if item["id"] in seen:
                raise ValueError(f"Duplicate GitHub issue across pages: {item['id']}")
            seen.add(item["id"])
            all_issues.append(item)
        if len(batch) < config["page_size"]:
            break
    else:
        raise ValueError(f"GitHub pagination cap reached for {repo}; refusing a partial inventory")
    return all_issues


def candidate_documents(all_items, config, now):
    age = dt.timedelta(days=config["source_max_age_days"])
    eligible = [x for x in all_items if x["state"] == "open"
                and x["repo"].split("/")[0] in config["source_owners"]
                and (now - age) <= date(x["created_at"]) <= now]
    return sorted(eligible, key=lambda x: (x["repo"], x["number"]))


TERM_FORMS = {
    "robotstxt": r"robots[\s._-]*txt",
    "commoncrawl": r"common[\s_-]*crawl",
    "lumio": r"lumi[\s_-]*o",
    "openlid": r"open[\s_-]*lid",
    "glotlid": r"glot[\s_-]*lid",
    "markdown": r"(?:mark[\s_-]*down|md)",
}


def term_context(issue, term):
    """A literal original-text excerpt with a verifiable source field."""
    expression = TERM_FORMS.get(term, re.escape(term) + r"s?")
    pattern = re.compile(r"(?<![a-z0-9])(?:" + expression + r")(?![a-z0-9])", re.I)
    for field, original in (("title", issue["title"]), ("body", issue["body"])):
        hit = pattern.search(original)
        if hit:
            return {"field": field, "excerpt": " ".join(
                original[max(0, hit.start() - 55):hit.end() + 55].split())[:160]}
    raise ValueError(f"No original phrase supports normalized token '{term}'")


def rank_pairs(items, config, now):
    """Pure same-input lexical baseline and evidence-gated title-aware pilot."""
    maxchars = config["max_body_chars_for_matching"]
    processed = {
        x["id"]: {"title": tokens(x["title"]),
                   "all": tokens(x["title"] + " " + x["body"][:maxchars]),
                   "body_truncated": len(x["body"]) > maxchars}
        for x in items
    }
    frequency = Counter(t for x in items for t in processed[x["id"]]["all"])
    count = len(items)
    idf = {t: 1.0 + math.log((count + 1) / (freq + 1))
           for t, freq in frequency.items()}
    active = candidate_documents(items, config, now)
    all_rankings = {}
    baseline_rankings = {}
    for source in active:
        pool = []
        src = processed[source["id"]]
        for target in items:
            if (target["repo"].split("/")[0].casefold() ==
                    source["repo"].split("/")[0].casefold()
                    or date(target["created_at"]) > date(source["created_at"])):
                continue
            tgt = processed[target["id"]]
            shared = src["all"] & tgt["all"]
            if not shared:
                continue
            # Baseline uses all available title+body text, not just titles.
            raw_score = sum(idf[t] for t in shared)
            baseline_rank = (raw_score, target["id"])
            baseline_rankings.setdefault(source["id"], []).append((baseline_rank, target["id"]))
            salient = sorted((t for t in shared if idf[t] >= 2.0
                              and (t in src["title"] or t in tgt["title"])),
                             key=lambda t: (-idf[t], t))
            if not salient:
                continue
            evidence_score = sum(
                idf[t] * (1.0 + (1.1 if t in src["title"] else 0.0)
                          + (1.1 if t in tgt["title"] else 0.0))
                for t in shared
            )
            if evidence_score < config["min_score"]:
                continue
            pool.append((evidence_score, raw_score, target, salient[:4],
                         processed[source["id"]]["body_truncated"],
                         tgt["body_truncated"]))
        pool.sort(key=lambda pair: (-pair[0], -pair[1], pair[2]["id"]))
        all_rankings[source["id"]] = pool[:config["max_suggestions_per_source"]]
    for key in baseline_rankings:
        baseline_rankings[key].sort(key=lambda p: (-p[0][0], p[1]))
    cards = []
    for source in active:
        for score, raw, target, match_terms, src_truncated, tgt_truncated in all_rankings.get(source["id"], []):
            baseline = baseline_rankings.get(source["id"], [])
            baseline_first = baseline[0][1] if baseline else None
            cards.append({
                "id": f"match:{source['id']}->{target['id']}",
                "source_id": source["id"], "source": report_issue(source),
                "target_id": target["id"], "target": report_issue(target),
                "classification": ("possible_prior_work" if target["state"] == "closed"
                                   else "possible_parallel_work"),
                "prior_closed_work_not_proven_merged_or_solved": target["state"] == "closed",
                "score": round(score, 3), "fulltext_baseline_score": round(raw, 3),
                "matched_terms": [
                    {"term": t,
                     "source": term_context(source, t),
                     "target": term_context(target, t),
                     "idf": round(idf[t], 3)}
                    for t in match_terms
                ],
                "baseline_fulltext_top1_id": baseline_first,
                "same_as_fulltext_baseline_top1": target["id"] == baseline_first,
                "ranking_text_truncated": src_truncated or tgt_truncated,
                "validation": "unreviewed_candidate_not_confirmed_reusable",
                "outreach": "none",
            })
    cards.sort(key=lambda c: (-c["score"], c["source_id"], c["target_id"]))
    return cards[:config["max_suggestions"]], {
        "active_open_issues_or_prs": len(active),
        "fulltext_baseline_top1_per_active_issue": len(baseline_rankings),
        "body_char_limit": maxchars,
        "baseline": "unweighted IDF overlap on the exact same title+body snapshot; "
                    "not a restricted title-only or one-hop control",
    }


def report_issue(issue):
    return {k: issue[k] for k in
            ("id", "repo", "number", "kind", "state", "title", "url",
             "created_at", "updated_at", "title_sha256", "body_sha256", "assignees")}


def verify_shortlist(cards, index, fetch=get_json):
    """Re-read only shortlisted original issues, fail closed on source drift."""
    ids = sorted({c[key] for c in cards for key in ("source_id", "target_id")})
    if len(ids) > MAX_REREADS:
        raise ValueError("Shortlist source re-read budget exceeded")
    for identifier in ids:
        old = index[identifier]
        latest = normalize_issue(old["repo"], fetch(
            f"{API}/{old['repo']}/issues/{old['number']}"))
        for key in ("title_sha256", "body_sha256", "kind", "state", "updated_at",
                    "created_at", "url"):
            if old[key] != latest[key]:
                raise ValueError(f"Original GitHub issue changed during audit: {identifier}")
    return len(ids)


def build(config, fetch=get_json, now=None):
    validate(config)
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Expected timezone-aware current timestamp")
    inventories = {repo: fetch_issues(repo, config, fetch=fetch) for repo in config["repositories"]}
    items = [item for rows in inventories.values() for item in rows]
    if len({x["id"] for x in items}) != len(items):
        raise ValueError("Duplicate item in cross-repository inventory")
    candidates, stats = rank_pairs(items, config, now)
    rechecked = verify_shortlist(candidates, {x["id"]: x for x in items}, fetch=fetch)
    return {
        "schema": 1, "status": "review_only", "generated_at_utc": now.isoformat(),
        "repositories": list(config["repositories"]),
        "inventory_counts": {key: len(rows) for key, rows in inventories.items()},
        "items_indexed": len(items), "source_candidates": stats["active_open_issues_or_prs"],
        "shortlisted_sources_rechecked": rechecked,
        "matcher": "lexical technical-term evidence gate, IDF and title-context ranking (NOT LLM/AI reasoning)",
        "baseline": stats["baseline"], "baseline_top1_sources": stats["fulltext_baseline_top1_per_active_issue"],
        "suggestions": candidates, "suggestions_count": len(candidates),
        "suggestions_matching_same_input_baseline_top1": sum(x["same_as_fulltext_baseline_top1"] for x in candidates),
        "human_quality_labels_collected": 0,
        "evidence_levels": "Phrase overlap is a review candidate, not collaboration, identical code or verified prior solution.",
        "limitations": "Bounded repo registry and source age, English-oriented tokens, GitHub-only pilot; "
                       "issue/PR body and title verified for shortlisted cards, not issue comments or merge status. "
                       "Closed pull requests are not necessarily merged. No claim of better quality than full-text search, "
                       "no labels, no automated outreach. Source bodies longer than the configured limit are truncated for ranking.",
    }


def markdown(report):
    lines = [
        "# Collaboration Matcher — cross-organization pilot", "",
        "**Review only. Rule-based matcher, not an LLM and not proof of duplicate effort.**",
        f"Audited **{report['items_indexed']}** public issues/PRs in "
        f"**{len(report['repositories'])}** repositories, "
        f"considering **{report['source_candidates']}** recently opened active items. "
        f"Found **{report['suggestions_count']}** candidate handoffs. "
        f"Re-checked **{report['shortlisted_sources_rechecked']}** underlying issue/PR sources.", "",
        f"**Same-input full-text baseline:** "
        f"{report['suggestions_matching_same_input_baseline_top1']}/"
        f"{report['suggestions_count']} suggestions are also the lexical baseline's "
        f"top-1 target for that source. **This does not establish improved precision or recall.**", "",
        "## Review queue (no messages sent)", "",
    ]
    if not report["suggestions"]:
        lines += ["No candidates passed the conservative gate in this bounded run.", ""]
    for n, c in enumerate(report["suggestions"], 1):
        a, b = c["source"], c["target"]
        lines += [
            f"### {n}. [{a['title']}]({a['url']}) ↔ [{b['title']}]({b['url']})", "",
            f"- Source: {a['repo']} / {a['kind']} / {a['state']} / SHA256 {a['body_sha256']}",
            f"- Possible related work: {b['repo']} / {b['kind']} / {b['state']} "
            f"/ SHA256 {b['body_sha256']}",
            f"- Category: {c['classification']} — **not a verified solution or collaboration**.",
            f"- Ranking score: {c['score']}; baseline top-1 agrees: "
            f"{'yes' if c['same_as_fulltext_baseline_top1'] else 'no'} "
            f"(baseline target ID: {c['baseline_fulltext_top1_id']}).",
            f"- Suggested assignees (not contacted): "
            f"{', '.join('@' + p for p in b['assignees']) or 'not specified'}",
            f"- Ranking text truncated: {'yes' if c['ranking_text_truncated'] else 'no'}",
            "- Original matching expressions (not independently validated):",
        ]
        for t in c["matched_terms"]:
            lines.append(
                f"  - **{t['term']}**: source {t['source']['field']} "
                f"«{t['source']['excerpt'].replace(chr(10), ' ')}»; "
                f"target {t['target']['field']} "
                f"«{t['target']['excerpt'].replace(chr(10), ' ')}»"
            )
        lines += ["- Suggested review: compare actual code, current acceptance criteria, "
                  "age of earlier work and whether the teams already coordinate.", ""]
    lines += [
        "## What must be measured next", "",
        "An independent reviewer should label the shortlist as **actionable reuse**, "
        "**related but already coordinated**, or **not useful**. Check the corresponding "
        "full-text baseline candidates under the same review protocol. "
        "Without these labels we cannot claim that matching adds value.", "",
        "## Limitations", "", report["limitations"], "",
    ]
    return "\n".join(lines) + "\n"


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
        (folder / "collaboration_matches.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (folder / "COLLABORATION_MATCHES.md").write_text(markdown(result), encoding="utf-8")
        print(f"Collaboration matcher: {result['suggestions_count']} review candidates "
              f"from {result['source_candidates']} recent source items")
        return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f"Matcher audit aborted; no report published: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
