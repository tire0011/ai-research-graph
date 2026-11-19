# Decision gate — StateBench for Prelude long context

**Reviewed:** 2026-11-15
**Type:** Follow-up to a *pre-existing* graph-generated cross-project candidate, not a new discovery.
**Decision:** **DO NOT IMPLEMENT OR CONTACT MAINTAINERS** on the current evidence. Preserve as a conditional research-evaluation idea.
**Original candidate:** [COLLABORATION_REVIEW_NEXT_CASES.md](../../results/COLLABORATION_REVIEW_NEXT_CASES.md), item 1.

## The actual decision question

Would integrating the newly available StateBench test into OpenEuroLLM's Prelude 256k evaluation be a *small high-leverage intervention*, avoiding duplicated tests or addressing the current release blocker?

The prior graph card described the task as a complement to Needle-In-A-Haystack and implied it might be a relatively inexpensive handoff. We challenge this before writing code.

## Original evidence and technical comparison

| Dimension | OpenEuroLLM side | AllenAI side | Implication |
| --- | --- | --- | --- |
| Target | [Taskboard #392](https://github.com/OpenEuroLLM/Taskboard/issues/392): extend Prelude to 256k, release a working long-context model | [olmo-eval PR #358](https://github.com/allenai/olmo-eval/pull/358) merged: StateBench state-tracking tasks | Complementary broad topic, **not** duplication |
| Current blocker | [RULER EOS analysis](https://github.com/OpenEuroLLM/Taskboard/issues/392#issuecomment-6824248223): model selects EOS as first answer token on `qa_hotpot` and `qa_squad`; source reports 91/100 and 83/100 EOS-first in a selected 4k checkpoint probe, with large score changes under `min_tokens 1` | StateBench reports multiple-choice **per-token logprob accuracy** for state variables, not generated answers after an `Answer:` cue | **Different failure mode**: StateBench is **not a direct diagnostic** for EOS-first collapse |
| Existing evaluation | #392 includes an extensive RULER curriculum, checkpoint and EOS-control investigation; [RULER itself](https://github.com/NVIDIA/RULER) covers more than single-needle retrieval, including variable tracking/aggregation | [StateBench publication 2026-11-03](https://huggingface.co/blog/allenai/statebench) explores state tracking with multiple formats and update regimes; olmo-eval has 10% subsets | Extra coverage may help **only if** a state-tracking gap remains; do not portray RULER as NIAH-only |
| Runner | [oellm-eval README](https://github.com/OpenEuroLLM/oellm-eval/blob/main/README.md) and [pyproject](https://github.com/OpenEuroLLM/oellm-eval/blob/main/pyproject.toml) show HPC scheduling around lm-eval-harness and its own task groups | [olmo-eval README](https://github.com/allenai/olmo-eval/blob/main/README.md) documents a separate task/provider runtime and task registration | Porting StateBench is **not evidenced as plug-and-play**; exact integration cost not measured |
| Checkpoint | [openeurollm/prelude-long](https://huggingface.co/openeurollm/prelude-long) now exists publicly | StateBench published on HF with length strata, including 128k/256k; 10% task variants available in olmo-eval | Public artifacts exist; this is **not** evidence that an evaluation run is practical on a local 8GB GPU |

## Ordinary search as baseline

Two simple search paths are enough to rediscover the underlying candidate:
1. Search the OpenEuroLLM Taskboard for long-context / RULER and open [#392](https://github.com/OpenEuroLLM/Taskboard/issues/392).
2. Search for `long context state tracking benchmark` or `StateBench` and read [the 2026-11-03 public benchmark explanation](https://huggingface.co/blog/allenai/statebench) or [olmo-eval #358](https://github.com/allenai/olmo-eval/pull/358).

The earlier cross-project graph review already found this candidate; **this audit neither proves novelty of retrieval nor times the source-search baseline**. Crucially, the *actual* decision requires reading definitions and failure modes, not just linking issue titles.

## Evidence-level decisions

- **Supported:** #392's EOS problem is real *as reported by its maintainers*; StateBench measures a distinct state-tracking score; the integration harnesses are different; StateBench PR #358 is merged.
- **Not supported:** StateBench would fix, diagnose or prevent the EOS-first collapse; porting it into oellm-eval would be trivial; OpenEuroLLM does not already have equivalent state-tracking evaluation in private; a cross-org collaboration is required.
- **Potentially useful later:** a narrowly specified head-to-head evaluation of 4k/32k and then 128k/256k state-tracking error classes on published checkpoints, if maintainers say existing RULER tests leave a meaningful gap and resource/runner compatibility is confirmed.

## Smallest next action, with stop rules

**Now: no action on third-party repos.** Do **not** propose a new benchmark integration as a remedy for EOS, because it targets a different variable. Do **not** duplicate already documented RULER/EOS investigations.

If future evidence shows a missing *state-tracking* decision (not EOS), first compare RULER's current variable-tracking tasks with StateBench's task and format families. Define the unique new measurable outcome before any port. Then run a **single 10% short-context subset** on one public checkpoint **only if** the existing runner can do so with low effort and approved compute. Stop if the new score changes no research decision or requires substantial integration merely to produce another benchmark number.

This is a **credible negative/no-go research result**: an attractive multi-hop connection does not imply a worthwhile intervention. It is not proof that the graph saves time: reading the primary sources makes the same limitation visible.

## Reusable graph learning

Preserve the original candidate **and this rejection as an evidence-linked update**. The graph should eventually distinguish:

`shares_topic` → `mechanism_comparison` → `measurement_compatibility` → `incremental_value` → `decision`.

These are **proposed labels**, not currently implemented graph edge types. Do not add a schema/service based on this one example. Review future candidate connections against existing control experiments and *what variable they actually measure*, not lexical similarity alone.
