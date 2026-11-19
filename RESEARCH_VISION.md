# Research Vision: From Evidence Graph to Testable Scientific Hypotheses

**Status:** Research direction / proposal, not an implemented capability or established scientific result.
**Recorded:** 2026-11-14
**Project:** [AI Research Graph](https://github.com/tire0011/ai-research-graph)

## One overall idea

Build an **evidence-grounded, cross-disciplinary research discovery system** that helps humans ask better questions, links observations and explanations across scientific fields, proposes *falsifiable* hypotheses, finds relevant prior work and counterevidence, and identifies small experiments with high potential information value.

The long-term goal is **not** merely to find related documents, assemble a knowledge graph, or have an LLM generate plausible ideas. It is to make the path from *curiosity -> evidence -> hypothesis -> critical test -> updated understanding* inspectable, reusable, and progressively more useful.

This is an **extension of the existing graph**, not a replacement or a separate agent project. Preserve its evidence/provenance discipline and independently validated baselines. Keep human decisions and automated external actions separate.

**Unified mission checkpoint:** [Checkpoint 0002 — one graph, multiple scientific outcomes](research_checkpoints/0002-unified-mission-2026-11-14.md) explicitly preserves the original aims of **detecting potential duplicate work, finding high-leverage low-effort interventions, and facilitating grounded collaboration** alongside hypothesis discovery, historical evaluation and checkpoint-based learning. These are complementary views over one evidence foundation, not independent project pivots.

## Essential conversation principle: questions are probes, not pivots

The researcher need not be a subject-matter expert. Questions, analogies, speculative comparisons, and apparent changes of topic are how new connections are explored.

**Do not silently redefine the project objective after each question.**

For every relevant exploration:

1. Capture the **original question or intuition** without pretending it is a verified claim.
2. Identify the **discipline(s)** and the **mechanism**, not merely matching terms.
3. Record **what is established**, **what is proposed**, **what is disputed or unknown**, and **what would falsify it**.
4. Connect the result to the overall research goal and to earlier questions.
5. Preserve rejected ideas and negative results as learning, rather than forgetting them.
6. Periodically synthesize a **single coherent research direction** from the accumulated questions; human review decides priorities.

A useful user question can become a graph node even when the correct answer is "this has already been done" or "the analogy fails."

## Two complementary jobs of the graph

### A. Existing job: evidence and collaboration mapping

Continue the current scoped OpenEuroLLM/OpenAIRE/Hugging Face work: public sources, exact references, declarations and limitations, cross-project opportunities, and fair comparisons to ordinary search. Claims about citations, metadata, implementation, verified outcomes, and causal effects **must remain distinct**.

The repository already has a bounded research-interventions pilot. Reuse its proposal / skeptic / experimenter roles and source checks where appropriate; do not describe them as automated discoveries.

### B. Proposed extension: hypothesis discovery and evaluation

Explore cross-disciplinary transfer (neuroscience, biology, physics, mathematics, engineering, linguistics, machine learning, etc.). The useful unit is a **mechanistic hypothesis**, not a topical connection between papers.

Possible typed records and links (proposals; not current schema):

- **Question**: human-originated prompt and its intended underlying problem.
- **Observation / finding**: sourced statement with method, population/context, limits and version.
- **Mechanism / model**: explanation with assumptions and domain of validity.
- **Analogy / transfer proposal**: which specific mechanism might map from domain A to B, and where the analogy may break.
- **Hypothesis**: testable prediction, expected direction, confounders and failure condition.
- **Prior-work / counterevidence**: independent studies, null results, contradictions, and unresolved novelty checks.
- **Experiment / outcome**: protocol, controls, resources, baseline, measurement and evidence for results.
- **Decision / synthesis**: why the idea was retained, rejected or deferred, and how it contributes to the overall direction.

Distinguish edge types such as `cites`, `reports`, `suggests`, `contradicts`, `inspired_by`, `predicts`, `tested_by`, and `replicated_by`. A speculative `inspired_by` edge is **not** an evidenced `causes` or `improves` edge. Store original source URLs, relevant exact excerpts, capture dates, and hashes where appropriate. Never fabricate research relationships.

## Initial question trail (leads, not conclusions)

These questions led to this extension. Keep them connected, rather than treating the newest one as the sole project:

1. **Multilingual training:** Why do additional languages sometimes improve capabilities in other languages? What is learned, transferred, or forgotten? Can we predict effective language mixtures instead of exhaustive trial and error?
2. **Mathematical representations:** Can a transformation (SVD/PCA, spectral analysis, geometry, dynamics, information-theoretic measures, etc.) reveal learning mechanisms invisible in raw weights? Which methods are already established, and what would make a new claim nontrivial?
3. **Functional transfer versus geometric similarity:** Does similarity between linguistic representations imply usable cross-lingual knowledge, or only correlated activation patterns? How could an intervention distinguish the two?
4. **Other sciences:** What techniques developed for vector spaces and evolving systems in signal processing, control, fluid dynamics, physics and mathematics can be transferred with meaningful assumptions and falsifiable predictions?
5. **Neuroscience/biology:** Artificial neural networks have historical inspiration in simplified biological neurons, but modern backprop-trained transformers are **not** brain replicas. Can *specific* biological mechanisms such as replay, consolidation, sparsity or plasticity suggest controlled AI experiments? Check existing AI work before calling anything new.
6. **The meta-question:** Rather than asking an LLM for novel ideas, can we create a system that reliably **discovers research-worthy, untested questions** from grounded observations, gaps and contradictions?

The current answers include substantial prior work. **No hypothesis here is claimed to be novel, true, causal, or effective.** "Maybe companies know it privately" is uncertainty, never evidence of novelty.

## Operating loop

1. **Collect:** human questions, papers, source experiments, explicit limitations and counterexamples.
2. **Normalize:** entities, exact research claims, contexts, comparability, caveats and provenance.
3. **Connect:** citation/dependency links **plus** candidate mechanistic analogies and contradictions; clearly separate evidence from conjecture.
4. **Generate:** a small set of precise hypotheses with predicted observation and likely disproof.
5. **Challenge:** prior-art / novelty search; independent skeptical review; simple alternatives; measurement confounds; publication and retrieval bias.
6. **Prioritize with human review:** potential knowledge gain, falsifiability, resource cost, scope, novelty uncertainty, and fit with the evolving shared research vision. A novelty score from an LLM is not proof of novelty.
7. **Test:** smallest decisive experiment with frozen data/protocol, suitable controls, and a fair baseline.
8. **Learn:** store positive, null and negative outcomes and synthesize how the *overall* idea should evolve. Only change the mission through an explicit human decision.

**Preserve an idea registry** even when the first investigation shows earlier researchers already tried something. Attach "already studied" citations and the precise remaining gap; do not drop the reasoning trail.

## Persistent idea checkpoints and synthesis (proposal)

Human exploration must survive chat changes without treating each new question as a mission pivot. Store **research/idea checkpoints**, distinct from neural-network training checkpoints. This section specifies a minimal human-reviewed workflow, **not an implemented scheduler or graph schema**.

### Checkpoint lifecycle and lineage

- Create an **append-only checkpoint** after a meaningful new question, relevant result, contradiction, discarded hypothesis or unexpected connection; do not save every casual message.
- Each checkpoint should record a stable ID, creation date, original question/intuition, current synthesis, linked prior checkpoint IDs, source evidence and its availability date, confidence/limitations, open questions, candidate falsifiable hypotheses, and what would cause a re-review.
- Preserve previous snapshots. **Corrections, expansions and mergers produce new checkpoints** with explicit `supersedes`, `extends`, `combines` or `contradicts` links. Never silently rewrite the earlier line of reasoning.
- Revisit open checkpoints when new evidence appears and at deliberate review milestones (e.g. after a batch of related explorations, before choosing an experiment, or during a project review). No automatic periodic execution is implied.
- A **synthesis checkpoint** joins multiple idea threads into a coherent *working* theory, identifies tensions and competing explanations, and proposes the next decisive test. It is a provisional model, not proof of a new scientific theory.
- Include previously researched, refuted and inconclusive ideas. `already_known`, `rejected`, `open`, `under_test`, `supported` and `superseded` are suggested statuses, **not current schema values**.
- Keep source evidence, interpretive claims, and hypotheses in separate fields. A graph connection or expert analogy does not automatically provide causal evidence.

A manual checkpoint can initially be a Markdown file with explicit backlinks; only develop typed graph records after we verify that the format helps. The first manually captured example is [research_checkpoints/0001-foundation-2026-11-14.md](research_checkpoints/0001-foundation-2026-11-14.md). Additional checkpoints should be captured when we actually review new ideas; no automatic collection from future chat sessions is claimed.

### Historical replay / rediscovery experiment (2023 cutoff)

**Specific proposed test:** freeze information that was publicly available no later than **2023-12-31**, formulate hypotheses about future research directions, then independently examine published evidence from **2024-01-01 through 2026-11-14** for support, contradiction, novelty, and missing predictions.

1. Choose a small bounded set of research questions and record their source snapshots, publication/availability dates and exact revisions **as known at the 2023 cutoff**.
2. Separate the hypothesis-generation phase from the **later-evidence evaluation**. Avoid exposing later papers, citations, metadata or derived claims to the candidate-generation step.
3. Beware **training-knowledge leakage**: an LLM trained after the cutoff can implicitly remember 2024–2026 results. Retrieval filters alone do not make this genuine historical prediction. Where feasible use a dated earlier model and strong controls; otherwise describe the result as *retrospective reconstruction with leakage risk*, not a real forecast.
4. Compare graph-assisted hypothesis generation with simpler fair baselines using the same permitted evidence: direct literature search, source-following search and source-grounded LLM without graph.
5. Evaluate exact, falsifiable predictions; how novel they were relative to 2023 prior art; soundness; cost; later independent corroborating **and contradicting** findings. Distinguish a published claim from replication or established truth. A hypothesis without a later paper is **unresolved**, not automatically wrong.
6. Record all candidate predictions *before* checking held-out sources and retain negative, inconclusive and already-known ideas. Prefer blind human review where possible.
7. Repeat the comparison only if a first small manual pilot demonstrates value. A broader graph or better-looking ideas alone are not success.

This 2023 cutoff is the current **candidate** for the first historical pilot; the precise design remains a human-reviewed decision.

## First proposed evaluation: historical research rediscovery

**Question:** Does a grounded cross-disciplinary graph help produce *more useful, testable and later-supported* hypotheses than straightforward literature search and LLM prompting?

A small, preregistered pilot:

- Choose a bounded scientific topic and a strict historical cutoff (e.g. knowledge available by **2023-12-31**).
- Build candidate ideas using only sources available at that cutoff, including publication dates, revisions and metadata restrictions. Be explicit about LLM pretraining leakage: a modern model may already know later discoveries. Do **not** claim a genuine time-blind prediction from a modern LLM without leakage controls.
- Compare at least: (a) plain keyword/semantic search with multi-hop reading, (b) LLM plus identical source packets, (c) graph-assisted reasoning using identical available evidence. Give the baselines comparable research effort and source access.
- Evaluate human-rated **specificity, novelty relative to the cutoff, falsifiability, evidence correctness, and experiment cost**. Separately measure whether a subsequently published study corroborates *or contradicts* the hypothesis. "Later published" is not automatically "true", and later absence is not proof of failure.
- Keep blind evaluation where feasible; record invalid, previously known, untestable, negative, and failed ideas too.
- If the graph shows no gain over simpler approaches, say so and do not expand the architecture.

**Prior to implementation:** manually create and review 3-5 example question-to-hypothesis cards and audit their sources. Extend the schema only if existing graph records cannot faithfully represent the needed distinctions.

## Example idea card (not a discovery)

**Human question:** Can transformations of activation trajectories reveal when adding another language causes *useful* transfer rather than only geometric similarity?

**Source domains:** multilingual transfer; representation geometry; dynamic systems; neuroscience as optional inspiration.

**Candidate mechanism:** a change in a cross-language activation subspace may correlate with functional transfer. This is *not* sufficient evidence of causation.

**Prediction:** a prespecified feature computed on earlier checkpoints predicts held-out cross-language task change better than simple existing similarity metrics, training-loss trends, and a matched text-only baseline.

**Counter-tests:** shuffle language identities; compare other checkpoint times/models; control for token counts, training exposure, task overlap and metric artifacts; perform targeted interventions if feasible.

**Prior-art check:** search representation similarity, spectral prediction, gradient agreement, cross-lingual transfer, training-dynamics and replay literature before spending compute. The existing results may already cover the full proposal.

**Outcome:** **unverified hypothesis seed**, novelty unknown, no result yet.

## Boundaries and commitments

- Keep the existing graph's provenance levels, source-failure behavior, fairness to search baselines, and read-only external research workflow.
- Distinguish **known fact / source-reported finding / interpretation / analogy / hypothesis / verified experimental effect**.
- Never promote an evidence edge into a causal or scientifically validated claim.
- Avoid new services, MCP endpoints or generalized autonomous agents before a focused test establishes benefit.
- No automatic publication, outreach, issue changes in third-party projects, or unapproved experiments.
- The overall idea should be updated by documented synthesis and human review, not by the latest conversational tangent.

## Immediate next human-reviewed decisions

1. Review this mission and the initial question trail; amend rather than silently overwrite.
2. Write 3-5 manually verified, cross-disciplinary hypothesis cards with prior-art links and negative evidence.
3. Decide a fair, small evaluation against ordinary research search. Implement only what that evaluation requires.

**Success means better research decisions and new verified knowledge, not simply a larger graph or more generated ideas.**
