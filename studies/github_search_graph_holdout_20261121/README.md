# Registered GitHub Search API versus graph-context holdout

Date frozen: **2026-11-21**. Code: [`github_search_graph_holdout.py`](../../github_search_graph_holdout.py), preregistration: [`config.json`](config.json).

## Decision question

> Where can an outside Python/software developer without HPC access spend 2–6 hours improving open European AI evaluation/data software, with an independently testable contribution?

The scope is **the same 19 public EU-AI-related repositories** used by our prior pilot, not all Europe. GitHub searches `bug` and `test` are made through the **real REST `GET /search/issues` endpoint** across four explicitly scoped groups of repositories, exactly as preregistered. Each query takes up to eight results in GitHub relevance order, with deterministic round-robin pooling, deduplication and up to 20 new issues for deeper analysis.

## Two actual arms

- **A — GitHub Search API baseline:** first five unique, previously *unreviewed* issues from the stratified native issue-search result order; no other information is used to rank A.
- **B — graph-context-enriched triage:** exactly the same set of up to 20 issues. Re-fetch live issue, all current comments (bounded), and issue timeline; check cross-referenced PRs (same-repo activity vs mere cross-repository mention), resource blockers and source version; inspect literal GitHub, Hugging Face and DOI/arXiv references; and confirm up to two cited code paths in the repository. Produce five ranked **candidates for human review**, not maintainer-approved tickets.

**Important:** B is presently a typed **GitHub-context overlay** on a Graph project, **not** a query traversing the OpenAIRE research graph or a general cross-project dependency graph. Literal references are context edges, **not verified reuse, causal dependencies or exact source-of-fix locations**.

## Method and evidence controls

- Historical review URLs are excluded **without using historical labels or ratings**; no scoring weights are trained on them.
- The input repo list, query terms, per-query cap, top-k, and budget are frozen in the config file before observing holdout labels.
- Both methods compete on the **same collected pool**. A's initial ranking costs fewer API calls; B's extra calls and latency must be reported before proposing an operational system.
- Any changed source, partial comment pagination or invalid PR context prevents B from declaring a candidate reviewed.
- A deterministic **method-blind review sheet** hides which method proposed each union-of-top-five issue. Human reviewers must inspect the original issue and related code and give each a 0–3 rating and a reason.
- The experiment **cannot claim a winner until all source reviews are complete**. A complete `judge()` call then reports within-sample plausible tasks at five; it is not a general performance estimate, and no user effort saved has been measured.
- No external issue/PR creation, notifications, assignments, code execution or private source access.

## Reproduction

```powershell
python -m unittest discover -s tests -v
python github_search_graph_holdout.py --config studies/github_search_graph_holdout_20261121/config.json --registry eu_opportunity_sources.json --ledger studies/eu_opportunity_quality_20261121/reviews.json --output results/github_search_graph_holdout
```

The separate GitHub Actions workflow `.github/workflows/github-search-graph-holdout.yml` runs offline tests on PRs and a read-only live query after merging to main, preserving `comparison.json`, `COMPARISON.md` and `method_blind_review_template.json` as downloadable workflow artifacts.

## Interpretation

If A equals or outperforms B, *do not* invent a graph benefit. Instead, investigate why link evidence or assumed resource fit did not help. If B wins on blinded source-rated tasks, validate on a second independent batch with updated repos and developer profiles before making public claims. Even a win on this restricted same-pool test would **not** demonstrate improved retrieval recall or cross-platform scientific collaboration yet.
