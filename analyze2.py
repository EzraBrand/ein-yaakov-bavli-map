"""Second pass: per-category AUC, Stam-vs-names deciles, ranked passages. Run after analyze.py."""
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent / "out"
am = pd.read_csv(OUT / "amudim.csv", encoding="utf-8-sig")
wn = pd.read_csv(OUT / "windows.csv", encoding="utf-8-sig", keep_default_na=False)


def auc(score, label):
    r = pd.Series(score).rank().values
    pos = label == 1
    n1, n0 = pos.sum(), (~pos).sum()
    return (r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


print("Per-category AUC (amudim, full English, per 100 words):")
for c in ["talmud_person", "bible_person", "generic_person", "place", "nation"]:
    f = 100 * am[f"{c}_full"] / am.words_full
    print(f"  {c:16s} {auc(f.values, am.label.values):.3f}  median aggada {f[am.label == 1].median():.2f} "
          f"/ other {f[am.label == 0].median():.2f}")

# does a 'non-sage names' score still work once Bible verses are taken out?
am["nonsage_minus_bible"] = 100 * (am.generic_person_full + am.place_full + am.nation_full) / am.words_full
print(f"  generic+place+nation (no Bible persons) {auc(am.nonsage_minus_bible.values, am.label.values):.3f}")

print("\nStam side: amudim by decile of names_per100_full -> median Stam markers per 100 Aramaic words")
am["dec"] = pd.qcut(am.names_per100_full.rank(method="first"), 10, labels=range(1, 11))
t = am.groupby("dec", observed=True).agg(names=("names_per100_full", "median"),
                                          stam=("stam_per100_he", "median"),
                                          nonsage=("nonsage_per100_full", "median"),
                                          aggada_share=("label", "mean"), n=("label", "size"))
print(t.round(2).to_string())

am["dec_ns"] = pd.qcut(am.nonsage_per100_full.rank(method="first"), 10, labels=range(1, 11))
t2 = am.groupby("dec_ns", observed=True).agg(nonsage=("nonsage_per100_full", "median"),
                                              stam=("stam_per100_he", "median"),
                                              aggada_share=("label", "mean"))
print("\n...by decile of non-sage names:")
print(t2.round(2).to_string())

zero = am[am.names_full <= 2]
print(f"\nAmudim with <=2 names (full English): {len(zero)}; median Stam {zero.stam_per100_he.median():.2f} "
      f"vs all {am.stam_per100_he.median():.2f}")

# ---- ranked passages: greedy non-overlapping windows ----
def top(df, key, n, asc=False):
    df = df.sort_values(key, ascending=asc)
    used, keep = set(), []
    for _, r in df.iterrows():
        k = (r.tractate, r.win)
        if any((r.tractate, r.win + d) in used for d in range(-7, 8)):
            continue
        used.add(k)
        keep.append(r)
        if len(keep) == n:
            break
    return pd.DataFrame(keep)


wn = wn[wn.words_full >= 300]
best = top(wn, "nonsage_per100_full", 60)
print("\nTop 60 passages by non-sage name density (label = in my aggada set):")
for _, r in best.iterrows():
    print(f"  {r.tractate} {r.start}-{r.end}  nonsage {r.nonsage_per100_full:.1f}  all {r.names_per100_full:.1f}  "
          f"stam {r.stam_per100_he:.2f}  lab {r.label}  | {r.names[:110]}")
best.to_csv(OUT / "top_passages_nonsage.csv", index=False, encoding="utf-8-sig")
best2 = top(wn, "names_per100_full", 60)
best2.to_csv(OUT / "top_passages_allnames.csv", index=False, encoding="utf-8-sig")
low = top(wn[wn.words_he >= 150], "names_per100_full", 40, asc=True)
print("\nLowest 25 name-density passages:")
for _, r in low.head(25).iterrows():
    print(f"  {r.tractate} {r.start}-{r.end}  names {r.names_per100_full:.2f}  stam {r.stam_per100_he:.2f} | {r.names[:80]}")
low.to_csv(OUT / "lowest_passages.csv", index=False, encoding="utf-8-sig")
