"""Checkpoint-matched controls for Prelude CoQA generative F1 anomalies."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import urllib.error
from pathlib import Path

from benchmark_probe import (
    DATASET, MODEL, SOURCE_DATASET, SOURCE_ISSUE,
    assess_scores, parquet_scores,
)


# Three distinct metrics are never pooled into one score or used as the
# outcome of one benchmark; only within-task adjacent differences are compared.
GROUPS = (
    ("coqa_gen_f1", "coqa_gen", "f1"),
    ("coqa_mc_acc", "coqa_mc", "acc"),
    ("squad_gen_f1", "squad_gen", "f1"),
)


def compare_controls(raw: dict) -> dict:
    """Require comparable independent series, then align exact checkpoint steps."""
    profiles = {}
    for label, task, metric in GROUPS:
        entries = [entry for entry in raw["rows"]
                   if (entry["row"].get("model"), entry["row"].get("task"),
                       entry["row"].get("metric")) == (MODEL, task, metric)]
        profiles[label] = assess_scores({
            **raw, "model": MODEL, "task": task, "metric": metric, "rows": entries,
        })

    status = "quality_blocked"
    aligned = None
    if all(profile["status"] == "comparable" for profile in profiles.values()):
        by_label = {label: {row["step"]: row["score"] for row in profile["records"]}
                    for label, profile in profiles.items()}
        common = sorted(set.intersection(*(set(scores) for scores in by_label.values())))
        if len(common) >= 2:
            series = {}
            for label, scores in by_label.items():
                changes = [
                    {"from_step": a, "to_step": b, "from_score": scores[a],
                     "to_score": scores[b], "delta": round(scores[b] - scores[a], 9)}
                    for a, b in zip(common, common[1:])
                ]
                largest = max(changes, key=lambda change: abs(change["delta"]))
                series[label] = {
                    "median_absolute_delta": statistics.median(abs(c["delta"]) for c in changes),
                    "largest_absolute_delta": abs(largest["delta"]),
                    "largest_change": largest,
                    "aligned_scores": [{"step": step, "score": scores[step]} for step in common],
                }
            coqa_largest = series["coqa_gen_f1"]["largest_change"]
            from_step, to_step = coqa_largest["from_step"], coqa_largest["to_step"]
            controls_at_coqa_peak = {
                label: {
                    "from_score": scores[from_step], "to_score": scores[to_step],
                    "delta": round(scores[to_step] - scores[from_step], 9),
                }
                for label, scores in by_label.items()
            }
            aligned = {
                "common_steps": common, "common_checkpoints": len(common),
                "matched_adjacent_pairs": len(common) - 1,
                "series": series, "coqa_peak_pair": [from_step, to_step],
                "controls_at_coqa_peak": controls_at_coqa_peak,
            }
            status = "comparable"
        else:
            status = "insufficient_overlap"
    return {"status": status, "profiles": profiles, "aligned": aligned}


def report(data: dict) -> str:
    lines = [
        "# Prelude checkpoint-matched benchmark controls", "",
        f"Collected: {data['timestamp_utc']} UTC.", "",
        f"Source: [{DATASET}]({SOURCE_DATASET}) and [research issue #163]({SOURCE_ISSUE}).",
        "All data are published evaluation aggregates; no evaluation was rerun.", "",
    ]
    if data["status"] == "source_error":
        return "\n".join(lines + [
            "## Source unavailable", "", f"Error: {data.get('error')}", "",
            "No scientific comparison was made.",
        ]) + "\n"

    source = data["source"]
    result = data["evaluation"]
    lines.extend([
        f"Dataset revision: {source['revision_sha']} (modified {source.get('last_modified')}).",
        f"Original source files inspected: {len(source['source_files'])}; "
        "their SHA256 and provenance URLs are in the JSON evidence.", "",
        "## Per-task data quality", "",
        "| Task / metric | Rows | Valid | Config variants | Sample-count variants | Verdict |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ])
    for label, _, _ in GROUPS:
        profile = result["profiles"][label]
        lines.append(
            f"| {label} | {profile['source_rows']} | {profile['valid_rows']} | "
            f"{profile['task_config_variants']} | {profile['sample_count_variants']} | "
            f"{profile['status']} |"
        )
    lines.extend(["", f"Overall: **{result['status']}**.", ""])
    if result["status"] != "comparable":
        for label, _, _ in GROUPS:
            p = result["profiles"][label]
            if p["status"] != "comparable":
                lines.append(f"- {label}: {p['status']} ({', '.join(p['problems']) or 'not enough rows'}).")
        lines.extend(["", "A benchmark contrast must not be inferred from non-comparable runs.", ""])
        return "\n".join(lines)

    aligned = result["aligned"]
    lines.extend([
        "## Changes on the same checkpoints", "",
        f"Common checkpoint steps: **{aligned['common_checkpoints']}**; "
        f"successive matched pairs: **{aligned['matched_adjacent_pairs']}**.", "",
        "| Task / metric | Median absolute change | Largest absolute change |",
        "| --- | ---: | ---: |",
    ])
    for label, _, _ in GROUPS:
        series = aligned["series"][label]
        lines.append(
            f"| {label} | {series['median_absolute_delta']:.4f} | "
            f"{series['largest_absolute_delta']:.4f} |"
        )
    a, b = aligned["coqa_peak_pair"]
    lines.extend([
        "", f"## Checkpoint pair with strongest matched CoQA-F1 change: {a:,} to {b:,}", "",
        "| Task / metric | Earlier | Later | Difference |",
        "| --- | ---: | ---: | ---: |",
    ])
    for label, _, _ in GROUPS:
        pair = aligned["controls_at_coqa_peak"][label]
        lines.append(
            f"| {label} | {pair['from_score']:.4f} | {pair['to_score']:.4f} "
            f"| {pair['delta']:+.4f} |"
        )
    lines.extend([
        "", "## Interpretation and limits", "",
        "These are checkpoint-matched, within-task changes in published aggregate "
        "scores. F1 and accuracy are different metrics; their raw levels should not "
        "be compared, and even their changes are descriptive, not statistical proof.",
        "Similar control stability would narrow the investigation toward "
        "CoQA generative evaluation or checkpoint-specific generation behavior, "
        "not establish a root cause. Per-example predictions and repeated runs "
        "would be needed to diagnose that cause.", "",
        "Exact source rows, aligned step identities, scores and computed changes "
        "are stored in results/prelude_controls.json.", "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results")
    args = parser.parse_args(argv)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    result = {"timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        raw = parquet_scores(
            groups=tuple((MODEL, task, metric) for _, task, metric in GROUPS),
        )
        assessment = compare_controls(raw)
        result.update({
            "status": assessment["status"],
            "source": {k: v for k, v in raw.items() if k != "rows"},
            "evaluation": assessment,
        })
    except (ValueError, KeyError, ImportError, urllib.error.URLError, TimeoutError) as exc:
        result.update({"status": "source_error",
                       "error": f"{type(exc).__name__}: {exc}"})
    (output / "prelude_controls.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "PRELUDE_CONTROLS.md").write_text(report(result), encoding="utf-8")
    print(f"Prelude controls: {result['status']}")
    # Source-side failure is recorded as unavailability and does not invalidate
    # the separately audited research graph or the original CoQA probe.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
