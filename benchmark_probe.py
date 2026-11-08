"""Bounded, source-attributed Prelude checkpoint score comparison (stdlib only)."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import math
import statistics
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

from research_graph import UA, fetch_json


DATASET = "openeurollm/prelude-base-eval-scores"
CONFIG, SPLIT = "default", "train"
MODEL, TASK, METRIC = "prelude_anneal2t", "coqa_gen", "f1"
PAGE_SIZE, MAX_PAGES = 100, 5
SOURCE_ISSUE = "https://github.com/OpenEuroLLM/oellm-eval/issues/163"
SOURCE_DATASET = f"https://huggingface.co/datasets/{DATASET}"
REQUIRED = {"model", "step", "task", "metric", "score", "task_config"}
MAX_PARQUET_FILES, MAX_PARQUET_BYTES = 16, 32 * 1024 * 1024


def json_url(base: str, **query: str | int) -> str:
    return base + "?" + urllib.parse.urlencode(query)


def step_number(raw: object) -> int | None:
    """Handle simple numeric or iter_-prefixed checkpoints, not arbitrary revision names."""
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        if math.isfinite(raw) and raw >= 0 and float(raw).is_integer():
            return int(raw)
        return None
    value = str(raw or "").strip()
    if value.startswith("iter_"):
        value = value[5:]
    if value.endswith(".0") and value[:-2].replace(",", "").isdigit():
        value = value[:-2]
    if value.isdigit() or (value and all(part.isdigit() for part in value.split(","))):
        return int(value.replace(",", ""))
    return None


def stable_digest(value: object) -> str:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            pass
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def filtered_scores(*, fetch=fetch_json, pages: int = MAX_PAGES) -> dict:
    """Read only a single comparable group through HF's documented filter API."""
    api = f"https://huggingface.co/api/datasets/{DATASET}"
    metadata_before = fetch(api)
    revision = metadata_before.get("sha")
    if not revision:
        raise ValueError("Dataset API did not provide a commit SHA")
    splits_url = json_url("https://datasets-server.huggingface.co/splits", dataset=DATASET)
    available = fetch(splits_url).get("splits") or []
    if not any(s.get("config") == CONFIG and s.get("split") == SPLIT for s in available):
        raise ValueError("Expected default/train split is not available")
    where = f'"model"={chr(39)}{MODEL}{chr(39)} AND "task"={chr(39)}{TASK}{chr(39)} AND "metric"={chr(39)}{METRIC}{chr(39)}'
    extracted, queries, features = [], [], set()
    full_last_page = False
    for page in range(pages):
        url = json_url("https://datasets-server.huggingface.co/filter",
                       dataset=DATASET, config=CONFIG, split=SPLIT, where=where,
                       offset=page * PAGE_SIZE, length=PAGE_SIZE)
        response = fetch(url)
        queries.append(url)
        if not isinstance(response.get("rows"), list):
            raise ValueError("HF filter did not return a rows list")
        features.update(f.get("name") for f in response.get("features") or [])
        rows = response["rows"]
        extracted.extend(rows)
        full_last_page = len(rows) == PAGE_SIZE
        if not full_last_page:
            break
    metadata_after = fetch(api)
    if metadata_after.get("sha") != revision:
        raise ValueError("Dataset revision changed during pagination")
    missing_columns = sorted(REQUIRED - features)
    if missing_columns:
        raise ValueError(f"Missing source columns: {', '.join(missing_columns)}")
    return {
        "dataset": DATASET, "revision_sha": revision,
        "last_modified": metadata_after.get("lastModified"), "config": CONFIG,
        "split": SPLIT, "model": MODEL, "task": TASK, "metric": METRIC,
        "source_issue": SOURCE_ISSUE, "source_dataset": SOURCE_DATASET,
        "filter_urls": queries, "rows": extracted, "scan_truncated": full_last_page,
        "feature_names": sorted(features),
        "source_method": "filtered_viewer_api",
    }


def parquet_scores(*, fetch=fetch_json, download=None,
                   groups: tuple[tuple[str, str, str], ...] | None = None) -> dict:
    """Inspect source Parquet files at an unchanged dataset commit.

    Files are small in this dataset; reading Parquet needs pyarrow installed
    only in the GitHub Actions job. Dataset-viewer /filter is not a dependency.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    def default_download(url):
        request = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read(MAX_PARQUET_BYTES + 1)

    download = download or default_download
    selected_groups = groups or ((MODEL, TASK, METRIC),)
    if not selected_groups or len(set(selected_groups)) != len(selected_groups):
        raise ValueError("Select at least one unique model/task/metric group")
    selected_set = set(selected_groups)
    api = f"https://huggingface.co/api/datasets/{DATASET}"
    before = fetch(api)
    sha = before.get("sha")
    if not sha:
        raise ValueError("Dataset API did not provide a commit SHA")
    tree_url = f"{api}/tree/{sha}?recursive=true"
    tree = fetch(tree_url)
    if not isinstance(tree, list):
        raise ValueError("Pinned dataset tree is not a list")
    parquet_paths = sorted(item["path"] for item in tree
                           if item.get("type") == "file" and
                           item.get("path", "").lower().endswith(".parquet"))
    if not 1 <= len(parquet_paths) <= MAX_PARQUET_FILES:
        raise ValueError(f"Unexpected Parquet file count: {len(parquet_paths)}")

    required_selection = {"model", "step", "task", "metric", "score", "task_config"}
    possible_selection = required_selection | {
        "num_fewshot", "eval_suite", "n_samples", "revision", "is_checkpoint",
    }
    rows, file_evidence, all_features = [], [], set()
    global_offset = 0
    for path in parquet_paths:
        url = f"https://huggingface.co/datasets/{DATASET}/resolve/{sha}/{urllib.parse.quote(path)}"
        blob = download(url)
        if len(blob) > MAX_PARQUET_BYTES:
            raise ValueError(f"Parquet file exceeds bounded size limit: {path}")
        reader = pq.ParquetFile(io.BytesIO(blob))
        cols = set(reader.schema_arrow.names)
        all_features.update(cols)
        total_rows = reader.metadata.num_rows
        file_details = {
            "path": path, "url": url, "rows": total_rows, "bytes": len(blob),
            "sha256": hashlib.sha256(blob).hexdigest(), "matched_rows": 0,
            "missing_required_columns": sorted(required_selection - cols),
            "step_type": str(reader.schema_arrow.field("step").type) if "step" in cols else None,
            "score_type": str(reader.schema_arrow.field("score").type) if "score" in cols else None,
        }
        file_evidence.append(file_details)
        if not required_selection.issubset(cols):
            global_offset += total_rows
            continue
        file_row_offset = 0
        for group in range(reader.num_row_groups):
            rg_rows = reader.metadata.row_group(group).num_rows
            selected = reader.read_row_group(group, columns=["model", "task", "metric"]).to_pydict()
            indices = [i for i, (model, task, metric) in enumerate(
                zip(selected["model"], selected["task"], selected["metric"]))
                if (model, task, metric) in selected_set]
            if indices:
                full = reader.read_row_group(
                    group, columns=sorted(cols & possible_selection)).to_pylist()
                for index in indices:
                    rows.append({
                        "row_idx": global_offset + file_row_offset + index,
                        "source_file": path,
                        "source_file_row_idx": file_row_offset + index,
                        "row": full[index],
                    })
                file_details["matched_rows"] += len(indices)
            file_row_offset += rg_rows
        global_offset += total_rows
    after = fetch(api)
    if after.get("sha") != sha:
        raise ValueError("Dataset revision changed during Parquet inspection")
    if not required_selection.issubset(all_features):
        raise ValueError("Parquet files lack required columns")
    return {
        "dataset": DATASET, "revision_sha": sha, "last_modified": after.get("lastModified"),
        "config": "original_files", "split": "all", "model": MODEL, "task": TASK, "metric": METRIC,
        "source_issue": SOURCE_ISSUE, "source_dataset": SOURCE_DATASET,
        "filter_urls": [], "source_files": file_evidence, "source_method": "pinned_source_parquet",
        "selected_groups": [list(group) for group in selected_groups],
        "rows": rows, "scan_truncated": False, "feature_names": sorted(all_features),
        "parquet_reader": f"pyarrow {pa.__version__}",
    }


def assess_scores(raw: dict) -> dict:
    """Block changes when the requested checkpoint series is not comparable."""
    records, invalid, invalid_samples = [], [], []
    for entry in raw["rows"]:
        data = entry.get("row") or {}
        step = step_number(data.get("step"))
        score = data.get("score")
        if (step is None or isinstance(score, bool) or
                not isinstance(score, (int, float)) or not math.isfinite(score) or
                score < 0 or score > 1):
            invalid.append(entry.get("row_idx"))
            if len(invalid_samples) < 8:
                invalid_samples.append({
                    "row_idx": entry.get("row_idx"), "source_file": entry.get("source_file"),
                    "raw_step": repr(data.get("step"))[:120],
                    "step_type": type(data.get("step")).__name__,
                    "raw_score": repr(score)[:120],
                    "score_type": type(score).__name__,
                })
            continue
        records.append({
            "step": step, "score": float(score), "row_idx": entry.get("row_idx"),
            "source_file": entry.get("source_file"),
            "source_file_row_idx": entry.get("source_file_row_idx"),
            "model": data.get("model"), "task": data.get("task"), "metric": data.get("metric"),
            "num_fewshot": data.get("num_fewshot"), "eval_suite": data.get("eval_suite"),
            "task_config_hash": stable_digest(data.get("task_config")),
            "n_samples": data.get("n_samples"),
        })
    records.sort(key=lambda row: row["step"])
    duplicate_steps = sorted(step for step, count in Counter(r["step"] for r in records).items() if count > 1)
    task_configs = {r["task_config_hash"] for r in records}
    fewshot = {r["num_fewshot"] for r in records}
    eval_suites = {r["eval_suite"] for r in records}
    sample_counts = {r["n_samples"] for r in records if r["n_samples"] is not None}
    unexpected_group = sum(r["model"] != raw["model"] or r["task"] != raw["task"] or
                           r["metric"] != raw["metric"] for r in records)
    problems = []
    if raw["scan_truncated"]:
        problems.append("source_filter_limit_reached")
    if invalid:
        problems.append("invalid_or_missing_scores")
    if duplicate_steps:
        problems.append("duplicate_checkpoint_steps")
    if len(task_configs) > 1:
        problems.append("inconsistent_task_config")
    if len(fewshot) > 1:
        problems.append("inconsistent_fewshot")
    if len(eval_suites) > 1:
        problems.append("inconsistent_eval_suite")
    if len(sample_counts) > 1:
        problems.append("inconsistent_sample_count")
    if unexpected_group:
        problems.append("unexpected_model_task_metric")
    comparisons = None
    if len(records) >= 2 and not problems:
        adjacent = [
            {"from_step": a["step"], "to_step": b["step"],
             "from_score": a["score"], "to_score": b["score"],
             "delta": round(b["score"] - a["score"], 9)}
            for a, b in zip(records, records[1:])
        ]
        peak = max(adjacent, key=lambda row: abs(row["delta"]))
        comparisons = {
            "adjacent_pairs": len(adjacent),
            "median_absolute_delta": statistics.median(abs(row["delta"]) for row in adjacent),
            "largest_absolute_delta": abs(peak["delta"]), "largest_change": peak,
            "lowest_score": min(row["score"] for row in records),
            "highest_score": max(row["score"] for row in records),
        }
    return {
        "status": "comparable" if comparisons else ("insufficient_rows" if not problems else "quality_blocked"),
        "source_rows": len(raw["rows"]), "valid_rows": len(records),
        "invalid_row_indices": invalid, "invalid_samples": invalid_samples,
        "duplicate_steps": duplicate_steps,
        "task_config_variants": len(task_configs), "fewshot_variants": len(fewshot),
        "eval_suite_variants": len(eval_suites), "sample_count_variants": len(sample_counts),
        "problems": problems, "records": records, "comparisons": comparisons,
    }


def markdown(data: dict) -> str:
    source = data.get("source") or {}
    profile = data.get("profile") or {}
    lines = [
        "# Prelude checkpoint evaluation – bounded source inspection", "",
        f"Collected: {data['timestamp_utc']} UTC.", "",
        f"Dataset: [{DATASET}]({SOURCE_DATASET}). Research question: [oellm-eval #163]({SOURCE_ISSUE}).",
        f"Filter: {MODEL} / {TASK} / {METRIC}; source method: {source.get('source_method', 'unavailable')}.", "",
        "Scope: one model + task + metric; not a cross-benchmark comparison or independent evaluation rerun.", "",
    ]
    if data["status"] == "source_error":
        lines.extend(["## Result", "", "**Source unavailable; no scores were analyzed.**",
                      f"Error: {data.get('error', 'unknown')}", "",
                      "An unavailable source is not evidence the experiment failed."])
        return "\n".join(lines) + "\n"
    lines.extend([
        f"Dataset revision: {source['revision_sha']}; modified: {source.get('last_modified')}.",
        f"Filtered rows: **{profile['source_rows']}**; valid scored rows: **{profile['valid_rows']}**.",
        f"Result: **{profile['status']}**.",
        f"Scanned all matching rows within cap: **{str(not source['scan_truncated']).lower()}**.", "",
        "## Data quality", "",
        f"- Duplicate checkpoint steps: **{len(profile['duplicate_steps'])}**",
        f"- Invalid/missing scores: **{len(profile['invalid_row_indices'])}**",
        f"- Task configurations: **{profile['task_config_variants']}** distinct digest(s)",
        f"- Few-shot settings: **{profile['fewshot_variants']}** distinct value(s)",
        f"- Evaluation suites: **{profile['eval_suite_variants']}** distinct value(s)",
        f"- Sample-count variants where available: **{profile['sample_count_variants']}**", "",
    ])
    if profile["problems"]:
        lines.extend(["Comparisons blocked because: " + ", ".join(profile["problems"]), ""])
    if source.get("source_files"):
        lines.extend([
            f"Source Parquet files inspected: **{len(source['source_files'])}**; "
            f"reader: {source.get('parquet_reader')}.",
            "Each file's original SHA256, URL, row count and matching row indices "
            "are retained in the JSON evidence.", "",
        ])
    if profile["comparisons"]:
        c = profile["comparisons"]
        peak = c["largest_change"]
        lines.extend([
            "## Adjacent checkpoint changes", "",
            f"- Comparable adjacent pairs: **{c['adjacent_pairs']}**",
            f"- Median absolute F1 change: **{c['median_absolute_delta']:.4f}**",
            f"- Largest absolute F1 change: **{c['largest_absolute_delta']:.4f}**",
            f"- Largest change: step **{peak['from_step']:,} → {peak['to_step']:,}** "
            f"(**{peak['from_score']:.3f} → {peak['to_score']:.3f}**).", "",
            "Descriptive changes only, not statistical significance or a root-cause diagnosis.", "",
        ])
    lines.extend([
        "## Provenance", "",
        f"- [Published dataset]({SOURCE_DATASET}) (revision listed above).",
        f"- [Original issue]({SOURCE_ISSUE}).",
        "- Exact source-file URLs or filter URLs, checkpoint scores and row indices are recorded in results/prelude_eval.json.", "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results")
    args = parser.parse_args(argv)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    try:
        try:
            raw = filtered_scores()
        except urllib.error.HTTPError as primary_error:
            # HF dataset-viewer occasionally returns HTTP 500. Use the
            # source repository's pinned, small Parquet files instead.
            if primary_error.code < 500:
                raise
            raw = parquet_scores()
            raw["viewer_filter_error"] = (f"HTTP {primary_error.code} at "
                                          f"{primary_error.geturl()}")
        profile = assess_scores(raw)
        result = {"timestamp_utc": timestamp, "status": profile["status"],
                  "source": {k: v for k, v in raw.items() if k != "rows"}, "profile": profile}
    except (ValueError, KeyError, urllib.error.URLError, TimeoutError) as exc:
        failed_url = exc.geturl() if isinstance(exc, urllib.error.HTTPError) else None
        result = {"timestamp_utc": timestamp, "status": "source_error",
                  "error": f"{type(exc).__name__}: {exc}",
                  "failed_url": failed_url, "source": None, "profile": None}
    (output / "prelude_eval.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "PRELUDE_EVAL.md").write_text(markdown(result), encoding="utf-8")
    print(f"Prelude eval probe: {result['status']}")
    # Optional companion data source: errors are explicit and do not overwrite
    # independently collected research graph results.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
