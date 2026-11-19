# Research checkpoint 0003 — First source-following decision audit

- **Date:** 2026-11-14
- **Type:** Evaluation/synthesis checkpoint
- **Extends:** [Checkpoint 0002](0002-unified-mission-2026-11-14.md)
- **Status:** Small qualitative audit complete; quantitative graph advantage **unproven**
- **Sources and audit:** [Decision audit](../results/interventions/DECISION_AUDIT_20261114.md) · [Structured case evidence](../results/interventions/DECISION_AUDIT_20261114.json)

## The question being tested

Can the *same* evidence graph help detect duplicated effort, identify small high-leverage improvements and coordination opportunities, without distracting us from the later hypothesis-discovery goal?

## Observations from four purposefully selected cases

1. **Dataset mixing (#451, #448, #186):** source searches already surface a new, ongoing 50B-token multilingual SFT leave-one-out plan. Avoid recommending duplicate training; check evaluation comparability only after outcomes exist.
2. **LlamaFactory (#391, #432, PR #65):** explicit dependency and active open implementation, with an existing user question. No new generic outreach or review required. Unit tests do not establish LUMI SFT/DPO throughput.
3. **Data-quality methods (#437, #353, #416):** potentially complementary techniques, not proven duplication. Judge scores in a *selected* dataset cannot explain why excluded examples failed. Do not build a full feature-analysis integration before a tiny validated comparison to metadata.
4. **Prelude context extension (#392):** active EOS/RULER diagnosis means another generic suggestion would add little; correctly abstain.

## What changed in the larger idea

**The priority is not making the graph generate more recommendations. It is generating fewer, better, decision-changing recommendations and confidently saying "already underway" or "not enough evidence."**

Three important separations:
- *Topic overlap* is not proof of *duplicated work*; independent replication can be useful.
- *High leverage* is a prospective judgment until cost and real benefit are measured.
- *A graph link* is not evidence that the graph beats direct multi-hop source reading.

This connects to the long-term science-discovery goal: the graph should first demonstrate reliable evidence/decision judgment, then test novel, falsifiable hypotheses (including the historical 2023-cutoff protocol).

## Review outcome and next trigger

- **Outcome:** A four-case manual, source-following pilot is now documented in the repository. The audit used live source documents and direct GitHub issue search; no timed or blinded graph query was executed.
- **Unresolved:** Does graph assistance improve precision, correctly avoided duplication, or time-to-decision *over the same source-following search* on unseen cases?
- **Next review trigger:** Freeze a small set of **unseen** research decisions, provide equal source access and budget to graph-assisted vs. source-following approaches, conduct blind scoring, and observe actual decisions. Stop infrastructure expansion if there is no gain.
- **Status of prior checkpoints:** Keep checkpoints 0001 and 0002 unchanged; this extends, rather than replaces, the goals.

No outreach or experiments were performed on third-party repositories.
