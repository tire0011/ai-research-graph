# Minimal language-recipe training pilot (Windows GPU)

This is an **executable experiment**, not a demonstrated improvement. The training script is designed for the user's 8 GB NVIDIA GPU under **native Windows**; WSL CUDA is not required. It uses a 0.5B base model, FP32 LoRA rank 4, batch size 1, sequence length 128 and no quantization. Memory usage and runtime must be checked locally.

## Prepare

Use Python 3.11 or 3.12 and a CUDA-enabled PyTorch wheel matching the installed NVIDIA driver; install from [pytorch.org](https://pytorch.org/get-started/locally/) (do not assume a specific CUDA wheel). Then:

```powershell
python -m pip install transformers peft accelerate safetensors numpy
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
python -m unittest discover -s tests -p test_train_language_lora.py -v
```

## Data

Create UTF-8 JSONL `data/language_pilot.jsonl`, one JSON object per line, with:
```json
{"language":"en","split":"train","text":"The train example."}
{"language":"fr","split":"train","text":"Un exemple d'entraînement."}
{"language":"eu","split":"train","text":"Entrenamenduko adibide bat."}
{"language":"en","split":"test","text":"A held-out English example."}
{"language":"fr","split":"test","text":"Un exemple français de test."}
{"language":"eu","split":"test","text":"Probarako euskarazko adibidea."}
```

These six rows only illustrate the format; the default recipe requires **90 English + 10 target-language distinct training rows** per run, plus test examples in all three languages. Prefer professionally translated or independently verified, task-matched sentences. Do not reuse any test text in training. The script currently checks counts but not near-duplicate contamination or semantic equivalence.

## Two runs from exactly the same base model

```powershell
python .\train_language_lora.py --data .\data\language_pilot.jsonl --target fr --count 100 --fraction 0.1 --steps 40 --output .\runs\en_fr
python .\train_language_lora.py --data .\data\language_pilot.jsonl --target eu --count 100 --fraction 0.1 --steps 40 --output .\runs\en_eu
python .\adapter_geometry.py .\runs\en_fr\geometry.npz .\runs\en_eu\geometry.npz --top-k 4
```

Each run saves a PEFT adapter, `geometry.npz`, and `metrics.json` with held-out causal-language-model loss before and after. The base weights are not altered. Use the **same model, seed, steps, target modules and tokenizer** for both. Different target languages may have different token counts even with equal example counts: the pilot matches example count, **not token budget**. This is a limitation, not a controlled comparison of training efficiency.

## Interpretation and next controls

- Loss on held-out texts measures next-token prediction, **not** language comprehension or instruction-following.
- Compare per-language loss deltas and adapter geometry. An association does not show causal mechanisms or optimal recipes.
- Next add token-matched training, multiple seeds, verified parallel tasks, a no-training baseline, and an independent benchmark before scientific conclusions.
- Model and dataset downloads require internet; no model was downloaded or trained by this repository change.
