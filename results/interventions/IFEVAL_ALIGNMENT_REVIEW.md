# Four-language independent instruction-following anchors — evidence review

**Date:** 2026-11-13. **Scope:** source and constraint alignment, **not** model
evaluation, judge calibration or synthetic-data-quality assessment.

## Real reproducible source result

The first live read-only GitHub Actions run is
[successful](https://github.com/tire0011/ai-research-graph/actions/runs/43445610677)
(eight new offline tests passed). Input was pinned to
[Telefonica-Scientific-Research/european-ifeval @ a1d07cc](https://github.com/Telefonica-Scientific-Research/european-ifeval/tree/a1d07cccc0d1a4c95f3a12282a748566d8e18a60).
The workflow artifact \`ifeval-four-language-constraints\` contains the full
machine-readable report (\`IFEVAL_ALIGNMENT_LIVE.json\`), **only IDs and hashes**.

| Metric | Observed |
| --- | ---: |
| German prompts | 541 |
| French prompts | 541 |
| Basque prompts | 541 |
| Irish prompts | 524 |
| Shared task IDs across all four languages | **524** |
| Shared IDs with identical checker name lists | **425** |
| Also identical checker arguments and no forced response-language rule | **197** |
| Balanced pilot candidates, five constraint types × four IDs | **20** |

**Selected task IDs** (not vetted for equivalent meaning):

| Automated check | IDs |
| --- | --- |
| No commas | 32, 1001, 1162, 1187 |
| JSON output | 13, 321, 1075, 1094 |
| Bullet-list count | 102, 1286, 1634, 1934 |
| Placeholder count | 1005, 1372, 1927, 2136 |
| Paragraph count | 1082, 1236, 1248, 1377 |

Source/translation quality according to the published
[\`data/source.json\`](https://github.com/Telefonica-Scientific-Research/european-ifeval/blob/a1d07cccc0d1a4c95f3a12282a748566d8e18a60/data/source.json):

- German: \`native_speaker\`; 541/541; 0 missing upstream IDs.
- Basque: \`native_speaker\`; 541/541; 0 missing.
- French: \`localized_verified\`; 541/541; 0 missing.
- Irish: \`machine_translated_with_localization\`; 524/541; 17 missing.

A spot check suggests that *some wording may differ materially* even where
checker IDs and parameters match: tasks #1162 (child-friendly riddle theme)
and #13 (named place in an instruction) require human equivalence review.
This is a **review flag**, not a declaration that either translation is wrong.
All twenty selected examples have \`semantic_equivalence_verified=false\`.

## Already-existing OpenEuroLLM implementations

- [Taskboard #448](https://github.com/OpenEuroLLM/Taskboard/issues/448)
  explicitly plans \`IFEVAL\` alongside other multilingual SFT benchmarks.
- [OpenEuroLLM/oellm-eval](https://github.com/OpenEuroLLM/oellm-eval)
  already supports an IFEval task family and outcome aggregation.
- [OpenEuroLLM/quickdash](https://github.com/OpenEuroLLM/quickdash/blob/main/configs/evals/ifeval.yaml)
  has an IFEval display/metric configuration.
- [Decontamination benchmarks](https://github.com/OpenEuroLLM/decontamination-benchmarks)
  include IFEval/Multi_IFEval sources. These are **decontamination** tools;
  their existence alone is not proof that the Telefonica variant has been
  evaluated on an OpenEuroLLM checkpoint.

**Avoid duplicate work:** Do not implement a parallel IFEval evaluator or
assume teams are unaware of the standard benchmark. Instead, check whether
the existing SFT evaluation pipeline can run the *same overlapping 197
metadata-aligned IDs* with all four variants and output matched
per-constraint results, with the source-quality tier retained.

## What this experiment can and cannot tell us

European IFEval objectively tests **instruction-following**, e.g. valid
JSON or obeying a no-comma rule. The [EuroMultiSynth-Instruct](https://huggingface.co/datasets/openeurollm/EuroMultiSynth-Instruct)
judge instead scored the *utility of a training request and the answer quality*.
Crucially, its rubric may deliberately reject pointless or artificial
constraints. **Therefore: European IFEval scores must NOT be used as a direct
gold standard for the Synthgen judge.**

### Smallest follow-up that could be worth showing researchers

1. Have competent speakers vet these 20 tasks (especially Irish) and remove
   differences that change the substantive task or checker's interpretation.
   Do not quietly replace failures after looking at model outcomes.
2. Take **one public pre/post SFT model pair** from #448 or its existing
   evaluation workflow, if available, and generate responses on the *same
   accepted IDs*, fixed model revision and decoding. Keep the benchmark
   strictly held out of training and prompt optimization.
3. Run **the upstream European IFEval evaluator** (do not reimplement its
   language-specific rules) for matched per-language/per-constraint
   pass/fail. Calculate paired differences and uncertainty, retaining
   source-quality tiers, especially machine-translated Irish.
4. Independently verify a few observed language gaps with native speakers.
   If none survive, stop. If a consistent gap appears, ask whether the
   model/data owners already investigate that failure; only then plan a
   targeted training or judging intervention.

This would tell us whether existing **instruction-following capability**
has a language-dependent gap. It would **not** isolate whether an older
synthetic-data judge rejected Irish examples unfairly; that still requires
original **pre-filter** rejected/accepted examples and human checks.

## Run independently (Windows PowerShell)

\`\`\`powershell
python -m unittest discover -s tests -p "test_ifeval_alignment.py" -v
python .\ifeval_alignment.py --fetch --source-dir .\ifeval_audit_source --out .\results\interventions\IFEVAL_ALIGNMENT_LIVE.json
\`\`\`

The source directory must not exist before the fetch. Only pinned public
GitHub files are downloaded; raw multilingual prompts are not committed or
uploaded with the report. The source data have upstream license and
test-only conditions; no model training on these prompts.

**Outcome:** An inspectable, repeatable candidate-selection method and
a list of *existing tools to reuse*. **No model was scored, no language
quality difference was established, no contributor was contacted.**
