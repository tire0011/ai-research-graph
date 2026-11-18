# DeepEval as an optional PR-opportunity judge

Decision (2026-11-18): **Use a deterministic evidence gate first; DeepEval only for subjective proposal quality.** No LLM judge can establish whether a linked PR exists, whether a bug reproduces, or whether maintainers welcome a contribution. These must be independently verified.

## Implementation
- `pr_opportunity_gate.py`: stdlib-only gate. Requires HTTPS evidence URLs for problem, reproduction, code location, expected impact and maintainer signal; rejects existing PRs, private-resource dependencies and missing explicit maintainer approval. A URL is a pointer, **not** verified evidence. Manual review is still required.
- `deepeval_pr_opportunity.py`: optional GEval on the proposal after the gate passes. A judge score is not a merge probability or factual validation.
- `tests/test_pr_opportunity_gate.py`: offline tests.

## PowerShell
```powershell
python -m unittest discover -s tests -p test_pr_opportunity_gate.py -v
python .\pr_opportunity_gate.py .\candidates.json
# Optional only after evidence validation; judge may use a paid API:
python -m pip install deepeval
python .\deepeval_pr_opportunity.py .\candidate.json
```

Example `candidates.json`:
```json
[{"title":"Example issue","evidence":{"problem":"https://github.com/example/repo/issues/1"},"scores":{"reach":2}}]
```
Output should be `investigate`, not `ready_for_pr`. Score coverage shows which dimensions are unknown. The weights are exploratory, not learned or calibrated.

## Research next step
Collect 20-30 historical PRs, label accepted/declined/ignored and independent downstream evidence, and compare rankings with/without the optional judge. Track calibration and false-positive suggestions. Do not train on post-outcome evidence when retrospectively predicting success.

DeepEval docs: https://deepeval.com/docs/metrics-llm-evals
