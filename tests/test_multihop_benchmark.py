import unittest

import multihop_benchmark as mh


def fixture():
    repo = "OpenEuroLLM/Taskboard"
    origin = {"id": f"github:{repo}#10", "type": "issue", "title": "Train dataset",
              "repository": repo, "description": "Follow #11", "updated_at": "fixed",
              "url": f"https://github.com/{repo}/issues/10"}
    middle = {"id": f"github:{repo}#11", "type": "pull_request", "title": "Dataset update",
              "repository": repo, "description": "https://huggingface.co/datasets/openeurollm/example-sample",
              "updated_at": "fixed", "url": f"https://github.com/{repo}/pull/11"}
    asset = {"id": "hf:dataset:openeurollm/example-sample", "type": "dataset",
             "title": "openeurollm/example-sample",
             "url": "https://huggingface.co/datasets/openeurollm/example-sample"}
    graph = {"timestamp_utc": "fixed", "nodes": [origin, middle, asset],
             "edges": [
                 {"source": origin["id"], "target": middle["id"], "status": "explicit_task_reference"},
                 {"source": middle["id"], "target": asset["id"], "status": "explicit_reference"},
             ]}
    case = {"id": "c1", "cohort": "positive", "anchor_id": origin["id"],
            "expected_paths": [[middle["id"], asset["id"]]]}
    def fetch(repo, number):
        node = next(n for n in graph["nodes"] if n["id"] == f"github:{repo}#{number}")
        return {"body": node["description"], "updated_at": node["updated_at"]}
    return graph, {"selection": {}, "cases": [case]}, fetch


class MultiHopTests(unittest.TestCase):
    def test_graph_and_raw_source_follow_agree(self):
        graph, study, fetch = fixture()
        result = mh.evaluate(graph, study, fetch=fetch, repeats=1)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["source_bodies_verified"], 2)
        self.assertEqual(result["summary"]["all"]["reference_paths"], 1)
        self.assertEqual(result["summary"]["all"]["graph_exact"], 1)
        self.assertEqual(result["summary"]["all"]["source_follow_exact"], 1)

    def test_candidates_and_unverified_labels_are_not_proven_paths(self):
        graph, _, _ = fixture()
        graph["edges"][1]["status"] = "candidate"
        self.assertEqual(mh.graph_paths(graph["edges"], graph["nodes"][0]["id"]), [])
        graph["edges"][1]["status"] = "identifier_match"
        self.assertEqual(mh.graph_paths(graph["edges"], graph["nodes"][0]["id"]), [])

    def test_no_target_requires_abstention(self):
        graph, study, fetch = fixture()
        graph["nodes"][0]["description"] = "No referenced task"
        graph["edges"] = []
        study["cases"][0]["cohort"] = "negative"
        study["cases"][0]["expected_paths"] = []
        result = mh.evaluate(graph, study, fetch=fetch, repeats=1)
        self.assertEqual(result["summary"]["all"]["correct_graph_abstentions"], 1)

    def test_incorrect_gold_refuses_success(self):
        graph, study, fetch = fixture()
        study["cases"][0]["expected_paths"] = []
        result = mh.evaluate(graph, study, fetch=fetch, repeats=1)
        self.assertEqual(result["status"], "source_error")
        self.assertIn("Frozen source-text annotation", result["cases"][0]["error"])

    def test_changed_original_body_is_not_zero(self):
        graph, study, _ = fixture()
        result = mh.evaluate(graph, study, fetch=lambda repo, num: {
            "body": "wrong", "updated_at": "new"}, repeats=1)
        self.assertEqual(result["status"], "source_error")
        self.assertEqual(result["evaluated"], 0)


if __name__ == "__main__":
    unittest.main()
