# High-impact PR opportunity scan — 2026-11-18

## Purpose
Restore the original Research Graph mission: find small, evidence-backed contributions that unblock many downstream users, without GPU/HPC access. **Do not create speculative PRs.** Treat the graph as a decision instrument rather than a research topic.

## Scoring rubric (provisional; not objective impact)
Score each criterion 0–3: downstream reach, verified bottleneck, feasibility without private resources, ownership gap, testability. Penalize overlap with existing PRs and lack of maintainer interest. Unknown != zero: report evidence gaps. Rank only after checking linked issues, PRs, source files, and maintainer feedback.

## Initial public issue candidates (not yet confirmed PR opportunities)
| Candidate | Evidence | Risk / blocker | Next validation |
|---|---|---|---|
| [Taskboard #441](https://github.com/OpenEuroLLM/Taskboard/issues/441) large-scale experiment progress tracker | Public issue explicitly requests consolidating cross-HPC progress, fixing false user attribution, documenting HPC and data mix, testing new runs and README. Broad potential value to experiment monitoring. | Assigned to sam-laing and dianaonutu; may need HPC data, implementation may already exist. | Inspect linked tracker repository, source and existing PRs; find a reproducible attribution bug or public-data-only test; ask maintainers before overlapping work. |
| [Taskboard #445](https://github.com/OpenEuroLLM/Taskboard/issues/445) model-card eval reporting | Explicit need for script generating tables/plots from HF eval dataset. Could remove repeated release work. | Assigned to spyysalo and geoalgo; likely already underway. | Read issue comments, existing scripts and related PRs; identify narrow missing test or reproducibility fix. |
| [Taskboard #450](https://github.com/OpenEuroLLM/Taskboard/issues/450) HF vs vLLM evaluation | Real benchmark numbers and incomplete matched 1,024-token runs; performance decisions affect eval costs. | Assigned; remaining work depends on LUMI allocation. | Look at oellm-eval #152 and PR #164 for a code-only correctness/reproducibility issue; avoid redoing benchmark without HPC. |
| [Taskboard #443](https://github.com/OpenEuroLLM/Taskboard/issues/443) Prelude evaluation collection | Most steps complete, remaining runs on MN due to LUMI queue. | 22 comments, multiple assignees, requires HPC; poor fit for local PR. | Do not pursue unless a public data-validation bug is found. |
| [Taskboard #349](https://github.com/OpenEuroLLM/Taskboard/issues/349) PDF extraction pipelines | Potentially high downstream impact for training-data quality. | Benchmark datasets on LUMI, assigned, 19 comments; large scope. | Only pursue narrow public sample + test if maintainer confirms gap. |

## Decision
**First investigate #441**, then #445, but do not write a PR until a distinct, reproducible defect and maintainer appetite are demonstrated. This is an evidence triage, not an assertion of likely acceptance. Existing user PRs may have low response rates; favor clear ownership, narrow scope, a failing test, and measured impact.

## Research Graph product loop
1. Discover active issues and related PRs across repos.
2. Link evidence: issue -> dependency -> implementation -> test -> owner -> public status.
3. Flag duplicates, blockers, stale promises and untested assumptions.
4. Estimate leverage and feasible contribution size with uncertainty.
5. Produce a one-page **PR opportunity brief**: problem, evidence URLs, exact code surface, reproducible failure, expected downstream effect, maintainer/overlap status, stop condition.
6. Only then propose or implement a PR, never automatically merge/post.

## Parking lot
LoRA language-recipe experiment is **paused by user choice**. Keep existing exploratory scripts as an optional branch artifact; no training or additional work unless explicitly requested.
