# Code-state recheck: OpenEuroLLM post-training #35

Date: 21 November 2026. Original issue: https://github.com/OpenEuroLLM/post-training/issues/35

**Why this matters:** the issue remains open and without an assignee, and the first human review rated it a plausible new coding contribution (tier 2). Direct code inspection shows that **some requested changes appear to exist already**. An issue's unchanged `updated_at` is not enough to infer that the underlying code remains untouched.

## Rechecked default-branch code (commit `681ee6d7a9a28f312b993ea83f7f582271fe6eda`)

- [`scripts/train.py`](https://github.com/OpenEuroLLM/post-training/blob/681ee6d7a9a28f312b993ea83f7f582271fe6eda/scripts/train.py): saves the resolved configuration to `run_dir/config.yaml` before constructing the trainer (lines 179–188).
- [`scripts/submit.py`](https://github.com/OpenEuroLLM/post-training/blob/681ee6d7a9a28f312b993ea83f7f582271fe6eda/scripts/submit.py): freezes `run_dir/config.yaml` before SLURM submission (lines 145–169).
- [`src/post_training/utils/logging.py`](https://github.com/OpenEuroLLM/post-training/blob/681ee6d7a9a28f312b993ea83f7f582271fe6eda/src/post_training/utils/logging.py): for the default INFO level, installs `NullHandler` when `RANK > 0` (lines 10–19).
- [`src/post_training/config.py`](https://github.com/OpenEuroLLM/post-training/blob/681ee6d7a9a28f312b993ea83f7f582271fe6eda/src/post_training/config.py): `save()` serializes the configuration to YAML (lines 412–414).

These observations partially address **two** of the original three requirements. They are code observations, **not** a claim that all logging requirements are met: copying the original YAML verbatim differs from saving the effective resolved configuration; the request for configuration in a log output file still needs clarification; and non-INFO log levels may behave differently.

## Revised *current* decision

- Original historical non-blinded assessment: tier **2** (plausibly scoped).
- **Code-informed correction:** tier **1**, `partial_implementation_observed`: **ask for precise remaining acceptance criteria before recommending as new work**.
- Do **not** rewrite the original frozen five-vs-five study after seeing the code. Preserve both assessments as separate, dated evidence, and do not interpret the historical 1/5 baseline as the current count of ready tasks.
- The code-dependent correction is **only valid if both issue state and checked default-branch commit match**. Missing code access or any later commit forces `code_revision_unverified`; an old tier-2 label must never silently return.

## Implication for the research graph

An actionable developer suggestion needs three linked evidence levels, not just an open GitHub task: **issue/discussion → existing implementation and PR history → what acceptance criteria remain unfinished**. This code-state recheck is a narrow proof of the requirement, not a general solution across all source repositories.
