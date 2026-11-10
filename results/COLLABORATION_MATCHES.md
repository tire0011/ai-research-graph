# Collaboration Matcher — cross-organization pilot

**Review only. Rule-based matcher, not an LLM and not proof of duplicate effort.**
Audited **665** public issues/PRs in **8** repositories, considering **202** recently opened active items. Found **25** candidate handoffs. Re-checked **30** underlying issue/PR sources.

**Same-input full-text baseline:** 3/25 suggestions are also the lexical baseline's top-1 target for that source. **This does not establish improved precision or recall.**

## Review queue (no messages sent)

### 1. [extract additional WARC metadata](https://github.com/OpenEuroLLM/warc2text/issues/1) ↔ [pick up crawl identifier in repackaging](https://github.com/hplt-project/monotextor-slurm/issues/9)

- Source: OpenEuroLLM/warc2text / issue / open / SHA256 d0efd4d10dc3ec879537c86212cdd10e121a3d0e1d2280118ea7cb2cc68c5436
- Possible related work: hplt-project/monotextor-slurm / issue / closed / SHA256 fd551bc90d760be0ae4250bb2a565bf33b0c8da27590f3234724cab5df392561
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 32.567; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): @ZJaume
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **warc**: source title «extract additional WARC metadata»; target body «2 does not include the crawl identifier. the specific WARC file name is there, but that may not be unique across»
  - **metadata**: source title «extract additional WARC metadata»; target body «metadata after S1 and S2 does not include the crawl identifier.»
  - **crawl**: source body «new invention, so presumably will hardly be present in crawls before 2024. but for newer data, it would be interest»; target title «pick up crawl identifier in repackaging»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 2. [download recent CC crawls to LUMIO](https://github.com/OpenEuroLLM/web-data-processing/issues/2) ↔ [downloading 2025 CC crawls to LUMI-O](https://github.com/hplt-project/HPLT-textpipes/issues/9)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 ecb0d2f70fdee40a8970c59dabbf96f8f6a351fd0dce31163ce64d4bc23363cd
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 46049d90e424be16cbe569d8df9c24e18cc2bb4a51d4eb06f9d892b474249f9f
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 31.89; baseline top-1 agrees: yes (baseline target ID: github:hplt-project/HPLT-textpipes#9).
- Suggested assignees (not contacted): @nvanva, @oepen
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **lumio**: source title «download recent CC crawls to LUMIO»; target title «downloading 2025 CC crawls to LUMI-O»
  - **crawl**: source title «download recent CC crawls to LUMIO»; target title «downloading 2025 CC crawls to LUMI-O»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 3. [extract additional WARC metadata](https://github.com/OpenEuroLLM/warc2text/issues/1) ↔ [(storage) management around 3.1 release](https://github.com/hplt-project/HPLT-textpipes/issues/18)

- Source: OpenEuroLLM/warc2text / issue / open / SHA256 d0efd4d10dc3ec879537c86212cdd10e121a3d0e1d2280118ea7cb2cc68c5436
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 aab15a7df6112e6a2be4fd4de1abba903d75bbfc6ccda59c1e84dc47d3908b80
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 27.219; baseline top-1 agrees: yes (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): @nvanva, @oepen
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **warc**: source title «extract additional WARC metadata»; target body «ctories for different stages (S1 + S2 combined), e.g. `warc`, `html`, `pool`, `clean`, `noise` + `robots.txt` pl»
  - **metadata**: source title «extract additional WARC metadata»; target body «Ls, if these were to occur~~ + output format: all `metadata.zst` in one file; XML, MD, and TEXT each in separate f»
  - **crawl**: source body «new invention, so presumably will hardly be present in crawls before 2024. but for newer data, it would be interest»; target body «to decide whether to preserve or not) + eight 2025 CC crawls on LUMI-O: 800 tib, each a separate bucket + S1 comple»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 4. [download recent CC crawls to LUMIO](https://github.com/OpenEuroLLM/web-data-processing/issues/2) ↔ [Stage 1 preprocessing for LUMI with streaming from/to LUMI-O](https://github.com/hplt-project/HPLT-textpipes/pull/15)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 ecb0d2f70fdee40a8970c59dabbf96f8f6a351fd0dce31163ce64d4bc23363cd
- Possible related work: hplt-project/HPLT-textpipes / pull_request / closed / SHA256 5ccba177b5f7bb930e7b93c280890adba195794793259cf813d20725e5ac817a
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 26.542; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#9).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **lumio**: source title «download recent CC crawls to LUMIO»; target title «Stage 1 preprocessing for LUMI with streaming from/to LUMI-O»
  - **crawl**: source title «download recent CC crawls to LUMIO»; target body «kept, including: * shuffling of WARCs within a single crawl before dividing them to batches, and shuffling batches»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 5. [S2-S4 updates](https://github.com/OpenEuroLLM/web-data-processing/issues/6) ↔ [XML to markdown conversion](https://github.com/hplt-project/HPLT-textpipes/pull/10)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 da1ef26f63fa097d38f34a984399f68abb1ce63e59f0c6a34720e3cba39e83ec
- Possible related work: hplt-project/HPLT-textpipes / pull_request / closed / SHA256 16701edb91eb2ee2a6c20abf8f63821252ac27b73f0c105173b8ecf8a603fee4
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 25.704; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **xml**: source body «ra release, current openlid (v3) and glotlid versions, xml and md into one file, standard zstd output, id ingesti»; target title «XML to markdown conversion»
  - **markdown**: source body «se, current openlid (v3) and glotlid versions, xml and md into one file, standard zstd output, id ingestion , an»; target title «XML to markdown conversion»
  - **trafilatura**: source body «The requirements from Mattermost: "the latest trafilatura release, current openlid (v3) and glotlid versions, xm»; target body «res: - jsonlines stdin->stdout processing - converts trafilatura's output XML to markdown, adding `md` field to *some*»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 6. [S2-S4 updates](https://github.com/OpenEuroLLM/web-data-processing/issues/6) ↔ [Change trafilatura TEI/XML to text behaviour](https://github.com/hplt-project/warc2text-runner/issues/2)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 da1ef26f63fa097d38f34a984399f68abb1ce63e59f0c6a34720e3cba39e83ec
- Possible related work: hplt-project/warc2text-runner / issue / closed / SHA256 0e3c996962897b825bf2fe4d2cdc76727eb73b8f377c92996b348b0784c2a7fd
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 22.277; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **trafilatura**: source body «The requirements from Mattermost: "the latest trafilatura release, current openlid (v3) and glotlid versions, xm»; target title «Change trafilatura TEI/XML to text behaviour»
  - **xml**: source body «ra release, current openlid (v3) and glotlid versions, xml and md into one file, standard zstd output, id ingesti»; target title «Change trafilatura TEI/XML to text behaviour»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 7. [robots.txt](https://github.com/OpenEuroLLM/web-data-processing/issues/7) ↔ [coordinate between uio and prompsit about robots.txt filtering](https://github.com/hplt-project/HPLT-textpipes/issues/17)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 c3dc6cd8ff795cf5d7f7c658bb416174de9183beeca2ffbde2c295a2d34467a7
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 c536125202804a56c61942837bb338fcc6d5cb13beab404621d93179a9a5677d
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 17.777; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): @ZJaume, @oepen
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **robotstxt**: source title «robots.txt»; target title «coordinate between uio and prompsit about robots.txt filtering»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 8. [robots.txt](https://github.com/OpenEuroLLM/web-data-processing/issues/7) ↔ [filtering by robots.txt for IA](https://github.com/hplt-project/HPLT-textpipes/issues/28)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 c3dc6cd8ff795cf5d7f7c658bb416174de9183beeca2ffbde2c295a2d34467a7
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 17.777; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **robotstxt**: source title «robots.txt»; target title «filtering by robots.txt for IA»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 9. [Long-Context Data Generation](https://github.com/OpenEuroLLM/Taskboard/issues/339) ↔ [pick up crawl identifier in repackaging](https://github.com/hplt-project/monotextor-slurm/issues/9)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 99bac3aa3e6944c44ac3f173ffde93b7e71046438847cc1324e3e6b8a51e21ba
- Possible related work: hplt-project/monotextor-slurm / issue / closed / SHA256 fd551bc90d760be0ae4250bb2a565bf33b0c8da27590f3234724cab5df392561
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 15.147; baseline top-1 agrees: no (baseline target ID: github:hplt-project/warc2text-runner#17).
- Suggested assignees (not contacted): @ZJaume
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **crawl**: source body «**HPLT v2 · CulturaX · FineWeb-2**: document-level web crawl with strong per-language coverage incl. `uk`, `el`. So»; target title «pick up crawl identifier in repackaging»
  - **metadata**: source body «[ ] Output in the agreed training format with retained metadata (language, task type, source doc, needle depth where a»; target body «metadata after S1 and S2 does not include the crawl identifier.»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 10. [Tokenizer evaluation](https://github.com/OpenEuroLLM/Taskboard/issues/146) ↔ [use open_clip.get_tokenizer to support all tokenizers](https://github.com/LAION-AI/CLIP_benchmark/pull/19)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 f60963ca7f0673544d33bf3d599f942befa5365705eb63a2a7e94c18924a18d9
- Possible related work: LAION-AI/CLIP_benchmark / pull_request / closed / SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 12.914; baseline top-1 agrees: no (baseline target ID: github:LAION-AI/CLIP_benchmark#113).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **tokenizer**: source title «Tokenizer evaluation»; target title «use open_clip.get_tokenizer to support all tokenizers»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 11. [Tokenize NemotronCC dataset with GPT OSS tokenizer](https://github.com/OpenEuroLLM/Taskboard/issues/188) ↔ [use open_clip.get_tokenizer to support all tokenizers](https://github.com/LAION-AI/CLIP_benchmark/pull/19)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 4452388e694a4f46c25509c0de735248daae0670c7ab0d58eaa0a0eeb01a40cd
- Possible related work: LAION-AI/CLIP_benchmark / pull_request / closed / SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 12.914; baseline top-1 agrees: no (baseline target ID: github:LAION-AI/CLIP_benchmark#133).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **tokenizer**: source title «Tokenize NemotronCC dataset with GPT OSS tokenizer»; target title «use open_clip.get_tokenizer to support all tokenizers»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 12. [Custom tokenizer for final flagship model training](https://github.com/OpenEuroLLM/Taskboard/issues/377) ↔ [use open_clip.get_tokenizer to support all tokenizers](https://github.com/LAION-AI/CLIP_benchmark/pull/19)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 8ab196d2603c0a39a6a27890a83f894bcc8db8224f0955b51a6e6a3a5ff70584
- Possible related work: LAION-AI/CLIP_benchmark / pull_request / closed / SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 12.914; baseline top-1 agrees: no (baseline target ID: github:LAION-AI/CLIP_benchmark#113).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **tokenizer**: source title «Custom tokenizer for final flagship model training»; target title «use open_clip.get_tokenizer to support all tokenizers»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 13. [Tokenize NemotronCC dataset with GPT OSS tokenizer](https://github.com/OpenEuroLLM/Taskboard/issues/188) ↔ [Add audio modality support for CLAP evaluation](https://github.com/LAION-AI/CLIP_benchmark/pull/148)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 4452388e694a4f46c25509c0de735248daae0670c7ab0d58eaa0a0eeb01a40cd
- Possible related work: LAION-AI/CLIP_benchmark / pull_request / open / SHA256 df48eb6c4d53295923feb9d152e9e1974d46e8c6fd0ad0331df56de1b36ff473
- Category: possible_parallel_work — **not a verified solution or collaboration**.
- Ranking score: 12.885; baseline top-1 agrees: no (baseline target ID: github:LAION-AI/CLIP_benchmark#133).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **tokenizer**: source title «Tokenize NemotronCC dataset with GPT OSS tokenizer»; target body «ependencies - `open_clip` (for model architecture and tokenizer) - `librosa` (audio decoding) - `torchaudio` (mel spec»
  - **markdown**: source body «m/OpenEuroLLM/training-data-catalogue/blob/main/README.md). - Which tokenizer? [`spyysalo/harmony-latin-plus`](h»; target body «ty functions for audio data handling | | `AUDIO_README.md` | Documentation for audio benchmarks with usage examp»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 14. [Add audio modality support for CLAP evaluation](https://github.com/LAION-AI/CLIP_benchmark/pull/148) ↔ [Polish checkpoint conversion scripts and add unittests](https://github.com/OpenEuroLLM/Taskboard/issues/29)

- Source: LAION-AI/CLIP_benchmark / pull_request / open / SHA256 df48eb6c4d53295923feb9d152e9e1974d46e8c6fd0ad0331df56de1b36ff473
- Possible related work: OpenEuroLLM/Taskboard / issue / closed / SHA256 ac451ecf109bf2e18c8bdc9fd96a703ff492d069d3ae286c9356813bf53fa7e0
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 11.041; baseline top-1 agrees: no (baseline target ID: github:OpenEuroLLM/Taskboard#167).
- Suggested assignees (not contacted): @timurcarstensen
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **checkpoint**: source body «LAP](https://github.com/LAION-AI/CLAP) (v1) pretrained checkpoints and models trained with the most recent [open_clip](ht»; target title «Polish checkpoint conversion scripts and add unittests»
  - **markdown**: source body «ty functions for audio data handling | | `AUDIO_README.md` | Documentation for audio benchmarks with usage examp»; target body «github.com/OpenEuroLLM/hpo-experiment/blob/main/README.md)»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 15. [finalize HPLT 4.0 public release](https://github.com/OpenEuroLLM/web-data-processing/issues/1) ↔ [Adapting S1 to LUMI-O](https://github.com/hplt-project/HPLT-textpipes/issues/7)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 00efe157f2cb1cb2ba128461e0a8744dc9b8bb4bbc2cb89936deb847ebfb7e35
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 3574a597308492298cbd573784064b7824ec0cca1045eb5432af97ce8383252c
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 10.717; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#29).
- Suggested assignees (not contacted): @nvanva
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **lumio**: source body «`poor` data after filtering. of these, (a) resides on LUMI-O (with an interim manifesto in `/nird/datalake/NS8112K/»; target title «Adapting S1 to LUMI-O»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 16. [finalize HPLT 4.0 public release](https://github.com/OpenEuroLLM/web-data-processing/issues/1) ↔ [downloading 2025 CC crawls to LUMI-O](https://github.com/hplt-project/HPLT-textpipes/issues/9)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 00efe157f2cb1cb2ba128461e0a8744dc9b8bb4bbc2cb89936deb847ebfb7e35
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 46049d90e424be16cbe569d8df9c24e18cc2bb4a51d4eb06f9d892b474249f9f
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 10.717; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#29).
- Suggested assignees (not contacted): @nvanva, @oepen
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **lumio**: source body «`poor` data after filtering. of these, (a) resides on LUMI-O (with an interim manifesto in `/nird/datalake/NS8112K/»; target title «downloading 2025 CC crawls to LUMI-O»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 17. [Add audio modality support for CLAP evaluation](https://github.com/LAION-AI/CLIP_benchmark/pull/148) ↔ [Evaluate missing checkpoints](https://github.com/OpenEuroLLM/Taskboard/issues/66)

- Source: LAION-AI/CLIP_benchmark / pull_request / open / SHA256 df48eb6c4d53295923feb9d152e9e1974d46e8c6fd0ad0331df56de1b36ff473
- Possible related work: OpenEuroLLM/Taskboard / issue / closed / SHA256 aca3b3af9708b676d326195edc38be53b92908a595b1891972e6f1f92a6e869c
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 10.666; baseline top-1 agrees: no (baseline target ID: github:OpenEuroLLM/Taskboard#167).
- Suggested assignees (not contacted): @timurcarstensen
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **checkpoint**: source body «LAP](https://github.com/LAION-AI/CLAP) (v1) pretrained checkpoints and models trained with the most recent [open_clip](ht»; target title «Evaluate missing checkpoints»
  - **tokenizer**: source body «ependencies - `open_clip` (for model architecture and tokenizer) - `librosa` (audio decoding) - `torchaudio` (mel spec»; target body «ons. - [x] open-sci-ref_model-0.13b_data-CommonCorpus_tokenizer-GPT-NeoX_samples-300B_global_bs-1008_context-4096_sche»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 18. [opt-out handling](https://github.com/OpenEuroLLM/web-data-processing/issues/3) ↔ [De-chunking in warc2text](https://github.com/hplt-project/warc2text-runner/issues/22)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 1a4769a95e100eda9f656ca822cf45096f681cd1e88f11a36f0b509cca5ef344
- Possible related work: hplt-project/warc2text-runner / issue / closed / SHA256 db82b1a21482c9c8d943a94fb932d90839bf8ad8243acdba77e574f23a3cdb8a
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 9.803; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): @nvanva
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **warc2text**: source body «Update warc2text to support opt-out handling. Quick look at the Apertus»; target title «De-chunking in warc2text»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 19. [opt-out handling](https://github.com/OpenEuroLLM/web-data-processing/issues/3) ↔ [Add warc2text html parser output for tests](https://github.com/hplt-project/warc2text-runner/pull/3)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 1a4769a95e100eda9f656ca822cf45096f681cd1e88f11a36f0b509cca5ef344
- Possible related work: hplt-project/warc2text-runner / pull_request / closed / SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 9.803; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **warc2text**: source body «Update warc2text to support opt-out handling. Quick look at the Apertus»; target title «Add warc2text html parser output for tests»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 20. [audio and video extraction from WARCs](https://github.com/OpenEuroLLM/web-data-processing/issues/8) ↔ [De-chunking in warc2text](https://github.com/hplt-project/warc2text-runner/issues/22)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 ed185fc6ff1ef2c3e059152801691ee71e85c64b7b221bdce9294745dd782e2e
- Possible related work: hplt-project/warc2text-runner / issue / closed / SHA256 db82b1a21482c9c8d943a94fb932d90839bf8ad8243acdba77e574f23a3cdb8a
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 9.803; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): @nvanva
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **warc2text**: source body «owing [this suggestion](https://github.com/OpenEuroLLM/warc2text/issues/1#issuecomment-6186769627), I create this separ»; target title «De-chunking in warc2text»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 21. [audio and video extraction from WARCs](https://github.com/OpenEuroLLM/web-data-processing/issues/8) ↔ [Tag filters moved from warc2text](https://github.com/hplt-project/warc2text-runner/issues/6)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 ed185fc6ff1ef2c3e059152801691ee71e85c64b7b221bdce9294745dd782e2e
- Possible related work: hplt-project/warc2text-runner / issue / closed / SHA256 0d94917256843567ef3e993a5bfbd2524a06c76eeb38d7c776c6facf305f01ad
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 9.803; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): @ZJaume, @nvanva
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **warc2text**: source body «owing [this suggestion](https://github.com/OpenEuroLLM/warc2text/issues/1#issuecomment-6186769627), I create this separ»; target title «Tag filters moved from warc2text»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 22. [Running MoE sanity check baseline](https://github.com/OpenEuroLLM/Taskboard/issues/119) ↔ [use open_clip.get_tokenizer to support all tokenizers](https://github.com/LAION-AI/CLIP_benchmark/pull/19)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 2e4058574a103fb794120eb430bbfc666060b21d8bccf87d9c9b880508e0d5fb
- Possible related work: LAION-AI/CLIP_benchmark / pull_request / closed / SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 8.475; baseline top-1 agrees: no (baseline target ID: github:LAION-AI/CLIP_benchmark#114).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **tokenizer**: source body «- Run on Jupiter and LUMI - Tokenizer: Gpt-neox 20B, 50k vocab - Nemotron-cc-HQ - 300BT -»; target title «use open_clip.get_tokenizer to support all tokenizers»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 23. [Tokenizer evaluation](https://github.com/OpenEuroLLM/Taskboard/issues/146) ↔ [Multilingual benchmark datasets](https://github.com/LAION-AI/CLIP_benchmark/pull/113)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 f60963ca7f0673544d33bf3d599f942befa5365705eb63a2a7e94c18924a18d9
- Possible related work: LAION-AI/CLIP_benchmark / pull_request / closed / SHA256 3bc28d2d5ddbdaca6c343793b8bd3c640b5a21ee87141cad70154f325e423214
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 8.475; baseline top-1 agrees: yes (baseline target ID: github:LAION-AI/CLIP_benchmark#113).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **tokenizer**: source title «Tokenizer evaluation»; target body «nguage` method to set the target language for the NLLB tokenizer. 6. Enabled building CSV files from directories. @»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 24. [Key Features decisions:Special Tokens (BOS), Whitespace, Reversibility, and Byte Fallback etc](https://github.com/OpenEuroLLM/Taskboard/issues/148) ↔ [use open_clip.get_tokenizer to support all tokenizers](https://github.com/LAION-AI/CLIP_benchmark/pull/19)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 d4a367cadaa3aa00bc144ea65a63bb4842aadaf912d5f7b5e2928f61ee0c4c8a
- Possible related work: LAION-AI/CLIP_benchmark / pull_request / closed / SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 8.475; baseline top-1 agrees: no (baseline target ID: github:hplt-project/warc2text-runner#17).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **tokenizer**: source body «ing characters or subwords that are not present in the tokenizer's learned vocabulary. The behavior of the UNK token si»; target title «use open_clip.get_tokenizer to support all tokenizers»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 25. [Long-Context Data Generation](https://github.com/OpenEuroLLM/Taskboard/issues/339) ↔ [use open_clip.get_tokenizer to support all tokenizers](https://github.com/LAION-AI/CLIP_benchmark/pull/19)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 99bac3aa3e6944c44ac3f173ffde93b7e71046438847cc1324e3e6b8a51e21ba
- Possible related work: LAION-AI/CLIP_benchmark / pull_request / closed / SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 8.475; baseline top-1 agrees: no (baseline target ID: github:hplt-project/warc2text-runner#17).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **tokenizer**: source body «-4) with a genuine 120k input window. - **Per-language tokenizers** for tf-idf term extraction (esp. `el`, `uk`).»; target title «use open_clip.get_tokenizer to support all tokenizers»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

## What must be measured next

An independent reviewer should label the shortlist as **actionable reuse**, **related but already coordinated**, or **not useful**. Check the corresponding full-text baseline candidates under the same review protocol. Without these labels we cannot claim that matching adds value.

## Limitations

Bounded repo registry and source age, English-oriented tokens, GitHub-only pilot; The technical vocabulary is curated and tuned on this observed cohort, NOT a held-out validation. Issue/PR body and title verified for shortlisted cards, not issue comments or merge status. Closed pull requests are not necessarily merged. No claim of better quality than full-text search, no labels, no automated outreach. Source bodies longer than the configured limit are truncated for ranking.

