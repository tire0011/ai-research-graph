# Collaboration Matcher — cross-organization pilot

**Review only. Rule-based matcher, not an LLM and not proof of duplicate effort.**
Audited **665** public issues/PRs in **8** repositories, considering **202** recently opened active items. Found **25** candidate handoffs. Re-checked **25** underlying issue/PR sources.

**Same-input full-text baseline:** 11/25 suggestions are also the lexical baseline's top-1 target for that source. **This does not establish improved precision or recall.**

## Review queue (no messages sent)

### 1. [Define Data Compliance Governance Strategy](https://github.com/OpenEuroLLM/Taskboard/issues/360) ↔ [AI Act Compliance Gaps and Security Governance Issues Identified in Model Evaluation Framework](https://github.com/LAION-AI/CLIP_benchmark/issues/149)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 c87e0ff1dfe49efbaec80c08479b16bba6b3d6d75ea6f569a1c21ccb66fbb2dd
- Possible related work: LAION-AI/CLIP_benchmark / issue / closed / SHA256 3ba86627be99974687400577dcefbd9dbeb2d236e79edb056033572054307e8c
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 134.031; baseline top-1 agrees: yes (baseline target ID: github:LAION-AI/CLIP_benchmark#149).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **gaps**: source body «olicies, assumptions, and justifications. * Identified gaps between the current implementation and the agreed gove»; target title «AI Act Compliance Gaps and Security Governance Issues Identified in Model Eva»
  - **governance**: source title «Define Data Compliance Governance Strategy»; target title «AI Act Compliance Gaps and Security Governance Issues Identified in Model Evaluation Framework»
  - **identified**: source body «f current policies, assumptions, and justifications. * Identified gaps between the current implementation and the agreed»; target title «AI Act Compliance Gaps and Security Governance Issues Identified in Model Evaluation Framework»
  - **compliance**: source title «Define Data Compliance Governance Strategy»; target title «AI Act Compliance Gaps and Security Governance Issues Identified in Mode»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 2. [Discover and Verify Concepts in Preference and Instruction-tuning Datasets](https://github.com/OpenEuroLLM/Taskboard/issues/353) ↔ [Proposal: optional audit manifest for benchmark result provenance](https://github.com/LAION-AI/CLIP_benchmark/issues/153)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 9d4524739d6a69b5dddd2d9e59e239c003a333050c64303682444318a32e089d
- Possible related work: LAION-AI/CLIP_benchmark / issue / open / SHA256 7ff165505ad9f26126c61508ac39b1703bc1b581980e32fb6fa3595afd4ae676
- Category: possible_parallel_work — **not a verified solution or collaboration**.
- Ranking score: 114.38; baseline top-1 agrees: yes (baseline target ID: github:LAION-AI/CLIP_benchmark#153).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **optional**: source body «teria. The minimum input is a prompt, a response, and optional metadata: $$ \mathcal{D}_{\mathrm{single}} = \{(x_i,y»; target title «Proposal: optional audit manifest for benchmark result provenance»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 3. [Train and export the OELLM 9B function-calling SFT checkpoint on LUMI](https://github.com/OpenEuroLLM/Taskboard/issues/385) ↔ [Bump setuptools from 65.5.0 to 70.0.0 in /two](https://github.com/hplt-project/warc2text-runner/pull/17)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 4a7887b689cbdc129280936e03a9a1684aaabf7c5b42deaf375b4f6039151ffc
- Possible related work: hplt-project/warc2text-runner / pull_request / closed / SHA256 e941f334b8ad33a1d682174a2c4b884398dc3884534e13ecab2296cd436d70a1
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 81.772; baseline top-1 agrees: yes (baseline target ID: github:hplt-project/warc2text-runner#17).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: yes
- Original matching expressions (not independently validated):
  - **two**: source body «ce packing | | Batch | 2,048 prepared rows per update; two accumulation microsteps in measured windows | | Memory»; target title «Bump setuptools from 65.5.0 to 70.0.0 in /two»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 4. [Add audio modality support for CLAP evaluation](https://github.com/LAION-AI/CLIP_benchmark/pull/148) ↔ [Key Features decisions:Special Tokens (BOS), Whitespace, Reversibility, and Byte Fallback etc](https://github.com/OpenEuroLLM/Taskboard/issues/148)

- Source: LAION-AI/CLIP_benchmark / pull_request / open / SHA256 df48eb6c4d53295923feb9d152e9e1974d46e8c6fd0ad0331df56de1b36ff473
- Possible related work: OpenEuroLLM/Taskboard / issue / open / SHA256 d4a367cadaa3aa00bc144ea65a63bb4842aadaf912d5f7b5e2928f61ee0c4c8a
- Category: possible_parallel_work — **not a verified solution or collaboration**.
- Ranking score: 80.92; baseline top-1 agrees: no (baseline target ID: github:hplt-project/warc2text-runner#17).
- Suggested assignees (not contacted): @flxst
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **fallback**: source body «p` and `clap_v2` model types with graceful ImportError fallback | | `clip_benchmark/cli.py` | Adds `--modality` flag (»; target title «cial Tokens (BOS), Whitespace, Reversibility, and Byte Fallback etc»
  - **key**: source body «lfoundations/open_clip) CLAP implementation (v2). ### Key features - **Audio modality in all evaluation tasks**»; target title «Key Features decisions:Special Tokens (BOS), Whitespace, R»
  - **feature**: source body «ndations/open_clip) CLAP implementation (v2). ### Key features - **Audio modality in all evaluation tasks**: zero-sh»; target title «Key Features decisions:Special Tokens (BOS), Whitespace, Reversibil»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 5. [finalize HPLT 4.0 public release](https://github.com/OpenEuroLLM/web-data-processing/issues/1) ↔ [moving the pool to nird](https://github.com/hplt-project/HPLT-textpipes/issues/29)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 00efe157f2cb1cb2ba128461e0a8744dc9b8bb4bbc2cb89936deb847ebfb7e35
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 ec6423123f6696a9024f1f190e4d3211dd18887b512840a61541af937353e15d
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 77.622; baseline top-1 agrees: yes (baseline target ID: github:hplt-project/HPLT-textpipes#29).
- Suggested assignees (not contacted): @akutuzov
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **pool**: source body «rom the HPLT pipeline, (b) 450 or so terabytes of the `pool`, and 44 + 12 + 15 terabytes of final `clean`, `noisy`»; target title «moving the pool to nird»
  - **nird**: source body «(a) resides on LUMI-O (with an interim manifesto in `/nird/datalake/NS8112K/public/four/pool/lumio.jsonl`), while»; target title «moving the pool to nird»
  - **public**: source title «finalize HPLT 4.0 public release»; target body «e download directory should be `/nird/datalake/NS8112K/public/four/pool/`, with sub-directories for each of the 75 c»
  - **release**: source title «finalize HPLT 4.0 public release»; target body «we will want to move the `pool` release (sans the html files) to the nird download site as qui»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 6. [Key Features decisions:Special Tokens (BOS), Whitespace, Reversibility, and Byte Fallback etc](https://github.com/OpenEuroLLM/Taskboard/issues/148) ↔ [Bump setuptools from 65.5.0 to 70.0.0 in /two](https://github.com/hplt-project/warc2text-runner/pull/17)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 d4a367cadaa3aa00bc144ea65a63bb4842aadaf912d5f7b5e2928f61ee0c4c8a
- Possible related work: hplt-project/warc2text-runner / pull_request / closed / SHA256 e941f334b8ad33a1d682174a2c4b884398dc3884534e13ecab2296cd436d70a1
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 77.039; baseline top-1 agrees: yes (baseline target ID: github:hplt-project/warc2text-runner#17).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: yes
- Original matching expressions (not independently validated):
  - **fallback**: source title «cial Tokens (BOS), Whitespace, Reversibility, and Byte Fallback etc»; target body «urces</code> when trying to read files in UTF-8 with a fallback -- by :user:<code>Avasam</code> (<a href="https://redi»
  - **feature**: source title «Key Features decisions:Special Tokens (BOS), Whitespace, Reversibil»; target body «ngelog</a>.</em></p> <blockquote> <h1>v70.0.0</h1> <h2>Features</h2> <ul> <li>Emit a warning when <code>[tools.setupto»
  - **etc**: source title «ns (BOS), Whitespace, Reversibility, and Byte Fallback etc»; target body «, script wrappers, automatically updated config files, etc..) Although precautions were taken to minimize disrupt»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 7. [Discover and Verify Concepts in Preference and Instruction-tuning Datasets](https://github.com/OpenEuroLLM/Taskboard/issues/353) ↔ [AI Act Compliance Gaps and Security Governance Issues Identified in Model Evaluation Framework](https://github.com/LAION-AI/CLIP_benchmark/issues/149)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 9d4524739d6a69b5dddd2d9e59e239c003a333050c64303682444318a32e089d
- Possible related work: LAION-AI/CLIP_benchmark / issue / closed / SHA256 3ba86627be99974687400577dcefbd9dbeb2d236e79edb056033572054307e8c
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 75.853; baseline top-1 agrees: no (baseline target ID: github:LAION-AI/CLIP_benchmark#153).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **compliance**: source body «cepts and training examples in Dolci that teach unsafe compliance and other undesirable behaviors. The authors then show»; target title «AI Act Compliance Gaps and Security Governance Issues Identified in Mode»
  - **framework**: source body «I have been developing a framework for analyzing Post-Training datas for a while, inspire»; target title «urity Governance Issues Identified in Model Evaluation Framework»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 8. [Add audio modality support for CLAP evaluation](https://github.com/LAION-AI/CLIP_benchmark/pull/148) ↔ [Bump setuptools from 65.5.0 to 70.0.0 in /two](https://github.com/hplt-project/warc2text-runner/pull/17)

- Source: LAION-AI/CLIP_benchmark / pull_request / open / SHA256 df48eb6c4d53295923feb9d152e9e1974d46e8c6fd0ad0331df56de1b36ff473
- Possible related work: hplt-project/warc2text-runner / pull_request / closed / SHA256 e941f334b8ad33a1d682174a2c4b884398dc3884534e13ecab2296cd436d70a1
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 72.486; baseline top-1 agrees: yes (baseline target ID: github:hplt-project/warc2text-runner#17).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: yes
- Original matching expressions (not independently validated):
  - **two**: source body «ated into the existing CLI and evaluation pipeline - **Two CLAP model loaders**: - `clap` — loads old LAION-CLA»; target title «Bump setuptools from 65.5.0 to 70.0.0 in /two»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 9. [Synthetic Generation for Multilingual Instruction Tuning](https://github.com/OpenEuroLLM/Taskboard/issues/437) ↔ [(storage) management around 3.1 release](https://github.com/hplt-project/HPLT-textpipes/issues/18)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 60340bc07b4f7dab33d9146825280eb7e5b3f048aed32032c989c468b128ca26
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 aab15a7df6112e6a2be4fd4de1abba903d75bbfc6ccda59c1e84dc47d3908b80
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 69.733; baseline top-1 agrees: no (baseline target ID: github:LAION-AI/CLIP_benchmark#148).
- Suggested assignees (not contacted): @nvanva, @oepen
- Ranking text truncated: yes
- Original matching expressions (not independently validated):
  - **instruction**: source title «Synthetic Generation for Multilingual Instruction Tuning»; target body «ZJaume) + ~~maybe perform WDS annotation (code and instructions from prompsit)~~ + drop documents flagged for `rob»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 10. [Synthetic Generation for Multilingual Instruction Tuning](https://github.com/OpenEuroLLM/Taskboard/issues/437) ↔ [Proposal: optional audit manifest for benchmark result provenance](https://github.com/LAION-AI/CLIP_benchmark/issues/153)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 60340bc07b4f7dab33d9146825280eb7e5b3f048aed32032c989c468b128ca26
- Possible related work: LAION-AI/CLIP_benchmark / issue / open / SHA256 7ff165505ad9f26126c61508ac39b1703bc1b581980e32fb6fa3595afd4ae676
- Category: possible_parallel_work — **not a verified solution or collaboration**.
- Ranking score: 69.091; baseline top-1 agrees: no (baseline target ID: github:LAION-AI/CLIP_benchmark#148).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: yes
- Original matching expressions (not independently validated):
  - **optional**: source body «------------------+ | dedupe (exact-hash, optional embedding) | +------------------------»; target title «Proposal: optional audit manifest for benchmark result provenance»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 11. [Long-Context Data Generation](https://github.com/OpenEuroLLM/Taskboard/issues/339) ↔ [Bump setuptools from 65.5.0 to 70.0.0 in /two](https://github.com/hplt-project/warc2text-runner/pull/17)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 99bac3aa3e6944c44ac3f173ffde93b7e71046438847cc1324e3e6b8a51e21ba
- Possible related work: hplt-project/warc2text-runner / pull_request / closed / SHA256 e941f334b8ad33a1d682174a2c4b884398dc3884534e13ecab2296cd436d70a1
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 68.788; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: yes
- Original matching expressions (not independently validated):
  - **two**: source body «l has to be synthesized deliberately. ## Description Two candidate generation paths were scoped (writeup §5):»; target title «Bump setuptools from 65.5.0 to 70.0.0 in /two»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 12. [extract additional WARC metadata](https://github.com/OpenEuroLLM/warc2text/issues/1) ↔ [downloading 2025 CC crawls to LUMI-O](https://github.com/hplt-project/HPLT-textpipes/issues/9)

- Source: OpenEuroLLM/warc2text / issue / open / SHA256 d0efd4d10dc3ec879537c86212cdd10e121a3d0e1d2280118ea7cb2cc68c5436
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 46049d90e424be16cbe569d8df9c24e18cc2bb4a51d4eb06f9d892b474249f9f
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 66.217; baseline top-1 agrees: yes (baseline target ID: github:hplt-project/HPLT-textpipes#9).
- Suggested assignees (not contacted): @nvanva, @oepen
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **warc**: source title «extract additional WARC metadata»; target body «crawls to LUMI. @nvanva, seeing as you are central in WARC data management currently and have extensive experienc»
  - **crawl**: source body «new invention, so presumably will hardly be present in crawls before 2024. but for newer data, it would be interest»; target title «downloading 2025 CC crawls to LUMI-O»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 13. [Train and export the OELLM 9B function-calling SFT checkpoint on LUMI](https://github.com/OpenEuroLLM/Taskboard/issues/385) ↔ [Upload lang split scripts](https://github.com/hplt-project/warc2text-runner/pull/4)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 4a7887b689cbdc129280936e03a9a1684aaabf7c5b42deaf375b4f6039151ffc
- Possible related work: hplt-project/warc2text-runner / pull_request / closed / SHA256 670bb20dfafbe226a2dc3b694218549ec67618d43e24bda14f8ffcad4d9f087e
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 65.761; baseline top-1 agrees: no (baseline target ID: github:hplt-project/warc2text-runner#17).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **split**: source body «ldout accounting. The exact prepared train and holdout splits are available in the [openeurollm/function-calling-sft»; target title «Upload lang split scripts»
  - **lumi**: source title «export the OELLM 9B function-calling SFT checkpoint on LUMI»; target body «*/docs.zst ``` reaching 90MB/s (on my machine, maybe LUMI could be more). It's not a super fast speed but, given»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 14. [Key Features decisions:Special Tokens (BOS), Whitespace, Reversibility, and Byte Fallback etc](https://github.com/OpenEuroLLM/Taskboard/issues/148) ↔ [stage1 does not correctly handle WARC paths containing special characters](https://github.com/hplt-project/warc2text-runner/issues/14)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 d4a367cadaa3aa00bc144ea65a63bb4842aadaf912d5f7b5e2928f61ee0c4c8a
- Possible related work: hplt-project/warc2text-runner / issue / closed / SHA256 bdd9ed64c799b971193460d7cc88d72f23efdfb19c472d8090fa313e9174cda1
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 63.099; baseline top-1 agrees: no (baseline target ID: github:hplt-project/warc2text-runner#17).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **character**: source body «n ([UNK]): Establish the designated token for handling characters or subwords that are not present in the tokenizer's le»; target title «oes not correctly handle WARC paths containing special characters»
  - **handle**: source body «of Joiners: Ensure that the decoding process correctly handles the joining of subwords, particularly in models that r»; target title «stage1 does not correctly handle WARC paths containing special characters»
  - **special**: source title «Key Features decisions:Special Tokens (BOS), Whitespace, Reversibility, and Byte Fall»; target title «stage1 does not correctly handle WARC paths containing special characters»
  - **correctly**: source body «Handling of Joiners: Ensure that the decoding process correctly handles the joining of subwords, particularly in model»; target title «stage1 does not correctly handle WARC paths containing special characters»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 15. [DPO checkpoint merging](https://github.com/OpenEuroLLM/Taskboard/issues/434) ↔ [Organize CLI arguments into groups](https://github.com/LAION-AI/CLIP_benchmark/issues/66)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 9985a3cd2bd18961cf201cb455229570a8bb824d7c89f04e363efbd32bb371c5
- Possible related work: LAION-AI/CLIP_benchmark / issue / open / SHA256 d118a2d13791b6d3728b2fd1cf3cc5ae675a7e327638a1d893ee9da12463aa57
- Category: possible_parallel_work — **not a verified solution or collaboration**.
- Ranking score: 58.97; baseline top-1 agrees: yes (baseline target ID: github:LAION-AI/CLIP_benchmark#66).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **checkpoint**: source title «DPO checkpoint merging»; target body «--pretrained PRETRAINED Model checkpoint name to use from OpenCLIP --task {zeroshot_classifi»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 16. [DPO checkpoint merging](https://github.com/OpenEuroLLM/Taskboard/issues/434) ↔ [Upload lang split scripts](https://github.com/hplt-project/warc2text-runner/pull/4)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 9985a3cd2bd18961cf201cb455229570a8bb824d7c89f04e363efbd32bb371c5
- Possible related work: hplt-project/warc2text-runner / pull_request / closed / SHA256 670bb20dfafbe226a2dc3b694218549ec67618d43e24bda14f8ffcad4d9f087e
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 58.286; baseline top-1 agrees: no (baseline target ID: github:LAION-AI/CLIP_benchmark#66).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **split**: source body «the one with the highest ELO. - **Honest selection.** Split the held-out benchmarks into two halves. Use one half»; target title «Upload lang split scripts»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 17. [extract additional WARC metadata](https://github.com/OpenEuroLLM/warc2text/issues/1) ↔ [pick up crawl identifier in repackaging](https://github.com/hplt-project/monotextor-slurm/issues/9)

- Source: OpenEuroLLM/warc2text / issue / open / SHA256 d0efd4d10dc3ec879537c86212cdd10e121a3d0e1d2280118ea7cb2cc68c5436
- Possible related work: hplt-project/monotextor-slurm / issue / closed / SHA256 fd551bc90d760be0ae4250bb2a565bf33b0c8da27590f3234724cab5df392561
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 58.228; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#9).
- Suggested assignees (not contacted): @ZJaume
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **identifier**: source body «ns to be seen whether e.g. FineWeb has preserved these identifiers, but in principle we should in the HPLT data). anothe»; target title «pick up crawl identifier in repackaging»
  - **warc**: source title «extract additional WARC metadata»; target body «2 does not include the crawl identifier. the specific WARC file name is there, but that may not be unique across»
  - **metadata**: source title «extract additional WARC metadata»; target body «metadata after S1 and S2 does not include the crawl identifier.»
  - **crawl**: source body «new invention, so presumably will hardly be present in crawls before 2024. but for newer data, it would be interest»; target title «pick up crawl identifier in repackaging»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 18. [[32B Dense] Mid-training downstream evals](https://github.com/OpenEuroLLM/Taskboard/issues/407) ↔ [Bump setuptools from 65.5.0 to 70.0.0 in /two](https://github.com/hplt-project/warc2text-runner/pull/17)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 f6dfb8a222749af2be2ed0a2ed722a3f1d9f8942bae220aec5ab05f86df724b4
- Possible related work: hplt-project/warc2text-runner / pull_request / closed / SHA256 e941f334b8ad33a1d682174a2c4b884398dc3884534e13ecab2296cd436d70a1
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 54.628; baseline top-1 agrees: no (baseline target ID: github:LAION-AI/CLIP_benchmark#148).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: yes
- Original matching expressions (not independently validated):
  - **two**: source body «xport PATH=$UV_TOOL_BIN_DIR:$PATH # add these two export lines to ~/.bashrc uv tool install -p 3.12 "gi»; target title «Bump setuptools from 65.5.0 to 70.0.0 in /two»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 19. [Define Data Compliance Governance Strategy](https://github.com/OpenEuroLLM/Taskboard/issues/360) ↔ [Proposal: optional audit manifest for benchmark result provenance](https://github.com/LAION-AI/CLIP_benchmark/issues/153)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 c87e0ff1dfe49efbaec80c08479b16bba6b3d6d75ea6f569a1c21ccb66fbb2dd
- Possible related work: LAION-AI/CLIP_benchmark / issue / open / SHA256 7ff165505ad9f26126c61508ac39b1703bc1b581980e32fb6fa3595afd4ae676
- Category: possible_parallel_work — **not a verified solution or collaboration**.
- Ranking score: 54.548; baseline top-1 agrees: no (baseline target ID: github:LAION-AI/CLIP_benchmark#149).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **provenance**: source body «cence types. * Dataset inclusion/exclusion criteria. * Provenance requirements. * Any other collection constraints. 2.»; target title «Proposal: optional audit manifest for benchmark result provenance»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 20. [download recent CC crawls to LUMIO](https://github.com/OpenEuroLLM/web-data-processing/issues/2) ↔ [downloading 2025 CC crawls to LUMI-O](https://github.com/hplt-project/HPLT-textpipes/issues/9)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 ecb0d2f70fdee40a8970c59dabbf96f8f6a351fd0dce31163ce64d4bc23363cd
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 46049d90e424be16cbe569d8df9c24e18cc2bb4a51d4eb06f9d892b474249f9f
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 54.367; baseline top-1 agrees: yes (baseline target ID: github:hplt-project/HPLT-textpipes#9).
- Suggested assignees (not contacted): @nvanva, @oepen
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **lumio**: source title «download recent CC crawls to LUMIO»; target title «downloading 2025 CC crawls to LUMI-O»
  - **crawl**: source title «download recent CC crawls to LUMIO»; target title «downloading 2025 CC crawls to LUMI-O»
  - **download**: source title «download recent CC crawls to LUMIO»; target body «lf a day (using a single "small" node and 128 parallel download threads). i am guessing a CC crawl is about ten times»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 21. [S2-S4 updates](https://github.com/OpenEuroLLM/web-data-processing/issues/6) ↔ [(storage) management around 3.1 release](https://github.com/hplt-project/HPLT-textpipes/issues/18)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 da1ef26f63fa097d38f34a984399f68abb1ce63e59f0c6a34720e3cba39e83ec
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 aab15a7df6112e6a2be4fd4de1abba903d75bbfc6ccda59c1e84dc47d3908b80
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 53.592; baseline top-1 agrees: yes (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): @nvanva, @oepen
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **release**: source body «requirements from Mattermost: "the latest trafilatura release, current openlid (v3) and glotlid versions, xml and md»; target title «(storage) management around 3.1 release»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 22. [Long-Context Data Generation](https://github.com/OpenEuroLLM/Taskboard/issues/339) ↔ [Stage 1 preprocessing for LUMI with streaming from/to LUMI-O](https://github.com/hplt-project/HPLT-textpipes/pull/15)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 99bac3aa3e6944c44ac3f173ffde93b7e71046438847cc1324e3e6b8a51e21ba
- Possible related work: hplt-project/HPLT-textpipes / pull_request / closed / SHA256 5ccba177b5f7bb930e7b93c280890adba195794793259cf813d20725e5ac817a
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 50.405; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#18).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **stage**: source body «e **task/answer layer** for our long-context extension stage, turning sourced long documents into training examples»; target title «Stage 1 preprocessing for LUMI with streaming from/to LUMI-O»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 23. [add text summarization tasks](https://github.com/OpenEuroLLM/Taskboard/issues/423) ↔ [Add audio modality support for CLAP evaluation](https://github.com/LAION-AI/CLIP_benchmark/pull/148)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 26d6b59478169f3c96b8a7ad09aeff1c3e5df2b78d3042f7d8ac2629c10535a1
- Possible related work: LAION-AI/CLIP_benchmark / pull_request / open / SHA256 df48eb6c4d53295923feb9d152e9e1974d46e8c6fd0ad0331df56de1b36ff473
- Category: possible_parallel_work — **not a verified solution or collaboration**.
- Ranking score: 49.798; baseline top-1 agrees: yes (baseline target ID: github:LAION-AI/CLIP_benchmark#148).
- Suggested assignees (not contacted): not specified
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **tasks**: source title «add text summarization tasks»; target body «### Key features - **Audio modality in all evaluation tasks**: zero-shot classification, zero-shot retrieval, and»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 24. [finalize HPLT 4.0 public release](https://github.com/OpenEuroLLM/web-data-processing/issues/1) ↔ [(storage) management around 3.1 release](https://github.com/hplt-project/HPLT-textpipes/issues/18)

- Source: OpenEuroLLM/web-data-processing / issue / open / SHA256 00efe157f2cb1cb2ba128461e0a8744dc9b8bb4bbc2cb89936deb847ebfb7e35
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 aab15a7df6112e6a2be4fd4de1abba903d75bbfc6ccda59c1e84dc47d3908b80
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 48.7; baseline top-1 agrees: no (baseline target ID: github:hplt-project/HPLT-textpipes#29).
- Suggested assignees (not contacted): @nvanva, @oepen
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **hplt**: source title «finalize HPLT 4.0 public release»; target body «background: https://ms.neural.mt/hplt/pl/mazfqbsf5fr5bea8gukc83m34o + ArchiveBot 2.3 pib on»
  - **release**: source title «finalize HPLT 4.0 public release»; target title «(storage) management around 3.1 release»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

### 25. [[32B Dense] Mid-training downstream evals](https://github.com/OpenEuroLLM/Taskboard/issues/407) ↔ [(storage) management around 3.1 release](https://github.com/hplt-project/HPLT-textpipes/issues/18)

- Source: OpenEuroLLM/Taskboard / issue / open / SHA256 f6dfb8a222749af2be2ed0a2ed722a3f1d9f8942bae220aec5ab05f86df724b4
- Possible related work: hplt-project/HPLT-textpipes / issue / closed / SHA256 aab15a7df6112e6a2be4fd4de1abba903d75bbfc6ccda59c1e84dc47d3908b80
- Category: possible_prior_work — **not a verified solution or collaboration**.
- Ranking score: 45.786; baseline top-1 agrees: no (baseline target ID: github:LAION-AI/CLIP_benchmark#148).
- Suggested assignees (not contacted): @nvanva, @oepen
- Ranking text truncated: no
- Original matching expressions (not independently validated):
  - **storage**: source body «write access to the shared eval directory. ### Weight storage Converted HF checkpoints can be found here: - `/e/fs»; target title «(storage) management around 3.1 release»
- Suggested review: compare actual code, current acceptance criteria, age of earlier work and whether the teams already coordinate.

## What must be measured next

An independent reviewer should label the shortlist as **actionable reuse**, **related but already coordinated**, or **not useful**. Check the corresponding full-text baseline candidates under the same review protocol. Without these labels we cannot claim that matching adds value.

## Limitations

Bounded repo registry and source age, English-oriented tokens, GitHub-only pilot; issue/PR body and title verified for shortlisted cards, not issue comments or merge status. Closed pull requests are not necessarily merged. No claim of better quality than full-text search, no labels, no automated outreach. Source bodies longer than the configured limit are truncated for ranking.

