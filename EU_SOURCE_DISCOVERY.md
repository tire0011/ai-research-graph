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

## Generic source discovery from a single core source

The only new manually configured web seed is the official RAISE hub (`https://raise4science.eu/`); the existing curated GitHub registry is retained for historical comparisons and ongoing issue discovery. No RAISE-specific parser, CORDIS adapter or OpenAIRE adapter is needed to follow public links. `generic_source_discovery.py` discovers additional sources from HTML links, advertised RSS/Atom feeds, structured JSON URLs, and feed links, including sources in previously unknown domains. Platform references are routed to the existing GitHub/Hugging Face detail frontier; platform metadata also supplies web referrals. Source URL, literal href, resolved target, retrieval time and document hash are retained. The generic web overlay is part of the same cumulative state branch. A verified reference is not a verified initiative, affiliation or collaboration.

Format detection distinguishes HTML, JSON, RSS, Atom, OpenAPI and other unsupported XML/content. OpenAPI descriptions and unsupported formats generate explicit adapter-review proposals; the crawler never generates/executes arbitrary code, invokes OpenAPI operations, uses credentials, submits forms or performs write requests. General JSON link extraction is not a semantic integration of a catalogue. JavaScript-only pages, APIs requiring queries or authentication, binary documents and unlinked APIs are outside this iteration. A specialized adapter may still be required; an AI can develop and test it in a reviewed PR, but no automatic coding agent is enabled.

**Bounds and security:** eight content pages per weekly run, two per host, at most 40 HTTP requests including robots checks, a 1 MiB response cap, 30 ranked links per page and 5,000 retained web sources. Public HTTPS only, no query strings or URL credentials, no automatic redirects (a redirect is a new checked candidate), no proxy, cookies or tokens. The resolved address is checked for public routability and pinned to the TLS connection to prevent private-network access and DNS rebinding. robots.txt is checked before fetching, with rate limits; unavailable robots policies are retried, disallowed sources are not read. Source text is untrusted data. Partial web errors are separately reported and retried without discarding successful observations; no coverage completeness is claimed. Candidates, links and adapter proposals remain review-only; no outreach.

The PR live smoke runs a separate two-page probe beginning with RAISE alone, checks real link evidence, and uploads diagnostics. Fixture tests demonstrate discovery of a previously unknown domain and its feed, cross-platform handoff over subsequent runs, and failure and network-policy boundaries.

## Verification

Offline fixture tests cover canonicalization, explicit references, repeat runs, partial failures, bounded pagination, migration, cumulative retention, multi-run recursion, cycles and missing targets. The same-repository PR workflow also runs a bounded read-only smoke test against actual public GitHub and Hugging Face endpoints using OpenEuroLLM as a seed. It checks nonempty listings and exact detail identities and uploads diagnostics. The smoke test does not publish state or prove all sources are covered. The scheduled-state branch publication itself requires a successful default-branch run and contents-write permission.

## Outstanding scope

- Hugging Face pagination, structured model-card lineage IDs, periodic freshness checks beyond the core, semantic catalogue extraction, verified affiliation and collaboration hypotheses.
- Independent ordinary-search comparison and evidence-backed contribution opportunities from newly discovered sources. The curated issue registry remains unchanged.
- Discovery of specific RAISE Observatory, CORDIS or OpenAIRE catalogues depends on actual links and accessible formats; specialized integration is not assumed.

API documentation: [GitHub organization repositories](https://docs.github.com/en/rest/repos/repos#list-organization-repositories), [GitHub repository details](https://docs.github.com/en/rest/repos/repos#get-a-repository), [Hugging Face Hub API](https://huggingface.co/docs/hub/api).

No external posting, permanent server, paid API or claim of graph advantage.

## Discovered repository review

The weekly workflow now reads up to 12 discovered GitHub repositories from the cumulative state, excluding existing curated sources. It re-fetches public metadata, checks exact identity, owner, activity, license hint, issue availability and explicit technical vocabulary. Least-recently reviewed candidates are sampled first; ties are balanced across owners. At most four eligible repositories are passed to the existing conservative issue/PR state checker (up to eight sampled issues and two deep checks per repository). Discovered-source review explicitly opts into single-owner issue analysis; the curated multi-organization default is unchanged. License metadata is reported, not used to exclude public issue review or topic overlap. Reuse requires separate license review. Topic overlap is independent of issue availability and activity gates.

Outputs: `SOURCE_TRIAGE.md` and `source_triage.json`, including at most five potential tasks and five cross-owner topic hypotheses, original metadata evidence, invitation labels and limitations. A topic match is not a verified technical handoff. Owner affiliation is only contextual evidence from the curated registry, not independently verified geography; unknown owners are explicitly marked unknown. A public issue label does not prove that maintainers will respond. The result includes the existing same-pool title baseline, not an independent test of research usefulness.

Successful reviews are persisted alongside discovery state on `eu-discovery-state`; a failed review preserves the previous successful review and does not block discovery state publication. The workflow uploads diagnostics, and the read-only PR smoke test reviews the live published source snapshot. Existing curated sources and prior research results are unchanged.

To run against a saved snapshot (PowerShell):

```powershell
python discovered_source_triage.py --snapshot .discovery-state/source_candidates.json --previous .discovery-state/source_triage.json --output results/european_ai
```

This is a bounded rule-based baseline, not an LLM semantic evaluator. Web/HF content relevance, verified European affiliation, requirement-level collaboration matching, independent review and automatic adapter development remain follow-up work. Adapter-review requests are visible in the report; no new executable code is generated or executed from a discovered source.

### First live review and correction (2026-11-24)

The initial live run (45400789813) reviewed 12 of 159 repositories and returned zero tasks and zero topic hypotheses, without API errors. Only one repository passed the original combined gates, so no issue analysis ran. The same data revealed that license hints were incorrectly used as a prerequisite for discovering topical overlaps and reading public issues. The gates have been separated and the report now includes selection counts. Re-running the same cohort is a regression check, not independent evidence of improved discovery. The original negative result is retained in the original workflow artifacts. Sparse descriptions and coarse vocabulary remain limitations.
