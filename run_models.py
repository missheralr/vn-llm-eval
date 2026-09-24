"""
Step 2: send every prompt to every model, save responses, then build blind A/B pairs.

Usage:
    pip install openai
    python run_models.py            # call the real APIs
    python run_models.py --dry-run  # fake responses, to test the pipeline

Outputs:
    responses.csv   one row per (prompt, model)
    pairs.csv       blind pairs for you to annotate (no model names)
    pairs_key.csv   which model is A / B in each pair (don't open while annotating)
"""
import csv
import itertools
import os
import random
import sys
import time

# Fill in the models you want to compare. Any OpenAI-compatible endpoint works
# (OpenAI, Gemini's OpenAI-compatible endpoint, OpenRouter, Groq, local Ollama...).
# Check each provider's docs for the current base_url and model name.
MODELS = [
    {"name": "model_1", "base_url": "https://api.openai.com/v1",
     "api_key_env": "OPENAI_API_KEY", "model": "FILL_ME"},
    {"name": "model_2", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
     "api_key_env": "GEMINI_API_KEY", "model": "FILL_ME"},
    {"name": "model_3", "base_url": "http://localhost:11434/v1",  # Ollama
     "api_key_env": None, "model": "FILL_ME"},
]

PROMPTS_FILE = "prompts.csv"
RESPONSES_FILE = "responses.csv"
SEED = 42


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    # utf-8-sig so Excel shows Vietnamese correctly
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def ask(cfg, prompt, dry_run):
    if dry_run:
        return f"[dry-run answer from {cfg['name']}] {prompt[:40]}..."
    from openai import OpenAI
    key = os.environ.get(cfg["api_key_env"]) if cfg["api_key_env"] else "none"
    client = OpenAI(base_url=cfg["base_url"], api_key=key)
    for attempt in range(3):
        try:
            r = client.chat.completions.create(
                model=cfg["model"],
                messages=[{"role": "user", "content": prompt}],
            )
            return r.choices[0].message.content.strip()
        except Exception as e:  # rate limits, timeouts...
            print(f"  error ({cfg['name']}, attempt {attempt + 1}): {e}")
            time.sleep(5 * (attempt + 1))
    return "[ERROR]"


def main():
    dry_run = "--dry-run" in sys.argv
    prompts = read_csv(PROMPTS_FILE)

    # Resume: keep responses already collected
    done = {}
    if os.path.exists(RESPONSES_FILE):
        for r in read_csv(RESPONSES_FILE):
            if r["response"] != "[ERROR]":
                done[(r["prompt_id"], r["model"])] = r

    rows = []
    for p in prompts:
        for cfg in MODELS:
            k = (p["id"], cfg["name"])
            if k in done:
                rows.append(done[k])
                continue
            print(f"{p['id']} -> {cfg['name']}")
            rows.append({"prompt_id": p["id"], "category": p["category"],
                         "model": cfg["name"], "response": ask(cfg, p["prompt"], dry_run)})
            write_csv(RESPONSES_FILE, rows, ["prompt_id", "category", "model", "response"])

    # Build blind pairs, random A/B order
    rng = random.Random(SEED)
    by_prompt = {}
    for r in rows:
        by_prompt.setdefault(r["prompt_id"], {})[r["model"]] = r["response"]
    pmap = {p["id"]: p for p in prompts}

    pairs, key = [], []
    n = 0
    for pid, resp in by_prompt.items():
        for m1, m2 in itertools.combinations(sorted(resp), 2):
            a, b = (m1, m2) if rng.random() < 0.5 else (m2, m1)
            n += 1
            pair_id = f"P{n:03d}"
            pairs.append({"pair_id": pair_id, "prompt_id": pid,
                          "category": pmap[pid]["category"], "prompt": pmap[pid]["prompt"],
                          "reference_answer": pmap[pid].get("reference_answer", ""),
                          "response_a": resp[a], "response_b": resp[b],
                          "human_winner": "", "human_reason": ""})
            key.append({"pair_id": pair_id, "model_a": a, "model_b": b})
    rng.shuffle(pairs)  # so you don't annotate the same prompt back to back

    write_csv("pairs.csv", pairs, list(pairs[0].keys()))
    write_csv("pairs_key.csv", key, ["pair_id", "model_a", "model_b"])
    print(f"Done: {len(rows)} responses, {len(pairs)} pairs.")


if __name__ == "__main__":
    main()
