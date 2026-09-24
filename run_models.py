"""
Step 2 (manual mode): collect responses by copy-pasting from the chat apps,
then build blind A/B pairs for annotation. No API key needed.

Usage:
    python run_models.py template   # create/extend responses.csv with empty rows to fill
    python run_models.py status     # show how many responses are still missing
    python run_models.py pairs      # build pairs.csv + pairs_key.csv once everything is filled

How to fill responses.csv:
    - Open it in Google Sheets or Excel. Rows are grouped by model, so you can
      work through one app at a time.
    - For each row: open a NEW chat in that app, paste the 'prompt' cell exactly,
      copy the whole answer back into the 'response' cell.
    - Multi-line answers: in Excel double-click the cell (or use the formula bar)
      before pasting, otherwise the text spreads over several rows.
      Google Sheets: select the cell and paste normally.
    - Save/download as CSV (UTF-8), keep the name responses.csv.
"""
import csv
import itertools
import os
import random
import sys

# Names used in the 'model' column. Change them if you compare other models.
MODELS = ["claude", "gemini", "chatgpt"]

PROMPTS_FILE = "prompts.csv"
RESPONSES_FILE = "responses.csv"
FIELDS = ["prompt_id", "category", "model", "prompt", "response"]
SEED = 42


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    # utf-8-sig so Excel shows Vietnamese correctly
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def load_responses():
    if not os.path.exists(RESPONSES_FILE):
        return {}
    return {(r["prompt_id"], r["model"]): r for r in read_csv(RESPONSES_FILE)}


def template():
    prompts = read_csv(PROMPTS_FILE)
    existing = load_responses()
    rows, added = [], 0
    for m in MODELS:                      # grouped by model = one app at a time
        for p in prompts:
            k = (p["id"], m)
            if k in existing:
                r = existing[k]
                r["prompt"] = p["prompt"]  # keep prompt text in sync with prompts.csv
                rows.append(r)
            else:
                rows.append({"prompt_id": p["id"], "category": p["category"],
                             "model": m, "prompt": p["prompt"], "response": ""})
                added += 1
    write_csv(RESPONSES_FILE, rows, FIELDS)
    print(f"{RESPONSES_FILE}: {len(rows)} rows ({added} new empty rows to fill).")


def missing_rows():
    prompts = read_csv(PROMPTS_FILE)
    resp = load_responses()
    return [(p["id"], m) for m in MODELS for p in prompts
            if not resp.get((p["id"], m), {}).get("response", "").strip()]


def status():
    miss = missing_rows()
    total = len(read_csv(PROMPTS_FILE)) * len(MODELS)
    print(f"Filled: {total - len(miss)}/{total}")
    for m in MODELS:
        ids = [pid for pid, mm in miss if mm == m]
        if ids:
            print(f"  {m}: missing {len(ids)} -> {', '.join(ids[:15])}{' ...' if len(ids) > 15 else ''}")


def pairs():
    miss = missing_rows()
    if miss:
        print(f"Still {len(miss)} empty responses. Run 'python run_models.py status' to see which.")
        sys.exit(1)
    prompts = read_csv(PROMPTS_FILE)
    pmap = {p["id"]: p for p in prompts}
    resp = load_responses()

    rng = random.Random(SEED)
    out, key, n = [], [], 0
    for p in prompts:
        for m1, m2 in itertools.combinations(MODELS, 2):
            a, b = (m1, m2) if rng.random() < 0.5 else (m2, m1)
            n += 1
            pid = p["id"]
            out.append({"pair_id": f"P{n:03d}", "prompt_id": pid, "category": p["category"],
                        "prompt": p["prompt"], "reference_answer": p.get("reference_answer", ""),
                        "response_a": resp[(pid, a)]["response"],
                        "response_b": resp[(pid, b)]["response"],
                        "human_winner": "", "human_reason": ""})
            key.append({"pair_id": f"P{n:03d}", "model_a": a, "model_b": b})
    rng.shuffle(out)  # so you don't annotate the same prompt back to back

    if os.path.exists("pairs.csv") and any(r.get("human_winner") for r in read_csv("pairs.csv")):
        print("pairs.csv already has annotations; rename or delete it first so you don't lose them.")
        sys.exit(1)
    write_csv("pairs.csv", out, list(out[0].keys()))
    write_csv("pairs_key.csv", key, ["pair_id", "model_a", "model_b"])
    print(f"Done: {len(out)} pairs. Annotate pairs.csv; don't open pairs_key.csv until you finish.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"template": template, "status": status, "pairs": pairs}.get(
        cmd, lambda: print(__doc__))()
