# Research mechanism extraction pilot

Refs #42 and the negative collaboration evaluation in #64. Experimental only.

## Fixed evaluation protocol

Select 20 modern versioned arXiv records from the existing published discovery state by SHA256 order within cs.AI/cs.CL/cs.LG. Known cases (including AtmosRegime, RuleCraft, Multiverse and other recently reviewed papers) are excluded. This is a bounded snapshot sample, not a representative or independently verified unseen cohort. The two known papers are reserved for separately labelled calibration; they do not contribute to prospective evaluation. The PR workflow freezes the snapshot and exact-version abstract packets as artifacts, with explicit collection errors. No paid inference is performed by PR CI.

Use existing semantic_review provider transport. Six fields with source section IDs or null; model text is not verified truth. Cache keyed by packet, model, provider and extractor version. Persist the output file locally and supply it on subsequent runs. The cache is not yet automatically committed to the cumulative discovery branch.

After downloading the cohort artifact (Windows PowerShell):

```powershell
python research_mechanisms.py --snapshot results/research-mechanisms/source_snapshot.json --packets results/research-mechanisms/packets.json --provider local --model YOUR_MODEL --output results/research-mechanisms-local
```

Use `--provider mistral --model mistral-small-latest` with a configured MISTRAL_API_KEY only if explicitly choosing hosted inference. Up to 20 calls. Reuse previous successful extraction via `--previous results/research-mechanisms-local/extractions.json`. Never commit credentials. Pin the actual model ID if possible.

The structured ranker compares question/measurement terms and mechanism/intervention fields, against plain IDF overlap on the same supplied abstracts. This is a heuristic over LLM-extracted structure, not an embedding search or proof of semantic advantage. It preserves missing extraction coverage. Review the union of top ten pairs per arm with identical source evidence via existing semantic_review.py; at most 20 pair calls, optional. For independent evaluation, shuffle the union and conceal rankings from reviewers, record falsifiable experiment, distinct methods, actual compatibility, counterevidence and existing coordination, classify plausible/testable vs weak/unsupported/unknown. Compare useful unique proposals, abstention, cost and review effort. Include a direct equal-source LLM baseline before making any claim of graph advantage. Neither valid references nor high agreement prove scientific entailment. No automatic graph promotion, contact or external repository changes.

Known calibration: AtmosRegime (2611.28669) and RuleCraft (2611.28745), already identified and contacted. Their control extraction and pair review are not yet run. No new independent outcome labels or model inference results are claimed by this change.
