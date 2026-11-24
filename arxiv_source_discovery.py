"""Bounded arXiv metadata discovery; affiliations are observations, not EU proof."""
import copy
import datetime as dt
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

API = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"
OS = "{http://a9.com/-/spec/opensearch/1.1/}"
MAX_BYTES = 4 * 1024 * 1024
QUERIES = (
    '(cat:cs.AI OR cat:cs.LG OR cat:cs.CL) AND (ti:"large language model" OR ti:LLM OR ti:"model compression")',
    '(cat:quant-ph OR cat:cs.AI OR cat:cs.LG) AND (ti:quantum OR abs:"quantum neural network") AND (abs:"language model" OR abs:transformer OR abs:"machine learning")',
)
ID = re.compile(r"(?:\d{4}\.\d{4,5}|[a-zA-Z][\w.-]*/\d{7})(?:v[1-9]\d*)?")
URL = re.compile(r'https://[^\s<>"\x27\]\)]+')

def fetch_atom(url):
    request = urllib.request.Request(url, headers={"User-Agent": "ai-research-graph/1.0 (https://github.com/tire0011/ai-research-graph)", "Accept": "application/atom+xml"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read(MAX_BYTES + 1)

def parse_atom(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES or re.search(br"<!DOCTYPE|<!ENTITY", raw, re.I):
        raise ValueError("invalid or oversized XML")
    root = ET.fromstring(raw)
    if root.tag != ATOM + "feed":
        raise ValueError("not an Atom feed")
    total = int(root.findtext(OS + "totalResults", "-1"))
    start = int(root.findtext(OS + "startIndex", "-1"))
    if total < 0 or start < 0:
        raise ValueError("missing pagination metadata")
    rows = []
    for entry in root.findall(ATOM + "entry"):
        def value(tag):
            return " ".join((entry.findtext(tag) or "").split())
        raw_id = value(ATOM + "id")
        p = urllib.parse.urlsplit(raw_id)
        identifier = p.path.removeprefix("/abs/")
        if p.scheme not in ("http", "https") or p.netloc not in ("arxiv.org", "export.arxiv.org") or not p.path.startswith("/abs/") or not ID.fullmatch(identifier):
            raise ValueError("invalid paper ID or arXiv error entry")
        canonical = re.sub(r"v\d+$", "", identifier)
        title = value(ATOM + "title")
        published, updated = value(ATOM + "published"), value(ATOM + "updated")
        if not title or not published or not updated:
            raise ValueError("incomplete paper metadata")
        for stamp in (published, updated):
            if dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")).tzinfo is None:
                raise ValueError("missing time zone")
        authors = []
        for author in entry.findall(ATOM + "author"):
            affiliations = sorted({" ".join(x.text.split()) for x in author.findall(ARXIV + "affiliation") if x.text and x.text.strip()})
            authors.append({"name": " ".join((author.findtext(ATOM + "name") or "").split()),
                            "affiliations": affiliations})
        # Retain literal link observations, not the full abstract or paper.
        source_text = " ".join(value(t) for t in (ATOM + "summary", ARXIV + "comment"))
        links = sorted({m.group().rstrip(".,;:") for m in URL.finditer(source_text)})
        rows.append({"id": canonical, "version_id": identifier,
                     "url": "https://arxiv.org/abs/" + identifier,
                     "title": title, "published": published, "updated": updated,
                     "authors": authors, "categories": sorted({x.get("term") for x in entry.findall(ATOM + "category") if x.get("term")}),
                     "explicit_links": links[:20], "links_truncated": len(links) > 20,
                     "affiliation_status": "author_reported" if any(x["affiliations"] for x in authors) else "unknown",
                     "european_relevance": "unknown", "review_only": True})
    if len(rows) > total or (not rows and start < total):
        raise ValueError("inconsistent pagination")
    return total, start, rows

def discover_publications(now, *, previous=None, fetch=None, days=21, page_size=50, max_pages=2):
    if not (1 <= days <= 90 and 1 <= page_size <= 100 and 1 <= max_pages <= 4):
        raise ValueError("invalid publication budget")
    previous = previous or {}
    stamp = now.isoformat()
    papers = {x["id"]: copy.deepcopy(x) for x in previous.get("papers", [])}
    for paper in papers.values():
        paper["new"] = False
    prior = set(papers)
    listings, errors, observations = [], [], []
    lower = (now - dt.timedelta(days=days)).strftime("%Y%m%d%H%M")
    upper = now.strftime("%Y%m%d%H%M")
    requests = 0
    for query in QUERIES:
        for page in range(max_pages):
            offset = page * page_size
            url = API + "?" + urllib.parse.urlencode({
                "search_query": f"({query}) AND submittedDate:[{lower} TO {upper}]",
                "sortBy": "submittedDate", "sortOrder": "descending",
                "start": offset, "max_results": page_size})
            if requests and fetch is None:
                time.sleep(3.1)
            requests += 1
            try:
                total, start, rows = parse_atom((fetch or fetch_atom)(url))
                if start != offset or len(rows) > page_size:
                    raise ValueError("unexpected page")
                truncated = offset + len(rows) < total and page == max_pages - 1
                listings.append({"adapter": "arxiv", "source_url": url, "count": len(rows),
                                 "total": total, "truncated": truncated})
                for row in rows:
                    row.update({"retrieved_at": stamp, "source_url": url, "new": row["id"] not in prior})
                    old = papers.get(row["id"], {})
                    row["first_seen"] = old.get("first_seen", stamp)
                    if not old or row["updated"] >= old["updated"]:
                        papers[row["id"]] = row
                    observations.append(row)
                if offset + len(rows) >= total:
                    break
                if len(rows) != page_size:
                    raise ValueError("incomplete page")
            except (OSError, ValueError, TypeError, ET.ParseError) as exc:
                errors.append({"source": url, "error": type(exc).__name__})
                break
    return {"schema": 1, "retrieved_at": stamp, "window": [lower, upper],
            "requests": requests, "papers": sorted(papers.values(), key=lambda x: x["id"]),
            "listings": listings, "errors": errors,
            "coverage": "partial" if errors or any(x["truncated"] for x in listings) else "bounded_query_results"}, observations
