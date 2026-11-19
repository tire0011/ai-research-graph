# Decision pilot: information lost between issue bodies and research results

**Reviewed:** 2026-11-15 · **Pre-registered selection:** [SELECTION.md](SELECTION.md) · **Machine-readable source audit:** [RESULTS.json](RESULTS.json)

## Key result

Three OpenEuroLLM issue anchors were selected using **only titles and update dates**, before their bodies and comments were inspected. The frozen [2026-11-14 graph snapshot](../../results/snapshot.json) contained all three tasks but **zero reference/comment edges from them**. Public source discussion supplied important decision context in **all three** (15 comments total).

This is a **small, stratified and non-blinded coverage audit**, not a statistically representative study or evidence that the graph beats ordinary search. Indeed, opening the original issue and comments surfaced the same information without a graph. The result is a concrete gap in *what our graph makes available to a researcher*, not evidence of saved research time.

| Preselected task | Graph node / source edge coverage | Source-first decisive context | Appropriate decision |
| --- | --- | --- | --- |
| [#346: multilingual downstream evaluation](https://github.com/OpenEuroLLM/Taskboard/issues/346) | Task body; 0 task/comment edges | Three comments identify evaluator configuration and request corrected scores; one comparison still unchecked in the task body | Check existing corrected metrics before proposing another evaluation |
| [#341: DocHPLT dataset analysis](https://github.com/OpenEuroLLM/Taskboard/issues/341) | One-sentence task body; 0 edges | Six comments contain preprocessing decisions, alignment caveats and a completed whole-document-versus-sentence comparison | **Avoid duplicate analysis**; cite and inspect completed study |
| [#343: intra-job fault tolerance](https://github.com/OpenEuroLLM/Taskboard/issues/343) | Completed checklist in body; 0 edges | Six comments link the implementation, report recovery measurements and discuss queue time vs standby-node cost | **Do not reimplement**; assess queue/failure economics if there is a decision to make |

### E1 — Downstream evaluation #346

The [issue body](https://github.com/OpenEuroLLM/Taskboard/issues/346) marks four evaluation entries complete and leaves `nemotron models` on `dclm-core-22` unmarked. A [project comment](https://github.com/OpenEuroLLM/Taskboard/issues/346#issuecomment-4981280373) specifies prior multilingual results and an evaluation environment. A [later comment](https://github.com/OpenEuroLLM/Taskboard/issues/346#issuecomment-6317702798) requests corrected scores. We **do not know** whether a corrected result was subsequently shared outside the issue.

The linked CSV returned HTTP 404 through the connected GitHub access used for this audit; that is an *access limitation*, not evidence the data do not exist.

**Small action:** First verify the corrected score publication and remaining evaluation status, reusing established environment versions. Do not propose an identical evaluation from the task title alone.

### D1 — DocHPLT #341

The indexed graph body reads only: “Analyze how DocHPLT dataset is structured, and how should it be processed in datamix.” The actual issue is **closed**. Its public discussion includes:
- [Language-pair segmentation mismatch rates](https://github.com/OpenEuroLLM/Taskboard/issues/341#issuecomment-5000224012) reported by contributors;
- [A chosen document-truncation and context-window strategy](https://github.com/OpenEuroLLM/Taskboard/issues/341#issuecomment-5002140093);
- [Detailed comparative evaluations](https://github.com/OpenEuroLLM/Taskboard/issues/341#issuecomment-5176031327) of DocHPLT and FineOPUS, with a *reported* broadly similar downstream outcome.

**Small action:** Cite/reuse the existing experiment, verify comparability if a new use case arises. An apparent “missing dataset analysis” from the graph's bare issue body would be **false**.

### W1 — Fault tolerance #343

The task is **closed**, and [the linked implementation PR #48](https://github.com/OpenEuroLLM/oellm-autoexp/pull/48) is **merged**. The [technical comment](https://github.com/OpenEuroLLM/Taskboard/issues/343#issuecomment-4969902010) reports 33 seconds recovery time and 20 lost steps for one test configuration. The [later discussion](https://github.com/OpenEuroLLM/Taskboard/issues/343#issuecomment-5088871358) asks whether reserve nodes justify their cost versus queuing and chained-job priority on different clusters.

This is **not an unimplemented resilience feature**. The open decision is operational: expected completion latency, failure frequency and GPU-hours may favor different strategies. There is no single break-even answer without representative queue/failure data.

**Small action:** Make a cost-versus-delay comparison from actual cluster logs *only if* maintainers face this decision. Avoid changing established code or repeating comments.

## Why this matters for our original mission

The existing graph already has [a verified bounded comment collector](../../impact_enrichment.py), but the regular snapshot intentionally only collects comments for **10 fixed impact-study issues**. These three newly selected issues were outside that selection. We should not interpret “zero source-comment edges” as “no discussion.”

The smallest reusable addition is [`decision_comment_packet.py`](../../decision_comment_packet.py): a **manual, read-only on-demand command**, not a new crawler or service. It reuses `github_comments_for_selected` to fetch at most five selected indexed issues, stores source URLs, exact public texts and SHA256 checksums, states coverage limits, refuses existing output files, and does not infer collaboration, causality or duplicate work. [Tests](../../tests/test_decision_comment_packet.py) cover provenance, multiple issues, bounds and fail-closed errors.

PowerShell example (uses the current graph snapshot; requires GitHub API reachability, `GITHUB_TOKEN` optional for public access):

```powershell
python .\decision_comment_packet.py `
  --snapshot .\results\snapshot.json `
  --issue 'github:OpenEuroLLM/Taskboard#346' `
  --issue 'github:OpenEuroLLM/Taskboard#341' `
  --issue 'github:OpenEuroLLM/Taskboard#343' `
  --output .\results\decision_comments_20261115.json
```

**This run was not executed against GitHub by the new CLI in this conversation;** the source review used the connected GitHub API. A successful unit-test run demonstrates only code correctness on fixtures, not source accuracy or decision improvement.

## What still has not been proven

- No **blinded independent reviewer** compared resulting decisions.
- The graph and source-first pathways do **not** ingest the same comment context, so this is a **coverage diagnosis**, not a fair graph-vs-text quality claim.
- No human time saving, avoided GPU-hours or novel scientific discovery has been measured.
- These three cases do not represent the entire OpenEuroLLM backlog.
- A GitHub comment is a reported claim; it is not an independent experimental replication.

## Next evidence gate

1. Use on-demand comment packets for three **new** cases; give both graph-assisted and source-following reviewers the **same frozen original source content**.
2. Ask each to choose `already done`, `potential reuse`, `credible blocker`, or `abstain`, with quoted evidence, a falsification question and a smallest proposed action. Compare against a simple reader with the same input.
3. Only invest in broader semantic edge generation if this changes a real decision, not merely adds attractive connections.

Preserve the historical 2023-cutoff research-idea experiment as a **separate scientific discovery test**, not a substitute for demonstrating reliable decision support.
