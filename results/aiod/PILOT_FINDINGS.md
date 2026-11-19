# Live AIoD metadata pilot — 2026-11-11

## Scope, not a catalogue-wide conclusion

Read-only queries to the official `https://api.aiodp.eu/v2/` catalogue succeeded:

| Asset | Sample | Description populated | Claimed-URL collision | Exhaustive? |
| --- | ---: | ---: | ---: | --- |
| [Projects](projects.json) | 20 | 20/20 | 2 groups / 4 records | No, 2 pages × 10 |
| [Datasets](datasets.json) | 10 | 0/10 | None observed | No, 1 page × 10 |
| [Publications](publications.json) | 10 | 10/10 | None observed | No, 1 page × 10 |

These are the **first API pages**, not a random sample. Descriptions under
`description.plain` were observed for projects; their absence in ten datasets
may be normal source sparsity, not evidence of a broken API. The sampled
catalogue records have distinct AIoD v2 IDs. Each result file records the
source URL, snapshot time, ID and canonical metadata SHA256.

## Concrete metadata-quality finding

Two pairs in the 20 projects have different AIoD IDs but the same **claimed
external URL and title**:

1. [Vado Filters robot assembly project](https://aire-edih.eu/en/project/2024-a-follow-up-project-for-testing-the-robot-assembly-of-intelligent-bag-filters-at-the-company-vado-filters-ou/):
   `proj_btUHkDO5tYPqOxCngsPJwH7d` and `proj_pvdOWA5GTKZcE8rMU0snoxbR`.
2. [Factory digital-twin optimization project](https://aire-edih.eu/en/project/2024-testing-of-the-applicability-of-an-ai-based-optimization-model-for-production-processes-using-a-digital-twin-of-the-factory/):
   `proj_1MVNkveOqhAYqb51E7CF0ZrT` and
   `proj_XgQps8wcm90nZkqms8DdAO0p`.

**Quality impact:** 4/20 records (20%) belong to two possible alias groups in
this small, non-random page sample. We cannot generalize that percentage to
AIoD as a whole or verify that the external source itself is duplicated.
The comparator therefore collapses repeated claimed URLs *within the sample*
to avoid inflated independent-opportunity counts. This is **duplicate
catalogue metadata**, not proof of parallel development by different humans.

## First cross-platform comparison: a negative result

The [GitHub evidence snapshot](../snapshot.json) contains 244 open tasks in
the relevant repositories. Our first baseline finds:

| AIoD type | Raw shared-token candidate pairs | Qualifying new human collaborations |
| --- | ---: | ---: |
| Projects (20 records; 18 unique claimed sources after local collapse) | 286 | 0 verified |
| Datasets (10 records) | 7 | 0 verified |
| Publications (10 records) | 226 | 0 verified |

The 15 top project overlaps in
[the review queue](CROSS_SOURCE_CANDIDATES.md) contain obvious topic mismatches,
e.g. **pallet movement detection** vs. **multilingual instruction tuning**;
**factory early-warning systems** vs. **tokenization decisions**. High shared
word scores from long descriptions are **not reliable requirement matching**.
These are quick qualitative counterexamples, not independently labeled
precision estimates. We cannot infer that *none* of the unreviewed pairs are
valuable, only that **no new collaboration is verified by this pilot**.

## Next controlled test

1. Define requirement-level positive and negative labels on blinded AIoD ↔
   GitHub case pairs, retaining both original URLs and technical artifacts.
2. Compare lexical retrieval against AIoD's
   [`aiod-enhanced-interaction`](https://github.com/aiondemand/aiod-enhanced-interaction)
   semantic service, when usable. Avoid rebuilding a vector database first.
3. Before considering human outreach, validate whether the teams are already
   coordinating, what artifact can be reused, and whether the owners agree.

No external messages were sent and no task or model-training claim was made.
