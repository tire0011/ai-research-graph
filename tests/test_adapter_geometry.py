import tempfile
import unittest
from pathlib import Path
import numpy as np
from adapter_geometry import compare, load_updates

class AdapterGeometryTests(unittest.TestCase):
    def test_identical(self):
        x = {"q": np.diag([3., 2., 1.])}
        r = compare(x, x, 2)["q"]
        self.assertAlmostEqual(r["cosine"], 1)
        self.assertAlmostEqual(r["left_subspace_overlap"], 1)
        self.assertAlmostEqual(r["delta_distance"], 0)

    def test_opposite(self):
        x = {"q": np.diag([3., 2., 1.])}
        r = compare(x, {"q": -x["q"]}, 2)["q"]
        self.assertAlmostEqual(r["cosine"], -1)
        self.assertAlmostEqual(r["left_subspace_overlap"], 1)

    def test_zero(self):
        r = compare({"q": np.zeros((2,2))}, {"q": np.eye(2)})["q"]
        self.assertIsNone(r["cosine"])
        self.assertIsNone(r["left_subspace_overlap"])

    def test_mismatch(self):
        with self.assertRaises(ValueError):
            compare({"q": np.eye(2)}, {"k": np.eye(2)})
        with self.assertRaises(ValueError):
            compare({"q": np.eye(2)}, {"q": np.eye(3)})

    def test_npz(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"a.npz"
            np.savez(p, **{"q.lora_A": np.array([[1.,2.]]),
                            "q.lora_B": np.array([[3.],[4.]]),
                            "q.scaling": np.array(0.5)})
            np.testing.assert_array_equal(load_updates(p)["q"], [[1.5,3.],[2.,4.]])

    def test_invalid_npz(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"a.npz"
            np.savez(p, **{"q.lora_A": np.ones((2,3)), "q.lora_B": np.ones((2,3))})
            with self.assertRaises(ValueError):
                load_updates(p)
