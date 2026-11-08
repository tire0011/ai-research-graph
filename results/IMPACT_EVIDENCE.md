# OpenEuroLLM change-impact candidates: ten original-source audits

Graph snapshot: `2026-11-08T21:30:14.918186+00:00`. Evaluated: `2026-11-08T21:33:28.762210+00:00`. Evidence verified: **10/10** cases, **21** literal phrases, **4** separately fetched comments. Status: `completed`.

Graph source parity for selected comments: **4/4**. Author-declared upstream links in the graph: **1**; commenter-reported OOM links: **1**. These are evidence classifications, not independent validation of the asserted dependency or failure.

**This is not a speedup ranking.** The ten open issues were purposefully selected for varied engineering signals. A reported result has not been independently reproduced; an issue reference does not prove a blocker. Do not sum unlike speed, accuracy and automation claims.

## Candidate changes and validation needed

| Issue | Source evidence class | Proposed change | Missing proof before impact claim |
| --- | --- | --- | --- |
| [github:OpenEuroLLM/Taskboard#385](https://github.com/OpenEuroLLM/Taskboard/issues/385) | `reported_speedup_pending_validation` | Validate the revised sequence-to-worker assignment before production adoption. | Reproduce throughput and complete the pending memory, save and resume acceptance checks. |
| [github:OpenEuroLLM/Taskboard#207](https://github.com/OpenEuroLLM/Taskboard/issues/207) | `cross_hardware_performance_gap` | Investigate expert-parallelism configuration and measure matched Jupiter runs. | Compare configurations on the same hardware and power envelope; do not treat reference H100 numbers as a demonstrated speedup. |
| [github:OpenEuroLLM/Taskboard#442](https://github.com/OpenEuroLLM/Taskboard/issues/442) | `reported_quality_gain_not_speedup` | Isolate the chat-template/thinking-adherence effect with a same-base control. | Report same-base accuracy and generated-token costs; quality gains are not throughput gains. |
| [github:OpenEuroLLM/Taskboard#391](https://github.com/OpenEuroLLM/Taskboard/issues/391) | `explicit_upstream_dependency` | Complete LlamaFactory support so a same-configuration TRL throughput comparison can be run. | Verify Taskboard #432 completion, then benchmark comparable SFT/DPO configurations on LUMI. |
| [github:OpenEuroLLM/Taskboard#432](https://github.com/OpenEuroLLM/Taskboard/issues/432) | `proposed_enabler` | Add and verify LlamaFactory in the post-training repository. | Validate an equivalent checkpoint before treating the backend as a credible TRL alternative. |
| [github:OpenEuroLLM/Taskboard#433](https://github.com/OpenEuroLLM/Taskboard/issues/433) | `reported_memory_blocker` | Find a feasible LUMI DPO configuration for the FSDP branch. | Confirm reproducible OOM and a successfully completed equivalent DPO run; measure throughput only afterward. |
| [github:OpenEuroLLM/Taskboard#340](https://github.com/OpenEuroLLM/Taskboard/issues/340) | `incomplete_automation` | Complete automatic checkpoint conversion within existing monitoring tooling. | Measure manual conversion time, error rate and end-to-end checkpoint availability before claiming saved researcher time. |
| [github:OpenEuroLLM/Taskboard#445](https://github.com/OpenEuroLLM/Taskboard/issues/445) | `proposed_automation` | Generate model-card tables and plots automatically from the evaluation dataset. | Compare time-to-publish and correction rates before and after automation. |
| [github:OpenEuroLLM/Taskboard#416](https://github.com/OpenEuroLLM/Taskboard/issues/416) | `quality_hypothesis` | Evaluate instruction-level dataset selection against the recorded baseline. | Compare model quality and data-processing cost on consistent training/evaluation setups; do not infer faster training from a link to a dataset. |
| [github:OpenEuroLLM/Taskboard#405](https://github.com/OpenEuroLLM/Taskboard/issues/405) | `planned_coverage` | Complete missing safety and fairness evaluation integrations. | Measure evaluation completeness and execution cost separately; coverage itself is not a throughput speedup. |

## Inspectable original-source evidence

### github:OpenEuroLLM/Taskboard#385 — Train and export the OELLM 9B function-calling SFT checkpoint on LUMI

Live issue state: `open`. Body versus graph: `exact_parity`. GitHub task-reference edges from this issue: **1**. Issue-body SHA256: `4a7887b689cbdc129280936e03a9a1684aaabf7c5b42deaf375b4f6039151ffc`.

- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/385): `106–107k tokens/s` — A revised assignment was timed above the earlier 94–99k-token/s production range.
- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/385): `about 9.5% faster` — Issue authors report a controlled comparison, not independently reproduced here.
- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/385): `remain required before adoption` — Production validation is explicitly outstanding.

### github:OpenEuroLLM/Taskboard#207 — Qwen3 235B-A22B weak scaling optimization

Live issue state: `open`. Body versus graph: `exact_parity`. GitHub task-reference edges from this issue: **1**. Issue-body SHA256: `190208fb084fd5d2d4832bcd457dafbdb6b406b37efc160b28682ec94b54d837`.

- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/207): `170–175` — The issue reports a current Jupiter throughput range in TFLOPs/s/GPU.
- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/207): `power cap` — Reference hardware and power limits differ, confounding the gap.
- [comment evidence](https://github.com/OpenEuroLLM/Taskboard/issues/207#issuecomment-4276947736): `Scaling EP instead of PP or TP seems to be the way to go` — A participant proposes a parallelism direction, without an independently verified gain.
- Source-hashed comment nodes in graph: `github_comment:OpenEuroLLM/Taskboard#4276947736` (`exact_parity`)

### github:OpenEuroLLM/Taskboard#442 — Investigate performance gap between current and Marianna's pipeline

Live issue state: `open`. Body versus graph: `exact_parity`. GitHub task-reference edges from this issue: **0**. Issue-body SHA256: `c8fb2d8fafecd4da87af75d3acf92171d5168e39a9f3618749e87caa44cec38d`.

- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/442): `before / after chat template fix` — The issue requests a controlled comparison to address a confounding factor.
- [comment evidence](https://github.com/OpenEuroLLM/Taskboard/issues/442#issuecomment-6635516812): `84.6%` — The comment reports forced-thinking MATH500 accuracy.
- [comment evidence](https://github.com/OpenEuroLLM/Taskboard/issues/442#issuecomment-6635516812): `34.8%` — The default-thinking MATH500 accuracy is reported separately.
- [comment evidence](https://github.com/OpenEuroLLM/Taskboard/issues/442#issuecomment-6721237269): `same base model as SFT-Excellent-v0.1` — A later comment says the same-base training control is still in progress.
- Source-hashed comment nodes in graph: `github_comment:OpenEuroLLM/Taskboard#6635516812` (`exact_parity`), `github_comment:OpenEuroLLM/Taskboard#6721237269` (`exact_parity`)

### github:OpenEuroLLM/Taskboard#391 — Ensuring post-training pipeline works

Live issue state: `open`. Body versus graph: `exact_parity`. GitHub task-reference edges from this issue: **1**. Issue-body SHA256: `3a88d7745a1405179ae3646bdb738d356f40a27cc7a55bb01974b366af19879f`.

- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/391): `Compare throughput against the existing TRL implementation` — A throughput comparison is planned; no result is asserted.
- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/391): `__Dependencies__
Issue #432` — The Dependencies section explicitly names the upstream task.
- [Explicitly named upstream task](https://github.com/OpenEuroLLM/Taskboard/issues/432): `github:OpenEuroLLM/Taskboard#432` (live state `open`, literal graph reference: `True`, declared-dependency edge: `True`).

### github:OpenEuroLLM/Taskboard#432 — Extend LLMFactory support to the post-training repo

Live issue state: `open`. Body versus graph: `exact_parity`. GitHub task-reference edges from this issue: **0**. Issue-body SHA256: `cc9dbde87ac631bbe255cf1b164301cc2ceedbef5648128b31d06b99b6d23393`.

- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/432): `Support LlamaFactory` — The issue is a planned implementation, not a measured improvement.
- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/432): `performance comparable` — Comparable performance is an acceptance target, not an observed result.

### github:OpenEuroLLM/Taskboard#433 — Add support for FSDP to TRL in the post-training repo

Live issue state: `open`. Body versus graph: `exact_parity`. GitHub task-reference edges from this issue: **0**. Issue-body SHA256: `1f43adea95275eb9448196b61d1de53bf44fd8ebccd21686f35d24cf8ce81a9a`.

- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/433): `Add support for Fully Sharded Data Parallel` — FSDP support is the work item.
- [comment evidence](https://github.com/OpenEuroLLM/Taskboard/issues/433#issuecomment-6121054773): `fails due to OOM issues on LUMI` — An issue comment reports a concrete memory blocker, absent from the issue-body-only graph.
- Source-hashed comment nodes in graph: `github_comment:OpenEuroLLM/Taskboard#6121054773` (`exact_parity`)

### github:OpenEuroLLM/Taskboard#340 — Set up monitoring and automatic tools for model training

Live issue state: `open`. Body versus graph: `exact_parity`. GitHub task-reference edges from this issue: **0**. Issue-body SHA256: `662fc8ca2fa727ff03a6cbce755802544cbb3894880cb5092226e27688300d27`.

- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/340): `- [ ] Automatic checkpoint conversion` — A specific automation step remains unchecked in the issue.

### github:OpenEuroLLM/Taskboard#445 — Automatic evaluation reporting for model card

Live issue state: `open`. Body versus graph: `exact_parity`. GitHub task-reference edges from this issue: **0**. Issue-body SHA256: `05a981a03488774b06a6995f3d8120ee921d441da1c175c80e9c516bc1f97a6c`.

- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/445): `a single script which generates model card table` — The task defines a concrete automation goal but reports no saved time.

### github:OpenEuroLLM/Taskboard#416 — Post-training dataset curation using instruction-level selection

Live issue state: `open`. Body versus graph: `exact_parity`. GitHub task-reference edges from this issue: **2**. Issue-body SHA256: `91d6419829bd9fdf51ccb72a81ee9053a4c6d78bb3d5fe67806da46766bcc8fd`.

- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/416): `instruction-level selection` — The issue proposes a data-quality experiment.
- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/416): `The goal was to have a baseline` — A baseline is described, but not a measured speed gain.

### github:OpenEuroLLM/Taskboard#405 — Add safety and fairness benchmarks

Live issue state: `open`. Body versus graph: `exact_parity`. GitHub task-reference edges from this issue: **1**. Issue-body SHA256: `8b8a346753980d87e89f8483baca7e952fb9b4532479610d34814fea86fe39f2`.

- [body evidence](https://github.com/OpenEuroLLM/Taskboard/issues/405): `Add and verify 'inspect_evals' integration` — Benchmark integration work is explicitly tracked.

## Research validity and next step

- **Measured training throughput**: #385 reports an approximately 9.5% uplift for a revised worker assignment, with production acceptance still outstanding. The report verifies that the authors made this claim, not its reproducibility.
- **Evaluation quality, not speed**: #442's comments document a thinking-mode accuracy difference; a same-base control is noted as pending. Increased generated tokens could make the stronger quality result slower to compute.
- **Dependency and feasibility**: #391 explicitly lists #432 as an upstream task; #433's comment reports a LUMI OOM problem. Neither is evidence of a realized speedup.
- **Data gap**: issue comments in 3 cases contain essential evidence not stored in the graph's issue-body-only snapshot. An impact query should therefore either include versioned comments or abstain from declaring no known blocker.
- **Selection bias**: these ten items were selected for promising, different signals after seeing issue titles. They are not representative of the indexed issue population and cannot establish which project should receive resources.
- **Impact estimation**: a credible next experiment needs a causal dependency relationship, a baseline, a same-configuration intervention, adoption/rollout status and an outcome measurement. A graph-edge count alone is not impact.
