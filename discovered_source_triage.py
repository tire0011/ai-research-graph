"""Read-only triage of newly discovered repositories, using the existing issue pipeline."""
import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from eu_source_discovery import canonical, detail_url, url_for
from discovered_collaboration_review import contact_review, prepare_discovered
from technical_leverage import rank as rank_leverage, markdown as leverage_markdown
from technical_leverage_sources import collect as collect_leverage
from eu_opportunity_discovery import build, get_json, is_stale, VOLUNTEER_LABELS

# Specific technical signals, deliberately not a geography or collaboration classifier.
TOPICS = {
    "evaluation": r"\b(?:benchmark(?:s|ing)?|evaluat(?:ion|ions|e|ing)|leaderboard)\b",
    "multilingual": r"\b(?:multilingual|machine.translation|language.identification|low.resource|tokenization|tokenizer)\b",
    "data-processing": r"\b(?:dataset|corpus|corpora|data.processing|data.cleaning|deduplication|web.crawl)\b",
    "speech": r"\b(?:speech|audio.codec|text.to.speech|automatic.speech.recognition)\b",
    "model-training": r"\b(?:pre.training|post.training|fine.tun(?:ing|e)|distillation|model.training)\b",
    "inference": r"\b(?:inference|quantization|model.serving|speculative.decoding)\b",
    "retrieval": r"\b(?:retrieval.augmented|semantic.search|vector.search|embedding|information.retrieval)\b",
    "research-metadata": r"\b(?:research.metadata|scholarly|knowledge.graph|provenance|bibliometric)\b",
}
MAX_METADATA = 12
MAX_ISSUE_REPOS = 4


def source_owner(repo):
    return repo.split("/")[0].casefold()


def analyze(config, snapshot, fetch=get_json, *, previous=None, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    stamp = now.isoformat()
    if snapshot.get("schema") != 2:
        raise ValueError("Expected cumulative discovery schema 2")
    curated = {x["repo"].casefold() for x in config["repositories"]}
    anchors = defaultdict(list)
    for source in config["repositories"]:
        anchors[source_owner(source["repo"])].append(
            {"source": "https://github.com/" + source["repo"], "region": source["region"]})
    urls = {}
    for item in snapshot["candidates"]:
        key = canonical(item["url"])
        if key and key[0] == "repository" and key[1] not in curated:
            urls[url_for(key)] = item
    # Least-recently reviewed first, with round-robin across owners, so large
    # organizations cannot permanently crowd out previously unknown owners.
    previous = previous or {}
    history = dict(previous.get("last_attempt", {}))
    cohorts = defaultdict(lambda: defaultdict(list))
    for url in sorted(urls):
        cohorts[history.get(url, "")][source_owner(canonical(url)[1])].append(url)
    selected = []
    for age in sorted(cohorts):
        groups = cohorts[age]
        while groups and len(selected) < MAX_METADATA:
            for owner in sorted(groups):
                selected.append(groups[owner].pop(0))
                if not groups[owner]:
                    del groups[owner]
                if len(selected) == MAX_METADATA:
                    break
        if len(selected) == MAX_METADATA:
            break
    metadata, errors = [], []
    for url in selected:
        history[url] = stamp
        key = canonical(url)
        endpoint = detail_url(key)
        try:
            row = fetch(endpoint)
            if not isinstance(row, dict) or row.get("full_name", "").casefold() != key[1]:
                raise ValueError("repository identity mismatch")
            if row.get("private") or row.get("archived") or row.get("fork") or row.get("disabled"):
                metadata.append({"url": url, "status": "excluded", "source_url": endpoint})
                continue
            repo = row["full_name"]
            owner = source_owner(repo)
            if (row.get("owner") or {}).get("login", "").casefold() != owner:
                raise ValueError("owner identity mismatch")
            description = row.get("description") or ""
            topics = row.get("topics") or []
            if not isinstance(description, str) or not isinstance(topics, list) or not all(isinstance(x, str) for x in topics):
                raise ValueError("invalid metadata")
            raw = description + "\n" + "\n".join(topics)
            matches = {name: sorted(set(m.group(0).lower() for m in re.finditer(pattern, raw, re.I)))
                       for name, pattern in TOPICS.items()}
            matches = {name: values for name, values in matches.items() if values}
            active = not is_stale(row.get("pushed_at"), now=now)
            license_id = (row.get("license") or {}).get("spdx_id")
            open_license_hint = isinstance(license_id, str) and license_id not in ("NOASSERTION", "NONE", "")
            record = {"url": url, "repo": repo, "status": "review_only", "source_url": endpoint,
                      "retrieved_at": stamp, "description": description, "topics": topics,
                      "metadata_sha256": hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest(),
                      "technical_signals": matches, "recent_push": active,
                      "license_spdx": license_id, "license_hint": open_license_hint,
                      "has_issues": row.get("has_issues") is True,
                      "affiliation_status": "curated_owner_context_only" if owner in anchors else "unknown",
                      "affiliation_context": anchors.get(owner, []),
                      "discovery_evidence": urls[url].get("evidence", [])}
            metadata.append(record)
        except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
            errors.append({"url": url, "stage": "metadata", "error": type(exc).__name__})
    topical = [r for r in metadata if r["status"] == "review_only" and r["technical_signals"]]
    # License metadata is not a precondition for reading issues or identifying topic overlap.
    eligible = [r for r in topical if r["recent_push"] and r["has_issues"]]
    eligible.sort(key=lambda r: (-len(r["technical_signals"]), r["url"]))
    # Select distinct owners before a second repository from any owner.
    issue_sources, seen_owners = [], set()
    for r in eligible:
        owner = source_owner(r["repo"])
        if owner not in seen_owners:
            issue_sources.append(r)
            seen_owners.add(owner)
        if len(issue_sources) == MAX_ISSUE_REPOS:
            break
    for r in eligible:
        if len(issue_sources) == MAX_ISSUE_REPOS:
            break
        if r not in issue_sources:
            issue_sources.append(r)
    issue_result = None
    if issue_sources:
        scoped = {**config, "max_issues_per_repo": min(config["max_issues_per_repo"], 8),
                  "candidate_checks_per_repo": 2, "max_new_suggestions": 5,
                  "repositories": [{"repo": r["repo"], "area": ", ".join(r["technical_signals"]),
                                    "region": "UNVERIFIED — candidate review only"} for r in issue_sources]}
        issue_result = build(scoped, fetch, now=now, allow_single_owner=True)
        errors.extend({"stage": "issue", **err} for err in issue_result["errors"])
    by_repo = {r["repo"]: r for r in issue_sources}
    tasks = []
    if issue_result:
        for task in issue_result["new_top5"]:
            meta = by_repo[task["repository"]]
            labels = sorted({x for x in task["labels"] if x.casefold() in VOLUNTEER_LABELS})
            tasks.append({**task, "affiliation_status": meta["affiliation_status"],
                          "repository_evidence_url": meta["source_url"],
                          "invitation_labels": labels,
                          "invitation_status": "public_issue_label" if labels else "unknown",
                          "license_spdx": meta["license_spdx"],
                          "reuse_status": "license_review_required",
                          "action": "Inspect current code and ask whether the task is wanted; do not claim automatically."})
    # Shared specific metadata signals are hypotheses, not a proven handoff.
    pairs = []
    for i, left in enumerate(topical):
        for right in topical[i+1:]:
            if source_owner(left["repo"]) == source_owner(right["repo"]):
                continue
            shared = sorted(set(left["technical_signals"]) & set(right["technical_signals"]))
            if not shared:
                continue
            pairs.append({"left": left["url"], "right": right["url"], "shared_areas": shared,
                          "status": "unverified_topic_overlap",
                          "evidence": [{"url": r["source_url"], "description": r["description"],
                                        "topics": r["topics"], "signals": r["technical_signals"],
                                        "license_spdx": r["license_spdx"], "recent_push": r["recent_push"],
                                        "retrieved_at": stamp} for r in (left, right)],
                          "next_check": "Compare open requirements, existing code, licenses and maintainer interest."})
    pairs.sort(key=lambda x: (-len(x["shared_areas"]), x["left"], x["right"]))
    # Keep handled scientific hypotheses inspectable; exclude them only from fresh outreach review.
    suppressed_pairs = []
    for pair in pairs:
        pair["contact_review"] = contact_review(config, source_owner(canonical(pair["left"])[1]),
                                               source_owner(canonical(pair["right"])[1]))
        if pair["contact_review"]["suppress_outreach"]:
            suppressed_pairs.append(pair)
    pairs = [x for x in pairs if not x["contact_review"]["suppress_outreach"]]
    collaboration = None
    if config.get("discovered_collaboration_review", False):
        collaboration = prepare_discovered(config, metadata, fetch, now=now)
        errors.extend({"stage": "collaboration", **x} for x in collaboration["errors"])
    collection = None
    if config.get("technical_leverage_collection", False):
        collection = collect_leverage(config, metadata, fetch, stamp=stamp,
                                      previous=previous.get("leverage_collection"))
        errors.extend({"stage": "leverage_collection", **x} for x in collection["errors"])
    leverage_input = {**snapshot, "verified_references": snapshot.get("verified_references", []) +
                      (collection["edges"] if collection else [])}
    web = snapshot.get("web_discovery") or {}
    return {"schema": 1, "retrieved_at": stamp, "snapshot_retrieved_at": snapshot.get("retrieved_at"),
            "pool_size": len(urls), "selected": selected, "last_attempt": history,
            "metadata": metadata, "filter_counts": {"metadata_review_only": sum(r["status"] == "review_only" for r in metadata),
                "technical_signals": len(topical), "active_with_issues": len(eligible),
                "selected_for_issue_review": len(issue_sources),
                "unknown_license_among_topical": sum(not r["license_hint"] for r in topical)}, "issue_repositories": [r["repo"] for r in issue_sources],
            "issue_review": issue_result, "tasks": tasks, "topic_hypotheses": pairs[:5],
            "suppressed_contact_hypotheses": suppressed_pairs, "collaboration_review": collaboration,
            "technical_leverage": rank_leverage(config, leverage_input),
            "leverage_collection": collection,
            "adapter_review": web.get("adapter_proposals", []), "errors": errors,
            "limitations": ["Repository descriptions and topics are lexical signals, not scientific assessment.",
                            "Curated owner context does not independently verify European affiliation.",
                            "SPDX metadata is only a license hint; actual license compatibility is not assessed.",
                            "An issue label is not proof of maintainer response or acceptance.",
                            "No claim of novel cooperation or superiority over search; independent review is pending.",
                            "Only the bounded repository sample receives semantic triage; web and HF relevance remain open."]}


def markdown(result):
    lines = ["# Discovered-source review queue", "",
             f"Pool: {result['pool_size']} repositories; inspected {len(result['selected'])}; errors: {len(result['errors'])}.",
             "", "## Selection diagnostics"]
    lines += [f"- {key}: {value}" for key, value in result["filter_counts"].items()]
    lines += [f"- Issue review: {len(result['issue_repositories'])} repositories"]
    lines += ["", "## Up to five engineering tasks (review only)"]
    for task in result["tasks"]:
        lines += [f"- {task['issue_url']} — {task['title']}",
                  f"  - Affiliation: {task['affiliation_status']}; invitation labels: {', '.join(task['invitation_labels']) or 'unknown'}.",
                  f"  - License metadata: {task['license_spdx'] or 'unknown'}; reuse requires license review.",
                  f"  - {task['action']}"]
    if not result["tasks"]:
        lines.append("No task surfaced in this bounded review; absence is not evidence of no opportunities.")
    lines += ["", "## Up to five topical hypotheses (not collaboration claims)"]
    for pair in result["topic_hypotheses"]:
        lines += [f"- {pair['left']} ↔ {pair['right']}: {', '.join(pair['shared_areas'])}",
                  f"  - {pair['next_check']}"]
    lines += ["", "## Previously handled contact pairs"]
    for pair in result.get("suppressed_contact_hypotheses", []):
        lines.append(f"- {pair['left']} ↔ {pair['right']} — {pair['contact_review']['status']}")
    review = result.get("collaboration_review")
    if review:
        lines += ["", "## Source-verified technical review packets",
                  f"Sampled {review['items_indexed']} issue/PR records; prepared {len(review['packets'])} packets; suppressed {len(review['suppressed_contact_candidates'])} contacted pairs.",
                  "Not confirmed handoffs; independent assessment required."]
        for item in review["packets"]:
            card = item["candidate"]
            lines.append(f"- {card['source']['url']} ↔ {card['target']['url']}")
    if result.get("leverage_collection"):
        collection = result["leverage_collection"]
        lines += ["", "## Bounded technical source collection",
                  f"Repositories: {len(collection['selected'])}; evidence edges: {len(collection['edges'])}; errors: {len(collection['errors'])}."]
        for row in collection["coverage"]:
            lines.append(f"- {row['repo']}: {row['readme']} README, {row['issues']} issues, {row['comments']} comments, {row['manifests']} manifests; partial: {row['truncated']}")
    if result.get("technical_leverage"):
        lines += leverage_markdown(result["technical_leverage"])
    lines += ["", "## Adapter review queue (no execution)"]
    lines += [f"- {x['url']} — {x['format']}" for x in result["adapter_review"]]
    lines += ["", "## Diagnostics"] + ["- " + json.dumps(x) for x in result["errors"]]
    lines += ["", "## Limits"] + ["- " + x for x in result["limitations"]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sources", default="eu_opportunity_sources.json")
    p.add_argument("--snapshot", required=True)
    p.add_argument("--previous")
    p.add_argument("--output", required=True)
    args = p.parse_args(argv)
    load = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))
    previous = load(args.previous) if args.previous and Path(args.previous).exists() else None
    result = analyze(load(args.sources), load(args.snapshot), previous=previous)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "source_triage.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "SOURCE_TRIAGE.md").write_text(markdown(result), encoding="utf-8")
    print(f"Source triage: {len(result['selected'])} repositories, {len(result['tasks'])} review tasks, "
          f"{len(result['topic_hypotheses'])} hypotheses, {len(result['errors'])} errors.")
    # Partial evidence remains useful, but a fully failed metadata collection must not be called a success.
    return 2 if result["selected"] and not result["metadata"] else 0


if __name__ == "__main__":
    sys.exit(main())
