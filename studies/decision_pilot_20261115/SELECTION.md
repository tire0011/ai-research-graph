# Decision pilot 2026-11-15 — selection frozen before source inspection

**Status:** Pre-registered case selection; this is not the evaluation result.
**Selection time:** 2026-11-15 (Europe/Berlin)
**Frozen graph source:** [results/snapshot.json](../../results/snapshot.json), timestamp `2026-11-14T21:59:08.316070+00:00`, 982 nodes and 407 edges.

## Selection protocol

To avoid hand-picking only successful examples, use a deterministic, title/metadata-only case selection. **Source issue bodies and comments were not read for the selected cases before this file was committed.** This is a small, stratified sample, not a random representative sample of scientific research.

- Population: `issue` nodes belonging to `OpenEuroLLM/Taskboard` in the frozen graph snapshot with `updated_at >= 2026-09-01`.
- Exclude issue identifiers already discussed, analyzed or in prior fixed benchmark cases (including the previous four-case audits, #450 link bug and #164 false-link target), plus title-only parent/top-level umbrella tasks.
- Category order: (1) evaluation title contains `evaluat|benchmark|judge|metric`; (2) data title contains `data|corpus|filter|annotat|collect`; (3) workflow title contains `pipeline|training|train|deployment|throughput|hardware`.
- Within each category, sort by unsigned 32-bit FNV-1a of UTF-16 code units of `2026-11-15-decision-pilot-v1|<lowercase node id>` ascending. Choose the first eligible, exclude it from later categories.
- Selection is defined using title, ID and update date **only**, not issue body, graph edges or actual outcome. No replacement after reading source except for unavailable or materially changed source; in that case mark inconclusive and preserve the exclusion reason.

The first selected candidate for evaluation before excluding the known #164 number was Taskboard #164; after excluding it, the first new candidate is **#346**. For workflow, the first was umbrella #218 (excluded due to “top-level” in title), so **#343** is selected. This explicit audit prevents silently changing the sample.

## Frozen cases and questions

| Case | Topic (title from graph) | Locked anchor | Research decision question |
| --- | --- | --- | --- |
| E1 | [Multilingual scaling laws — downstream evaluation](https://github.com/OpenEuroLLM/Taskboard/issues/346) | `github:OpenEuroLLM/Taskboard#346` | Is a related evaluation/measurement already planned or implemented, and what is the cheapest **missing** validation, if any? |
| D1 | [Analysis of DocHPLT parallel document dataset](https://github.com/OpenEuroLLM/Taskboard/issues/341) | `github:OpenEuroLLM/Taskboard#341` | Is a duplicate dataset analysis being proposed? Can an existing artifact answer the question with less work? |
| W1 | [Fault tolerance intra-job training](https://github.com/OpenEuroLLM/Taskboard/issues/343) | `github:OpenEuroLLM/Taskboard#343` | Is the engineering blocker already being addressed, and is there any evidence-backed, small, nonduplicate intervention? |

## Comparison contract

For each case, independently reconstruct the underlying source facts, follow exact public references and avoid inventing relationships. Record separately:

1. **Graph edge-first:** available anchored node and explicit graph edges, with their provenance and limitations. Any source text read for validation is reported.
2. **Ordinary source-first:** title/body, public issue comments, linked public upstream code and GitHub issue search as needed. Identify the smallest action or a correct abstention.
3. **Independent evidence audit:** compare all claims against original sources. Record what was found by *both*, by one, and by neither, with direct links.
4. **Decision outcome:** `already_covered`, `candidate_complement`, `credible_bottleneck`, `no_action` or `insufficient_evidence`; record alternatives, owner/context uncertainty and a **falsification/stop condition**.

**Important:** This is an honest *coverage and decision-trace pilot*, not a blinded agent-vs-agent study. The graph and source-first modes do not have identical source ingestion if public comments are unavailable in the graph; record that as an access/coverage gap rather than a fair model accuracy victory. The same researcher reviews both modes, so independent human quality scores, reviewer time savings, novelty and impact **cannot** be claimed.

## Outcome rule

A candidate is not “duplicate research” merely because titles are similar. Independently useful replication should not be treated as waste. A speculative relation never becomes a verified graph edge. The right answer can be **no action**. If this three-case audit does not reveal source-backed decisions that ordinary source-following misses, recommend simpler approaches and do not build additional infrastructure. Retain negative findings and create a new append-only synthesis checkpoint.

No third-party repo changes, human outreach or retraining are authorized by this selection.
