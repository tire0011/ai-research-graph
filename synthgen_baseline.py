"""Bounded read-only EuroMultiSynth-Instruct quality baseline (no LLM calls).

Samples separate language configs via public Hugging Face dataset-viewer API.
Stores counts/hashes, never prompt/response text. Does not prove data quality.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import random
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DATASET = "openeurollm/EuroMultiSynth-Instruct"
HOST = "https://datasets-server.huggingface.co"
HUB = "https://huggingface.co/api/datasets/openeurollm/EuroMultiSynth-Instruct"
DEFAULT_LANGUAGES = ("de", "fr", "eu", "ga")


def get_json(url: str) -> dict:
    with urlopen(Request(url, headers={"User-Agent": "research-graph-baseline/0.1"}), timeout=25) as resp:
        return json.load(resp)


def viewer(path: str, **params) -> str:
    return f"{HOST}/{path}?{urlencode({'dataset': DATASET, **params})}"


def dataset_revision(fetch=get_json) -> str:
    rev = fetch(HUB).get("sha")
    if not isinstance(rev, str) or len(rev) != 40 or any(c not in "0123456789abcdef" for c in rev.lower()):
        raise ValueError("Hugging Face dataset revision unavailable or invalid")
    return rev


def split_sizes(fetch=get_json) -> dict[str, int]:
    obj = fetch(viewer("size")).get("size", {})
    sizes = {}
    for item in obj.get("splits", []):
        if item.get("split") == "train" and isinstance(item.get("num_rows"), int):
            sizes[item["config"]] = item["num_rows"]
    if not sizes:
        raise ValueError("Hugging Face size API did not supply split counts")
    return sizes


def offsets(total: int, pages: int, length: int, seed: int, language: str) -> list[int]:
    if min(total, pages, length) <= 0 or length > 100 or pages * length > total:
        raise ValueError("Invalid sample: need disjoint pages of up to 100 rows")
    # One sampled nonoverlapping block from each of 'pages' disjoint strata.
    rng = random.Random(f"{seed}:{language}")
    chunk = total // pages
    result = []
    for i in range(pages):
        start, end = i * chunk, (i + 1) * chunk if i + 1 < pages else total
        result.append(rng.randint(start, end - length))
    return result


def normalized(row: dict, lang: str) -> tuple[str, str, int, str]:
    if not isinstance(row, dict) or row.get("language") != lang:
        raise ValueError("Missing or mismatched language")
    rid, domain, score, messages = (row.get(k) for k in ("id", "domain", "judge_score", "messages"))
    if not isinstance(rid, str) or not rid or not isinstance(domain, str) or not domain:
        raise ValueError("Missing row ID or domain")
    if type(score) is not int or not 7 <= score <= 10:
        raise ValueError("Unexpected quality score in released dataset")
    if not isinstance(messages, list) or len(messages) != 2:
        raise ValueError("Expected a single user/assistant message pair")
    for msg, role in zip(messages, ("user", "assistant")):
        if not isinstance(msg, dict) or msg.get("role") != role or not isinstance(msg.get("content"), str) or not msg["content"].strip():
            raise ValueError("Invalid message role or empty content")
    return rid, domain, score, hashlib.sha256((messages[0]["content"] + "\0" + messages[1]["content"]).encode()).hexdigest()


def collect(languages=DEFAULT_LANGUAGES, pages=3, length=25, seed=20261112, fetch=get_json) -> dict:
    sizes = split_sizes(fetch)
    before = dataset_revision(fetch)
    data = {}
    seen_ids = set()
    for lang in languages:
        if lang not in sizes:
            raise ValueError(f"Unknown language config: {lang}")
        starts = offsets(sizes[lang], pages, length, seed, lang)
        scores, domains = Counter(), Counter()
        digest = hashlib.sha256()
        for start in starts:
            payload = fetch(viewer("rows", config=lang, split="train", offset=start, length=length))
            rows = payload.get("rows")
            if not isinstance(rows, list) or len(rows) != length:
                raise ValueError(f"Incomplete page for {lang} offset={start}")
            for wrapper in rows:
                rid, domain, score, text_sha = normalized(wrapper.get("row"), lang)
                if rid in seen_ids:
                    raise ValueError(f"Duplicate sampled id {rid}")
                seen_ids.add(rid)
                scores[str(score)] += 1
                domains[domain] += 1
                # Hash only: sampled row index/id and original text checksum; no raw content stored.
                digest.update(f"{wrapper.get('row_idx')}\t{rid}\t{domain}\t{score}\t{text_sha}\n".encode())
        count = pages * length
        data[lang] = {
            "population_rows": sizes[lang], "sample_rows": count, "sample_offsets": starts,
            "scores": dict(sorted(scores.items())), "domains": dict(sorted(domains.items())),
            "score_10_share": round(scores["10"] / count, 4), "sample_sha256": digest.hexdigest()
        }
    after = dataset_revision(fetch)
    if before != after:
        raise ValueError("Dataset revision changed during sampling")
    return {
        "schema": 1, "dataset": DATASET, "hub_revision_before_after": before,
        "viewer_revision_pinned": False, "seed": seed, "pages_per_language": pages,
        "rows_per_page": length, "samples": data,
        "limitations": (
            "Unweighted descriptive pilot of contiguous page clusters, not i.i.d. random rows. "
            "Dataset viewer pages cannot be pinned to Hub SHA; SHA was checked before/after, "
            "which does not prove same-revision serving. Score distribution is conditioned "
            "on prior filtering; no semantic validation, model quality, or acceleration measured."
        ),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--languages", default=",".join(DEFAULT_LANGUAGES))
    p.add_argument("--pages", type=int, default=3)
    p.add_argument("--length", type=int, default=25)
    p.add_argument("--seed", type=int, default=20261112)
    a = p.parse_args(argv)
    languages = tuple(x.strip() for x in a.languages.split(","))
    if not all(languages) or len(set(languages)) != len(languages):
        p.error("Languages must be nonempty and unique")
    result = collect(languages, a.pages, a.length, a.seed)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": DATASET, "languages": list(result["samples"]), "rows": sum(x["sample_rows"] for x in result["samples"].values()), "out": str(a.out)}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
