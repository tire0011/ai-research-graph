# First linkage quality audit — 7 November 2026

This document records the **manual inspection and algorithmic changes** made after the first OpenEuroLLM snapshot. It is not a measurement of scientific correctness or comprehensive recall.

## Baseline and corrected result

| Measure | Initial algorithm | After boundary and namespace fixes |
| --- | ---: | ---: |
| Source records | 810 | 810 |
| Explicit source mentions | 31 | **28** |
| Name-only candidate links | 19 | **5** |
| Total inferred links | 50 | **33** |
| Duplicate node IDs | not checked | **0** |
| Duplicate edge pairs | not checked | **0** |
| Orphan edges | not checked | **0** |

The 810 records contained 493 issues and 192 pull requests (both open and closed), 78 Hugging Face models, 39 datasets, and 8 OpenAIRE keyword hits. There were 223 open issues and 19 open PRs. All 8 records lacking an update timestamp were OpenAIRE research products; this is missing source metadata, not evidence of inactivity.

## Confirmed mapping defects in the original code

1. **Version-prefix collision:** [Taskboard #377](https://github.com/OpenEuroLLM/Taskboard/issues/377) links to `tokenizer-256k-v2` and `tokenizer-128k-v2`. The previous substring comparison incorrectly added the distinct `tokenizer-256k` and `tokenizer-128k` artifacts.
2. **Cross-type prefix collision:** [oellm-eval #163](https://github.com/OpenEuroLLM/oellm-eval/issues/163) references the `prelude-base-eval-scores` *dataset*. The old check also attached the `prelude-base` *model* because its ID was a prefix.
3. **Different HF ownership:** [Taskboard #230](https://github.com/OpenEuroLLM/Taskboard/issues/230) links to `allenai/OLMo-3-7B-Think-SFT`, not to the same-named asset under `openeurollm/`. The first matcher proposed the latter because it ignored the namespace.

The new matcher requires an identifier boundary after the whole resource name and rejects name-only candidates that explicitly refer to another namespace. Regression tests cover these cases.

## What remains unverified?

The 28 explicit-reference excerpts were inspected for matching textual names/URLs. A match proves an artifact was **mentioned**, not that it was used in a particular experiment or causally related. Those semantics need additional metadata or domain review.

Five name-only candidates remain. All are **unverified**:

| GitHub source | Potential HF resource | Preliminary assessment |
| --- | --- | --- |
| [Taskboard #415](https://github.com/OpenEuroLLM/Taskboard/issues/415) | `openeurollm/prelude-base` | Plausible model-family mention; exact model/version unconfirmed |
| [Taskboard #308](https://github.com/OpenEuroLLM/Taskboard/issues/308) | `openeurollm/prelude-base` | Plausible model-family mention; exact model/version unconfirmed |
| [Taskboard #232](https://github.com/OpenEuroLLM/Taskboard/issues/232) | `openeurollm/OLMo-3-7B-Instruct-SFT` | Ambiguous: may refer to the upstream AllenAI model |
| [Taskboard #186](https://github.com/OpenEuroLLM/Taskboard/issues/186) | `openeurollm/OLMo-3-7B-Instruct-SFT` | Ambiguous: may refer to an externally sourced checkpoint |
| [oellm-eval #101](https://github.com/OpenEuroLLM/oellm-eval/issues/101) | `openeurollm/datamix-9b-80-20` | Plausible, but no complete repository ID given |

## Known limits and next checks

- **Recall has not been measured:** a missing link in the 33 results is not proof that no relationship exists. HF cards, GitHub code, publication text, GitHub Projects and dependency metadata may contain additional links.
- **OpenAIRE is keyword searched:** eight `OpenEuroLLM` hits cannot be compared directly to its complete set of project publications. No 1:1 publication reconciliation has been performed.
- **No scientific dependency labels:** the relationship here is `source mentions asset`, which is weaker than `trained_on`, `evaluates`, or `produced_by`.
- **Historical records included:** counts separate open from closed work; avoid interpreting all 685 GitHub issues/PRs as active tasks.
- **Provenance:** each newly generated edge stores the matched string, nearby text, source URL and target URL. A future human-reviewed gold set should evaluate entity resolution before semantic inference or MCP publication.

**Decision:** Continue with source-backed entity resolution and a manually labeled sample. Do not represent name-only candidates as verified research relationships.
