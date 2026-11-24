"""Bounded, read-only discovery of public web sources; never execute remote content."""
import copy
import datetime as dt
import hashlib
import http.client
import ipaddress
import json
import re
import socket
import ssl
import time
import urllib.parse as up
import urllib.robotparser
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

AGENT = "EUResearchGraph"
MAX_BYTES = 1024 * 1024
MAX_SOURCES = 5000
MAX_LINKS = 30
SIGNAL = re.compile(r"research|science|project|initiative|observatory|catalog|resource|dataset|model|open.?source|artificial|machine.learning|(?:^|[\W_])ai(?:$|[\W_])|api|feed|publication|software|infrastructure|community|partner|consortium|data|github|huggingface", re.I)
SKIP = re.compile(r"privacy|cookie|imprint|legal|login|logout|sign.?up|register|contact|subscribe|donate|share|calendar|wp-admin|wp-login|\.pdf$|\.zip$|\.png$|\.jpg$|\.svg$|\.mp4$", re.I)
SOCIAL = {"facebook.com", "instagram.com", "linkedin.com", "youtube.com", "youtu.be", "x.com", "twitter.com", "t.co"}
URL_PATTERN = re.compile(r'https://[^\s<>"\x27\]\)\\]+', re.ASCII)


def public_url(raw, base=None):
    """Canonical public HTTPS URL, no credentials, query, fragment or nonstandard ports."""
    if not isinstance(raw, str) or len(raw) > 2048 or any(ord(c) < 33 or ord(c) == 127 for c in raw):
        return None
    if "\\" in raw:
        return None
    try:
        p = up.urlsplit(up.urljoin(base or "", raw))
        host = p.hostname
        if p.scheme != "https" or not host or p.username or p.password or p.port not in (None, 443) or p.query:
            return None
        host = host.rstrip(".").encode("idna").decode("ascii").lower()
        if not re.fullmatch(r"[a-z0-9.-]+", host) or "." not in host:
            return None
        if any(not part or len(part) > 63 or part.startswith("-") or part.endswith("-") for part in host.split(".")):
            return None
        try:
            ipaddress.ip_address(host)
            return None  # Only DNS hostnames, even for public literals.
        except ValueError:
            pass
        if host.endswith((".local", ".localhost", ".internal", ".test", ".invalid", ".onion")):
            return None
        path = p.path or "/"
        if len(path) > 1000 or not path.isascii() or re.search(r"%(?:00|0a|0d|2f|5c)", path, re.I):
            return None
        return up.urlunsplit(("https", host, path, "", ""))
    except (ValueError, UnicodeError):
        return None


def public_addresses(host, resolver=socket.getaddrinfo):
    rows = resolver(host, 443, type=socket.SOCK_STREAM)
    addresses = list(dict.fromkeys(row[4][0] for row in rows))
    if not addresses or any(not ipaddress.ip_address(ip).is_global or
                            ipaddress.ip_address(ip).is_multicast for ip in addresses):
        raise ValueError("non-public DNS answer")
    return addresses


class PublicFetcher:
    """Pin validated DNS address to the TLS connection (no proxy, cookies or tokens)."""
    def __init__(self, budget=40):
        self.budget = budget
        self.requests = 0
        self.robots = {}
        self.last = {}

    def _get(self, url, delay=1):
        if public_url(url) != url:
            raise ValueError("invalid public URL")
        if self.requests >= self.budget:
            raise TimeoutError("request budget exhausted")
        p = up.urlsplit(url)
        host = p.hostname
        ip = public_addresses(host)[0]
        wait = delay - (time.monotonic() - self.last.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        self.requests += 1
        self.last[host] = time.monotonic()
        conn = http.client.HTTPSConnection(host, timeout=8)
        raw = socket.create_connection((ip, 443), timeout=8)
        try:
            # TLS certificate verification and SNI still use the original hostname.
            conn.sock = ssl.create_default_context().wrap_socket(raw, server_hostname=host)
            conn.request("GET", p.path, headers={"User-Agent": AGENT, "Accept-Encoding": "identity",
                                                "Accept": "text/html, application/json, application/xml, text/xml, */*;q=0.1",
                                                "Connection": "close"})
            response = conn.getresponse()
            mime = response.getheader("Content-Type", "").split(";")[0].strip().lower()
            location = response.getheader("Location")
            if response.status != 200:
                return response.status, mime, b"", location
            if response.getheader("Content-Encoding", "identity").lower() != "identity":
                raise ValueError("unsupported content encoding")
            if not (mime in ("text/html", "application/xhtml+xml", "application/json", "text/json",
                             "text/plain", "application/xml", "text/xml", "application/rss+xml", "application/atom+xml")
                    or mime.endswith(("+json", "+xml"))):
                return 200, mime, b"", None
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError("response exceeds byte budget")
            return 200, mime, body, None
        finally:
            conn.close()
            raw.close()

    def __call__(self, url):
        host = up.urlsplit(url).hostname
        if host not in self.robots:
            status, _, body, _ = self._get("https://" + host + "/robots.txt")
            if status in (404, 410):
                body = b"User-agent: *\nDisallow:\n"
            elif status != 200:
                raise PermissionError("robots policy unavailable")
            policy = urllib.robotparser.RobotFileParser()
            policy.parse(body.decode("utf-8", errors="replace").splitlines())
            self.robots[host] = policy
        policy = self.robots[host]
        if not policy.can_fetch(AGENT, url):
            raise PermissionError("robots policy disallows source")
        delay = policy.crawl_delay(AGENT) or 1
        rate = policy.request_rate(AGENT)
        if rate and rate.requests:
            delay = max(delay, rate.seconds / rate.requests)
        if delay > 10:
            raise PermissionError("crawl delay exceeds run budget")
        return self._get(url, delay)


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.anchor = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.anchor = [attrs["href"], attrs.get("title") or ""]
        elif tag == "link" and attrs.get("href"):
            rel = (attrs.get("rel") or "").lower().split()
            if "alternate" in rel and any(x in (attrs.get("type") or "") for x in ("rss", "atom", "json")):
                self.links.append((attrs["href"], "advertised feed", 3))

    def handle_data(self, data):
        if self.anchor and len(self.anchor[1]) < 200:
            self.anchor[1] += " " + data[:200]

    def handle_endtag(self, tag):
        if tag == "a" and self.anchor:
            self.links.append((self.anchor[0], self.anchor[1][:200], 0))
            self.anchor = None


def parse_document(mime, body):
    """Return format and explicit links. OpenAPI is detected, not invoked."""
    if mime in ("text/html", "application/xhtml+xml"):
        parser = Links()
        parser.feed(body.decode("utf-8", errors="replace"))
        return "html", parser.links
    if mime in ("application/json", "text/json") or mime.endswith("+json"):
        obj = json.loads(body)
        if isinstance(obj, dict) and ("openapi" in obj or "swagger" in obj):
            return "openapi", []
        links = []
        stack = [(obj, 0)]
        while stack and len(links) < 300:
            item, depth = stack.pop()
            if depth > 20:
                continue
            if isinstance(item, dict):
                stack.extend((v, depth+1) for v in reversed(list(item.values())))
            elif isinstance(item, list):
                stack.extend((v, depth+1) for v in reversed(item))
            elif isinstance(item, str) and item.startswith("https://"):
                links.append((item, "structured metadata link", 2))
        return "json", links
    if mime in ("application/xml", "text/xml", "application/rss+xml", "application/atom+xml") or mime.endswith("+xml"):
        if b"\x00" in body or re.search(br"<!DOCTYPE|<!ENTITY", body, re.I):
            raise ValueError("XML entities or unsupported encoding")
        root = ET.fromstring(body)
        kind = root.tag.rsplit("}", 1)[-1].lower()
        if kind not in ("rss", "feed", "rdf"):
            return "xml_requires_review", []
        links = []
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1].lower() == "link":
                href = element.get("href") or (element.text or "").strip()
                if href:
                    links.append((href, "feed link", 2))
        return "atom" if kind == "feed" else "rss", links
    return "unsupported", []


def ranked_links(links, base, platform_key):
    candidates = {}
    base_host = up.urlsplit(base).hostname
    for raw, label, weight in links:
        url = public_url(raw, base)
        if not url or url == base:
            continue
        p = up.urlsplit(url)
        if any(p.hostname == h or p.hostname.endswith("." + h) for h in SOCIAL):
            continue
        if platform_key(url):
            score = 5
        else:
            if SKIP.search(p.path):
                continue
            score = weight + 2 * bool(SIGNAL.search(p.path + " " + label))
            if p.hostname != base_host and p.path == "/":
                score += 1
            if not score:
                continue
        candidates[url] = max(score, candidates.get(url, 0))
    return sorted(candidates, key=lambda x: (-candidates[x], x))[:MAX_LINKS]


def metadata_links(text, source_entity, platform_key):
    """Discover additional web entry points from platform metadata."""
    return [url for url in ranked_links([(m.group().rstrip(".,;"), "metadata reference", 1)
             for m in URL_PATTERN.finditer(text)], source_entity, platform_key) if not platform_key(url)]


def discover_web(seeds, *, previous=None, referrals=(), platform_key, fetch=None, now=None, max_pages=8):
    instant = now or dt.datetime.now(dt.timezone.utc)
    stamp = instant.isoformat()
    state = copy.deepcopy(previous or {})
    if state and state.get("schema") != 1:
        raise ValueError("unsupported web state schema")
    sources = state.get("sources", {})
    edges = {(x["source"], x["target"]): x for x in state.get("references", [])}
    prior_sources, prior_edges = set(sources), set(edges)
    pending = list(dict.fromkeys(state.get("pending", [])))
    queued = set(pending)
    platform_refs, errors, hosts, dropped = {}, [], {}, 0
    fetcher = fetch or PublicFetcher()
    core = {public_url(s) for s in seeds}
    if None in core:
        raise ValueError("invalid core seed")

    def queue(url, evidence=None):
        nonlocal dropped
        if not url:
            return
        if platform_key(url):
            if evidence:
                platform_refs[url] = evidence
            return
        if url not in sources:
            if len(sources) >= MAX_SOURCES:
                dropped += 1
                return
            sources[url] = {"url": url, "first_seen": stamp, "status": "pending",
                            "format": "unknown", "affiliation": "unverified"}
        item = sources[url]
        if evidence:
            pair = (evidence["source_entity"], url)
            if pair not in edges and len(edges) >= 5 * MAX_SOURCES:
                dropped += 1
            else:
                first = edges.get(pair, {}).get("first_seen", stamp)
                edges[pair] = {"source": pair[0], "target": url, "first_seen": first,
                               "last_seen": stamp, "relationship": "explicit_reference", "evidence": evidence}
        if item["status"] in ("pending", "retry") and url not in queued:
            queued.add(url)
            pending.append(url)

    for seed in sorted(core):
        queue(seed)
        if sources[seed]["status"] == "read":
            last = dt.datetime.fromisoformat(sources[seed]["last_checked"])
            if instant - last >= dt.timedelta(days=7):
                sources[seed]["status"] = "pending"
                queue(seed)
    for url, proof in referrals:
        queue(url, proof)

    deferred = []
    checked = 0
    # New links discovered within a run can become the next frontier.
    while pending and checked < max_pages:
        url = pending.pop(0)
        queued.discard(url)
        item = sources[url]
        host = up.urlsplit(url).hostname
        if hosts.get(host, 0) >= 2:
            deferred.append(url)
            continue
        hosts[host] = hosts.get(host, 0) + 1
        checked += 1
        item["last_checked"] = stamp
        try:
            status, mime, body, location = fetcher(url)
            if status in (301, 302, 303, 307, 308):
                target = public_url(location, url)
                item.update(status="read", format="redirect")
                links = [(target, "HTTP redirect", 3)] if target else []
                kind = "redirect"
            elif status in (401, 403, 404, 410):
                item.update(status="unavailable", http_status=status)
                continue
            elif status != 200:
                raise OSError("HTTP " + str(status))
            else:
                kind, links = parse_document(mime, body)
                item.update(status="read", format=kind, content_type=mime,
                            body_sha256=hashlib.sha256(body).hexdigest() if body else None)
                if kind in ("openapi", "unsupported", "xml_requires_review"):
                    item["status"] = "adapter_review"
            item.pop("error", None)
            for target in ranked_links(links, url, platform_key):
                proof = {"source_url": url, "source_entity": url, "retrieved_at": stamp,
                         "type": "public_" + kind + "_reference", "excerpt": target,
                         "body_sha256": item.get("body_sha256")}
                queue(target, proof)
        except PermissionError as exc:
            item.update(status="policy_blocked", error=str(exc))
            errors.append({"url": url, "error": str(exc)})
        except (OSError, ValueError, RecursionError, ET.ParseError, http.client.HTTPException) as exc:
            item.update(status="retry", error=type(exc).__name__)
            errors.append({"url": url, "error": type(exc).__name__})
            deferred.append(url)
    pending = list(dict.fromkeys(deferred + pending))
    return {"schema": 1, "core_seeds": sorted(core), "sources": sources,
            "references": sorted(edges.values(), key=lambda x: (x["source"], x["target"])),
            "pending": pending, "platform_refs": platform_refs, "errors": errors,
            "new_sources": len(set(sources) - prior_sources), "new_references": len(set(edges) - prior_edges),
            "checked": checked, "dropped_by_budget": dropped, "complete": not errors and not pending and not dropped,
            "adapter_proposals": [{"url": x["url"], "format": x["format"],
                 "action": "Review schema and read-only adapter requirements; no code generated or executed"}
                 for x in sources.values() if x["status"] == "adapter_review"]}
