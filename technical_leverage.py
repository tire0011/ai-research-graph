"""Read-only prioritization of shared technical components from discovery evidence.

References are leads, not proof of use. Curated project context is not verified
geography. Known case evidence is kept separate from automatic retrieval.
"""
from collections import defaultdict
from urllib.parse import urlsplit


def component_key(url):
    from eu_source_discovery import canonical, url_for
    key = canonical(url)
    return url_for(key) if key else None


def owner(url):
    from eu_source_discovery import canonical
    key = canonical(url)
    if not key:
        return None
    return key[1].split("/")[0].casefold()


def rank(config, snapshot, *, limit=10):
    if not 1 <= limit <= 20:
        raise ValueError("invalid leverage limit")
    curated = {x["repo"].split("/")[0].casefold()
               for x in config["repositories"]}
    groups = defaultdict(dict)
    observations = 0
    for edge in snapshot.get("verified_references", []):
        if (edge.get("relationship") != "references"
                or edge.get("verification_status") != "verified"):
            continue
        source, target = edge.get("source"), edge.get("target")
        if not isinstance(source, str) or not isinstance(target, str):
            continue
        src, dst = component_key(source), component_key(target)
        if not src or not dst or owner(src) == owner(dst):
            continue
        evidence = edge.get("evidence") or {}
        evidence_url = evidence.get("source_url")
        excerpt = evidence.get("excerpt")
        if (not isinstance(evidence_url, str)
                or urlsplit(evidence_url).scheme != "https"
                or not isinstance(excerpt, str)
                or component_key(excerpt) != dst
                or evidence.get("source_entity") != source):
            continue
        observations += 1
        groups[dst][src] = {"source": src, "owner": owner(src),
                            "source_url": evidence_url, "excerpt": excerpt,
                            "last_seen": edge.get("last_seen"),
                            "status": "historical_reference_not_verified_use"}
    candidates = []
    for target, refs in groups.items():
        owners = {r["owner"] for r in refs.values()}
        if len(owners) < 2:
            continue
        known = owners & curated
        candidates.append({"component": target, "distinct_source_owners": len(owners),
                           "curated_owner_context_count": len(known),
                           "unknown_owner_context_count": len(owners - known),
                           "references": sorted(refs.values(), key=lambda r: r["source"]),
                           "status": "shared_reference_review_only",
                           "next_check": "Inspect actual imports, data or evaluation use, licence and open tasks."})
    candidates.sort(key=lambda c: (-c["curated_owner_context_count"],
                                   -c["distinct_source_owners"], c["component"]))
    return {"schema": 1, "observations": observations, "candidate_count": len(candidates),
            "candidates": candidates[:limit], "review_only": True,
            "known_cases": config.get("technical_leverage_cases", []),
            "limitations": ["Historical explicit references are not verified technical dependencies.",
                            "Distinct owner namespaces are not necessarily distinct organizations.",
                            "Curated owner context is not verified European affiliation.",
                            "Known cases are editorial evidence, not automatic discoveries or holdout successes.",
                            "No measured impact, automatic outreach or automatic graph promotion."]}


def markdown(result):
    lines = ["", "## Technical leverage candidates (review only)",
             f"Eligible historical reference observations: {result['observations']}; "
             f"shared components: {result['candidate_count']}."]
    for row in result["candidates"]:
        lines.append(f"- {row['component']} — {row['distinct_source_owners']} source owners "
                     f"({row['curated_owner_context_count']} with curated context)")
        for ref in row["references"]:
            lines.append(f"  - {ref['source']} — {ref['source_url']}")
        lines.append("  - " + row["next_check"])
    if not result["candidates"]:
        lines.append("No shared component surfaced in the available evidence; not proof of absence.")
    lines.append("### Known cases (editorial, separate from automatic ranking)")
    for case in result["known_cases"]:
        lines.append(f"- {case['component']}: {case['finding']}")
        lines.extend("  - " + url for url in case["source_urls"])
    lines.extend("- " + item for item in result["limitations"])
    return lines
