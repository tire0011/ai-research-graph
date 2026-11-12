# Research intervention pilot — find the next useful action, not the nearest text

**Status:** 2026-11-12 source-backed hypothesis review. No outside LLM was run.
No research acceleration, previously unknown contact, or reusable integration is yet confirmed.
This extends (does not replace) the earlier [impact evidence](../IMPACT_EVIDENCE.md)
and [AIoD search pilot](../aiod/TARGETED_REVIEW.md).

## Reframe: decision bottlenecks

Instead of treating every shared subject as an opportunity, distinguish:

| Relationship | Evidence needed | Meaningful action |
| --- | --- | --- |
| Duplicate engineering | Same objective, deliverable and overlapping implementation, *and* independent effort | Ask whether to consolidate |
| Complementary capability | A concrete artifact or method from A can meet a requirement of B | Run an interface/compatibility test |
| Experimental bottleneck | Explicit failure blocks a measurable milestone | Find a discriminating experiment, not another keyword match |
| Missing evaluation | A deliverable exists but a known blind spot is not measured | Add an independent test with a baseline |
| Coordinated already | Public known dependencies/team relationships | Track the existing handoff, never market as a novel discovery |

**Critical distinction:** "High potential impact" is an untested hypothesis. The actual
researcher's priority and spare capacity must be learned from them, not inferred from GitHub activity.

## Opportunity A — PrefScope × EuroMultiSynth-Instruct

- [Taskboard #353](https://github.com/OpenEuroLLM/Taskboard/issues/353):
  concept discovery in prompt/response training datasets. The author provides
  [PrefScope](https://github.com/kargibora/PrefScope) and its
  [public viewer](https://github.com/kargibora/OELLM-JudgeLens).
- [Taskboard #437](https://github.com/OpenEuroLLM/Taskboard/issues/437):
  35-language synthetic instruction-generation via
  [synthgen](https://github.com/OpenEuroLLM/synthgen).
- [Release dataset](https://huggingface.co/datasets/openeurollm/EuroMultiSynth-Instruct):
  **4,160,598** rows; columns `id`, `language`, `messages` (user / assistant),
  `domain`, `persona` and `judge_score` (retained scores 7–10).
  License: Apache-2.0 in the dataset card.
- **Potential measurement gap:** the public dataset card reports that **77.7% of retained rows have judge_score=10**, limiting score discrimination *within the released subset*. This is not proof of poor judging: the upstream quality filter selected these rows. The proposed audit must compare against this existing field and against separate human-labeled controls.
- PrefScope's [table mapper](https://github.com/kargibora/PrefScope/blob/main/prefscope/data/tabular.py)
  understands roles such as `user:first` / `assistant:last` and
  records model/data provenance. This suggests a small input-format bridge;
  **no end-to-end data+model run has been performed here**.

**New proposed experiment — not yet executed:**

1. Capture the exact HF dataset revision. Select a fixed-seed, stratified,
   small sample from German/French and Basque/Irish (high/low data counts).
   Equal sample sizes per language; preserve `domain` and `judge_score`.
2. **No-LLM baseline first:** tabulate language × domain × score;
   inspect random and low-scoring cases. A concept difference is interesting
   only if it adds information beyond these known source metadata.
3. Use a documented PrefScope lens on the same prompt/response pairs.
   Check lens language coverage and **held-out label verification** before
   interpreting feature counts. Never compare raw activation magnitudes
   across languages as though they were calibrated.
4. Require independently reviewed *actionable* example groups (e.g.
   missing task intent within a language) and an explicit, small counterfactual
   intervention (reweight, regenerate or filter a bounded held-out subset).
5. Verify with a fixed model-quality task/baseline and cost estimate.
   If no stable new signal appears, **stop**; do not contact the developers
   merely about an attractive concept map.

**Important:** Both efforts are within OpenEuroLLM; they might already
coordinate privately. This is a **possible useful internal handoff**, not
a newly discovered cross-organization contact.

**Current decision:** `test_small_sample_first`. No suggested external
message until a reproducible gain or a concrete unanswered interface question.

## Opportunity B — Prelude long context #392

[Taskboard #392](https://github.com/OpenEuroLLM/Taskboard/issues/392)
is a documented technical blocker candidate. New public comments already
contain controlled investigation of early EOS in RULER QA, comparisons with
different checkpoints, P(EOS) probes, and release discussion. Existing work
is unusually thorough; generic advice to "try different decoding" or
"evaluate long context" would repeat their experiments.

[AllenAI StateBench](https://github.com/allenai/olmo-eval/blob/main/src/olmo_eval/evals/tasks/state_bench_lc.py)
provides a genuinely different *state-tracking* test, with explicit 128k/256k
token strata. **However:** it uses multiple-choice log-likelihood scoring,
not the problematic generative `Answer:` continuation. It could reveal
additional long-context weaknesses; it would **not diagnose or fix** the
early-EOS failure by itself. Tokenizer compatibility, test costs and the team's
existing benchmark coverage are unknown.

**Current decision:** `no_outreach_without_gap`; the release team already
has an active diagnosis. First establish whether a missing independent
state-tracking measurement would change their checkpoint decision.

## Can other LLMs help?

Yes, but with different tasks and outputs, **not** majority voting:

1. **Proposer (different model):** suggest one reusable artifact and a
   falsifiable intervention.
2. **Skeptic (independent model family):** look for duplication, already
   documented coordination, wrong task interface, confounding and missing data.
3. **Experimenter (independent model family if feasible):** specify the
   cheapest controlled test, cost, baseline, metric and stop condition.
4. **Human:** read actual sources; choose whether to run anything or make contact.

A review from three tools using the **same underlying model** is not
independent. Even different model families can share systematic error.
See [Apple research on correlated judge errors](https://machinelearning.apple.com/research/correlated-llm-evaluation-panels).
Different models do not independently verify factual claims just by agreeing.

Use [`research_interventions.py`](../../research_interventions.py)
with the source-backed
[`CONCEPT_AUDIT_CASE.json`](CONCEPT_AUDIT_CASE.json).
The script prepares three prompts without calling a model or showing the curator's intervention proposal to the independent reviewers. Review JSON is
checked for valid roles, cited source URLs, and differing model families.
A successful gate means `human_review_only`, **never "verified impact"**.
This is a preparation protocol, not an evaluation of model quality.

## PowerShell pilot

```powershell
python -m unittest discover -s tests -p "test_research_interventions.py" -v
python .\research_interventions.py prepare --case .\results\interventions\CONCEPT_AUDIT_CASE.json --dir .\results\interventions\review_run
Get-Content .\results\interventions\review_run\proposer.prompt.txt -Raw | Set-Clipboard
```

Paste each of the three role-specific prompts into a **different** model's
conversation (Claude / Copilot / OpenCode or a local Ollama model), separately,
without showing it the other responses. Save their exact JSON answers as
`proposer.json`, `skeptic.json`, `experimenter.json` in `review_run`.
Do not publish raw chats or secrets.

```powershell
python .\research_interventions.py evaluate --case .\results\interventions\CONCEPT_AUDIT_CASE.json --dir .\results\interventions\review_run
```

**Current status:** Only the code, tests and source cards have been added.
This transcript has not executed other model families or a GPU evaluation.
No external project contacts have been made.

## How we measure acceleration (future)

- Discovery precision against blinded, independent human labels;
- Review time spent *per accepted actionable intervention*;
- Confirmed reuse or correctly avoided redundant implementation;
- Measured time-to-decision or model-quality/cost difference after control;
- Confirmed new introductions, tracked separately from within-project handoffs.

Never treat number of AI-generated suggestions or model votes as speedup.
