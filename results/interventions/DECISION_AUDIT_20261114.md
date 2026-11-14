# Decision audit: Can the graph prevent duplicate research and find low-cost leverage?

**Date:** 2026-11-14
**Type:** Read-only, source-following *qualitative* case audit
**Related vision:** [RESEARCH_VISION.md](../../RESEARCH_VISION.md) · [Checkpoint 0002](../../research_checkpoints/0002-unified-mission-2026-11-14.md)
**Structured source cards:** [DECISION_AUDIT_20261114.json](DECISION_AUDIT_20261114.json)

## Executive result

We reviewed **four purposeful OpenEuroLLM cases**, rather than starting another graph feature. The most useful immediate behavior is often **not** to build, repeat, or contact anyone:

- A current dataset-ablation task already targets multilingual SFT mixture decisions.
- LlamaFactory framework work has a clearly documented dependency and an open PR under active review; the researcher already asked about help.
- Two data-quality analysis approaches are *possibly complementary*, not demonstrably duplicate or integrated.
- A long-context regression is already the subject of detailed diagnosis.

**No measured graph advantage, compute savings, accepted collaboration, newly established causality, or model-quality gain is claimed.** The existing sources and ordinary issue search often reveal the central facts. The next useful evaluation must compare actual decisions with a fair source-following baseline.

### Method and evidence limits

On 2026-11-14 we inspected original public GitHub issue bodies, selected comments, PR status/description, the current repository's existing [intervention pilot](PILOT.md) and [judge-or-generator decision](JUDGE_OR_GENERATOR_DECISION.md), and published Hugging Face dataset descriptions. Example GitHub issue searches used:

- `repo:OpenEuroLLM/Taskboard "IFEVAL"`
- `repo:OpenEuroLLM/Taskboard "synthetic" "instruction"`
- `repo:OpenEuroLLM/Taskboard "LlamaFactory"`
- `repo:OpenEuroLLM/Taskboard "concept" "dataset"`

These returned multiple core tasks, including #448, #451, #437, #345, #391, #432, #353 and #318. We read original links and followed the #391 -> #432 -> PR #65 chain. **This was not a timed or blinded automated graph-vs-text benchmark.** We examined existing graph reports but did not run a fresh graph query on the same fixed sources. The text-based baseline here is an observed *discovery path*, not a numerical precision or recall score. GitHub issue bodies were live reads, not frozen by immutable source SHAs.

## Case A — Multilingual SFT ablations: avoid duplicate compute

**Primary sources:** [#451 leave-one-out](https://github.com/OpenEuroLLM/Taskboard/issues/451) (open, updated Nov 14), [#448 multilingual mix evaluation](https://github.com/OpenEuroLLM/Taskboard/issues/448), [#186 original data/replay tracks](https://github.com/OpenEuroLLM/Taskboard/issues/186), [#437 dataset generation](https://github.com/OpenEuroLLM/Taskboard/issues/437).

**Observed:** #451 describes four planned same-budget runs: one baseline containing three multilingual datasets, and three leave-one-out variants. Each uses 50B tokens and fixed 80/20 English-to-multilingual token accounting. #448 explicitly lists evaluation suites including IFEVAL and elo-EU; #186 contains earlier SFT mixture and replay measurements. An issue plan is not a report that all runs finished.

**Relationship:** *Related ongoing experiments*, not demonstrated duplicate teams. The #451 design tests the effect of removing one dataset **while reallocating its multilingual token share among the others**, not the isolated intrinsic quality of any dataset.

**Smallest useful action:** When #451 publishes results, check whether its benchmark definitions, language breakdown and baseline are actually comparable to #448 and #186. Avoid a duplicate SFT ablation or a new IFEval runner.

**Stop condition:** The evaluation contract is already shared or results are not yet reported. No new training proposed.

**Simple-search finding:** GitHub search `"synthetic" "instruction"` already surfaced #451, while `"IFEVAL"` surfaced #448.

## Case B — LlamaFactory: known dependency, not a missing collaboration

**Primary sources:** [#391 throughput task](https://github.com/OpenEuroLLM/Taskboard/issues/391), [#432 upstream LlamaFactory support](https://github.com/OpenEuroLLM/Taskboard/issues/432), [post-training PR #65](https://github.com/OpenEuroLLM/post-training/pull/65), [existing question from tire0011](https://github.com/OpenEuroLLM/Taskboard/issues/391#issuecomment-6741197470).

**Observed:** #391 directly declares dependency on #432; #432's comment links PR #65. As checked, #65 is **open, unmerged**. Its description reports **332 tests passed**, addressing submission/configuration handling; that is **not** a published same-configuration LUMI SFT/DPO throughput benchmark. The issue already contains a question from the researcher about blockers and possible reproducible benchmarking assistance. There is no reason to ask again.

**Relationship:** *Existing public coordination* and *upstream technical dependency*, not a new connection our graph uncovered.

**Smallest useful action:** Wait for a public implementation/benchmark milestone and then check whether #391 has a real uncovered throughput or reproducibility question. Otherwise abstain.

**Stop condition:** A comparable benchmark is already published or reviewers already cover the exact proposed issue. No unsolicited PR comment.

**Simple-search finding:** `"LlamaFactory"` returns #391 and #432; following one declared dependency and one PR link reaches the implementation. The graph has not demonstrated incremental value for this case.

## Case C — Data quality: potential complementarity, unproven advantage

**Primary sources:** [#437 synthgen](https://github.com/OpenEuroLLM/Taskboard/issues/437), [#353 sparse concept analysis](https://github.com/OpenEuroLLM/Taskboard/issues/353), [#416 Propella instruction selection](https://github.com/OpenEuroLLM/Taskboard/issues/416), [#318 prior curation](https://github.com/OpenEuroLLM/Taskboard/issues/318), [EuroMultiSynth release](https://huggingface.co/datasets/openeurollm/EuroMultiSynth-Instruct), [Propella annotations](https://huggingface.co/datasets/openeurollm/propella-annotations).

**Observed:** #437 produces synthetic instruction/answer pairs and filters them using a judge; #353 investigates candidate interpretable concepts with held-out validation; #416 uses Propella annotation dimensions for instruction selection. #318 is closed, #416 remains open. The released EuroMultiSynth subset has **4,160,598** accepted rows; scores are restricted to 7–10 and **77.7%** are score 10. The accepted data cannot independently explain why rejected generations failed. Published Propella annotations cover several Dolci splits, **not proven row-matched EuroMultiSynth annotations**.

**Relationship:** *Candidate complementary methods*, **not** established duplicate research and not proof that PrefScope detects missing qualities. Existing metadata and Propella's quality dimensions are important baselines.

**Smallest useful action:** Before any integration, compare a tiny fixed-seed language×domain×score sample and ask whether existing quality attributes or already-public Propella *methodology* suffice; any new concept signal needs independently held-out human confirmation. This is a proposed test, not an executed result.

**Stop condition:** No compatible language coverage, no independently validated labels, or no actionable signal beyond simple metadata. Do not claim judge bias from selected data.

**Simple-search finding:** `"concept" "dataset"` already retrieves #353, #318 and #32, and synthetic-instruction search retrieves #437; determining complementarity requires reading their intended mechanisms, not just matching phrases.

## Case D — Prelude long context: negative control / correct abstention

**Primary source:** [#392](https://github.com/OpenEuroLLM/Taskboard/issues/392), especially [RULER EOS diagnosis](https://github.com/OpenEuroLLM/Taskboard/issues/392#issuecomment-6824248223) and [checkpoint release](https://github.com/OpenEuroLLM/Taskboard/issues/392#issuecomment-6858140249).

**Observed:** Long context development, RULER QA failures, EOS-first hypotheses, checkpoint controls, training curves and release discussion are already documented in extensive public comments. The issue remains open; public source comments report `prelude-long` checkpoint availability.

**Relationship:** *Already active investigation*. Recommending generic long-context testing would duplicate ongoing work.

**Smallest useful action:** No action without a specific *unmeasured*, decision-changing experiment.

**Stop condition:** Ordinary source reading already answers the proposed next question.

## One combined decision table

| Case | Relationship | Proposed decision | Scientific evidence of gain? |
| --- | --- | --- | --- |
| #451 ↔ #448 ↔ #186 | Related planned training | Do not duplicate ablation; check matched evaluation only when results exist | No |
| #391 → #432 → PR #65 | Declared dependency + active implementation | Do not duplicate review; check after public milestone | No |
| #437 ↔ #353 ↔ #416 | Possible complementarity | Tiny baseline first; no integration yet | No |
| #392 | Existing thorough investigation | Abstain from generic intervention | No |

A recommendation *not* to act is valid if it is properly sourced. But merely discovering existing work is not evidence that the graph saves researcher time: the simple baseline found much of it as well.

## What to measure next (without more infrastructure)

A single fair **decision-quality pilot**, using a few *unseen* questions:

1. Freeze a source window and two or three actual researcher decisions (e.g. a real merge/blocker question, an evaluation gap, a genuinely candidate reusable artifact).
2. Give direct source-following search and graph-assisted review the **same original sources**, retrieval budget, and ability to follow multiple hops.
3. Blindly review each answer for exact evidence support, correct abstention, what concrete decision it changes, and estimated reviewer effort.
4. Record whether a recommendation actually prevented duplicate work, led to confirmed reuse or changed a measured experiment. Otherwise state *unproven*.
5. If direct source search remains as useful, simplify; do not justify new graph architecture from qualitative possibilities.

This pilot is compatible with the wider [Research Vision](../../RESEARCH_VISION.md), including future cross-disciplinary hypothesis checkpoints and the 2023-cutoff historical test. **The original duplication/leverage goals remain primary, not replaced.**
