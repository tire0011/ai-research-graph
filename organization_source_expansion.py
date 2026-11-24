"""Bounded organization-driven expansion using registry websites and research products."""
import copy
import datetime as dt
import urllib.parse
import time

from generic_source_discovery import public_url
from publication_organizations import EU, ROR_ID, ROR_API, ror_json
from publication_openaire import API as OA_API
from research_graph import fetch_json, openaire_node

def registry_record(rid, payload):
    if payload.get("id") != rid or payload.get("status") != "active":
        return {"status": "identity_or_status_mismatch", "websites": [], "countries": []}
    countries = sorted({x.get("geonames_details", {}).get("country_code")
                        for x in payload.get("locations", [])
                        if x.get("geonames_details", {}).get("country_code") in EU})
    if not countries:
        return {"status": "outside_eu_scope", "websites": [], "countries": []}
    websites = {}
    for link in payload.get("links", []):
        raw = link.get("value")
        url = public_url(raw)
        if link.get("type") == "website" and url:
            websites[url] = raw
    return {"status": "registry_identity_matched", "countries": countries,
            "websites": [{"url": u, "raw": websites[u]} for u in sorted(websites)[:2]],
            "websites_truncated": len(websites) > 2}

def research_url(rid, now):
    if not ROR_ID.fullmatch(rid):
        raise ValueError("invalid ROR identifier")
    since = (now - dt.timedelta(days=90)).date().isoformat()
    return OA_API + "?" + urllib.parse.urlencode({
        "filter": f"authorships.institutions.ror:{rid},from_publication_date:{since},title_and_abstract.search:large language model",
        "sort": "publication_date:desc", "page_size": 5,
        "select": "id,pids,mainTitle,type,publicationDate,organizations,codeRepositoryUrl"})

def research_records(payload):
    rows, total = payload["results"], payload["header"]["numFound"]
    if not isinstance(rows, list) or type(total) is not int or total < len(rows) or len(rows) > 5 or (total and not rows):
        raise ValueError("invalid research-product page")
    products = {}
    for row in rows:
        rid = row.get("id")
        if not isinstance(rid, str) or not rid or len(rid) > 300:
            raise ValueError("missing research-product identity")
        node = openaire_node(row)
        products[rid] = {"openaire_id": rid, "title": node["title"],
                         "identifiers": node["identifiers"], "type": row.get("type"),
                         "publication_date": row.get("publicationDate"),
                         "organizations": row.get("organizations") or [],
                         "code_repository": public_url(row.get("codeRepositoryUrl")),
                         "relationship": "openaire_org_filter_candidate", "review_only": True}
    return {"status": "returned_candidates" if rows else "no_results",
            "total": total, "truncated": total > len(rows),
            "products": [products[k] for k in sorted(products)]}

def expand(organization_state, now, *, previous=None, registry_fetch=None, research_fetch=None, max_organizations=3):
    if not 0 <= max_organizations <= 6:
        raise ValueError("invalid organization expansion budget")
    previous = previous or {}
    records = copy.deepcopy(previous.get("organizations", {}))
    stamp = now.isoformat()
    errors, referrals, selected = [], [], []
    pool = {}
    for rid, org in organization_state.get("organizations", {}).items():
        if not ROR_ID.fullmatch(rid):
            continue
        proofs = [x for x in org.get("observations", [])
                  if x.get("status") == "registry_match_candidate"
                  and x.get("ror_id") == rid and x.get("eu_location") == "listed"]
        if proofs:
            pool[rid] = sorted({x["paper_id"] for x in proofs})
    def eligible(rid):
        old = records.get(rid, {})
        if not old.get("attempted_at"):
            return True
        ttl = 7 if old.get("last_attempt_status") == "source_error" else 28
        return now - dt.datetime.fromisoformat(old["attempted_at"]) >= dt.timedelta(days=ttl)
    queue = sorted((rid for rid in pool if eligible(rid)),
                   key=lambda rid: (records.get(rid, {}).get("attempted_at", ""), rid))
    for rid in queue[:max_organizations]:
        if selected and registry_fetch is None:
            time.sleep(1)
        selected.append(rid)
        source = ROR_API + "/" + rid.rsplit("/", 1)[1]
        old = records.get(rid, {})
        record = {**old, "attempted_at": stamp, "paper_ids": pool[rid], "review_only": True}
        try:
            registry = registry_record(rid, (registry_fetch or ror_json)(source))
            record.update(registry=registry, registry_source_url=source, registry_retrieved_at=stamp,
                          last_attempt_status=registry["status"])
            if registry["status"] == "registry_identity_matched":
                for site in registry["websites"]:
                    referrals.append((site["url"], {"source_url": source, "source_entity": rid,
                        "retrieved_at": stamp, "type": "ror_registry_website", "excerpt": site["raw"],
                        "resolved_url": site["url"]}))
                url = research_url(rid, now)
                try:
                    products = research_records((research_fetch or (lambda u: fetch_json(u, timeout=25)))(url))
                    record.update(research=products, research_source_url=url, research_retrieved_at=stamp)
                    for product in products["products"]:
                        code = product["code_repository"]
                        if code:
                            referrals.append((code, {"source_url": url, "source_entity": "openaire:" + product["openaire_id"],
                                "retrieved_at": stamp, "type": "openaire_code_repository_metadata",
                                "excerpt": code, "resolved_url": code}))
                except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
                    record["last_attempt_status"] = "source_error"
                    errors.append({"source": url, "error": type(exc).__name__})
            else:
                # A stale previous observation is historical, not a current referral.
                record.pop("research", None)
                record.pop("research_source_url", None)
                record.pop("research_retrieved_at", None)
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            record["last_attempt_status"] = "source_error"
            errors.append({"source": source, "error": type(exc).__name__})
        records[rid] = record
    return {"schema": 1, "retrieved_at": stamp, "organizations": records,
            "selected": selected, "eligible_count": len(queue), "errors": errors,
            "limitations": ["EU-27 ROR location candidates only; registry identity is not proof of a paper affiliation.",
                            "Official website metadata and research-product query results are source assertions, not cooperation.",
                            "OpenAIRE returns a bounded topical sample; results are not fed back into arXiv until version identity is independently checked.",
                            "Unmatched organizations are not expanded by guessing names or domains."]}, referrals
