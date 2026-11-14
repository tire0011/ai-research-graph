# Research checkpoint 0004 — Evidence correctness before research decisions

- **Date:** 2026-11-14
- **Type:** Quality finding + decision synthesis
- **Extends:** [0003 decision audit](0003-decision-audit-2026-11-14.md)
- **Status:** Concrete parser defect fixed and GitHub Actions green; research acceleration still unproven
- **Source audit:** [Task link replay report](../results/interventions/TASK_LINK_REPLAY_20261114.md) and [structured evidence](../results/interventions/TASK_LINK_REPLAY_20261114.json)
- **Verified run:** [Research graph probe GitHub Actions](https://github.com/tire0011/ai-research-graph/actions/runs/43645317653)

## Original insight

When linking issue `#450` to its cross-repository implementation and measurement tasks, the graph counted the same Markdown reference both as a foreign GitHub URL and as a same-repository bare number. That produces false research connections — an operational risk for our long-term goals of avoiding duplicate work and finding useful collaborations.

## What is demonstrated

1. **Before fix:** Taskboard #450 had four outgoing explicit task references, but two were incorrect: the Markdown labels `#152` and `#164` referred to oellm-eval rather than Taskboard.
2. **Code/test change:** Two independent parsers disambiguate GitHub Markdown link labels; four targeted regression tests cover this example and preserve unrelated bare numbers.
3. **After fix:** Successful workflow rerun; 982 nodes, **407 edges** (down from 409), and exactly two correct outgoing task edges from #450.
4. **Bounded four-issue replay:** Correct literal target sets **4/4 for both** the repaired graph and simple canonical-URL extraction. This is targeted, small and not a blind benchmark.

## How this changes the unified idea

We should prioritize **trustworthy distinctions and correct abstention** over more speculative edges or AI-generated recommendations:

- `explicit_source_reference` and `inferred_workflow_overlap` belong to **different evidence layers**.
- Scientific task overlap is not verified duplication; independent replication can be valuable.
- A cost-saving intervention is **a decision hypothesis**, not measured research benefit.
- An answer available with a simple source search provides **no demonstrated graph advantage** merely because the graph can reproduce it.

Fresh cases offer further examples:
- [Taskboard #450](https://github.com/OpenEuroLLM/Taskboard/issues/450): HF/vLLM comparison is already in progress; don't request another backend implementation.
- [Taskboard #443](https://github.com/OpenEuroLLM/Taskboard/issues/443) and [#445](https://github.com/OpenEuroLLM/Taskboard/issues/445): evaluation collection and model-card reporting may be complementary, but no directly sourced dependency; don't invent one.
- [Taskboard #449](https://github.com/OpenEuroLLM/Taskboard/issues/449): broad planning issue, no grounded specific bottleneck; abstain.

## Next checkpoint / review trigger

Only after **preselecting unseen researcher decision questions** and freezing equal evidence packets should we measure whether graph assistance outperforms source-following review in accuracy, useful decisions and review effort. Prefer manual small study to another infrastructure service. The historical 2023-cutoff prediction pilot remains a separate future test of *new idea discovery*, not a substitute for proving the graph's existing redundancy and leverage value.

**No novel scientific discovery, realized savings or additional third-party outreach is claimed.**
