# European model landscape: first graph pilot (2026-11-19)

**Status: bounded, source-qualified discovery pilot. Not a deployed discovery service.**

This extends [the same research graph](../../README.md), rather than starting a
parallel graph. It keeps the current weekly workflow, frozen studies and
last-good snapshot untouched. Its separate overlay has stable project and
infrastructure IDs compatible with the main graph's node/edge convention.

## What's actually included

- 25 European AI model initiatives, selected from the
  [OpenLLM Europe community catalogue](https://github.com/OpenLLM-Europe/European-OpenLLM-Projects),
  plus Olala from its [official model card](https://huggingface.co/OVHaiLLM/Olala-v1.0-mini-7A1B).
  Entries marked `catalogue_lead` were **not independently revalidated**;
  this is not a verified list of active/open projects or official affiliation.
- Seven *reported* source relationships, including the already-known
  [OpenEuroLLM–HPLT joint reference-model release](https://openeurollm.eu/blog/hplt-oellm-38-reference-models).
  This prior collaboration must never be shown as new.
- One computed two-hop connection: Olala and Luciole both *report* training
  using **Jean Zay**. This is **not evidence of collaboration**.
- Three source-backed **unreviewed questions**: Olala ↔ Luciole,
  Olala ↔ Soofi S, and Olala ↔ OpenEuroLLM. These remain separate from
  factual edges and have stop conditions.

## Execute (PowerShell)

```powershell
python -m unittest tests.test_eu_model_landscape -v
python .\eu_model_landscape.py --snapshot .\results\snapshot.json
# Without the existing snapshot, omit --snapshot to inspect only new nodes/edges.
```

Outputs: `results/eu_model_landscape_pilot.json` and
`results/EU_MODEL_LANDSCAPE_PILOT.md`. They are read-only-derived pilot
outputs. No external request is made by this script. No existing source is
modified and no contacts are made.

## First useful question: Olala and Luciole

- [Olala's model card](https://huggingface.co/OVHaiLLM/Olala-v1.0-mini-7A1B)
  reports Mamba-3/MoE and training on JUPITER, Jean Zay and MeluXina.
- [Luciole model card](https://huggingface.co/OpenLLM-France/Luciole-8B-Base)
  reports a hybrid Mamba/Transformer architecture;
  [OpenLLM France's announcement](https://futurium.ec.europa.eu/en/apply-ai-alliance/community-content/luciole-fully-open-llm-family-european-digital-commons)
  reports training on Jean Zay.
- **Question, not inference:** Is there a directly reusable efficiency/context
  evaluation, in view of the different architectures and inference stacks?
  First inspect published benchmarks, versions, inference backends, hardware,
  measurements and any concrete unmet maintainer request. If there is none,
  explicitly stop. Sharing a supercomputer is not a working relationship.

## How to decide whether this should grow

Use the [seven decision gates](../../RESEARCH_DECISION_GATES.md) and
[collaboration review protocol](../../COLLABORATION_REVIEW_PROTOCOL.md).
Freeze the *same source packet* for graph-assisted and ordinary source-first
reviewers, including negative cases. Measure justified actionable decisions,
source accuracy, false positives, abstentions, and verification effort.
The existence of a 2-hop path, similar names, or model architectures is not
proof of useful collaboration or duplicate work.

Avoid an always-on crawler, ranking model, outreach or schema migration until
a decision-level advantage has been demonstrated. This preserves the project's
wider research/hypothesis mission, rather than changing its focus.
