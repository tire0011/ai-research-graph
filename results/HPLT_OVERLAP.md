# HPLT ↔ OpenEuroLLM: source-audited code and issue overlaps

**Read-only pilot. Byte-identical files do not establish wasted effort. Closed issues do not establish reusable fixes.** No external messages sent.

Checked **3** pinned trees, **8** original issues, **2** code scopes, **5** cross-project issue pairs.

## Pinned Git-file comparisons

### common-crawl-download

Which Common Crawl acquisition scripts are byte-identical, and which have diverged?

- Sources: OpenEuroLLM/web-data-processing at 0765a2c413e46d3e106751bc7d8de4cb29df4053 versus hplt-project/HPLT-textpipes at 4bbfb80ed0c4b83c47860872904b75cfffacbd2f.
- Same suffix: **4** paths; **1** nontrivial exact files, **0** trivial exact files, **3** changed-file blobs.

| Component | Source A | Source B | Status |
| --- | --- | --- | --- |
| cc_list_latest.txt | [code](https://github.com/OpenEuroLLM/web-data-processing/blob/0765a2c413e46d3e106751bc7d8de4cb29df4053/download/cc/cc_list_latest.txt) | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/download/cc/cc_list_latest.txt) | same_relative_path_different_blobs |
| cc_list_latest_download.sh | [code](https://github.com/OpenEuroLLM/web-data-processing/blob/0765a2c413e46d3e106751bc7d8de4cb29df4053/download/cc/cc_list_latest_download.sh) | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/download/cc/cc_list_latest_download.sh) | same_relative_path_different_blobs |
| download_crawl_rclone.sh | [code](https://github.com/OpenEuroLLM/web-data-processing/blob/0765a2c413e46d3e106751bc7d8de4cb29df4053/download/cc/download_crawl_rclone.sh) | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/download/cc/download_crawl_rclone.sh) | same_relative_path_different_blobs |
| get_url_lists.sh | [code](https://github.com/OpenEuroLLM/web-data-processing/blob/0765a2c413e46d3e106751bc7d8de4cb29df4053/download/cc/get_url_lists.sh) | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/download/cc/get_url_lists.sh) | identical_nontrivial_file |

### hplt-stage2-lineage

Which Stage-2 pipeline utilities were carried forward unchanged, and which differ across HPLT releases?

- Sources: hplt-project/HPLT-textpipes at 4bbfb80ed0c4b83c47860872904b75cfffacbd2f versus hplt-project/warc2text-runner at 0b88ccc8f439d4375d880ff2ca2b385b903c00ff.
- Same suffix: **27** paths; **12** nontrivial exact files, **5** trivial exact files, **10** changed-file blobs.

| Component | Source A | Source B | Status |
| --- | --- | --- | --- |
| __init__.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/__init__.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/__init__.py) | identical_trivial_file |
| batch_htmls.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/batch_htmls.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/batch_htmls.py) | identical_nontrivial_file |
| batch_htmls_prtpy.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/batch_htmls_prtpy.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/batch_htmls_prtpy.py) | identical_nontrivial_file |
| fastertext_lid/__init__.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/fastertext_lid/__init__.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/fastertext_lid/__init__.py) | identical_trivial_file |
| fastertext_lid/basic_log.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/fastertext_lid/basic_log.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/fastertext_lid/basic_log.py) | identical_nontrivial_file |
| fastertext_lid/patterns.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/fastertext_lid/patterns.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/fastertext_lid/patterns.py) | identical_nontrivial_file |
| fastertext_lid/proto_langid.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/fastertext_lid/proto_langid.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/fastertext_lid/proto_langid.py) | same_relative_path_different_blobs |
| qualitycontrol/__init__.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/qualitycontrol/__init__.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/qualitycontrol/__init__.py) | identical_trivial_file |
| qualitycontrol/check_linecnt.sh | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/qualitycontrol/check_linecnt.sh) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/qualitycontrol/check_linecnt.sh) | same_relative_path_different_blobs |
| qualitycontrol/check_text_lang_linecnts.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/qualitycontrol/check_text_lang_linecnts.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/qualitycontrol/check_text_lang_linecnts.py) | identical_nontrivial_file |
| qualitycontrol/traferrstats.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/qualitycontrol/traferrstats.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/qualitycontrol/traferrstats.py) | same_relative_path_different_blobs |
| stage2download.sh | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/stage2download.sh) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/stage2download.sh) | identical_nontrivial_file |
| stage2local.sh | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/stage2local.sh) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/stage2local.sh) | same_relative_path_different_blobs |
| stage2local_batch.sh | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/stage2local_batch.sh) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/stage2local_batch.sh) | identical_nontrivial_file |
| stage2nodeparallel.sh | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/stage2nodeparallel.sh) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/stage2nodeparallel.sh) | same_relative_path_different_blobs |
| stage2nodeparallel_batched.sh | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/stage2nodeparallel_batched.sh) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/stage2nodeparallel_batched.sh) | same_relative_path_different_blobs |
| stage2stage.sh | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/stage2stage.sh) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/stage2stage.sh) | identical_nontrivial_file |
| stage2stagelumio.sh | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/stage2stagelumio.sh) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/stage2stagelumio.sh) | same_relative_path_different_blobs |
| stage2traf.sh | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/stage2traf.sh) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/stage2traf.sh) | same_relative_path_different_blobs |
| tagfilter/__init__.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/tagfilter/__init__.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/tagfilter/__init__.py) | identical_trivial_file |
| tagfilter/mt-filter-list.annotated | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/tagfilter/mt-filter-list.annotated) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/tagfilter/mt-filter-list.annotated) | identical_nontrivial_file |
| tagfilter/tagextractor.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/tagfilter/tagextractor.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/tagfilter/tagextractor.py) | identical_nontrivial_file |
| tagfilter/tagfilter1.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/tagfilter/tagfilter1.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/tagfilter/tagfilter1.py) | same_relative_path_different_blobs |
| trafilatura/__init__.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/trafilatura/__init__.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/trafilatura/__init__.py) | identical_trivial_file |
| trafilatura/measure_time.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/trafilatura/measure_time.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/trafilatura/measure_time.py) | identical_nontrivial_file |
| trafilatura/traf.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/trafilatura/traf.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/trafilatura/traf.py) | same_relative_path_different_blobs |
| trafilatura/traf_from_html.py | [code](https://github.com/hplt-project/HPLT-textpipes/blob/4bbfb80ed0c4b83c47860872904b75cfffacbd2f/src/hplt_textpipes/stage2/trafilatura/traf_from_html.py) | [code](https://github.com/hplt-project/warc2text-runner/blob/0b88ccc8f439d4375d880ff2ca2b385b903c00ff/src/warc2text_runner/stage2/trafilatura/traf_from_html.py) | identical_nontrivial_file |

## Original issue overlap (human review)

| OpenEuroLLM current task | HPLT historic task | Follow-up |
| --- | --- | --- |
| [download recent CC crawls to LUMIO](https://github.com/OpenEuroLLM/web-data-processing/issues/2) (open) | [downloading 2025 CC crawls to LUMI-O](https://github.com/hplt-project/HPLT-textpipes/issues/9) (closed) | inspect_prior_work |
| [robots.txt](https://github.com/OpenEuroLLM/web-data-processing/issues/7) (open) | [coordinate between uio and prompsit about robots.txt filtering](https://github.com/hplt-project/HPLT-textpipes/issues/17) (closed) | inspect_prior_work |
| [S2-S4 updates](https://github.com/OpenEuroLLM/web-data-processing/issues/6) (open) | [OpenLID 3 run](https://github.com/hplt-project/HPLT-textpipes/issues/19) (closed) | inspect_prior_work |
| [S2-S4 updates](https://github.com/OpenEuroLLM/web-data-processing/issues/6) (open) | [GlotLID v3 run](https://github.com/hplt-project/HPLT-textpipes/issues/21) (closed) | inspect_prior_work |
| [S2-S4 updates](https://github.com/OpenEuroLLM/web-data-processing/issues/6) (open) | [XML-to-MD run](https://github.com/hplt-project/HPLT-textpipes/issues/20) (closed) | inspect_prior_work |

## Source-backed issue observations

### common-crawl-lumio

Review the older HPLT LUMI-O Common Crawl workflow before duplicating download tooling.

- [A: download recent CC crawls to LUMIO](https://github.com/OpenEuroLLM/web-data-processing/issues/2) — open; phrase 'crawl' in body: 'Download the latest crawls to LUMIO. Due to insufficient free space on LUMIO for all crawl' (matched SHA256 ecb0d2f70fdee40a8970c59dabbf96f8f6a351fd0dce31163ce64d4bc23363cd; body SHA256 ecb0d2f70fdee40a8970c59dabbf96f8f6a351fd0dce31163ce64d4bc23363cd).
- [B: downloading 2025 CC crawls to LUMI-O](https://github.com/hplt-project/HPLT-textpipes/issues/9) — closed; phrase 'crawl' in body: 'and others have suggested we include the latest and greatest CC crawls in our raw data collection. i notice that also Hugging Face co' (matched SHA256 46049d90e424be16cbe569d8df9c24e18cc2bb4a51d4eb06f9d892b474249f9f; body SHA256 46049d90e424be16cbe569d8df9c24e18cc2bb4a51d4eb06f9d892b474249f9f).
- Duplicate implementation: **not established**. Issue comments and acceptance criteria require manual verification.

### robots-txt

Compare previously coordinated robots.txt filtering with the new planned interpretation of allow/deny rules.

- [A: robots.txt](https://github.com/OpenEuroLLM/web-data-processing/issues/7) — open; phrase 'robots.txt' in body: 'apt the intermediate step by jaume, interpreting the totality of robots.txt captures (now probably more conservatively then we used to) and' (matched SHA256 c3dc6cd8ff795cf5d7f7c658bb416174de9183beeca2ffbde2c295a2d34467a7; body SHA256 c3dc6cd8ff795cf5d7f7c658bb416174de9183beeca2ffbde2c295a2d34467a7).
- [B: coordinate between uio and prompsit about robots.txt filtering](https://github.com/hplt-project/HPLT-textpipes/issues/17) — closed; phrase 'robots.txt' in body: 'nd AB (ArchiveBot) will need to be filtered against the compiled robots.txt index. @nvanva and @ZJaume will need to be involved.' (matched SHA256 c536125202804a56c61942837bb338fcc6d5cb13beab404621d93179a9a5677d; body SHA256 c536125202804a56c61942837bb338fcc6d5cb13beab404621d93179a9a5677d).
- Duplicate implementation: **not established**. Issue comments and acceptance criteria require manual verification.

### openlid-upgrade

Check whether HPLT OpenLID v3 integration can be reused for the OpenEuroLLM pipeline update.

- [A: S2-S4 updates](https://github.com/OpenEuroLLM/web-data-processing/issues/6) — open; phrase 'openlid' in body: 'ements from Mattermost: "the latest trafilatura release, current openlid (v3) and glotlid versions, xml and md into one file, standard zs' (matched SHA256 da1ef26f63fa097d38f34a984399f68abb1ce63e59f0c6a34720e3cba39e83ec; body SHA256 da1ef26f63fa097d38f34a984399f68abb1ce63e59f0c6a34720e3cba39e83ec).
- [B: OpenLID 3 run](https://github.com/hplt-project/HPLT-textpipes/issues/19) — closed; phrase 'OpenLID' in title: 'OpenLID 3 run' (matched SHA256 cb2336f514662b00bd46f8fe74dd17da59fd2a3e6ed6eeeaa3e2adb9b2c28ad2; body SHA256 187c6d12083f5e2433794eeec7c4262587923c5c1b12eda01eb54ecbe8e01a90).
- Duplicate implementation: **not established**. Issue comments and acceptance criteria require manual verification.

### glotlid-upgrade

Check the earlier GlotLID v3 runner and interface before implementing an alternative.

- [A: S2-S4 updates](https://github.com/OpenEuroLLM/web-data-processing/issues/6) — open; phrase 'glotlid' in body: 'rmost: "the latest trafilatura release, current openlid (v3) and glotlid versions, xml and md into one file, standard zstd output, id ing' (matched SHA256 da1ef26f63fa097d38f34a984399f68abb1ce63e59f0c6a34720e3cba39e83ec; body SHA256 da1ef26f63fa097d38f34a984399f68abb1ce63e59f0c6a34720e3cba39e83ec).
- [B: GlotLID v3 run](https://github.com/hplt-project/HPLT-textpipes/issues/21) — closed; phrase 'GlotLID' in body: 'stage3 or a subfolder. @jindrahelcl Since you experimented with GlotLID v3 before, would you agree to create such a script with the hype' (matched SHA256 d0159e6614e5e6a6fb30d82d6c0866eb525466b81b8531500ce43b72ad8866d0; body SHA256 d0159e6614e5e6a6fb30d82d6c0866eb525466b81b8531500ce43b72ad8866d0).
- Duplicate implementation: **not established**. Issue comments and acceptance criteria require manual verification.

### xml-to-markdown

Inspect existing HPLT XML-to-Markdown script and I/O contract before combining outputs.

- [A: S2-S4 updates](https://github.com/OpenEuroLLM/web-data-processing/issues/6) — open; phrase 'xml' in body: 'trafilatura release, current openlid (v3) and glotlid versions, xml and md into one file, standard zstd output, id ingestion , and p' (matched SHA256 da1ef26f63fa097d38f34a984399f68abb1ce63e59f0c6a34720e3cba39e83ec; body SHA256 da1ef26f63fa097d38f34a984399f68abb1ce63e59f0c6a34720e3cba39e83ec).
- [B: XML-to-MD run](https://github.com/hplt-project/HPLT-textpipes/issues/20) — closed; phrase 'XML' in body: 'proto_langid.py, i.e. reading from stdin json lines containing 'xml' field and printing to stdout parallel json lines containing the' (matched SHA256 bf60c5b914728325a5707e79ce7ac51e8c403c7fc84ad60bacabd67335a18d35; body SHA256 bf60c5b914728325a5707e79ce7ac51e8c403c7fc84ad60bacabd67335a18d35).
- Duplicate implementation: **not established**. Issue comments and acceptance criteria require manual verification.

## Method boundaries

Curated pair selection. Git blob hashes establish only byte identity. Shared paths with different hashes indicate code differences, not necessarily historical provenance. Original issue descriptions and state re-read; comments, code semantics, licenses and resolution are NOT validated. No automatic outreach.
