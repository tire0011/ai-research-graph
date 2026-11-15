# Historical replay H2023 — frozen pre-2024 evidence and hypothesis seeds

**Created:** 2026-11-15 (retrospective, NOT a time-blind forecast)
**Cutoff:** sources demonstrably published no later than **2023-12-31**.
**Research question:** Can evidence-grounded cross-disciplinary reasoning recover subsequent research questions about useful transfer and forgetting in multilingual language models?

## Strict caveat: model knowledge leakage

This assistant was trained after the cutoff and already knew or encountered later work. In particular, the 2024 publication *Multilingual Instruction Tuning With Just a Pinch of Multilinguality* appeared in an initial mixed-date search **before this protocol was committed**. Therefore these proposals are **contaminated retrospective hypothesis reconstruction**, not time-blind scientific predictions. The 2024 paper must **not** count as evidence of genuine prospective forecasting, even if it later appears to match a prediction.

This repository document locks what we can evaluate *methodologically*: whether ideas have precise provenance, explicit countertests, correct prior-art interpretation and useful research decisions. A true forecasting benchmark requires archived model training cutoff, time-locked external researchers, or contamination controls not provided here.

## Eligible source set (published by the cutoff)

1. Muennighoff et al. (ACL 2023), [*Crosslingual Generalization through Multitask Finetuning*](https://aclanthology.org/2023.acl-long.891/). Result reported: English multitask tuning of a pretrained multilingual model can improve tasks in other languages; multilingual tasks and translated prompts produce different transfer patterns. **Evidence:** benchmark experiments with BLOOMZ/mT0; not proof that tiny amounts of multilingual tuning always suffice.
2. Choenni, Garrette & Shutova (EMNLP 2023), [*How do languages influence each other? Studying cross-lingual data sharing during LM fine-tuning*](https://aclanthology.org/2023.emnlp-main.818/). Reported: training examples in other languages can reinforce or complement learning, with influence increasing during fine-tuning; uses TracIn on multilingual masked LMs, **not** a causal proof for decoder-only LLMs.
3. Winata et al. (Findings ACL 2023), [*Overcoming Catastrophic Forgetting in Massively Multilingual Continual Learning*](https://aclanthology.org/2023.findings-acl.48/). Reported: sequential updates can forget prior languages; adjusting the learning rate can limit forgetting. **Context:** up to 51 languages, classification/sequence labeling; not direct evidence for modern instruction SFT.
4. Badola, Dave & Talukdar (Findings ACL 2023), [*Parameter-Efficient Finetuning for Robust Continual Multilingual Learning*](https://aclanthology.org/2023.findings-acl.619/). Reported: languages absent from an update can regress; a parameter-efficient method using linguistic relatedness can improve retention. **Context:** continual multilingual learning, not proof of a universally optimal language mixture.

All four are legitimate pre-cutoff works; exact publication metadata and primary paper URLs are given. These are summarized findings, not copied article text.

## Frozen hypothesis seeds (do not edit after later-outcome inspection)

### H23-01 — A small language-diversity dose may carry disproportionate value

**Prompted by:** multilingual task transfer in Muennighoff 2023, data complementation in Choenni 2023.

**Mechanistic proposal:** In a pretrained multilingual model, some instruction-following ability transfers at the task level. A small set of diverse, high-quality non-English instructions may act as a *transfer trigger* rather than requiring proportional training data for every language.

**Prediction to test:** With equal total instruction samples and matched tasks, an English-majority mixture containing **at most 1%** instructions drawn from **2–4 other languages** improves mean held-out non-English instruction-following performance over a pure-English mixture. English quality should be reported separately and should not lose more than **2 percentage points** on the chosen matched benchmark. Results are model- and prompt-dependent.

**Falsification:** no held-out language gain, or measurable English degradation beyond threshold; effect disappears in matched instruction-format and data-quality controls. **Caveat:** the chosen 1%/2–4 threshold may be hindsight-contaminated; pre-2024 proof is not claimed.

### H23-02 — Training-data *identity* matters for forgetting, beyond language ratio

**Prompted by:** Winata 2023 continual forgetting; Muennighoff 2023 prompt-language tradeoffs.

**Mechanistic proposal:** Forgetting can depend on the previously learned task/data distribution, not only the numerical English-vs-other-language share.

**Prediction to test:** At equal total tokens, fixed English/non-English share, matched English task categories and compute, a replay subset from the *original prior English SFT distribution* retains English benchmark quality better than new English examples from a different source. Compare the same multilingual training set in both arms.

**Falsification:** source identity has no effect after controlling data quality, task distribution and replay exposure, or a simple learning-rate schedule yields equal retention. **Caveat:** related continual-learning mitigations already existed in 2023. This is not presumed novel.

### H23-03 — Mechanistic transfer signals should predict *functional* transfer

**Prompted by:** Choenni 2023 data attribution and Badola 2023 linguistic regularities.

**Mechanistic proposal:** A measure of cross-language **influence on held-out predictions** will predict changes in functional task quality more accurately than superficial script similarity or uncalibrated vector proximity alone.

**Prediction to test:** Prespecify a cheap cross-language influence statistic on a small multilingual model at an early checkpoint. On held-out tasks and languages, it predicts the *direction* of later zero-shot performance change better than a same-compute baseline based only on script, family and static representation similarity. Use multiple language pairs and out-of-sample evaluation.

**Falsification:** no measurable held-out prediction advantage, or correlation vanishes under matched token-exposure/task-type controls. Distinguish observational prediction from causal intervention.

**Caveat:** this is a 2026-formulated hypothesis seed informed by older papers, not evidence that a scientist in 2023 would have proposed this exact statistic.

## Baseline and outcome-review contract

1. Time-lock this hypothesis set and its sources **before** opening further 2024–2026 papers (except the 2024 contamination already declared).
2. Later studies are admissible **only to evaluate** these fixed hypotheses; keep their URLs and study methods separate from the 2023 evidence.
3. For each prediction, assess exact variables, controls, language coverage, model type, benchmark comparability and independent reproduction. Use `supported_under_conditions`, `contradicted`, `already_known_pre_cutoff`, `not_tested`, or `inconclusive`.
4. Record missing or negative evidence and distinguish a published claim from replication.
5. Compare a plain-source reasoning path against a graph-structured reasoning path using identical pre-cutoff sources; no advantage can be claimed when the candidate ideas were written by the same contaminated modern model.
6. If this attempt yields only rediscovery of prior art, preserve it as a **negative lesson** and refine the system to identify more useful, falsifiable unanswered questions.

**No new model training, experimental results or genuine post-2023 predictions are claimed.**
