import json
import tempfile
import unittest
from pathlib import Path
from train_language_lora import read_examples, select_training

class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"language": lang, "split": "train", "text": f"{lang} sample {i}"} for lang in ("en","fr","eu") for i in range(100)]

    def test_mix(self):
        selected = select_training(self.rows, "eu", 0.1, 50, 42)
        self.assertEqual(sum(lang=="eu" for lang,_ in selected), 5)
        self.assertEqual(sum(lang=="en" for lang,_ in selected), 45)

    def test_reproducible(self):
        self.assertEqual(select_training(self.rows,"fr",0.2,30,2), select_training(self.rows,"fr",0.2,30,2))

    def test_disjoint_targets(self):
        selected = select_training(self.rows,"fr",0.1,20,1)
        self.assertNotIn("eu", [lang for lang,_ in selected])

    def test_insufficient(self):
        with self.assertRaises(ValueError):
            select_training(self.rows,"eu",0.1,200,42)

    def test_bad_fraction(self):
        with self.assertRaises(ValueError):
            select_training(self.rows,"eu",0,20,42)

    def test_read_examples(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"data.jsonl"
            p.write_text(json.dumps({"language":"en","split":"test","text":"hello"})+"\n",encoding="utf-8")
            self.assertEqual(len(read_examples(p)),1)
            p.write_text(json.dumps({"language":"xx","split":"test","text":"hello"})+"\n",encoding="utf-8")
            with self.assertRaises(ValueError):
                read_examples(p)
