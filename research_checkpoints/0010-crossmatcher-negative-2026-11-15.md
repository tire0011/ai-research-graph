# Research checkpoint 0010 — Single keywords are not research overlap

**Date:** 2026-11-15
**Type:** Preselected small cross-project comparison + bounded code change
**Extends:** [Checkpoint 0009](0009-source-drift-2026-11-15.md)
**Selection frozen first:** [SELECTION.md](../studies/crossmatcher_review_20261115/SELECTION.md)
**Source reviews and labels:** [RESULTS.md](../studies/crossmatcher_review_20261115/RESULTS.md) · [RESULTS.json](../studies/crossmatcher_review_20261115/RESULTS.json)
**Code:** [PR #44](https://github.com/tire0011/ai-research-graph/pull/44) — merged after repository offline tests passed

## Our original objective remains

Build one evidence-grounded research graph to **spot potential duplicate effort, reuse existing work, find high-leverage low-effort interventions, connect complementary teams, and develop testable cross-disciplinary hypotheses**. Human questions explore new paths through that mission; old hypotheses and decisions are not silently replaced.

## Findings from three pre-registered source anchors

We compared the earlier technical-vocabulary matcher's top choice against the **same-input, full-text baseline top choice** for three deliberately selected *different-target* source tasks. We read both target sources and the public issue comments rather than assume shared words equal reuse.

| Source task | Technical candidate | Full-text candidate | Correct decision |
| --- | --- | --- | --- |
| [MoE training baseline #119](https://github.com/OpenEuroLLM/Taskboard/issues/119) | Unrelated CLIP tokenizer change: **0** | Unrelated CLIP distributed-evaluation fix: **0** | No relevant cross-project reuse |
| [Opt-out processing #3](https://github.com/OpenEuroLLM/web-data-processing/issues/3) | Unrelated HTTP de-chunking: **0** | Adjacent HPLT robots.txt release planning: **1** | Existing Apertus/Swiss-AI methodology already cited in own issue |
| [Audio/video WARC extraction #8](https://github.com/OpenEuroLLM/web-data-processing/issues/8) | Unrelated de-chunking: **0** | Adjacent HPLT crawl-storage work: **1** | No external reusable extractor; source team already plans small multi-crawl trial |

*Rubric:* 0 irrelevant; 1 adjacent; 2 sourced plausible reuse; 3 verified technical action candidate. Three sources, six candidate pairs, one non-blinded assistant reviewer, original matcher **previously tuned on the observed cohort**.

**Actionable candidates (score ≥2):** technical matcher **0/3**, ordinary full-text **0/3**. Coarse topical relevance scores: 0 vs 2; full text did better in two source cases but both were **non-actionable**. Do not claim general full-text or graph superiority or independent validity from this tiny non-blind review.

## The most useful research fact was in an issue discussion

[OpenEuroLLM audio extraction #8](https://github.com/OpenEuroLLM/web-data-processing/issues/8) says 2025/2026 crawls appear to contain little usable audio while 2018/2019 crawls were more useful, as reported by contributors. The team is already choosing an affordable sample across crawls, discussing LUMI-O storage and an estimated **3–5 days** for a WARC extension. None of these estimates was independently verified here.

The potential high-information action is a **small year×MIME×crawl-sample trial** before major reprocessing. But that is **not a new suggestion or collaboration**: project contributors have already proposed it. Correct graph behavior is to make the existing plan and its supporting observations visible and **not send duplicate advice**.

## Systemic failure mode

Among 25 historic candidate matches, **15 share exactly one** technical term: 7 `tokenizer`, 4 `warc2text`, 2 `lumio`, 2 `robotstxt`. The selected technical top-1 false matches had only `tokenizer` or `warc2text` in common.

**Importantly**, single terms can be genuinely specific: `robotstxt` might indicate the same opt-out problem, `lumio` the same infrastructure. Automatically removing 15 suggestions could create false negatives.

## Small verified code improvement

[PR #44](https://github.com/tire0011/ai-research-graph/pull/44) introduces **`single_term_only`** on candidate records and a clear *requires mechanism review* warning in human-readable reports. It **does not change ranking, remove candidates, assert duplication, contact researchers or trigger expensive experiments**. Two regression tests preserve both single-term and multi-term matches.

This is **better visibility of weak evidence**, not a proven increase in relevance or research throughput. The existing [collaboration evidence validator](../collaboration_review.py) remains the real gate before treating a link as potential reuse.

## Strategic synthesis: what to stop and what to measure

The graph's literal reference benchmarks already tied ordinary text, and this test adds **no evidence of useful new cross-project matching**. Therefore:

1. **Stop tuning ranking on the same inspected cohort**. The vocabulary was already tuned there, and further tiny wins would be overfitting.
2. Do not create generic semantic edges or new agents based on a shared topic. Keep negative observations and contradictions in the permanent research memory.
3. For any future matcher value claim, commit **fresh unseen tasks and the exact baseline first**, then obtain independent blinded source-review labels and a real decision outcome. One method's top-1 looking interesting is not sufficient.
4. Spend the next bounded research cycle on an **actual unaddressed scientific/engineering decision**, selected by evidence of an unmet need rather than by a lexical match. Prefer a tiny information-gaining experiment over broad infrastructure.
5. Preserve the separate **prospective hypothesis track**, including the 2023 replay's acknowledged training-leakage failure, as another use of the same research graph rather than a new mission.

**No external GitHub discussions were modified. No proven saved compute, new scientific discovery, or graph-vs-search advantage is claimed.**
