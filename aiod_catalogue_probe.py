"""Bounded read-only AI-on-Demand catalogue probe (official REST v2, stdlib).

Only the listing endpoint is used; no model content, private resources or
mutating API calls. This is a source adapter, not a collaboration matcher.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import datetime as dt
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


API_HOSTS = ("https://api.aiodp.eu", "https://api.aiod.eu")
ASSET_TYPES = ("projects", "datasets", "publications")
MAX_LIMIT = 25
MAX_PAGES = 3
MAX_BYTES = 2_000_000
USER_AGENT = "ai-research-graph/aiod-read-only-pilot"


def fetch_json(url: str, *, timeout: int = 12):
    """HTTP GET only; all URLs originate from allowlisted hosts and paths."""
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": USER_AGENT,
    }, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        size = response.headers.get("Content-Length")
        if size is not None and int(size) > MAX_BYTES:
            raise ValueError("AIoD page exceeds size limit")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("AIoD page exceeds size limit")
        return json.loads(raw.decode("utf-8"))


def url_for(host: str, asset_type: str, offset: int, limit: int) -> str:
    if host not in API_HOSTS or asset_type not in ASSET_TYPES:
        raise ValueError("Unrecognized official AIoD host or asset type")
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise ValueError("Invalid offset/limit")
    query = urllib.parse.urlencode({"offset": offset, "limit": limit})
    return f"{host}/v2/{asset_type}?{query}"


def stable_id(raw: dict, asset_type: str) -> str:
    """The AIoD v2 identifier, not a name-based or external-platform guess."""
    ident = raw.get("identifier")
    if type(ident) is int and ident > 0:
        return f"aiod:v2:{asset_type}:{ident}"
    if isinstance(ident, str) and ident.strip() and len(ident) <= 128:
        return f"aiod:v2:{asset_type}:{ident.strip()}"
    raise ValueError("AIoD asset has no usable v2 identifier")


def normalise(raw: dict, asset_type: str, host: str, page_url: str) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("Non-object AIoD asset")
    key = stable_id(raw, asset_type)
    title = raw.get("name") or raw.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"AIoD asset has no title: {key}")
    description = raw.get("description_plain") or raw.get("description") or ""
    # The live AIoD v2 projects endpoint uses {"description": {"plain": "..."}}.
    # Keep the project summary as searchable evidence without guessing from
    # arbitrary nested metadata or flattening contacts/identities.
    if isinstance(description, dict):
        description = description.get("plain", "")
    if not isinstance(description, str):
        description = ""
    original = raw.get("same_as")
    # 'same_as' is merely a supplied metadata link; not proof of identity.
    if not isinstance(original, str) or not original.startswith("https://"):
        original = None
    platform = raw.get("platform")
    platform_id = raw.get("platform_resource_identifier")
    fingerprint = hashlib.sha256(json.dumps(
        raw, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    # A v2 identifier may itself contain ':'; never reconstruct it from our
    # composite graph key because that would silently truncate the ID.
    suffix = urllib.parse.quote(str(raw["identifier"]).strip(), safe="")
    return {
        "id": key, "type": "catalogue_asset", "asset_type": asset_type,
        "title": title.strip(), "description": description[:1000],
        "url": f"{host}/v2/{asset_type}/{suffix}",
        "original_url_claim": original,
        "platform": platform if isinstance(platform, str) else None,
        "platform_resource_identifier": str(platform_id) if isinstance(platform_id, (str, int))
                                                        and not isinstance(platform_id, bool) else None,
        "source_page_url": page_url, "metadata_sha256": fingerprint,
        "evidence_level": "indexed_metadata_only",
        "new_collaboration_confirmed": False,
    }


def quality_summary(nodes: list[dict]) -> dict:
    """Detect possible duplicate metadata records, not duplicate R&D work."""
    external_urls = defaultdict(list)
    titles = defaultdict(list)
    for node in nodes:
        if node.get("original_url_claim"):
            external_urls[node["original_url_claim"]].append(node["id"])
        titles[node["title"].casefold().strip()].append(node["id"])
    shared = [
        {"claimed_external_url": url, "aiod_record_ids": ids}
        for url, ids in sorted(external_urls.items()) if len(ids) > 1
    ]
    repeated_titles = [
        {"normalized_title": title, "aiod_record_ids": ids}
        for title, ids in sorted(titles.items()) if len(ids) > 1
    ]
    return {
        "grain": "AIoD v2 catalogue record, not unique underlying research project",
        "description_present": sum(bool(n["description"]) for n in nodes),
        "same_claimed_url_groups": shared,
        "records_in_same_claimed_url_groups": sum(len(g["aiod_record_ids"]) for g in shared),
        "same_title_groups": repeated_titles,
        "records_in_same_title_groups": sum(len(g["aiod_record_ids"]) for g in repeated_titles),
        "scope": "Sample-only indicators; external identities not verified",
    }


def collect(asset_type: str, *, host: str = API_HOSTS[0], offset: int = 0,
            limit: int = 10, pages: int = 1, fetch=fetch_json,
            now: dt.datetime | None = None) -> dict:
    if type(pages) is not int or not 1 <= pages <= MAX_PAGES:
        raise ValueError("Page count outside bounded pilot")
    if now is None:
        now = dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Expected timezone-aware timestamp")
    # Validate parameters and URL before making the first request.
    url_for(host, asset_type, offset, limit)
    nodes, seen, sources = [], set(), []
    last_full = False
    for n in range(pages):
        page_url = url_for(host, asset_type, offset + n * limit, limit)
        page = fetch(page_url)
        # Official SDK documents a list[dict] for list endpoints. Do not
        # silently interpret unknown wrappers or mix versions.
        if not isinstance(page, list) or len(page) > limit:
            raise ValueError("Unexpected AIoD v2 list response or oversized page")
        sources.append({"url": page_url, "items": len(page)})
        for raw in page:
            node = normalise(raw, asset_type, host, page_url)
            if node["id"] in seen:
                raise ValueError(f"Duplicate v2 identifier across AIoD pages: {node['id']}")
            seen.add(node["id"])
            nodes.append(node)
        last_full = len(page) == limit
        if not last_full:
            break
    return {
        "schema": 1, "source": "aiod_metadata_v2", "status": "sampled_read_only",
        "generated_at_utc": now.isoformat(), "asset_type": asset_type,
        "api_host": host, "requested_offset": offset, "requested_limit": limit,
        "pages_fetched": len(sources), "sample_limited": last_full,
        "items": len(nodes), "source_pages": sources, "nodes": nodes,
        "data_quality": quality_summary(nodes),
        "novel_collaboration_confirmed": False,
        "limitations": "Bounded REST v2 metadata sample only; a full page does not prove completeness. "
                       "No semantic matching, person/contact inference, artifact reuse or source-side "
                       "execution was verified; platform URLs are metadata claims.",
    }


def markdown(result: dict) -> str:
    lines = [f"# AI-on-Demand — {result['asset_type']} metadata probe", "",
             f"**{result['items']}** entries from {result['pages_fetched']} bounded API pages. "
             f"Sample-limited: **{result['sample_limited']}**.", "",
             "Only the catalogue's claims are recorded, not confirmed collaboration.", ""]
    for node in result["nodes"]:
        title = node["title"].replace("\n", " ").replace("|", "\\|")
        lines.append(f"- **{title}** — [catalogue record]({node['url']}) "
                     f"(metadata SHA256 `{node['metadata_sha256']}`)")
        if node["original_url_claim"]:
            lines.append(f"  - [Claimed external source]({node['original_url_claim']}); identity unverified")
    qa = result["data_quality"]
    lines += ["", "## Catalogue data quality (sample only)", "",
              f"Description present: {qa['description_present']} / {result['items']}; "
              f"records sharing an external-URL claim: "
              f"{qa['records_in_same_claimed_url_groups']} "
              f"in {len(qa['same_claimed_url_groups'])} groups. ",
              "These are possible duplicate **metadata records**, not proof "
              "that independent researchers duplicated work.", ""]
    for group in qa["same_claimed_url_groups"]:
        lines.append(f"- [Shared claimed URL]({group['claimed_external_url']}): "
                     + ", ".join(f"`{id}`" for id in group["aiod_record_ids"]))
    lines += ["", "## Limitations", "", result["limitations"], ""]
    return "\n".join(lines)


def write_success(result: dict, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / result["asset_type"]
    # Both representations are prepared before any durable replacement.
    content = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    human = markdown(result)
    (path.with_suffix(".json")).write_text(content, encoding="utf-8")
    (path.with_suffix(".md")).write_text(human, encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--type", choices=ASSET_TYPES, default="projects")
    parser.add_argument("--host", choices=API_HOSTS, default=API_HOSTS[0])
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--output", default="results/aiod")
    args = parser.parse_args(argv)
    try:
        result = collect(args.type, host=args.host, offset=args.offset,
                         limit=args.limit, pages=args.pages)
        write_success(result, Path(args.output))
        print(f"AIoD {args.type}: sampled {result['items']} v2 catalogue records")
        return 0
    except (OSError, ValueError, TypeError, KeyError, urllib.error.URLError,
            urllib.error.HTTPError, json.JSONDecodeError) as exc:
        # Never destroy the last successful report if the remote API fails.
        print(f"AIoD source_error (previous good results preserved): "
              f"{type(exc).__name__}: {str(exc)[:160]}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
