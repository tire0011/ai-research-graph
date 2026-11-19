# Candidate intervention — is it the multilingual judge, the generator, or the sample mix?

**Reviewed 2026-11-13; proposed study, not an established bug or scientific result.**
No external contact, model scoring, new human labels or fine-tuning has been performed.
This is a *decision bottleneck* card: identify what evidence would change the
next action before proposing an expensive retraining run.

## Research question and practical decision

The 35-language [EuroMultiSynth-Instruct release](https://huggingface.co/datasets/openeurollm/EuroMultiSynth-Instruct)
retains 4,160,598 single-turn examples after LLM judging and de-duplication.
The [production findings](https://github.com/OpenEuroLLM/synthgen/blob/main/production/35lang_run/FINDINGS.md)
already identified dramatically different initial per-language judge pass
rates (Irish **8.3%** and German **99.0%** in the *partial-run* table).
These are **not new discoveries by our graph**. The full public release
contains 25,941 Irish and 50,716 Basque examples versus 230,459 German
and 103,013 French examples.

**Decision to unlock:** Before allocating compute to generate more
low-resource-language data, decide whether the bottleneck is (a)
generator/response quality, (b) language-dependent judge calibration or
prompt format, (c) topic/domain composition, or (d) quality filtering and
deduplication jointly. Different diagnoses imply different fixes.

## What already exists — reuse, do not duplicate

- [Taskboard #437](https://github.com/OpenEuroLLM/Taskboard/issues/437):
  `synthgen` localized generation, judge scoring, filter and deduplication.
- [Taskboard #345](https://github.com/OpenEuroLLM/Taskboard/issues/345):
  earlier 11-language instruction dataset includes a small independent
  **back-translation quality check**. Do not propose repeating a full
  translation of the whole release.
- [Taskboard #32](https://github.com/OpenEuroLLM/Taskboard/issues/32)
  is **closed** but contains extensive cross-language pretraining-quality
  classification and human-annotated work (including Basque), with discussion
  about score/calibration variation. This is **pretraining web text**, not an
  interchangeable judge for instruction-following pairs. Transfer the
  experiment design, relevant annotator contacts or labeling rubric only
  after confirming suitability.
- [Taskboard #186](https://github.com/OpenEuroLLM/Taskboard/issues/186)
  shows that simply scaling multilingual SFT does **not necessarily improve
  downstream performance**, and that source and replay mixture matter.
  Its multilingual experiment is not a direct EuroMultiSynth ablation.
- [Our 300-row pilot](LIVE_BASELINE_20261112.md) found strongly different
  score-10 frequencies across small *clustered* language samples. This
  cannot establish bias or explain the pre-filter pass-rate gap.
- [PrefScope / #353](https://github.com/OpenEuroLLM/Taskboard/issues/353)
  could subsequently test concept coverage; it does not itself validate
  the language judge or distinguish rejected from generated data.

## Four falsifiable hypotheses

| Hypothesis | Discriminating evidence | What we should do if supported |
| --- | --- | --- |
| H1: generator output quality differs | Independent native-language human judgments also rate original Irish/Basque generation lower within matched domains | Improve prompts/generator or curate examples rather than recalibrating scores |
| H2: judge is language-sensitive | Human-verified equivalent prompt/response **anchor pairs** receive systematically different scores solely by language, using the *same* judge/rubric; independent human scores stay matched | Calibrate judge, use per-language validation or supplement with a different judge |
| H3: sample mix explains apparent gaps | Domain-balanced and score-balanced comparisons reduce/disappear observed differences | Avoid single global pass-rate comparisons; adjust sampling/reporting |
| H4: selection and deduplication dominate | Raw gen counts, judge-passing counts and final survivor counts per language expose major losses at different stages | Target the actual filtering stage, not generation volume |

## Stage A — public-data pilot (does not need HPC credentials)

1. Pin the [Hugging Face dataset](https://huggingface.co/datasets/openeurollm/EuroMultiSynth-Instruct)
   to a **commit SHA** and read the specific Parquet language configurations.
   Avoid high-frequency dataset-viewer API calls (our broader pilot received
   HTTP 429). Store content hashes, never copies of full public data in the PR.
2. In `de`, `fr`, `eu`, `ga`, draw a **fixed-seed within-domain** small
   sample, including score 7/8 and score 10 examples. Report both the
   conditional stratum comparisons and selection effects, not a misleading
   overall i.i.d. estimate. Pilot size suggestion: **40 retained
   examples/language**; adjust when rare cells lack sufficient examples.
3. Reuse or create **20 meaning-equivalent anchor tasks** with high-quality
   answers, carefully translated and checked by a competent native reviewer
   for each target language. These are **controls**, not random original
   samples. Ask a frozen judge with the same scoring rubric to assess the
   controls in each language; compare paired within-task score differences,
   not unrelated corpus distributions.
4. Run a second independent judge *without showing either model the other's
   answers*. Validate via a small blind human audit: correctness, fluency,
   instruction satisfaction, and task usefulness as separate dimensions.
   If qualified native reviewers are unavailable, report **inconclusive**.
5. Pre-register comparisons and report paired effect estimates/uncertainty
   with per-language and per-domain breakdowns. At this stage a score
   difference is a **calibration hypothesis** only. Use score scale and
   prompt/revision provenance; do not claim to replicate the published
   original Qwen3.6 judge if its exact checkpoint/settings were not used.

**Cheap early stop:** If anchor translations do not meet native-language
equivalence requirements, or domain-matched results are unstable across
sampling seeds, pause. Do not build a PrefScope integration yet.

## Stage B — missing evidence for actual 8.3% Irish pass-rate cause

The release contains **only accepted rows with scores 7–10**. This is
**selection-biased**: it is **impossible** to attribute initial failures to
judge bias versus bad generation using the release alone.

To actually diagnose pre-filter pass rates, request from the authors (only
after reviewing existing work and with user approval) a **small random
pre-filter sample** from the original run containing both accepted *and
rejected* examples across languages and domains, with `language`,
`domain`, `judge_score`, generator and judge model/prompt version and
enough text to re-score under appropriate access controls. Alternatively
ask them to run the same blinded rubric experiment locally and publish only
aggregate disagreement rates. Do not request their entire HPC corpus.

## Outcomes: choose the lever, not a predetermined solution

- If native raters largely agree with the judge: improve
  **generation prompts/model** and inspect authentic low-resource outputs.
- If raters disagree systematically while equivalent anchor items are
  penalized only by language: improve or **calibrate the judge**.
- If effects disappear after matching domain and data stage: adjust
  **measurement/sampling**, not models.
- If all hypotheses remain weak: **stop**. The graph should label the
  relationship `known_problem / unresolved_cause`, not `confirmed_synergy`.

## What to send if and only if Stage A yields a defensible result

A question to [#437](https://github.com/OpenEuroLLM/Taskboard/issues/437),
referencing their original identification of this problem, e.g.:

> I noticed your production findings already flag the very low Irish
> judge-pass rate. We're testing whether this reflects actual generation
> quality, differing judge calibration, or domain composition using
> matched-language anchor examples and a separate quality baseline.
> Has a pre-filter, independently reviewed sample already been evaluated
> for Irish/Basque? If not, would a small reproducible disagreement-rate
> report be useful?

**Draft only — no contact performed.** A useful eventual result would be
a changed decision about how to spend generation/judging compute, then
confirmed by a downstream same-budget training comparison. The current
evidence does not justify claiming accelerated research.
