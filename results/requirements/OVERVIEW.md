# European AI ecosystem — requirements comparison

**Official-source snapshot:** 2026-11-11. No live import or outreach.

| Requirement | AI-on-Demand (AIoD) | EOSC EU Node | AI4EOSC | EOSC-ARENA |
| --- | --- | --- | --- | --- |
| [Find projects, tools and people](discovery.md) | documented | documented | documented | planned |
| [Spot duplicate work and reuse](duplicate_reuse.md) | adjacent | adjacent | adjacent | adjacent |
| [Connect humans and agents](human_agent_coordination.md) | adjacent | adjacent | adjacent | planned |
| [Interoperable sources and services](interop.md) | documented | documented | documented | planned |
| [Shared model development and evaluation](joint_model_work.md) | adjacent | adjacent | documented | planned |
| [Provenance and verification](provenance.md) | adjacent | documented | adjacent | planned |

**Legend:** documented = described by an official source; planned = announced/under development; adjacent = relevant but not demonstrated for the requirement; not_assessed = unknown, not unsupported.

## Known relationships (do not rediscover as new)

- EOSC-ARENA **extends** AI4EOSC ([source](https://arena.ai4eosc.eu/platform-overview/))
- EOSC-ARENA **integrates_with** EOSC EU Node ([source](https://arena.ai4eosc.eu/))
- AI4EOSC **deploys_via** EOSC EU Node ([source](https://docs.ai4eosc.eu/en/latest/howtos/deploy/eosc-node.html))

## Existing cross-project candidate reviews (not confirmed)

- **Model-card reporting / benchmark provenance** (complementary_hypothesis): [duplicate_reuse](duplicate_reuse.md), [provenance](provenance.md), [human_agent_coordination](human_agent_coordination.md); [source 1](https://github.com/OpenEuroLLM/Taskboard/issues/445), [source 2](https://github.com/LAION-AI/CLIP_benchmark/issues/153)
- **256k context extension / StateBench** (complementary_hypothesis): [duplicate_reuse](duplicate_reuse.md), [joint_model_work](joint_model_work.md); [source 1](https://github.com/OpenEuroLLM/Taskboard/issues/392), [source 2](https://github.com/allenai/olmo-eval/pull/358)
- **Arena-Hard v2 / contamination exclusion** (shared_problem): [duplicate_reuse](duplicate_reuse.md), [provenance](provenance.md); [source 1](https://github.com/OpenEuroLLM/oellm-eval/pull/174), [source 2](https://github.com/allenai/olmo-eval/pull/474)

## Interpretation

- Multiple documented capabilities in one requirement indicate possible overlap, **not duplicate engineering work**.
- Planned agent-to-agent integration in EOSC-ARENA is especially relevant to our Human–AI hypothesis; it is **not a finished connector**.
- AIoD's documented metadata API is the clearest next read-only source adapter candidate. EOSC onboarding has eligibility and review requirements.
- There is no established common cross-project model-training integration process in this bounded evidence sample; this is **not** proof none exists.

Documented means the official source describes a capability, not that it was tested here. Planned is a stated future target. Adjacent is related, not proof of requirement satisfaction. Not assessed is unknown, never absent. Known relations are already-public relationships, not new matches.
