# AI Research Graph — feasibility probe

Read-only prototype for linking research metadata across [OpenEuroLLM GitHub](https://github.com/OpenEuroLLM), [Hugging Face](https://huggingface.co/openeurollm) and [OpenAIRE](https://graph.openaire.eu/).

**Goal:** find demonstrable links between live engineering tasks and open research artifacts; measure gaps before proposing any additional infrastructure. This is independent of the Nexus agent project.

## Workflow

The [Research graph probe](.github/workflows/research-graph.yml) runs on the default branch, manually, and weekly on Monday. It publishes:

- [`results/REPORT.md`](results/REPORT.md): small human-readable coverage and linkage report.
- [`results/snapshot.json`](results/snapshot.json): source nodes, edges, provenance URLs, and errors.
- GitHub Actions artifact containing both files.
- [`QUALITY_REVIEW.md`](QUALITY_REVIEW.md): inspectable baseline audit, false-positive examples and unresolved relationships.
- [`results/QA_EVIDENCE.md`](results/QA_EVIDENCE.md): four auditable cross-platform question evidence packets, regenerated from the latest graph.
- [`QA_AI_REVIEW.md`](QA_AI_REVIEW.md): the first one-time AI answer trial, including evidence limits and cases that require abstention.

It uses only public endpoints and the built-in GitHub Actions token. No local PC or GPU is required. The GitHub token is used only for read access to source issues and committing generated results to this repository.

If an essential API fails (e.g. a GitHub gateway timeout), the run keeps the partial diagnostic report as an Actions artifact but **exits unsuccessfully before committing new results**. This preserves the last complete report in the repository.

## Local run (optional)

```powershell
python -m unittest discover -s tests -v
python research_graph.py --output results
python qa_probe.py --snapshot results/snapshot.json --output results/QA_EVIDENCE.md
```

## Evidence and limits

Links explicitly mentioning a complete Hugging Face repository URL/ID are labeled `explicit_reference`; matching a sufficiently specific artifact slug produces a `candidate` needing review. Prefix overlaps (e.g. `tokenizer-256k` vs `tokenizer-256k-v2`) are not accepted as matches, nor are name-only mentions that explicitly refer to a different owner (e.g. `allenai/model` instead of `openeurollm/model`). These labels describe *textual evidence*, not scientific validity or proven dependency. Each edge includes its exact matched text and nearby context for inspection. The probe deliberately does not use an LLM to invent missing relationships.

The probe also extracts explicit **DOI and modern arXiv IDs** from GitHub issue bodies and Hugging Face model/dataset cards, and reads publication `pids` in OpenAIRE Graph. Matching records receive a separate `identifier_match` edge. A shared ID reliably identifies a referenced publication but **does not prove that an implementation uses, reproduces, or validates that paper**. For example, five `openeurollm` Hugging Face models reference arXiv `2609.24797` in metadata, and OpenAIRE's *Complex KDA* publication has the same identifier. DOI `10.48550/arxiv.2609.24797` is recognized as the arXiv mirror.

Hugging Face [model-card metadata](https://huggingface.co/docs/hub/model-cards) can also declare `base_model` and `datasets` by complete Hub repository ID. The probe creates `declared_metadata` edges only when the target repository is present in its indexed Hugging Face inventory. It follows **one hop** of references not present in the initial OpenEuroLLM inventory: at most 40 unique model/dataset targets are checked using the **public** Hugging Face API, with four concurrent workers. Only repositories whose identities the API confirms become additional nodes and edges. When the API returns a **different canonical ID** for the declared reference (e.g. after a rename), both are retained and the link is labeled `verified_redirect` / `declared_metadata_redirect`. Missing, inaccessible or failed lookups remain separate records in `external_hf_target_checks`. The original card declarations and their verification state remain in `external_hf_card_references`. The process does not recursively crawl third-party model cards or use a private token. Confirming a target exists does **not** independently verify training lineage.

Beyond the OpenEuroLLM keyword search, the workflow resolves up to **80 distinct arXiv citations** from both GitHub tasks and Hugging Face cards using OpenAIRE's documented `ids.arxiv` OR filter (batches of at most 40 IDs). The report now measures which cited IDs actually resolve, which are absent from the API response, and how many artifacts of each source type have resolvable citations. Skipped IDs and failed API batches are recorded explicitly. Older non-numeric arXiv identifier formats are not yet supported. This is bounded citation discovery, not a global research index.

The report separates **open vs closed** GitHub issues and PRs, and measures duplicate IDs, duplicate edges, missing link endpoints, missing update timestamps, and citation-lookup completeness. It also counts publications referenced from both GitHub and Hugging Face; such a two-source bridge does not establish a direct dependency between the engineering task and model. Declared Hugging Face lineage is reported separately from cross-platform references and ambiguous name-only candidates, including the one-hop target-verification outcomes. API failures remain visible; no missing response is silently interpreted as zero hits.

OpenAIRE results are a keyword-search sample plus the bounded citation lookup, not an exhaustive count of OpenEuroLLM research products. The report preserves source errors rather than silently treating missing responses as zero matches. GitHub retrieval has a `max_pages=10` safeguard per repository, so very large projects may need pagination adjustments.

### Next validation step

Run an independent LLM over the fixed evidence packets using a supported inference provider, then score answers against sourced citations and unsupported-claim avoidance. The GitHub Actions evidence check does **not** make an LLM call and therefore makes no claim of autonomous AI answer accuracy. Manually annotate name-only candidates and measure recall before considering a common graph service or MCP interface. A reference to an artifact does not establish a causal dependency on it.
