# Language recipe: adapter geometry pilot

A CPU-only NumPy tool for comparing two LoRA adapters **from the same base model**. No training or checkpoint inference has been performed.

## Input
Explicit NumPy NPZ files with keys `<module>.lora_A` (rank × input), `<module>.lora_B` (output × rank), optional `<module>.scaling` scalar. Updates are reconstructed as `scaling * B @ A`. This is **not** a direct PEFT/safetensors reader. Do not enable pickle.

## Windows PowerShell
```powershell
python -m pip install numpy
python -m unittest discover -s tests -p test_adapter_geometry.py -v
python .\adapter_geometry.py .\adapter_en_fr.npz .\adapter_en_eu.npz --top-k 4
```

Measures: Frobenius norms and distance; cosine similarity of update matrices; overlap of top-k left-singular-vector subspaces; entropy-based effective rank. **Opposite updates have the same singular subspaces but negative cosine.** Subspace overlap alone does not reveal linguistic concepts. Tied singular values may make individual top-k subspaces unstable.

Next: export two *real* PEFT LoRA adapters trained with identical base/tokenizer/target modules and matched token budgets; evaluate held-out language tasks and compare whether geometry predicts transfer. Control for seed, task equivalence and contamination. No model quality claims from geometry alone.
