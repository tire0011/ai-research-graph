# Ten new OpenEuroLLM research questions: source-grounded holdout

Snapshot: `2026-11-08T13:36:27.015055+00:00` UTC. Live original issues fetched: **10/10**.
Issue bodies identical to the snapshot, at the **same update timestamp**: **10/10**.
Questions supported by the graph's retained source phrases: **10/10**.
Issues with any cross-platform evidence edge: **0/10**; issues with internal `#issue` references in text: **2/10**.
Issues with resolved, in-snapshot GitHub task-reference edges: **2/10** (2 distinct edges).

| Original issue and question | Source body vs graph | Sourced external links | Internal task links |
| --- | --- | ---: | ---: |
| [OpenEuroLLM/Taskboard#420](https://github.com/OpenEuroLLM/Taskboard/issues/420): Which two document categories must the planned PDF benchmark cover, and should computation cost be included? | `exact_source_parity` | 0 | 0 |
| [OpenEuroLLM/Taskboard#435](https://github.com/OpenEuroLLM/Taskboard/issues/435): What example language mixture is proposed for Prelude DPO? Is it a completed experiment? | `exact_source_parity` | 0 | 0 |
| [OpenEuroLLM/Taskboard#434](https://github.com/OpenEuroLLM/Taskboard/issues/434): How many checkpoint averages across how many models does this issue report? Are their scores independently reproduced? | `exact_source_parity` | 0 | 0 |
| [OpenEuroLLM/Taskboard#431](https://github.com/OpenEuroLLM/Taskboard/issues/431): Which DPO variants are planned for the same learning-rate/beta grid? | `exact_source_parity` | 0 | 1 |
| [OpenEuroLLM/oellm-eval#165](https://github.com/OpenEuroLLM/oellm-eval/issues/165): Which evaluation backend lacked the sample-logging flag? | `exact_source_parity` | 0 | 0 |
| [OpenEuroLLM/oellm-eval#45](https://github.com/OpenEuroLLM/oellm-eval/issues/45): What container-build cost reduction was proposed? | `exact_source_parity` | 0 | 0 |
| [OpenEuroLLM/oellm-eval#166](https://github.com/OpenEuroLLM/oellm-eval/issues/166): Which two settings are needed for code-execution evaluation tasks in this issue? | `exact_source_parity` | 0 | 1 |
| [OpenEuroLLM/oellm-eval#96](https://github.com/OpenEuroLLM/oellm-eval/issues/96): What AMD-GPU environment variable was suggested for the LUMI CPU fallback? Was it proven to fix the problem? | `exact_source_parity` | 0 | 0 |
| [OpenEuroLLM/oellm-autoexp#6](https://github.com/OpenEuroLLM/oellm-autoexp/issues/6): Which configuration directory held bind mounts that were missing at launch? | `exact_source_parity` | 0 | 0 |
| [OpenEuroLLM/oellm-autoexp#5](https://github.com/OpenEuroLLM/oellm-autoexp/issues/5): Why did generic setup instructions not cover the LUMI cluster? | `exact_source_parity` | 0 | 0 |

## Short, original-source-grounded answers

- **pdf_ocr_benchmark** (`planned`): Digitally born and scanned documents, with computational costs considered. [Original issue](https://github.com/OpenEuroLLM/Taskboard/issues/420). Internal issue numbers in its body: none. Resolved graph task targets: none.
- **dpo_mixture** (`proposal`): 75% English and 25% multilingual is an illustrative proposal, not a demonstrated optimal mix. [Original issue](https://github.com/OpenEuroLLM/Taskboard/issues/435). Internal issue numbers in its body: none. Resolved graph task targets: none.
- **dpo_checkpoint_merges** (`reported_not_reproduced`): The issue reports 282 averages across four models; the issue text alone does not independently reproduce their scores. [Original issue](https://github.com/OpenEuroLLM/Taskboard/issues/434). Internal issue numbers in its body: none. Resolved graph task targets: none.
- **dpo_variants** (`planned`): APO, IPO and length-normalized DPO are planned for comparison against vanilla DPO. [Original issue](https://github.com/OpenEuroLLM/Taskboard/issues/431). Internal issue numbers in its body: 214. Resolved graph task targets: github:OpenEuroLLM/Taskboard#214.
- **evalchemy_samples** (`reported`): The issue says Evalchemy lacked native sample-logging support, unlike lm-eval-harness. [Original issue](https://github.com/OpenEuroLLM/oellm-eval/issues/165). Internal issue numbers in its body: none. Resolved graph task targets: none.
- **pr_container_build** (`proposal`): Avoid building every container for every pull request; cluster-based builds were described as a later step. [Original issue](https://github.com/OpenEuroLLM/oellm-eval/issues/45). Internal issue numbers in its body: none. Resolved graph task targets: none.
- **contamination_exclusion** (`reported`): The issue specifies --confirm_run_unsafe_code and HF_ALLOW_CODE_EVAL=1. [Original issue](https://github.com/OpenEuroLLM/oellm-eval/issues/166). Internal issue numbers in its body: 159. Resolved graph task targets: github:OpenEuroLLM/oellm-eval#159.
- **lumi_cpu_fallback** (`hypothesis`): HIP_VISIBLE_DEVICES was proposed for AMD GPU visibility; the issue presents this as a potential fix, not a proven root cause. [Original issue](https://github.com/OpenEuroLLM/oellm-eval/issues/96). Internal issue numbers in its body: none. Resolved graph task targets: none.
- **singularity_binds** (`reported`): The issue points to config/container and shows a singularity exec command without visible bind arguments. [Original issue](https://github.com/OpenEuroLLM/oellm-autoexp/issues/6). Internal issue numbers in its body: none. Resolved graph task targets: none.
- **lumi_setup** (`reported`): The issue attributes the gap to differences between LUMI and other clusters. [Original issue](https://github.com/OpenEuroLLM/oellm-autoexp/issues/5). Internal issue numbers in its body: none. Resolved graph task targets: none.

## Meaning and limitations

The ten issue IDs were sampled with a fixed deterministic rule **before** inspecting their bodies. Questions and short answers were annotated afterward and are not blinded or independently judged.
The checks verify exact source text and required supporting phrases; they do NOT test autonomous language-model answers, scientific truth, or human research time. The GitHub API is a live source lookup, whereas the graph is a precomputed snapshot: network latency is not comparable to in-memory lookup latency.
A missing cross-platform edge is a graph coverage gap, not evidence that no real-world relationship exists. Hypotheses and proposed training mixes are not established results.
An internal GitHub issue/PR cross-reference proves only that its source text mentions an indexed task. It does not prove a dependency, that a PR was merged, or that a finding was reproduced.
Source-body SHA256, update times, question annotations and graph link targets are retained in the JSON evidence.
