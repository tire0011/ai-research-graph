# Cross-organization candidate relevance: technical matcher vs full-text search

**Date:** 2026-11-15 · **Source selection frozen before reviewing original issue texts:** [SELECTION.md](SELECTION.md) · **Individual source-linked labels:** [RESULTS.json](RESULTS.json).

## Decision

**Neither method identified a confirmed actionable reuse opportunity in the three preselected source tasks.** The specialized matcher performed **worse on broad topical relevance** than its plain full-text baseline for two tasks and tied once. We should **not** spend more engineering effort on automated collaboration claims or turn all co-mentioned technologies into graph edges.

This is a small after-the-fact review of a matcher **already tuned** on the underlying cohort, with one non-blinded reviewer (the assistant), not an independent scientific evaluation or population precision estimate.

| Source question | Technical matcher top-1 (0–3) | Same-snapshot full text top-1 (0–3) | Decision |
| --- | --- | --- | --- |
| [MoE baseline, #119](https://github.com/OpenEuroLLM/Taskboard/issues/119) | [CLIP tokenizer PR #19](https://github.com/LAION-AI/CLIP_benchmark/pull/19): **0** | [CLIP distributed evaluation PR #114](https://github.com/LAION-AI/CLIP_benchmark/pull/114): **0** | Both irrelevant; abstain |
| [Opt-out handling, #3](https://github.com/OpenEuroLLM/web-data-processing/issues/3) | [WARC de-chunking #22](https://github.com/hplt-project/warc2text-runner/issues/22): **0** | [HPLT data release #18](https://github.com/hplt-project/HPLT-textpipes/issues/18): **1** | Full text at least mentions compatible robots.txt filtering, but neither is a demonstrated transferable solution |
| [WARC audio/video extraction, #8](https://github.com/OpenEuroLLM/web-data-processing/issues/8) | [WARC de-chunking #22](https://github.com/hplt-project/warc2text-runner/issues/22): **0** | [HPLT data release #18](https://github.com/hplt-project/HPLT-textpipes/issues/18): **1** | Full text gives related crawl/storage context; neither produces an audio extraction implementation |

*Rubric defined before review:* 0 irrelevant; 1 adjacent without verified reuse; 2 sourced plausible reuse; 3 demonstrated compatible decision-ready action. This is ordinal single-reviewer scoring; **do not interpret 0 vs 2 total points as a statistical effect**.

## Honest numeric summary

- **3** prespecified source tasks, **6** paired candidate records; reviewer inspected original issues/PRs and public comments for both arms.
- Technical matcher: **0/3** actionable top-1 (`score >= 2`); full text: **0/3** actionable top-1.
- The technical ranking won **0** cases, tied **1**, and lost **2** on the coarse relevance rubric. Total ordinal scores: **0 vs 2**, which does **not** establish general superiority of full-text search.
- Among all **25** archived technical suggestions, **15** rely on exactly one matched term: `tokenizer` (7), `warc2text` (4), `lumio` (2), `robotstxt` (2). All **three** selected top-1 failures rely on a **single** matching word (`tokenizer` or `warc2text`). This is a repeated *observed error mode*, **not** evidence that all single-term matches are bad: `robotstxt` may describe a compatible issue, and `lumio` can be specific infrastructure.
- The technical vocabulary and candidate-selection process were tuned on this corpus **before** this review. A future independent holdout is necessary before trusting any new filtering rule.

## A higher-leverage observation came from the primary sources, not the candidate rankings

The interesting *research decision* is inside the [audio/video extraction thread](https://github.com/OpenEuroLLM/web-data-processing/issues/8):

- The team reports **little useful audio in the 2025/2026 Common Crawl snapshots**, but more in **2018/2019**: [original team comment](https://github.com/OpenEuroLLM/web-data-processing/issues/8#issuecomment-6753122403). This is a reported finding, not independently verified by us.
- A developer estimates **3–5 days** for extending the WARC pipeline: [original estimate](https://github.com/OpenEuroLLM/web-data-processing/issues/8#issuecomment-6780649827).
- The group is **already deciding how to run a sample across different crawls** for useful-yield estimates: [planning comment](https://github.com/OpenEuroLLM/web-data-processing/issues/8#issuecomment-6795969898).
- The discussion also exposes limited LUMI-O capacity: [storage comment](https://github.com/OpenEuroLLM/web-data-processing/issues/8#issuecomment-6829815600).

**High-value question (already being asked by researchers):** Before expensive reprocessing, which mixture of year, MIME type and crawler snapshots yields enough usable audio for training? A small representative source-year/MIME pilot, with downstream usefulness and storage cost measured, could matter more than another lexical cross-project suggestion.

**Do not duplicate this advice publicly:** the team already debates the same sample design and has an assigned developer. This is evidence of *ongoing coordinated work*, not a new collaboration or measured avoided compute. No external code, comments or issues were changed.

## Why these matches failed

The matcher scores the shared identifier `warc2text` even when one task is about **retroactive opt-out** and the other is about **de-chunking archived HTTP responses**. Those have distinct requirements and outputs. The shared word `tokenizer` likewise links a GPT-NeoX MoE training baseline with an unrelated CLIP tokenizer API change.

The text baseline got closer to the processing domain in two cases, but its HPLT storage/release issue still does not solve the source requirements. Both systems need a **question/measurement compatibility check** before treating any pair as an action.

## Decision for the repository

1. **Do not auto-filter all single-token matches yet**: 15/25 archived suggestions use one term, including potentially legitimate `robotstxt` and `lumio` connections. Blindly removing them may harm recall.
2. Keep the existing, already-tested [collaboration review source/evidence gate](../../collaboration_review.py) before any human-facing claim of reuse or new partnership.
3. Prioritize **evidence about the actual pending experiment**: required input/output, source code readiness, results and prior public coordination. For #8, that information is contained in comments rather than in the top-1 cross-repo link.
4. If we revisit matching, freeze fresh unseen source anchors first and compare an *unchanged* full-text baseline and a proposed stricter gate using independent reviewers. Do not optimize on these three inspected examples.
5. Keep negative candidate pairs and the original matcher output untouched, so later checkpoints can explain why an idea was rejected.

**Result:** A useful *negative* test of the cross-project matcher, **no demonstrated graph advantage**, and a confirmed need to connect source discussions to concrete decisions. Do not expand graph infrastructure on this evidence.
