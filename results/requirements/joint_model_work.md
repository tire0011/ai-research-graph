# Shared model development and evaluation

**Question:** Can separate contributors contribute to the same model-training or evaluation effort?

**Success test:** Demonstrate one jointly versioned model/data/evaluation contribution and a reproducible outcome.

| Platform | Evidence status | Source-backed observation |
| --- | --- | --- |
| [AI-on-Demand (AIoD)](https://www.aiodp.ai/) | adjacent | RAIL and the AI Builder support experiments; this does not establish a shared training pipeline for one common LLM. [Official source](https://www.iais.fraunhofer.de/en/press-events/press-releases/AI-on-Demand_Platform.html) |
| [EOSC EU Node](https://open-science-cloud.ec.europa.eu/) | adjacent | Compute and data services support research workflows; no EOSC-wide common LLM-training process is established by this source. [Official source](https://open-science-cloud.ec.europa.eu/support/frequently-asked-questions) |
| [AI4EOSC](https://ai4eosc.eu/) | documented | Platform supports training, fine-tuning, federated computing and shared modules; this does not imply joint training of one European foundation model. [Official source](https://docs.ai4eosc.eu/en/latest/getting-started/overview.html) |
| [EOSC-ARENA](https://arena.ai4eosc.eu/) | planned | Work package 7 covers scientific GenAI model pre- and post-training; this is not proof of a common open European foundation model. [Official source](https://arena.ai4eosc.eu/project-deliverables/) |

## Cross-project candidate cases (separate evidence layer)

- **256k context extension / StateBench** — `complementary_hypothesis`: OpenEuroLLM's ongoing 256k model extension could potentially use AllenAI's merged long-context state-tracking evaluations; runner compatibility is unknown. ([source 1](https://github.com/OpenEuroLLM/Taskboard/issues/392), [source 2](https://github.com/allenai/olmo-eval/pull/358))

**Next:** Inspect actual interfaces, participation, maturity and shared requirements before suggesting any reuse or outreach.

Status is based on curated public documentation, not tested service integrations.
