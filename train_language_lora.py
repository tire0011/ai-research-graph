"""Small Windows CUDA LoRA language-mixture experiment; no quantization required."""
import argparse
import json
import random
from collections import Counter
from pathlib import Path

LANGUAGES = ("en", "fr", "eu")

def read_examples(path):
    rows = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or row.get("language") not in LANGUAGES or not isinstance(row.get("text"), str) or not row["text"].strip():
            raise ValueError(f"Invalid example on line {n}")
        if row.get("split") not in ("train", "test"):
            raise ValueError(f"Invalid split on line {n}")
        rows.append(row)
    return rows

def select_training(rows, target, target_fraction, count, seed):
    if target not in ("fr", "eu") or not 0 < target_fraction < 1 or count < 2:
        raise ValueError("Invalid recipe")
    rng = random.Random(seed)
    n_target = round(count * target_fraction)
    if not 0 < n_target < count:
        raise ValueError("Recipe rounds to a single language")
    pools = {lang: [r["text"] for r in rows if r["split"] == "train" and r["language"] == lang] for lang in ("en", target)}
    needed = {"en": count - n_target, target: n_target}
    if any(len(pools[lang]) < needed[lang] for lang in needed):
        raise ValueError(f"Insufficient examples: required {needed}, available { {k:len(v) for k,v in pools.items()} }")
    chosen = [(lang, text) for lang, n in needed.items() for text in rng.sample(pools[lang], n)]
    rng.shuffle(chosen)
    return chosen

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True, help="JSONL: language en/fr/eu, split train/test, text")
    p.add_argument("--target", choices=("fr", "eu"), required=True)
    p.add_argument("--model", default="Qwen/Qwen2.5-0.5B")
    p.add_argument("--fraction", type=float, default=0.1)
    p.add_argument("--count", type=int, default=100)
    p.add_argument("--steps", type=int, default=40)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    if args.steps < 1:
        p.error("--steps must be positive")
    rows = read_examples(args.data)
    selected = select_training(rows, args.target, args.fraction, args.count, args.seed)
    heldout = {lang: [r["text"] for r in rows if r["split"] == "test" and r["language"] == lang] for lang in LANGUAGES}
    if any(not v for v in heldout.values()):
        p.error("At least one held-out test row per language required")
    # Import GPU dependencies only after input validation.
    import numpy as np
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model
    from safetensors.torch import load_file

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Device:", device, "training examples:", Counter(lang for lang, _ in selected))
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.float32).to(device)
    model.config.use_cache = False

    def loss_for(text):
        ids = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)["input_ids"].to(device)
        if ids.shape[1] < 2:
            raise ValueError("Example too short after tokenization")
        return model(input_ids=ids, labels=ids).loss

    def evaluate():
        model.eval()
        result = {}
        with torch.no_grad():
            for lang, texts in heldout.items():
                result[lang] = float(sum(loss_for(t).item() for t in texts) / len(texts))
        return result

    baseline = evaluate()
    config = LoraConfig(r=4, lora_alpha=8, target_modules=["q_proj", "v_proj"], lora_dropout=0.0, bias="none", task_type="CAUSAL_LM")
    model = get_peft_model(model, config)
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=1e-4)
    for step in range(args.steps):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        loss = loss_for(selected[step % len(selected)][1])
        loss.backward()
        optimizer.step()
        if (step + 1) % 10 == 0:
            print(f"step {step+1}: loss {loss.item():.4f}")
    after = evaluate()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    model.save_pretrained(output / "adapter", safe_serialization=True)
    weights = load_file(str(output / "adapter" / "adapter_model.safetensors"), device="cpu")
    arrays = {}
    for key, value in weights.items():
        if key.endswith(".lora_A.weight"):
            prefix = key[:-len(".lora_A.weight")]
            arrays[prefix + ".lora_A"] = value.float().numpy()
        elif key.endswith(".lora_B.weight"):
            prefix = key[:-len(".lora_B.weight")]
            arrays[prefix + ".lora_B"] = value.float().numpy()
        else:
            raise ValueError("Unexpected adapter tensor: " + key)
    for key in list(arrays):
        if key.endswith(".lora_A"):
            arrays[key[:-len(".lora_A")] + ".scaling"] = np.array(config.lora_alpha / config.r)
    np.savez_compressed(output / "geometry.npz", **arrays)
    result = {"model": args.model, "target": args.target, "fraction": args.fraction,
              "count": args.count, "steps": args.steps, "seed": args.seed,
              "train_language_counts": dict(Counter(lang for lang, _ in selected)),
              "heldout_loss_before": baseline, "heldout_loss_after": after,
              "warning": "Tiny pilot; loss is not instruction-following performance. No statistical conclusion."}
    (output / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
