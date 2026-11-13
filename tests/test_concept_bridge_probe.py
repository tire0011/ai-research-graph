"""Offline controls for the exploratory phrase-based recall probe."""

import datetime as dt
import json
import unittest
from pathlib import Path

import concept_bridge_probe as probe
from test_collaboration_matcher import FakeGitHub, issue

NOW = dt.datetime(2026, 11, 10, 12, tzinfo=dt.timezone.utc)


class PhraseBridgeTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(Path("collaboration_sources.json").read_text())
        self.config["min_score"] = 2.0  # small fake corpus has much lower IDF
        self.fake = FakeGitHub(self.config)
        # An IDF gate should be tested with a nontrivial document population,
        # not relaxed to make a tiny hand-picked example pass.
        for n in range(600, 640):
            self.fake.items["hplt-project/monotextor-slurm"].append(issue(
                "hplt-project/monotextor-slurm", n, f"Unrelated historical item {n}",
                "No shared output artifact.", state="closed",
                created="2025-01-01T00:00:00Z"))

    def test_generic_inflection_and_negative_phrases(self):
        self.assertIn("model card", probe.phrases("Automatic model cards"))
        self.assertIn("model card", probe.phrases("A model-card is published"))
        self.assertNotIn("open source", probe.phrases("open source software"))
        self.assertNotIn("for model", probe.phrases("reports for models"))

    def test_cross_org_phrase_bridge_without_handpicked_pair_rules(self):
        source = "OpenEuroLLM/Taskboard"
        target = "LAION-AI/CLIP_benchmark"
        self.fake.items[source].append(issue(
            source, 445, "Automatic evaluation reporting for model card",
            "A script generates model card tables from evaluations.",
            created="2026-11-06T09:11:53Z"))
        self.fake.items[target].append(issue(
            target, 153, "Optional audit manifest for benchmark result provenance",
            "A result manifest can support model cards with provenance metadata.",
            created="2026-05-10T22:19:24Z"))
        result = probe.build(self.config, fetch=self.fake, now=NOW)
        pair = next(c for c in result["suggestions"]
                    if c["source_id"].endswith("Taskboard#445")
                    and c["target_id"].endswith("CLIP_benchmark#153"))
        self.assertEqual(pair["phrase"], "model card")
        self.assertEqual(pair["source_evidence"]["field"], "title")
        self.assertEqual(pair["target_evidence"]["field"], "body")
        self.assertEqual(pair["status"], "unreviewed_phrase_overlap")
        self.assertEqual(pair["coordination"], "unknown")
        self.assertEqual(pair["outreach"], "none")
        self.assertGreater(result["original_sources_rechecked"], 0)

    def test_shared_generic_model_word_does_not_create_pair(self):
        source = "OpenEuroLLM/Taskboard"
        target = "LAION-AI/CLIP_benchmark"
        self.fake.items[source].append(issue(
            source, 500, "Train model on datasets",
            "Model training data work with new metrics."))
        self.fake.items[target].append(issue(
            target, 155, "Update model architecture",
            "Training a model with new metrics.", created="2025-07-01T00:00:00Z"))
        result = probe.build(self.config, fetch=self.fake, now=NOW)
        self.assertFalse(any(c["source_id"].endswith("Taskboard#500")
                             and c["target_id"].endswith("CLIP_benchmark#155")
                             for c in result["suggestions"]))

    def test_explicit_limitations_and_no_outreach(self):
        result = probe.build(self.config, fetch=self.fake, now=NOW)
        md = probe.markdown(result)
        self.assertIn("Not a measured discovery success", md)
        self.assertIn("no holdout accuracy", result["limitations"])
        self.assertEqual(result["outreach"], "none")


if __name__ == "__main__":
    unittest.main()
