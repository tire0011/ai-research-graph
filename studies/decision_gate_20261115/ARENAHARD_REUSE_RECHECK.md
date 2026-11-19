# Decision recheck — Arena-Hard contamination exclusion after PR merge

**Date:** 2026-11-15
**Origin:** [Cross-project collaboration candidate review of 2026-11-10](../../results/COLLABORATION_REVIEW_NEXT_CASES.md), item 2.
**Status:** **Conditional reuse candidate**, not a confirmed unmet need, not a completed transfer or graph advantage.

## A previously recorded source fact changed

The earlier review described [OpenEuroLLM oellm-eval PR #174](https://github.com/OpenEuroLLM/oellm-eval/pull/174) as **open**. The linked original PR is now **merged** (2026-11-11 13:20:25 UTC). It implements `collect --exclude_samples` and recomputes eligible **JudgeArena** per-run win rates after removing contaminated questions. That converts a speculative pending change into source-backed existing code *within OpenEuroLLM*.

Control checks on the same date:
- [OpenEuroLLM post-training PR #65](https://github.com/OpenEuroLLM/post-training/pull/65) remains **open**.
- [AllenAI olmo-eval PR #358](https://github.com/allenai/olmo-eval/pull/358) remains merged.
- [AllenAI olmo-eval PR #372](https://github.com/allenai/olmo-eval/pull/372) remains merged.

This is a **purposefully chosen four-item freshness check**, not a random estimate of source staleness or measured saved time. One status claim in an earlier graph report changed. It demonstrates why candidate decisions must be rechecked *before recommendations*, not why a graph is automatically superior to direct GitHub search.

## Is anything reusable between projects?

**OpenEuroLLM implementation:** [#174](https://github.com/OpenEuroLLM/oellm-eval/pull/174) handles JudgeArena result formats, question IDs including multilingual suffixes, swapped judge order, and recalculates plain/weighted win rates. It carefully refuses to fabricate unsupported confidence intervals, Elo and AlpacaEval length-adjusted metrics.

**AllenAI implementation:** [olmo-eval PR #474](https://github.com/allenai/olmo-eval/pull/474) is merged. It implements Arena-Hard v2 using fixed upstream dataset and judge revisions, two judge positions, weighted verdicts, and separate style-adjusted and raw scores. Its [Arena-Hard task implementation](https://github.com/allenai/olmo-eval/blob/main/src/olmo_eval/evals/tasks/arena_hard.py) retains battle outcomes and style features in `judge_result`. The metric iterates stored responses, calls `in_slice`, and optionally fits style-adjusted win rates.

**Technical relationship:** The *validation principles* are complementary (stable question ID, exclude **both** judge orders, recompute supported aggregate metrics from **saved** predictions, identify invalid aggregates). **The OpenEuroLLM code is not a drop-in AllenAI patch**: the result schemas, benchmarks, judge/control metrics and task providers differ. Do not assume the presence of an unmet feature in AllenAI merely because the inspected Arena-Hard task file contains no `exclude_samples`/contamination-specific option. Other filtering tools, source pipelines or private practices may exist.

**Smallest actionable possibility, only if requested by maintainers:** Re-score a fixed public subset of previously stored Arena-Hard predictions after excluding a known question ID, using each framework's **native** metric implementation. Verify that both position-swapped battles are handled and compare the resulting raw/weighted scores. Check separately whether any style-controlled aggregate remains statistically interpretable on a changed sample; do **not** copy OpenEuroLLM's warnings or AllenAI's style estimator blindly. Do not schedule new model generations or judge calls until raw-recalculation feasibility is established.

**Stop conditions:** If the upstream team has no contamination-specific decision, if outputs are not available for offline rescoring, if a built-in filtering mechanism already serves the need, or if comparability of metric definitions fails, **no project change or outreach**.

## Plain-source-search comparison

A direct query for `Arena-Hard` in both repositories and reading [PR #174](https://github.com/OpenEuroLLM/oellm-eval/pull/174) and [PR #474](https://github.com/allenai/olmo-eval/pull/474) exposes the same source information. This work has **not shown** the graph retrieves this pairing faster or enables a better independently judged decision than ordinary search.

## Reusable finding for the research graph

The same candidate can change over time from `proposal_only` to `implemented` without a new similarity edge. The valuable record is a **dated evidence and decision change**:

`candidate shared benchmark` (Nov 10) -> `source implementation merged` (Nov 11) -> `code-level method comparison` (Nov 15) -> `conditional reuse pending actual receiver need`.

Do not overwrite the old report. **Append this update** and require source-state confirmation before converting any old research idea into a new action. This is relevant both to avoiding duplicate work and to growing a persistent research memory. No confirmed research acceleration or additional model capability is claimed.
