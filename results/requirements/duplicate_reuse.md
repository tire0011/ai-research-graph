# Spot duplicate work and reuse

**Question:** Are independent teams solving the same requirement, and can one reuse a specific artifact?

**Success test:** Name both requirements, implementation maturity, transferable artifact and technical mismatch; human confirms relevance.

| Platform | Evidence status | Source-backed observation |
| --- | --- | --- |
| [AI-on-Demand (AIoD)](https://www.aiodp.ai/) | adjacent | AI resources are made discoverable and reusable, but evidence here does not establish automatic duplicate-work detection. [Official source](https://www.iais.fraunhofer.de/en/press-events/press-releases/AI-on-Demand_Platform.html) |
| [EOSC EU Node](https://open-science-cloud.ec.europa.eu/) | adjacent | Software and workflows can be found and reused, but documented discovery is not itself a duplicate-work detector. [Official source](https://open-science-cloud.ec.europa.eu/support/frequently-asked-questions) |
| [AI4EOSC](https://ai4eosc.eu/) | adjacent | Reusable modules and common APIs support implementation reuse, not automated discovery of overlapping team requirements. [Official source](https://docs.ai4eosc.eu/en/latest/getting-started/overview.html) |
| [EOSC-ARENA](https://arena.ai4eosc.eu/) | adjacent | Planned agent marketplace and knowledge services may help reuse, but no implemented duplicate-work matcher is demonstrated. [Official source](https://arena.ai4eosc.eu/project-deliverables/) |

## Cross-project candidate cases (separate evidence layer)

- **Model-card reporting / benchmark provenance** — `complementary_hypothesis`: OpenEuroLLM needs model-card reports; LAION has an optional audit-manifest proposal. Code compatibility and maintainer interest are not established. ([source 1](https://github.com/OpenEuroLLM/Taskboard/issues/445), [source 2](https://github.com/LAION-AI/CLIP_benchmark/issues/153))
- **256k context extension / StateBench** — `complementary_hypothesis`: OpenEuroLLM's ongoing 256k model extension could potentially use AllenAI's merged long-context state-tracking evaluations; runner compatibility is unknown. ([source 1](https://github.com/OpenEuroLLM/Taskboard/issues/392), [source 2](https://github.com/allenai/olmo-eval/pull/358))
- **Arena-Hard v2 / contamination exclusion** — `shared_problem`: Both teams address Arena-Hard v2, but one implements pairwise scoring and the other cleans contaminated results. Neither duplicate code nor a transferable contract is proven. ([source 1](https://github.com/OpenEuroLLM/oellm-eval/pull/174), [source 2](https://github.com/allenai/olmo-eval/pull/474))

**Next:** Inspect actual interfaces, participation, maturity and shared requirements before suggesting any reuse or outreach.

Status is based on curated public documentation, not tested service integrations.
