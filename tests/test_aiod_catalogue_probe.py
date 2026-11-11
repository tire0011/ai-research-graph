"""Offline contract tests for official AIoD v2 read-only catalogue sampling."""

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import aiod_catalogue_probe as aiod


NOW = dt.datetime(2026, 11, 11, 9, tzinfo=dt.timezone.utc)


def asset(identifier, name, **extras):
    return {
        "identifier": identifier, "name": name,
        "platform": "huggingface", "platform_resource_identifier": f"hf-{identifier}",
        "same_as": f"https://huggingface.co/datasets/example/{identifier}",
        "description_plain": "Research source metadata, not proof of model training.",
        **extras,
    }


class AiodProbeTests(unittest.TestCase):
    def test_v2_list_url_is_bounded_get_on_official_host(self):
        url = aiod.url_for("https://api.aiodp.eu", "projects", 0, 10)
        self.assertEqual(url, "https://api.aiodp.eu/v2/projects?offset=0&limit=10")
        for host in ("http://api.aiodp.eu", "https://example.org"):
            with self.assertRaisesRegex(ValueError, "Unrecognized"):
                aiod.url_for(host, "projects", 0, 10)
        with self.assertRaisesRegex(ValueError, "Invalid offset/limit"):
            aiod.url_for("https://api.aiodp.eu", "projects", 0, 500000)

    def test_fetch_two_pages_with_stable_v2_id_and_source_hash(self):
        seen = []
        def fake(url):
            seen.append(url)
            return [asset(81, "Open research project"), asset(82, "Research service")] if "offset=0" in url else [asset(83, "New component")]

        report = aiod.collect("projects", limit=2, pages=2, fetch=fake, now=NOW)
        self.assertEqual(report["items"], 3)
        self.assertFalse(report["sample_limited"])
        self.assertEqual([x["id"] for x in report["nodes"]],
                         ["aiod:v2:projects:81", "aiod:v2:projects:82", "aiod:v2:projects:83"])
        self.assertIn("offset=2&limit=2", seen[1])
        self.assertEqual(len(report["nodes"][0]["metadata_sha256"]), 64)
        self.assertEqual(report["nodes"][0]["evidence_level"], "indexed_metadata_only")
        self.assertFalse(report["novel_collaboration_confirmed"])

    def test_full_final_page_is_marked_incomplete(self):
        report = aiod.collect("datasets", limit=1, pages=1,
                              fetch=lambda _: [asset(1, "One")], now=NOW)
        self.assertTrue(report["sample_limited"])

    def test_unexpected_wrappers_are_not_silently_guessed(self):
        with self.assertRaisesRegex(ValueError, "Unexpected AIoD v2"):
            aiod.collect("projects", fetch=lambda _: {"items": [asset(1, "One")]})

    def test_missing_or_conflicting_identifiers_fail_before_writing(self):
        for rows in ([asset(None, "Missing")], [asset(4, "A"), asset(4, "B")]):
            with self.assertRaises(ValueError):
                aiod.collect("projects", limit=2, fetch=lambda _: rows)

    def test_untrusted_external_link_does_not_become_original_source(self):
        row = asset(42, "Dataset", same_as="javascript:alert(1)")
        node = aiod.normalise(row, "datasets", aiod.API_HOSTS[0],
                              aiod.url_for(aiod.API_HOSTS[0], "datasets", 0, 1))
        self.assertIsNone(node["original_url_claim"])

    def test_identifier_containing_colon_is_not_truncated_in_record_url(self):
        node = aiod.normalise(asset("catalogue:record:42", "Colon ID"), "projects",
                              aiod.API_HOSTS[0],
                              aiod.url_for(aiod.API_HOSTS[0], "projects", 0, 1))
        self.assertEqual(node["id"], "aiod:v2:projects:catalogue:record:42")
        self.assertTrue(node["url"].endswith("/catalogue%3Arecord%3A42"))

    def test_real_v2_nested_plain_description_is_extracted(self):
        row = asset(51, "Medical imaging tools", description_plain="",
                    description={"plain": "Evaluate medical image segmentation across sites"})
        node = aiod.normalise(row, "projects", aiod.API_HOSTS[0],
                              aiod.url_for(aiod.API_HOSTS[0], "projects", 0, 1))
        self.assertEqual(node["description"],
                         "Evaluate medical image segmentation across sites")

    def test_same_claimed_external_url_flags_metadata_alias_not_duplicate_work(self):
        report = aiod.collect("projects", limit=3, fetch=lambda _: [
            asset(1, "Shared research title", same_as="https://research.example.org/p/7"),
            asset(2, "Shared research title", same_as="https://research.example.org/p/7"),
            asset(3, "Different activity", same_as="https://research.example.org/p/8"),
        ], now=NOW)
        qa = report["data_quality"]
        self.assertEqual(qa["records_in_same_claimed_url_groups"], 2)
        self.assertEqual(len(qa["same_claimed_url_groups"]), 1)
        self.assertEqual(qa["records_in_same_title_groups"], 2)
        self.assertFalse(report["novel_collaboration_confirmed"])

    def test_failure_does_not_replace_previous_good_files(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            success = aiod.collect("projects", fetch=lambda _: [asset(11, "Good")], now=NOW)
            aiod.write_success(success, folder)
            old = (folder / "projects.json").read_bytes()
            with patch.object(aiod, "collect", side_effect=OSError("offline")):
                self.assertEqual(aiod.main(["--output", directory]), 1)
            self.assertEqual((folder / "projects.json").read_bytes(), old)
            self.assertIn("sample_limited", json.loads(old))

    def test_rejects_unbounded_paging(self):
        with self.assertRaisesRegex(ValueError, "Page count"):
            aiod.collect("projects", pages=100, fetch=lambda _: [])


if __name__ == "__main__":
    unittest.main()
