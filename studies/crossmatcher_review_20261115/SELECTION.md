# Cross-project candidate relevance — frozen review selection

**Registered:** 2026-11-15 (evening CET) before reading the six candidate source threads in this pass.
**Input:** [Original matcher snapshot from Nov 10](../../results/collaboration_matches.json), with **665 source items** and 25 technical suggestions. This matcher was tuned on the observed cohort: the present review is **NOT** an independent untuned holdout or an unbiased estimate of general precision.

## Goal

Find whether the *technical-vocabulary candidate ranking* gives a researcher more **actionably relevant** cross-project references than the same-input **unweighted full-text top-1** baseline. This complements the existing task-reference retrieval benchmark and directly addresses the graph mission: avoid duplicating research or suggest grounded reuse.

## Locked selection

1. Consider unique source anchors in the first 25 matcher suggestions with `same_as_fulltext_baseline_top1 = false`. Use the first suggestion per anchor in snapshot order.
2. Exclude sources directly reviewed with detailed pair-level conclusions in `results/COLLABORATION_FIRST_REVIEW.md` and already documented as intentional primary case studies. Exclude: `OpenEuroLLM/web-data-processing#6`, `#7`, `#1`, `#2` and `OpenEuroLLM/warc2text#1`. These cases have pre-existing ground knowledge.
3. Remaining source anchors ranked by unsigned 32-bit FNV-1a hash of `2026-11-15-crossmatcher-holdout-v1|<lowercase source id>`, ascending. Select first three. No replacement if results are negative or source material inaccessible.

| Trial | Source anchor | Technical matcher top 1 | Same-snapshot full-text top 1 |
| --- | --- | --- | --- |
| R1 | [OpenEuroLLM Taskboard #119](https://github.com/OpenEuroLLM/Taskboard/issues/119) | [LAION CLIP_benchmark PR #19](https://github.com/LAION-AI/CLIP_benchmark/pull/19) | [LAION CLIP_benchmark PR #114](https://github.com/LAION-AI/CLIP_benchmark/pull/114) |
| R2 | [OpenEuroLLM web-data-processing #3](https://github.com/OpenEuroLLM/web-data-processing/issues/3) | [HPLT warc2text-runner #22](https://github.com/hplt-project/warc2text-runner/issues/22) | [HPLT HPLT-textpipes #18](https://github.com/hplt-project/HPLT-textpipes/issues/18) |
| R3 | [OpenEuroLLM web-data-processing #8](https://github.com/OpenEuroLLM/web-data-processing/issues/8) | [HPLT warc2text-runner #22](https://github.com/hplt-project/warc2text-runner/issues/22) | [HPLT HPLT-textpipes #18](https://github.com/hplt-project/HPLT-textpipes/issues/18) |

## Predefined source-based review rubric (score each pair independently)

- **0 — Irrelevant:** No directly compatible task, input/output, mechanism, source artifact or measured outcome; shared vocabulary is misleading.
- **1 — Adjacent:** Broad technical domain overlap, but different deliverables or unknown usable transfer.
- **2 — Plausible reusable artifact:** A cited public implementation, method or data artifact could answer an explicit part of the source task, but compatibility/receiving need not yet confirmed.
- **3 — Demonstrably actionable:** Source-supported compatible need and existing public reusable solution; a specific low-effort verification could influence an active research decision. This is still **not** proof of actual adoption.

Evaluate exact task intent, input-output structures, version/state, existing public coordination, and potential false-positive costs. Use current original issue/PR descriptions and comments for **both arms**, with the same depth and an explicit abstention option. Preserve all six candidates, including failures.

**Important limitations:** We already know which suggestion came from which ranker, so the reviewer is *not blinded* and is the same assistant. The proposals and technical-vocabulary rules were selected/tuned earlier on an observed cohort; not a valid model-generalization benchmark. Do not claim user time, saved compute, acceptance or novel collaboration. Even a high score is only a provisional independent-source **relevance judgment**, not a measured benefit.

## Decision rule

If technical matcher gives at most the same sum of relevance scores as plain text on these three cases, prefer simpler retrieval and only add precision controls if a **specific repeated error mode** is confirmed. No new automatic outreach or graph services. If better, require an independently blinded subsequent holdout before claiming advantage.
