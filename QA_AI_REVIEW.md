# AI-assisted research answer trial — 8 November 2026

**Method:** An AI assistant (ChatGPT) answered four source-grounded questions from the public OpenEuroLLM graph. The deterministic `qa_probe.py` independently checks that each referenced path exists in the graph and produces [`results/QA_EVIDENCE.md`](results/QA_EVIDENCE.md). This document records a **one-time AI answer trial**, not unattended inference in GitHub Actions, a blinded benchmark, or an independent scientific verification.

## 1. OpenThoughts experiment

**Question:** Which task and Hugging Face dataset both cite the OpenThoughts paper? Does that establish use of the dataset?

**Answer:** [Taskboard #321](https://github.com/OpenEuroLLM/Taskboard/issues/321) proposes reproducing OpenThinker3-7B results using 31.6k samples. The [OpenThoughts3-1.2M dataset](https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M) and the task both cite [OpenThoughts: Data Recipes for Reasoning Models](https://arxiv.org/abs/2506.04178) (arXiv `2506.04178`). **That does not establish that the task used this specific Hugging Face dataset**; it establishes a shared publication reference.

**Assessment:** A useful cross-platform discovery, supported as a *citation link* only.

## 2. Annealing mixtures and FineMath

**Question:** Is FineMath proven to be part of OpenEuroLLM's automated annealing mixtures?

**Answer:** [Taskboard #56](https://github.com/OpenEuroLLM/Taskboard/issues/56) discusses testing high-quality annealing data mixtures and refers to the [SmolLM2 paper](https://arxiv.org/abs/2502.02737) (arXiv `2502.02737`). The [FineMath dataset](https://huggingface.co/datasets/HuggingFaceTB/finemath) cites the same paper. **There is no direct evidence in this graph that FineMath was included in the task's mixtures.** A shared citation is a lead for investigation, not a reproducibility claim.

**Assessment:** Correctly refuses to promote shared citation to dataset usage.

## 3. HellaSwag evaluation and OLMo 3

**Question:** What connects the multilingual HellaSwag PR to OLMo 3 artifacts?

**Answer:** [oellm-eval PR #156](https://github.com/OpenEuroLLM/oellm-eval/pull/156) changes the multilingual HellaSwag few-shot setting to 10 and cites the [OLMo 3 paper](https://arxiv.org/abs/2512.13961) (arXiv `2512.13961`). The [OpenEuroLLM OLMo-3-7B-Think-SFT model](https://huggingface.co/openeurollm/OLMo-3-7B-Think-SFT) also cites that paper. **The graph does not prove this PR evaluated that particular model** or that the paper's methods were reproduced.

**Assessment:** Precise issue-to-paper-to-model discovery, with scope limits.

## 4. Inaccessible HPLT dataset

**Question:** Can the graph verify that `HPLT/HPLT4.0` was used to train the OpenEuroLLM datamix model?

**Answer:** The [datamix-0.7b-hplt-3.0-eng-cc-100bt model card](https://huggingface.co/openeurollm/datamix-0.7b-hplt-3.0-eng-cc-100bt) declares `HPLT/HPLT4.0` as a dataset. The public [Hugging Face target](https://huggingface.co/datasets/HPLT/HPLT4.0) returned HTTP 401 during the probe. **We can confirm the declaration, but cannot independently verify the target's contents or actual training usage.** HTTP 401 does not show that the dataset does not exist.

**Assessment:** Appropriate evidence-limited answer and explicit uncertainty.

## Outcome and limitations

The four AI-generated responses stayed within the available citation/declaration evidence and included source links. The automated evidence contract passed **4/4 cases** against the November 8 snapshot. This is a small, selected demonstration: it does **not** measure precision, recall, hallucination rate across unseen questions or autonomous agent reliability.

The practical result is that the graph can supply an agent with *auditable evidence packets*. A repeatable end-to-end LLM evaluation will require a supported inference provider and explicit model credentials/budget; GitHub Actions currently performs deterministic evidence checks only. The agent project Nexus remains separate.
