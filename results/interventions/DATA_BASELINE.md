# EuroMultiSynth-Instruct: source-backed baseline before model experiments

**Status (2026-11-12):** The 16 new isolated unit tests passed locally (seven
independent-review tests and nine new baseline tests). A read-only GitHub
Actions pilot was started on branch `experiment/concept-phrase-bridge-20261110`:
[view its runs](https://github.com/tire0011/ai-research-graph/actions/workflows/synthgen-baseline-pilot.yml).
Live sampled results must be checked from the workflow artifact; they are
**not** represented here as verified scientific measurements.

## Why this baseline

The [official EuroMultiSynth-Instruct dataset card](https://huggingface.co/datasets/openeurollm/EuroMultiSynth-Instruct)
states that 4,160,598 *retained* prompt/response pairs span 35 languages.
Only scores 7–10 survived filtering; **77.7% of retained rows scored 10**.
This distribution may reflect selection and scale compression, not necessarily
a judging defect.

The [PrefScope project](https://github.com/kargibora/PrefScope) can analyze
sparse concept features in prompt/response examples. Our hypothesis is that
a concept-based audit could reveal *actionable gaps beyond the known domain
and judge-score metadata*. It has not yet done so.

## Stage 1 — small real-data baseline

[`synthgen_baseline.py`](../../synthgen_baseline.py) retrieves published
rows through the [Hugging Face dataset-viewer API](https://huggingface.co/docs/dataset-viewer/rows),
bounded to three disjoint sampled blocks of 25 examples each in `de`,
`fr`, `eu` and `ga`, for **300 samples total**. It checks:

- Whether the expected user/assistant message structure is present;
- per-language domain distribution and counts of retained judge scores;
- sample start offsets, random seed, a checksum of source texts and other
  sampling metadata, but **not** any saved raw prompts or responses;
- whether the Hub SHA remains unchanged at the start/end.

The viewer endpoint cannot pin a specific dataset commit, so even matching
pre/post revisions **do not prove** the served rows came from that SHA.
The sample is made of clustered short consecutive pages; it is **not a
representative simple random sample** and should be used for feasibility and
schema checks, not statistical claims about populations or fairness.

### Run from Windows PowerShell

```powershell
python -m unittest discover -s tests -p "test_synthgen_baseline.py" -v
python .\synthgen_baseline.py --languages de,fr,eu,ga --pages 3 --length 25 --out .\results\interventions\synthgen_baseline_local.json
```

Review [GitHub Actions](https://github.com/tire0011/ai-research-graph/actions/workflows/synthgen-baseline-pilot.yml)
for a remote artifact named `synthgen-baseline-aggregates` from the automated pilot.
Raw training data remains only in memory during this stage. The generated
summary is descriptive, not a result of PrefScope.

## Stage 2 — follow-up if stage 1 works

1. Obtain a **revision-pinned** source sample, with actual domain, score and
   language strata. Check both low and high judge-score bins with appropriately
   sized samples, not just natural prevalence.
2. Independently inspect and label a small blinded holdout set. The controlled
   baseline uses the same `language`, `domain`, `persona` and `judge_score`
   columns before any SAE features.
3. Apply a suitable PrefScope lens **on precisely the same samples**, with
   per-language feature semantics checked. Avoid uncalibrated cross-language
   activation comparisons.
4. Compare incremental discoveries *beyond that baseline* on held-out data:
   new concrete quality failures, verified concept coverage, time to find
   problems and reviewer cost. Unnamed/unverified features count as
   abstentions, never successes.
5. If that leads to a reproducible, cheap intervention, offer an actionable
   handoff to the relevant maintainers. Otherwise stop.

**Do not claim** any new research collaboration, dataset-quality improvement
or acceleration from the stage-1 summary alone.
