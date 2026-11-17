"""Aggregate segments.csv to amudim and 8-segment passage windows; test the hypothesis on a labelled set.

Run: py -3.13 -I analyze.py   (after name_density.py)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
SEF = HERE.parent.parent / "talmud-names-discovery" / "sefaria"
WIN = 8  # segments per passage window

seg = pd.read_csv(OUT / "segments.csv", encoding="utf-8-sig", keep_default_na=False)
seg["daf"] = seg["amud"].str[:-1].astype(int)
seg["side"] = seg["amud"].str[-1]
seg["amud_ix"] = seg["daf"] * 2 + (seg["side"] == "b")
gem = seg[seg.is_mishna == 0].copy()

# ---- labelled aggadic passages (amud ranges, inclusive) + a keyword that must occur in the range ----
AGGADA = [
    ("Berakhot", "6a", "7b", "Yishmael ben Elisha"),
    ("Berakhot", "55a", "57b", "dream"),
    ("Shabbat", "30a", "30b", "Angel of Death"),
    ("Shabbat", "33b", "34a", "cave"),
    ("Shabbat", "88a", "89b", "Moses"),
    ("Yoma", "35b", "35b", "Hillel"),
    ("Sukkah", "51b", "52b", "evil inclination"),
    ("Taanit", "19b", "20a", "Nakdimon"),
    ("Taanit", "21a", "21a", "Naḥum of Gam Zu"),
    ("Taanit", "23a", "25a", "Ḥoni"),
    ("Megillah", "10b", "16b", "Ahasuerus"),
    ("Chagigah", "14b", "15b", "Aḥer"),
    ("Ketubot", "62b", "63a", "Akiva"),
    ("Ketubot", "103a", "104a", "Rabbi Yehuda HaNasi"),
    ("Sotah", "11a", "13b", "Pharaoh"),
    ("Gittin", "55b", "58a", "Kamtza"),
    ("Gittin", "68a", "68b", "Ashmedai"),
    ("Kiddushin", "66a", "66a", "Yannai"),
    ("Bava Metzia", "58b", "59b", "oven"),
    ("Bava Metzia", "83b", "86a", "Reish Lakish"),
    ("Bava Batra", "73a", "75b", "Rabba bar bar Ḥana"),
    ("Sanhedrin", "38a", "39b", "Adam"),
    ("Sanhedrin", "93a", "99a", "Messiah"),
    ("Sanhedrin", "101b", "103b", "Manasseh"),
    ("Sanhedrin", "104b", "106b", "Balaam"),
    ("Avodah Zarah", "10a", "11a", "Antoninus"),
    ("Avodah Zarah", "17a", "18b", "Durdayya"),
    ("Menachot", "29b", "29b", "Akiva"),
]


def amud_ix(a):
    return int(a[:-1]) * 2 + (a[-1] == "b")


seg["aggada_label"] = 0
problems = []
for tr, a1, a2, kw in AGGADA:
    m = (seg.tractate == tr) & seg.amud_ix.between(amud_ix(a1), amud_ix(a2))
    en = json.load(open(SEF / f"{tr.replace(' ', '_')}_en.json", encoding="utf-8"))["text"]
    i1, i2 = amud_ix(a1) - 2, amud_ix(a2) - 2  # Sefaria list index: 2a -> 2
    hit = sum(" ".join(en[i]).count(kw) for i in range(i1, i2 + 1))
    seg.loc[m, "aggada_label"] = 1
    problems.append((tr, a1, a2, kw, int(m.sum()), hit))
gem = seg[seg.is_mishna == 0].copy()


def rates(df, by):
    g = df.groupby(by, sort=False)
    s = g[["words_full", "words_bold", "words_he", "names_full", "names_bold", "distinct_full", "distinct_bold",
           "talmud_person_full", "bible_person_full", "generic_person_full", "place_full", "nation_full",
           "talmud_person_bold", "bible_person_bold", "generic_person_bold", "place_bold", "nation_bold",
           "verses", "stam_he", "narr_he", "aggada_label"]].sum()
    s["segments"] = g.size()
    s["aggada_label"] = (s["aggada_label"] / s["segments"]).round(2)
    s["names_per100_full"] = 100 * s.names_full / s.words_full.clip(lower=1)
    s["names_per100_bold"] = 100 * s.names_bold / s.words_bold.clip(lower=1)
    s["distinct_per100_full"] = 100 * s.distinct_full / s.words_full.clip(lower=1)
    s["nonsage_per100_full"] = 100 * (s.bible_person_full + s.generic_person_full + s.place_full + s.nation_full) \
        / s.words_full.clip(lower=1)
    s["talmud_person_per100_bold"] = 100 * s.talmud_person_bold / s.words_bold.clip(lower=1)
    s["stam_per100_he"] = 100 * s.stam_he / s.words_he.clip(lower=1)
    s["narr_per100_he"] = 100 * s.narr_he / s.words_he.clip(lower=1)
    s["verses_per100_full"] = 100 * s.verses / s.words_full.clip(lower=1)
    return s.reset_index()


def auc(score, label):
    """Mann-Whitney AUC: P(random positive scores higher than random negative)."""
    r = pd.Series(score).rank().values
    pos = label == 1
    n1, n0 = pos.sum(), (~pos).sum()
    return (r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


if __name__ == "__main__":
    print("Validation passages (rows, keyword found among matched names):")
    for p in problems:
        print("  ", p)

    am = rates(gem, ["tractate", "amud", "amud_ix"])
    am = am[am.words_full >= 150]
    am["label"] = (am.aggada_label >= 0.5).astype(int)

    # ---- passage windows: WIN consecutive Gemara segments within one tractate, step WIN/2 ----
    wins = []
    for tr, df in gem.groupby("tractate", sort=False):
        df = df.reset_index(drop=True)
        for st in range(0, max(len(df) - WIN + 1, 1), WIN // 2):
            w = df.iloc[st:st + WIN]
            first, last = w.iloc[0], w.iloc[-1]
            wins.append({"tractate": tr, "start": f"{first.amud}:{first.seg}", "end": f"{last.amud}:{last.seg}",
                         "win": st, **{k: w[k].sum() for k in
                                       ["words_full", "words_bold", "words_he", "names_full", "names_bold",
                                        "distinct_full", "talmud_person_full", "bible_person_full",
                                        "generic_person_full", "place_full", "nation_full", "talmud_person_bold",
                                        "verses", "stam_he", "narr_he"]},
                         "aggada_label": w.aggada_label.mean(),
                         "names": "; ".join(sorted({n for x in w.names_list for n in x.split("; ") if n}))})
    wn = pd.DataFrame(wins)
    wn["names_per100_full"] = 100 * wn.names_full / wn.words_full.clip(lower=1)
    wn["names_per100_bold"] = 100 * wn.names_bold / wn.words_bold.clip(lower=1)
    wn["distinct_per100_full"] = 100 * wn.distinct_full / wn.words_full.clip(lower=1)
    wn["nonsage_per100_full"] = 100 * (wn.bible_person_full + wn.generic_person_full + wn.place_full
                                       + wn.nation_full) / wn.words_full.clip(lower=1)
    wn["stam_per100_he"] = 100 * wn.stam_he / wn.words_he.clip(lower=1)
    wn["narr_per100_he"] = 100 * wn.narr_he / wn.words_he.clip(lower=1)
    wn["label"] = (wn.aggada_label >= 0.5).astype(int)

    feats = ["names_per100_full", "names_per100_bold", "distinct_per100_full", "nonsage_per100_full",
             "talmud_person_per100_bold", "verses_per100_full", "stam_per100_he", "narr_per100_he"]
    print(f"\nAmudim: {len(am)} (aggada-labelled {am.label.sum()})")
    for f in feats:
        print(f"  AUC {f:28s} {auc(am[f].values, am.label.values):.3f}   "
              f"median aggada {am[am.label == 1][f].median():.2f} / other {am[am.label == 0][f].median():.2f}")
    print(f"\nWindows: {len(wn)} (aggada-labelled {wn.label.sum()})")
    for f in [x for x in feats if x in wn]:
        print(f"  AUC {f:28s} {auc(wn[f].values, wn.label.values):.3f}")
    print("\nSpearman (amudim) names_per100_full vs stam_per100_he:",
          round(am.names_per100_full.corr(am.stam_per100_he, method="spearman"), 3),
          "| names_per100_bold vs stam:", round(am.names_per100_bold.corr(am.stam_per100_he, method="spearman"), 3),
          "| distinct_full vs stam:", round(am.distinct_per100_full.corr(am.stam_per100_he, method="spearman"), 3))
    am.to_csv(OUT / "amudim.csv", index=False, encoding="utf-8-sig")
    wn.to_csv(OUT / "windows.csv", index=False, encoding="utf-8-sig")
