"""Audit aligned European IFEval constraints; no scoring, LLM calls or training.

Fetches 4 source files from a pinned public GitHub commit, or reads an offline
copy. Generated summaries contain IDs, checker metadata and prompt SHA256 only.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

UPSTREAM_REPO = "Telefonica-Scientific-Research/european-ifeval"
UPSTREAM_SHA = "a1d07cccc0d1a4c95f3a12282a748566d8e18a60"
LANGUAGES = ("de", "fr", "eu", "ga")
CHECKERS = (
    "punctuation:no_comma",
    "detectable_format:json_format",
    "detectable_format:number_bullet_lists",
    "detectable_content:number_placeholders",
    "length_constraints:number_paragraphs",
)
SOURCE_URL = "https://github.com/" + UPSTREAM_REPO + "/tree/" + UPSTREAM_SHA
MAX_BYTES = 2_000_000


def fetch_pinned_sources(folder: Path) -> None:
    if folder.exists():
        raise FileExistsError("Use a new source directory; never overwrite provenance.")
    folder.mkdir(parents=True)
    base = f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{UPSTREAM_SHA}/data/"
    for name in (*[f"{lang}.jsonl" for lang in LANGUAGES], "source.json"):
        request = Request(base + name, headers={"User-Agent": "research-graph-ifeval-audit/0.1"})
        with urlopen(request, timeout=30) as response:
            content = response.read(MAX_BYTES + 1)
        if not content or len(content) > MAX_BYTES:
            raise ValueError("Unexpected or oversized upstream source file: " + name)
        (folder / name).write_bytes(content)


def load_rows(path: Path) -> dict[int, dict]:
    found = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        key = row.get("key")
        if type(key) is not int or key in found:
            raise ValueError(f"{path.name}:{lineno}: invalid or repeated key")
        names, args = row.get("instruction_id_list"), row.get("kwargs")
        if (
            not isinstance(row.get("prompt"), str) or not row["prompt"].strip()
            or not isinstance(names, list) or not names
            or not all(isinstance(n, str) for n in names)
            or not isinstance(args, list) or len(args) != len(names)
            or not all(isinstance(a, dict) for a in args)
            or type(row.get("requires_answer_in_source_language")) is not bool
        ):
            raise ValueError(f"{path.name}:{lineno}: invalid prompt or checker fields")
        found[key] = row
    if not found:
        raise ValueError("No rows: " + str(path))
    return found


def evaluate(folder: Path, per_checker: int = 4) -> dict:
    if not 1 <= per_checker <= 20:
        raise ValueError("per_checker must be 1-20")
    rows = {lang: load_rows(folder / f"{lang}.jsonl") for lang in LANGUAGES}
    metadata = json.loads((folder / "source.json").read_text(encoding="utf-8"))
    for lang in LANGUAGES:
        item = metadata.get(lang)
        if not isinstance(item, dict) or item.get("quality") not in {
            "native_speaker", "localized_verified", "machine_translated_with_localization"
        } or not isinstance(item.get("missing_samples"), int):
            raise ValueError(f"Missing provenance metadata: {lang}")
    shared = set.intersection(*(set(rows[lang]) for lang in LANGUAGES))
    same_rules = [
        key for key in shared
        if all(rows[lang][key]["instruction_id_list"] == rows["de"][key]["instruction_id_list"]
               for lang in LANGUAGES)
    ]
    strict = [
        key for key in same_rules
        if all(rows[lang][key]["kwargs"] == rows["de"][key]["kwargs"]
               and not rows[lang][key]["requires_answer_in_source_language"]
               for lang in LANGUAGES)
    ]
    buckets = defaultdict(list)
    for key in sorted(strict):
        instructions = rows["de"][key]["instruction_id_list"]
        if len(instructions) == 1 and instructions[0] in CHECKERS:
            buckets[instructions[0]].append(key)
    chosen = []
    for checker in CHECKERS:
        for key in buckets[checker][:per_checker]:
            chosen.append({
                "key": key,
                "single_checker": checker,
                "prompt_sha256": {
                    lang: hashlib.sha256(rows[lang][key]["prompt"].encode("utf-8")).hexdigest()
                    for lang in LANGUAGES
                },
                "semantic_equivalence_verified": False,
                "model_scored": False,
            })
    return {
        "schema": 1,
        "origin": SOURCE_URL,
        "source_commit": UPSTREAM_SHA,
        "languages": list(LANGUAGES),
        "source_counts": {lang: len(rows[lang]) for lang in LANGUAGES},
        "source_provenance": {
            lang: {
                "quality": metadata[lang]["quality"],
                "missing_samples": metadata[lang]["missing_samples"],
                "source": metadata[lang].get("source"),
            }
            for lang in LANGUAGES
        },
        "shared_keys": len(shared),
        "same_instruction_ids": len(same_rules),
        "strict_matching_checker_kwargs_and_no_response_language_constraint": len(strict),
        "selected_count": len(chosen),
        "selected": chosen,
        "validation": "Metadata-aligned candidates only; semantic equivalence and translations require native reviewers.",
        "not_a_measurement_of": [
            "LLM-judge calibration", "instruction-following accuracy",
            "synthetic training data quality", "research acceleration"
        ],
        "safety_note": (
            "IFEval is a test benchmark, not new training data. Do not tune on this "
            "selection or assume benchmark tasks match synthgen's quality rubric."
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--fetch", action="store_true",
                        help="Download only four pinned GitHub files plus provenance to a new directory")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--per-checker", type=int, default=4)
    args = parser.parse_args(argv)
    if args.fetch:
        fetch_pinned_sources(args.source_dir)
    report = evaluate(args.source_dir, args.per_checker)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_counts": report["source_counts"], "shared_keys": report["shared_keys"],
        "same_rules": report["same_instruction_ids"],
        "strict": report["strict_matching_checker_kwargs_and_no_response_language_constraint"],
        "candidates": report["selected_count"],
        "out": str(args.out)
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
