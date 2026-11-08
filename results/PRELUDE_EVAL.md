# Prelude checkpoint evaluation – bounded source inspection

Collected: 2026-11-08T09:59:50.586262+00:00 UTC.

Dataset: [openeurollm/prelude-base-eval-scores](https://huggingface.co/datasets/openeurollm/prelude-base-eval-scores). Research question: [oellm-eval #163](https://github.com/OpenEuroLLM/oellm-eval/issues/163).
Filter: prelude_anneal2t / coqa_gen / f1; source method: pinned_source_parquet.

Scope: one model + task + metric; not a cross-benchmark comparison or independent evaluation rerun.

Dataset revision: cf5f9d05ee6e2485273e7ebea7320645c7f6d778; modified: 2026-11-06T10:04:28.000Z.
Filtered rows: **107**; valid scored rows: **0**.
Result: **quality_blocked**.
Scanned all matching rows within cap: **true**.

## Data quality

- Duplicate checkpoint steps: **0**
- Invalid/missing scores: **107**
- Task configurations: **0** distinct digest(s)
- Few-shot settings: **0** distinct value(s)
- Evaluation suites: **0** distinct value(s)
- Sample-count variants where available: **0**

Comparisons blocked because: invalid_or_missing_scores

Source Parquet files inspected: **5**; reader: pyarrow 26.0.1.
Each file's original SHA256, URL, row count and matching row indices are retained in the JSON evidence.

## Provenance

- [Published dataset](https://huggingface.co/datasets/openeurollm/prelude-base-eval-scores) (revision listed above).
- [Original issue](https://github.com/OpenEuroLLM/oellm-eval/issues/163).
- Exact source-file URLs or filter URLs, checkpoint scores and row indices are recorded in results/prelude_eval.json.
