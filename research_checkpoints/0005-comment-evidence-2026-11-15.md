# Research checkpoint 0005 — Comments carry research outcomes

- **Date:** 2026-11-15
- **Type:** Preselected decision-study result / coverage gap / small tooling response
- **Extends:** [Checkpoint 0004](0004-link-correctness-2026-11-14.md)
- **Original research mission:** avoid duplicated effort, find high-leverage changes, connect complementary work, and eventually generate falsifiable cross-disciplinary hypotheses
- **Selection frozen before reading case bodies:** [Selection protocol](../studies/decision_pilot_20261115/SELECTION.md)
- **Observed results:** [Study report](../studies/decision_pilot_20261115/RESULTS.md) and [structured evidence](../studies/decision_pilot_20261115/RESULTS.json)
- **Status:** Small non-blinded coverage study; not a proven graph-vs-search performance gain

## What changed

Across three title/metadata-selected issues (#346, #341, #343), the graph snapshot held the task body but had **zero source-comment links** for each. Direct GitHub source-following revealed a total of **15 public comments**, with decision-changing information in all three.

- **#346:** One downstream evaluation is unchecked and a comment requests corrected scores. The smallest action is verify completion/correction; no duplicate experiment should be proposed.
- **#341:** A one-line indexed task hides a completed DocHPLT versus FineOPUS comparison in comments. The task is closed; a new generic analysis would risk duplicating research.
- **#343:** The task is closed and associated PR #48 merged. The remaining open question in discussion is whether spare nodes are economically preferable to queuing/restart, which depends on measured conditions. A new implementation is not justified.

## Foundational lesson

**Our graph must preserve the evolution from proposed task → experiment → observed result → unresolved decision.** An issue title or static body alone may be too early a checkpoint. Comments and linked PRs can contain decisive evidence, including unexpected null results and important economic tradeoffs.

This does **not** mean adding every mention as an actionable graph edge, automatically declaring collaboration, or broadening crawling without proof. The existing `impact_enrichment.github_comments_for_selected` collector already supplies attributable, bounded, SHA256-hashed public comment records. A small [manual on-demand tool](../decision_comment_packet.py) reuses it for selected research decisions rather than creating a new service; it does not make causal or cost claims.

## How it relates to the bigger research idea

- Detect duplicate research: **#341** is a concrete example of an apparently unstudied question that was actually answered.
- Find high leverage: **#343** directs effort away from writing code and toward measuring whether existing resilience features make economic sense.
- Coordinate without duplication: **#346** points to existing evaluations and pending result correction instead of sending another generic benchmark suggestion.
- Discover novel hypotheses: **not yet tested**; historical 2023-cutoff protocol remains separate, with leakage risk.
- Preserve learning: this checkpoint extends earlier goals without replacing them.

## Limits and next test

A standard GitHub issue-plus-comments read found this context just as well. The pilot is too small for population claims; the modes were not independently blinded and did not have equal comment-source coverage. No actual research speedup, independently reproduced improvement or cost saving was measured.

**Next:** compare graph-assisted and source-following decisions on the **same frozen original evidence packets**, with a separate reviewer where possible, before creating semantic “duplicate” or “high-value” edges. If ordinary source-following does as well, keep the simpler route. Store all negative findings and confirmed decisions as further versioned checkpoints.

No messages or code changes were made to OpenEuroLLM repositories.
