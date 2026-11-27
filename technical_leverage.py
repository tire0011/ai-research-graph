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
    seen = set()
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
        kind = evidence.get("type", "historical_reference")
        key = (src, evidence_url, kind)
        identity = (dst, key)
        if identity not in seen:
            observations += 1
            seen.add(identity)
        existing = groups[dst].get(key)
        if existing and (existing.get("last_seen") or "") > (edge.get("last_seen") or ""):
            continue
        groups[dst][key] = {"source": src, "owner": owner(src),
                            "source_url": evidence_url, "excerpt": excerpt,
                            "last_seen": edge.get("last_seen"), "first_seen": edge.get("first_seen"),
                            "evidence_type": kind, "context": evidence.get("context"),
                            "sha256": evidence.get("sha256"),
                            "status": ("declared_vcs_dependency_not_runtime_verified" if kind == "manifest_vcs_declaration"
                                       else "reference_not_verified_use")}
    candidates = []
    for target, refs in groups.items():
        owners = {r["owner"] for r in refs.values()}
        if len(owners) < 2:
            continue
        known = owners & curated
        dependency_owners = {r["owner"] for r in refs.values() if r["evidence_type"] == "manifest_vcs_declaration"}
        candidates.append({"component": target, "distinct_source_owners": len(owners),
                           "curated_owner_context_count": len(known),
                           "unknown_owner_context_count": len(owners - known),
                           "declared_dependency_owner_count": len(dependency_owners),
                           "references": sorted(refs.values(), key=lambda r: r["source"]),
                           "status": "shared_reference_review_only",
                           "next_check": "Inspect actual imports, data or evaluation use, licence and open tasks."})
    candidates.sort(key=lambda c: (-c["curated_owner_context_count"],
                                   -c["distinct_source_owners"], c["component"]))
    return {"schema": 1, "observations": observations, "candidate_count": len(candidates),
            "candidates": candidates[:limit], "review_only": True,
            "known_cases": config.get("technical_leverage_cases", []),
            "limitations": ["Cumulative observations are historical; links may have changed or disappeared.",
                            "Explicit references are not verified technical dependencies; VCS declarations are not runtime verification.",
                            "Distinct owner namespaces are not necessarily distinct organizations.",
                            "Curated owner context is not verified European affiliation.",
                            "Known cases are editorial evidence, not automatic discoveries or holdout successes.",
                            "No measured impact, automatic outreach or automatic graph promotion."]}


def markdown(result):
    lines = ["", "## Technical leverage candidates (review only)",
             f"Eligible reference observations: {result['observations']}; "
             f"shared components: {result['candidate_count']}."]
    for row in result["candidates"]:
        lines.append(f"- {row['component']} — {row['distinct_source_owners']} source owners "
                     f"({row['curated_owner_context_count']} with curated context; {row['declared_dependency_owner_count']} declared VCS dependency owners)")
        for ref in row["references"]:
            lines.append(f"  - {ref['source']} — {ref['source_url']} ({ref['evidence_type']})")
        lines.append("  - " + row["next_check"])
    if not result["candidates"]:
        lines.append("No shared component surfaced in the available evidence; not proof of absence.")
    lines.append("### Known cases (editorial, separate from automatic ranking)")
    for case in result["known_cases"]:
        lines.append(f"- {case['component']}: {case['finding']}")
        lines.extend("  - " + url for url in case["source_urls"])
    lines.extend("- " + item for item in result["limitations"])
    return lines
