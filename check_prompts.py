"""
Step 1 check: run this every time you edit prompts.csv.

Usage:
    python check_prompts.py

It reports ERRORS (must fix) and WARNINGS (worth a look).
"""
import csv
import sys
from collections import Counter

FILE = "prompts.csv"
REQUIRED = ["id", "category", "prompt", "reference_answer", "notes"]
TARGET_PER_CATEGORY = (4, 12)  # min, max you aim for per category


def main():
    try:
        with open(FILE, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            cols = reader.fieldnames or []
            rows = list(reader)
    except UnicodeDecodeError:
        print("ERROR: file is not UTF-8. In Excel use 'Save As > CSV UTF-8'; in Google Sheets download as CSV.")
        sys.exit(1)

    errors, warnings = [], []
    missing_cols = [c for c in REQUIRED if c not in cols]
    if missing_cols:
        print(f"ERROR: missing columns {missing_cols}. Header must be: {','.join(REQUIRED)}")
        sys.exit(1)

    ids = Counter(r["id"].strip() for r in rows)
    for i, n in ids.items():
        if n > 1:
            errors.append(f"id '{i}' is used {n} times")
    prompts = Counter(r["prompt"].strip().lower() for r in rows)
    for p, n in prompts.items():
        if n > 1 and p:
            errors.append(f"same prompt appears {n} times: '{p[:50]}...'")

    for line, r in enumerate(rows, start=2):  # line 1 = header
        rid = r["id"].strip() or f"(line {line})"
        if not r["id"].strip():
            errors.append(f"line {line}: empty id")
        if not r["category"].strip():
            errors.append(f"{rid}: empty category")
        if not r["prompt"].strip():
            errors.append(f"{rid}: empty prompt")
        if not r["reference_answer"].strip():
            errors.append(f"{rid}: empty reference_answer (write the answer or grading criteria BEFORE asking the models)")
        elif len(r["reference_answer"].strip()) < 10:
            warnings.append(f"{rid}: reference_answer is very short; add how you got it or what to check")
        if len(r["prompt"].strip()) < 25:
            warnings.append(f"{rid}: prompt is very short; is it too easy?")
        if not r["notes"].strip():
            warnings.append(f"{rid}: no note on the trap; what is this prompt trying to catch?")

    cats = Counter(r["category"].strip() for r in rows if r["category"].strip())
    lo, hi = TARGET_PER_CATEGORY
    for c, n in sorted(cats.items()):
        if n < lo:
            warnings.append(f"category '{c}' has only {n} prompts (aim for {lo}-{hi})")
        elif n > hi:
            warnings.append(f"category '{c}' has {n} prompts (more than {hi}; other categories may be thin)")

    print(f"{len(rows)} prompts in {len(cats)} categories:")
    for c, n in sorted(cats.items()):
        print(f"  {c:<24}{n}")
    print()
    for e in errors:
        print("ERROR:  ", e)
    for w in warnings:
        print("WARNING:", w)
    if not errors and not warnings:
        print("All good.")
    elif not errors:
        print("\nNo errors. Warnings are optional to fix.")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
