# Provenance and verification

**Question:** Can the platform track evidence, changes, dataset/model identity and human acceptance?

**Success test:** Trace a suggestion to original sources and distinguish documentation, intentions and executed results.

| Platform | Evidence status | Source-backed observation |
| --- | --- | --- |
| [AI-on-Demand (AIoD)](https://www.aiodp.ai/) | adjacent | Cross-platform metadata provides resource identities, not a verified provenance chain for our matcher's collaboration claims. [Official source](https://aiondemand.github.io/aiondemand/) |
| [EOSC EU Node](https://open-science-cloud.ec.europa.eu/) | documented | The federation emphasizes FAIR metadata, open research outputs and reproducible workflows; application-level claim verification is still separate. [Official source](https://open-science-cloud.ec.europa.eu/support/frequently-asked-questions) |
| [AI4EOSC](https://ai4eosc.eu/) | adjacent | Model-development and experiment-tracking services are documented; our particular cross-team evidence chain is not verified. [Official source](https://docs.ai4eosc.eu/en/latest/getting-started/overview.html) |
| [EOSC-ARENA](https://arena.ai4eosc.eu/) | planned | Work package 8 plans data/model lifecycle tracking, provenance, persistent IDs and automatically generated metadata. [Official source](https://arena.ai4eosc.eu/project-deliverables/) |

## Cross-project candidate cases (separate evidence layer)

- **Model-card reporting / benchmark provenance** — `complementary_hypothesis`: OpenEuroLLM needs model-card reports; LAION has an optional audit-manifest proposal. Code compatibility and maintainer interest are not established. ([source 1](https://github.com/OpenEuroLLM/Taskboard/issues/445), [source 2](https://github.com/LAION-AI/CLIP_benchmark/issues/153))
- **Arena-Hard v2 / contamination exclusion** — `shared_problem`: Both teams address Arena-Hard v2, but one implements pairwise scoring and the other cleans contaminated results. Neither duplicate code nor a transferable contract is proven. ([source 1](https://github.com/OpenEuroLLM/oellm-eval/pull/174), [source 2](https://github.com/allenai/olmo-eval/pull/474))

**Next:** Inspect actual interfaces, participation, maturity and shared requirements before suggesting any reuse or outreach.

Status is based on curated public documentation, not tested service integrations.
