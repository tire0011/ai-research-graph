# Twenty source-grounded GitHub research questions

Snapshot: `2026-11-13T19:33:08.963869+00:00`. Verified: **20/20**. Status: `completed`.

## Exact target-set correctness and correct abstentions

| Cohort | Method | Exact answers | Correct no-link answers | Source top-1 | Median lookup (ms) |
| --- | --- | ---: | ---: | ---: | ---: |
| all | Precomputed evidence graph | 18/20 | 8 | 18/20 | 2.6996 |
| all | Source text (same snapshot) | 18/20 | 8 | 18/20 | 2.7238 |
| all | Live GitHub issue/PR search | 18/20 | 8 | 18/20 | 349.3 |
| random | Precomputed evidence graph | 10/10 | 8 | 10/10 | 1.8606 |
| random | Source text (same snapshot) | 10/10 | 8 | 10/10 | 1.8779 |
| random | Live GitHub issue/PR search | 10/10 | 8 | 10/10 | 377.55 |
| reference_rich | Precomputed evidence graph | 8/10 | 0 | 8/10 | 2.6996 |
| reference_rich | Source text (same snapshot) | 8/10 | 0 | 8/10 | 2.7238 |
| reference_rich | Live GitHub issue/PR search | 8/10 | 0 | 8/10 | 337.55 |

**Do not compare snapshot milliseconds with live GitHub search milliseconds as a speedup.** The former has already paid data-collection and graph-indexing costs; the latter includes network latency. GitHub search indexing and rate limits may also affect results.

The random cohort was selected by fixed ID hashing without looking at bodies; the second cohort was deliberately enriched for reference-bearing tasks and can make the overall score optimistic. Frozen expected IDs were curated from source text; this is **not** a blinded human/LLM evaluation. All methods have the same repository, source type and title search phrase. The graph and text routes inspect captured data; the GitHub method uses live issue/PR search. A literal cross-reference does not prove an implementation, experiment or scientific dependency.

## Per-question audit

| Source task and question | Gold links | Graph exact | Text exact | GitHub exact |
| --- | ---: | --- | --- | --- |
| [github:OpenEuroLLM/Taskboard#351](https://github.com/OpenEuroLLM/Taskboard/issues/351): Function-calling RL reproduction and transfer study? | 1 | True | True | True |
| [github:OpenEuroLLM/Taskboard#320](https://github.com/OpenEuroLLM/Taskboard/issues/320): Add support for LUMI for our post-training pipeline? | 0 | True | True | True |
| [github:OpenEuroLLM/Taskboard#364](https://github.com/OpenEuroLLM/Taskboard/issues/364): Integrate Qwen3 MoE conversion to oellm-autoexp? | 1 | True | True | True |
| [github:OpenEuroLLM/Taskboard#130](https://github.com/OpenEuroLLM/Taskboard/issues/130): Add CUNI people to github? | 0 | True | True | True |
| [github:OpenEuroLLM/Taskboard#184](https://github.com/OpenEuroLLM/Taskboard/issues/184): Better LLM judges evaluation for instruction-tuned models? | 0 | True | True | True |
| [github:OpenEuroLLM/oellm-eval#152](https://github.com/OpenEuroLLM/oellm-eval/issues/152): Integrate vLLM as a backend? | 0 | True | True | True |
| [github:OpenEuroLLM/oellm-eval#5](https://github.com/OpenEuroLLM/oellm-eval/issues/5): Add instructions to add automatically in ~/.bashrc? | 0 | True | True | True |
| [github:OpenEuroLLM/oellm-eval#126](https://github.com/OpenEuroLLM/oellm-eval/issues/126): Integrate packaged JudgeArena tasks? | 0 | True | True | True |
| [github:OpenEuroLLM/oellm-autoexp#10](https://github.com/OpenEuroLLM/oellm-autoexp/issues/10): Make a proper error message when path to config file is wrong? | 0 | True | True | True |
| [github:OpenEuroLLM/oellm-autoexp#43](https://github.com/OpenEuroLLM/oellm-autoexp/issues/43): Progress tracker tool? | 0 | True | True | True |
| [github:OpenEuroLLM/Taskboard#405](https://github.com/OpenEuroLLM/Taskboard/issues/405): Add safety and fairness benchmarks? | 1 | True | True | True |
| [github:OpenEuroLLM/Taskboard#337](https://github.com/OpenEuroLLM/Taskboard/issues/337): Integrate JudgeArena into oellm-eval? | 1 | True | True | False |
| [github:OpenEuroLLM/Taskboard#131](https://github.com/OpenEuroLLM/Taskboard/issues/131): LUMI: Create a container which has working kernels when using bias? | 1 | True | True | True |
| [github:OpenEuroLLM/Taskboard#50](https://github.com/OpenEuroLLM/Taskboard/issues/50): Evaluate new models? | 1 | False | False | True |
| [github:OpenEuroLLM/Taskboard#384](https://github.com/OpenEuroLLM/Taskboard/issues/384): Benchmark Qwen3.5-9B Base and post-trained Qwen3.5-9B on BFCL V4 non-Web? | 1 | True | True | True |
| [github:OpenEuroLLM/oellm-eval#2](https://github.com/OpenEuroLLM/oellm-eval/pull/2): feat: adding multi-cluster eval functionality? | 1 | True | True | True |
| [github:OpenEuroLLM/oellm-eval#37](https://github.com/OpenEuroLLM/oellm-eval/pull/37): feat: add --venv_path option for running without containers? | 1 | False | False | True |
| [github:OpenEuroLLM/oellm-eval#135](https://github.com/OpenEuroLLM/oellm-eval/pull/135): Fix model args in models, fixes #132.? | 1 | True | True | True |
| [github:OpenEuroLLM/oellm-eval#143](https://github.com/OpenEuroLLM/oellm-eval/pull/143): Replace the CSV file format with TSV.? | 2 | True | True | True |
| [github:OpenEuroLLM/oellm-autoexp#69](https://github.com/OpenEuroLLM/oellm-autoexp/issues/69): `monitor_autoexp.py --session <id>` crashes with `TypeError` when `--session-dir` isn't given? | 1 | True | True | False |

## Interpretation

Primary outcomes are source top-1 accuracy and exact answer-set accuracy, not model-generated answer quality. Correct abstention requires identifying the correct source and returning no indexed links. Source-body SHA256 and retrieved IDs are in the JSON audit. Source failures are not counted as zero and never overwrite the last complete report.
A useful next experiment needs independently authored, genuinely unseen researcher questions and an end-to-end tool-using agent evaluated with source-grounded answer judgments.
