# Automatic source discovery — first increment

Run `python eu_opportunity_discovery.py --discover-sources --output results/european_ai --previous-candidates .discovery-state/source_candidates.json`.

The existing curated issue collector remains unchanged in scope. The opt-in expansion reads public GitHub organization repositories and Hugging Face author model/dataset metadata. It rotates up to four registry owners per week, bounds GitHub pagination to two pages, caches responses within a run, and records partial failures. Hugging Face owner names are search hints, not verified identity matches. Explicit URLs in metadata establish references only. Candidate affiliation remains unknown; no candidates are promoted automatically.

The existing weekly workflow uploads JSON and Markdown artifacts and caches the previous successful candidate snapshot. This is not yet a cumulative historical registry; returning owners may appear new again. Hugging Face pagination, recursive source following, project/publication adapters, verified affiliation and collaboration hypotheses remain outstanding. No external posting occurs.

Official API documentation to validate before extending:
- https://docs.github.com/en/rest/repos/repos#list-organization-repositories
- https://huggingface.co/docs/hub/api
- RAISE: machine-readable catalogue availability not established.
- CORDIS and OpenAIRE: endpoint and schema validation pending.

Verification: deterministic fixture tests cover canonicalization, explicit references, repeat runs, partial failures and bounded GitHub pagination. CI is configured to execute tests. Local repository clone failed because the execution environment cannot resolve github.com. Live endpoint smoke tests and a frozen independent ordinary-search comparison are outstanding; no evidence of graph advantage is claimed.
