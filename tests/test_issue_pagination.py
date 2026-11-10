"""Prevent incomplete GitHub issue inventories from looking complete."""

import unittest
from unittest.mock import patch

from research_graph import github_issues


def row(n):
    return {
        "number": n, "title": f"Issue {n}", "body": "",
        "html_url": f"https://github.com/example/repo/issues/{n}",
        "state": "open", "updated_at": "2026-11-10T00:00:00Z",
    }


class GithubPaginationTests(unittest.TestCase):
    def test_full_final_page_must_fail_closed(self):
        urls = []

        def get(url, *, token=None):
            urls.append(url)
            page = len(urls)
            return [row(n) for n in range((page - 1) * 100 + 1, page * 100 + 1)]

        with patch("research_graph.fetch_json", side_effect=get):
            with self.assertRaisesRegex(ValueError, "page cap"):
                github_issues("example/repo", max_pages=2)
        self.assertEqual(len(urls), 2)

    def test_partial_final_page_succeeds(self):
        batches = [[row(n) for n in range(1, 101)], [row(101)]]
        with patch("research_graph.fetch_json", side_effect=lambda *a, **kw: batches.pop(0)):
            issues = github_issues("example/repo", max_pages=2)
        self.assertEqual(len(issues), 101)
        self.assertEqual(issues[-1]["id"], "github:example/repo#101")

    def test_reject_invalid_page_cap(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            github_issues("example/repo", max_pages=0)


if __name__ == "__main__":
    unittest.main()
