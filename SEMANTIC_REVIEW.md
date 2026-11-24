# Semantic evidence review — experimental pilot

The rule-based graph supplies candidate pairs; the semantic evaluator collects two bounded GitHub README excerpts, sends a fixed evidence packet to a selected model, and validates the JSON response against exact evidence quotations. No model-directed network requests, tool calls, outreach, adapter execution or graph-edge promotion. An exact quotation is not proof of entailment; the claims and verdict require human review. Papers, issues, dataset/model cards, independent counter-evidence retrieval, reviewer-model comparison, persistent deduplication and semantic graph ingestion are follow-ups, not implemented in this increment.

## Local comparison (Windows PowerShell)

Start your existing llama.cpp OpenAI-compatible server with Ornith-1.5-9B, listening on loopback. Use the model name exposed by its API; JSON mode must be supported by the runtime.

```powershell
python semantic_review.py --cases studies/semantic_review_pilot/cases.json --provider local --model Ornith-1.5-9B --local-url http://127.0.0.1:8080/v1 --output results/ornith
```

If the model fails to return valid evidence-linked JSON, record the failure; do not silently repair or count it as agreement. The local provider never receives the Mistral key.

## Mistral

Create an API key in Mistral Studio. Use a dedicated project/workspace with a spending limit. In the repository's Settings > Secrets and variables > Actions, add the repository secret `MISTRAL_API_KEY`. Do not commit or paste the key into logs or issues.

Optional Actions variable `SEMANTIC_REVIEW_MODEL` (default `mistral-small-latest`). Prefer a dated model ID when comparing runs. On the Actions tab run **Semantic evidence review** on main with mode `calibration`. Download the result artifact. Mode `discovered` uses the latest published source-triage snapshot. Set `SEMANTIC_REVIEW_ENABLED=true` only after reviewing the first manual run; that enables a weekly Wednesday cloud review, independently of the Tuesday source discovery. The workflow uses GitHub-hosted runners, never calls Mistral on PRs, and caps each run to five requests (1800 output tokens each, no automatic retry). Billing depends on the account and model. No secrets or paid calls are needed for offline tests.

For local Mistral testing use the environment variable `MISTRAL_API_KEY` and run:

```powershell
python semantic_review.py --cases studies/semantic_review_pilot/cases.json --provider mistral --model mistral-small-latest --output results/mistral
```

## Evaluation

Three provisional calibration examples are provided: LAION/AURA (plausible experiment), LAION/Sphinx documentation theme (negative control), and a deliberately title-only ablation. The expected labels are hidden from the model. The report records validated format, quotation presence, provisional agreement, model version, usage and evidence hashes. These are not a ten-case independent benchmark or measured model-quality results. Expand to independently reviewed, unseen positive/negative cases before selecting a model or claiming value. Compare against simple keyword triage and measure useful experiments, false-positive claims, abstentions, latency and cost. Review actual reasoning claims rather than optimizing only the label agreement.

The API key and local model are not configured by this PR. No live model call has been performed. The pilot is opt-in.
