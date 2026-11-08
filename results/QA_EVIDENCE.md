# Research question evidence probe

This is **source verification**, not an automated LLM response. The listed evidence is the minimal context an AI agent could receive; a language model must still be evaluated separately.

Graph snapshot: `2026-11-08T21:30:14.918186+00:00` UTC. Passed: **4/4** evidence checks.

## openthoughts_bridge

**Question:** Which OpenEuroLLM task and Hugging Face dataset both cite the OpenThoughts paper? Does this prove the task used that dataset?

**Evidence check:** PASS

Evidence classification: `shared_paper_citation`; arXiv `2506.04178`.

- github_task: [Reproduce OpenThinker3-7B (on 31.6k samples)](https://github.com/OpenEuroLLM/Taskboard/issues/321)
- publication: [OpenThoughts: Data Recipes for Reasoning Models](https://arxiv.org/abs/2506.04178)
- hf_artifact: [open-thoughts/OpenThoughts3-1.2M](https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M)

**Limit:** The sources cite the same publication. No direct dataset usage, evaluation, or causal dependency is proven.

## smollm2_bridge

**Question:** Is FineMath proven to be part of OpenEuroLLM's automated annealing mixtures, or do the task and dataset only cite the same paper?

**Evidence check:** PASS

Evidence classification: `shared_paper_citation`; arXiv `2502.02737`.

- github_task: [automated dataset mixtures for annealing](https://github.com/OpenEuroLLM/Taskboard/issues/56)
- publication: [SmolLM2: When Smol Goes Big -- Data-Centric Training of a Small Language Model](https://arxiv.org/abs/2502.02737)
- hf_artifact: [HuggingFaceTB/finemath](https://huggingface.co/datasets/HuggingFaceTB/finemath)

**Limit:** The sources cite the same publication. No direct dataset usage, evaluation, or causal dependency is proven.

## olmo3_bridge

**Question:** What links the multilingual HellaSwag PR to OLMo 3 artifacts, and what is NOT established by that link?

**Evidence check:** PASS

Evidence classification: `shared_paper_citation`; arXiv `2512.13961`.

- github_task: [Set n_shots: [10] for multilingual HellaSwag to align with original](https://github.com/OpenEuroLLM/oellm-eval/pull/156)
- publication: [Olmo 3](https://arxiv.org/abs/2512.13961)
- hf_artifact: [openeurollm/OLMo-3-7B-Think-SFT](https://huggingface.co/openeurollm/OLMo-3-7B-Think-SFT)

**Limit:** The sources cite the same publication. No direct dataset usage, evaluation, or causal dependency is proven.

## hplt_unverified

**Question:** Can we verify that HPLT/HPLT4.0 was used to train openeurollm/datamix-0.7b-hplt-3.0-eng-cc-100bt?

**Evidence check:** PASS

Evidence classification: `unverified_publisher_declaration`.

- publisher_model_card: [openeurollm/datamix-0.7b-hplt-3.0-eng-cc-100bt](https://huggingface.co/openeurollm/datamix-0.7b-hplt-3.0-eng-cc-100bt)
- unverified_target: [HPLT/HPLT4.0](https://huggingface.co/datasets/HPLT/HPLT4.0)

**Limit:** The model card declares this resource, but the Hub lookup is inaccessible; use cannot be independently confirmed.
