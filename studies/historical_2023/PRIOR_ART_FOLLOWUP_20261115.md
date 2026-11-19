# Additional prior-art check: cross-language transfer and mechanistic signals

**Date:** 2026-11-15
**Extends:** [2023-cutoff hypothesis register](HYPOTHESES.md) and [2024–2026 outcome review](OUTCOME_REVIEW.md)
**Purpose:** Avoid claiming a novel transfer-prediction experiment that has already been studied.

## Near neighbors that change our research plan

1. [ConGrad — Conflicting Gradient Filtering for Multilingual Preference Alignment](https://aclanthology.org/2026.eacl-long.299/) (EACL 2026; [preprint dated 2025](https://arxiv.org/abs/2503.23777)). Its gradient-affinity signal is used to **select preference examples** benefiting multilingual objectives, with experiments on LLaMA3-8B and Gemma2-2B across ten languages. This establishes that cross-language gradient agreement for **training selection** is not a new idea. It does **not**, by itself, establish success at forecasting future functional transfer across model checkpoints.
2. [A Post-trainer's Guide to Multilingual Training Data](https://arxiv.org/abs/2504.16677) (preprint April 2025) examines multilingual transfer under controlled data mixtures and task settings. It reports that no isolated factor explains transfer consistently across all considered post-training configurations. Any proposed simple universal "recipe" needs much stronger evidence.
3. [Ability Transfer Through Language Mixing](https://aclanthology.org/2025.ijcnlp-long.76/) (2025) uses controlled artificial tasks including arithmetic and **graph navigation**, varying vocabulary, grammar and computational requirements. It finds positive transfer and different effects of grammatical vs lexical shifts. Thus even the idea of controlled synthetic languages / toy transfer tasks is not inherently novel.
4. [Why Better Cross-Lingual Alignment Fails for Better Cross-Lingual Transfer: Case of Encoders](https://aclanthology.org/2026.mrl-1.10/) (MRL 2026) finds that better geometric alignment does not reliably imply downstream transfer; alignment and task gradients may be poorly aligned. Important: **encoder models**, not a general theorem about all LLMs.
5. [Disentangling Linguistic Relatedness from Task Alignment in Cross-Lingual Transfer](https://aclanthology.org/2026.acl-srw.62/) (ACL SRW 2026) finds strong confounding between model baseline ability, task-format alignment and apparent family-based transfer in the studied Arabic fine-tuning setting.

## Updated hypothesis boundary

**Not novel by themselves:** multilingual mixtures; tiny multilingual instruction fractions; controlled toy-language transfer tasks; static geometry comparisons; gradient-affinity-based training sample selection; replay for forgetting.

**Possibly meaningful but NOT verified as novel:** Can an affordable, prespecified cross-language influence/gradient statistic measured at an early training checkpoint accurately predict **later out-of-sample functional transfer** better than (a) training-loss trends, (b) static representation geometry, (c) language family/script similarity, and (d) gradient-affinity selection baselines across several tasks, with equal compute and exposure? The answer could be no. Before implementation, search explicitly for **early-checkpoint transfer forecasting** and validate if existing studies already answer it.

## Decision for this project

- Do not begin more training, infrastructure, or outreach solely on an attractive analogy.
- Treat cross-disciplinary neuroscience/dynamic-systems ideas as **hypothesis sources**, not as evidence of novelty.
- Preserve this as prior-art and negative-search learning in the overall graph vision.
- Next high-leverage scientific action is a **small prior-art matrix** specifying exactly which question/outcome measure has not been addressed by existing papers; if no defensible gap remains, abandon this hypothesis and generate alternatives.

This is a targeted literature review, not an exhaustive novelty certificate, and makes no reproduction or scientific discovery claim.
