# Accelerating AI development in the EU — where the levers are

**Written:** 12 November 2026. **Status:** strategy note and hypothesis collection, **not a measurement**. It combines (a) what this repository has actually observed in public EU AI projects with (b) public EU infrastructure and policy programs. Every claim about this repo links to a generated evidence file; every external claim links to a primary public source. Nothing here is a proven speedup, a causal claim, or a policy recommendation to any institution.

## 1. What this repository's own evidence shows

The probe was built to find friction, and it found four concrete kinds:

| # | Observation (measured, not inferred) | Evidence | Why it matters for acceleration |
| --- | --- | --- | --- |
| F1 | Provenance is thin at exactly the point where it would save time: of **920+ indexed nodes**, only **1** concrete W&B run URL and **8** dataset-manifest declarations with **2** co-located processing scripts were captured; the OpenThinker3 reproduction task ([Taskboard #321](https://github.com/OpenEuroLLM/Taskboard/issues/321)) is still open with **no public results, run manifest or benchmark table**. | [results/REPORT.md](results/REPORT.md); [CASE_STUDY_OPENTHINKER3.md](CASE_STUDY_OPENTHINKER3.md) | When a run cannot be traced to data, code, checkpoint and scores, every team re-derives it. That is duplicated work, not parallel discovery. |
| F2 | Cross-project overlap exists but public coordination signals are weak: **25** candidate handoffs between 8 EU repositories, yet the coordination check found **0 direct cross-task links**, only **10 shared-participant** and **2 broader-repo** signals among shortlisted pairs. | [results/COLLABORATION_MATCHES.md](results/COLLABORATION_MATCHES.md); [results/COLLABORATION_COORDINATION.md](results/COLLABORATION_COORDINATION.md) | Teams re-implement WARC ingestion, robots.txt handling, eval harnesses and scaling baselines that already exist elsewhere in the EU (see [results/CROSS_PROJECT.md](results/CROSS_PROJECT.md), [results/ROBOTS_REUSE.md](results/ROBOTS_REUSE.md)). |
| F3 | Declared dependencies and blockers wait for validation: [Taskboard #391](https://github.com/OpenEuroLLM/Taskboard/issues/391) declares a dependency on #432 (LlamaFactory vs TRL throughput comparison); [Taskboard #433](https://github.com/OpenEuroLLM/Taskboard/issues/433) reports a reproducible OOM in a DPO/FSDP branch on LUMI; [Taskboard #385](https://github.com/OpenEuroLLM/Taskboard/issues/385) reports **106–107k vs 94–99k tokens/s (~9.5%)** explicitly "pending validation". | [results/IMPACT_EVIDENCE.md](results/IMPACT_EVIDENCE.md); [results/OPPORTUNITIES.md](results/OPPORTUNITIES.md) | Reported gains that nobody validates, and blockers that nobody resolves, are idle capacity. These are not proven speedups or proven blockers — they are a review queue. |
| F4 | Reference comparisons are confounded: [Taskboard #207](https://github.com/OpenEuroLLM/Taskboard/issues/207) compares Jupiter (170–175 TFLOPs/s/GPU) against H100 references under different power caps; a weekly sample of 50 open issues surfaced OOM and performance mentions but no automatic impact ranking. | [results/IMPACT_EVIDENCE.md](results/IMPACT_EVIDENCE.md); [results/DISCOVERY.md](results/DISCOVERY.md) | Without matched-hardware, matched-config comparisons, EU teams cannot tell whether a pipeline choice actually saves compute — the scarcest resource. |

A recurring caveat from our own audits applies throughout: a shared citation, a shared term or a shared participant is a **lead, not proof** ([QA_AI_REVIEW.md](QA_AI_REVIEW.md), [QUALITY_REVIEW.md](QUALITY_REVIEW.md)). The levers below are therefore framed as "worth testing", each with an explicit falsification condition.

## 2. The levers, grouped by bottleneck

### L1 — Compute: make EuroHPC/AI Factory access predictable, not heroic

Europe already owns top-tier public compute: the EuroHPC JU has procured **11 supercomputers**, with **JUPITER** (Jülich, Europe's first exascale, TOP500 #4), **LUMI** (Kajaani, #9) and **Leonardo** (Bologna, #10) in the world top 10 ([EuroHPC JU, Oct 2025](https://www.eurohpc-ju.europa.eu/eurohpc-ju-selects-six-additional-ai-factories-expand-europepes-ai-capabilities-2025-10-10_en)). The **AI Factories** network grew from 7 sites (Dec 2024) to 13 (Mar 2025) to **19** (Oct 2025), plus **13 "AI Factory Antennas"** linking countries without their own factory, and an **AI Gigafactories** call launched 30 July 2026 under Council Regulation (EU) 2026/150; the broader **InvestAI** initiative was announced at up to **€200 bn** ([EuroHPC JU](https://www.eurohpc-ju.europa.eu/); [European Commission, InvestAI](https://digital-strategy.ec.europa.eu/en/policies/investai)). This repository's own issues show the factories are already the training ground: LUMI and JUPITER appear throughout [results/IMPACT_EVIDENCE.md](results/IMPACT_EVIDENCE.md).

- **Lever:** predictable, fast allocation for SMEs/startups and researchers (the antenna model), and standardized access procedures across factories.
- **Lever:** shared, reproducible benchmark protocols on factory hardware (tokens/s, TFLOPs/s/GPU, memory) so results like F4 become comparable by construction. The graph could later track whether matched comparisons actually happen.
- **Falsification:** if allocation lead time and benchmark divergence are already small, this lever adds little; measure before investing.

### L2 — Data: multilingual, legally clean, reusable

Europe's differentiator is lawful multilingual data at scale, not raw crawls.

- The DSM Directive (EU) 2019/790 **Article 4 TDM exception** plus the AI Act's GPAI **copyright policy obligation (Art. 53)** ([Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)) create a workable legal basis — if pipelines implement TDM/robots.txt reservations correctly. Our [robots.txt reuse audit](results/ROBOTS_REUSE.md) shows exactly this handoff happening in practice: OpenEuroLLM proposed reusing HPLT's earlier robots.txt indexing work instead of rebuilding it.
- Shared multilingual corpora and pipelines (HPLT v4, Common Crawl processing, OSCAR-class resources; OpenEuroLLM ↔ HPLT ↔ LAION cooperation on MixtureVitae and multilingual reference models is already documented in [results/CROSS_PROJECT.md](results/CROSS_PROJECT.md)) mean one extraction pipeline serves many projects.
- **Lever:** publish processed corpora + manifests (row counts, token counts, decontamination status — note the case study found a **failed decontamination step** for `openthoughts-3`, [CASE_STUDY_OPENTHINKER3.md](CASE_STUDY_OPENTHINKER3.md)) so downstream training does not re-crawl, re-clean or re-decontaminate.
- **Falsification:** if most projects still re-crawl because published corpora miss their language/domain, the gap is coverage, not tooling.

### L3 — Coordination: reuse before re-implement

F2 is the core finding. Concrete reuse targets already visible in this repo:

- **WARC/text extraction:** [OpenEuroLLM/web-data-processing](https://github.com/OpenEuroLLM/web-data-processing) vs [hplt-project/HPLT-textpipes](https://github.com/hplt-project/HPLT-textpipes) and [warc2text-runner](https://github.com/hplt-project/warc2text-runner) — shared topic terms, byte-identical files found in the bounded HPLT audit ([results/HPLT_OVERLAP.md](results/HPLT_OVERLAP.md)).
- **Evaluation:** [OpenEuroLLM/oellm-eval](https://github.com/OpenEuroLLM/oellm-eval) (SLURM job arrays across HPC clusters) vs [utter-project/eurollm-evaluation](https://github.com/utter-project/eurollm-evaluation), both building on `lm-evaluation-harness`.
- **Scaling references:** LAION's [open-sci-ref-0.01](https://github.com/LAION-AI/open-sci-ref-0.01) intermediate checkpoints vs OpenEuroLLM's [dense_english_scaling_laws](https://github.com/OpenEuroLLM/dense_english_scaling_laws) — published loss curves can be reused instead of retrained.
- **Lever:** a standing, machine-readable "new task → existing related work" index across EU orgs — which is exactly what `collaboration_matcher.py` prototypes, but it needs **human precision labels on unseen questions** before anyone builds a permanent service (the open measurement question in the [README](README.md)).
- **Falsification:** if reviewers label most matcher suggestions as already-coordinated or irrelevant, coordination tooling is not the bottleneck; if they are actionable, reuse is.

### L4 — Provenance: make every experiment re-runnable by default

F1 is the deepest structural finding. The case study proposes an **experiment manifest** with typed relations (`cites_paper`, `declares_dataset`, `trained_on`, `evaluated_with`, `produced_checkpoint`, `reproduces_result`) anchored to commits, dataset revisions and run IDs ([CASE_STUDY_OPENTHINKER3.md](CASE_STUDY_OPENTHINKER3.md)). Today the snapshot captured only **1** concrete W&B run reference across all indexed OpenEuroLLM tasks.

- **Lever:** public run manifests (data revision, code commit, hyperparameters, seeds, run URL, eval suite revision, scores) attached to every training issue/PR as a merge requirement — the same way CI checks code.
- **Lever:** model cards that declare `base_model`/`datasets` lineage — the graph already verifies **76** such declarations and one-hop external targets ([results/REPORT.md](results/REPORT.md)); making this systematic turns lineage from forensics into infrastructure.
- **Falsification:** if reproductions already succeed without manifests (check: sample reproduction tasks and count how many are publicly verifiable), the overhead is not justified.

### L5 — Evaluation as shared infrastructure

Duplicate eval stacks (F2) fragment comparability. A single multilingual benchmark suite run on EuroHPC hardware with published harnesses ([oellm-eval](https://github.com/OpenEuroLLM/oellm-eval) pattern) lets every EU model be compared on the same ruler — which is what makes open models *adoptable*.

- **Lever:** converge on a small set of maintained multilingual benchmarks + leaderboards; publish per-language scores, not only averages (Europe's edge is language coverage).
- **Falsification:** if leaderboard scores do not predict downstream task success for EU users, invest in task-specific evals instead.

### L6 — Regulation as an accelerator, not a brake

The AI Act ([Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)) is fully in application since **2 August 2026**: prohibitions and AI-literacy since 2 Feb 2025, GPAI obligations (technical documentation, copyright policy, systemic-risk evaluation) since 2 Aug 2025, transparency (Art. 50) and enforcement since 2 Aug 2026; the Digital Omnibus (Regulation (EU) 2026/1744, in force 27 July 2026) pushed Annex III high-risk duties to **2 Dec 2027** and Annex I to **2 Aug 2028** ([EC AI Act Service Desk timeline](https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act); [Shaping Europe's digital future](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)).

- **Lever:** one rulebook across 27 markets removes legal fragmentation; providers who build compliance artifacts once (risk management, data governance, transparency, human oversight) sell everywhere. Regulatory **sandboxes** (Art. 57–58) and the GPAI **Code of Practice** give a presumption-of-conformity fast lane for open-model providers.
- **Lever:** treat compliance data (model cards, data statements, eval reports) as *reusable public artifacts* — the same artifacts L4/L5 need. Compliance and reproducibility reinforce each other.
- **Falsification:** if compliance artifacts are produced but never reused or inspected, the Act is only cost; measure reuse of published documentation.

### L7 — Open models and permissive licensing

OpenEuroLLM, EuroLLM, LAION and HPLT publish under permissive licenses (e.g. Apache-2.0 for LAION's open-sci-ref). Open weights + declared lineage (L4) let SMEs fine-tune instead of training from scratch — the cheapest acceleration available, and it compounds: every fine-tune is a new starting point for the next team.

- **Lever:** keep model cards machine-readable and version-pinned on the Hub; the graph's one-hop lineage verification shows this is feasible with public APIs alone.
- **Falsification:** if fine-tuning from EU open bases is rare in practice (measure downstream `base_model` declarations), open release is not converting into reuse.

### L8 — Talent, procurement and language coverage

- **Lever:** public procurement as a demand anchor — EU administrations buying EU open models for the 24 official languages creates a guaranteed market and a multilingual testbed (language coverage is where EU models can verifiably beat generic ones).
- **Lever:** AI Factories as talent hubs with researcher access (antenna model), plus mobility between academia and factories; the repo's own opportunity queue names public assignees precisely so humans — not automation — can route questions ([results/OPPORTUNITIES.md](results/OPPORTUNITIES.md)).
- **Falsification:** if procurement cycles remain slower than model release cycles, the demand anchor does not accelerate anything; measure time-to-deploy.

## 3. Suggested sequencing

| Horizon | Lever | First concrete step | Evidence that it works |
| --- | --- | --- | --- |
| Now (0–6 months) | L3, L4 | Human-label the existing 25 matcher candidates; require a run-manifest link on new training PRs | Reviewer precision on unseen questions; count of publicly reproducible tasks |
| Near (6–18 months) | L1, L2, L5 | Matched-hardware benchmark protocol across LUMI/JUPITER; publish processed-corpus manifests; one shared multilingual eval suite | Comparable tokens/s numbers; corpora reused instead of re-crawled; leaderboard adoption |
| Structural (1–3 years) | L6, L7, L8 | Compliance artifacts as public, versioned data; procurement pipeline for EU open models; Gigafactory-scale training for frontier models | Reuse of published documentation; time-to-deploy in public sector; frontier-scale EU runs |

## 4. What this project can measure next

1. **Reuse rate:** fraction of new EU tasks whose matcher suggestion is labeled actionable reuse by an independent reviewer (the README's open "measurement that matters").
2. **Provenance completeness:** share of training issues with a linked run manifest / eval artifact — baseline today is ~1 run reference in 920 nodes.
3. **Blocker resolution time:** time from a reported OOM/dependency (e.g. #433, #391→#432) to a verified fix — a direct speed metric for the ecosystem, unlike benchmark speed.
4. **Cross-org edge density:** grow the 8-repo registry and track whether "no visible link" (13/25 today) shrinks as coordination becomes public.

## 5. Limits of this analysis

- Rows F1–F4 are measurements from bounded, sometimes purposeful samples; they are **not population estimates** for all EU AI projects.
- External program facts (AI Factories count, timelines, InvestAI) are as published in November 2026 and link to primary sources; they describe programs, not their effectiveness.
- No lever above is claimed to be *proven* to accelerate development; each carries a falsification condition precisely because this repo's core lesson is that textual evidence is not causal evidence ([QA_AI_REVIEW.md](QA_AI_REVIEW.md)).
- This document proposes no outreach to any project or institution and sends no messages.

## Sources

- Internal evidence: [results/REPORT.md](results/REPORT.md), [results/CROSS_PROJECT.md](results/CROSS_PROJECT.md), [results/HPLT_OVERLAP.md](results/HPLT_OVERLAP.md), [results/ROBOTS_REUSE.md](results/ROBOTS_REUSE.md), [results/COLLABORATION_MATCHES.md](results/COLLABORATION_MATCHES.md), [results/COLLABORATION_COORDINATION.md](results/COLLABORATION_COORDINATION.md), [results/IMPACT_EVIDENCE.md](results/IMPACT_EVIDENCE.md), [results/OPPORTUNITIES.md](results/OPPORTUNITIES.md), [results/DISCOVERY.md](results/DISCOVERY.md), [CASE_STUDY_OPENTHINKER3.md](CASE_STUDY_OPENTHINKER3.md), [QA_AI_REVIEW.md](QA_AI_REVIEW.md), [QUALITY_REVIEW.md](QUALITY_REVIEW.md)
- [EuroHPC JU — six additional AI Factories (Oct 2025)](https://www.eurohpc-ju.europa.eu/eurohpc-ju-selects-six-additional-ai-factories-expand-europes-ai-capabilities-2025-10-10_en) and [EuroHPC JU — AI Factory Antennas (Oct 2025)](https://www.eurohpc-ju.europa.eu/eurohpc-ju-selects-ai-factory-antennas-broaden-ai-factories-initiative-2025-10-13_en)
- [European Commission — InvestAI](https://digital-strategy.ec.europa.eu/en/policies/investai)
- [Regulation (EU) 2024/1689 (AI Act)](https://eur-lex.europa.eu/eli/reg/2024/1689/oj); [EC AI Act Service Desk — implementation timeline](https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act); [Shaping Europe's digital future — AI Act](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)
- [Directive (EU) 2019/790 (DSM), Art. 4 TDM exception](https://eur-lex.europa.eu/eli/dir/2019/790/oj)
