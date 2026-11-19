# Task-reference precision replay + next research decisions (2026-11-14)

**Status:** Completed small reference-level replay against original GitHub issue bodies. The current graph and a simple URL-based source parser both pass **4/4 target-set cases**. **Not** a blinded decision benchmark or a demonstration of research acceleration.

- [Machine-readable case results](TASK_LINK_REPLAY_20261114.json)
- [Workflow run](https://github.com/tire0011/ai-research-graph/actions/runs/43645317653): GitHub Actions completed successfully, including unit tests and a regenerated graph snapshot
- [Earlier four-decision audit](DECISION_AUDIT_20261114.md)
- [Mission checkpoint 0002](../../research_checkpoints/0002-unified-mission-2026-11-14.md)

## A real false-link bug was found and corrected

Before the fix, [Taskboard #450](https://github.com/OpenEuroLLM/Taskboard/issues/450) explicitly pointed to [oellm-eval issue #152](https://github.com/OpenEuroLLM/oellm-eval/issues/152) and [oellm-eval PR #164](https://github.com/OpenEuroLLM/oellm-eval/pull/164). The old graph parser incorrectly interpreted the **`#152` and `#164` inside Markdown link labels** as additional references to *Taskboard* issues with the same numbers, creating four graph edges instead of the intended two.

The correction identifies Markdown links whose labels and GitHub issue/PR URL carry the same number and excludes that label's number from *same-repository* number matching. A distinct unrelated `#n` in the same label is still eligible as a separate reference. The independent source-text reference parser received the same disambiguation rule, implemented independently rather than reading graph edges.

Regression cases were added to:
- [tests/test_research_graph.py](../../tests/test_research_graph.py)
- [tests/test_research_questions_benchmark.py](../../tests/test_research_questions_benchmark.py)

The latest successful [research-graph workflow](https://github.com/tire0011/ai-research-graph/actions/runs/43645317653) regenerated [snapshot.json](../snapshot.json) with **982 nodes and 407 edges** (previous pre-fix snapshot had 982 nodes and 409 edges). For Taskboard #450 it now records only the **two correct** oellm-eval targets.

## Observed small source-reference replay

The [JSON audit](TASK_LINK_REPLAY_20261114.json) records original issue URLs, source update times, graph targets and a conservative baseline extracting full canonical GitHub issue/PR URLs from each original issue body.

| New anchor | Literal linked GitHub task targets | Graph exact | Canonical URL baseline exact |
|---|---|---|---|
| [Taskboard #450](https://github.com/OpenEuroLLM/Taskboard/issues/450) | oellm-eval #152 and PR #164 | yes | yes |
| [Taskboard #443](https://github.com/OpenEuroLLM/Taskboard/issues/443) | none in issue body | yes (abstains) | yes |
| [Taskboard #445](https://github.com/OpenEuroLLM/Taskboard/issues/445) | none in issue body | yes (abstains) | yes |
| [Taskboard #449](https://github.com/OpenEuroLLM/Taskboard/issues/449) | none in issue body | yes (abstains) | yes |

**Results: graph 4/4 exact; URL baseline 4/4 exact.** This is a purposefully chosen tiny set, not a representative or genuinely blinded holdout: #450 was selected after noticing the bug. The baseline here sees full canonical links, **not** unqualified `#n` references. The comparison does **not** establish general graph correctness or decision quality.

## Three practical research decisions, not just hyperlinks

### #450 — A measured backend trade-off, not a reason to rebuild

The [source issue](https://github.com/OpenEuroLLM/Taskboard/issues/450) reports that vLLM runs **slower** than the HF backend on ARC-Easy/HellaSwag/TriviaQA under the tested setup (0.83–0.86x) but **faster** on selected generation-style tasks (2.27–3.98x). The planned work explicitly includes matched 1,024-token runs. [The integration PR #164](https://github.com/OpenEuroLLM/oellm-eval/pull/164) remains open and already acknowledges the need for real cluster evaluation.

**Smallest sensible decision:** Don't propose a second vLLM integration. Follow the already planned matched benchmark; if results vary by task type, require a task-specific backend recommendation rather than one universal choice. Treat numbers as source-reported, not independently reproduced.

**Baseline:** Direct source reading and two linked repository URLs already reveal this. No unique graph contribution established.

### #443 and #445 — Similar workflow, not proven duplicate work

[Taskboard #443](https://github.com/OpenEuroLLM/Taskboard/issues/443) concerns collecting and scheduling missing Prelude evaluations. [Taskboard #445](https://github.com/OpenEuroLLM/Taskboard/issues/445) concerns generating model-card tables and plots from published evaluation datasets. A comment on #445 already identifies the [implemented notebook/script](https://github.com/OpenEuroLLM/notebooks/tree/main/prelude-evaluations-model-card), and the researcher has **already** raised a provenance question in [an existing comment](https://github.com/OpenEuroLLM/Taskboard/issues/445#issuecomment-6773062235).

**Possible relationship:** A complementary, evaluation-output-to-reporting handoff. Neither issue explicitly references the other in its body, so the existing graph has **no evidence edge** between them. An ordinary GitHub search for `evaluation model card` finds both issues. We should **not** create a verified dependency edge or repeat the outreach.

**Smallest sensible decision:** No generic new model-card script. If the maintainers identify a mismatch, test a pinned evaluation revision and checkpoint identifier against the existing published script. Otherwise abstain.

### #449 — Broad coordination, insufficient evidence for a specific intervention

[Taskboard #449](https://github.com/OpenEuroLLM/Taskboard/issues/449) describes a 32B annealing plan, responsible contributors, mixture variants and a timeline. It has no literal task-reference edge in the current snapshot.

**Smallest sensible decision:** Don't invent a blocking dependency or duplicate work from similarity to Prelude annealing. Revisit only if a specific missing input, owner or experimental decision becomes documented.

## What the graph needs next

**Key observation:** Source-grounded link precision is necessary, but a graph that only follows explicit IDs cannot, by itself, adjudicate `same work` vs `complementary` or quantify `high leverage`. We should not automatically add speculative similarity edges.

Next *proper* research evaluation:
1. Select **fresh unseen** decision questions without inspecting candidate answers; commit the selection and source window first.
2. Freeze equal-source input packets for a graph-assisted reviewer and an independent source-following reviewer, including comments and direct source links; equalize time/retrieval budget.
3. Require each reviewer to give one of `duplicate`, `complementary`, `known coordination`, `actionable bottleneck`, `no action`, or `insufficient evidence`, with citations, estimated intervention cost, and a falsification test.
4. Use an independent reviewer and, if possible, the owning researcher to judge **decision change** and true avoided redundant work, not number of suggested links.
5. Preserve negatives, conflicts, unsupported claims and abstentions in versioned idea/research checkpoints.

**Stop gate:** If direct source search gives the same decisions at similar review cost, prefer the simpler tool and do not add new persistent infrastructure.

## Limitations

- Small, cherry-picked sample; not blind, not a scientific discovery test.
- The independent baseline is only canonical-URL extraction in the numeric replay; the qualitative baseline includes human source-following.
- No scientifically validated causation, measured workflow acceleration, saved GPU budget, or proof of unknown coordination.
- Public GitHub issue bodies are live, with last-updated times; they were not pinned by immutable Git SHAs in this audit.
- External repositories were read only; no public OpenEuroLLM issues, PRs or comments were modified.
