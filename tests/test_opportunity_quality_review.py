"""Offline tests: manual labels are source-pinned, conservative, and not auto-approval."""

import copy
import json
import unittest
from pathlib import Path

import opportunity_quality_review as q

LEDGER = Path(__file__).resolve().parents[1] / (
    "studies/eu_opportunity_quality_20261121/reviews.json"
)


def fixture():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    cards = [
        {
            "issue_url": row["issue_url"],
            "updated_at": row["source_updated_at"],
            "comment_count": row["source_comment_count"],
            "repository": row["issue_url"].split("/")[3] + "/" + row["issue_url"].split("/")[4],
            "issue_number": int(row["issue_url"].rsplit("/", 1)[-1]),
            "title": f"Historical task {row['issue_url'].rsplit('/', 1)[-1]}",
            "state": {"status": "new"},
        }
        for row in ledger["reviews"]
    ]
    return ledger, {"all_reviewed": cards, "new_top5": ledger["graph_top5"][:]}


class FrozenComparisonTests(unittest.TestCase):
    def test_complete_eight_issue_union(self):
        ledger, _ = fixture()
        q.validate(ledger)
        self.assertEqual(len(ledger["reviews"]), 8)
        self.assertEqual(len(set(ledger["graph_top5"] + ledger["title_baseline_top5"])), 8)

    def test_no_superiority_claim_and_no_confirmed_maintainer_approval(self):
        ledger, _ = fixture()
        result = q.frozen_comparison(ledger)
        self.assertEqual(result["graph_heuristic_top5"]["plausible_or_better"], 0)
        self.assertEqual(result["same_pool_title_only_top5"]["plausible_or_better"], 1)
        self.assertEqual(result["unique_issues_reviewed"], 8)
        self.assertFalse(result["claims_of_graph_superiority_supported"])
        self.assertEqual(result["confirmed_free_contributions"], 0)

    def test_second_review_is_additive_not_part_of_frozen_comparison(self):
        ledger, sample = fixture()
        self.assertEqual(len(q.review_rows(ledger)), 13)
        self.assertEqual(q.frozen_comparison(ledger)["unique_issues_reviewed"], 8)
        new_cards = []
        for row in ledger["additional_cohorts"][0]["reviews"]:
            bits = row["issue_url"].split("/")
            new_cards.append({
                "issue_url": row["issue_url"],
                "updated_at": row["source_updated_at"],
                "comment_count": row["source_comment_count"],
                "repository": "/".join(bits[3:5]),
                "issue_number": int(bits[-1]),
                "title": "Additional reviewed task",
                "state": {"status": "new"},
            })
        sample["all_reviewed"].extend(new_cards)
        result = q.annotate(sample, ledger)
        self.assertEqual(result["additional_review_cohorts"], 1)
        self.assertEqual(len(result["quality_shortlist"]), 1)
        self.assertTrue(any(item["issue_url"].endswith("/JudgeArena/issues/24")
                            for item in result["quality_shortlist"]))
        self.assertEqual(result["comparison"]["unique_issues_reviewed"], 8)

    def test_additional_cohorts_reject_duplicate_issue(self):
        ledger, _ = fixture()
        ledger["additional_cohorts"][0]["reviews"][0]["issue_url"] = (
            ledger["reviews"][0]["issue_url"])
        with self.assertRaises(ValueError):
            q.validate(ledger)

    def test_incomplete_review_or_unlinked_evidence_fails(self):
        ledger, _ = fixture()
        ledger["reviews"].pop()
        with self.assertRaises(ValueError):
            q.validate(ledger)
        ledger, _ = fixture()
        ledger["reviews"][0]["evidence_urls"] = []
        with self.assertRaises(ValueError):
            q.validate(ledger)

    def test_duplicate_source_or_fake_url_fails(self):
        ledger, _ = fixture()
        ledger["graph_top5"][0] = ledger["graph_top5"][1]
        with self.assertRaises(ValueError):
            q.validate(ledger)
        ledger, _ = fixture()
        ledger["reviews"][0]["issue_url"] = "https://example.invalid/1"
        with self.assertRaises(ValueError):
            q.validate(ledger)


class CurrentQueueTests(unittest.TestCase):
    def test_existing_solution_is_not_presented_as_new_coding_work(self):
        ledger, sample = fixture()
        result = q.annotate(sample, ledger)
        rejected = next(c for c in result["annotated_candidates"]
                        if c["issue_url"].endswith("/pocket-tts/issues/345"))
        self.assertEqual(rejected["quality_review"]["tier"], 0)
        self.assertNotIn(rejected["issue_url"],
                         [row["issue_url"] for row in result["quality_shortlist"]])

    def test_plausibly_scoped_task_is_still_not_maintainer_confirmed(self):
        ledger, sample = fixture()
        result = q.annotate(sample, ledger)
        self.assertEqual(result["quality_shortlist"], [])
        reviewed = next(c for c in result["annotated_candidates"]
                        if c["issue_url"].endswith("/OpenEuroLLM/post-training/issues/35"))
        self.assertEqual(reviewed["quality_review"]["status"], "code_revision_unverified")
        self.assertEqual(result["comparison"]["graph_heuristic_top5"]["maintainer_confirmed"], 0)
        self.assertIn("non-blinded", q.markdown(result))

    def test_changed_source_invalidates_manual_review_without_overwrite(self):
        ledger, sample = fixture()
        target = next(c for c in sample["all_reviewed"]
                      if c["issue_url"].endswith("/OpenEuroLLM/post-training/issues/35"))
        target["updated_at"] = "2026-11-22T00:00:00Z"
        result = q.annotate(sample, ledger)
        self.assertEqual(result["quality_shortlist"], [])
        reviewed = next(c for c in result["annotated_candidates"]
                        if c["issue_url"] == target["issue_url"])
        self.assertEqual(reviewed["quality_review"]["status"], "stale_review")
        self.assertEqual(len(sample["all_reviewed"]), 8)
        self.assertNotIn("quality_review", target)

    def test_added_comment_invalidates_review_even_if_update_timestamp_unchanged(self):
        ledger, sample = fixture()
        target = next(c for c in sample["all_reviewed"]
                      if c["issue_url"].endswith("/OpenEuroLLM/post-training/issues/35"))
        target["comment_count"] += 1
        result = q.annotate(sample, ledger)
        self.assertEqual(result["quality_shortlist"], [])
        reviewed = next(c for c in result["annotated_candidates"]
                        if c["issue_url"] == target["issue_url"])
        self.assertEqual(reviewed["quality_review"]["status"], "stale_review")

    def test_live_followup_status_supersedes_manual_positive(self):
        ledger, sample = fixture()
        target = next(c for c in sample["all_reviewed"]
                      if c["issue_url"].endswith("/OpenEuroLLM/post-training/issues/35"))
        target["state"]["status"] = "follow_up"
        result = q.annotate(sample, ledger)
        self.assertEqual(result["quality_shortlist"], [])
        reviewed = next(c for c in result["annotated_candidates"]
                        if c["issue_url"] == target["issue_url"])
        self.assertEqual(reviewed["quality_review"]["status"], "state_supersedes_review")

    def test_pinned_code_head_supersedes_original_frozen_rating(self):
        ledger, sample = fixture()
        pin = ledger["code_rechecks"][0]
        result = q.annotate(sample, ledger,
                            code_heads={pin["code_repo"]: pin["code_head_sha"]})
        entry = next(c for c in result["annotated_candidates"]
                     if c["issue_url"] == pin["issue_url"])
        self.assertEqual(entry["quality_review"]["status"], "manual_code_review_current")
        self.assertEqual(entry["quality_review"]["tier"], 1)
        self.assertEqual(result["quality_shortlist"], [])
        # Original non-blinded comparison remains historical, not overwritten.
        self.assertEqual(result["comparison"]["same_pool_title_only_top5"]
                         ["plausible_or_better"], 1)

    def test_changed_code_head_blocks_old_manual_recommendation(self):
        ledger, sample = fixture()
        pin = ledger["code_rechecks"][0]
        result = q.annotate(sample, ledger, code_heads={pin["code_repo"]: "0" * 40})
        entry = next(c for c in result["annotated_candidates"]
                     if c["issue_url"] == pin["issue_url"])
        self.assertEqual(entry["quality_review"]["status"], "code_revision_unverified")
        self.assertIn(entry, result["new_needing_human_review"])

    def test_live_code_head_fetch_can_fail_without_claiming_readiness(self):
        ledger, sample = fixture()
        pin = ledger["code_rechecks"][0]
        def good(url):
            self.assertIn(pin["code_repo"], url)
            return [{"sha": pin["code_head_sha"]}]
        self.assertEqual(q.fetch_code_heads(ledger, good),
                         {pin["code_repo"]: pin["code_head_sha"]})
        def failing(_):
            raise OSError("temporary network error")
        self.assertEqual(q.fetch_code_heads(ledger, failing), {})

    def test_code_recheck_requires_pinned_repository_commit(self):
        ledger, _ = fixture()
        ledger["code_rechecks"][0]["code_head_sha"] = "not-a-real-sha"
        with self.assertRaises(ValueError):
            q.validate(ledger)

    def test_unreviewed_issue_is_not_implicitly_approved(self):
        ledger, sample = fixture()
        sample["all_reviewed"].append({
            "issue_url": "https://github.com/kyutai-labs/hibiki/issues/99",
            "updated_at": "2026-11-21T00:00:00Z", "repository": "kyutai-labs/hibiki",
            "issue_number": 99, "title": "Unknown", "state": {"status": "new"},
        })
        result = q.annotate(sample, ledger)
        self.assertTrue(any(card["issue_url"].endswith("/hibiki/issues/99") and
                            card["quality_review"]["status"] == "unreviewed"
                            for card in result["new_needing_human_review"]))
        self.assertNotIn("hibiki", [row["repository"] for row in result["quality_shortlist"]])


if __name__ == "__main__":
    unittest.main()
