# Prelude checkpoint-matched benchmark controls

Collected: 2026-11-08T14:13:59.118243+00:00 UTC.

Source: [openeurollm/prelude-base-eval-scores](https://huggingface.co/datasets/openeurollm/prelude-base-eval-scores) and [research issue #163](https://github.com/OpenEuroLLM/oellm-eval/issues/163).
All data are published evaluation aggregates; no evaluation was rerun.

Dataset revision: cf5f9d05ee6e2485273e7ebea7320645c7f6d778 (modified 2026-11-06T10:04:28.000Z).
Original source files inspected: 5; their SHA256 and provenance URLs are in the JSON evidence.

## Per-task data quality

| Task / metric | Rows | Valid | Config variants | Sample-count variants | Verdict |
| --- | ---: | ---: | ---: | ---: | --- |
| coqa_gen_f1 | 107 | 107 | 1 | 1 | comparable |
| coqa_mc_acc | 107 | 107 | 1 | 1 | comparable |
| squad_gen_f1 | 107 | 107 | 1 | 1 | comparable |

Overall: **comparable**.

## Changes on the same checkpoints

Common checkpoint steps: **107**; successive matched pairs: **106**.

| Task / metric | Median absolute change | Largest absolute change |
| --- | ---: | ---: |
| coqa_gen_f1 | 0.0705 | 0.4244 |
| coqa_mc_acc | 0.0087 | 0.0644 |
| squad_gen_f1 | 0.0044 | 0.0153 |

## Checkpoint pair with strongest matched CoQA-F1 change: 1,092,000 to 1,094,400

| Task / metric | Earlier | Later | Difference |
| --- | ---: | ---: | ---: |
| coqa_gen_f1 | 0.3202 | 0.7446 | +0.4244 |
| coqa_mc_acc | 0.8560 | 0.8610 | +0.0050 |
| squad_gen_f1 | 0.9012 | 0.9047 | +0.0034 |

## Interpretation and limits

These are checkpoint-matched, within-task changes in published aggregate scores. F1 and accuracy are different metrics; their raw levels should not be compared, and even their changes are descriptive, not statistical proof.
Similar control stability would narrow the investigation toward CoQA generative evaluation or checkpoint-specific generation behavior, not establish a root cause. Per-example predictions and repeated runs would be needed to diagnose that cause.

Exact source rows, aligned step identities, scores and computed changes are stored in results/prelude_controls.json.
