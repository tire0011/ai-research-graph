# European AI contribution quality — first unblinded review (21 November 2026)

**Scope:** five candidates from the European discovery heuristic vs. five from the title-only lexical baseline over the **same 32 verified candidates**, from [GitHub Actions run 44890820839](https://github.com/tire0011/ai-research-graph/actions/runs/44890820839). There are **eight unique GitHub issues**. All eight issues and their available public comments were reopened. Detailed source-pinned labels are in [reviews.json](reviews.json).

> This is a manually judged, **non-blinded exploratory review**, not a controlled comparison against GitHub's real search API, a general precision estimate, or a finding that graph retrieval is better.

## Fixed ordinal rubric

- **0 — Not new:** already under way, existing solution offered, or a request for non-coding verification by maintainers.
- **1 — Uncertain:** a relevant problem with unclear maintainer direction, another contributor's proposed fix, or specialized infrastructure needed.
- **2 — Plausible:** reasonably scoped coding work with apparent public requirements, without verified maintainer approval.
- **3 — Confirmed:** maintainer explicitly welcomes external contribution and acceptance criteria are concrete.

## Five originally proposed by the discovery heuristic

| Issue | Tier | What the public evidence actually shows |
| --- | ---: | --- |
| [Kyutai pocket-tts #410](https://github.com/kyutai-labs/pocket-tts/issues/410) | 1 | Reproducible Spanish digit failure, but the author asks about a possible retrain or a *separate* normalizer; library implementation work is not yet agreed. |
| [Kyutai pocket-tts #345](https://github.com/kyutai-labs/pocket-tts/issues/345) | 0 | The issue author already produced ONNX exports, a validation pipeline and an offer to contribute; duplicating that work is not a new contribution. |
| [LAION CLAP #189](https://github.com/LAION-AI/CLAP/issues/189) | 0 | Request to check Papers with Code evaluation metadata, not a scoped engineering task for an outside developer. |
| [LAION CLIP_benchmark #147](https://github.com/LAION-AI/CLIP_benchmark/issues/147) | 1 | The reporter describes a possible squeeze-based fix and offers a PR; first ask whether they are still working on it. |
| [OpenEuroLLM Taskboard #451](https://github.com/OpenEuroLLM/Taskboard/issues/451) | 0 | Four large SFT ablations are **already queued** after tokenization. HPC execution is not a newly available task. |

**0/5** met tier 2 or 3. The original ranking found open technical discussions but no clearly new, externally actionable top-five task.

## Five in the same-pool title-only baseline

| Issue | Tier | What the public evidence actually shows |
| --- | ---: | --- |
| [LAION CLIP_benchmark #147](https://github.com/LAION-AI/CLIP_benchmark/issues/147) | 1 | As above: reporter has a proposed fix. |
| [OpenEuroLLM oellm-eval #165](https://github.com/OpenEuroLLM/oellm-eval/issues/165) | 1 | Missing sample logging for `evalchemy`; work may require upstream backend changes and needs scope/acceptance confirmation. |
| [OpenEuroLLM post-training #35](https://github.com/OpenEuroLLM/post-training/issues/35) | 2 | Three concrete logging goals: save YAML, include config in output, log only from rank 0. Plausible external code contribution, **not** accepted by maintainers. |
| [OpenAIRE IIS #1602](https://github.com/openaire/iis/issues/1602) | 1 | Replace Airflow transformer integration workflows with Spark unit tests; substantial specialized environment and migration work. |
| [LAION CLAP #189](https://github.com/LAION-AI/CLAP/issues/189) | 0 | As above: request to verify public evaluation records. |

**1/5** met tier 2 or 3. **0/10** selection slots had verified maintainer invitation. These small, non-independent numbers are a direction for improving the workflow, not scientific evidence of ranking quality.

## Engineering consequence

Instead of changing scoring weights to fit these eight examples (overfitting), retain all original proposals and attach an **auditable manual readiness layer**:

1. Source review includes issue URL, issue update timestamp, **comment count**, rationale, and citations.
2. Reviews **expire automatically** if source timestamp or comment count changes; a live GitHub follow-up state always overrides them.
3. The workflow separates *plausibly scoped / human reviewed* from *untested new items*; neither is advertised as maintainer-approved.
4. Keep the lexical baseline exactly as it was, so a future blind test can compare against plain GitHub search on fresh unseen issues.

**Next experimental gate:** freeze a new independent sample and a precise developer query, ask someone not shown the model rankings to rate whether the task is actually externally implementable, and compare **real GitHub Search API results** with the existing heuristic and graph-assisted retrieval. Until demonstrated, do not market this as a graph advantage.
