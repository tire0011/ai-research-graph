# AIoD source-adapter pilot — not a verified collaboration

The optional read-only pilot adds **two independent steps** to the European
requirements reports without changing the existing GitHub research graph,
scheduled jobs or evidence tiers:

1. `aiod_catalogue_probe.py` requests a bounded sample of **AI-on-Demand
   public REST v2 metadata** for `projects`, `datasets` or `publications`.
2. `aiod_cross_compare.py` compares this sample to **open GitHub issue/PR
   descriptions** in the existing `results/snapshot.json`. Its output is a
   review queue of overlapping words, *not* duplicate work or human contact.

## Provenance and endpoint assumptions

- Official [REST usage documentation](https://aiondemand.github.io/AIOD-rest-api/using/)
  illustrates bounded catalogue lists. The
  [v1-to-v2 migration guide](https://aiondemand.github.io/AIOD-rest-api/using/migration-v1-v2/)
  introduces `/v2/projects`, `/v2/datasets`, `/v2/publications` and the
  unified `identifier` field. The
  [Python SDK project reference](https://aiondemand.github.io/aiondemand/api/assets/projects/)
  describes listing results as `list[dict]`.
- Documentation mentions both `api.aiodp.eu` and `api.aiod.eu`. These are the
  **only allowed API hosts**; the current default is `https://api.aiodp.eu`.
  **The default host was successfully queried live on 2026-11-11:** bounded
  responses for projects, datasets and publications all returned a v2 list.
  In particular, projects use `description: {plain: "..."}`; the adapter now
  explicitly handles this observed shape. The alternate host, catalogue-wide
  completeness, API stability and authentication requirements are unverified.
- Each entry carries a stable v2 catalogue ID, its listing-page URL, raw
  canonical metadata SHA256, and a *claimed* external link if supplied.
  An external platform's identity is **not verified** by that claim.
- The probe is limited to 25 results/page and three pages (75 maximum),
  uses GET only and a 12-second timeout, and does not read private records.
  A full last page is flagged as `sample_limited`; do not infer coverage.
- Source `data_quality` records description completeness and collisions on
  claimed external URLs and normalized titles. These indicate **potential
  metadata aliases**, not independently duplicated research efforts. The
  lexical comparator collapses identical claimed external URLs within its
  source sample to avoid ranking them as separate opportunities.

## Run on a machine with access (Windows PowerShell)

From the repository root:

```powershell
python -m unittest discover -s tests -p 'test_aiod*.py' -v
python aiod_catalogue_probe.py --type projects --limit 10 --pages 2
python aiod_cross_compare.py --aiod results/aiod/projects.json --snapshot results/snapshot.json
```

If the documented default endpoint is unavailable, the alternate documented
host can be tried explicitly:

```powershell
python aiod_catalogue_probe.py --host https://api.aiod.eu --type projects --limit 10
```

The probe writes `results/aiod/projects.json` and `.md` **on success only**;
fetch/parse errors keep the previous successful result. The comparator writes
`CROSS_SOURCE_CANDIDATES.json` and `.md` only after a valid successful sample.
Generated outputs must be reviewed before committing; do not check in any
failed or fabricated "live" results.

The [2026-11-11 pilot findings](results/aiod/PILOT_FINDINGS.md) include a
source-backed quality assessment and results of the initial bounded queries.

## Targeted search pilot against five open OpenEuroLLM issues

`aiod_targeted_search.py` separately uses the **official v2 search API**
(`GET /search/{asset_type}`), verified against the service's OpenAPI schema
on 2026-11-11. The search response has the shape
`{total_hits, resources, offset, limit}`; this differs from the catalogue
listing endpoint's bare `list[dict]`. It uses explicit `search_query`,
`search_fields=name`, and `get_all=true`, with at most five returned results
per search and three concurrent reads. Search phrases, issue IDs and asset
types are fixed in code before inspecting the results; no source mutation or
external messaging is possible. Reports retain source IDs, URLs, titles and
metadata hashes rather than copying full third-party publication abstracts.

```powershell
python aiod_targeted_search.py --limit 5
python -m unittest discover -s tests -p 'test_aiod_targeted_search.py' -v
```

The recorded [targeted retrieval results](results/aiod/TARGETED_SEARCH_RESULTS.md)
and [five-case technical review](results/aiod/TARGETED_REVIEW.md) show mostly
single-word false positives. The reported title-term gate only determines a
review priority; it is **not** a collaboration score. A failed search leaves
the previous successful results untouched.

## What to review in a candidate

1. Are both source URLs and descriptions real, current and independently read?
2. Do both teams address **the same requirement**, or merely share technical
   vocabulary? What maturity or artifact can actually transfer?
3. Are they already collaborating, reusing the same repository, or citing one
   another? If unknown, keep `existing_coordination: unknown`.
4. Is a concrete joint improvement feasible, with maintainers and consent?
   Only human review can mark a genuinely new collaboration.

## Existing technology and next experiment

AIoD already publishes
[`aiondemand/aiod-enhanced-interaction`](https://github.com/aiondemand/aiod-enhanced-interaction),
an open-source semantic search/embedding service for its catalogue. This may
be a stronger retrieval baseline than our lexical script. **We should compare
retrieval with that existing service before building another vector database.**
Our proposed differentiation is *requirement equivalence, complementary work,
artifact compatibility and human-agent handoffs* — not merely search relevance.

The next useful experiment is a small **blinded, independently reviewed** set
of real AIoD ↔ GitHub cases: label same requirement, complementary,
already-coordinating, unrelated and unknown, then measure false positives and
review effort against lexical and existing semantic retrieval. Until that
exists, all cross-source hits are `unreviewed_lexical_overlap` and
`novel_collaboration_confirmed: false`; no messages are sent.
