# Five OpenEuroLLM requirements — targeted AIoD review

**Pilot on 2026-11-11; exploratory, not blinded.** Five open OpenEuroLLM
Taskboard issues were checked live on GitHub and their issue goals were fixed
before the AIoD search. The probe made 15 bounded public API searches (each
issue phrase across projects, datasets and publications; first five hits per
asset type). Details and source/metadata SHA256 values are recorded in
[`TARGETED_SEARCH_RESULTS.json`](TARGETED_SEARCH_RESULTS.json).

**Result:** 42 issue-specific catalogue entries returned after within-issue
URL-alias removal; **0** entries show both defining search terms in the
title. **0 verified** new relationships, reusable implementations or existing
coordination checks. This is not a precision estimate, because the entire
shortlist was not independently labeled or source-reproduced.

## Five qualitative checks against the original requirements

| OpenEuroLLM requirement | Example AIoD hit | Preliminary review | Missing bridge |
| --- | --- | --- | --- |
| [#445: model-card evaluation reporting](https://github.com/OpenEuroLLM/Taskboard/issues/445) | [Circular Data Service Cards](https://api.aiodp.eu/v2/publications/pub_OVWGdMO1Z3S6bG30Zj8gqrRh) | **Unrelated**: cards for circular-economy data-service design, not model-card tables/plots | No transferable evaluation-report script |
| [#392: 256k long-context checkpoint](https://github.com/OpenEuroLLM/Taskboard/issues/392) | [QUAC: Question answering in context](https://api.aiodp.eu/v2/publications/pub_XttnJAv5g7aZ5hF9zVYHkr6w) | **Weak context-word overlap**: no evidence of 256k checkpoint extension or Needle-in-a-Haystack runner | Evaluation context length, artifact and integration unknown |
| [#353: sparse concept discovery in post-training](https://github.com/OpenEuroLLM/Taskboard/issues/353) | [Post-hoc Concept Disentanglement](https://api.aiodp.eu/v2/publications/pub_Q5soQrN8Id4FOgPB3dmAP1Iw) | **Methodological adjacency hypothesis**: concept vectors/vision vs. reusable SAE prompt–response concepts and holdout verification | No demonstrated shared data interface, implementation or compatible verifier |
| [#437: 35-language instruction synthesis](https://github.com/OpenEuroLLM/Taskboard/issues/437) | [MAD-TSC multilingual aligned news data](https://api.aiodp.eu/v2/datasets/data_ugYAIrCmmIoBnGrDgQAMrZ9G) | **Possible source-domain complement**, not duplicate development: sentiment-labeled news vs. synthetic instruction/answer pairs | Languages, license, format, distribution suitability and actual interest unverified |
| [#360: data compliance governance](https://github.com/OpenEuroLLM/Taskboard/issues/360) | [AI-DAPT data-pipeline lifecycle project](https://api.aiodp.eu/v2/projects/proj_7yIB83mDHRpHJXHhc8LYYiyD) | **Adjacent domain only**: governance policy decisions are not interchangeable with AI pipeline automation | No common compliance framework or governance artifact established |

The AIoD search responses are relevance-ranked keyword hits and can match
only one common word. For example, searching `model card` also finds models
without model cards and card-based tools without models. This pilot records
that behavior instead of treating API ranking as cross-team relevance.

**Negative controls:** the previously examined
[OpenEuroLLM #445 ↔ LAION CLIP_benchmark #153](../COLLABORATION_REVIEW_NEXT_CASES.md)
and [OpenEuroLLM #392 ↔ AllenAI olmo-eval #358](../COLLABORATION_REVIEW_NEXT_CASES.md)
pairs were discovered before this AIoD run. They are separate known
collaboration *hypotheses*, not new discoveries by this targeted API pilot.

## Why this matters and next gate

1. **Retrieval is not matching.** AIoD can retrieve catalogue assets, but
   broad word overlap fails to establish requirement, maturity and interfaces.
2. **Technical review is the bottleneck.** An actual complement requires a
   plausible reusable artifact and defined compatibility test, not thematic
   similarity alone.
3. **Unknown is not no collaboration.** Existing coordination has not been
   checked for these external AIoD authors and cannot be inferred absent.

For a stronger test, start with each task's concrete output contract and
technical vocabulary, compare source-backed retrieval against an independent
semantic search where available, and have a reviewer label a balanced sample
of positives and known false positives. Track precision, reviewer effort,
reusability and any **confirmed** new coordination separately. No outreach
was performed by this study.
