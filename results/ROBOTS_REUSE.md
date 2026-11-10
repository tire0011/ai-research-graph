# HPLT robots.txt → OpenEuroLLM: verified reuse trace

**Source-linked reuse assessment, not a confirmed code fix or compliance audit.**
Checked 12 source excerpts across 3 pinned code repositories.

## What is already coordinated

The OpenEuroLLM issue explicitly proposes adapting Jaume's earlier step; this is a handoff opportunity, not an independent duplicate implementation.

## Reusable stages

- HPLT Stage 1 extracts robots.txt WARC responses
- monotextor-slurm builds an FST index of disallowed site URLs
- the annotation stage can create a per-document allowed.zst mask
- HPLT Stage 3 consumes the mask only when the file is present

## Important distinction

OpenEuroLLM warc2text already processes record-local X-Robots-Tag and HTML robots directives; this does not replace sitewide captured robots.txt processing.

## Evidence by source

### OpenEuroLLM request — requested-adaptation

- [Original pinned source](https://github.com/OpenEuroLLM/web-data-processing/issues/7) — github_issue
- Matched source phrase: adopt and adapt the intermediate step by jaume
- Exact excerpt: Requirements from Mattermost: "before running the new S2, we will need to adopt and adapt the intermediate step by jaume, interpreting the totality of robots.txt captures (now probably more conse
- SHA256: c3dc6cd8ff795cf5d7f7c658bb416174de9183beeca2ffbde2c295a2d34467a7
- Interpretation for human review: The existing pipeline is explicitly named as work to adapt; this is not newly discovered unrelated duplication.
- Runtime claim validated: no

### Adjacent OpenEuroLLM task — existing-opt-out-task

- [Original pinned source](https://github.com/OpenEuroLLM/web-data-processing/issues/3) — github_issue
- Matched source phrase: opt-out handling
- Exact excerpt: Update warc2text to support opt-out handling. Quick look at the Apertus approach.
- SHA256: 1a4769a95e100eda9f656ca822cf45096f681cd1e88f11a36f0b509cca5ef344
- Interpretation for human review: Separate opt-out policy issue requiring decisions about applicability and retroactive filtering.
- Runtime claim validated: no

### Capture — hplt-capture

- [Original pinned source](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/README.md) — pinned_git_file
- Matched source phrase: robotstxt.warc.gz
- Exact excerpt: original WARC file corresponding to HTTP responses containing PDF files - robotstxt.warc.gz: the subset of records from the original WARC file with URIs ending by rob
- SHA256: 67f2d993cc43fb88b5986642691cc6bb34bd3d652e09ac32052917924229d013
- Interpretation for human review: HPLT Stage 1 stores robots.txt captures separately for later processing.
- Runtime claim validated: no

### Sitewide URL index — hplt-index

- [Original pinned source](https://github.com/hplt-project/monotextor-slurm/blob/57c92953b0b62fb99d3068ba1a6a67e3a1423919/09.robotstxt) — pinned_git_file
- Matched source phrase: disallowed-urls.fst
- Exact excerpt: sif \ fst set --force --sorted $OUTPUT_DIR/disallowed-urls $OUTPUT_DIR/disallowed-urls.fst.tmp zstdmt -qf --rm $OUTPUT_DIR/disallowed-urls mv $OUTPUT_DIR/disallowed
- SHA256: 106e5a955a016fd37e72338e59068d96f35f77c9f297bfaf9e4cb6c8f730a2bc
- Interpretation for human review: Existing HPLT batch produces an indexed set of disallowed URLs from captured robots.txt.
- Runtime claim validated: no

### Crawler policy selection — hplt-agent-scope

- [Original pinned source](https://github.com/hplt-project/monotextor-slurm/blob/57c92953b0b62fb99d3068ba1a6a67e3a1423919/scripts/robots2tsv.py) — pinned_git_file
- Matched source phrase: agents = ('ia_archiver', 'ccbot', '*')
- Exact excerpt: ile("^\s*$") agent_re = re.compile("^User-agent: ?([^#]+?)(#.*)?$", re.I) agents = ('ia_archiver', 'ccbot', '*') tbl = [chr(i) for i in range(sys.maxunicode) if not cat(chr(i)).startswit
- SHA256: 153a41867ae7f3541106b3c1f1df59a0f6b500d12fae1396c1d8f732fabcf133
- Interpretation for human review: The existing parser is scoped to these user agents and requires review against OpenEuroLLM use cases.
- Runtime claim validated: no

### Matching — hplt-rule-matcher

- [Original pinned source](https://github.com/hplt-project/monotextor-slurm/blob/57c92953b0b62fb99d3068ba1a6a67e3a1423919/utils/src/bin/robots-filter.rs) — pinned_git_file
- Matched source phrase: StringPatriciaSet
- Exact excerpt: ProgressFinish, ProgressStyle}; use log::{debug, warn}; use patricia_tree::StringPatriciaSet; use rayon::prelude::*; use regex::Regex; use regex_automata::dense; #[de
- SHA256: ca1f7938a89e796a6c1480d5d594e9da2ec183dc0499871b70bb6544a08eadd2
- Interpretation for human review: HPLT already has a compiled Rust matcher for robots allow/disallow patterns against an URL index.
- Runtime claim validated: no

### Annotation — hplt-annotation

- [Original pinned source](https://github.com/hplt-project/monotextor-slurm/blob/57c92953b0b62fb99d3068ba1a6a67e3a1423919/09.2.robots-annotate) — pinned_git_file
- Matched source phrase: robotstxt-annotate
- Exact excerpt: arity exec --bind $binddirs --pwd $(pwd -P) monotextor.sif \ parallel -j64 robotstxt-annotate $flashrobots/disallowed-urls.fst \ {}/metadata.zst {}/allowed.zst :::
- SHA256: f7a0fe5d830152613b150cd00eada4c207116cf656d9e307c7ec08ff59c94c52
- Interpretation for human review: Prior HPLT script invokes the tool generating line-aligned allowance annotations.
- Runtime claim validated: no

### Stage 3 consumption — hplt-stage3-filter

- [Original pinned source](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage3/stage3local_v2.sh) — pinned_git_file
- Matched source phrase: rclone lsf "${INPUT_DIR}/allowed.zst"
- Exact excerpt: e the empty string that will collapse when given as an additional argument rclone lsf "${INPUT_DIR}/allowed.zst" &>/dev/null && ALLOWED_PIPE="$TMP_DIR/pipe_allowed" // ALLOWED_PIPE="" st
- SHA256: 80b6f17f1d52d1c4e709ea11bd2f3a3f0d2260214070c333e18f160612c0cf98
- Interpretation for human review: Stage 3 optionally reads allowed.zst; if absent it does not apply this sitewide filter.
- Runtime claim validated: no

### Documented Stage 3 contract — hplt-stage3-docs

- [Original pinned source](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage3/README.md) — pinned_git_file
- Matched source phrase: If present, this file will be used
- Exact excerpt: a binary mask describning compatability of each document with robots.txt. If present, this file will be used when running stage3 to remove incompatible documents. </details> ## Prep
- SHA256: 3f7940face813f1601c5de15b99b8bb2283cca6773ad5a6d86950b379991c3ef
- Interpretation for human review: HPLT documents that allowance filtering depends on presence of allowed.zst.
- Runtime claim validated: no

### Record-local opt-outs — oe-page-level

- [Original pinned source](https://github.com/OpenEuroLLM/warc2text/blob/e3ea96f28f79c1020264611de9f3f071d9b0f88a/src/robotsreservation.cc) — pinned_git_file
- Matched source phrase: x-robots-tag
- Exact excerpt: Header(const Record& record) const { if (!record.HTTPheaderExists("x-robots-tag")) return true; std::string directives = util::toLower
- SHA256: c72e432657e6dd3770abd0327c0deaf6e5f712894c5a24aaff22b472617aaea0
- Interpretation for human review: Existing OpenEuroLLM code checks X-Robots-Tag and HTML robots directives, not the cross-page historical sitewide robots index.
- Runtime claim validated: no

### WARC capture extraction — oe-robot-captures

- [Original pinned source](https://github.com/OpenEuroLLM/warc2text/blob/e3ea96f28f79c1020264611de9f3f071d9b0f88a/src/warcpreprocessor.cc) — pinned_git_file
- Matched source phrase: robots_warc_writer.writeRecord(content)
- Exact excerpt: if (!options.robots_process && ::isRobotsTxt(record)) { robots_warc_writer.writeRecord(content); // no-op if robots_warc_writer is not opened. continue;
- SHA256: 9f0583e60a34cf1d15a4cf56077e33612fb125582fd3b7512f2aca05ff487836
- Interpretation for human review: OpenEuroLLM extracts robots.txt response records for a separate downstream processing step.
- Runtime claim validated: no

### Policy explanation — oe-opt-out-doc

- [Original pinned source](https://github.com/OpenEuroLLM/warc2text/blob/e3ea96f28f79c1020264611de9f3f071d9b0f88a/OPTOUT.md) — pinned_git_file
- Matched source phrase: X-Robots-Tag
- Exact excerpt: atching tag has a value other than `0`. ## Robots reservation Both the `X-Robots-Tag` HTTP header and the `<meta name="robots" ...>` meta tag hold a comma-sepa
- SHA256: 51826c1b487ad5847d6b4553cd70c91616f2e0650b1827c031b46d9121cbe28f
- Interpretation for human review: The current page-local filtering rules are documented separately from sitewide robots.txt evaluation.
- Runtime claim validated: no

## Highest-priority validation gap

For datasets requiring post-crawl sitewide robots.txt checks, absent allowed.zst currently means the HPLT Stage 3 script omits that filter. Verify intended behavior and test fail-closed policy where required.

## Tests before an external PR

1. Confirm the intended crawler user-agent policy and robots.txt group precedence, wildcard handling and allow/disallow specificity with tests.
2. Decide the temporal policy for robots.txt captures and missing/ambiguous captures; avoid assuming one historical capture applies retroactively.
3. For IA or other crawls requiring post-hoc robots filtering, explicitly require allowed.zst or fail the job rather than silently continuing.
4. Check URL normalization (scheme, www, ports, percent encoding) and sample allow/disallow precedence before reusing a URL index.
5. Verify line count, line order, and key consistency among metadata.zst, allowed.zst and downstream Stage 3 outputs.
6. Keep HTTP/meta/TDM reservations separate from sitewide robots.txt decisions; document combined exclusion policy.
7. Confirm existing stakeholders have already scheduled this adaptation before posting any duplicate implementation request.

## Boundaries

Static source evidence only. Pinned Git content SHA and original issue text verified. No robots policy correctness, historical capture coverage, runtime tests, licensing or legal assessment. No messages posted.
Duplicate work: not_established.
