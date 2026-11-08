# Two-hop research evidence: graph versus source-following

Snapshot: `2026-11-08T21:35:02.740730+00:00`. Checked: **20/20** case sources; original GitHub task bodies verified: **40**. Status: `completed`.

## Exact evidence paths

| Cohort | Cases | Explicit 2-hop paths | Graph correct | Follow-source correct | Graph ms | Follow-source ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 20 | 16 | 20/20 | 20/20 | 0.02 | 9.8877 |
| positive | 9 | 16 | 9/9 | 9/9 | 0.0202 | 23.5907 |
| negative | 11 | 0 | 11/11 | 11/11 | 0.0199 | 3.2307 |

Lookup times are in-memory medians after snapshot collection and graph construction. They exclude original source fetches, index construction, parsing at ingestion, human research and review time; do **not** treat them as an end-to-end speedup.

The source-following baseline navigates the same two hops from raw snapshot text, without reading graph edges. It is deliberately allowed to follow links, so a graph advantage cannot be manufactured by denying the baseline the second hop.

## Per-question original-source evidence

| Anchor task | Gold paths | Graph matches | Text-follow matches | Explicit first-hop task IDs |
| --- | ---: | --- | --- | --- |
| [github:OpenEuroLLM/Taskboard#220](https://github.com/OpenEuroLLM/Taskboard/issues/220) | 1 | True | True | `github:openeurollm/taskboard#384`, `github:openeurollm/taskboard#385`, `github:openeurollm/taskboard#386`, `github:openeurollm/taskboard#387`, `github:openeurollm/taskboard#388`, `github:openeurollm/taskboard#389`, `github:openeurollm/taskboard#390` |
| [github:OpenEuroLLM/Taskboard#351](https://github.com/OpenEuroLLM/Taskboard/issues/351) | 1 | True | True | `github:openeurollm/taskboard#220` |
| [github:OpenEuroLLM/Taskboard#352](https://github.com/OpenEuroLLM/Taskboard/issues/352) | 1 | True | True | `github:openeurollm/taskboard#220` |
| [github:OpenEuroLLM/Taskboard#354](https://github.com/OpenEuroLLM/Taskboard/issues/354) | 2 | True | True | `github:openeurollm/taskboard#344`, `github:openeurollm/taskboard#361` |
| [github:OpenEuroLLM/Taskboard#384](https://github.com/OpenEuroLLM/Taskboard/issues/384) | 1 | True | True | `github:openeurollm/taskboard#385` |
| [github:OpenEuroLLM/Taskboard#385](https://github.com/OpenEuroLLM/Taskboard/issues/385) | 1 | True | True | `github:openeurollm/taskboard#220` |
| [github:OpenEuroLLM/Taskboard#416](https://github.com/OpenEuroLLM/Taskboard/issues/416) | 7 | True | True | `github:openeurollm/taskboard#318`, `github:openeurollm/taskboard#330` |
| [github:OpenEuroLLM/oellm-eval#140](https://github.com/OpenEuroLLM/oellm-eval/pull/140) | 1 | True | True | `github:openeurollm/oellm-eval#130`, `github:openeurollm/oellm-eval#136`, `github:openeurollm/oellm-eval#137` |
| [github:OpenEuroLLM/oellm-eval#150](https://github.com/OpenEuroLLM/oellm-eval/pull/150) | 1 | True | True | `github:openeurollm/oellm-eval#142` |
| [github:OpenEuroLLM/Taskboard#431](https://github.com/OpenEuroLLM/Taskboard/issues/431) | 0 | True | True | `github:openeurollm/taskboard#214` |
| [github:OpenEuroLLM/oellm-eval#166](https://github.com/OpenEuroLLM/oellm-eval/issues/166) | 0 | True | True | `github:openeurollm/oellm-eval#159` |
| [github:OpenEuroLLM/Taskboard#405](https://github.com/OpenEuroLLM/Taskboard/issues/405) | 0 | True | True | `github:openeurollm/oellm-eval#124` |
| [github:OpenEuroLLM/Taskboard#364](https://github.com/OpenEuroLLM/Taskboard/issues/364) | 0 | True | True | `github:openeurollm/oellm-autoexp#54` |
| [github:OpenEuroLLM/Taskboard#337](https://github.com/OpenEuroLLM/Taskboard/issues/337) | 0 | True | True | `github:openeurollm/oellm-eval#56` |
| [github:OpenEuroLLM/oellm-eval#2](https://github.com/OpenEuroLLM/oellm-eval/pull/2) | 0 | True | True | `github:openeurollm/taskboard#70` |
| [github:OpenEuroLLM/oellm-autoexp#69](https://github.com/OpenEuroLLM/oellm-autoexp/issues/69) | 0 | True | True | `github:openeurollm/oellm-autoexp#70` |
| [github:OpenEuroLLM/Taskboard#320](https://github.com/OpenEuroLLM/Taskboard/issues/320) | 0 | True | True | none |
| [github:OpenEuroLLM/Taskboard#130](https://github.com/OpenEuroLLM/Taskboard/issues/130) | 0 | True | True | none |
| [github:OpenEuroLLM/oellm-eval#152](https://github.com/OpenEuroLLM/oellm-eval/issues/152) | 0 | True | True | none |
| [github:OpenEuroLLM/oellm-autoexp#10](https://github.com/OpenEuroLLM/oellm-autoexp/issues/10) | 0 | True | True | none |

## Scientific limits

This small, deliberately selected sample is **not blind** and overrepresents known link paths. Gold paths were frozen after inspecting explicit source metadata and are checked again against the current original GitHub bodies. A link between tasks means only a textual mention; a second link to Hugging Face means the intermediate task explicitly mentions a model/dataset. Neither proves usage, model training, experimental success or causality. Negative cases are absence of this exact path pattern in the bounded snapshot, not proof of absence of real-world relationships.

This benchmark isolates **cross-source link traversal**; the preceding twenty-question experiment measured **finding the source task**. An actual researcher workflow would need both, plus independently evaluated AI answer quality and provenance completeness.
