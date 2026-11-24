# Semantic evidence review — experimental pilot

The existing rule-based graph supplies candidate pairs. The evaluator collects bounded public GitHub README excerpts, divides exact source text into deterministic sections, and sends only the evidence packet to the selected model. Claims cite section IDs (e.g. `e1:s001`) instead of repeating quotes. Each section has offsets and original text, and each document carries its revision and SHA-256 of the supplied excerpt. IDs are stable for the same evidence snapshot, not across changed versions. The artifact resolves references through its packet. Reference existence does **not** prove entailment, truth, or cooperation. No model-directed network requests, tools, outreach, adapter execution or graph-edge promotion.

## Local comparison (Windows PowerShell)

Run a loopback OpenAI-compatible server (for example llama.cpp with Ornith-1.5-9B) and use its advertised model ID:

```powershell
python semantic_review.py --cases studies/semantic_review_pilot/cases.json --provider local --model Ornith-1.5-9B --local-url http://127.0.0.1:8080/v1 --limit 3 --output results/ornith
```

The local server never receives the Mistral key. Invalid responses are not silently repaired.

## GitHub Actions / Mistral

Use a dedicated Mistral project with a spending limit. Set repository secret `MISTRAL_API_KEY` and optionally Actions variable `SEMANTIC_REVIEW_MODEL` (default `mistral-small-latest`, prefer a dated ID for reproducibility). In Actions > Semantic evidence review, choose Run workflow on main:
- `calibration`: original 3 cases, directly comparable with previous pilot.
- `benchmark`: explicit manual opt-in, 20 cases, at most 20 requests.
- `discovered`: latest source-triage snapshot, at most 5 requests.

Schedule remains opt-in via `SEMANTIC_REVIEW_ENABLED=true`; scheduled discovery reviews retain the five-call cap. PRs run offline tests only. Requests are bounded to 1800 output tokens each, 90-second timeout, no automatic retries. No local machine required. Model and usage are recorded when returned. Billing depends on model and account.

The artifact contains the bounded model response (up to 12000 characters, configured secret redacted), finish reason, elapsed time, usage, safe error codes and validation details. Unexpected transport exceptions report only their type; HTTP errors omit provider bodies. Do not treat model output as trusted instructions. No raw model responses are printed in logs. A failed format check fails the workflow but still uploads the artifact.

## Evaluation

The 20-case set has 5 provisional examples per verdict, preserves the original three, includes real README excerpts pinned by blob hashes and synthetic title-only ablations. Sources are reused; author-assigned labels are not an independently reviewed or held-out benchmark. In particular, plausible experiments are suggestions, not proven results; documented recommendations are not proof of cooperation. The original LAION/AURA question remains open.

Metrics distinguish attempted, valid, labeled and correct counts; invalid responses never count as correct. Review the actual claims, section support, practicality of proposed experiments and cost, not just label agreement. The three original cases are useful for regression comparison; the 20-case set is a broader calibration and not a production acceptance threshold. Before promotion, obtain independent human judgments on diverse previously unseen projects and measure false positives, abstentions, and baseline performance. Persistent deduplication, independent counter-evidence retrieval, reviewer-model comparison and graph ingestion remain follow-ups.
