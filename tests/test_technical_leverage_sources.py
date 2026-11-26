import unittest
from technical_leverage_sources import references, manifest_dependencies, select_repos, collect

STAMP = "2026-11-26T14:00:00+00:00"

class SourceTests(unittest.TestCase):
    def test_exact_links_and_hash(self):
        rows = references("EU/project", "See [tool](https://github.com/tools/eval/issues/3). "
                          "https://github.com/tools/eval https://github.com/EU/project",
                          "https://github.com/EU/project#readme", "readme_reference", STAMP)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["target"], "https://github.com/tools/eval")
        self.assertEqual(len(rows[0]["evidence"]["sha256"]), 64)

    def test_manifest_direct_vcs_only(self):
        rows = manifest_dependencies("EU/project", "requirements.txt",
                                     "# git+https://github.com/no/comment\n"
                                     "pkg @ git+https://github.com/tools/eval.git@main\n"
                                     "torch>=2\n",
                                     "https://github.com/EU/project/blob/main/requirements.txt", STAMP)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["target"], "https://github.com/tools/eval")
        self.assertEqual(rows[0]["evidence"]["type"], "manifest_vcs_declaration")

    def test_toml_and_npm(self):
        for path, body in [
            ("pyproject.toml", '[project]\ndependencies=["x @ git+https://github.com/tools/eval"]'),
            ("package.json", '{"dependencies":{"x":"git+https://github.com/tools/eval.git"}}')
        ]:
            with self.subTest(path=path):
                self.assertEqual(len(manifest_dependencies("EU/p", path, body,
                    "https://github.com/EU/p/blob/main/" + path, STAMP)), 1)

    def test_rotation(self):
        cfg = {"repositories": [{"repo": f"org{i}/a"} for i in range(10)]}
        first = select_repos(cfg, [], None)
        second = select_repos(cfg, [], {"last_attempt": {x.lower(): STAMP for x in first}})
        self.assertEqual(len(first), 8)
        self.assertIn("org9/a", second)

    def test_private_identity_gate(self):
        result = collect({"repositories": [{"repo": "EU/p"}]}, [],
                         lambda url: {"full_name":"EU/p","private":True}, stamp=STAMP)
        self.assertFalse(result["edges"])
        self.assertTrue(result["errors"])

    def test_live_shape_mock_and_comment_provenance(self):
        import base64
        repo = "EU/p"
        api = "https://api.github.com/repos/" + repo
        issue = "https://github.com/EU/p/issues/1"
        text = "https://github.com/tools/eval"
        def fetch(url):
            if url == api:
                return {"full_name":repo,"private":False,"fork":False,"archived":False}
            if url == api + "/readme":
                return {"content":base64.b64encode(text.encode()).decode(),"encoding":"base64",
                        "html_url":"https://github.com/EU/p/blob/main/README.md","sha":"abc"}
            if url == api + "/contents":
                return []
            if "/issues?" in url:
                return [{"number":1,"html_url":issue,"body":"","comments":1}]
            if "/comments?" in url:
                return [{"id":123,"html_url":issue+"#issuecomment-123","body":text}]
            raise AssertionError(url)
        result = collect({"repositories":[{"repo":repo}]}, [], fetch, stamp=STAMP)
        self.assertEqual(len(result["edges"]), 2)
        self.assertEqual(result["coverage"][0]["comments"], 1)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["edges"][1]["evidence"]["source_url"],issue+"#issuecomment-123")
