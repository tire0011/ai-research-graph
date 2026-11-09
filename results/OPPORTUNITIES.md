# Research opportunities for human review

**Read-only pilot.** Every finding is derived from the independent ten-issue impact audit. No GitHub messages, labels or notifications have been sent. Selection is not a project-wide ranking or a verified acceleration.

Examined **10** purposefully sampled issues; **3** evidence-triggered proposals.

## [github:OpenEuroLLM/Taskboard#385](https://github.com/OpenEuroLLM/Taskboard/issues/385) — Train and export the OELLM 9B function-calling SFT checkpoint on LUMI

- Evidence: `reported_speedup_pending_validation` (reported, not reproduced).
- Proposed action: Validate the revised sequence-to-worker assignment before production adoption.
- Required verification: Reproduce throughput and complete the pending memory, save and resume acceptance checks.
- Public contact: @ReinforcedKnowledge (`github_issue_assignee`; please confirm the appropriate person).
- Suggested channel: [existing issue](https://github.com/OpenEuroLLM/Taskboard/issues/385); **human approval required before any outreach**.
- Draft question for review: Would a reproducible check help? Reproduce throughput and complete the pending memory, save and resume acceptance checks.
- Original-source evidence:
  - [106–107k tokens/s](https://github.com/OpenEuroLLM/Taskboard/issues/385) (SHA256 `4a7887b689cbdc129280936e03a9a1684aaabf7c5b42deaf375b4f6039151ffc`)
  - [about 9.5% faster](https://github.com/OpenEuroLLM/Taskboard/issues/385) (SHA256 `4a7887b689cbdc129280936e03a9a1684aaabf7c5b42deaf375b4f6039151ffc`)
  - [remain required before adoption](https://github.com/OpenEuroLLM/Taskboard/issues/385) (SHA256 `4a7887b689cbdc129280936e03a9a1684aaabf7c5b42deaf375b4f6039151ffc`)

## [github:OpenEuroLLM/Taskboard#391](https://github.com/OpenEuroLLM/Taskboard/issues/391) — Ensuring post-training pipeline works

- Evidence: `explicit_upstream_dependency` (author-declared, not proven blocking).
- Proposed action: Complete LlamaFactory support so a same-configuration TRL throughput comparison can be run.
- Required verification: Verify Taskboard #432 completion, then benchmark comparable SFT/DPO configurations on LUMI.
- Public contact: @Neonkraft (`github_issue_assignee`; please confirm the appropriate person).
- Suggested channel: [existing issue](https://github.com/OpenEuroLLM/Taskboard/issues/391); **human approval required before any outreach**.
- Draft question for review: Would a reproducible check help? Verify Taskboard #432 completion, then benchmark comparable SFT/DPO configurations on LUMI.
- Original-source evidence:
  - [Compare throughput against the existing TRL implementation](https://github.com/OpenEuroLLM/Taskboard/issues/391) (SHA256 `3a88d7745a1405179ae3646bdb738d356f40a27cc7a55bb01974b366af19879f`)
  - [__Dependencies__ Issue #432](https://github.com/OpenEuroLLM/Taskboard/issues/391) (SHA256 `3a88d7745a1405179ae3646bdb738d356f40a27cc7a55bb01974b366af19879f`)
- Author-declared upstream task: `github:OpenEuroLLM/Taskboard#432`.

## [github:OpenEuroLLM/Taskboard#433](https://github.com/OpenEuroLLM/Taskboard/issues/433) — Add support for FSDP to TRL in the post-training repo

- Evidence: `reported_memory_blocker` (commenter-reported, not reproduced).
- Proposed action: Find a feasible LUMI DPO configuration for the FSDP branch.
- Required verification: Confirm reproducible OOM and a successfully completed equivalent DPO run; measure throughput only afterward.
- Public contact: @Neonkraft (`github_issue_assignee`; please confirm the appropriate person).
- Suggested channel: [existing issue](https://github.com/OpenEuroLLM/Taskboard/issues/433); **human approval required before any outreach**.
- Draft question for review: Would a reproducible check help? Confirm reproducible OOM and a successfully completed equivalent DPO run; measure throughput only afterward.
- Original-source evidence:
  - [Add support for Fully Sharded Data Parallel](https://github.com/OpenEuroLLM/Taskboard/issues/433) (SHA256 `1f43adea95275eb9448196b61d1de53bf44fd8ebccd21686f35d24cf8ce81a9a`)
  - [fails due to OOM issues on LUMI](https://github.com/OpenEuroLLM/Taskboard/issues/433#issuecomment-6121054773) (SHA256 `5b1619a14f239f8e4d4785adae8935c53ee01a08147fb7d00debbb485216a13b`)

## Boundaries

Not project-wide, not independently measured speedups; no automated outreach
Source evidence is attributed to issue authors/commenters; its scientific claims remain unverified.
