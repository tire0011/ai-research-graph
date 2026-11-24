# Automatic source discovery — cumulative, bounded pilot

Run locally with PowerShell:

```powershell
python eu_opportunity_discovery.py --discover-sources --output results/european_ai --previous-candidates .discovery-state/source_candidates.json
# Only after a successful run, preserve the cumulative state for the next run:
New-Item -ItemType Directory -Force .discovery-state | Out-Null
Copy-Item results/european_ai/source_candidates.json .discovery-state/source_candidates.json
```

The existing curated issue collector remains unchanged in scope. The opt-in expansion reads public GitHub organization repositories and Hugging Face author model/dataset metadata. It rotates up to four registry owners per week, bounds GitHub pagination to two pages, caches responses within a run, and records partial failures. Hugging Face owner names are search hints, not verified identity matches. European affiliation remains unknown; no candidates are promoted automatically.

## Cumulative discovery

- Schema 2 retains candidates, first/last observations, historical reference edges, and an explicit FIFO frontier. Schema 1 snapshots can be migrated. New flags and counts are relative to the previous successful state, not just the current owner sample.
- Explicit GitHub/Hugging Face metadata references enqueue public detail lookups, including links to previously unknown owners. Each confirmed detail can yield new references. At most 12 detail requests per normal run and 20 distinct targets per metadata record; remaining frontier entries carry over. Already-expanded targets and cycles are not re-expanded. Detail requests use fixed public API hosts, not arbitrary linked websites.
- Missing targets (404/410), excluded resources and identity mismatches are recorded separately. Transient errors retain the pending target and make the run unsuccessful. Public identity confirmation does not verify affiliation, technical dependency or collaboration. Historical references are not a claim of current relationships; periodic revalidation is outstanding.
- Successful default-branch workflow runs persist state as a Git commit on the dedicated `eu-discovery-state` branch. State is not dependent on an evictable Actions cache. A failed fetch or collection never overwrites last-known-good state. The push is non-forced, and scheduled discovery is serialized; a concurrent remote update must fail rather than lose data. The state branch contains only public metadata and is never a code or curated-source branch. Pull requests do not publish state.

## Verification

Offline fixture tests cover canonicalization, explicit references, repeat runs, partial failures, bounded pagination, migration, cumulative retention, multi-run recursion, cycles and missing targets. The same-repository PR workflow also runs a bounded read-only smoke test against actual public GitHub and Hugging Face endpoints using OpenEuroLLM as a seed. It checks nonempty listings and exact detail identities and uploads diagnostics. The smoke test does not publish state or prove all sources are covered. The scheduled-state branch publication itself requires a successful default-branch run and contents-write permission.

## Outstanding scope

- Hugging Face pagination, structured model-card lineage IDs, periodic freshness checks, RAISE, CORDIS and OpenAIRE adapters, verified affiliation and collaboration hypotheses.
- Independent ordinary-search comparison and evidence-backed contribution opportunities from newly discovered sources. The curated issue registry remains unchanged.
- RAISE machine-readable catalogue availability and CORDIS/OpenAIRE endpoint and schema validation are pending.

API documentation: [GitHub organization repositories](https://docs.github.com/en/rest/repos/repos#list-organization-repositories), [GitHub repository details](https://docs.github.com/en/rest/repos/repos#get-a-repository), [Hugging Face Hub API](https://huggingface.co/docs/hub/api).

No external posting, permanent server, paid API or claim of graph advantage.
