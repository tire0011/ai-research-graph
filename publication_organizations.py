"""Resolve explicit publication affiliations conservatively using arXiv HTML and ROR v2."""
import copy
import datetime as dt
from html.parser import HTMLParser
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

ROR_API = "https://api.ror.org/v2/organizations"
EU = set("AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE".split())
ROR_ID = re.compile(r"https://ror\.org/0[a-z0-9]{8}")
VERSION = re.compile(r"(?:\d{4}\.\d{4,5}|[a-zA-Z][\w.-]*/\d{7})v[1-9]\d*")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
MAX_HTML = 512 * 1024
MAX_JSON = 2 * 1024 * 1024

class AffiliationParser(HTMLParser):
    """Only collect explicit LaTeXML affiliation elements inside the author header."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.capture = None
        self.parts = []
        self.affiliations = []
        self.complete = False

    def handle_starttag(self, tag, attrs):
        if self.complete or tag in VOID:
            return
        classes = set(dict(attrs).get("class", "").split())
        self.stack.append((tag, classes))
        in_authors = any("ltx_authors" in x[1] for x in self.stack)
        if in_authors and self.capture is None and "ltx_role_affiliation" in classes:
            self.capture = len(self.stack)
            self.parts = []

    def handle_startendtag(self, tag, attrs):
        if tag not in VOID:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self.capture is not None and not self.complete:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.complete or tag in VOID:
            return
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                if self.capture is not None and i < self.capture:
                    raw = " ".join(" ".join(self.parts).split())
                    raw = re.sub(r"^Affiliation\s*:\s*", "", raw, flags=re.I)
                    if 2 <= len(raw) <= 500:
                        self.affiliations.append(raw)
                    self.capture = None
                if any("ltx_authors" in x[1] for x in self.stack[i:]):
                    self.complete = True
                del self.stack[i:]
                break

def parse_affiliations(html):
    parser = AffiliationParser()
    parser.feed(html)
    if not parser.complete:
        raise ValueError("author header unavailable or incomplete")
    return sorted(set(parser.affiliations))

def request_bytes(url, limit):
    request = urllib.request.Request(url, headers={"User-Agent": "ai-research-graph/1.0 (https://github.com/tire0011/ai-research-graph)"})
    with urllib.request.urlopen(request, timeout=20) as response:
        if urllib.parse.urlsplit(response.geturl()).hostname != urllib.parse.urlsplit(url).hostname:
            raise ValueError("unexpected response host")
        return response.read(limit + 1)

def html_affiliations(url):
    return parse_affiliations(request_bytes(url, MAX_HTML)[:MAX_HTML].decode("utf-8", errors="replace"))

def ror_json(url):
    raw = request_bytes(url, MAX_JSON)
    if len(raw) > MAX_JSON:
        raise ValueError("oversized ROR response")
    return json.loads(raw)

def parse_ror(payload):
    items = payload["items"]
    if not isinstance(items, list):
        raise ValueError("invalid ROR items")
    chosen = [x for x in items if x.get("chosen") is True]
    if len(chosen) != 1:
        return {"status": "ambiguous" if len(chosen) > 1 else "unresolved"}
    match = chosen[0]
    org = match["organization"]
    if org.get("status") != "active" or not ROR_ID.fullmatch(org.get("id", "")):
        return {"status": "unresolved"}
    countries = sorted({x["geonames_details"]["country_code"] for x in org.get("locations", [])
                        if re.fullmatch(r"[A-Z]{2}", x.get("geonames_details", {}).get("country_code") or "")})
    names = [x["value"] for x in org.get("names", []) if "ror_display" in x.get("types", [])]
    # ROR chosen is an algorithmic match, not independently verified author identity.
    return {"status": "registry_match_candidate", "ror_id": org["id"],
            "name": names[0] if names else None, "countries": countries,
            "eu_location": "listed" if EU.intersection(countries) else "not_listed" if countries else "unknown",
            "score": match.get("score"), "matching_type": match.get("matching_type"),
            "matched_substring": match.get("substring")}

def source_error(url, exc):
    diagnostic = {"source": url, "error": type(exc).__name__}
    if isinstance(exc, urllib.error.HTTPError):
        diagnostic["http_status"] = exc.code
        diagnostic["retryable"] = exc.code == 429 or 500 <= exc.code <= 599
        if exc.headers and exc.headers.get("Retry-After"):
            diagnostic["retry_after"] = exc.headers["Retry-After"]
    return diagnostic


def resolve(papers, now, *, previous=None, html_fetch=None, ror_fetch=None,
            max_papers=6, max_ror=16):
    if not (0 <= max_papers <= 12 and 0 <= max_ror <= 32):
        raise ValueError("invalid organization budget")
    previous = previous or {}
    records = copy.deepcopy(previous.get("papers", {}))
    cache = copy.deepcopy(previous.get("ror_cache", {}))
    stamp = now.isoformat()
    errors = []
    requests = 0
    html_requests = 0
    # Least-recently attempted first, with new paper versions eligible immediately.
    def priority(p):
        old = records.get(p["id"], {})
        return (old.get("attempted_at", "") if old.get("version_id") == p["version_id"] else "",
                p["id"])
    selected = sorted(papers, key=priority)[:max_papers]
    for paper in selected:
        pid, version = paper["id"], paper["version_id"]
        if not VERSION.fullmatch(version) or re.sub(r"v\d+$", "", version) != pid:
            errors.append({"paper_id": pid, "error": "invalid version"})
            continue
        source = "https://arxiv.org/abs/" + version
        raw = sorted({a for x in paper.get("authors", []) for a in x.get("affiliations", [])
                      if isinstance(a, str) and 2 <= len(a) <= 500})
        old = records.get(pid, {})
        sources = {a: source for a in raw}
        html_status = "not_needed"
        html_http_status = None
        if not raw:
            source = "https://arxiv.org/html/" + version
            if old.get("version_id") == version and old.get("html_status") == "read":
                raw = old.get("raw_affiliations", [])
                html_status = "read"
            else:
                if html_requests and html_fetch is None:
                    time.sleep(3.1)
                html_requests += 1
                try:
                    raw = (html_fetch or html_affiliations)(source)
                    html_status = "read"
                except urllib.error.HTTPError as exc:
                    html_http_status = exc.code
                    if exc.code in (404, 410):
                        # Optional HTML rendition missing, not negative affiliation evidence.
                        html_status = "not_found"
                    else:
                        html_status = "unavailable"
                        errors.append(source_error(source, exc))
                except (OSError, ValueError, TypeError) as exc:
                    html_status = "unavailable"
                    errors.append(source_error(source, exc))
            sources = {a: source for a in raw}
        matches = []
        for affiliation in raw[:30]:
            key = affiliation
            url = ROR_API + "?" + urllib.parse.urlencode({"affiliation": affiliation})
            cached = cache.get(key)
            if cached and now - dt.datetime.fromisoformat(cached["retrieved_at"]) < dt.timedelta(days=30):
                result = cached
            elif requests >= max_ror:
                result = {"status": "deferred_budget"}
            else:
                if requests and ror_fetch is None:
                    time.sleep(0.25)
                requests += 1
                try:
                    result = {**parse_ror((ror_fetch or ror_json)(url)),
                              "source_url": url, "retrieved_at": stamp}
                    cache[key] = result
                except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
                    result = {"status": "source_error"}
                    errors.append(source_error(url, exc))
            matches.append({"raw_affiliation": affiliation, "publication_source_url": sources[affiliation],
                            **result})
        records[pid] = {"paper_id": pid, "version_id": version, "attempted_at": stamp,
                        "html_status": html_status, "html_http_status": html_http_status,
                        "raw_affiliations": raw,
                        "affiliations": matches, "affiliations_truncated": len(raw) > 30,
                        "review_only": True, "european_affiliation_verified": False}
    organizations = {}
    for record in records.values():
        for match in record["affiliations"]:
            if match["status"] == "registry_match_candidate":
                org = organizations.setdefault(match["ror_id"], {"ror_id": match["ror_id"],
                    "paper_ids": [], "observations": [], "review_only": True})
                org["paper_ids"].append(record["paper_id"])
                org["observations"].append({**match, "paper_id": record["paper_id"]})
    for org in organizations.values():
        org["paper_ids"] = sorted(set(org["paper_ids"]))
    return {"schema": 1, "retrieved_at": stamp, "papers": records, "ror_cache": cache,
            "organizations": organizations, "selected": [p["id"] for p in selected],
            "html_requests": html_requests, "ror_requests": requests, "errors": errors,
            "limitations": ["Explicit paper-level affiliations; no inferred author identity from HTML.",
                            "ROR chosen is a candidate match; locations do not prove headquarters or individual affiliation.",
                            "Unknown or missing matches remain review-only; no automatic promotion."]}
