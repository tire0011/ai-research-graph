# Research graph: decision gate before recommending work

**Status:** Review procedure, not a deployed classifier or scientific-validation algorithm.
**Evidence:** [StateBench no-go](studies/decision_gate_20261115/STATEBENCH_VS_PRELUDE.md) and [Arena-Hard conditional reuse](studies/decision_gate_20261115/ARENAHARD_REUSE_RECHECK.md).

## Intended value

The graph is a **research memory and decision aid**: find work that already exists, promising low-effort interventions, beneficial coordination, and cross-disciplinary hypotheses. A new human question can expand understanding without replacing the mission. More edges alone are **not** the objective.

## Seven questions every candidate must survive

1. **What precise decision is pending?** State the researcher/maintainer's actual measurable question rather than shared vocabulary. If there is none, stop.
2. **What is already implemented or measured?** Recheck original GitHub issues, comments, PR merge status, dataset/model revisions, paper dates and experimental outcomes **now**. Store review date and URLs. Never assume an earlier open issue remains open.
3. **Same problem, mechanism and measurement?** Compare inputs, model versions, task formulations, outcome variables, metrics, controls, data and possible failure modes. Different metrics may make a proposed handoff misleading.
4. **Is the alternative already available?** Check reproducibility and existing source code, tests, datasets and owner activity. Independent replication can have value; similar titles do **not** imply waste.
5. **Smallest informative next action?** Prefer inspecting a stored result, comparing a handful of existing outputs, or calculating a decision threshold before building a service, scheduling GPUs or writing another evaluator.
6. **What would falsify the recommendation?** Name a concrete disproof/stop condition and distinguish confirmed facts from author reports, analogies, hypotheses and private/unknown coordination.
7. **Does the graph add value over ordinary research?** Re-run a fair direct-source / text-search baseline with the same available primary evidence. If a person can reach the same decision with equal effort, say so: no proven graph advantage.

## Decision outputs (human-reviewed)

- **No action / already done:** existing solution or completed evaluation covers the goal.
- **Reject:** measurement mismatch, missing need, non-comparable outcomes or excessive additional work.
- **Conditional reuse:** a grounded artifact is available, but receiver demand or compatibility still needs confirmation.
- **Testable next experiment:** minimal protocol, fixed controls, direct measurement, resource estimate and defined stop rule.
- **Insufficient evidence:** no factual claim of duplicate work, collaboration or expected savings.

Record source URL/date and the *decision trajectory*. Keep original candidates: `proposed → reviewed → rejected|conditional|tested|verified`. These are process descriptions, **not** new persisted edge statuses without schema review.

## Reference cases

| Candidate from graph | New evidence | Decision | Why |
| --- | --- | --- | --- |
| OpenEuroLLM Prelude context ↔ AllenAI StateBench | EOS-first generative QA collapse vs per-token multiple-choice logprob state tracking, and distinct harnesses | **Reject immediate integration** | The benchmark does not directly test the release blocker; RULER already covers more than needle retrieval |
| OpenEuroLLM arena-hard exclusions ↔ AllenAI Arena-Hard v2 | OpenEuroLLM [PR #174](https://github.com/OpenEuroLLM/oellm-eval/pull/174) merged after the original candidate card; AllenAI [PR #474](https://github.com/allenai/olmo-eval/pull/474) stores judged outcomes and different style metrics | **Conditional reuse** | Matching high-level validation concept, different result schemas and metric assumptions; need an actual receiver decision before integration |

**This is a demonstrated improvement to the quality of our *reasoning trail*, not demonstrated acceleration by graph software.** Plain source searches can also find these facts.

## What to do next

Do not build a generalized auto-collaboration agent or upgrade the schema on these two cases. First have an independent reviewer evaluate the same candidate and source packet against a plain-search baseline, and confirm whether a real researcher's decision changes. Otherwise preserve this small checklist as documentation and keep exploring questions.
