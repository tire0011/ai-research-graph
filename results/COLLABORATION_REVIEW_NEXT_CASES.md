# Expanded human review — second set of candidate connections

**Status:** hypotheses requiring human verification, not demonstrated novel
collaborations. No outreach or automatic tagging. On 2026-11-10 an exploratory
11-repository probe covered 1,401 issues/PRs and 309 recent active sources;
there were many false lexical matches. This is not a precision measurement.
The [expanded source registry](../collaboration_expanded_sources.json) lets the
scan be reproduced without changing production matching.

## 1. Complementary: 256k context extension ↔ task-specific tests

- **Need:** [OpenEuroLLM Taskboard #392](https://github.com/OpenEuroLLM/Taskboard/issues/392)
  is **open**, assigned to `luomajouni`, and asks to extend the final Prelude
  checkpoint to **256k** with a Needle-In-A-Haystack deliverable. A comment
  reports the extension started on LUMI, subject to HPC queues.
- **Existing work:** [AllenAI olmo-eval PR #358](https://github.com/allenai/olmo-eval/pull/358)
  is **merged** and adds `StateBench` long-context *state tracking* with
  2k–1m length buckets and 10% fast-run variants. [PR #372](https://github.com/allenai/olmo-eval/pull/372)
  is also **merged**, bringing LongBench v2 with pinned datasets and separate
  development/held-out scores.
- **Possible handoff:** test Prelude's 256k checkpoint with a small StateBench
  subset (e.g. 128k/256k strata) in addition to Needle-In-A-Haystack. This
  measures state tracking rather than only retrieving a hidden item.
- **Third-party component:** the dataset behind LongBench v2 is
  [`zai-org/LongBench-v2`](https://huggingface.co/datasets/zai-org/LongBench-v2);
  it is an *existing upstream dependency*, not evidence of a newly discovered
  organizational link.
- **Before suggesting contact:** check whether the Prelude evaluation runner
  can consume olmo-eval tasks, whether the 256k input actually fits and whether
  the team already runs equivalent state-tracking tests. The Taskboard issue
  itself mentions Needle-In-A-Haystack but not StateBench; this is not proof
  the team has never discussed it elsewhere.
- **Public coordination sampled:** authors, assignees and issue commenters in
  the two linked threads show no shared GitHub login; their displayed issue
  bodies and issue comments contain no direct reference to the other repo.
  Other PR review discussions, private channels and offline collaboration
  were **not** checked.

**Review label:** `complementary` **hypothesis**; strongest concrete second
candidate so far, not an established transfer.

## 2. Similar domain, different deliverables: Arena-Hard v2

- [AllenAI olmo-eval PR #474](https://github.com/allenai/olmo-eval/pull/474),
  **merged**, implemented Arena-Hard v2 pairwise judging, style-controlled
  scoring, reproducible fixed judge and dataset revisions.
- [OpenEuroLLM oellm-eval PR #174](https://github.com/OpenEuroLLM/oellm-eval/pull/174),
  **open**, adds `collect --exclude_samples` to remove contaminated evaluation
  battles and recompute *supported* JudgeArena win-rate scores, including
  Arena-Hard, with explicit caveats for unsupported ELO/confidence intervals.
- Both use Arena-Hard but solve *different evaluation lifecycle steps*.
  Calling the code duplicate would be misleading. A possible handoff is the
  **contamination/exclusion contract**, if AllenAI wants post-hoc exclusions
  and its task result format can support them. No confirmed need on AllenAI's
  side is visible in these two PRs.
- [Arena-Hard-Auto](https://github.com/lmarena/arena-hard-auto) is an existing
  external benchmark used by the AllenAI implementation. Its existence does
  not mean that the two maintainer teams are already collaborating.
- **Public coordination sampled:** there are no shared issue authors or
  issue commenters, and no direct cross-repo reference in the inspected issue
  bodies/comments. This does not establish that no private coordination exists.

**Review label:** `shared_problem` until an explicit reusable artifact and
receiver requirement are verified; **do not reach out** on this evidence alone.

## 3. Existing earlier model-card candidate

- [OpenEuroLLM Taskboard #445](https://github.com/OpenEuroLLM/Taskboard/issues/445)
  requires automated model-card evaluation reporting.
- [LAION CLIP_benchmark #153](https://github.com/LAION-AI/CLIP_benchmark/issues/153)
  proposes optional audit/provenance metadata for a benchmark run.
- A cross-project compatibility **question** was posted by the user on
  [#445](https://github.com/OpenEuroLLM/Taskboard/issues/445#issuecomment-6773062235).
  The LAION proposal is not evidence of an available implementation; do not
  claim this is already integrated or novel collaboration.

**Review label:** `complementary` proposal, awaiting any owner response.

## What counts as success?

Record separately: (a) candidate retrieval, (b) independently confirmed
technical handoff, (c) absence/presence of *known* prior coordination,
(d) maintainer interest, (e) actual reuse/outcome. So far only (a) and portions
of (b)'s source verification have been performed for these new examples.

Run the [review protocol](../COLLABORATION_REVIEW_PROTOCOL.md) on subsequent
candidates, including negative controls. Never treat a shared keyword as a
dependency or a missing public link as proof two people have not collaborated.
