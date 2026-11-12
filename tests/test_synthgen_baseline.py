"""No-network synthetic fixtures, never interpreted as real dataset measurements."""
import unittest
from urllib.parse import parse_qs, urlparse
from synthgen_baseline import collect, dataset_revision, normalized, offsets, split_sizes

SHA = "a" * 40

def row(lang, n):
    return {
        "id": f"{lang}-{n}", "language": lang,
        "domain": "coding" if n % 2 else "translation",
        "judge_score": 10 if n % 3 else 7,
        "messages": [{"role":"user", "content":f"Question {n}"},
                     {"role":"assistant", "content":f"Answer {n}"}]
    }

def fake_api(url):
    if url.startswith("https://huggingface.co/api/"):
        return {"sha": SHA}
    parsed = urlparse(url)
    if parsed.path.endswith("/size"):
        return {"size":{"splits":[{"config":l,"split":"train","num_rows":60} for l in ("de","eu")]}}
    params = parse_qs(parsed.query)
    lang, start, length = params["config"][0], int(params["offset"][0]), int(params["length"][0])
    return {"rows":[{"row_idx":n,"row":row(lang,n)} for n in range(start,start+length)]}

class BaselineTests(unittest.TestCase):
    def test_offsets_disjoint_and_deterministic(self):
        x = offsets(120, 3, 10, 5, "de")
        self.assertEqual(x, offsets(120, 3, 10, 5, "de"))
        self.assertEqual(len(x), 3)
        self.assertTrue(x[0]+10 <= x[1] and x[1]+10 <= x[2])

    def test_invalid_offsets_fail(self):
        with self.assertRaises(ValueError): offsets(5,2,3,0,"de")
        with self.assertRaises(ValueError): offsets(1000,2,101,0,"de")

    def test_valid_record(self):
        self.assertEqual(normalized(row("de",1),"de")[2],10)

    def test_invalid_role_fails(self):
        x = row("de", 1)
        x["messages"][0]["role"] = "system"
        with self.assertRaisesRegex(ValueError, "role"): normalized(x,"de")

    def test_invalid_score_fails(self):
        x = row("de",1)
        x["judge_score"] = 11
        with self.assertRaisesRegex(ValueError, "score"): normalized(x,"de")

    def test_size_revision(self):
        self.assertEqual(dataset_revision(fake_api),SHA)
        self.assertEqual(split_sizes(fake_api),{"de":60,"eu":60})

    def test_realistic_structure_only(self):
        output = collect(("de","eu"),pages=2,length=5,seed=9,fetch=fake_api)
        self.assertEqual(output["hub_revision_before_after"],SHA)
        self.assertFalse(output["viewer_revision_pinned"])
        self.assertEqual(output["samples"]["eu"]["sample_rows"],10)
        self.assertEqual(sum(output["samples"]["de"]["scores"].values()),10)

    def test_revision_change_fails(self):
        count = 0
        def modified(url):
            nonlocal count
            if url.startswith("https://huggingface.co/api/"):
                count += 1
                return {"sha": ("a" if count==1 else "b") * 40}
            return fake_api(url)
        with self.assertRaisesRegex(ValueError,"revision changed"):
            collect(("de",),pages=2,length=5,fetch=modified)

    def test_incomplete_page_fails(self):
        def modified(url):
            data = fake_api(url)
            if urlparse(url).path.endswith("/rows"):
                data["rows"].pop()
            return data
        with self.assertRaisesRegex(ValueError,"Incomplete"):
            collect(("de",),pages=2,length=5,fetch=modified)

if __name__ == "__main__": unittest.main()
