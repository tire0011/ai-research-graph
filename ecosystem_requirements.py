"""Build independent requirement reports and a cross-platform comparison.

This is a transparent synthesis of *curated official documentation*, not live
catalogue crawling, automatic duplicate detection or evidence of new teamwork.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


STATUSES = {"documented", "planned", "adjacent"}
KNOWN_RELATIONS = {"extends", "integrates_with", "deploys_via"}
CASE_CLASSES = {"complementary_hypothesis", "potential_duplicate", "shared_problem", "third_party_hypothesis"}


def validate(registry: dict) -> None:
    if registry.get("schema") != 1:
        raise ValueError("Unsupported ecosystem registry schema")
    platforms = registry.get("platforms")
    requirements = registry.get("requirements")
    observations = registry.get("observations")
    relations = registry.get("known_relations")
    cases = registry.get("cross_project_cases")
    if not all(isinstance(x, list) and x for x in (platforms, requirements, observations)):
        raise ValueError("Missing platforms, requirements or observations")
    if not isinstance(relations, list) or not isinstance(cases, list):
        raise ValueError("Missing known relation or cross-project case list")
    platform_ids = [x["id"] for x in platforms]
    requirement_ids = [x["id"] for x in requirements]
    if (len(platform_ids) != len(set(platform_ids))
            or len(requirement_ids) != len(set(requirement_ids))):
        raise ValueError("Duplicate platform or requirement ID")
    if any(not isinstance(x.get("name"), str) or not x["name"] or
           not x.get("url", "").startswith("https://") for x in platforms):
        raise ValueError("Every platform needs a name and HTTPS URL")
    if any(not all(isinstance(x.get(k), str) and x[k] for k in
                   ("id", "title", "question", "acceptance"))
           or not x["id"].replace("_", "").isalnum() for x in requirements):
        raise ValueError("Invalid requirement definition")
    seen = set()
    for x in observations:
        pair = x.get("platform"), x.get("requirement")
        if (pair in seen or pair[0] not in platform_ids or pair[1] not in requirement_ids
                or x.get("status") not in STATUSES
                or not isinstance(x.get("finding"), str) or not x["finding"]
                or not x.get("source_url", "").startswith("https://")):
            raise ValueError(f"Invalid or duplicate evidence: {pair}")
        seen.add(pair)
    for rel in relations:
        if (rel.get("from") not in platform_ids or rel.get("to") not in platform_ids
                or rel["from"] == rel["to"] or rel.get("type") not in KNOWN_RELATIONS
                or not rel.get("source_url", "").startswith("https://")):
            raise ValueError(f"Invalid supported platform relation: {rel}")
    case_ids = [x.get("id") for x in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Duplicate cross-project case ID")
    for case in cases:
        urls = case.get("source_urls")
        tagged = case.get("requirements")
        if (not isinstance(case.get("title"), str) or not case["title"]
                or case.get("classification") not in CASE_CLASSES
                or not isinstance(case.get("finding"), str) or not case["finding"]
                or not isinstance(tagged, list) or not tagged
                or len(tagged) != len(set(tagged))
                or any(r not in requirement_ids for r in tagged)
                or not isinstance(urls, list) or len(urls) < 2
                or any(not isinstance(u, str) or not u.startswith("https://") for u in urls)):
            raise ValueError(f"Invalid cross-project case: {case.get('id')}")


def build(registry: dict) -> dict:
    validate(registry)
    by_pair = {(x["platform"], x["requirement"]): x for x in registry["observations"]}
    matrix = {
        r["id"]: {
            p["id"]: by_pair.get((p["id"], r["id"]), {"status": "not_assessed"})["status"]
            for p in registry["platforms"]
        } for r in registry["requirements"]
    }
    return {
        "schema": 1, "as_of": registry["as_of"],
        "basis": "Curated official source claims; no external API ingest, runtime verification or benchmark",
        "platforms": registry["platforms"], "requirements": registry["requirements"],
        "observations": registry["observations"], "matrix": matrix,
        "cross_project_cases": registry["cross_project_cases"],
        "known_relations": registry["known_relations"],
        "novel_collaboration_confirmed": False, "duplicate_work_confirmed": False,
        "limitations": (
            "Documented means the official source describes a capability, not that it was "
            "tested here. Planned is a stated future target. Adjacent is related, not "
            "proof of requirement satisfaction. Not assessed is unknown, never absent. "
            "Known relations are already-public relationships, not new matches."
        ),
    }


def requirement_report(report: dict, requirement: dict) -> tuple[dict, str]:
    rid = requirement["id"]
    pmap = {p["id"]: p for p in report["platforms"]}
    observations = [o for o in report["observations"] if o["requirement"] == rid]
    cases = [c for c in report["cross_project_cases"] if rid in c["requirements"]]
    result = {
        "schema": 1, "requirement": requirement, "as_of": report["as_of"],
        "observations": observations, "cross_project_cases": cases,
        "not_assessed": [p["id"] for p in report["platforms"]
                                                    if report["matrix"][rid][p["id"]] == "not_assessed"],
        "known_relations": report["known_relations"],
        "novel_collaboration_confirmed": False,
    }
    lines = [f"# {requirement['title']}", "",
             f"**Question:** {requirement['question']}", "",
             f"**Success test:** {requirement['acceptance']}", "",
             "| Platform | Evidence status | Source-backed observation |",
             "| --- | --- | --- |"]
    obs = {o["platform"]: o for o in observations}
    for p in report["platforms"]:
        row = obs.get(p["id"])
        if row:
            lines.append(f"| [{p['name']}]({p['url']}) | {row['status']} | "
                         f"{row['finding']} [Official source]({row['source_url']}) |")
        else:
            lines.append(f"| [{p['name']}]({p['url']}) | not_assessed | No verified source claim in this pilot; **not proof of absence**. |")
    lines += ["", "## Cross-project candidate cases (separate evidence layer)", ""]
    for case in cases:
        links = ", ".join(f"[source {i}]({url})" for i, url in enumerate(case["source_urls"], 1))
        lines.append(f"- **{case['title']}** — `{case['classification']}`: "
                     f"{case['finding']} ({links})")
    if not cases:
        lines.append("No candidate case mapped yet; this is not proof there are none.")
    lines += ["", "**Next:** Inspect actual interfaces, participation, maturity and shared "
              "requirements before suggesting any reuse or outreach.", "",
              "Status is based on curated public documentation, not tested service integrations.", ""]
    return result, "\n".join(lines)


def overview(report: dict) -> str:
    ids = [p["id"] for p in report["platforms"]]
    lines = ["# European AI ecosystem — requirements comparison", "",
             f"**Official-source snapshot:** {report['as_of']}. No live import or outreach.", "",
             "| Requirement | " + " | ".join(p["name"] for p in report["platforms"]) + " |",
             "| --- | " + " | ".join("---" for _ in ids) + " |"]
    for r in report["requirements"]:
        cells = [report["matrix"][r["id"]][p] for p in ids]
        lines.append(f"| [{r['title']}]({r['id']}.md) | " + " | ".join(cells) + " |")
    lines += ["", "**Legend:** documented = described by an official source; planned = "
              "announced/under development; adjacent = relevant but not demonstrated for the "
              "requirement; not_assessed = unknown, not unsupported.", "",
              "## Known relationships (do not rediscover as new)", ""]
    names = {p["id"]: p["name"] for p in report["platforms"]}
    for rel in report["known_relations"]:
        lines.append(f"- {names[rel['from']]} **{rel['type']}** {names[rel['to']]} "
                     f"([source]({rel['source_url']}))")
    lines += ["", "## Existing cross-project candidate reviews (not confirmed)", ""]
    for case in report["cross_project_cases"]:
        links = ", ".join(f"[source {i}]({url})" for i, url in enumerate(case["source_urls"], 1))
        refs = ", ".join(f"[{rid}]({rid}.md)" for rid in case["requirements"])
        lines.append(f"- **{case['title']}** ({case['classification']}): {refs}; {links}")
    lines += ["", "## Interpretation", "",
              "- Multiple documented capabilities in one requirement indicate possible overlap, "
              "**not duplicate engineering work**.",
              "- Planned agent-to-agent integration in EOSC-ARENA is especially relevant to "
              "our Human–AI hypothesis; it is **not a finished connector**.",
              "- AIoD's documented metadata API is the clearest next read-only source adapter "
              "candidate. EOSC onboarding has eligibility and review requirements.",
              "- There is no established common cross-project model-training integration "
              "process in this bounded evidence sample; this is **not** proof none exists.",
              "", report["limitations"], ""]
    return "\n".join(lines)


def write_reports(report: dict, output: Path) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    for req in report["requirements"]:
        data, md = requirement_report(report, req)
        for suffix, content in (("json", json.dumps(data, indent=2, ensure_ascii=False) + "\n"),
                                ("md", md)):
            path = output / f"{req['id']}.{suffix}"
            path.write_text(content, encoding="utf-8")
            paths.append(path)
    for name, content in (("OVERVIEW.md", overview(report)),
                          ("comparison.json", json.dumps(report, indent=2, ensure_ascii=False) + "\n")):
        path = output / name
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default="ecosystem_sources.json")
    parser.add_argument("--output", default="results/requirements")
    args = parser.parse_args(argv)
    try:
        registry = json.loads(Path(args.sources).read_text(encoding="utf-8"))
        result = build(registry)
        paths = write_reports(result, Path(args.output))
        print(f"Wrote {len(paths)} evidence-limited requirement reports/indices")
        return 0
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"Ecosystem reporting failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
