# EuroMultiSynth-Instruct — first real bounded baseline

**2026-11-12 — completed remote sample; exploratory, NOT a quality finding.**
GitHub Actions [run #43312918956](https://github.com/tire0011/ai-research-graph/actions/runs/43312918956)
completed successfully with all **16 then-existing unit tests** green
(seven research-intervention review tests; nine baseline tests).
Its summary-only artifact is `synthgen-baseline-aggregates`.

- Public dataset: [EuroMultiSynth-Instruct](https://huggingface.co/datasets/openeurollm/EuroMultiSynth-Instruct)
- Public source SHA before and after the API requests: `dc644a8b901567b2d46ad4b4ccf557afdedaf4a0`
- **Important:** dataset-viewer pages were **not pinned** to that SHA.
- Seed `20261112`, three spaced *contiguous* blocks of 25 rows each language.
- Total 300 retained rows (75 per language); no raw prompt/response saved to the artifact.

| Language | Dataset size | Sampled | Score 10 | Score 9 | Score 8 | Score 7 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| German (`de`) | 230,459 | 75 | 74 | 1 | 0 | 0 |
| French (`fr`) | 103,013 | 75 | 71 | 2 | 1 | 1 |
| Basque (`eu`) | 50,716 | 75 | 6 | 13 | 17 | 39 |
| Irish (`ga`) | 25,941 | 75 | 23 | 5 | 27 | 20 |

The apparent score distribution differs markedly across languages.
This **does not establish unequal quality or judge bias**: all rows were
preselected by score; examples were sampled in only three contiguous blocks
per language; the topical mix differs sharply (the 75 Irish samples include
52 labeled `coding`, compared with 33 German and 26 Basque). The result is a
**strong reason to test for sample-order/domain confounding** before anyone
contacts the teams.

### First falsification step

A later test (see workflow on the same PR branch) samples **12 disjoint
shorter blocks × 8 rows per language**, using seed `20261113`.
It also measures **domain × score** so we can compare the same topical
categories across languages. A changed estimate will signal sampling
instability, not a worsening or improvement of the underlying dataset.

A next-stage experiment needs a revision-pinned, independent
language/domain/score-stratified sample, human-checked cases and a
same-sample metadata baseline *before* PrefScope. No claim of acceleration,
new collaboration or semantic-quality improvement is warranted yet.

See [methods and limitations](DATA_BASELINE.md).
