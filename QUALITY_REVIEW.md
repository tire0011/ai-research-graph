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

## Expanded citation coverage audit — 7 November 2026

The second probe added DOI/arXiv extraction from GitHub and Hugging Face, exact OpenAIRE PID matching, and 12 individual arXiv lookups. It produced **56** cross-platform edges, of which **23** were scholarly identifier matches. Those 12 lookups covered only a subset of the explicitly cited arXiv IDs.

The third probe replaced individual lookups with OpenAIRE's documented `ids.arxiv:ID1|ID2` OR filter, using at most 40 IDs per request and a total limit of 80. The OR behavior was verified against live OpenAIRE results for two known publications before implementation. Both GitHub and Hugging Face are now eligible sources of citation IDs.

| Metric | Before expanded batch lookup | After expanded batch lookup |
| --- | ---: | ---: |
| Total records | 822 | **849** |
| Research products in snapshot | 20 | **47** |
| Shared scholarly-ID edges | 23 | **54** |
| All observed cross-source edges | 56 | **87** |
| Distinct explicit arXiv IDs identified across GitHub/HF | 40 | **40** |
| Distinct cited arXiv IDs resolved through OpenAIRE | partial sample | **40/40** |
| Publications cited by both GitHub and HF | not reported | **1** |
| Duplicate nodes / edges / orphan edges | 0 / 0 / 0 | **0 / 0 / 0** |
| Source API errors | 0 (one deliberate coverage warning) | **0** |

### Remaining linkage bottleneck

- GitHub issues/PRs: **20/685** source records (2.9%) have an explicit DOI/arXiv identifier. All 20 link to a known OpenAIRE publication in this snapshot.
- Hugging Face models/datasets: **19/117** records (16.2%) have a DOI/arXiv identifier. All 19 link to a known OpenAIRE publication.
- The other **763** engineering/model/dataset records are **not proven unconnected**; the metadata probe simply has no persistent scholarly identifier to join on. More relationship data may exist in README files, commit messages, datasets, model cards, publication text or community infrastructure.
- One publication is cited by records on both GitHub and Hugging Face. This creates a traceable **GitHub → publication ← HF** bridge, but is not evidence that those artifacts share authors, code, data, evaluation results or a direct development dependency.
- The five name-only matches remain unconfirmed. Until manually reviewed, they should not be promoted into verified edges.

**Quality conclusion:** The exact-ID join has **100% lookup coverage for the 40 explicitly captured modern arXiv IDs in this bounded source snapshot**, with no observed integrity defects. This is *not* 100% research discovery recall or an estimate of the precision of all graph edges. The next highest-value work is a small manually labeled set of missing relationships and a metadata publishing convention, not a larger central agent or MCP service.

## Structured Hugging Face metadata audit — 8 November 2026

The five unresolved name-only GitHub-to-HF candidates from the first audit were reinspected in their original issue/PR text. The evidence does **not** justify silently promoting any to an exact repository reference:

- **Taskboard #415 and #308:** `Prelude-base` is mentioned as a model/family name, without the full `openeurollm/prelude-base` Hub identifier in the matched context. These remain plausible, not verified.
- **Taskboard #232 and #186:** `OLMo-3-7B-Instruct-SFT` appears in reproduction/upstream-checkpoint contexts; #186 links to AllenAI open-instruct information. The `openeurollm` model card itself declares an **AllenAI** base model. It would be misleading to assume that an unqualified name refers specifically to the OpenEuroLLM-owned copy.
- **oellm-eval #101:** `datamix-9b-80-20` is named in a test context, but the full Hugging Face namespace is absent. Keep it as a candidate.

Instead, we inspected the structured `base_model` and `datasets` fields already exposed in public Hugging Face model cards. These are documented as fields containing full Hub repository IDs. For the existing 849-record snapshot:

| Source-backed relationship | Observed count | How it is used |
| --- | ---: | --- |
| Exact model-card reference to another indexed OpenEuroLLM asset | **10** | New `declared_metadata` edges; no name guessing |
| Model-card reference to an asset outside the indexed OpenEuroLLM organization | **65** | Recorded separately, not verified or linked to invented nodes |
| Previously recorded cross-platform edges | **87** | Remain unchanged and separately labeled |
| Total edges including exact in-org card declarations | **97** | 54 scholarly IDs, 28 direct GitHub-to-HF references, 10 card declarations, 5 candidates |

Examples: `openeurollm/OLMo-3-7B-Dolci-Translated-A-75EN` declares `openeurollm/OLMo-3-7B-Instruct-SFT` as `base_model` and `openeurollm/Dolci-Instruct-SFT-translated` under `datasets`; `openeurollm/oellm-9b-256k-sft` declares `openeurollm/oellm-9b-256k-theta64m-prelude` as its base model.

**Interpretation:** This exposes a useful additional layer of published metadata without an LLM or guessed semantic links. As with any publisher-supplied description, the declarations themselves have not been experimentally verified. A natural next test is to resolve the 65 out-of-scope references against their actual Hugging Face repository records and investigate their authorship/lineage, while continuing to keep manual name matches separate.

## One-hop external Hugging Face target audit — 8 November 2026

The next live probe investigated **65 publisher-declared external model/dataset references** representing **37 distinct Hugging Face IDs**. Every target was queried via the public Hugging Face API, without a personal credential and without recursively following external cards.

The first inspection found 32 exact IDs returning public metadata, two references returning HTTP **401** (not publicly accessible to this probe), and three requests whose API responses contained a **different canonical repository ID**. Those three were initially classified as fetch failures by an overly strict exact-name check. We corrected the code to retain the original declaration and the returned canonical identity, with a separate `verified_redirect` status and `declared_metadata_redirect` edge. This is not a guessed string substitution.

| Originally declared target | API-returned canonical target | Kind |
| --- | --- | --- |
| `LLM360/MegaMath` | `IFM/MegaMath` | dataset |
| `laineyyy/openeurollm-datamix-2b-en-80pct-DPO-HelpSteer3` | `ezosa/openeurollm-datamix-2b-en-80pct-DPO-HelpSteer3` | model |
| `openeurollm/prelude` | `openeurollm/prelude-base` | model; canonical target already indexed |

The two inaccessible declarations were `HPLT/HPLT4.0` (dataset) and `AI-Sweden-Models/oellm-9b-base` (model). **HTTP 401 does not prove nonexistence** and the graph does not treat those as confirmed public assets. A model-card `base_model` or `datasets` assertion is evidence only that its publisher *declared* a relationship; it is not a validated training lineage.

The code maintains distinct states for direct public matches, canonical-name resolutions, HTTP 401/403, HTTP 404, transient lookup failures and items beyond the lookup limit. It persists the original declared IDs, canonical target IDs and lookup outcomes for subsequent review. The bounded lookup makes no claim to discover every project dependency.
