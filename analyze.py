"""
Step 5: compute results.

Needs: pairs.csv (with human_winner filled in: A / B / tie),
       pairs_key.csv, judge_results.csv (optional)

Usage:
    pip install pandas scikit-learn
    python analyze.py

Output: results.md
"""
import os
import pandas as pd
from sklearn.metrics import cohen_kappa_score


def md_table(df):
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return "\n".join(lines)


def win_rates(df, winner_col):
    rec = []
    for _, r in df.iterrows():
        w = r[winner_col]
        for side, model in (("A", r.model_a), ("B", r.model_b)):
            score = 0.5 if w == "tie" else (1.0 if w == side else 0.0)
            rec.append({"model": model, "category": r.category, "score": score})
    s = pd.DataFrame(rec)
    overall = (s.groupby("model")["score"].agg(["mean", "count"])
                .rename(columns={"mean": "win_rate", "count": "comparisons"})
                .sort_values("win_rate", ascending=False).reset_index())
    overall["win_rate"] = (overall["win_rate"] * 100).round(1).astype(str) + "%"
    by_cat = (s.pivot_table(index="category", columns="model", values="score", aggfunc="mean")
               .mul(100).round(0).astype(int).astype(str).add("%").reset_index())
    return overall, by_cat


def main():
    pairs = pd.read_csv("pairs.csv", encoding="utf-8-sig")
    key = pd.read_csv("pairs_key.csv", encoding="utf-8-sig")
    df = pairs.merge(key, on="pair_id")
    df["human_winner"] = df["human_winner"].astype(str).str.strip().replace({"Tie": "tie", "TIE": "tie"})
    df = df[df["human_winner"].isin(["A", "B", "tie"])]
    if df.empty:
        raise SystemExit("No annotated pairs yet: fill human_winner with A / B / tie in pairs.csv")

    out = ["# Results", "", f"Annotated pairs: {len(df)}", ""]
    overall, by_cat = win_rates(df, "human_winner")
    out += ["## Human preference: overall win rate (tie = 0.5)", "", md_table(overall), "",
            "## Human preference: win rate by category", "", md_table(by_cat), ""]

    if os.path.exists("judge_results.csv"):
        j = pd.read_csv("judge_results.csv", encoding="utf-8-sig")
        df = df.merge(j, on="pair_id")
        agree = (df.human_winner == df.judge_winner).mean()
        kappa = cohen_kappa_score(df.human_winner, df.judge_winner)
        consistent = df.judge_consistent.astype(str).str.lower().eq("true").mean()
        conf = pd.crosstab(df.human_winner, df.judge_winner).reset_index()
        conf.columns = ["human \\ judge"] + list(conf.columns[1:])
        out += ["## Human vs LLM judge", "",
                f"- Raw agreement: {agree:.1%}",
                f"- Cohen's kappa: {kappa:.2f}",
                f"- Judge position consistency (same verdict when A/B swapped): {consistent:.1%}", "",
                md_table(conf), ""]
        dis = df[df.human_winner != df.judge_winner][["pair_id", "category", "human_winner", "judge_winner", "human_reason", "judge_reason"]]
        dis.to_csv("disagreements.csv", index=False, encoding="utf-8-sig")
        out.append(f"Disagreements saved to disagreements.csv ({len(dis)} pairs). Read them: they are the best material for your write-up.")

    with open("results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
