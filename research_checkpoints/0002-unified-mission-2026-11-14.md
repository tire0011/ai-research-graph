# Research checkpoint 0002 — One graph, multiple scientific outcomes

- **Date:** 2026-11-14
- **Type:** Synthesis checkpoint / proposed mission clarification
- **Status:** Working synthesis — discussion, not tested implementation
- **Extends:** [Checkpoint 0001](0001-foundation-2026-11-14.md)
- **Vision:** [RESEARCH_VISION.md](../RESEARCH_VISION.md)

## Origin: the human question

The research graph should not silently become *only* an idea generator. Its earlier aims remain essential: identify duplicated research, discover collaboration opportunities, and determine where a small intervention yields the largest research benefit. Can one coherent system also support cross-disciplinary hypotheses, historical experiments, and idea checkpoints?

## Unified mission

**Accelerate scientific progress by making existing work more reusable, avoiding unnecessary duplication, identifying high-leverage interventions, connecting complementary researchers and artifacts, and generating and validating new hypotheses.**

Treat these as **different questions asked of a shared evidence foundation**, not five disconnected software products. Preserve the ability to ask open-ended human questions without silently changing the mission.

### Shared evidence foundation

Capture and preserve attributable sources, dated claims, projects, issues/PRs, artifacts, experiments, observed results, limitations, explicit dependencies, and question/idea checkpoints. Preserve distinctions between:
- same topic and actually duplicated work;
- explicit link and confirmed collaboration;
- reported metric and independently reproduced improvement;
- candidate cost/benefit and measured impact;
- intuitive analogy and causal scientific explanation;
- proposed hypothesis and verified discovery.

Do not add wide data ingestion or new graph infrastructure before evidence shows it improves the selected decision.

## Five questions / views of one graph

1. **Redundancy:** Is two groups' work truly overlapping? Compare research questions, methods, deliverables, settings, evidence, participants, and progress. Shared keywords or citations alone are not enough. Some independent replication is valuable and **must not be falsely labelled waste**.
2. **Leverage:** Which specific bottleneck, reusable component, verification, or missing experiment could produce the highest *expected information or research value* relative to effort? Impact and cost are estimates with uncertainty until empirically measured. Prioritize concrete, attributable tasks, not buzzwords.
3. **Coordination:** Who could benefit from whom? Require a directional, grounded handoff and check whether public evidence already shows coordination; private conversations remain unknown. Do not contact researchers automatically.
4. **Discovery:** What contradictions, unexplained outcomes, cross-disciplinary mechanisms or missing experiments suggest falsifiable hypotheses? Review prior art before claiming novelty.
5. **Learning / historical validation:** Revisit append-only idea checkpoints, synthesize multiple lines, and test historical rediscovery using a 2023-12-31 source cutoff, 2024–2026 held-out evidence, and explicit modern-LLM leakage controls.

All five views read from the same source/provenance discipline. Their outputs remain different, auditable judgments; they do not all need to become graph edge types immediately.

## Existing repo coverage (as of this checkpoint, source README)

- Cross-platform OpenEuroLLM/GitHub/Hugging Face/OpenAIRE evidence and provenance snapshots: **working bounded feasibility prototype**.
- Source-grounded research overlap and collaboration review: **limited pilot/candidates**, not confirmed project-wide duplicate detection or measured collaboration savings.
- Impact study, opportunity detector, research-interventions pilot: **bounded, auditable signals** of possible high-value interventions; not proof of actual time or money saved.
- Research hypothesis generation: **documented vision and prompt/review proposals**, not demonstrated scientific discovery.
- Idea checkpoints: **manual Markdown convention**, not automated lifecycle.
- Historical replay: **evaluation design only**, not a completed time-blind forecast.

## Proposed prioritization, without building new infrastructure

Start from two or three *real* ongoing OpenEuroLLM research questions with source links. For each, compare the value of these outputs:

- A genuine overlap/reuse opportunity; avoid asserting duplicate research when independent replication is appropriate.
- A concrete low-effort, high-leverage action with measurable expected effect and explicit uncertainty (e.g. missing benchmark, shared evaluation artifact, preventable repeat effort).
- A cross-disciplinary hypothesis with a predicted result and falsification test.

Test the outputs against direct source-following text search and a grounded LLM with equal evidence access. Ask researchers or a blinded reviewer whether the graph changed what they would actually do. Record cost, relevance, false positives, abstentions, and *verified* benefit. If no advantage is found, simplify.

The separate historical 2023-cutoff experiment is a useful follow-on to test **idea discovery**, not a substitute for testing the original redundancy/leverage goals.

## Working order of operations

1. **Map goals and current capabilities** (this checkpoint), rather than continue feature expansion.
2. **Pick one or two meaningful, source-backed cases** where discovering redundancy or leverage could matter today.
3. **Produce and challenge small decision packets**, measuring whether they improve on search.
4. **Only then test higher-risk hypothesis discovery and historical replay**, keeping the same foundation and preserving all results as checkpoints.
5. **Synthesize** discoveries, failed assumptions and useful cross-domain connections into a new append-only checkpoint.

## Review triggers

- A real research decision, study or experiment becomes available for comparison.
- A contradiction appears between an existing hypothesis and new evidence.
- A proposed view fails to outperform a simpler baseline.
- New human questions suggest an additional dimension that should be *connected* to existing goals, not replace them.

**No new code, auto-outreach, schema migration or claim of demonstrated value is approved by this checkpoint.**
