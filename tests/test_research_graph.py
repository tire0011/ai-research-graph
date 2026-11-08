import base64
import json
import unittest
import urllib.error
from unittest.mock import patch

from research_graph import (
    citation_coverage, enrich_publications, exact_reference, external_hf_asset,
    github_metadata_inventory, dataset_urls_in_source, resolve_github_dataset_declarations,
    hf_card_declarations, identifiers_in, incomplete_essential_sources,
    linked_experiment_runs, links_between, normalized, openaire_by_arxiv_batch, openaire_node,
    quality_profile, report, scholarly_links, verify_external_hf_references,
)


class ResearchGraphTests(unittest.TestCase):
    def setUp(self):
        self.asset = {
            "id": "hf:dataset:openeurollm/prelude-base-eval-scores", "type": "dataset",
            "title": "openeurollm/prelude-base-eval-scores",
            "url": "https://huggingface.co/datasets/openeurollm/prelude-base-eval-scores",
        }

    def issue(self, body):
        return {"id": "github:OpenEuroLLM/Taskboard#445", "type": "issue", "title": "evaluation", "description": body, "url": "https://github.com/OpenEuroLLM/Taskboard/issues/445"}

    def test_explicit_hf_link_is_recorded(self):
        result = links_between([self.issue(f"See {self.asset['url']}"), self.asset])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "explicit_reference")
        self.assertEqual(result[0]["evidence_type"], "url")
        self.assertIn("huggingface.co", result[0]["context"])

    def test_exact_hf_id_is_recorded(self):
        result = links_between([self.issue("openeurollm/prelude-base-eval-scores"), self.asset])
        self.assertEqual(result[0]["status"], "explicit_reference")
        self.assertEqual(result[0]["evidence_type"], "repository_id")

    def test_name_only_is_not_verified(self):
        result = links_between([self.issue("Update prelude-base-eval-scores plot"), self.asset])
        self.assertEqual(result[0]["status"], "candidate")

    def test_generic_model_name_does_not_match(self):
        self.assertEqual(links_between([self.issue("Evaluate Prelude") , self.asset]), [])

    def test_cross_source_only(self):
        self.assertEqual(links_between([self.issue("See another issue")]), [])

    def test_rejects_tokenizer_prefix_false_positive(self):
        older = {"id": "hf:model:openeurollm/tokenizer-256k", "type": "model", "title": "openeurollm/tokenizer-256k", "url": "https://huggingface.co/openeurollm/tokenizer-256k"}
        newer = {"id": "hf:model:openeurollm/tokenizer-256k-v2", "type": "model", "title": "openeurollm/tokenizer-256k-v2", "url": "https://huggingface.co/openeurollm/tokenizer-256k-v2"}
        edges = links_between([self.issue("See https://huggingface.co/openeurollm/tokenizer-256k-v2"), older, newer])
        self.assertEqual([edge["target"] for edge in edges], [newer["id"]])

    def test_rejects_model_prefix_of_dataset(self):
        model = {"id": "hf:model:openeurollm/prelude-base", "type": "model", "title": "openeurollm/prelude-base", "url": "https://huggingface.co/openeurollm/prelude-base"}
        result = links_between([self.issue(self.asset["url"]), model, self.asset])
        self.assertEqual([edge["target"] for edge in result], [self.asset["id"]])

    def test_repo_id_followed_by_slash_is_valid(self):
        self.assertIsNotNone(exact_reference("openeurollm/foo/resolve/main", "openeurollm/foo"))

    def test_foreign_hf_namespace_not_a_candidate(self):
        model = {"id": "hf:model:openeurollm/OLMo-3-7B-Think-SFT", "type": "model", "title": "openeurollm/OLMo-3-7B-Think-SFT", "url": "https://huggingface.co/openeurollm/OLMo-3-7B-Think-SFT"}
        self.assertEqual(links_between([self.issue("See https://huggingface.co/allenai/OLMo-3-7B-Think-SFT"), model]), [])
        self.assertEqual(links_between([self.issue("[OLMo-3-7B-Think-SFT](https://huggingface.co/allenai/OLMo-3-7B-Think-SFT)"), model]), [])

    def test_duplicate_and_orphan_checks(self):
        a = self.issue("issue")
        profile = quality_profile([a, a], [{"source": a["id"], "target": "missing"}])
        self.assertEqual(profile["duplicate_node_ids"], 1)
        self.assertEqual(profile["edges_with_missing_endpoints"], 1)

    def test_normalizer(self):
        self.assertEqual(normalized("Prelude Base/Eval Scores"), "prelude-base-eval-scores")

    def test_report_exposes_failures(self):
        output = report([], [], {"OpenAIRE": "timeout"}, "2026-11-07", None)
        self.assertIn("OpenAIRE", output)
        self.assertIn("unavailable", output)

    def test_essential_source_failures_block_incomplete_ci_snapshot(self):
        errors = {"OpenEuroLLM/Taskboard": "HTTP 504", "OpenAIRE citation coverage": "limited"}
        self.assertEqual(incomplete_essential_sources(errors), ["OpenEuroLLM/Taskboard"])
        self.assertEqual(incomplete_essential_sources({"Hugging Face external lookup": "HTTP 429"}),
                         ["Hugging Face external lookup"])
        self.assertEqual(incomplete_essential_sources({"OpenAIRE citation coverage": "limited"}), [])
        self.assertEqual(incomplete_essential_sources({"GitHub source manifests": "truncated"}),
                         ["GitHub source manifests"])

    def test_extract_source_dataset_urls_only_exact_namespaced_hf_urls(self):
        content = ('data: https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M\n'
                   'repeat: https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M\n'
                   'not_a_dataset: https://huggingface.co/other/model\n'
                   'suffix: https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M-extra\n')
        hits = dataset_urls_in_source(content)
        self.assertEqual([hit["declared_id"] for hit in hits],
                         ["open-thoughts/OpenThoughts3-1.2M", "open-thoughts/OpenThoughts3-1.2M-extra"])
        self.assertEqual(hits[0]["context"], "data: https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M")

    def test_github_manifests_use_pinned_commit_and_link_adjacent_scripts(self):
        repo = "OpenEuroLLM/training-data-collection"
        path = "flag/openthoughts-3/metadata.yaml"
        script = "flag/openthoughts-3/etc/textify.py"
        text = 'source: "https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M"\n'
        payload = base64.b64encode(text.encode()).decode()
        def responder(url, token=None):
            if url == f"https://api.github.com/repos/{repo}":
                return {"default_branch": "main"}
            if url.endswith("/commits/main"):
                return {"sha": "a" * 40, "commit": {"tree": {"sha": "b" * 40}}}
            if "/git/trees/" in url:
                return {"truncated": False, "tree": [
                    {"type": "blob", "path": path, "size": 120, "sha": "c" * 40},
                    {"type": "blob", "path": script, "size": 800, "sha": "d" * 40},
                    {"type": "blob", "path": "flag/empty/metadata.yaml", "size": 20, "sha": "e" * 40},
                ]}
            if path in url:
                self.assertIn(f"ref={'a' * 40}", url)
                return {"encoding": "base64", "content": payload}
            return {"encoding": "base64", "content": base64.b64encode(b'license: none').decode()}
        with patch("research_graph.fetch_json", side_effect=responder):
            nodes, refs, adjacent, stats = github_metadata_inventory(repo, max_files=2)
        self.assertEqual([node["type"] for node in nodes], ["source_file", "processing_script"])
        self.assertEqual(refs[0]["declared_id"], "open-thoughts/OpenThoughts3-1.2M")
        self.assertEqual(adjacent[0]["relationship"], "located_in_dataset_directory")
        self.assertEqual(stats["manifests_with_dataset_url"], 1)
        self.assertIn("/blob/" + "a" * 40, nodes[0]["url"])

    def test_github_manifest_tree_truncation_is_not_silent(self):
        def responder(url, token=None):
            if url.endswith("training-data-collection"):
                return {"default_branch": "main"}
            if "/commits/" in url:
                return {"sha": "a", "commit": {"tree": {"sha": "b"}}}
            return {"truncated": True, "tree": []}
        with patch("research_graph.fetch_json", side_effect=responder):
            with self.assertRaisesRegex(ValueError, "truncated"):
                github_metadata_inventory("OpenEuroLLM/training-data-collection")

    def test_verified_github_source_declaration_is_not_training_proof(self):
        source_id = "github_file:OpenEuroLLM/training-data-collection/flag/openthoughts-3/metadata.yaml"
        ref = {"source": source_id, "declared_id": "open-thoughts/OpenThoughts3-1.2M",
               "evidence": "https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M",
               "context": "source: https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M"}
        verified = {"id": "hf:dataset:open-thoughts/OpenThoughts3-1.2M", "type": "dataset",
                    "title": "open-thoughts/OpenThoughts3-1.2M", "url": ref["evidence"], "is_external": True}
        with patch("research_graph.external_hf_asset", return_value=verified):
            additions, checks, edges = resolve_github_dataset_declarations([], [ref])
        self.assertEqual(additions, [verified])
        self.assertEqual(checks[0]["status"], "verified_public")
        self.assertEqual(edges[0]["status"], "declared_source_file")
        self.assertEqual(edges[0]["relationship"], "declares_dataset")
        self.assertEqual(quality_profile([{"id": source_id, "type": "source_file"}, verified], edges)["edges_with_missing_endpoints"], 0)
        text = report([{"id": source_id, "type": "source_file", "title": "metadata.yaml", "url": "https://github.com/example"}, verified],
                      edges, {}, "2026-11-08", 0)
        self.assertIn("GitHub YAML manifest declarations to indexed/verified datasets: **1**", text)
        self.assertIn("not** proof of actual training", text)

    def test_unverified_github_source_url_is_recorded_but_not_linked(self):
        ref = {"source": "github_file:repo/config.yaml", "declared_id": "outside/missing",
               "evidence": "https://huggingface.co/datasets/outside/missing", "context": "dataset: outside/missing"}
        with patch("research_graph.external_hf_asset", side_effect=urllib.error.HTTPError(
                ref["evidence"], 404, "not found", None, None)):
            added, checks, edges = resolve_github_dataset_declarations([], [ref])
        self.assertEqual(added, [])
        self.assertEqual(edges, [])
        self.assertEqual(checks[0]["status"], "not_publicly_found")

    def test_real_run_link_is_deduplicated_and_not_claimed_as_verified(self):
        link = "https://wandb.ai/openeurollm-project/oellm_32b_dense/runs/tjeg54n7"
        issue = self.issue(f"Loss increased. [Run]({link}), repeated: {link}.")
        run_nodes, edges = linked_experiment_runs([issue])
        self.assertEqual(len(run_nodes), 1)
        self.assertEqual(len(edges), 1)
        self.assertEqual(run_nodes[0]["verification"], "source_link_only")
        self.assertEqual(edges[0]["evidence"], link)
        self.assertEqual(edges[0]["relationship"], "links_experiment_run")
        self.assertEqual(quality_profile([issue, *run_nodes], edges)["edges_with_missing_endpoints"], 0)
        summary = report([issue, *run_nodes], edges, {}, "2026-11-08", 0)
        self.assertIn("Concrete W&B run URLs in GitHub tasks (source links only): **1**", summary)
        self.assertIn("source_link_only", summary)

    def test_project_dashboard_does_not_become_experiment_run(self):
        issue = self.issue("Project https://wandb.ai/openeurollm-project/baby_9b_dense")
        self.assertEqual(linked_experiment_runs([issue]), ([], []))
        issue = self.issue("Placeholder https://wandb.ai/openeurollm-project/foo/runs/... instead of a run")
        self.assertEqual(linked_experiment_runs([issue]), ([], []))

    def test_multiple_issues_can_reference_same_run_with_distinct_edges(self):
        url = "https://wandb.ai/openeurollm-project/oellm_32b_dense/runs/tjeg54n7"
        a, b = self.issue(url), self.issue(url)
        b["id"] = "github:OpenEuroLLM/Taskboard#381"
        nodes, edges = linked_experiment_runs([a, b])
        self.assertEqual(len(nodes), 1)
        self.assertEqual(len(edges), 2)

    def test_github_dataset_lookup_cap_records_skipped_references(self):
        refs = [{"source": f"github_file:config{i}.yaml", "declared_id": f"outside/dataset{i}",
                 "evidence": f"https://huggingface.co/datasets/outside/dataset{i}", "context": "declared"}
                for i in range(3)]
        def verify(kind, repo_id):
            return {"id": f"hf:{kind}:{repo_id}", "type": kind, "title": repo_id}
        with patch("research_graph.external_hf_asset", side_effect=verify) as mocked:
            nodes, checks, edges = resolve_github_dataset_declarations([], refs, limit=1)
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(len(edges), 1)
        self.assertEqual([check["status"] for check in checks],
                         ["verified_public", "not_checked_limit", "not_checked_limit"])

    def test_scholarly_ids_are_explicit_and_version_normalized(self):
        text = 'See https://arxiv.org/pdf/2609.24797v2 and arxiv:2609.24797; https://doi.org/10.48550/arXiv.2609.24797.'
        self.assertEqual(identifiers_in(text), {
            "arxiv": ["2609.24797"], "doi": ["10.48550/arxiv.2609.24797"],
        })
        self.assertEqual(identifiers_in("version 2609.24797 and model 1.3B"), {"arxiv": [], "doi": []})

    def test_arxiv_pdf_and_mirror_doi_only(self):
        self.assertEqual(identifiers_in("https://arxiv.org/pdf/2510.26202v3.pdf")["arxiv"], ["2510.26202"])
        self.assertEqual(identifiers_in("doi:10.48550/arXiv.2609.24797")["arxiv"], ["2609.24797"])
        self.assertEqual(identifiers_in("arxiv:2609.24797wrong")["arxiv"], [])

    def test_openaire_pid_is_extracted_with_http_url(self):
        paper = openaire_node({
            "id": "doi_dedup___::abc", "mainTitle": "Complex KDA", "type": "publication",
            "pids": [{"scheme": "doi", "value": "10.48550/arXiv.2609.24797"}],
            "instances": [{"urls": ["https://arxiv.org/abs/2609.24797"]}],
        })
        self.assertEqual(paper["url"], "https://arxiv.org/abs/2609.24797")
        self.assertEqual(paper["identifiers"]["arxiv"], ["2609.24797"])

    def test_five_models_link_to_same_publication_by_arxiv(self):
        paper = openaire_node({
            "id": "complex-kda", "mainTitle": "Complex KDA",
            "pids": [{"scheme": "arXiv", "value": "2609.24797"}],
        })
        assets = [{
            "id": f"hf:model:openeurollm/complex-kda-{i}", "type": "model",
            "title": f"openeurollm/complex-kda-{i}",
            "url": f"https://huggingface.co/openeurollm/complex-kda-{i}",
            "description": '{"tags": ["arxiv:2609.24797"]}',
        } for i in range(5)]
        edges = scholarly_links([paper, *assets])
        self.assertEqual(len(edges), 5)
        self.assertTrue(all(edge["status"] == "identifier_match" for edge in edges))
        self.assertTrue(all(edge["target"] == paper["id"] for edge in edges))
        self.assertEqual(quality_profile([paper, *assets], edges)["duplicate_edge_pairs"], 0)

    def test_no_spurious_scholarly_matches(self):
        paper = openaire_node({"id": "p1", "pids": [{"scheme": "arXiv", "value": "2609.24797"}]})
        issue = self.issue("An unrelated model named complex-kda")
        self.assertEqual(scholarly_links([paper, issue]), [])

    def test_bounded_openaire_enrichment_reports_missing_coverage(self):
        issues = []
        for i in range(3):
            node = self.issue(f"see https://arxiv.org/abs/2501.0000{i}")
            node["id"] += f"-{i}"
            node["identifiers"] = identifiers_in(node["description"])
            node["state"] = "open"
            issues.append(node)
        errors = {}
        with patch("research_graph.openaire_by_arxiv_batch", return_value=[openaire_node({"id": "pub"})]) as mocked:
            products = enrich_publications(issues, errors, limit=2)
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(len(mocked.call_args.args[0]), 2)
        self.assertEqual(len(products), 1)
        self.assertIn("Queried 2 of 3", errors["OpenAIRE citation coverage"])

    def test_arxiv_batch_uses_documented_or_filter(self):
        with patch("research_graph.fetch_json", return_value={"results": []}) as mocked:
            self.assertEqual(openaire_by_arxiv_batch(["2609.24797", "2510.26202"]), [])
        requested = mocked.call_args.args[0]
        self.assertIn("ids.arxiv%3A2609.24797%7C2510.26202", requested)
        self.assertIn("page_size=100", requested)

    def test_enrichment_includes_hugging_face_citations(self):
        asset = dict(self.asset, identifiers={"arxiv": ["2609.24797"], "doi": []})
        errors = {}
        with patch("research_graph.openaire_by_arxiv_batch", return_value=[]) as mocked:
            enrich_publications([asset], errors)
        self.assertEqual(mocked.call_args.args[0], ["2609.24797"])
        self.assertEqual(errors, {})

    def test_citation_coverage_reveals_three_platform_bridges(self):
        paper = openaire_node({"id": "paper", "mainTitle": "Paper", "pids": [{"scheme": "arXiv", "value": "2609.24797"}]})
        issue = self.issue("See arxiv:2609.24797")
        issue["identifiers"] = identifiers_in(issue["description"])
        asset = dict(self.asset, identifiers={"arxiv": ["2609.24797", "2510.26202"], "doi": []})
        nodes = [paper, issue, asset]
        coverage = citation_coverage(nodes, scholarly_links(nodes))
        self.assertEqual(coverage["referenced_unique_arxiv_ids"], 2)
        self.assertEqual(coverage["resolved_unique_arxiv_ids"], 1)
        self.assertEqual(coverage["unresolved_arxiv_ids"], ["2510.26202"])
        self.assertEqual(coverage["publications_bridging_github_and_hf"], 1)
        self.assertEqual(coverage["by_source_type"]["issue"]["linked_to_openaire"], 1)
        summary = report(nodes, scholarly_links(nodes), {}, "2026-11-07", 1)
        self.assertIn("Three-platform publication bridges", summary)
        self.assertIn("not** proof of direct model/task dependence", summary)

    def test_model_card_declares_exact_base_model_and_dataset(self):
        model = {"id": "hf:model:openeurollm/child", "type": "model", "title": "openeurollm/child",
                 "url": "https://huggingface.co/openeurollm/child",
                 "description": json.dumps({"base_model": ["openeurollm/base", "allenai/base"],
                                            "datasets": ["openeurollm/train", "other/train"]})}
        base = {"id": "hf:model:openeurollm/base", "type": "model", "title": "openeurollm/base",
                "url": "https://huggingface.co/openeurollm/base"}
        dataset = {"id": "hf:dataset:openeurollm/train", "type": "dataset", "title": "openeurollm/train",
                   "url": "https://huggingface.co/datasets/openeurollm/train"}
        edges, outside = hf_card_declarations([model, base, dataset])
        self.assertEqual(len(edges), 2)
        self.assertEqual({edge["evidence_type"] for edge in edges}, {"base_model", "datasets"})
        self.assertEqual({edge["target"] for edge in edges}, {base["id"], dataset["id"]})
        self.assertTrue(all(edge["status"] == "declared_metadata" for edge in edges))
        self.assertEqual({item["declared_id"] for item in outside}, {"allenai/base", "other/train"})
        self.assertTrue(all(item["verification"] == "not_fetched_outside_indexed_inventory" for item in outside))

    def test_card_does_not_create_fake_prefix_or_self_links(self):
        model = {"id": "hf:model:openeurollm/base", "type": "model", "title": "openeurollm/base",
                 "url": "https://huggingface.co/openeurollm/base",
                 "description": json.dumps({"base_model": ["openeurollm/base", "openeurollm/base-v2", "openeurollm/base-v2"]})}
        self.assertEqual(hf_card_declarations([model])[0], [])
        self.assertEqual(len(hf_card_declarations([model])[1]), 1)

    def test_report_separates_card_declarations_from_scholarly_links(self):
        child = {"id": "hf:model:openeurollm/child", "type": "model", "title": "openeurollm/child",
                 "url": "https://huggingface.co/openeurollm/child",
                 "description": json.dumps({"base_model": "openeurollm/base"})}
        parent = {"id": "hf:model:openeurollm/base", "type": "model", "title": "openeurollm/base",
                  "url": "https://huggingface.co/openeurollm/base"}
        edges, _ = hf_card_declarations([child, parent])
        summary = report([child, parent], edges, {}, "2026-11-08", 0)
        self.assertIn("HF model-card declarations to indexed/verified targets: **1**", summary)
        self.assertIn("Shared scholarly identifiers (arXiv/DOI): **0**", summary)

    def test_external_asset_must_be_confirmed_by_public_hf_api(self):
        payload = {"id": "allenai/Model-X", "private": False,
                   "cardData": {"tags": ["arxiv:2609.24797"]},
                   "lastModified": "2026-11-08T00:00:00Z"}
        with patch("research_graph.fetch_json", return_value=payload) as fetched:
            node = external_hf_asset("model", "allenai/Model-X")
        self.assertIn("/api/models/allenai/Model-X", fetched.call_args.args[0])
        self.assertEqual(node["id"], "hf:model:allenai/Model-X")
        self.assertTrue(node["is_external"])
        self.assertEqual(node["identifiers"]["arxiv"], ["2609.24797"])
        with patch("research_graph.fetch_json", return_value={"id": "other/Model-X"}):
            renamed = external_hf_asset("model", "allenai/Model-X")
        self.assertEqual(renamed["id"], "hf:model:other/Model-X")
        self.assertEqual(renamed["resolved_from_alias"], "allenai/Model-X")

    def test_external_resolution_deduplicates_targets_and_handles_404(self):
        refs = [{"target_type": "dataset", "declared_id": "outside/datasetA"}] * 3 + [
            {"target_type": "dataset", "declared_id": "outside/datasetB"}]
        def fake_lookup(kind, repo_id):
            if repo_id.endswith("datasetB"):
                raise urllib.error.HTTPError("https://huggingface.co/", 404, "not found", None, None)
            return {"id": "hf:dataset:outside/datasetA", "type": "dataset", "title": "outside/datasetA"}
        with patch("research_graph.external_hf_asset", side_effect=fake_lookup) as mocked:
            found, checked = verify_external_hf_references(refs)
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(len(found), 1)
        self.assertEqual([x["status"] for x in checked], ["verified_public", "not_publicly_found"])

    def test_external_model_is_one_hop_only_and_no_name_guesses(self):
        original = {"id": "hf:model:openeurollm/child", "type": "model", "title": "openeurollm/child",
                    "url": "https://huggingface.co/openeurollm/child",
                    "description": json.dumps({"base_model": "allenai/Model-X"})}
        outside = {"id": "hf:model:allenai/Model-X", "type": "model", "title": "allenai/Model-X",
                   "url": "https://huggingface.co/allenai/Model-X", "is_external": True,
                   "description": json.dumps({"base_model": "other/grandparent"})}
        edges, missing = hf_card_declarations([original, outside])
        self.assertEqual(len(edges), 1)
        self.assertEqual(missing, [])
        self.assertEqual(links_between([self.issue("Testing Model-X"), outside]), [])

    def test_verified_canonical_redirect_creates_evidenced_card_link(self):
        child = {"id": "hf:model:openeurollm/child", "type": "model", "title": "openeurollm/child",
                 "url": "https://huggingface.co/openeurollm/child",
                 "description": json.dumps({"base_model": "openeurollm/prelude"})}
        canonical = {"id": "hf:model:openeurollm/prelude-base", "type": "model",
                     "title": "openeurollm/prelude-base", "url": "https://huggingface.co/openeurollm/prelude-base"}
        aliases = {("model", "openeurollm/prelude"): "openeurollm/prelude-base"}
        edges, unresolved = hf_card_declarations([child, canonical], aliases=aliases)
        self.assertEqual(unresolved, [])
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["status"], "declared_metadata_redirect")
        self.assertEqual(edges[0]["evidence"], "openeurollm/prelude")
        self.assertEqual(edges[0]["canonical_id"], "openeurollm/prelude-base")
        check = [{"target_type": "model", "declared_id": "openeurollm/prelude",
                  "status": "verified_redirect", "canonical_id": "openeurollm/prelude-base"}]
        summary = report([child, canonical], edges, {}, "2026-11-08", 0, check)
        self.assertIn("verified HF canonical IDs: **1**", summary)
        self.assertIn("still unresolved in this graph: **0**", summary)

    def test_redirect_and_unauthorized_external_targets_have_distinct_status(self):
        refs = [{"target_type": "model", "declared_id": "old/model"},
                {"target_type": "model", "declared_id": "private/model"}]
        def fake_lookup(kind, repo_id):
            if repo_id == "private/model":
                raise urllib.error.HTTPError("https://huggingface.co/", 401, "unauthorized", None, None)
            return {"id": "hf:model:new/model", "type": "model", "title": "new/model",
                    "resolved_from_alias": "old/model"}
        with patch("research_graph.external_hf_asset", side_effect=fake_lookup):
            found, checks = verify_external_hf_references(refs)
        self.assertEqual(len(found), 1)
        self.assertEqual({check["status"] for check in checks}, {"verified_redirect", "inaccessible"})
        self.assertEqual(next(check["canonical_id"] for check in checks if check["status"] == "verified_redirect"), "new/model")

    def test_report_separates_scholarly_edges(self):
        paper = openaire_node({"id": "abc", "mainTitle": "Paper", "pids": [{"scheme": "arXiv", "value": "2609.24797"}]})
        issue = self.issue("see arxiv:2609.24797")
        edges = scholarly_links([paper, issue])
        text = report([paper, issue], edges, {}, "2026-11-07", 1)
        self.assertIn("Shared scholarly identifiers (arXiv/DOI): **1**", text)
        self.assertIn("2609.24797", text)


if __name__ == "__main__":
    unittest.main()
