"""Offline unit tests for public cross-project evidence and cautious classification."""

import base64
import json
import tempfile
import unittest
from pathlib import Path

import cross_project_audit as cp


class FakeGitHub:
    TEXT = {
        "OpenEuroLLM/oellm-eval": "CLI for model evaluation and benchmark scheduling.\n",
        "utter-project/eurollm-evaluation": "Evaluation scripts for multilingual model benchmark.\n",
        "OpenEuroLLM/web-data-processing": "Pipeline for metadata extraction from web archives (WARC).\n",
        "hplt-project/HPLT-textpipes": "HPLT WARC metadata extraction for multilingual dataset building.\n",
        "hplt-project/warc2text-runner": "Process WARC archives with distributed extraction jobs.\n",
        "OpenEuroLLM/dense_english_scaling_laws": "Training model hyperparameters and scaling laws.\n",
        "LAION-AI/open-sci-ref-0.01": "Reference models for training dynamics, scaling and dataset research.\n",
        "LAION-AI/CLIP_benchmark": "Evaluation benchmark of vision-language CLIP models.\n",
        "OpenEuroLLM/training-data-catalogue": "Dataset metadata and training-data catalogue.\n",
    }

    def __init__(self, *, include_direct_link=False, drift=False):
        self.calls = []
        self.reads = {}
        self.include_direct_link = include_direct_link
        self.drift = drift

    def __call__(self, url):
        self.calls.append(url)
        prefix = f"{cp.API}/"
        assert url.startswith(prefix), url
        rest = url[len(prefix):]
        name = rest.removesuffix("/readme")
        assert name in self.TEXT
        if url.endswith("/readme"):
            self.reads[name] = self.reads.get(name, 0) + 1
            content = self.TEXT[name]
            if self.include_direct_link and name == "OpenEuroLLM/oellm-eval":
                content += "Uses https://github.com/utter-project/eurollm-evaluation\n"
            if self.drift and self.reads[name] == 2:
                content += "Changed before verification\n"
            return {
                "encoding": "base64",
                "content": base64.b64encode(content.encode()).decode(),
                "html_url": f"https://github.com/{name}/blob/main/README.md",
                "sha": cp.sha256(content),
            }
        return {
            "full_name": name, "html_url": f"https://github.com/{name}",
            "archived": False, "fork": False, "parent": None,
            "pushed_at": "2026-11-09T00:00:00Z",
            "description": "",
        }


class CrossProjectTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(Path("cross_project_sources.json").read_text())

    def test_registry_scopes_multiple_european_organizations(self):
        cp.validate_registry(self.registry)
        orgs = {x.split("/")[0] for x in self.registry["repositories"]}
        self.assertEqual(orgs, {"OpenEuroLLM", "LAION-AI", "hplt-project", "utter-project"})
        self.assertEqual(len(self.registry["pairs"]), 6)

    def test_sources_are_reread_and_duplicates_never_claimed(self):
        fake = FakeGitHub()
        result = cp.build(self.registry, fake)
        self.assertEqual(result["status"], "read_only_human_review")
        self.assertEqual(result["repositories_checked"], 9)
        self.assertEqual(result["pairs_checked"], 6)
        self.assertTrue(all(fake.reads[r] == 2 for r in self.registry["repositories"]))
        self.assertTrue(all(p["duplicate_work"] == "not_established"
                            and p["outreach"] == "none" for p in result["comparisons"]))
        self.assertTrue(any(p["shared_terms"] for p in result["comparisons"]))
        self.assertIn("NOT established", cp.markdown(result))

    def test_literal_cross_repository_link_is_not_misclassified_as_collaboration(self):
        result = cp.build(self.registry, FakeGitHub(include_direct_link=True))
        eval_pair = next(p for p in result["comparisons"] if p["id"] == "evaluation-eurollm")
        self.assertEqual(eval_pair["classification"], "explicit_repository_reference")
        self.assertEqual(len(eval_pair["direct_references"]), 1)
        self.assertEqual(eval_pair["duplicate_work"], "not_established")

    def test_readme_changed_while_reading_refuses_to_report(self):
        with self.assertRaisesRegex(ValueError, "README drift"):
            cp.build(self.registry, FakeGitHub(drift=True))

    def test_cross_org_and_repo_registry_are_validated(self):
        modified = json.loads(json.dumps(self.registry))
        modified["pairs"][0]["b"] = "OpenEuroLLM/web-data-processing"
        with self.assertRaises(ValueError):
            cp.validate_registry(modified)

    def test_report_writes_only_after_success(self):
        fake = FakeGitHub()
        out = cp.build(self.registry, fake)
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "CROSS_PROJECT.md"
            p.write_text(cp.markdown(out))
            self.assertTrue(p.read_text().startswith("# European AI cross-project overlap"))
            self.assertNotIn("confirmed duplicated work", p.read_text().lower())


if __name__ == "__main__":
    unittest.main()
