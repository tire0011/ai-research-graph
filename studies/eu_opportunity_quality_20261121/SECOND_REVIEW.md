# Second source-backed quality review — 19-repository EU pilot

Review date: **21 November 2026**. Input: [European AI discovery run 44912578063](https://github.com/tire0011/ai-research-graph/actions/runs/44912578063), which sampled 173 open issues across 19 repositories and checked 50 candidate issues. No collection errors.

**Review protocol:** five previously unreviewed new candidates from the enlarged 19-repository sample, checked against their original issue bodies and visible comments. Judgments are from one non-blinded reviewer. This is **not** added to the earlier [five-versus-five comparison](REVIEW.md); the source population changed. The source timestamps, comment counts, and reasons are frozen in [reviews.json](reviews.json) under `additional_cohorts`.

| New candidate | Tier | Source-backed observation |
| --- | ---: | --- |
| [OpenEuroLLM/JudgeArena #67](https://github.com/OpenEuroLLM/JudgeArena/issues/67) | **0** | The author states that most leaderboard work already exists on `feat/live-leaderboard` and `feat/leaderboard-hf-space`. The discussion is about choices for existing implementation, not a free build-from-scratch task. |
| [Pleias/Pleias-RAG-Library #18](https://github.com/Pleias/Pleias-RAG-Library/issues/18) | **0** | An external audit vendor is seeking feedback or paying customers; not a request to contribute code to Pleias. |
| [kyutai-labs/hibiki #19](https://github.com/kyutai-labs/hibiki/issues/19) | **1** | A proposed README tidy-up whose author offers to submit a PR. The maintainer has not explicitly requested an independent contributor for the same work. |
| [OpenEuroLLM/JudgeArena #24](https://github.com/OpenEuroLLM/JudgeArena/issues/24) | **2** | A reasonable implementation request to add SGLang beside vLLM; a maintainer says it would be useful but notes that LangChain integration may need a custom wrapper. Requires inference-backend knowledge and tests, with no external contributor approval yet. |
| [OpenEuroLLM/JudgeArena #128](https://github.com/OpenEuroLLM/JudgeArena/issues/128) | **0** | Detailed cache architecture is already under discussion with related draft PRs; do not treat existing cache work as untouched. |

**Result:** 1/5 is a *plausible* engineering contribution (tier 2), **0/5 maintainer-confirmed** (tier 3). The other four require clarification or have already attracted the very contributions the graph should help people find.

## Scientific and product decision

We are still discovering discussions, not reliably discovering **unclaimed, useful engineering contributions**. The correct next experiment is not more keyword tuning. Instead:

1. Require a record of *what work remains*, whether prior implementation exists, and **who has already offered to do it**.
2. Distinguish research tasks needing HPC or original team access from locally testable work.
3. Ask an independent contributor/maintainer to evaluate a new unseen batch with an explicit task profile and acceptance criteria.
4. Run a real GitHub Search API retrieval baseline on the same scope and query. The existing title-only baseline only ranks preselected candidates.

The extra five rows are an **additive qualitative cohort**. They must not modify the original eight-issue frozen comparison. Both cohorts remain read-only and become stale if the original GitHub issue update time or comment count changes.
