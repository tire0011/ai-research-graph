# AI Research Graph — feasibility probe

Read-only prototype for linking research metadata across [OpenEuroLLM GitHub](https://github.com/OpenEuroLLM), [Hugging Face](https://huggingface.co/openeurollm) and [OpenAIRE](https://graph.openaire.eu/).

**Goal:** find demonstrable links between live engineering tasks and open research artifacts; measure gaps before proposing any additional infrastructure. This is independent of the Nexus agent project.

## Workflow

The [Research graph probe](.github/workflows/research-graph.yml) runs on the default branch, manually, and weekly on Monday. It publishes:

- [`results/REPORT.md`](results/REPORT.md): small human-readable coverage and linkage report.
- [`results/snapshot.json`](results/snapshot.json): source nodes, edges, provenance URLs, and errors.
- GitHub Actions artifact containing both files.

It uses only public endpoints and the built-in GitHub Actions token. No local PC or GPU is required. The GitHub token is used only for read access to source issues and committing generated results to this repository.

## Local run (optional)

```powershell
python -m unittest discover -s tests -v
python research_graph.py --output results
```

## Evidence and limits

Links explicitly mentioning a complete Hugging Face repository URL/ID are labeled `verified`; matching a sufficiently specific artifact slug produces a `candidate` needing review. These labels describe *link evidence*, not scientific validity of the underlying research. The probe deliberately does not use an LLM to invent missing relationships.

OpenAIRE results are a keyword-search sample, not an exhaustive count of OpenEuroLLM research products. The report preserves source errors rather than silently treating missing responses as zero matches. GitHub retrieval has a `max_pages=10` safeguard per repository, so very large projects may need pagination adjustments.

### Next validation step

Manually annotate 25 cross-platform candidate pairs against their source links; measure precision, missed relations and data freshness. Only then consider a common graph service or MCP interface.
