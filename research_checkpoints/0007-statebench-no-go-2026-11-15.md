# Research checkpoint 0007 — An attractive link fails the action test

- **Date:** 2026-11-15
- **Type:** Critical review of existing cross-organization graph candidate
- **Extends:** [Checkpoint 0006](0006-unified-evidence-2026-11-15.md)
- **Case:** [StateBench ↔ Prelude review](../studies/decision_gate_20261115/STATEBENCH_VS_PRELUDE.md)
- **Status:** **No-go for immediate integration/outreach**; conditional evaluation idea preserved

## Human goal remains unchanged

Use the same evidence graph to **avoid redundant research**, find **small high-leverage actions**, **connect genuinely complementary work**, and develop **falsifiable scientific hypotheses** with durable checkpoints. Human exploratory questions are probes, not a new mission each time.

## Before / after

**Previous graph candidate:** OpenEuroLLM's Prelude long-context work could complement AllenAI's new StateBench state-tracking tests, perhaps an efficient extra evaluation.

**New verified technical comparison:**

- OpenEuroLLM [Taskboard #392](https://github.com/OpenEuroLLM/Taskboard/issues/392) reports a **generative EOS-first answer collapse** in RULER QA. This is already investigated through controlled checkpoints and decoding probes.
- AllenAI [olmo-eval PR #358](https://github.com/allenai/olmo-eval/pull/358), merged, supplies StateBench **per-token multiple-choice logprob** scoring for state-tracking problems, with 10% variants.
- These are **different outcome variables and protocols**. StateBench cannot be recommended as a fix or direct diagnostic for the EOS-first failure.
- RULER already includes variable-tracking/aggregation tasks, so claiming "new kind of state tracking not in RULER" without comparing existing task coverage would be unsound.
- OpenEuroLLM's evaluation orchestration is lm-eval-based, while olmo-eval uses its own framework. Porting or running cross-framework experiments has not been shown inexpensive.

**Result:** no immediate port, new test run or unsolicited maintainers' message. If the real later question is *state tracking*, first establish what current RULER tasks lack and whether a tiny existing StateBench subset could supply decision-changing evidence. Stop if there is no distinct question or integration is expensive.

## Why this matters to the graph

The failure is **not missing links**: the graph already retrieved a plausible cross-project pair. The missing reasoning is *measurement alignment*. Two groups can use the same topic language, yet a bridge may not address the target problem.

**Useful negative knowledge:** `topic overlap` ≠ `same mechanism` ≠ `compatible measurement` ≠ `cheap action`. Keep this no-go attached to the prior candidate, rather than repeating it later.

A direct ordinary search plus careful source reading can reach the same conclusion. **No graph advantage or time savings have been demonstrated.** This case also illustrates why adding thousands more speculative edges would be unwise.

## Decision threshold for further graph development

Do **not** build new automatic matching services/semantic edge databases based on this pilot. Continue only with small, source-backed decision tests until we can document a real example where a graph-based route **changes a reviewed research action** compared with equally informed source search at reasonable cost.

The separately documented 2023-cutoff historical replay remains hindsight-contaminated. A future real-time prospective hypothesis registry may be meaningful, but it must not inherit a false "successful future prediction" result.

## Next research checkpoint trigger

- A new, genuinely unresolved research need with competing published methods; or
- an independently judged useful action that source-following search missed under a comparable budget; or
- a new scientific experiment with hypotheses registered before its results.

**Negative result preserved. No third-party modifications and no new graph infrastructure.**
