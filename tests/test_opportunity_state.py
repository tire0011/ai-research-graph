"""Offline regression cases grounded in five known public GitHub issues.

Issue numbers and states were checked on 2026-11-21. Fixtures are frozen
examples, not promises that live task status remains unchanged.
"""

import unittest

from opportunity_state import classify, related_pull_requests

ACTOR = "tire0011"


def issue(repo, number, *, state="open", creator="someone", assignees=()):
    return {
        "html_url": f"https://github.com/{repo}/issues/{number}",
        "state": state,
        "user": {"login": creator},
        "assignees": [{"login": login} for login in assignees],
    }


def status(record, comments=(), prs=(), **kwargs):
    return classify(record, list(comments), list(prs), actor=ACTOR, **kwargs)


class HistoricalIssueRegressionTests(unittest.TestCase):
    def test_441_our_existing_comment_is_a_followup(self):
        # https://github.com/OpenEuroLLM/Taskboard/issues/441
        task = issue("OpenEuroLLM/Taskboard", 441, creator="dianaonutu",
                     assignees=("dianaonutu", "sam-laing"))
        comment = {"user": {"login": ACTOR}, "html_url":
                   "https://github.com/OpenEuroLLM/Taskboard/issues/441#issuecomment-6988821622"}
        observed = status(task, [comment])
        self.assertEqual(observed["status"], "follow_up")
        self.assertEqual(observed["reason"], "actor_commented")
        self.assertIn("6988821622", observed["evidence_urls"][0])

    def test_163_our_own_issue_is_not_new(self):
        # https://github.com/OpenEuroLLM/oellm-eval/issues/163
        observed = status(issue("OpenEuroLLM/oellm-eval", 163, creator=ACTOR))
        self.assertEqual(observed["status"], "follow_up")
        self.assertEqual(observed["reason"], "actor_created_issue")

    def test_warc_audio_8_assigned_work_is_not_claimed_free(self):
        # https://github.com/OpenEuroLLM/web-data-processing/issues/8
        task = issue("OpenEuroLLM/web-data-processing", 8, creator="nvanva",
                     assignees=("nvanva", "akutuzov", "MariaFjodorowa"))
        observed = status(task)
        self.assertEqual(observed["status"], "in_progress")
        self.assertIn("unconfirmed", observed["reason"])

    def test_evalchemy_165_is_a_new_candidate_not_a_verified_slot(self):
        # https://github.com/OpenEuroLLM/oellm-eval/issues/165
        observed = status(issue("OpenEuroLLM/oellm-eval", 165, creator="HannanJaved"))
        self.assertEqual(observed["status"], "new")
        self.assertIn("no_observed", observed["reason"])

    def test_flores_169_closed_is_not_recommended(self):
        # https://github.com/OpenEuroLLM/oellm-eval/issues/169
        observed = status(issue("OpenEuroLLM/oellm-eval", 169, state="closed",
                                creator="HannanJaved", assignees=("HannanJaved",)))
        self.assertEqual(observed["status"], "closed_or_resolved")
        self.assertIn("not_proof_of_fix", observed["reason"])


class StateSafetyTests(unittest.TestCase):
    def setUp(self):
        self.task = issue("OpenEuroLLM/oellm-eval", 165, creator="HannanJaved")
        self.pr_url = "https://github.com/OpenEuroLLM/oellm-eval/pull/300"

    def test_live_linked_pr_does_not_count_as_a_new_task(self):
        pr = {"url": self.pr_url, "state": "open", "author": "other", "merged": False}
        result = status(self.task, prs=[pr])
        self.assertEqual(result["status"], "in_progress")
        self.assertEqual(result["evidence_urls"], [self.pr_url])
        self.assertIn("not_proof_of_fix", result["reason"])

    def test_research_graph_pr_mention_is_not_work_on_judgearena_issue(self):
        target = issue("OpenEuroLLM/JudgeArena", 24, creator="kargibora")
        crossrepo_pr = {
            "url": "https://github.com/tire0011/ai-research-graph/pull/51",
            "state": "closed", "merged": True, "author": ACTOR,
        }
        result = status(target, prs=[crossrepo_pr])
        self.assertEqual(result["status"], "new")
        self.assertNotEqual(result["reason"], "actor_cross_referenced_pr")

    def test_research_graph_pr_mention_is_not_work_on_post_training_issue(self):
        target = issue("OpenEuroLLM/post-training", 35, creator="maintainer")
        crossrepo_pr = {
            "url": "https://github.com/tire0011/ai-research-graph/pull/52",
            "state": "closed", "merged": True, "author": ACTOR,
        }
        self.assertEqual(status(target, prs=[crossrepo_pr])["status"], "new")

    def test_cross_repo_open_pr_cannot_imply_work_in_progress(self):
        pr = {"url": "https://github.com/other-org/other-repo/pull/5",
              "state": "open", "author": "other", "merged": False}
        self.assertEqual(status(self.task, prs=[pr])["status"], "new")

    def test_malformed_cross_reference_is_not_ignored(self):
        pr = {"url": "https://github.com/other-org/other-repo/issues/5",
              "state": "open", "author": "other"}
        with self.assertRaisesRegex(ValueError, "Invalid linked PR evidence"):
            status(self.task, prs=[pr])

    def test_real_kyutai_wav_229_collaborator_declined_requested_fix(self):
        # https://github.com/kyutai-labs/pocket-tts/issues/229
        task = issue("kyutai-labs/pocket-tts", 229, creator="davidvk89")
        comment = {
            "user": {"login": "gabrieldemarmiesse"},
            "author_association": "COLLABORATOR",
            "body": ("Yup this was intentional, otherwise the wav format doesn't "
                     "support streaming write. I don't think we'll address it though, "
                     "if you want a good wav file with the size inside, "
                     "i encourage you to write the python code."),
            "html_url": "https://github.com/kyutai-labs/pocket-tts/issues/229#issuecomment-1",
        }
        result = status(task, comments=[comment])
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["reason"], "maintainer_explicitly_declined_requested_work")
        self.assertIn("issues/229", result["evidence_urls"][0])

    def test_comment_without_maintainer_authority_cannot_decline(self):
        task = issue("kyutai-labs/pocket-tts", 229, creator="davidvk89")
        text = "I don't think we'll address it."
        comment = {"user": {"login": "someone"},
                   "author_association": "NONE", "body": text}
        result = status(task, comments=[comment])
        self.assertEqual(result["status"], "new")

    def test_maintainer_just_discussing_not_a_decline(self):
        task = issue("kyutai-labs/pocket-tts", 229, creator="davidvk89")
        comment = {"user": {"login": "collaborator"},
                   "author_association": "COLLABORATOR",
                   "body": "We'll address it in the next release."}
        self.assertEqual(status(task, comments=[comment])["status"], "new")

    def test_explicit_we_wont_fix_comment_from_owner_blocks_new_work(self):
        task = issue("kyutai-labs/pocket-tts", 229, creator="davidvk89")
        comment = {"author_association": "OWNER",
                   "user": {"login": "maintainer"},
                   "body": "We won't fix this in the server."}
        self.assertEqual(status(task, comments=[comment])["status"], "needs_review")

    def test_closed_or_merged_pr_does_not_prove_issue_fixed(self):
        pr = {"url": self.pr_url, "state": "closed", "author": "other", "merged": True}
        self.assertEqual(status(self.task, prs=[pr])["status"], "needs_review")

    def test_actor_pr_is_a_followup(self):
        pr = {"url": self.pr_url, "state": "open", "author": ACTOR, "merged": False}
        self.assertEqual(status(self.task, prs=[pr])["status"], "follow_up")

    def test_failed_pr_check_is_not_silently_new(self):
        result = classify(self.task, [], None, actor=ACTOR,
                          validation_error="GitHub API 503")
        self.assertEqual(result["status"], "needs_review")

    def test_unverified_without_actor_is_not_silently_new(self):
        self.assertEqual(classify(self.task, [], None, actor=None)["status"],
                         "needs_review")

    def test_human_feedback_overrides_fresh_candidates(self):
        self.assertEqual(status(self.task, feedback_state="reviewed")["status"],
                         "follow_up")
        self.assertEqual(status(self.task, feedback_state="dismissed")["status"],
                         "dismissed")
        self.assertEqual(status(self.task, feedback_state="resolved")["status"],
                         "closed_or_resolved")

    def test_canonical_pr_cross_reference_is_checked_live(self):
        hits = []

        def fake_fetch(url):
            hits.append(url)
            if "/timeline?" in url:
                return [{"event": "cross-referenced", "source": {"issue": {
                    "pull_request": {
                        "url": "https://api.github.com/repos/OpenEuroLLM/oellm-eval/pulls/300"
                    }
                }}}]
            return {"html_url": self.pr_url, "state": "open",
                    "merged_at": None, "user": {"login": "maintainer"}}

        related = related_pull_requests(fake_fetch, self.task["html_url"])
        self.assertEqual(len(related), 1)
        self.assertEqual(related[0]["url"], self.pr_url)
        self.assertEqual(len(hits), 2)

    def test_non_pr_cross_reference_is_ignored(self):
        def fake_fetch(_):
            return [{"event": "cross-referenced",
                     "source": {"issue": {"html_url": self.task["html_url"]}}}]

        self.assertEqual(related_pull_requests(fake_fetch, self.task["html_url"]), [])

    def test_pagination_limit_fails_closed(self):
        def fake_fetch(_):
            return [{"event": "commented"}] * 100

        with self.assertRaisesRegex(ValueError, "pagination cap"):
            related_pull_requests(fake_fetch, self.task["html_url"])

    def test_invalid_pr_link_is_rejected(self):
        def fake_fetch(_):
            return [{"event": "cross-referenced", "source": {"issue": {
                "pull_request": {"url": "https://evil.example/pull/1"}
            }}}]

        with self.assertRaisesRegex(ValueError, "Invalid cross-referenced PR URL"):
            related_pull_requests(fake_fetch, self.task["html_url"])


if __name__ == "__main__":
    unittest.main()
