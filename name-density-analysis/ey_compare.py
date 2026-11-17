"""Compare name / verse proxies with Ein Yaakov's selection of aggadic passages.

Label: a Gemara segment is 'Ein Yaakov' if >= 50% of its Aramaic 4-grams occur in Ein Yaakov (align_ein_yaakov.py).
Scores: densities per 100 English words, raw (segment) and smoothed over a centred window of segments.
Classifier: logistic regression (numpy), leave-one-tractate-out, on smoothed log features.

Run: py -3.13 -I ey_compare.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent / "out"
seg = pd.read_csv(OUT / "segments.csv", encoding="utf-8-sig", keep_default_na=False)
cov = pd.read_csv(OUT.parent.parent / "out" / "ey_segment_coverage.csv", encoding="utf-8-sig")
df = seg.merge(cov, on=["tractate", "amud", "seg"], how="left")
f2 = pd.read_csv(OUT / "segments_feat2.csv", encoding="utf-8-sig")
df = df.merge(f2, on=["tractate", "amud", "seg"], how="left")
df = df[(df.is_mishna == 0)].reset_index(drop=True)
EY_TH = 0.4
df["ey"] = (df.ey_coverage >= EY_TH).astype(int)
df["evaluable"] = df.he_4grams >= 5

W = df.words_full.clip(lower=1)
raw = {
    "bible_person": df.bible_person_full,
    "verses": df.verses,
    "bible_person+verses": df.bible_person_full + df.verses,
    "nonsage_names": df.bible_person_full + df.place_full + df.nation_full + df.generic_person_full,
    "nonsage+verses": df.bible_person_full + df.place_full + df.nation_full + df.generic_person_full + df.verses,
    "place+nation+generic": df.place_full + df.nation_full + df.generic_person_full,
    "all_names": df.names_full,
    "sage_names": df.talmud_person_full,
    "stam_markers_he": df.stam_he,
    "narrative_markers_he": df.narr_he_x,
    "med_he": df.med_he, "med_en": df.med_en, "narr2_he": df.narr_he_y, "narr_en": df.narr_en,
    "dialogue_he": df.dial_he, "law_he": df.law_he, "law_en": df.law_en,
}
denom_he = df.words_he.clip(lower=1)


def auc(score, label):
    r = pd.Series(score).rank().values
    pos = label == 1
    n1, n0 = pos.sum(), (~pos).sum()
    return (r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def smooth(counts, denom, k):
    """Sum counts and words over a centred window of 2k+1 segments inside each tractate."""
    if k == 0:
        return 100 * counts / denom
    num = counts.groupby(df.tractate).transform(lambda s: s.rolling(2 * k + 1, center=True, min_periods=1).sum())
    den = denom.groupby(df.tractate).transform(lambda s: s.rolling(2 * k + 1, center=True, min_periods=1).sum())
    return 100 * num / den


ev = df.evaluable.values
y = df.ey.values
print(f"Gemara segments: {len(df)}, evaluable: {ev.sum()}, Ein Yaakov: {y[ev].sum()} ({y[ev].mean():.1%})\n")
print(f"{'feature':24s}" + "".join(f"  k={k:<4d}" for k in (0, 2, 4, 8)) + "   (AUC vs Ein Yaakov; k = +/- segments)")
sm = {}
for name, c in raw.items():
    d = denom_he if name.endswith("_he") else W
    line = f"{name:24s}"
    for k in (0, 2, 4, 8):
        s = smooth(c.astype(float), d.astype(float), k)
        sm[(name, k)] = s
        line += f"  {auc(s.values[ev], y[ev]):.3f} "
    print(line)

# ---- logistic regression, leave-one-tractate-out ----
K = 4
feat_names = ["bible_person", "verses", "place+nation+generic", "sage_names", "stam_markers_he", "narrative_markers_he"]


def design(names):
    X = np.column_stack([np.log1p(sm[(n, K)].values) for n in names] + [np.log1p(sm[(n, 0)].values) for n in names])
    return (X - X.mean(0)) / X.std(0)


def fit(X, y, l2=1.0, it=400, lr=0.5):
    X1 = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(X1.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-X1 @ w))
        g = X1.T @ (p - y) / len(y) + l2 * np.r_[0, w[1:]] / len(y)
        w -= lr * g
    return w


def cv(names):
    X = design(names)
    pred = np.zeros(len(df))
    for tr in df.tractate.unique():
        te = (df.tractate == tr).values
        trn = ~te & ev
        w = fit(X[trn], y[trn])
        pred[te] = 1 / (1 + np.exp(-(np.column_stack([np.ones(te.sum()), X[te]]) @ w)))
    return pred


results = {}
for label, names in [("verses only", ["verses"]),
                     ("bible persons + verses", ["bible_person", "verses"]),
                     ("all name groups + verses", ["bible_person", "verses", "place+nation+generic", "sage_names"]),
                     ("+ Aramaic stam/narrative markers", feat_names),
                     ("+ set 2: medicine, narrative, dialogue, law", feat_names + ["med_he", "med_en", "narr2_he",
                                                                         "narr_en", "dialogue_he", "law_he", "law_en"]),
                     ("set 2 + stam only (no names, no verses)", ["med_he", "med_en", "narr2_he", "narr_en",
                                                                  "dialogue_he", "law_he", "law_en", "stam_markers_he"])]:
    p = cv(names)
    results[label] = p
    # best-F1 threshold
    best = max(((f1, t) for t in np.linspace(0.05, 0.95, 91)
                for f1 in [2 * ((p[ev] >= t) & (y[ev] == 1)).sum() /
                           max((p[ev] >= t).sum() + y[ev].sum(), 1)]))
    t = best[1]
    yp = (p[ev] >= t).astype(int)
    tp, fp, fn = ((yp == 1) & (y[ev] == 1)).sum(), ((yp == 1) & (y[ev] == 0)).sum(), ((yp == 0) & (y[ev] == 1)).sum()
    acc = (yp == y[ev]).mean()
    pe = y[ev].mean() * yp.mean() + (1 - y[ev].mean()) * (1 - yp.mean())
    print(f"\nLOTO logistic [{label}]: AUC {auc(p[ev], y[ev]):.3f}  best F1 {best[0]:.3f} at p>={t:.2f}  "
          f"precision {tp / (tp + fp):.3f} recall {tp / (tp + fn):.3f} accuracy {acc:.3f} kappa {(acc - pe) / (1 - pe):.3f}")

df["p_aggada"] = results["+ Aramaic stam/narrative markers"]
df["p_full"] = results["+ set 2: medicine, narrative, dialogue, law"]
df["p_names_verses"] = results["all name groups + verses"]
for k in ("bible_person", "verses", "nonsage_names", "sage_names", "stam_markers_he", "med_he", "med_en", "narr2_he", "law_he", "law_en"):
    df[f"{k}_sm{K}"] = sm[(k, K)]

# ---- per tractate: Ein Yaakov share vs predicted share ----
g = df[df.evaluable].groupby("tractate", sort=False).agg(ey_share=("ey", "mean"), pred_share=("p_names_verses", "mean"), pred_full=("p_full", "mean"),
                                                         n=("ey", "size"))
print("\nPer tractate, share of Gemara segments: Ein Yaakov vs model (names+verses) mean probability")
print(g.round(3).sort_values("ey_share", ascending=False).to_string())
print("Spearman across tractates:", round(g.ey_share.corr(g.pred_share, method="spearman"), 3), "| full model:", round(g.ey_share.corr(g.pred_full, method="spearman"), 3))
df.to_csv(OUT / "segments_ey.csv", index=False, encoding="utf-8-sig")
