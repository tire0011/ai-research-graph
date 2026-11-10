# Prelude checkpoint evaluation – bounded source inspection

Collected: 2026-11-10T08:33:06.010446+00:00 UTC.

Dataset: [openeurollm/prelude-base-eval-scores](https://huggingface.co/datasets/openeurollm/prelude-base-eval-scores). Research question: [oellm-eval #163](https://github.com/OpenEuroLLM/oellm-eval/issues/163).
Filter: prelude_anneal2t / coqa_gen / f1; source method: pinned_source_parquet.

Scope: one model + task + metric; not a cross-benchmark comparison or independent evaluation rerun.

Dataset revision: 88f335f943f34bbf1fbba681719b2750f02340f7; modified: 2026-11-09T14:42:16.000Z.
Filtered rows: **107**; valid scored rows: **107**.
Result: **comparable**.
Scanned all matching rows within cap: **true**.

## Data quality

- Duplicate checkpoint steps: **0**
- Invalid/missing scores: **0**
- Task configurations: **1** distinct digest(s)
- Few-shot settings: **1** distinct value(s)
- Evaluation suites: **1** distinct value(s)
- Sample-count variants where available: **1**

Source Parquet files inspected: **5**; reader: pyarrow 26.0.1.
Each file's original SHA256, URL, row count and matching row indices are retained in the JSON evidence.

## Adjacent checkpoint changes

- Comparable adjacent pairs: **106**
- Median absolute F1 change: **0.0705**
- Largest absolute F1 change: **0.4244**
- Largest change: step **1,092,000 → 1,094,400** (**0.320 → 0.745**).

Descriptive changes only, not statistical significance or a root-cause diagnosis.

## Provenance

- [Published dataset](https://huggingface.co/datasets/openeurollm/prelude-base-eval-scores) (revision listed above).
- [Original issue](https://github.com/OpenEuroLLM/oellm-eval/issues/163).
- Exact source-file URLs or filter URLs, checkpoint scores and row indices are recorded in results/prelude_eval.json.
