# AI Research Graph — feasibility probe

Read-only prototype for linking research metadata across [OpenEuroLLM GitHub](https://github.com/OpenEuroLLM), [Hugging Face](https://huggingface.co/openeurollm) and [OpenAIRE](https://graph.openaire.eu/).

**Goal:** find demonstrable links between live engineering tasks and open research artifacts; measure gaps before proposing any additional infrastructure. This is independent of the Nexus agent project.

## Workflow

The [Research graph probe](.github/workflows/research-graph.yml) runs on the default branch, manually, and weekly on Monday. It publishes:

- [`results/REPORT.md`](results/REPORT.md): small human-readable coverage and linkage report.
- [`results/snapshot.json`](results/snapshot.json): source nodes, edges, provenance URLs, and errors.
- GitHub Actions artifact containing both files.
- [`QUALITY_REVIEW.md`](QUALITY_REVIEW.md): inspectable baseline audit, false-positive examples and unresolved relationships.

It uses only public endpoints and the built-in GitHub Actions token. No local PC or GPU is required. The GitHub token is used only for read access to source issues and committing generated results to this repository.

## Local run (optional)

```powershell
python -m unittest discover -s tests -v
python research_graph.py --output results
```

## Evidence and limits

Links explicitly mentioning a complete Hugging Face repository URL/ID are labeled `explicit_reference`; matching a sufficiently specific artifact slug produces a `candidate` needing review. Prefix overlaps (e.g. `tokenizer-256k` vs `tokenizer-256k-v2`) are not accepted as matches, nor are name-only mentions that explicitly refer to a different owner (e.g. `allenai/model` instead of `openeurollm/model`). These labels describe *textual evidence*, not scientific validity or proven dependency. Each edge includes its exact matched text and nearby context for inspection. The probe deliberately does not use an LLM to invent missing relationships.

The probe also extracts explicit **DOI and modern arXiv IDs** from GitHub issue bodies and Hugging Face model/dataset cards, and reads publication `pids` in OpenAIRE Graph. Matching records receive a separate `identifier_match` edge. A shared ID reliably identifies a referenced publication but **does not prove that an implementation uses, reproduces, or validates that paper**. For example, five `openeurollm` Hugging Face models reference arXiv `2609.24797` in metadata, and OpenAIRE's *Complex KDA* publication has the same identifier. DOI `10.48550/arxiv.2609.24797` is recognized as the arXiv mirror.

Beyond the OpenEuroLLM keyword search, the workflow resolves up to **12 arXiv citations** from GitHub issues using OpenAIRE's `ids.arxiv` filter (open issues and recent updates first; up to three concurrent requests). The report marks any skipped citations or failed API lookups as incomplete coverage. Older non-numeric arXiv identifier formats are not yet supported. This is a sampling limit, not a global research index.

The report separates **open vs closed** GitHub issues and PRs, and measures duplicate IDs, duplicate edges, missing link endpoints, and missing update timestamps. API failures remain visible; no missing response is silently interpreted as zero hits.

OpenAIRE results are a keyword-search sample plus the bounded citation lookup, not an exhaustive count of OpenEuroLLM research products. The report preserves source errors rather than silently treating missing responses as zero matches. GitHub retrieval has a `max_pages=10` safeguard per repository, so very large projects may need pagination adjustments.

### Next validation step

Manually annotate name-only candidates against their source links; measure precision, missed relations and data freshness. Only then consider a common graph service or MCP interface. A reference to an artifact does not establish a causal dependency on it.
