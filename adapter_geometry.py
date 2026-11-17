"""CPU-only comparison of LoRA weight updates from explicit .npz matrices."""
import argparse
import json
import numpy as np

def load_updates(path):
    with np.load(path, allow_pickle=False) as data:
        names = sorted(k[:-7] for k in data.files if k.endswith(".lora_A"))
        if not names:
            raise ValueError("No LoRA matrices")
        result = {}
        for name in names:
            a, b = np.asarray(data[name+".lora_A"], dtype=float), np.asarray(data[name+".lora_B"], dtype=float)
            if a.ndim != 2 or b.ndim != 2 or b.shape[1] != a.shape[0]:
                raise ValueError("Invalid LoRA shapes: "+name)
            scale = float(data[name+".scaling"]) if name+".scaling" in data else 1.0
            if not np.isfinite(a).all() or not np.isfinite(b).all() or not np.isfinite(scale):
                raise ValueError("Nonfinite values: "+name)
            result[name] = scale * (b @ a)
        return result

def compare(left, right, k=4):
    if k < 1 or set(left) != set(right):
        raise ValueError("Invalid rank or module mismatch")
    out = {}
    for name in sorted(left):
        x, y = left[name], right[name]
        if x.shape != y.shape:
            raise ValueError("Shape mismatch: "+name)
        nx, ny = np.linalg.norm(x), np.linalg.norm(y)
        sx = np.linalg.svd(x, compute_uv=False)
        sy = np.linalg.svd(y, compute_uv=False)
        rank = min(k, min(x.shape))
        ux = np.linalg.svd(x, full_matrices=False)[0][:, :rank]
        uy = np.linalg.svd(y, full_matrices=False)[0][:, :rank]
        def effective_rank(s):
            p = s**2
            if not p.sum():
                return 0.0
            p /= p.sum()
            p = p[p > 0]
            return float(np.exp(-np.sum(p*np.log(p))))
        out[name] = {
            "frobenius_left": float(nx), "frobenius_right": float(ny),
            "delta_distance": float(np.linalg.norm(x-y)),
            "cosine": float(np.sum(x*y)/(nx*ny)) if nx and ny else None,
            "left_subspace_overlap": float(np.linalg.norm(ux.T@uy, "fro")**2/rank) if nx and ny else None,
            "effective_rank_left": effective_rank(sx),
            "effective_rank_right": effective_rank(sy),
        }
    return out

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("left")
    p.add_argument("right")
    p.add_argument("--top-k", type=int, default=4)
    args = p.parse_args()
    print(json.dumps(compare(load_updates(args.left), load_updates(args.right), args.top_k), indent=2))
