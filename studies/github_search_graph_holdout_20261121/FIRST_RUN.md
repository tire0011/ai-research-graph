# First real GitHub Search versus graph-context holdout — negative finding

Executed: **2026-11-21**. Original frozen queries and source cohort: [config.json](config.json).
Original GitHub Actions run: https://github.com/tire0011/ai-research-graph/actions/runs/44929754369

## Actual read-only result

- **8 actual REST GitHub issue searches** across 19 curated EU-AI-related repositories and the frozen `bug` / `test` terms.
- **52 distinct public issues** returned in the deterministic, stratified API pool; **5** previously reviewed issue URLs excluded from the evaluated queue.
- **20** held-out issues considered in both methods; **16** passed all bounded source-context checks, **4** were conservatively quarantined because their verification did not complete.
- Native stratified GitHub Search returned its first **five** (not automatically actionable).
- Context-enriched triage returned only **one** apparently new, non-HPC-blocked candidate: [Kyutai pocket-tts #229](https://github.com/kyutai-labs/pocket-tts/issues/229).
- **Direct review overturned that candidate.** [A repository collaborator explicitly said the streaming WAV header behavior is intentional and they do not intend to address it](https://github.com/kyutai-labs/pocket-tts/issues/229#issuecomment-5091614084). A following commenter accepted the recommended Python workaround.
- No confirmed useful, maintainer-welcomed task was identified by the graph-context arm. **No graph advantage has been demonstrated.**

## Methodological correction, not an invisible retune

The original JSON and blind-review artifact remain attached to the original workflow run. We do **not** rewrite those historic outputs, accept a graph winner, or claim a successful code location. Instead, add a narrowly grounded [opportunity-state](../../opportunity_state.py) rule for **explicitly declined work in a GitHub comment authored by an OWNER/MEMBER/COLLABORATOR**. Unverified comments or unprivileged comments cannot determine maintainer intent.

After the fix, new live runs use the corrected state classifier. They are sensitivity/recheck runs after observing a failure, **not a new untouched blind holdout**. The initial test configuration and frozen source list are unchanged.

## Next controlled research step

This study mainly tests filtering/ranking of *GitHub-search-returned* issues, not the core hypothesis of finding **new cross-project opportunities by traversing the OpenAIRE/Hugging Face/scientific graph**. A meaningful next experiment should generate candidates from **cross-repository, source-verified relationships not retrieved by the original query**, then compare with a much stronger, query-equivalent GitHub Search baseline. Independent method-blinded reviewers must assess actual remaining work, existing code/PRs, resource fit, and maintainer readiness. Until then, treat the graph as exploratory evidence-mapping only.
