# Research checkpoint 0008 — Decision gates beat more edges

**Date:** 2026-11-15
**Extends:** [0007 StateBench no-go](0007-statebench-no-go-2026-11-15.md)
**Process:** [Research Decision Gates](../RESEARCH_DECISION_GATES.md)
**Cases:** [StateBench ↔ Prelude](../studies/decision_gate_20261115/STATEBENCH_VS_PRELUDE.md) and [Arena-Hard reuse recheck](../studies/decision_gate_20261115/ARENAHARD_REUSE_RECHECK.md)
**Status:** Two bounded source-reviewed decision probes; no measured advantage over ordinary research, no research outcome or accepted collaboration.

## Original goal

Find where the **least extra work** has the most potential scientific value, while recognizing already-completed efforts and connecting complementary projects. Use the persistent graph to collect human questions, conflicts, evidence, experiments and later corrections, not to pursue the last conversation tangent.

## What we learned

1. **StateBench and Prelude long-context:** our existing graph surfaced an interesting cross-organization match, but an independent comparison of measurement protocols shows that StateBench's logprob state tracking would not directly diagnose Prelude's first-token EOS collapse in RULER QA. Moreover RULER already includes more than needle retrieval. **Decision: no immediate integration, no outreach, no extra GPU spending**. Preserve this as a tested negative intervention hypothesis.
2. **Arena-Hard contamination filtering:** a prior report described [OpenEuroLLM PR #174](https://github.com/OpenEuroLLM/oellm-eval/pull/174) as open, but it **merged on 2026-11-11**. Its actual implementation validates matched questions, two judge positions and which aggregate scores can safely be recalculated. [AllenAI's PR #474](https://github.com/allenai/olmo-eval/pull/474) has its own scoring system and saved judge outcomes. **Decision: conditional transfer of verification *principles*, no code port and no external message until a missing use case is demonstrated.**
3. Of **four purposely selected PR status claims** checked against the earlier notes, one had changed. That does **not** estimate overall project staleness, but demonstrates why dated checkpoints and a fresh original-source status preflight matter.

## How the main research idea becomes sharper

An evidence graph must not imply every related pair is an opportunity.

`human curiosity → candidate linkage → actual unmet decision → mechanisms/metrics → check existing code and studies → minimal falsifiable action → re-review after new evidence`.

Negative findings are first-class data. A rejected idea should be easier to retrieve later than to re-propose.

Our own full-text / graph retrieval benchmarks still show equal exact accuracy on bounded literal links. The case studies have *not* shown saved researcher time. This is evidence for **minimal tooling and stronger critical review**, not a justification for a new service.

## Next limited milestone

Try one previously unseen **genuine pending decision** with the [seven-question review protocol](../RESEARCH_DECISION_GATES.md). Compare normal source search against graph-assisted synthesis using identical source packets and an independent reviewer. Require a specific changed action; otherwise stop schema/service expansion.

In parallel, the historical 2023-cutoff exercise remains explicitly **retrospective and contaminated by later model knowledge**, not an actual future forecast. A genuinely prospective hypothesis experiment is a separate next direction if the right unanswered scientific question emerges.

**No external repositories were modified and no new runner, crawler, GPU training or benchmark integration was launched in this checkpoint.**
