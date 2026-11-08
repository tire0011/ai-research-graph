import unittest

import research_questions_benchmark as benchmark


def fixture():
    repo = "OpenEuroLLM/Taskboard"
    origin = {"id": f"github:{repo}#10", "type": "issue", "repository": repo,
              "title": "Explore safety benchmarks", "description": "See #11",
              "url": f"https://github.com/{repo}/issues/10", "updated_at": "fixed"}
    target = {"id": f"github:{repo}#11", "type": "issue", "repository": repo,
              "title": "Fix existing benchmark", "description": "",
              "url": f"https://github.com/{repo}/issues/11", "updated_at": "fixed"}
    graph = {"timestamp_utc": "fixed", "nodes": [origin, target],
             "edges": [{"source": origin["id"], "target": target["id"],
                        "status": "explicit_task_reference"}]}
    study = {"selection": {"seed": "test"}, "cases": [{"id": "a", "cohort": "random",
             "anchor_id": origin["id"], "search_query": "Explore safety benchmarks",
             "expected_ids": [target["id"]]}]}
    return graph, study


class ResearchQuestionsBenchmarkTests(unittest.TestCase):
    def test_parse_source_links_without_graph_edges(self):
        known = {"github:openeurollm/taskboard#11", "github:openeurollm/oellm-eval#124"}
        body = "See #11 and https://github.com/OpenEuroLLM/oellm-eval/pull/124; repeat #11."
        self.assertEqual(benchmark.source_references(body, "OpenEuroLLM/Taskboard", known),
                         ["github:openeurollm/oellm-eval#124", "github:openeurollm/taskboard#11"])

    def test_parser_rejects_reference_prefixes(self):
        known = {"github:openeurollm/taskboard#11"}
        self.assertEqual(benchmark.source_references("#11-experimental and #111 and foo#11",
                                                     "OpenEuroLLM/Taskboard", known), [])

    def test_github_search_and_graph_can_agree_on_real_link(self):
        graph, study = fixture()
        result = benchmark.evaluate(graph, study, repeats=1, delay=0,
            fetch=lambda repo, num: {"body": "See #11", "updated_at": "fixed"},
            search=lambda repo, kind, phrase: {"items": [{"number": 10,
                "title": "Explore safety benchmarks", "body": "See #11"}],
                "total_count": 1, "latency_ms": 8, "query": "fixture"})
        self.assertEqual(result["status"], "completed")
        for method in ("graph", "text", "github_search"):
            self.assertEqual(result["summary"]["all"][method]["exact_answers"], 1)

    def test_unavailable_search_never_counts_as_zero(self):
        graph, study = fixture()
        result = benchmark.evaluate(graph, study, repeats=1, delay=0,
            fetch=lambda repo, num: {"body": "See #11", "updated_at": "fixed"},
            search=lambda repo, kind, phrase: (_ for _ in ()).throw(TimeoutError("github unreachable")))
        self.assertEqual(result["status"], "source_error")
        self.assertEqual(result["evaluated"], 0)
        self.assertIn("source_error", benchmark.markdown(result))

    def test_live_search_accepts_issues_with_null_body(self):
        graph, study = fixture()
        graph["nodes"][0]["description"] = ""
        graph["edges"] = []
        study["cases"][0]["expected_ids"] = []
        result = benchmark.evaluate(graph, study, repeats=1, delay=0,
            fetch=lambda repo, num: {"body": "", "updated_at": "fixed"},
            search=lambda repo, kind, phrase: {"items": [{"number": 10,
                "title": "Explore safety benchmarks", "body": None}],
                "total_count": 1, "latency_ms": 8, "query": "fixture"})
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["summary"]["all"]["github_search"]["correct_abstentions"], 1)

    def test_stale_source_refuses_comparison(self):
        graph, study = fixture()
        result = benchmark.evaluate(graph, study, repeats=1, delay=0,
            fetch=lambda repo, num: {"body": "different", "updated_at": "new"},
            search=lambda repo, kind, phrase: (_ for _ in ()).throw(AssertionError("must not search")))
        self.assertEqual(result["status"], "source_error")
        self.assertIn("stale", result["cases"][0]["error"])

    def test_wrong_gold_does_not_measure_success(self):
        graph, study = fixture()
        study["cases"][0]["expected_ids"] = []
        result = benchmark.evaluate(graph, study, repeats=1, delay=0,
            fetch=lambda repo, num: {"body": "See #11", "updated_at": "fixed"},
            search=lambda repo, kind, phrase: (_ for _ in ()).throw(AssertionError("must not search")))
        self.assertEqual(result["status"], "source_error")
        self.assertIn("Frozen gold", result["cases"][0]["error"])


if __name__ == "__main__":
    unittest.main()
