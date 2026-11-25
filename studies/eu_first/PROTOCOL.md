# EU-first research pilot

The global knowledge corpus is retained. EU-27 is the starting point for research opportunities, not a filter on scientific truth.

1. Query OpenAIRE Graph v4 for arXiv-indexed publications in four topical queries over the last 180 days using its documented `authorships.countries` filter (27 EU member codes). Results are source-discovery candidates only.
2. Resolve up to 20 distinct arXiv identities to exact versions in a single batch. Reuse the existing affiliation resolver for up to 12 papers and 32 ROR requests. Explicit paper affiliations plus an unambiguous registry candidate with exclusively EU-listed locations establish an EU evidence candidate, not independent verification. Mixed locations, missing evidence and stale versions remain unknown. Author nationality is never inferred.
3. Select up to 20 EU candidates and 10 global comparators. Report shortages; do not pad the EU cohort. Exclude known manually reviewed papers. This is a bounded exploratory sample, not a census, independent validation, or representative EU benchmark.
4. The existing hypothesis comparator now supports a version-ID-to-geography mapping. Both arms use identical eligibility and priority: EU–EU, EU–non-EU, EU–unknown. Global-only pairs are retained in the background corpus but excluded from the EU action shortlist. Unknown is not non-EU. This does not prove incremental scientific usefulness.
5. Review source evidence and candidate affiliations before calling them verified. The live CI produces the geography manifest and provenance records; it does not run paid models, claim collaboration or send mail. The subsequent frozen abstract/model test must explicitly handle the up-to-30-item cohort in bounded batches, use independent labels and measure useful actionable proposals rather than counts.

Run the read-only pilot against an existing discovery snapshot:

```powershell
python eu_first_research.py --snapshot results/source_candidates.json --output results/eu-first
```

Pass `--previous results/eu-first/eu_first.json` on a later run to reuse versioned papers and affiliation cache. Publication indexing lag, bounded pages, author-header availability and ROR ambiguity can constrain recall. No cumulative automated state publishing is enabled by this pilot.

Source documentation: https://graph.openaire.eu/docs/apis/graph-api-v4/research-products/filter-syntax/
