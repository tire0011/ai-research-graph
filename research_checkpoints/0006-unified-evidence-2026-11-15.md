# Research checkpoint 0006 — Negative evidence and a real scientific next question

- **Date:** 2026-11-15
- **Type:** Synthesis across graph utility and historical hypothesis discovery
- **Extends:** [Checkpoint 0005](0005-comment-evidence-2026-11-15.md); retains [original unified mission](0002-unified-mission-2026-11-14.md)
- **Status:** Evidence-based research direction; no demonstrated new scientific discovery

## Why this checkpoint exists

The goal of our research graph is **not** to make a larger collection of paper links. It is to reduce wasted research effort, connect complementary work, find low-cost high-information tests and eventually produce falsifiable, genuinely new ideas. Exploratory human questions are **probes**, not a new mission at every turn. Preserve negative findings and later connections.

## Thread A — Does the graph offer better research decisions than source search?

- The existing 20-question/20-two-hop retrieval benchmarks show **no accuracy improvement** over fair source-following text.
- [Three preselected OpenEuroLLM cases](../studies/decision_pilot_20261115/SELECTION.md) had zero extra graph edges while relevant facts were found in fifteen public comments.
- [Exactly identical source evidence](../studies/decision_pilot_20261115/FROZEN_EVIDENCE.json) was captured for a graph-assisted and plain-source review, with [a reproducible parity audit](../paired_decision_evidence.py) and unit tests. This supports an **input-equality conclusion**, not a blinded model-decision comparison.
- Correct abstention matters: a task may already be completed, a PR may already be merged, and an economics question may matter more than another implementation. Claiming a graph benefit without an independently observed decision difference would be misleading.

**Decision:** Do not expand crawlers or semantic-edge services just to produce more connections. Use the existing source-comment tooling on demand and insist on original-source confirmation.

## Thread B — Can the graph help find scientific hypotheses that are worth testing?

- [Historical 2023-cutoff hypothesis seeds](../studies/historical_2023/HYPOTHESES.md) were documented with pre-2024 papers and explicit falsification tests.
- [The later-evidence review](../studies/historical_2023/OUTCOME_REVIEW.md) finds partial consistency for tiny multilingual mixture benefits and original-source replay, but no tested demonstration of the proposed early influence predictor.
- **The historical exercise is contaminated:** a modern model already knows 2024 findings. It is NOT a successful scientific forecast.
- [New prior-art inspection](../studies/historical_2023/PRIOR_ART_FOLLOWUP_20261115.md) shows that gradient-based multilingual filtering, toy-language ability transfer, and geometric misalignment have already been studied. These cannot be claimed as original ideas.

**Decision:** Treat this as a first negative/educational historical reconstruction. Next seek an exact unanswered and cheaply falsifiable *prospective* question, with independent checks against recent papers.

## One coherent idea remains

**Question -> dated evidence -> explicit relation and contradiction -> provisional hypothesis -> smallest falsification test -> observed outcome -> durable versioned checkpoint.**

The same foundation supports:
- avoiding work already completed (DocHPLT);
- identifying a real operational research decision (reserve nodes versus HPC requeue);
- unifying complementary research tasks (evaluation and reporting);
- challenging mechanistic hypotheses about multilingual transfer;
- recording when ordinary search is just as effective.

This checkpoint extends, rather than replaces, the other four missions.

## Next evidence gate

1. Confirm the source-parity runner has passed and archived the exact input digest; **do not count input parity as decision quality**.
2. For *one* new question, compare a concrete graph-derived decision packet against plain source-following with the same original sources and an independent reviewer or human owner; record actual change of action. If both are equal, prefer the simpler method.
3. Alternatively, conduct a truly prospective small-scale research test with a hypothesis frozen before new results exist; avoid retrospective forecasting claims. For multilingual transfer, start with a precise prior-art matrix and a low-compute discriminating experiment, **only** if novelty is still plausible.

**No further infrastructure or third-party outreach is authorized by this checkpoint.**
