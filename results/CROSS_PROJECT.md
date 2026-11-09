# European AI cross-project overlap — exploratory pilot

**Read-only and review-only.** Shared topics are not proof of duplicate work or wasted effort.

Audited **9** public repositories, **6** curated cross-organization pairs.

## Documented cooperation (editorial source references)

These official reports are curated context; the automated audit does not revalidate their web content.

- **OpenEuroLLM ↔ LAION:** MixtureVitae training-data co-development, reported by OpenEuroLLM. [Original public source](https://openeurollm.eu/blog/first-year-progress-and-next-steps).
- **OpenEuroLLM ↔ HPLT:** Shared multilingual reference-model work, reported by OpenEuroLLM. [Original public source](https://openeurollm.eu/blog/first-year-progress-and-next-steps).
- **OpenEuroLLM ↔ EuroLLM:** Collaboration on multilingual synthetic data, reported by OpenEuroLLM. [Original public source](https://openeurollm.eu/blog/first-year-progress-and-next-steps).

## Repo-to-repo comparisons

### LLM evaluation: [OpenEuroLLM/oellm-eval](https://github.com/OpenEuroLLM/oellm-eval/blob/main/README.md) ↔ [utter-project/eurollm-evaluation](https://github.com/utter-project/eurollm-evaluation/blob/main/README.md)

- Status: **shared_topic_terms**; duplicate work: **NOT established**.
- What to investigate: Do they share benchmark implementations, datasets or scripts? Different scale and HPC requirements may justify both.
- Last repository push: OpenEuroLLM/oellm-eval 2026-11-04T13:24:00Z; utter-project/eurollm-evaluation 2025-03-17T20:49:57Z.
- Shared text `evaluation`: [A](https://github.com/OpenEuroLLM/oellm-eval/blob/main/README.md) (`# OpenEuroLLM Eval (oellm-eval) A lightweight CLI for scheduling LLM evaluations across multiple HPC clusters using SLURM job arrays and Singularity`, SHA256 `a8f7a28ac5bad0f3c529b16b9f35d4304393a6d2ee86dc0ffeffada62eb2b6ab`); [B](https://github.com/utter-project/eurollm-evaluation/blob/main/README.md) (`# EuroLLM Evaluation ## European LLM Leaderboard Leaderboard details: https://huggingfa`, SHA256 `07d621a528c7eab8664f0440d16ad8dcb863cce0239e22ae79e9703176084bf1`).
- Shared text `lm-eval`: [A](https://github.com/OpenEuroLLM/oellm-eval/blob/main/README.md) (`# OpenEuroLLM Eval (oellm-eval) A lightweight CLI for scheduling LLM evaluations across multiple HP`, SHA256 `a8f7a28ac5bad0f3c529b16b9f35d4304393a6d2ee86dc0ffeffada62eb2b6ab`); [B](https://github.com/utter-project/eurollm-evaluation/blob/main/README.md) (`board ### Installation '''bash git clone https://github.com/OpenGPTX/lm-evaluation-harness.git cd lm-evaluation-harness git checkout 43468b998f0cc`, SHA256 `07d621a528c7eab8664f0440d16ad8dcb863cce0239e22ae79e9703176084bf1`).
- Required next check: Human must inspect current issues, code paths, licences and already shared dependencies before claiming redundancy.

### WARC text extraction: [OpenEuroLLM/web-data-processing](https://github.com/OpenEuroLLM/web-data-processing/blob/main/README.md) ↔ [hplt-project/HPLT-textpipes](https://github.com/hplt-project/HPLT-textpipes/blob/main/README.md)

- Status: **shared_topic_terms**; duplicate work: **NOT established**.
- What to investigate: Are data cleaning, text extraction stages or intermediate formats reusable across both pipelines?
- Last repository push: OpenEuroLLM/web-data-processing 2026-11-09T13:57:56Z; hplt-project/HPLT-textpipes 2026-10-06T15:53:03Z.
- Shared text `metadata extraction`: [A](https://github.com/OpenEuroLLM/web-data-processing/blob/main/README.md) (`# web-data-processing Pipeline for text and metadata extraction from different web data archives ## Source crawls - [Helper scripts`, SHA256 `58ff077370c15c428764455b928361d6e99769d54fc078881696084e8005bdeb`); [B](https://github.com/hplt-project/HPLT-textpipes/blob/main/README.md) (`tPipes This repository contains code and description of how text and metadata extraction for [HPLT v4 datasets](https://hplt-project.org/datasets/v4.0) was do`, SHA256 `67f2d993cc43fb88b5986642691cc6bb34bd3d652e09ac32052917924229d013`).
- Shared text `text and metadata extraction`: [A](https://github.com/OpenEuroLLM/web-data-processing/blob/main/README.md) (`# web-data-processing Pipeline for text and metadata extraction from different web data archives ## Source crawls - [Helper scripts`, SHA256 `58ff077370c15c428764455b928361d6e99769d54fc078881696084e8005bdeb`); [B](https://github.com/hplt-project/HPLT-textpipes/blob/main/README.md) (`HPLT TextPipes This repository contains code and description of how text and metadata extraction for [HPLT v4 datasets](https://hplt-project.org/datasets/v4.0) was do`, SHA256 `67f2d993cc43fb88b5986642691cc6bb34bd3d652e09ac32052917924229d013`).
- Shared text `pipeline`: [A](https://github.com/OpenEuroLLM/web-data-processing/blob/main/README.md) (`# web-data-processing Pipeline for text and metadata extraction from different web data archives ##`, SHA256 `58ff077370c15c428764455b928361d6e99769d54fc078881696084e8005bdeb`); [B](https://github.com/hplt-project/HPLT-textpipes/blob/main/README.md) (`logged. Text is extracted from such resources by the text extraction pipeline described below. Two sources of web crawls are employed: Common Craw`, SHA256 `67f2d993cc43fb88b5986642691cc6bb34bd3d652e09ac32052917924229d013`).
- Required next check: Human must inspect current issues, code paths, licences and already shared dependencies before claiming redundancy.

### Web-archive processing: [OpenEuroLLM/web-data-processing](https://github.com/OpenEuroLLM/web-data-processing/blob/main/README.md) ↔ [hplt-project/warc2text-runner](https://github.com/hplt-project/warc2text-runner/blob/main/README.md)

- Status: **shared_topic_terms**; duplicate work: **NOT established**.
- What to investigate: Compare parallel WARC ingestion and extraction before building similar tools.
- Last repository push: OpenEuroLLM/web-data-processing 2026-11-09T13:57:56Z; hplt-project/warc2text-runner 2026-01-31T00:07:41Z.
- Shared text `extraction`: [A](https://github.com/OpenEuroLLM/web-data-processing/blob/main/README.md) (`# web-data-processing Pipeline for text and metadata extraction from different web data archives ## Source crawls - [Helper scripts`, SHA256 `58ff077370c15c428764455b928361d6e99769d54fc078881696084e8005bdeb`); [B](https://github.com/hplt-project/warc2text-runner/blob/main/README.md) (`# warc2text-runner NB! For the latest version of the HPLT text extraction pipelines used for HPLT v4 please refer to the [HPLT-textpipes repos`, SHA256 `f200179a4c67b2198e3ac0d707b8a3c852a18250871ba83e82c7568fdab218bf`).
- Shared text `text`: [A](https://github.com/OpenEuroLLM/web-data-processing/blob/main/README.md) (`# web-data-processing Pipeline for text and metadata extraction from different web data archives ## Source c`, SHA256 `58ff077370c15c428764455b928361d6e99769d54fc078881696084e8005bdeb`); [B](https://github.com/hplt-project/warc2text-runner/blob/main/README.md) (`# warc2text-runner NB! For the latest version of the HPLT text extraction pipelin`, SHA256 `f200179a4c67b2198e3ac0d707b8a3c852a18250871ba83e82c7568fdab218bf`).
- Required next check: Human must inspect current issues, code paths, licences and already shared dependencies before claiming redundancy.

### LLM scaling baselines: [OpenEuroLLM/dense_english_scaling_laws](https://github.com/OpenEuroLLM/dense_english_scaling_laws/blob/main/README.md) ↔ [LAION-AI/open-sci-ref-0.01](https://github.com/LAION-AI/open-sci-ref-0.01/blob/main/README.md)

- Status: **shared_topic_terms**; duplicate work: **NOT established**.
- What to investigate: Can published reference checkpoints and loss curves be reused rather than reproduced?
- Last repository push: OpenEuroLLM/dense_english_scaling_laws 2026-08-28T13:08:55Z; LAION-AI/open-sci-ref-0.01 2026-02-13T13:06:34Z.
- Shared text `scaling`: [A](https://github.com/OpenEuroLLM/dense_english_scaling_laws/blob/main/README.md) (`# OELLM Dense English Scaling Laws 🇪🇺🤖📈 This project contains the **data and analysis scripts** us`, SHA256 `b07fbd810d9e5eb4f1aa9c0cd0bf8dfc379cc2309687d77137e464a91bf30e8e`); [B](https://github.com/LAION-AI/open-sci-ref-0.01/blob/main/README.md) (`are released under permissive Apache 2.0 licence. <img src="figures/ScalingCompute.svg" alt="ScalingCompute" width="700" /> See the [Open-sci-re`, SHA256 `bafd88a1ed4d10f8b9e352e94c27c1797fd966fa1a9d963bf940b59d2288142a`).
- Shared text `model`: [A](https://github.com/OpenEuroLLM/dense_english_scaling_laws/blob/main/README.md) (`s** used to study scaling laws for dense English-language transformer models. The corresponding collection of checkpoints is available in the 🤗`, SHA256 `b07fbd810d9e5eb4f1aa9c0cd0bf8dfc379cc2309687d77137e464a91bf30e8e`); [B](https://github.com/LAION-AI/open-sci-ref-0.01/blob/main/README.md) (`509.09009</a></h4> Open-sci-ref 0.01 is a research dense transformer model family that includes all the intermediate checkpoints trained on 8 di`, SHA256 `bafd88a1ed4d10f8b9e352e94c27c1797fd966fa1a9d963bf940b59d2288142a`).
- Shared text `dataset`: [A](https://github.com/OpenEuroLLM/dense_english_scaling_laws/blob/main/README.md) (`how **hyperparameters and model performance scale** with model size, dataset size, and compute, with a particular focus on learning rate and batch`, SHA256 `b07fbd810d9e5eb4f1aa9c0cd0bf8dfc379cc2309687d77137e464a91bf30e8e`); [B](https://github.com/LAION-AI/open-sci-ref-0.01/blob/main/README.md) (`ll the intermediate checkpoints trained on 8 different reference open datasets (C4, Pile, SlimPajama, FineWeb-Edu-1.4T (v1.0.0), DCLM-baseline, Nem`, SHA256 `bafd88a1ed4d10f8b9e352e94c27c1797fd966fa1a9d963bf940b59d2288142a`).
- Required next check: Human must inspect current issues, code paths, licences and already shared dependencies before claiming redundancy.

### Evaluation tools across modalities: [OpenEuroLLM/oellm-eval](https://github.com/OpenEuroLLM/oellm-eval/blob/main/README.md) ↔ [LAION-AI/CLIP_benchmark](https://github.com/LAION-AI/CLIP_benchmark/blob/main/README.md)

- Status: **shared_topic_terms**; duplicate work: **NOT established**.
- What to investigate: Check modality and task differences before comparing implementations; shared generic terms do not establish duplicate work.
- Last repository push: OpenEuroLLM/oellm-eval 2026-11-04T13:24:00Z; LAION-AI/CLIP_benchmark 2026-11-05T15:23:52Z.
- Shared text `benchmark`: [A](https://github.com/OpenEuroLLM/oellm-eval/blob/main/README.md) (`gs. Available task groups: - 'crows-pairs' - CrowS-Pairs social bias benchmark (English, 0-shot, 'pct_stereotype') - 'bpb-corpus' - Bits-per-byte on`, SHA256 `a8f7a28ac5bad0f3c529b16b9f35d4304393a6d2ee86dc0ffeffada62eb2b6ab`); [B](https://github.com/LAION-AI/CLIP_benchmark/blob/main/README.md) (`# CLIP Benchmark [![pypi](https://img.shields.io/pypi/v/clip_benchmark.svg)](https://p`, SHA256 `a484cfa42d08749beda9957a70fc60373c22b2a7d3488b7c6fb98f3ed12907dc`).
- Shared text `evaluation`: [A](https://github.com/OpenEuroLLM/oellm-eval/blob/main/README.md) (`# OpenEuroLLM Eval (oellm-eval) A lightweight CLI for scheduling LLM evaluations across multiple HPC clusters using SLURM job arrays and Singularity`, SHA256 `a8f7a28ac5bad0f3c529b16b9f35d4304393a6d2ee86dc0ffeffada62eb2b6ab`); [B](https://github.com/LAION-AI/CLIP_benchmark/blob/main/README.md) (`del to use, the dataset and the task to evaluate on. Once it is done, evaluation is performed and the results are written into a JSON file. ### Using`, SHA256 `a484cfa42d08749beda9957a70fc60373c22b2a7d3488b7c6fb98f3ed12907dc`).
- Shared text `model`: [A](https://github.com/OpenEuroLLM/oellm-eval/blob/main/README.md) (`rity containers. ## Features - **Schedule evaluations** on multiple models and tasks: 'oellm-eval schedule' - **Collect results** and check for`, SHA256 `a8f7a28ac5bad0f3c529b16b9f35d4304393a6d2ee86dc0ffeffada62eb2b6ab`); [B](https://github.com/LAION-AI/CLIP_benchmark/blob/main/README.md) (`/pypi/clip_benchmark) The goal of this repo is to evaluate CLIP-like models on a standard set of datasets on different tasks such as zero-shot c`, SHA256 `a484cfa42d08749beda9957a70fc60373c22b2a7d3488b7c6fb98f3ed12907dc`).
- Required next check: Human must inspect current issues, code paths, licences and already shared dependencies before claiming redundancy.

### Dataset processing vs cataloguing: [OpenEuroLLM/training-data-catalogue](https://github.com/OpenEuroLLM/training-data-catalogue/blob/main/README.md) ↔ [hplt-project/HPLT-textpipes](https://github.com/hplt-project/HPLT-textpipes/blob/main/README.md)

- Status: **shared_topic_terms**; duplicate work: **NOT established**.
- What to investigate: Is there interoperable metadata or a useful reference link, even though a catalogue and extraction pipeline serve different purposes?
- Last repository push: OpenEuroLLM/training-data-catalogue 2026-10-25T14:45:46Z; hplt-project/HPLT-textpipes 2026-10-06T15:53:03Z.
- Shared text `dataset`: [A](https://github.com/OpenEuroLLM/training-data-catalogue/blob/main/README.md) (`for LLM development. This page aims to offer navigational help in the dataset landscape, essentially providing a structured ‘catalogue’ of availabl`, SHA256 `34d3d2d756c42691be20af5e1b9884034b5b2a977b29eb8ee34f2306ae4faaf5`); [B](https://github.com/hplt-project/HPLT-textpipes/blob/main/README.md) (`code and description of how text and metadata extraction for [HPLT v4 datasets](https://hplt-project.org/datasets/v4.0) was done. ## Install on L`, SHA256 `67f2d993cc43fb88b5986642691cc6bb34bd3d652e09ac32052917924229d013`).
- Shared text `metadata`: [A](https://github.com/OpenEuroLLM/training-data-catalogue/blob/main/README.md) (`s encoded as a JSON object comprising the document text and available metadata (as defined by each distinct resource), and each JSON object is seria`, SHA256 `34d3d2d756c42691be20af5e1b9884034b5b2a977b29eb8ee34f2306ae4faaf5`); [B](https://github.com/hplt-project/HPLT-textpipes/blob/main/README.md) (`tPipes This repository contains code and description of how text and metadata extraction for [HPLT v4 datasets](https://hplt-project.org/datasets/v`, SHA256 `67f2d993cc43fb88b5986642691cc6bb34bd3d652e09ac32052917924229d013`).
- Shared text `data`: [A](https://github.com/OpenEuroLLM/training-data-catalogue/blob/main/README.md) (`# OpenEuroLLM Catalogue of LLM Training Data ## Background There is a bit of a growth industry in (pre-)trainin`, SHA256 `34d3d2d756c42691be20af5e1b9884034b5b2a977b29eb8ee34f2306ae4faaf5`); [B](https://github.com/hplt-project/HPLT-textpipes/blob/main/README.md) (`es This repository contains code and description of how text and metadata extraction for [HPLT v4 datasets](https://hplt-project.org/datasets/v`, SHA256 `67f2d993cc43fb88b5986642691cc6bb34bd3d652e09ac32052917924229d013`).
- Required next check: Human must inspect current issues, code paths, licences and already shared dependencies before claiming redundancy.

## Boundaries

Manually curated bounded pair sample, original README/metadata evidence only. Shared terms, cross-links and editorially documented collaboration are distinct. No code similarity test, no issue-level duplicate verification, no outreach.

No code was compared automatically; even an explicit cross-repo URL only proves that the URL is mentioned in the README. Do not contact project maintainers without separate human approval.
