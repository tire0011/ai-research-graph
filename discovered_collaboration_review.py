"""Bounded bridge from discovered repositories to the existing collaboration matcher."""
import datetime as dt
from urllib.parse import urlencode

import collaboration_matcher as cm
import collaboration_review as cr

BLOCKED = {"contacted","contacted_no_followup","dismissed","already_handled","resolved"}

def contact_review(config, left, right):
    pair = {left.casefold(), right.casefold()}
    for entry in config.get("connection_reviews", []):
        owners = entry.get("github_owners", [])
        if len(owners) == 2 and {x.casefold() for x in owners} == pair:
            return {"id":entry["id"], "status":entry["status"],
                    "suppress_outreach":entry["status"] in BLOCKED}
    return {"status":"unknown", "suppress_outreach":False}

def prepare_discovered(config, metadata, fetch, *, now, max_repos=4, max_cards=10):
    if not 2 <= max_repos <= 6 or not 1 <= max_cards <= 10:
        raise ValueError("invalid matching budget")
    # Select distinct owners first from the already inspected metadata.
    eligible = sorted((m for m in metadata if m.get("status")=="review_only"
                       and m.get("has_issues") and m.get("recent_push")
                       and m.get("technical_signals")), key=lambda m:m["repo"].casefold())
    repos, owners = [], set()
    for m in eligible:
        owner = m["repo"].split("/")[0].casefold()
        if owner not in owners:
            owners.add(owner)
            repos.append(m["repo"])
        if len(repos)==max_repos:
            break
    errors, items, inventories = [], [], {}
    for repo in repos:
        url = f"{cm.API}/{repo}/issues?" + urlencode({"state":"all","per_page":30,"sort":"updated","direction":"desc"})
        try:
            rows = fetch(url)
            if not isinstance(rows,list) or len(rows)>30:
                raise ValueError("invalid issue page")
            parsed = [cm.normalize_issue(repo,row) for row in rows]
            if len({x["id"] for x in parsed})!=len(parsed):
                raise ValueError("duplicate issue")
            items.extend(parsed)
            inventories[repo]={"source_url":url,"count":len(parsed),"possibly_truncated":len(rows)==30}
        except (OSError,ValueError,TypeError,KeyError,AttributeError) as exc:
            errors.append({"source":url,"error":type(exc).__name__})
    scoped={"source_owners":[repo.split("/")[0] for repo in repos],
            "source_max_age_days":400,"max_body_chars_for_matching":6000,
            "min_score":7,"max_suggestions":max_cards,"max_suggestions_per_source":2}
    cards, stats = cm.rank_pairs(items,scoped,now)
    packets, suppressed = [], []
    for card in cards:
        contact = contact_review(config,card["source"]["repo"].split("/")[0],
                                 card["target"]["repo"].split("/")[0])
        if contact["suppress_outreach"]:
            suppressed.append({"candidate":card,"contact_review":contact})
            continue
        try:
            packet = cr.prepare(card,fetch=fetch,check_public=True)
            packets.append({"candidate":card,"packet":packet,"contact_review":contact,
                            "status":"awaiting_independent_requirement_and_artifact_review",
                            "outreach_approved":False})
        except (OSError,ValueError,TypeError,KeyError,AttributeError) as exc:
            errors.append({"candidate_id":card["id"],"error":type(exc).__name__})
    return {"schema":1,"repositories":repos,"inventories":inventories,"items_indexed":len(items),
            "candidate_count":len(cards),"packets":packets,"suppressed_contact_candidates":suppressed,
            "baseline":stats,"errors":errors,"review_only":True,
            "limitations":["Recent single-page issue sample, not exhaustive.",
                           "Reuses existing lexical retrieval, not proof of technical fit.",
                           "Original issue and coordination packet only; human/LLM review must specify handoff and license.",
                           "At most ten candidate cards; evaluation still requires independent labels and same-input baseline."]}
