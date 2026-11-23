# Research opportunity discovery — human review

**Read-only experiment. No messages were sent.** Mentions are evidence for triage, not proof of a performance gain, confirmed blocker, or available contributor.

Sample: **50** ID-selected open issues out of **210** open issues, excluding **10** original cases. Seed: 2026-W48. Source re-reads: **50**.

Found **2** source-linked review cards across **1** issues. No automatic impact ranking.

## Up to five new, unclaimed review candidates

None in this sample passed the public state checks. This is not proof that no work exists.


## All source-backed candidates and dispositions

## [211: Qwen3 30B-A2B weak and strong scaling](https://github.com/OpenEuroLLM/Taskboard/issues/211)

- Signal: performance_mention — literal source mention; claim not independently verified
- Required verification: Reported performance phrase, not an independently reproduced gain; request comparable measurements.
- Manual feedback state: new
- Opportunity state: **in_progress** (issue_assigned_activity_unconfirmed)
- State evidence: https://github.com/OpenEuroLLM/Taskboard/issues/211
- Suggested contact (not notified): @Vmjkom, @tvosch, @ibaucells (github_assignee)
- Stable ID: github:OpenEuroLLM/Taskboard#211:performance_mention
- Source excerpts:
  - [issue_comment](https://github.com/OpenEuroLLM/Taskboard/issues/211#issuecomment-6057044334): at 16 / 32 nodes. BF16 is 3–5% faster than FP8 and uses less memory per GPU (e.g. 0.890 vs 0.915 at 8 (SHA256 09bffacb0b3f66f96448becb71a07e5ac9b6b2cb29b43c3a84b3e522d024d191)

## [211: Qwen3 30B-A2B weak and strong scaling](https://github.com/OpenEuroLLM/Taskboard/issues/211)

- Signal: reported_memory_issue — literal source mention; claim not independently verified
- Required verification: Reported memory difficulty; reproduce it and locate the failure phase.
- Manual feedback state: new
- Opportunity state: **in_progress** (issue_assigned_activity_unconfirmed)
- State evidence: https://github.com/OpenEuroLLM/Taskboard/issues/211
- Suggested contact (not notified): @Vmjkom, @tvosch, @ibaucells (github_assignee)
- Stable ID: github:OpenEuroLLM/Taskboard#211:reported_memory_issue
- Source excerpts:
  - [issue_comment](https://github.com/OpenEuroLLM/Taskboard/issues/211#issuecomment-6211454878): nces the work across pipeline stages. **Did not fit in 64 GB** (OOM in the first iteration): - TP1, VPP 6, no recompute, MBS 4 and M (SHA256 294b1bf0e973ad0a928090be8ac14c9d20a9870e9a0925d6dae32cecc6cbeae4)

## Limitations

Deterministic, weekly rotating 50-issue sample of currently open tasks; heuristic text triage only, not verified impact or a project-wide ranking. Cross-referenced PRs and assignees indicate possible activity, not a fix. Only a bounded timeline is checked; absence of a PR is not proof none exists. New means unclaimed in observed public evidence, not maintainer-approved. Human review required before communication; no posts sent.

Feedback is human-entered, not automatically verified against GitHub. Absence from a rotating sample does not indicate an issue is resolved.
