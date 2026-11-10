# Collaboration Matcher — first exploratory human-assisted review

Review context: 2026-11-10. This is **not blinded or independent** and must not be presented as measured Precision@k. The original 25-pair run rechecked 30 tasks and 132 public issue comments. It found 10 pairs with shared GitHub participants, 2 with broader repository references, and 13 with no directly observable public connection. **Neither a shared participant nor an absent link proves whether teams collaborate on the task.**

## Representative inspected matches

| Source task | Older task | Provisional assessment | Why |
| --- | --- | --- | --- |
| [OpenEuroLLM Common Crawl LUMI-O](https://github.com/OpenEuroLLM/web-data-processing/issues/2) | [HPLT CC to LUMI-O](https://github.com/hplt-project/HPLT-textpipes/issues/9) | Existing coordination / content reuse | Both discuss downloads with @nvanva and @oepen; Git file comparison also confirms an identical get_url_lists.sh; this is not a new connection |
| [OpenEuroLLM S2–S4 update](https://github.com/OpenEuroLLM/web-data-processing/issues/6) | [HPLT XML → Markdown](https://github.com/hplt-project/HPLT-textpipes/pull/10) | Plausible reuse, existing repo context | S2–S4 explicitly wants combined XML and Markdown. An OpenEuroLLM comment references HPLT code; no proof the specific old PR was applied |
| [OpenEuroLLM robots.txt](https://github.com/OpenEuroLLM/web-data-processing/issues/7) | [HPLT robots coordination](https://github.com/hplt-project/HPLT-textpipes/issues/17) | Already-planned adaptation | OpenEuroLLM explicitly requests adapting Jaume's existing robots.txt intermediate step; repeating a generic call to collaborate adds little |
| [OpenEuroLLM WARC metadata](https://github.com/OpenEuroLLM/warc2text/issues/1) | [HPLT crawl ID repackaging](https://github.com/hplt-project/monotextor-slurm/issues/9) | Related data lineage, not equivalent requirement | WARC record identifiers and the crawl identifier serve different purposes. Public participant @oepen overlaps |
| [OpenEuroLLM tokenizer evaluation](https://github.com/OpenEuroLLM/Taskboard/issues/146) | [LAION multilingual CLIP datasets](https://github.com/LAION-AI/CLIP_benchmark/pull/113) | Related but insufficiently actionable | OpenEuroLLM considers LM tokenizer fertility and downstream training effects. LAION adds multilingual image–text retrieval datasets and NLLB-CLIP evaluation; shared language coverage alone does not establish reusable evaluation code |
| [OpenEuroLLM long-context data](https://github.com/OpenEuroLLM/Taskboard/issues/339) | [HPLT crawl ID repackaging](https://github.com/hplt-project/monotextor-slurm/issues/9) | Weak match | Long-context generation and adding crawl IDs to S2 metadata address different work |

## New, **manually identified** hypothesis (not found by the matcher)

- [OpenEuroLLM/oellm-eval#163](https://github.com/OpenEuroLLM/oellm-eval/issues/163) documents checkpoint evaluation provenance and reproducibility questions, including configuration comparisons and missing per-sample logs.
- [LAION-AI/CLIP_benchmark#153](https://github.com/LAION-AI/CLIP_benchmark/issues/153) proposes an optional, source-linked benchmark-run manifest recording model, dataset, task, metrics and benchmark commit.
- **Potential common ground:** a small reusable manifest schema for evaluation provenance across different model modalities. This could make results easier to cite or compare; it does **not** solve the CoQA F1 anomaly, imply the tools are interchangeable, or demonstrate that either project is interested in collaboration.
- No public direct link or shared GitHub participants were established for this pair from the checked issues. Private coordination was not assessed. **Do not contact teams automatically.**
- Next verification: inspect current evaluation outputs and ask maintainers whether shared run-level metadata conventions would be useful *before* proposing implementation.

## What the experiment actually tells us

The matcher can surface older technical work, but several high-scoring matches are already coordinated or merely share terminology. The public-coordination check eliminates some optimistic novelty assumptions; it does **not** measure useful-new-collaboration discovery. The more interesting cross-project provenance hypothesis needed a **manual search outside the ranked shortlist**, illustrating limited concept coverage.

For a valid comparison with plain text search, freeze an unseen query set and have an independent reviewer label both methods' suggestions as actionable new contact, already coordinated reuse, adjacent topic, or irrelevant. Do not report precision improvements or successful collaboration before such labels and real replies exist.
