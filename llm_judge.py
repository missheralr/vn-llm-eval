"""
Step 4: let an LLM judge the same pairs, using the same rubric.
Each pair is judged twice (A/B and swapped) to reduce position bias;
if the two verdicts disagree, the result is recorded as 'tie'.

Usage:
    python llm_judge.py            # real API
    python llm_judge.py --dry-run  # random verdicts, to test the pipeline

Output: judge_results.csv
"""
import csv
import json
import os
import random
import re
import sys

JUDGE = {"base_url": "https://api.openai.com/v1", "api_key_env": "OPENAI_API_KEY",
         "model": "FILL_ME"}  # ideally NOT one of the models being compared

TEMPLATE = """You are an expert evaluator of Vietnamese and English AI responses.

RUBRIC:
{rubric}

PROMPT:
{prompt}

REFERENCE NOTES (may be empty):
{reference}

RESPONSE A:
{a}

RESPONSE B:
{b}

Reply with JSON only: {{"winner": "A" | "B" | "tie", "reason": "<1-3 sentences in English>"}}"""


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def judge_once(prompt, ref, a, b, rubric, dry_run):
    if dry_run:
        return random.choice(["A", "B", "tie"]), "dry-run"
    from openai import OpenAI
    client = OpenAI(base_url=JUDGE["base_url"], api_key=os.environ.get(JUDGE["api_key_env"]))
    text = TEMPLATE.format(rubric=rubric, prompt=prompt, reference=ref, a=a, b=b)
    r = client.chat.completions.create(model=JUDGE["model"],
                                       messages=[{"role": "user", "content": text}])
    out = r.choices[0].message.content
    m = re.search(r"\{.*\}", out, re.S)
    try:
        d = json.loads(m.group(0))
        w = str(d.get("winner", "")).strip()
        return (w if w in ("A", "B", "tie") else "tie"), d.get("reason", "")
    except Exception:
        return "tie", f"unparseable: {out[:200]}"


def main():
    dry_run = "--dry-run" in sys.argv
    rubric = open("rubric.md", encoding="utf-8").read()
    rows = []
    for p in read_csv("pairs.csv"):
        print(p["pair_id"])
        w1, r1 = judge_once(p["prompt"], p["reference_answer"], p["response_a"], p["response_b"], rubric, dry_run)
        w2, _ = judge_once(p["prompt"], p["reference_answer"], p["response_b"], p["response_a"], rubric, dry_run)
        w2 = {"A": "B", "B": "A", "tie": "tie"}[w2]  # map swapped verdict back
        final = w1 if w1 == w2 else "tie"
        rows.append({"pair_id": p["pair_id"], "judge_winner": final,
                     "judge_consistent": w1 == w2, "judge_reason": r1})
    with open("judge_results.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("Saved judge_results.csv")


if __name__ == "__main__":
    main()
