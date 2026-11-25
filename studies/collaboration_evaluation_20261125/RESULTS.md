# Same-input collaboration pilot — 2026-11-25

## Result and decision

**No-go for expanding the current lexical matcher as if it were an established collaboration finder.** The current method abstained on all ten frozen source tasks. The plain same-input IDF overlap baseline retrieved ten candidates; preliminary original-source inspection found no immediately actionable reuse. This does not establish higher precision (zero suggestions means undefined precision), recall, or graph advantage.

## Provenance and selection

- [Automatic discovered-source triage](https://github.com/tire0011/ai-research-graph/actions/runs/45560254829): 12 repository metadata inspections, four topical hypotheses, zero issue/PR records in the selected four repositories, zero review packets, one repository metadata error (DiscernBench).
- [Fixed-cohort live evaluation](https://github.com/tire0011/ai-research-graph/actions/runs/45560463959): separate manually selected discovered-repository cohort, rules frozen before retrieval outcomes. Artifact `collaboration-evaluation-cohort/frozen_cohort.json`; corpus SHA256 `3bbe7d548a2c53ef46b919930a2627607cfb0d79628de9a740d988992cb94c9a`.
- The same input consists of 30 Helsinki-NLP/OPUS-MT-train records, 30 hplt-project/OpusTrainer records, 29 kyutai-labs/moshi-finetune records, 0 LAION-AI/agent-bud-e records, 89 total, zero acquisition errors. First two lists are possibly truncated. Twelve eligible open issues/PRs, ten sampled, all from Kyutai (six PRs and four issues). This is a narrow, manually chosen corpus, not a representative EU-wide or independent holdout.
- Method: existing technical gate, versus same-input unweighted IDF overlap on title plus first 6000 body characters, top-1 cross-owner earlier-created work. This is not a comparison against web search engines. Source selection by owner round-robin and creation date; no selection by usefulness.
- Labels below are a **non-blinded assistant assessment**, using separately fetched live issue/PR bodies after cohort freeze; the live text was inspected but hash parity against the frozen artifact was not independently checked in this assessment. No claim of independent human review, verified implementation compatibility, or exhaustive absence of possible handoffs. Preserve the frozen corpus for independent labels.

## Preliminary outcome review

All technical targets are null (abstained). The baseline target and preliminary label for each source:

| Kyutai source | HPLT baseline target | Label | Why |
|---|---|---|---|
| [PR 29](https://github.com/kyutai-labs/moshi-finetune/pull/29) | [#46](https://github.com/hplt-project/OpusTrainer/issues/46) | unrelated | Dependency pin and sphn compatibility vs historical training-curve issue. |
| [PR 28](https://github.com/kyutai-labs/moshi-finetune/pull/28) | [#46](https://github.com/hplt-project/OpusTrainer/issues/46) | topic only | Token-weighted distributed evaluation vs teacher-model curve anomaly. No matching measurement or reusable implementation. |
| [PR 27](https://github.com/kyutai-labs/moshi-finetune/pull/27) | [#46](https://github.com/hplt-project/OpusTrainer/issues/46) | unrelated | FSDP gradient clipping/startup vs Marian epoch/warmup anomaly. |
| [PR 26](https://github.com/kyutai-labs/moshi-finetune/pull/26) | [PR 63](https://github.com/hplt-project/OpusTrainer/pull/63) | unrelated | LoRA checkpoint export vs sentence punctuation modifier. |
| [PR 25](https://github.com/kyutai-labs/moshi-finetune/pull/25) | [#46](https://github.com/hplt-project/OpusTrainer/issues/46) | topic only | Frame-accurate supervision/annotation contract vs training data/epoch investigation. |
| [#24](https://github.com/kyutai-labs/moshi-finetune/issues/24) | [#54](https://github.com/hplt-project/OpusTrainer/issues/54) | topic only | Both involve alignment/index correctness but one is audio duration/frame masking, the other source/target text-token bounds; general test idea, not a demonstrated reusable solution. |
| [PR 22](https://github.com/kyutai-labs/moshi-finetune/pull/22) | [#46](https://github.com/hplt-project/OpusTrainer/issues/46) | unrelated | CUDA environment and dependency conflict vs training curve anomaly. |
| [#21](https://github.com/kyutai-labs/moshi-finetune/issues/21) | [#44](https://github.com/hplt-project/OpusTrainer/issues/44) | topic only | Need for monophonic pretraining vs stage-specific Marian early stopping. A stage configuration feature cannot answer the scientific question. |
| [#20](https://github.com/kyutai-labs/moshi-finetune/issues/20) | [#40](https://github.com/hplt-project/OpusTrainer/issues/40) | unrelated | Distributed PyTorch backward error vs Unicode typo-modifier KeyError. |
| [#19](https://github.com/kyutai-labs/moshi-finetune/issues/19) | [PR 63](https://github.com/hplt-project/OpusTrainer/pull/63) | unrelated | MLX LoRA fine-tuning vs punctuation robustness. |

Technical: 0 suggestions, 10 abstentions, actionable yield 0/10, precision undefined. Baseline: 10 suggestions, 4 topic-only, 6 unrelated, 0 confirmed actionable, preliminary yield 0/10. No claims about recall because relevant unreturned work was not exhaustively labelled. Contact status does not change these scientific labels.

## Exploratory finding outside the frozen cohort

Manual README inspection of the four new research repositories from the empty issue sample surfaced a more promising **methodological hypothesis**, not a verified collaboration:
- [AtmosRegime](https://github.com/acodercat/atmosregime) ([paper](https://arxiv.org/abs/2611.28669)): contrasts physical-formula validity regimes and explicit correct-formula or warning conditions. README blob 09945caf443f1a6c8e43bceff31d4525a356b850.
- [RuleCraft](https://github.com/gaojianxin05/rulecraft) ([paper](https://arxiv.org/abs/2611.28745)): contrasts text, named game and image-only rules against game-engine-checked outcomes. README blob 410c315e542a204997edf56e48bd54d7a496fff9.
- Shared question: can a model apply the correct rule when the governing context differs from its default? A small comparison could align experimental conditions and measure recognition versus execution, not combine incompatible text/image scores. This was not one of the automatically returned topic pairs and must not be counted as a matcher hit. No verified unmet maintainer need, EU affiliation, or current coordination; no outreach.

## Next decision gate

Keep issue retrieval and source provenance, preserve prior 0/3 negative result. Obtain independent labels on the frozen cases; broaden future cohort by source type and owner *before* labels. Investigate paper-level mechanisms and explicit artifacts as a separate experimental retrieval approach, rather than tuning technical keywords on these ten cases. Compare against same-input lexical/semantic retrieval on a new cohort. No automatic contact, no claim of graph advantage, no additional data-source expansion justified by this result.
