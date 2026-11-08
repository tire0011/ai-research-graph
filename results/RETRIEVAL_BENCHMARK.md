# Cross-platform research retrieval: controlled comparison

Snapshot: `2026-11-08T11:51:52.642475+00:00` UTC, **920 nodes**, **215 edges**.
Scored 6 curated target artifacts in a top-10 shortlist.

| Method | Found curated artifacts |
| --- | ---: |
| Evidence graph | 6/6 |
| Plain-text source-record search | 6/6 |

Both methods use the **same captured source records** and receive the question and the source type. The graph also uses its previously computed, source-attributed edges. The plain-text baseline searches node titles/descriptions without traversing edges.

**Important:** This is a small, intentionally curated *retrieval* check, not a held-out scientific benchmark, live GitHub/HF search, end-to-end human timing, proof of model training, or evidence that an MCP service is beneficial.

Graph index construction: 0.2189 ms. Each query timing is the median of 31 in-memory runs (no network).

| Question | Graph targets | Text targets | Graph ms | Text ms |
| --- | ---: | ---: | ---: | ---: |
| prelude_eval_dataset | 1/1 | 1/1 | 0.0084 | 1.8847 |
| tokenizer_v2 | 2/2 | 2/2 | 0.0088 | 0.3462 |
| openthoughts_shared_paper | 1/1 | 1/1 | 0.0089 | 1.8510 |
| finemath_shared_paper | 1/1 | 1/1 | 0.0132 | 1.8304 |
| olmo3_shared_paper | 1/1 | 1/1 | 0.0167 | 0.4374 |

- **hplt_unverified**: abstained (inaccessible); no positive retrieval score.

## Interpretation

A found artifact is not proof of scientific use. Citation joins indicate shared references; declared metadata records remain declarations. Compare longer, genuinely unseen research questions and include live source-search latency and researcher judgments before proposing a production MCP.
