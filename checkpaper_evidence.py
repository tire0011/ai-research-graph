"""Import public CheckPaper audit metadata, not scientific verdicts or executable code."""
import base64
import copy
import datetime as dt
import hashlib
import re
from urllib.parse import quote

API = "https://api.github.com/repos/checkpaper/audits/contents/"
WEB = "https://github.com/checkpaper/audits"
PATH = re.compile(r"20\d{2}/[\w.-]+/", re.ASCII)
ARXIV = re.compile(r"https://arxiv\.org/abs/(\d{4}\.\d{4,5})(v[1-9]\d*)?(?=[)\s#]|$)")
SECTION = re.compile(r"^## (Paper|Findings|Reproduce|Status|Author response)\s*$", re.M)
MAX_BYTES = 512 * 1024

def read_blob(path, fetch):
    row = fetch(API + quote(path, safe="/"))
    if row.get("path") != path or row.get("encoding") != "base64" or row.get("type") != "file":
        raise ValueError("unexpected file metadata")
    if type(row.get("size")) is not int or not 0 <= row["size"] <= MAX_BYTES:
        raise ValueError("file size outside budget")
    raw = base64.b64decode("".join(row["content"].split()), validate=True)
    sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if len(raw) != row["size"] or sha != row["sha"]:
        raise ValueError("Git blob identity mismatch")
    return raw.decode("utf-8"), sha

def index_paths(text):
    return sorted({m.group(1)+"README.md" for m in re.finditer(r"\]\((20\d{2}/[\w.-]+/)\)", text)
                   if PATH.fullmatch(m.group(1))})

def parse_audit(path, text, sha, stamp):
    matches = list(SECTION.finditer(text))
    if len({m.group(1) for m in matches}) != len(matches):
        raise ValueError("ambiguous audit sections")
    sections = {m.group(1): text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)].strip()
                for i,m in enumerate(matches)}
    if not {"Paper","Findings","Reproduce","Status"}.issubset(sections):
        raise ValueError("missing audit sections")
    ids = {(m.group(1),m.group(2)) for m in ARXIV.finditer(sections["Paper"])}
    if len(ids) != 1 or next(iter(ids))[1] is None:
        return {"status":"unsupported_or_unversioned", "path":path, "blob_sha":sha, "retrieved_at":stamp}
    pid, version = next(iter(ids))
    # Store only a short attributed excerpt and links, not copied full audits.
    links = sorted(set(re.findall(r"https://(?:github\.com|huggingface\.co)/[^\s)<>\"]+",sections["Status"]+"\n"+sections.get("Author response",""))))[:12]
    return {"status":"versioned_audit_reference", "path":path,"blob_sha":sha,
            "source_url":WEB+"/blob/main/"+path,
            "immutable_source_url":"https://api.github.com/repos/checkpaper/audits/git/blobs/"+sha,
            "paper_id":pid,"paper_version":pid+version,
            "paper_url":"https://arxiv.org/abs/"+pid+version,
            "status_excerpt":sections["Status"][:240],
            "author_response_section_present":bool(sections.get("Author response")),
            "author_response_links":links, "findings_present":bool(sections["Findings"]),
            "license_notice":"Repository README declares text CC BY 4.0 and code MIT; attributed status excerpt only.",
            "attribution":"CheckPaper Audits", "retrieved_at":stamp,
            "review_only":True,"scientific_validity_verified":False,
            "audit_script_executed":False}

def collect(now, fetch, *, previous=None, max_audits=5):
    if not 0 <= max_audits <= 10:
        raise ValueError("audit budget")
    previous = previous or {}
    records = copy.deepcopy(previous.get("records", {}))
    history = copy.deepcopy(previous.get("last_attempt", {}))
    errors, selected = [], []
    stamp = now.isoformat()
    try:
        index, index_sha = read_blob("README.md",fetch)
        paths = index_paths(index)
        if not paths:
            raise ValueError("no audit entries in index")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return {**previous,"schema":1,"retrieved_at":stamp,"records":records,"last_attempt":history,
                "selected":[],"errors":[{"source":API+"README.md","error":type(exc).__name__}],"coverage":"source_error"}
    for path in sorted(paths,key=lambda p:(history.get(p,""),p))[:max_audits]:
        history[path] = stamp
        selected.append(path)
        try:
            text, sha = read_blob(path,fetch)
            records[path] = parse_audit(path,text,sha,stamp)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            errors.append({"source":API+path,"error":type(exc).__name__})
    return {"schema":1,"retrieved_at":stamp,"index_sha":index_sha,"indexed_paths":len(paths),
            "selected":selected,"records":records,"last_attempt":history,"errors":errors,
            "coverage":"partial" if errors or len(paths)>len(selected) else "bounded_complete",
            "limitations":["Only explicit versioned arXiv identifiers linked; no assumed DOI or version mapping.",
                           "Audit status is a source assertion; no global paper quality score.",
                           "Read-only public metadata; no API review requests, external contact or script execution."]}
