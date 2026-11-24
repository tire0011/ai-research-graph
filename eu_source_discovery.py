"""Bounded source expansion for the European opportunity pipeline (review only)."""
import copy
import datetime as dt
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from http_util import get_json
from arxiv_source_discovery import discover_publications
from publication_organizations import resolve as resolve_organizations
from publication_openaire import enrich as enrich_openaire
from generic_source_discovery import discover_web, metadata_links

GH = "https://api.github.com"
HF = "https://huggingface.co"
LINK = re.compile(r'https://(?:github\.com/[\w.-]+/[\w.-]+|huggingface\.co/(?:datasets/)?[\w.-]+/[\w.-]+)(?=[/?#\s)\]>"\x27]|$)')
ID = re.compile(r"[\w.-]+/[\w.-]+", re.ASCII)
LIMITATIONS = [
    "Owner membership is a scope hint, not proof of geography or collaboration.",
    "Bounded first two pages; not an exhaustive index.",
    "RAISE, CORDIS and OpenAIRE not enabled; endpoints and mapping require validation.",
    "Explicit references prove references only, not dependencies or cooperation.",
    "No graph advantage established; search comparison and independent review pending.",
]

def canonical(url):
    p = urllib.parse.urlsplit(url)
    parts = p.path.strip("/").split("/")
    kind = "repository" if p.netloc == "github.com" else "model"
    if p.netloc == "huggingface.co" and parts[0] == "datasets":
        kind, parts = "dataset", parts[1:]
    if p.scheme != "https" or p.netloc not in ("github.com", "huggingface.co") or len(parts) < 2:
        return None
    if parts[0].lower() in ({"topics", "orgs", "users", "search", "marketplace", "features", "collections", "settings"} if kind == "repository" else {"spaces", "collections", "organizations", "docs", "blog", "models", "datasets"}):
        return None
    name = "/".join(parts[:2])
    if kind == "repository":
        name = name.removesuffix(".git")
    if not ID.fullmatch(name) or any(x in (".", "..") for x in name.split("/")):
        return None
    return (kind, name.lower() if kind == "repository" else name)

def url_for(key):
    kind, name = key
    return ("https://github.com/" if kind == "repository" else
            HF + ("/datasets/" if kind == "dataset" else "/")) + name

def hf_json(url):
    # Never send GitHub credentials to Hugging Face.
    request = urllib.request.Request(url, headers={"User-Agent": "eu-research-graph", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)

class GitHub:
    name = "github"
    def pages(self, owner, fetch):
        for page in (1, 2):
            url = f"{GH}/orgs/{owner}/repos?type=public&sort=updated&per_page=30&page={page}"
            rows = fetch(url)
            if not isinstance(rows, list):
                raise ValueError("invalid GitHub listing")
            yield url, rows
            if len(rows) < 30:
                break
    def record(self, row):
        name = row["full_name"]
        if not ID.fullmatch(name) or row.get("private") or row.get("fork") or row.get("archived"):
            return None
        return ("repository", name.lower()), " ".join(str(row.get(k) or "") for k in ("description", "homepage"))

class HuggingFace:
    name = "huggingface"
    def pages(self, owner, fetch):
        for kind in ("models", "datasets"):
            url = f"{HF}/api/{kind}?author={owner}&limit=30&full=true"
            rows = fetch(url)
            if not isinstance(rows, list):
                raise ValueError("invalid Hugging Face listing")
            yield url, [(kind, row) for row in rows]
    def record(self, entry):
        kind, row = entry
        name = row["id"]
        if not ID.fullmatch(name) or row.get("private"):
            return None
        return ("model" if kind == "models" else "dataset", name), json.dumps(row.get("cardData") or {})

def detail_url(key):
    kind, name = key
    if kind == "repository":
        return f"{GH}/repos/{name}"
    return f"{HF}/api/{'models' if kind == 'model' else 'datasets'}/{name}"


def discover(config, *, fetch=None, previous=None, now=None, max_owners=4, max_follow=12, web_fetch=None, max_web_pages=8, publication_fetch=None, affiliation_fetch=None, ror_fetch=None, openaire_fetch=None):
    instant = now or dt.datetime.now(dt.timezone.utc)
    stamp = instant.isoformat()
    known = {("repository", x["repo"].lower()) for x in config["repositories"]}
    owners = sorted({x["repo"].split("/")[0] for x in config["repositories"]}, key=str.lower)
    if not owners:
        raise ValueError("empty seed registry")
    if max_owners < 1 or max_follow < 0:
        raise ValueError("invalid discovery budget")
    offset = instant.isocalendar().week * max_owners % len(owners)
    owners = (owners[offset:] + owners[:offset])[:max_owners]
    previous = previous or {}
    if previous and previous.get("schema") not in (1, 2):
        raise ValueError("unsupported discovery state schema")
    candidates = {x["url"]: copy.deepcopy(x) for x in previous.get("candidates", [])
                  if canonical(x["url"]) not in known}
    prior = set(candidates)
    for item in candidates.values():
        item["new"] = False
        item.setdefault("first_seen", previous.get("retrieved_at", stamp))
    edges = {(x["source"], x["target"]): copy.deepcopy(x)
             for x in previous.get("verified_references", [])}
    prior_edges = set(edges)
    expanded = dict(previous.get("expanded", {}))
    pending = list(dict.fromkeys(previous.get("pending", [])))
    # Migrate old snapshots: unresolved reference targets become the first frontier.
    if previous.get("schema") == 1:
        pending.extend(x["target"] for x in edges.values() if x["target"] not in pending)
    queued = set(pending)
    errors, cache, listings, checks = [], {}, [], []
    attempted = set()
    web_seeds = config.get('web_seeds', [])
    web_referrals = []

    def read(url):
        if url not in cache:
            attempted.add(url)
            if fetch is None:
                time.sleep(0.5)
            cache[url] = (fetch(url) if fetch else
                          get_json(url, user_agent="eu-research-graph", timeout=15, attempts=2)[0]
                          if url.startswith(GH + "/") else hf_json(url))
        return cache[url]

    def add(key, evidence, reason, identity=False):
        if key in known:
            return
        url = url_for(key)
        item = candidates.setdefault(url, {"url": url, "kind": key[0], "review_only": True,
            "verification_status": "unknown", "european_relevance": reason,
            "new": url not in prior, "first_seen": stamp, "evidence": []})
        item["last_seen"] = stamp
        if identity:
            item["identity_status"] = "confirmed_public_metadata"
        # Keep the latest observation of each distinct piece of evidence, not a weekly duplicate.
        fingerprint = lambda e: {k: v for k, v in e.items() if k != "retrieved_at"}
        item["evidence"] = [e for e in item["evidence"] if fingerprint(e) != fingerprint(evidence)]
        item["evidence"].append(evidence)

    def enqueue(key):
        url = url_for(key)
        if url not in expanded and url not in queued:
            pending.append(url)
            queued.add(url)

    def ingest(record, source, origin):
        key, description = record
        source_entity = url_for(key)
        evidence = {"source_url": source, "source_entity": source_entity,
                    "retrieved_at": stamp, "type": origin}
        add(key, evidence, "scoped discovery; affiliation unverified", identity=True)
        ingest_references(source_entity, description, evidence)

    def ingest_references(source_entity, description, evidence):
        source = evidence["source_url"]
        if web_seeds:
            for url, raw in metadata_links(description, source_entity, canonical):
                web_referrals.append((url, {**evidence, 'type': 'explicit_metadata_reference', 'excerpt': raw, 'resolved_url': url}))
        # Bound reference fan-out per record; references are evidence, not confirmed cooperation.
        targets = {}
        for match in LINK.finditer(description):
            target = canonical(match.group())
            if target and url_for(target) != source_entity:
                targets.setdefault(target, match.group())
        for target, excerpt in list(targets.items())[:20]:
            proof = {"source_url": source, "source_entity": source_entity, "retrieved_at": stamp,
                     "type": "explicit_metadata_reference", "excerpt": excerpt}
            add(target, proof, "reference from scoped source; affiliation unverified")
            pair = (source_entity, url_for(target))
            first_seen = edges.get(pair, {}).get("first_seen", stamp)
            edges[pair] = {"source": pair[0], "target": pair[1],
                "relationship": "references", "verification_status": "verified",
                "first_seen": first_seen, "last_seen": stamp, "evidence": proof}
            enqueue(target)

    for owner in owners:
        for adapter in (GitHub(), HuggingFace()):
            try:
                for source, rows in adapter.pages(owner, read):
                    listings.append({"adapter": adapter.name, "source_url": source, "count": len(rows)})
                    for row in rows:
                        try:
                            record = adapter.record(row)
                            if record:
                                ingest(record, source, "owner_listing")
                        except (ValueError, TypeError, KeyError, AttributeError) as exc:
                            errors.append({"source": source, "error": type(exc).__name__})
            except (ValueError, TypeError, KeyError, OSError) as exc:
                errors.append({"source": adapter.name, "owner": owner, "error": type(exc).__name__})

    publication_state = copy.deepcopy(previous.get("publication_discovery"))
    if config.get("arxiv_discovery", False):
        publication_state, observations = discover_publications(
            instant, previous=publication_state, fetch=publication_fetch)
        listings.extend(publication_state["listings"])
        errors.extend(publication_state["errors"])
        for paper in observations:
            proof = {"source_url": paper["source_url"], "source_entity": paper["url"],
                     "retrieved_at": stamp, "type": "publication_metadata"}
            ingest_references(paper["url"], " ".join(paper["explicit_links"]), proof)

    organization_state = copy.deepcopy(previous.get("organization_discovery"))
    if config.get("organization_discovery", False) and publication_state:
        organization_state = resolve_organizations(
            publication_state["papers"], instant, previous=organization_state,
            html_fetch=affiliation_fetch, ror_fetch=ror_fetch)
        errors.extend(organization_state["errors"])

    openaire_state = copy.deepcopy(previous.get("openaire_discovery"))
    if config.get("openaire_discovery", False) and publication_state:
        openaire_state = enrich_openaire(publication_state["papers"], instant,
                                        previous=openaire_state, fetch=openaire_fetch)
        errors.extend(openaire_state["errors"])

    # FIFO across runs. Newly discovered links may themselves yield more links.
    # Never broaden to arbitrary owner listings or execute remote content.
    for _ in range(max_follow):
        if not pending:
            break
        url = pending.pop(0)
        queued.discard(url)
        if url in expanded:
            continue
        key = canonical(url)
        if not key or url_for(key) != url:
            errors.append({"source": url, "error": "invalid frontier identity"})
            continue
        source = detail_url(key)
        try:
            row = read(source)
            if not isinstance(row, dict):
                raise ValueError("invalid detail response")
            if key[0] == "repository":
                record = GitHub().record(row)
            else:
                record = HuggingFace().record(("models" if key[0] == "model" else "datasets", row))
            if record is None:
                status = "excluded"
            elif record[0] != key:
                status = "identity_mismatch"
            else:
                ingest(record, source, "detail_lookup")
                status = "confirmed_public_metadata"
            expanded[url] = status
            # An already-listed entity retains its historical identity observation.
            if url in candidates:
                candidates[url]["detail_status"] = status
            checks.append({"url": url, "source_url": source, "status": status})
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 410):
                expanded[url] = "not_found"
                if url in candidates:
                    candidates[url]["detail_status"] = "not_found"
                checks.append({"url": url, "source_url": source, "status": "not_found"})
            else:
                errors.append({"source": source, "error": f"HTTP {exc.code}"})
                enqueue(key)
                break
        except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
            errors.append({"source": source, "error": type(exc).__name__})
            enqueue(key)
            break
    web_state = None
    if web_seeds:
        web_state = discover_web(web_seeds, previous=previous.get("web_discovery"),
                                 referrals=web_referrals, platform_key=canonical,
                                 fetch=web_fetch, now=instant, max_pages=max_web_pages)
        for reference in web_state["platform_refs"]:
            target = canonical(reference["target"])
            proof = reference["evidence"]
            add(target, proof, "public web reference; affiliation unverified")
            pair = (proof["source_entity"], url_for(target))
            edges[pair] = {"source": pair[0], "target": pair[1], "relationship": "references",
                           "verification_status": "verified",
                           "first_seen": edges.get(pair, {}).get("first_seen", stamp),
                           "last_seen": stamp, "evidence": proof}
            enqueue(target)
    return {"schema": 2, "retrieved_at": stamp, "owners": owners, "requests": len(attempted),
            "web_discovery": web_state,
            "publication_discovery": publication_state,
            "organization_discovery": organization_state,
            "openaire_discovery": openaire_state,
            "listings": listings, "detail_checks": checks, "pending": pending, "expanded": expanded,
            "new_reference_count": len(set(edges) - prior_edges),
            "candidates": sorted(candidates.values(), key=lambda x: x["url"]),
            "verified_references": sorted(edges.values(), key=lambda x: (x["source"], x["target"])),
            "hypotheses": [], "errors": errors, "limitations": LIMITATIONS +
            ["Historical observations persist; not evidence a link is still present.",
             "At most 20 distinct targets per metadata record and bounded detail requests per run.",
             "Detail lookups do not prove European affiliation; unresolved or excluded targets stay review-only.",
             "Previously expanded targets are not automatically revalidated."]}

def write_report(result, output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "source_candidates.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = ["# Automatic source discovery (review only)", "", "## New candidates"]
    lines += ["- " + x["url"] for x in result["candidates"] if x["new"]]
    lines += ["", f"Total retained candidates: {len(result['candidates'])}",
              f"New references: {result['new_reference_count']}",
              f"Pending detail lookups: {len(result['pending'])}",
              "", "## Historical verified metadata references"]
    lines += ["- " + x["source"] + " references " + x["target"] for x in result["verified_references"]]
    lines += ["", "## Collaboration hypotheses", "Not evaluated in this iteration.",
              "", "## Engineering tasks", "See existing OPPORTUNITIES.md; new sources require review.",
              "", "## Errors and limitations"]
    lines += ["- " + json.dumps(x) for x in result["errors"]]
    lines += ["- " + x for x in result["limitations"]]
    publications = result.get("publication_discovery")
    if publications:
        lines += ["", "## arXiv publication discovery (review only)",
                  f"Retained papers: {len(publications['papers'])}",
                  f"Coverage: {publications['coverage']}",
                  "Author-reported affiliations do not establish European relevance.",
                  "### New papers"]
        lines += [f"- {x['url']} — affiliation: {x['affiliation_status']}"
                  for x in publications["papers"] if x["new"]]
        lines += ["", "### Publication query diagnostics"]
        lines += ["- " + json.dumps(x) for x in publications["listings"]]
    organizations = result.get("organization_discovery")
    if organizations:
        lines += ["", "## Publication organization candidates (review only)",
                  f"Retained ROR organizations: {len(organizations['organizations'])}",
                  f"HTML requests: {organizations['html_requests']}; ROR requests: {organizations['ror_requests']}",
                  "Registry location is not proof of an author's location or headquarters."]
        for org in organizations["organizations"].values():
            lines += [f"- {org['ror_id']} — {len(org['paper_ids'])} paper(s)"]
        lines += ["", "### Organization discovery limitations"] + [
            "- " + x for x in organizations["limitations"]]
    openaire = result.get("openaire_discovery")
    if openaire:
        lines += ["", "## OpenAIRE exact-ID enrichment (review only)",
                  f"Selected papers: {len(openaire['selected'])} of {openaire['eligible_count']} eligible",
                  f"Retained paper observations: {len(openaire['papers'])}",
                  "Relationships below are OpenAIRE assertions, not independently verified facts."]
        for pid, observation in sorted(openaire["papers"].items()):
            lines += [f"- arXiv:{pid} — {observation['last_attempt_status']}"]
            for record in observation.get("records", []):
                lines += [f"  - {record['openaire_id']}: {len(record['organizations'])} organization(s), {len(record['projects'])} grant(s)"]
        lines += ["- " + x for x in openaire["limitations"]]
    web = result.get("web_discovery")
    if web:
        (out / "web_source_candidates.json").write_text(json.dumps(web, indent=2) + "\n", encoding="utf-8")
        lines += ["", "## Generic web source discovery",
                  f"Retained web sources: {len(web['sources'])}",
                  f"New web sources: {web['new_sources']}",
                  f"New web references: {web['new_references']}",
                  f"Pending web sources: {len(web['pending'])}",
                  f"Errors this run: {len(web['errors'])}",
                  f"Budget exclusions this run: {web['dropped_by_budget']}",
                  "Partial traversal; public links do not prove affiliation or collaboration.",
                  "", "### Source format / adapter review"]
        lines += [f"- {x['url']} — {x['format']} ({x['status']})"
                  for x in web["sources"].values() if x["status"] != "pending"]
        lines += ["", "### Adapter proposals (review required; not executed)"]
        lines += [f"- {x['url']} — {x['format']}: {x['action']}" for x in web["adapter_proposals"]]
        lines += ["", "### Web source diagnostics"] + ["- " + json.dumps(x) for x in web["errors"]]
    (out / "SOURCE_DISCOVERY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
