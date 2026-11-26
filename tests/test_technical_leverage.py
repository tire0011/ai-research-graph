import unittest
from technical_leverage import rank

class LeverageTests(unittest.TestCase):
    config = {"repositories": [{"repo": "EU/seed"}]}
    def edge(self, src, dst, **kwargs):
        return {"source": src, "target": dst, "relationship": "references",
                "verification_status": "verified",
                "evidence": {"source_entity": src, "source_url": src,
                             "excerpt": dst}, **kwargs}

    def test_shared_component_and_owner_dedup(self):
        target = "https://github.com/tools/eval"
        rows = [self.edge("https://github.com/EU/a", target),
                self.edge("https://github.com/eu/b", target),
                self.edge("https://github.com/other/c", target),
                self.edge("https://github.com/tools/self", target)]
        result = rank(self.config, {"verified_references": rows})
        self.assertEqual(result["candidate_count"], 1)
        item = result["candidates"][0]
        self.assertEqual(item["distinct_source_owners"], 2)
        self.assertEqual(item["curated_owner_context_count"], 1)
        self.assertEqual(item["unknown_owner_context_count"], 1)
        self.assertEqual(len(item["references"]), 3)

    def test_one_owner_not_shared(self):
        target = "https://github.com/tools/eval"
        self.assertFalse(rank(self.config, {"verified_references": [
            self.edge("https://github.com/EU/a", target),
            self.edge("https://github.com/eu/b", target)]})["candidates"])

    def test_evidence_and_status_gate(self):
        row = self.edge("https://github.com/EU/a", "https://github.com/tools/eval")
        row["evidence"]["excerpt"] = "https://github.com/tools/other"
        other = self.edge("https://github.com/other/c", "https://github.com/tools/eval")
        other["verification_status"] = "unknown"
        self.assertEqual(rank(self.config, {"verified_references": [row, other]})["observations"], 0)

    def test_known_cases_not_ranked(self):
        result = rank({**self.config, "technical_leverage_cases": [{"component": "example"}]}, {})
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(len(result["known_cases"]), 1)

    def test_priority_and_limit(self):
        rows = []
        for target, owners in [("a", ["x", "y", "z"]), ("b", ["EU", "x"])]:
            for owner in owners:
                rows.append(self.edge(f"https://github.com/{owner}/r", f"https://github.com/tools/{target}"))
        result = rank(self.config, {"verified_references": rows}, limit=1)
        self.assertEqual(result["candidate_count"], 2)
        self.assertTrue(result["candidates"][0]["component"].endswith("/b"))

    def test_duplicate_observation_not_counted_twice(self):
        target = "https://github.com/tools/eval"
        row = self.edge("https://github.com/EU/a", target)
        result = rank(self.config, {"verified_references": [row, row]})
        self.assertEqual(result["observations"], 1)

    def test_attachment_links_are_not_components(self):
        target = "https://github.com/user-attachments/assets"
        result = rank(self.config, {"verified_references": [
            self.edge("https://github.com/EU/a", target),
            self.edge("https://github.com/other/b", target)]})
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["observations"], 0)
