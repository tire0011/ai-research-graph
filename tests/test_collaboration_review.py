"""Offline contract tests for human/local-model collaboration assessments."""

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import collaboration_matcher as cm
import collaboration_review as review
from test_collaboration_matcher import FakeGitHub, issue


def item(repo, number, title, body, created="2026-05-10T22:19:24Z"):
    return cm.normalize_issue(repo, issue(repo, number, title, body, created=created))


class ReviewTests(unittest.TestCase):
    def setUp(self):
        from pathlib import Path
        import json
        cfg = json.loads(Path("collaboration_sources.json").read_text())
        self.fake = FakeGitHub(cfg)
        self.source = item("OpenEuroLLM/Taskboard", 445,
                           "Automatic evaluation reporting for model card",
                           "Generate model-card plots and tables from HF evaluations.",
                           "2026-11-06T09:11:53Z")
        self.target = item("LAION-AI/CLIP_benchmark", 153,
                           "Optional audit manifest for result provenance",
                           "The proposal offers a per-run audit manifest for model cards.")
        self.fake.items[self.source["repo"]].append(issue(
            self.source["repo"], 445, self.source["title"], self.source["body"],
            created=self.source["created_at"]))
        self.fake.items[self.target["repo"]].append(issue(
            self.target["repo"], 153, self.target["title"], self.target["body"],
            created=self.target["created_at"]))
        card = {"id": "pair:445-153", "source": cm.report_issue(self.source),
                "target": cm.report_issue(self.target), "source_id": self.source["id"],
                "target_id": self.target["id"]}
        self.packet = review.prepare(card, fetch=self.fake)

    def evidence(self, party, quote):
        return {"party": party, "field": "body", "quote": quote,
                "source_url": self.packet["records"][party]["url"]}

    def test_complementary_proposal_is_not_a_confirmed_collaboration(self):
        proposal = {
            "relation": "complementary", "readiness": "proposal_only",
            "handoff": {"from": "target", "to": "source",
                        "artifact": "Optional evaluation provenance manifest"},
            "evidence": [
                self.evidence("source", "Generate model-card plots and tables"),
                self.evidence("target", "per-run audit manifest for model cards"),
            ],
            "verification_question": "Would the optional provenance sidecar help the model-card workflow?",
        }
        result = review.validate(self.packet, proposal)
        self.assertEqual(result["proposed_next_check"], "ask_maintainers_if_useful")
        self.assertFalse(result["outreach_approved"])
        self.assertFalse(result["novel_collaboration_confirmed"])
        self.assertEqual(result["readiness_claim"], "proposal_only")
        self.assertFalse(result["readiness_independently_verified"])

    def test_topic_similarity_only_cannot_invent_a_handoff(self):
        proposal = {
            "relation": "topic_only", "readiness": "unknown", "handoff": None,
            "evidence": [self.evidence("source", "Generate model-card plots"),
                         self.evidence("target", "audit manifest for model cards")],
            "verification_question": "Do these separate tasks share an implementable artifact?",
        }
        self.assertEqual(review.validate(self.packet, proposal)["proposed_next_check"],
                         "do_not_contact")
        proposal["handoff"] = {"from": "source", "to": "target", "artifact": "A made-up dependency"}
        with self.assertRaisesRegex(ValueError, "cannot claim a handoff"):
            review.validate(self.packet, proposal)

    def test_unverifiable_source_quotation_is_rejected(self):
        proposal = {
            "relation": "complementary", "readiness": "implemented",
            "handoff": {"from": "target", "to": "source", "artifact": "A reusable adapter"},
            "evidence": [self.evidence("source", "This code is production ready"),
                         self.evidence("target", "per-run audit manifest for model cards")],
            "verification_question": "Is there a tested adapter that can be reused here?",
        }
        with self.assertRaisesRegex(ValueError, "not found"):
            review.validate(self.packet, proposal)

    def test_third_party_needs_third_owner_and_evidence(self):
        third = item("hplt-project/HPLT-textpipes", 91, "Provenance writer",
                     "A reusable provenance writer with test coverage.")
        self.fake.items[third["repo"]].append(issue(
            third["repo"], 91, third["title"], third["body"], created=third["created_at"]))
        card = {"id": "pair:445-153", "source": cm.report_issue(self.source),
                "target": cm.report_issue(self.target), "source_id": self.source["id"],
                "target_id": self.target["id"]}
        packet = review.prepare(card, fetch=self.fake, third_item=cm.report_issue(third))
        proposal = {
            "relation": "third_party_enabler", "readiness": "reported",
            "handoff": {"from": "third", "to": "source", "artifact": "Provenance writer"},
            "evidence": [
                self.evidence("source", "Generate model-card plots"),
                self.evidence("target", "per-run audit manifest for model cards"),
                {"party": "third", "field": "body", "quote": "reusable provenance writer",
                 "source_url": packet["records"]["third"]["url"]},
            ],
            "verification_question": "Does the existing writer support the required output contract?",
        }
        self.assertEqual(review.validate(packet, proposal)["proposed_next_check"],
                         "verify_external_artifact_and_license")
        proposal["evidence"].pop()
        with self.assertRaisesRegex(ValueError, "third-source evidence"):
            review.validate(packet, proposal)

    def test_source_drift_fails_closed(self):
        self.fake.items[self.source["repo"]][-1]["body"] += " changed"
        card = {"id": "pair:445-153", "source": cm.report_issue(self.source),
                "target": cm.report_issue(self.target), "source_id": self.source["id"],
                "target_id": self.target["id"]}
        with self.assertRaisesRegex(ValueError, "Source changed"):
            review.prepare(card, fetch=self.fake)

    def test_cli_prepares_packet_then_checks_local_model_review(self):
        card = {"id": "pair:445-153", "source": cm.report_issue(self.source),
                "target": cm.report_issue(self.target), "source_id": self.source["id"],
                "target_id": self.target["id"]}
        with tempfile.TemporaryDirectory() as folder:
            matches, packet, model, output = [Path(folder) / n for n in
                                               ("matches.json", "packet.json", "review.json", "checked.json")]
            matches.write_text(json.dumps({"suggestions": [card]}), encoding="utf-8")
            with patch.object(review.cm, "get_json", self.fake):
                self.assertEqual(review.main([
                    "--matches", str(matches), "--candidate-id", card["id"],
                    "--output", str(packet)]), 0)
            assert packet.exists()
            assessment = {
                "relation": "complementary", "readiness": "proposal_only",
                "handoff": {"from": "target", "to": "source",
                            "artifact": "Optional model-card provenance manifest"},
                "evidence": [self.evidence("source", "Generate model-card plots and tables"),
                             self.evidence("target", "per-run audit manifest for model cards")],
                "verification_question": "Could the model-card job consume this sidecar manifest?",
            }
            model.write_text(json.dumps(assessment), encoding="utf-8")
            self.assertEqual(review.main([
                "--packet", str(packet), "--review", str(model),
                "--output", str(output)]), 0)
            self.assertFalse(json.loads(output.read_text())["outreach_approved"])

    def test_duplicate_candidate_id_rejected(self):
        card = {"id": "same"}
        with self.assertRaisesRegex(ValueError, "exactly once"):
            review.select_candidate({"suggestions": [card, card]}, "same")

    def test_optional_public_coordination_check_is_not_a_novelty_claim(self):
        card = {"id": "pair:445-153", "source": cm.report_issue(self.source),
                "target": cm.report_issue(self.target), "source_id": self.source["id"],
                "target_id": self.target["id"]}
        packet = review.prepare(card, fetch=self.fake, check_public=True)
        self.assertEqual(packet["public_coordination"]["public_coordination_signal"],
                         "shared_public_participants")
        self.assertFalse(packet["public_coordination"]["new_collaboration_confirmed"])


if __name__ == "__main__":
    unittest.main()
