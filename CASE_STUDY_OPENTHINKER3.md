# Case study: Can public metadata explain OpenEuroLLM's OpenThinker3 reproduction?

**Checked:** 8 November 2026. **Scope:** public GitHub issues and default-branch code, upstream paper/model/dataset descriptions. This is a metadata and reproducibility audit, **not** a training run. Nexus is not involved.

## Short answer

We can reconstruct a meaningful **data preparation path** for OpenThoughts3 within OpenEuroLLM, including a concrete Hugging Face dataset reference, conversion code, SLURM processing configuration and published token counts. **We cannot verify that the separate OpenThinker3 reproduction objective was completed**, or whether its reported benchmark scores match the upstream paper: the [reproduction task](https://github.com/OpenEuroLLM/Taskboard/issues/321) has no public results, run manifest, benchmark table or linked implementation in its body/comments. The task remains open with zero comments as checked.

This case shows why a shared publication citation is only a discovery lead. A repository-wide metadata search found substantially stronger operational links, while also exposing a specific data-processing caveat.

## Source-backed trace

| Question | Public evidence | Assessment |
| --- | --- | --- |
| What is the research target? | [Taskboard #321](https://github.com/OpenEuroLLM/Taskboard/issues/321) asks to reproduce OpenThinker3-7B results with 31.6K samples and compare with the [OpenThoughts paper](https://arxiv.org/abs/2506.04178). | **Goal documented; outcome unverified.** The issue is open, unassigned and has no public comments (checked 2026-11-08). |
| What does 31.6K mean? | The published [OpenThoughts paper](https://openreview.net/pdf?id=7xjoTuaNmN) describes controlled data-recipe ablations using 31,600 samples per strategy and Qwen2.5-7B-Instruct. The upstream project's [full OpenThinker3-7B model](https://github.com/open-thoughts/open-thoughts) is reported as trained on the **1.2M-sample** OpenThoughts3 dataset. | **Important ambiguity:** reproducing 31.6K-sample ablations is not automatically reproducing the full model or its flagship scores. The exact paper experiment/table needs specifying. |
| Is the OpenThoughts3 dataset referenced by OpenEuroLLM code? | [`flag/openthoughts-3/metadata.yaml`](https://github.com/OpenEuroLLM/training-data-collection/blob/main/flag/openthoughts-3/metadata.yaml) explicitly links to [`open-thoughts/OpenThoughts3-1.2M`](https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M) and lists a tokenizer/processing recipe. The dataset also occurs in [`flag/etc/datasets.txt`](https://github.com/OpenEuroLLM/training-data-collection/blob/main/flag/etc/datasets.txt). | **Direct source declaration**, stronger than an indirect shared-paper citation; not by itself proof of training usage. |
| Is there runnable preprocessing code? | [`textify.py`](https://github.com/OpenEuroLLM/training-data-collection/blob/main/flag/openthoughts-3/etc/textify.py) converts compressed conversation records to ChatML text; [`textify.slurm`](https://github.com/OpenEuroLLM/training-data-collection/blob/main/flag/openthoughts-3/etc/textify.slurm) specifies a 120-task shard conversion. The script depends on `qa_to_text`; a related [packer issue comment](https://github.com/OpenEuroLLM/training-data-packer/issues/43#issuecomment-4786904825) links a converter attachment. | **Code and scheduling instructions found.** Their existence does not establish successful execution of that exact version or a reproducible end-to-end training run. |
| Is processing recorded? | The [`flag` collection README](https://github.com/OpenEuroLLM/training-data-collection/blob/main/flag/README.md) records **1,200,000 sequences and 20.20 billion tokens** for `openthoughts-3` in its tokenization table. Its reasoning-dataset row is struck through, and the contamination section says the **decontamination step** failed for `openthoughts-3` and `agenttrove-0.0`. | **Some processing and accounting are documented, but final mixture inclusion is unclear.** The failed step was decontamination; it would be incorrect to say all data processing failed. |
| Was reasoning-data packing tracked? | [training-data-packer #43](https://github.com/OpenEuroLLM/training-data-packer/issues/43) mentions `openthoughts-3`, is closed as completed, and the last comment says management moved to T4.3. | **Adjacent processing activity**; not evidence that Taskboard #321's model/benchmark reproduction succeeded. |
| What are the upstream reference scores? | The [upstream OpenThoughts README](https://github.com/open-thoughts/open-thoughts) reports OpenThinker3-7B benchmark results including **53.3 AIME 2025**, **51.7 LiveCodeBench 06/24–01/25** and **53.7 GPQA-D**, evaluated with Evalchemy. | **Reference values only.** No matching OpenEuroLLM-run scores were identified in the inspected reproduction issue and linked code. |

## Reproduction evidence still needed

The following are **not established for Taskboard #321** by the inspected sources:

1. **Exact experiment variant:** which 31.6K-sample ablation, task domain, filtering method and paper table are intended?
2. **Pinned data:** exact input dataset version, sample IDs/selection method, preprocessing and decontamination decisions.
3. **Training configuration:** base checkpoint/revision, hyperparameters, distributed training code revision, environment and random seeds.
4. **Independent outputs:** training log, final checkpoint, evaluation suite revision, per-task scores, variance across seeds and comparison against the selected paper baseline.
5. **Provenance linking:** a direct reference from #321 to the actual run, commit, model card or evaluation artifact.

Absence of these items **in the inspected public sources** does not demonstrate that internal experiments never happened. It means an independent researcher cannot currently reconstruct or verify the outcome from those sources alone.

## Example of a stronger research record

To make this result genuinely reusable by an AI agent, a public experiment manifest could identify:

| Field | Example of required information | Current status |
| --- | --- | --- |
| Research objective | `OpenEuroLLM/Taskboard#321` and selected paper table | Issue known; table unspecified |
| Data | Dataset revision + exact 31.6K sample manifest | Upstream resource known; sample manifest not found |
| Training | Base model SHA, code commit and complete settings | Not found for this issue |
| Evaluation | Benchmark version, prompts, scoring method, seeds | Upstream tool mentioned; specific reproduction run not found |
| Results | Run ID, logs, output checkpoint, score comparison | Not found for this issue |
| Validation | Independent rerun or reviewer confirmation | Not found for this issue |

The manifest should express relationship **types** explicitly: `cites_paper`, `declares_dataset`, `processes_dataset`, `trained_on`, `evaluated_with`, `produced_checkpoint` and `reproduces_result`. These must not be collapsed into a generic "related" link. Use actual commits, dataset revisions and run artifacts as evidence before assigning the stronger relationship types.

## What this demonstrates about the research graph

- **Useful discovery:** the original three-platform bridge (GitHub task → paper ← Hugging Face dataset) led to related OpenEuroLLM repositories and concrete preprocessing metadata that were absent from our initial issue/model/paper graph.
- **Important negative finding:** one can find a real data-collection pipeline and still **not** have evidence of the separate model reproduction result. This is exactly where an AI assistant should abstain rather than guess.
- **Clear next indexing target:** include relevant source files, data collection manifests, and run/benchmark results from GitHub, with versioned provenance. Code search and explicit dataset URLs carry stronger operational evidence than shared citations.
- **Practical collaboration question:** ask maintainers whether #321 has a public run/benchmark report and which 31.6K paper ablation was targeted. Do not imply the reproduction failed; simply request the missing provenance if a follow-up is desired.

**Bottom line:** The graph helped expose *where to look* and what evidence is missing. It has **not** independently reproduced the scientific result. This distinction is the central lesson for an interoperable research-assistant interface.
