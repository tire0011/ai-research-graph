# AI Research Graph — feasibility probe

Read-only prototype for linking research metadata across [OpenEuroLLM GitHub](https://github.com/OpenEuroLLM), [Hugging Face](https://huggingface.co/openeurollm) and [OpenAIRE](https://graph.openaire.eu/).

**Goal:** find demonstrable links between live engineering tasks and open research artifacts; measure gaps before proposing any additional infrastructure. This is independent of the Nexus agent project.

## Feasibility verdict

**A cross-platform evidence graph is feasible; the need for a permanent graph service or MCP is not yet demonstrated.** In the audited snapshot of **920 nodes**, we found **35 explicit URL/ID references**, **89 shared scholarly identifiers**, and **75 metadata declarations**. These are separate evidence levels, not 199 confirmed research dependencies: a shared paper ID or a dataset declaration does **not** prove an artifact was used in training or reproduction. The immediate next step is to test whether the existing, versioned snapshot answers concrete research questions better than direct searches; only then decide whether a shared query service is worth maintaining.

## Experimental research-intervention review (2026-11-12)

The [research intervention pilot](results/interventions/PILOT.md) reframes
cross-project matching as **testable actions that might remove a research
bottleneck**. The first case examines possible reuse of PrefScope to audit
EuroMultiSynth-Instruct data; a separate note explains why the ongoing Prelude
long-context EOS investigation should not receive duplicate advice.

Run the optional [offline multi-model review harness](research_interventions.py)
with [source-backed case input](results/interventions/CONCEPT_AUDIT_CASE.json).
It prepares three independent prompts (proposer, skeptic, experimenter) and
validates returned JSON evidence references. **No other LLM has been run here**;
no automated outreach, model voting, test of scientific benefit or claim of
unknown collaborators. The independent prompts can also be executed against **installed local Ollama models** via [the PowerShell 7 runner](tools/run_local_llm_review.ps1), with [editable example model configuration](results/interventions/ollama_models.example.json). Tests are in
[`tests/test_research_interventions.py`](tests/test_research_interventions.py).

## Workflow

The [Research graph probe](.github/workflows/research-graph.yml) runs on the default branch, manually, and weekly on Monday. It publishes:

- [`results/REPORT.md`](results/REPORT.md): small human-readable coverage and linkage report.
- [`results/snapshot.json`](results/snapshot.json): source nodes, edges, provenance URLs, and errors.
- GitHub Actions artifact containing both files.
- [`QUALITY_REVIEW.md`](QUALITY_REVIEW.md): inspectable baseline audit, false-positive examples and unresolved relationships.
- [`results/QA_EVIDENCE.md`](results/QA_EVIDENCE.md): four auditable cross-platform question evidence packets, regenerated from the latest graph.
- [`results/RETRIEVAL_BENCHMARK.md`](results/RETRIEVAL_BENCHMARK.md): first controlled comparison of graph traversal against plain-text search of the same captured records. Includes positive and abstention questions; it is not a live search or MCP benchmark.
- [`results/HOLDOUT_EVIDENCE.md`](results/HOLDOUT_EVIDENCE.md): ten additional questions sampled from actual issues before examining their bodies, with fresh GitHub source checks, SHA256 text parity, and separate counts of cross-platform evidence and resolvable GitHub task references.
- [`results/RESEARCH_QUESTIONS.md`](results/RESEARCH_QUESTIONS.md): twenty fixed task-reference questions comparing a graph lookup, an ordinary text search of the same snapshot, and live GitHub issue/PR title search. Includes strict live source-text verification and clearly separated random/reference-rich cohorts.
- [`results/MULTIHOP_EVIDENCE.md`](results/MULTIHOP_EVIDENCE.md): twenty explicitly scoped two-hop questions (`GitHub task → referenced task → mentioned HF artifact`), with an independently re-read original-source audit and a fair source-following comparison that is also allowed to traverse both hops.
- [`results/IMPACT_EVIDENCE.md`](results/IMPACT_EVIDENCE.md): ten independently re-read, purposefully chosen OpenEuroLLM change candidates; traces exact issue-body and comment claims, an explicit upstream dependency, provisional throughput evidence and gaps in existing graph coverage.
- [`results/OPPORTUNITIES.md`](results/OPPORTUNITIES.md): a small **human-review queue** of evidence-backed opportunities with responsible public GitHub contacts, proposed verification and clickable original sources; no messages or labels are sent.
- [`QA_AI_REVIEW.md`](QA_AI_REVIEW.md): the first one-time AI answer trial, including evidence limits and cases that require abstention.
- [`CASE_STUDY_OPENTHINKER3.md`](CASE_STUDY_OPENTHINKER3.md): a deeper end-to-end investigation of a real reproduction objective, including data-processing evidence and missing experimental provenance.

It uses only public endpoints and the built-in GitHub Actions token. No local PC or GPU is required. The GitHub token is used only for read access to source issues and committing generated results to this repository.

If an essential API fails (e.g. a GitHub gateway timeout), the run keeps the partial diagnostic report as an Actions artifact but **exits unsuccessfully before committing new results**. This preserves the last complete report in the repository.

The retrieval comparison is intentionally narrow: both methods see the same snapshot; the graph uses verified provenance edges and the baseline scans source-record text without joins. Target recall@10 and in-memory timings are descriptive engineering measurements, not evidence of researcher productivity or autonomous AI answer quality. The next experiment needs unseen researcher questions and a live GitHub/Hugging Face search baseline.

The separate [ten-issue holdout study](.github/workflows/holdout-study.yml) checks newly sampled original GitHub issue texts against the stored graph after a successful graph run. It measures source coverage, textual evidence fidelity, and whether the graph actually has sourced cross-platform relationships for realistic questions. Sources are read again independently with the built-in GitHub token; API failures **fail this companion job without overwriting the last good study**. This is issue-level evidence verification, not a blind evaluation of an autonomous research agent or a comparison of human research time. Multiple result-writing workflows retry their Git rebase/push to avoid losing valid evidence when they complete concurrently.

The separate [twenty-question comparison](.github/workflows/research-questions.yml) uses twenty fixed task title-search phrases and manually frozen, source-grounded issue/PR reference targets. Ten tasks were sampled by deterministic ID hashing without reading their bodies; ten deliberately contain GitHub references, including cross-repository links. The comparison uses the **same repository, task type, and search phrase** for the graph and text-snapshot methods and GitHub's live issue/PR search API. All methods must identify the correct source task and exact set of indexed target task IDs, including returning no target when none exists. Fresh original GitHub issue/PR text, update timestamps, and a second text-reference parser independently check the frozen targets; inconsistent sources and API errors create diagnostics, **not misleading zeros or replacement of last-good results**. Reported in-memory lookup milliseconds are **not comparable** with live API search latency: index construction, network transfer, caching and rate limits differ. The results are a *technical reference retrieval test*, not a blinded human study, free-form AI answer benchmark, or proof that an MCP server saves research time. The seeded sample and reference-rich sample are reported separately so the enriched positives cannot masquerade as an unbiased population estimate.

The separate [two-hop evidence comparison](.github/workflows/multihop-benchmark.yml) tests the exact sequence **task mentions task → that task explicitly mentions an indexed Hugging Face resource**. Its 20 fixed cases deliberately include nine positive-source chains and eleven abstention controls, several containing a genuine first-hop GitHub link but no evidenced HF second hop. These are stratified, source-selected cases, **not a blinded or representative sample**. The benchmark re-fetches both source issues/PRs from public GitHub, verifies their bodies and update timestamps, checks frozen path annotations using a raw-text parser, and only then compares graph traversal to a **source-following baseline that is allowed to open the intermediate task and inspect its text**. On source changes or API errors, it records diagnostics without replacing successful evidence. Local timings exclude data acquisition and graph construction, so they cannot establish researcher productivity or the total payoff from operating a persistent service. A link to a dataset or model still does not prove that it was used in training or that an experiment succeeded.

The independent [ten-task change-impact audit](.github/workflows/impact-study.yml) asks a different question: **which actual tasks might remove a bottleneck, accelerate training or automate research work?** Its deliberately selected issues are not presented as an unbiased top-ten ranking. The companion job independently reads live issue bodies and specific original issue comments, checks frozen source excerpts and SHA256, and distinguishes a provisional reported throughput improvement from a cross-hardware gap, a quality improvement, a reported OOM blocker, a clearly declared task dependency and unmeasured automation ideas. It reports source drift separately from missing source evidence and fails without overwriting last-good results if a required source disappears. The graph now also stores a **bounded sample of those original comments** and their checksums; the audit independently checks whether the selected comment bodies and separately labeled dependency/blocker claims survived indexing. Comments outside that sample remain unindexed, so absence of a blocker in graph edges must not be treated as real-world absence. No time-saving, scientific or causal improvement is inferred solely from cross-references.

The [opportunity detector](opportunity_detector.py) runs **after** that original-source audit, using its verified JSON rather than unverified text matching. It recognizes three narrowly defined signals: reported speedups awaiting validation, explicitly declared upstream dependencies, and commenter-reported memory blockers. Each record carries original URLs, hashes, evidence limitations, a concrete follow-up check, and the GitHub assignee (or clearly labeled issue-author fallback) read from the public live issue. It **never contacts people or adds tags**; the report and [`results/opportunities.json`](results/opportunities.json) are review-only suggestions. A stale graph, missing source proof or failed comment parity stops publication rather than creating a misleading recommendation. This is a demonstration of the proposed human–AI interface, not project-wide detection or coordination infrastructure.

## Separate Prelude benchmark probes

The independent [Prelude benchmark workflow](.github/workflows/prelude-benchmarks.yml) starts after a successful graph workflow or manually, without affecting graph collection. It inspects published Prelude checkpoint scores from the
[OpenEuroLLM Prelude benchmark dataset](https://huggingface.co/datasets/openeurollm/prelude-base-eval-scores).
It writes results/PRELUDE_EVAL.md (interpretable comparison and quality verdict)
and results/prelude_eval.json (dataset revision, source filter URLs, original row
indices, raw scores and computed changes). This is an independent companion
probe, not a modification of the research graph's established evidence edges.
It compares only one model, task and metric: prelude_anneal2t / coqa_gen / F1.
The probe reads published Parquet files directly at a pinned Hugging Face dataset commit,
recording their SHA256 checksums. Transient source failures are retried up to three times;
the benchmark job installs a Parquet reader, while the graph workflow stays standard-library-only.
Duplicate checkpoints, missing scores, configuration differences, or a truncated
query block comparison rather than producing misleading numbers. API failure is
recorded in separate `*_error.json` and `*_ERROR.md` diagnostics with a nonzero exit code, **not committed over the last successful reports**. Each successful probe may be saved independently even if the other fails. No benchmark
is rerun, and F1 changes alone do not establish significance or cause.

The companion control analysis compares CoQA generative F1, CoQA multiple-choice
accuracy and SQuAD generative F1. It first verifies each task's checkpoint-series
quality independently, then compares changes across **only checkpoint steps
present in all three tasks**. Results and source evidence are saved as
results/PRELUDE_CONTROLS.md and results/prelude_controls.json. Different
benchmark metrics are not combined into a common quality score; these are
descriptive within-task changes, not evidence of causation or statistical significance.

## Local run (optional)

```powershell
python -m unittest discover -s tests -v
python research_graph.py --output results
python qa_probe.py --snapshot results/snapshot.json --output results/QA_EVIDENCE.md
```

## Evidence and limits

Links explicitly mentioning a complete Hugging Face repository URL/ID are labeled `explicit_reference`; matching a sufficiently specific artifact slug produces a `candidate` needing review. Prefix overlaps (e.g. `tokenizer-256k` vs `tokenizer-256k-v2`) are not accepted as matches, nor are name-only mentions that explicitly refer to a different owner (e.g. `allenai/model` instead of `openeurollm/model`). These labels describe *textual evidence*, not scientific validity or proven dependency. Each edge includes its exact matched text and nearby context for inspection. The probe deliberately does not use an LLM to invent missing relationships.

The graph now also resolves literal GitHub issue/PR cross-references (`#214`, `owner/repo#159`, canonical `/issues/` and `/pull/` URLs), with a separate `explicit_task_reference` / `references_task` edge **only when its target is already present in the indexed GitHub inventory**. Cross-repository references use the explicitly named repository; bare issue numbers refer to the source's own repository. References to unindexed tasks are retained as `unresolved_github_task_references` diagnostics rather than fabricated nodes or dangling edges. These links are textual mentions, **not** verified task dependencies, merged code, or reproducible experimental results. The ten-issue holdout reports them separately so it never conflates an internal task link with a verified external research-artifact link.

### Bounded comment and dependency evidence

To test whether the graph can locate concrete change opportunities, it now fetches all public issue comments for the **ten fixed issues** in `impact_cases.json` (up to three GitHub API pages per issue, with a hard failure rather than silent truncation). Each becomes a separate `issue_comment` node with the complete original text, GitHub URL, update timestamp, author and `body_sha256`; `source_comment` edges attach them to the relevant issue. This is a purposeful sample, **not project-wide comment coverage**. If this essential API collection fails, the graph workflow refuses to replace the last complete snapshot.

The source-aware parser adds a distinct `author_declared_dependency` edge only for a literal, indexed GitHub task reference appearing in a labeled **Dependencies** section or an explicit **blocked by / depends on** statement. For example, Taskboard #391 declares a dependency on #432. Separately, a comment with an explicit failure such as **fails due to OOM** may create a `reported_blocker` edge from that comment to its issue (e.g. #433). Both types retain the source URL and matched text; neither asserts that the dependency actually blocks execution, that the failure was reproduced, or that a change speeds anything up. Ordinary task mentions stay `explicit_task_reference` without being upgraded. The ten-task companion report validates original comment hashes and these separately typed edges against freshly fetched sources.

The probe also extracts explicit **DOI and modern arXiv IDs** from GitHub issue bodies and Hugging Face model/dataset cards, and reads publication `pids` in OpenAIRE Graph. Matching records receive a separate `identifier_match` edge. A shared ID reliably identifies a referenced publication but **does not prove that an implementation uses, reproduces, or validates that paper**. For example, five `openeurollm` Hugging Face models reference arXiv `2609.24797` in metadata, and OpenAIRE's *Complex KDA* publication has the same identifier. DOI `10.48550/arxiv.2609.24797` is recognized as the arXiv mirror.

Hugging Face [model-card metadata](https://huggingface.co/docs/hub/model-cards) can also declare `base_model` and `datasets` by complete Hub repository ID. The probe creates `declared_metadata` edges only when the target repository is present in its indexed Hugging Face inventory. It follows **one hop** of references not present in the initial OpenEuroLLM inventory: at most 40 unique model/dataset targets are checked using the **public** Hugging Face API, with four concurrent workers. Only repositories whose identities the API confirms become additional nodes and edges. When the API returns a **different canonical ID** for the declared reference (e.g. after a rename), both are retained and the link is labeled `verified_redirect` / `declared_metadata_redirect`. Missing, inaccessible or failed lookups remain separate records in `external_hf_target_checks`. The original card declarations and their verification state remain in `external_hf_card_references`. The process does not recursively crawl third-party model cards or use a private token. Confirming a target exists does **not** independently verify training lineage.

The prototype also scans a **bounded sample of up to 32 dataset YAML manifests** under the public [`OpenEuroLLM/training-data-collection`](https://github.com/OpenEuroLLM/training-data-collection) `flag/<dataset>/metadata.yaml` tree, with OpenThoughts3 examined first as a documented test case. GitHub's tree and contents APIs are used against a pinned commit, and the run aborts if the tree listing is truncated or metadata retrieval fails. Explicit `https://huggingface.co/datasets/<owner>/<name>` references create `declared_source_file` / `declares_dataset` edges **only when the HF dataset identity is present or verified through its public API** (up to 12 new identities). Adjacent `etc/textify.py` or `etc/textify.slurm` paths create a separate `co_located_source_code` relationship to the manifest, **not** evidence that the scripts ran. The snapshot retains the scanned commit SHA, file blob SHAs, sample limits, unverified URLs and source errors. This is a targeted metadata probe, not an exhaustive search through all files or repositories and not proof of training on any declared dataset.

Concrete **Weights & Biases run URLs** explicitly linked in indexed GitHub issues/PRs are now kept as `experiment_run_ref` nodes with `explicit_run_reference` edges. For example, [Taskboard #381](https://github.com/OpenEuroLLM/Taskboard/issues/381) links an individual training run while discussing a loss anomaly. Only `https://wandb.ai/<entity>/<project>/runs/<run-id>` links qualify; project dashboards and placeholder run IDs do not. These references are labeled `source_link_only`: the graph has **not** retrieved W&B measurements, verified public access, proven run completion, or independently reproduced the loss figures in the issue. That distinction allows future verified run/benchmark artifacts to be added without upgrading source claims prematurely.

Beyond the OpenEuroLLM keyword search, the workflow resolves up to **80 distinct arXiv citations** from both GitHub tasks and Hugging Face cards using OpenAIRE's documented `ids.arxiv` OR filter (batches of at most 40 IDs). The report now measures which cited IDs actually resolve, which are absent from the API response, and how many artifacts of each source type have resolvable citations. Skipped IDs and failed API batches are recorded explicitly. Older non-numeric arXiv identifier formats are not yet supported. This is bounded citation discovery, not a global research index.

The report separates **open vs closed** GitHub issues and PRs, and measures duplicate IDs, duplicate edges, missing link endpoints, missing update timestamps, and citation-lookup completeness. It also counts publications referenced from both GitHub and Hugging Face; such a two-source bridge does not establish a direct dependency between the engineering task and model. Declared Hugging Face lineage is reported separately from cross-platform references and ambiguous name-only candidates, including the one-hop target-verification outcomes. API failures remain visible; no missing response is silently interpreted as zero hits.

OpenAIRE results are a keyword-search sample plus the bounded citation lookup, not an exhaustive count of OpenEuroLLM research products. The report preserves source errors rather than silently treating missing responses as zero matches. GitHub retrieval has a `max_pages=10` safeguard per repository, so very large projects may need pagination adjustments.

### Next validation step

To run the companion probe locally (optional): python benchmark_probe.py --output results.
GitHub Actions executes this command automatically without the user's PC.

Run an independent LLM over the fixed evidence packets using a supported inference provider, then score answers against sourced citations and unsupported-claim avoidance. The GitHub Actions evidence check does **not** make an LLM call and therefore makes no claim of autonomous AI answer accuracy. Manually annotate name-only candidates and measure recall before considering a common graph service or MCP interface. A reference to an artifact does not establish a causal dependency on it.

## Rotating issue discovery and human feedback (separate pilot)

The [rotating discovery workflow](.github/workflows/opportunity-discovery.yml) independently samples **50 currently open Taskboard issues**, excluding the original ten purposefully selected impact-study cases. Selection is by reproducible SHA256 ID order with a weekly ISO-week seed, without using the issue descriptions for selection. This is an exploratory sample, not a statistically representative estimate, a project-wide ranking, or an exhaustive search.

The detector re-reads every selected issue and the original supporting comments. It rejects source drift and incomplete comment pagination before writing [results/discovery.json](results/discovery.json) and [results/DISCOVERY.md](results/DISCOVERY.md). Rules currently surface **literal memory/OOM reports, performance phrases, and explicit Dependencies-section references**. A phrase match is **not** independent validation of a speedup, blocker, or researcher availability. Evidence includes exact original excerpts, source links and SHA256 checksums. Suggested contacts are public issue assignees or clearly labeled author fallbacks, **never notified automatically**.

The report is generated weekly on Monday or via manual GitHub Actions dispatch, separate from the existing ten-issue impact workflow. PR checks run unit tests without querying live APIs or committing results. On a failed live audit, previous successful reports remain unchanged.

Human decisions can optionally be saved using the append-only [opportunity_feedback.py](opportunity_feedback.py) log. The log uses a stable issue-and-signal key, so feedback survives weekly sampling rotations; it records `reviewed`, `proposal_prepared`, `published`, `response_received`, `resolved`, or `dismissed` with validated transitions. It **does not send, verify, or infer real GitHub comments**. Published, response, and resolved events require a human-provided GitHub issue or PR link. These are self-reported review statuses, not live platform assertions. To mark an observed card reviewed, for example (PowerShell):

```powershell
python opportunity_feedback.py --issue-id "github:OpenEuroLLM/Taskboard#123:reported_memory_issue" --status reviewed --actor tire0011 --note "Checked original source"
git add results/opportunity_feedback.jsonl
git commit -m "review: record human feedback"
```

Only record real human actions; never mark a comment published unless it was actually posted and has an original link. Review and commit such events manually. If an issue disappears from the rotating sample, this **does not** mean it is fixed or closed.


## European cross-project overlap pilot

The [cross-project audit](.github/workflows/cross-project-audit.yml) now compares a **small, manually selected, read-only sample of nine public GitHub repositories** across **OpenEuroLLM, LAION-AI, hplt-project and utter-project (EuroLLM)**. The [source registry](cross_project_sources.json) contains six explicit repo-to-repo hypotheses and separately labeled links to existing collaborations reported by OpenEuroLLM.

The job independently loads and re-loads every repository README, checks source stability and SHA256 hashes, and records linked original README excerpts for matching **literal technical terms** and any direct GitHub repo hyperlinks. Results: [results/CROSS_PROJECT.md](results/CROSS_PROJECT.md) and [results/cross_project.json](results/cross_project.json). It runs weekly on Tuesday, on manual dispatch and once on merge; pull requests run offline tests only.

**Strict evidence distinctions:** an official blog describing collaboration is a curated external source, not checked automatically by this GitHub-only audit. A literal shared term is a *topic overlap*, not identical implementation. An explicit GitHub URL in a README proves a mention, **not cooperation or reuse**. None of these are sufficient to claim duplicate code, redundant effort or measured savings; such claims require manual review of current tasks, code, provenance, licenses, existing dependencies and use cases. No automated outreach, labels or GitHub comments. This bounded pilot is not exhaustive, does not yet search cross-project issues, and does not change the existing ten-issue or 50-issue discovery workflows.


## HPLT–OpenEuroLLM code and issue handoff (bounded audit)

The [HPLT code/issue workflow](.github/workflows/hplt-overlap-audit.yml) extends the preceding README-only EU overlap pilot with a **narrow, original-source comparison** of the Common Crawl download components and HPLT Stage-2 version lineage. The [case registry](hplt_overlap_cases.json) deliberately scopes two code pairs and five issue pairs; selection is manual, **not a project-wide duplicate detector**.

The audit pins each repository tree to a commit SHA before comparing Git blob hashes. It distinguishes:
- **Byte-identical nontrivial files** (same blob SHA, at least 64 bytes): verified reuse of file *content*, not evidence of shared authorship or unnecessary duplication.
- **Byte-identical trivial files** (such as zero-length module markers): excluded from meaningful reuse counts.
- **Same relative file path, different blob SHA**: a candidate for reviewing version divergence, without claiming the changes are compatible.

For issues, the audit reads the original bodies and current open/closed status twice, checks literal preselected phrases and hashes each body. The five human-review links cover **Common Crawl transfers, robots.txt handling, OpenLID, GlotLID and XML-to-Markdown**. A closed HPLT issue and an open OpenEuroLLM issue suggest potential prior knowledge, **not proof of a solution or of duplicate work**. Comments, historical discussions, code semantics, licenses, acceptance tests and actual reuse are outside the automated evidence level.

The job runs weekly on Wednesday, manually and after merging source changes. It produces [results/HPLT_OVERLAP.md](results/HPLT_OVERLAP.md) and [results/hplt_overlap.json](results/hplt_overlap.json) only after a complete successful audit; a source error prevents replacing last-known-good reports. Unit tests run on pull requests without external API access. No automated outreach or changes to external repositories.


## Tracing robots.txt reuse across HPLT and OpenEuroLLM

The [robots.txt reuse source audit](robots_reuse_audit.py) extends the HPLT overlap study with a **12-source, pinned-code and issue-text trace**. It follows the handoff that the OpenEuroLLM issue already proposes: reusing Jaume's earlier HPLT robots.txt indexing and annotation work. The [curated registry](robots_reuse_cases.json) distinguishes sitewide historical robots.txt evaluation from the separate HTTP `X-Robots-Tag`, HTML robots meta tag and TDM mechanisms in `warc2text`.

The audit cryptographically verifies each downloaded file against its original Git blob SHA from a pinned commit and re-reads every selected issue. It verifies **the presence of cited implementation steps**, not the correctness of robots.txt matching, AI-training permission policy, runtime throughput or legal compliance.

The corresponding [source report](results/ROBOTS_REUSE.md) and [machine-readable trace](results/robots_reuse.json) are generated alongside the existing HPLT audit. The report includes a checklist of acceptance tests for user-agent selection, path matching, historical captures, URL normalization, line-aligned `allowed.zst` masks, and the behavior when an expected mask is missing. Missing `allowed.zst` is not inherently a bug: HPLT intentionally omits this step for some crawl types; however, when the mask is required, silently proceeding without it must be assessed.

This analysis is **read-only** and does not claim a new implementation, verified duplicate work, or a fix. No automatic posting to other projects.


## Collaboration Matcher — the collaboration goal, not a graph speed race

The current research question is **whether separate EU research teams can reuse earlier work and find useful collaborators**, not whether precomputed graph traversal is faster than an equivalent snapshot text scan.



**Pilot precision gate:** after the first live run, general shared words (e.g. `two`, `optional`, `stage`) produced unhelpful suggestions involving dependency-update PRs. The matcher now requires a specific shared technical component (such as `robots.txt` or `OpenLID`) or multiple technical terms and caps score contributions to four signals. This curated technical vocabulary was refined from observed live results: **it is not independent test evidence or a model of all possible research collaboration**, particularly policy/governance topics. The next evaluation must use unseen questions and independent human labels.

The [collaboration matcher](collaboration_matcher.py) is a **rule-based, auditable baseline** (not an LLM): a bounded registry of [eight public GitHub repositories](collaboration_sources.json) is scanned for all visible issues and pull requests. Recently created *open* tasks are matched to earlier related work in **other GitHub organizations**. Matching issue numbers are **not** hand-picked. Original titles, body hashes, matched phrases, source links, states, assignees and a separate full-text baseline are kept for each suggestion. Only shortlisted sources are re-fetched and checked for source changes before writing the report.

- [Collaboration matches (human-review queue)](results/COLLABORATION_MATCHES.md)
- [Structured matches and baseline](results/collaboration_matches.json)

The [public coordination check](collaboration_coordination.py) now re-reads each shortlisted issue/PR and its public issue comments to distinguish **exact cross-task references**, **shared authors/assignees/commenters**, **broader repository references**, and **no directly observed public link**. Findings are saved to [results/COLLABORATION_COORDINATION.md](results/COLLABORATION_COORDINATION.md) and [results/collaboration_coordination.json](results/collaboration_coordination.json), within the existing weekly cross-project workflow. **Shared participants do not prove successful collaboration; absent public evidence does not prove novelty.** Human review of technical relevance and any private discussions is still needed. No messages are sent.

The matcher runs inside the existing cross-project audit workflow on a weekly/manual schedule and on code changes. It does **not** post comments, send messages, infer that closed PRs were merged, or claim a historic issue is solved. This initial candidate finder is limited to GitHub. Hugging Face and OpenAIRE remain important for a later *cross-platform* evaluation, but must not be represented as covered by this test.

**The measurement that matters next:** ask a reviewer who did not prepare the candidates to label both matcher suggestions *and* same-input full-text search results as actionable reuse, already-coordinated related work or irrelevant. Record precision and useful unique discoveries; compare against the baseline before investing in a graph service, MCP endpoint or LLM ranking. Current benchmark ties are real and do **not** justify a permanent service by themselves.

### Exploratory concept-phrase bridge (separate experiment)

The technical vocabulary gate misses some cross-project work-product relationships. The optional [concept-phrase probe](concept_bridge_probe.py) explores **rare, adjacent two-word phrases anchored in an active issue title**, including simple singular/plural normalization. It rechecks the selected original source bodies, carries a same-input lexical baseline, and leaves existing technical matches untouched. Run it manually with `python concept_bridge_probe.py`; it has no scheduled workflow and does not contact anyone.

The [first non-blinded case review](results/CONCEPT_BRIDGE_FIRST_REVIEW.md) documents an OpenEuroLLM model-card reporting task and an earlier, unanswered proposal in LAION's benchmark issue tracker. This hypothesis **was identified manually before the phrase probe was implemented**. Recovering it is a replay check, not an independent discovery or measured accuracy gain. The first two-repository probe also surfaced generic or misleading pairs; an independent reviewer and a frozen future holdout are needed before any wider rollout.

### Requirement-level collaboration triage (manual experiment)

The next question is whether tasks are **potentially duplicative**, have a
**specific complementary handoff**, or could benefit from an **independent
third-party artifact**. Shared terms and benchmark names are not enough.
The [expanded source registry](collaboration_expanded_sources.json) adds
OpenEuroLLM's eval work, HPLT-WP4 and AllenAI's `olmo-eval`, without changing
the production source registry or scheduled matcher.

The [second case review](results/COLLABORATION_REVIEW_NEXT_CASES.md) examines
long-context training vs. already-implemented state-tracking evaluations, and
different Arena-Hard scoring/contamination tasks. The optional
[evidence review CLI](collaboration_review.py) first re-fetches the full
original issue/PR bodies, can inspect public coordination, and checks an
independent reviewer or local LLM's **exact source quotations** and proposed
technical handoff. See the [review protocol](COLLABORATION_REVIEW_PROTOCOL.md)
for local commands and JSON schema. Model judgments of maturity and practical
compatibility are *not* certified by exact-quote validation. No automatic
contact, no novelty claim and no measured ranking improvement.

### European platform and requirement comparison (separate source layer)

The optional [European ecosystem source registry](ecosystem_sources.json)
records **AI-on-Demand (AIoD), EOSC EU Node, AI4EOSC and EOSC-ARENA**, using
official platform documentation, including known relations among them. AIoD's
metadata catalogue provides a documented [REST API](https://aiondemand.github.io/AIOD-rest-api/)
and [Python SDK](https://aiondemand.github.io/aiondemand/). The separate,
bounded [AIoD source pilot](AIOD_SOURCE_ADAPTER.md) can now **request public
REST v2 catalogue metadata** and compare it lexically with the stored GitHub
snapshot; the live **AIoD v2 public listing endpoint was verified** on
2026-11-11 in three bounded samples. See
[pilot findings](results/aiod/PILOT_FINDINGS.md) for coverage, duplicate
metadata and false-positive limitations. No EOSC adapter is implemented. AIoD also has its own
[semantic search project](https://github.com/aiondemand/aiod-enhanced-interaction),
which must be considered a retrieval baseline rather than rebuilt by default.
The second [targeted search pilot](results/aiod/TARGETED_REVIEW.md) verifies
five live, open OpenEuroLLM requirements against AIoD search. It retrieves
42 issue-specific results from 15 bounded search calls, but identifies **zero
verified technical handoffs or newly collaborating teams**; single-word
matches dominate. The [search script](aiod_targeted_search.py) and its
results are separate from the production matcher and scheduled workflows.
EOSC-ARENA publicly plans agent-to-agent interoperability; this is a proposed
work package, *not* proof that a usable integration has shipped.

Run `python ecosystem_requirements.py` to regenerate **six requirement-specific
JSON and Markdown reports** and a combined
[comparison matrix](results/requirements/OVERVIEW.md). Requirement domains are:
resource/people discovery, duplicate work/reuse, human–agent coordination,
interoperability, joint model work and evidence/provenance. The report links
three earlier GitHub candidate case reviews to relevant domains without
silently promoting them to confirmed collaborations. Machine-readable
[comparison JSON](results/requirements/comparison.json) preserves official URLs,
documented/planned/adjacent evidence and explicit existing relationships.

The static evidence snapshot was reviewed on 2026-11-11. The pilot limits
pagination, uses v2 resource IDs and records metadata SHA256; a live bounded
API response and nested project descriptions were confirmed. Authentication,
full catalogue coverage, licensing and change detection remain unverified.
**Platform coverage is not a score; missing evidence is not
evidence of a missing feature.**

