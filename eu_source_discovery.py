"""Bounded source expansion for the European opportunity pipeline (review only)."""
import datetime as dt
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from http_util import get_json

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
    name = "/".join(parts[:2]).removesuffix(".git")
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

def discover(config, *, fetch=None, previous=None, now=None, max_owners=4):
    stamp = (now or dt.datetime.now(dt.timezone.utc)).isoformat()
    known = {("repository", x["repo"].lower()) for x in config["repositories"]}
    owners = sorted({x["repo"].split("/")[0] for x in config["repositories"]}, key=str.lower)
    # Rotate the bounded owner sample weekly to avoid starving later owners.
    offset = (now or dt.datetime.now(dt.timezone.utc)).isocalendar().week * max_owners % len(owners)
    owners = (owners[offset:] + owners[:offset])[:max_owners]
    candidates, edges, errors, cache = {}, {}, [], {}
    prior = {x["url"] for x in (previous or {}).get("candidates", [])}
    def read(url):
        if url not in cache:
            if fetch is None:
                time.sleep(0.5)
            cache[url] = (fetch(url) if fetch else
                          get_json(url, user_agent="eu-research-graph", timeout=15, attempts=2)[0]
                          if url.startswith(GH + "/") else hf_json(url))
        return cache[url]
    def add(key, evidence, reason):
        if key not in known:
            url = url_for(key)
            item = candidates.setdefault(url, {"url": url, "kind": key[0], "review_only": True,
                "verification_status": "unknown", "european_relevance": reason,
                "new": url not in prior, "evidence": []})
            if evidence not in item["evidence"]:
                item["evidence"].append(evidence)
    for owner in owners:
        for adapter in (GitHub(), HuggingFace()):
            try:
                for source, rows in adapter.pages(owner, read):
                    for row in rows:
                        try:
                            record = adapter.record(row)
                            if not record:
                                continue
                            key, description = record
                            evidence = {"source_url": source, "retrieved_at": stamp, "type": "owner_listing"}
                            add(key, evidence, "registry owner search; affiliation unverified")
                            for match in LINK.finditer(description):
                                target = canonical(match.group())
                                if not target or target == key:
                                    continue
                                proof = {"source_url": source, "retrieved_at": stamp,
                                         "type": "explicit_metadata_reference", "excerpt": match.group()}
                                add(target, proof, "reference from scoped source; affiliation unverified")
                                pair = (url_for(key), url_for(target))
                                edges[pair] = {"source": pair[0], "target": pair[1],
                                    "relationship": "references", "verification_status": "verified",
                                    "evidence": proof}
                        except (ValueError, TypeError, KeyError, AttributeError) as exc:
                            errors.append({"source": source, "error": type(exc).__name__})
            except (ValueError, TypeError, KeyError, OSError) as exc:
                errors.append({"source": adapter.name, "owner": owner, "error": type(exc).__name__})
    return {"schema": 1, "retrieved_at": stamp, "owners": owners, "requests": len(cache),
            "candidates": sorted(candidates.values(), key=lambda x: x["url"]),
            "verified_references": sorted(edges.values(), key=lambda x: (x["source"], x["target"])),
            "hypotheses": [], "errors": errors, "limitations": LIMITATIONS}

def write_report(result, output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "source_candidates.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = ["# Automatic source discovery (review only)", "", "## New candidates"]
    lines += ["- " + x["url"] for x in result["candidates"] if x["new"]]
    lines += ["", "## Verified metadata references"]
    lines += ["- " + x["source"] + " references " + x["target"] for x in result["verified_references"]]
    lines += ["", "## Collaboration hypotheses", "Not evaluated in this iteration.",
              "", "## Engineering tasks", "See existing OPPORTUNITIES.md; new sources require review.",
              "", "## Errors and limitations"]
    lines += ["- " + json.dumps(x) for x in result["errors"]]
    lines += ["- " + x for x in result["limitations"]]
    (out / "SOURCE_DISCOVERY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
