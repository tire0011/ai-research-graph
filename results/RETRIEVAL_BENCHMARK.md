# Cross-platform research retrieval: controlled comparison

Snapshot: `2026-11-08T14:11:15.900825+00:00` UTC, **920 nodes**, **366 edges**.
Scored 6 curated target artifacts in a top-10 shortlist.

| Method | Found curated artifacts |
| --- | ---: |
| Evidence graph | 6/6 |
| Plain-text source-record search | 6/6 |

Both methods use the **same captured source records** and receive the question and the source type. The graph also uses its previously computed, source-attributed edges. The plain-text baseline searches node titles/descriptions without traversing edges.

**Important:** This is a small, intentionally curated *retrieval* check, not a held-out scientific benchmark, live GitHub/HF search, end-to-end human timing, proof of model training, or evidence that an MCP service is beneficial.

Graph index construction: 0.2665 ms. Each query timing is the median of 31 in-memory runs (no network).

| Question | Graph targets | Text targets | Graph ms | Text ms |
| --- | ---: | ---: | ---: | ---: |
| prelude_eval_dataset | 1/1 | 1/1 | 0.0078 | 1.9536 |
| tokenizer_v2 | 2/2 | 2/2 | 0.0154 | 0.3235 |
| openthoughts_shared_paper | 1/1 | 1/1 | 0.0082 | 1.9438 |
| finemath_shared_paper | 1/1 | 1/1 | 0.0117 | 1.8832 |
| olmo3_shared_paper | 1/1 | 1/1 | 0.0153 | 0.3933 |

- **hplt_unverified**: abstained (inaccessible); no positive retrieval score.

## Interpretation

A found artifact is not proof of scientific use. Citation joins indicate shared references; declared metadata records remain declarations. Compare longer, genuinely unseen research questions and include live source-search latency and researcher judgments before proposing a production MCP.
