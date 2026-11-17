"""List passages where the names+verses model and Ein Yaakov disagree (8-segment windows, non-overlapping)."""
import html
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
SEF = HERE.parent / "talmud-names-discovery" / "sefaria"
df = pd.read_csv(OUT / "segments_ey.csv", encoding="utf-8-sig", keep_default_na=False)
df = df[df.evaluable.astype(str) == "True"].reset_index(drop=True)
WIN = 8
_cache = {}


def text(tr, amud, seg):
    if tr not in _cache:
        _cache[tr] = json.load(open(SEF / f"{tr.replace(' ', '_')}_en.json", encoding="utf-8"))["text"]
    d, s = int(amud[:-1]), amud[-1]
    t = _cache[tr][2 * (d - 1) + (s == "b")][seg - 1]
    return html.unescape(re.sub(r"<[^>]+>", "", t))


rows = []
for tr, g in df.groupby("tractate", sort=False):
    g = g.reset_index(drop=True)
    for st in range(0, max(len(g) - WIN + 1, 1), WIN // 2):
        w = g.iloc[st:st + WIN]
        a, b = w.iloc[0], w.iloc[-1]
        rows.append({"tractate": tr, "win": st, "start": f"{a.amud}:{a.seg}", "end": f"{b.amud}:{b.seg}",
                     "ey_share": w.ey.mean(), "p": w.p_names_verses.mean(),
                     "bible": w.bible_person_full.sum(), "verses": w.verses.sum(), "sage": w.talmud_person_full.sum(),
                     "places_etc": (w.place_full + w.nation_full + w.generic_person_full).sum(),
                     "stam": w.stam_he.sum(), "words": w.words_full.sum(),
                     "first_text": text(tr, a.amud, int(a.seg))[:160]})
wn = pd.DataFrame(rows)


def pick(d, key, asc, n):
    d = d.sort_values(key, ascending=asc)
    used, keep = set(), []
    for _, r in d.iterrows():
        if any((r.tractate, r.win + k) in used for k in range(-7, 8)):
            continue
        used.add((r.tractate, r.win))
        keep.append(r)
        if len(keep) == n:
            break
    return pd.DataFrame(keep)


fp = pick(wn[wn.ey_share == 0], "p", False, 40)
fn = pick(wn[wn.ey_share == 1], "p", True, 40)
for title, d in (("HIGH model score, NOT in Ein Yaakov", fp), ("IN Ein Yaakov, LOW model score", fn)):
    print(f"\n=== {title} ===")
    for _, r in d.iterrows():
        print(f"{r.tractate} {r.start}-{r.end} p={r.p:.2f} bible={r.bible} verses={r.verses} sage={r.sage} "
              f"oth={r.places_etc} stam={r.stam} | {r.first_text[:130]}")
fp.to_csv(OUT / "disagree_model_yes_ey_no.csv", index=False, encoding="utf-8-sig")
fn.to_csv(OUT / "disagree_ey_yes_model_no.csv", index=False, encoding="utf-8-sig")

# order (seder) breakdown of false positives among the top 200 windows
SEDER = {"Zevachim": "Kodashim", "Menachot": "Kodashim", "Chullin": "Kodashim", "Bekhorot": "Kodashim",
         "Arakhin": "Kodashim", "Temurah": "Kodashim", "Keritot": "Kodashim", "Meilah": "Kodashim",
         "Tamid": "Kodashim", "Niddah": "Taharot"}
top = pick(wn, "p", False, 300)
top["seder"] = top.tractate.map(SEDER).fillna("other")
print("\nTop 300 model windows: share in Ein Yaakov (>=50% of segments), by seder")
print(top.groupby("seder").apply(lambda d: pd.Series({"n": len(d), "in_EY": (d.ey_share >= .5).mean()})).round(2))
