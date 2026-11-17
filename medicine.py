"""Narrow medicine/remedy score; top medicine passages and whether Ein Yaakov includes them.

Output: out/medicine_passages.csv
Run: py -3.13 -I medicine.py  (after ey_compare.py)
"""
import html
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
SEF = HERE.parent / "talmud-names-discovery" / "sefaria"
OUT = HERE / "out"
TAG = re.compile(r"<[^>]+>")
# narrow: remedy vocabulary only (no plain food/drink words)
MED_EN = re.compile(r"\b(?:remed(?:y|ies)|cure[sd]?|heal(?:s|ed|ing)?|illness|sick|fever|physician|doctor|"
                    r"disease|ailment|harmful to|beneficial for|good for|bad for|bloodletting|let blood|demons?|"
                    r"evil spirit|incantation|amulet|swelling|wound|blindness|intestin\w*|spleen|kidneys?)\b", re.I)
MED_HE = re.compile(r"(?<![א-ת])[ודהבלכמש]{0,2}(?:סמא|סמנא|אסותא|רפואה|רפואת|מעלי|קשה ל|קשין ל|"
                    r"צמרמורתא|אישתא|שדא|שידא|שדים|מזיקין|לחש|קמיע|דם|כוליא|טחול|מעיא|ליתי|לייתי|לישתי)"
                    r"(?![א-ת])")

rows = []
for p in sorted(SEF.glob("*_en.json")):
    tr = p.name[:-8]
    en = json.load(open(p, encoding="utf-8"))["text"]
    he = json.load(open(SEF / f"{tr}_he.json", encoding="utf-8"))["text"]
    for ai, amud in enumerate(en):
        for si, raw in enumerate(amud):
            if raw:
                e = html.unescape(TAG.sub(" ", raw))
                h = TAG.sub(" ", he[ai][si]) if ai < len(he) and si < len(he[ai]) else ""
                rows.append({"tractate": tr.replace("_", " "), "amud": f"{ai // 2 + 1}{'ab'[ai % 2]}", "seg": si + 1,
                             "med_n_en": len(MED_EN.findall(e)), "med_n_he": len(MED_HE.findall(h)),
                             "text": e[:150]})
m = pd.DataFrame(rows)
seg = pd.read_csv(OUT / "segments_ey.csv", encoding="utf-8-sig", keep_default_na=False,
                  usecols=["tractate", "amud", "seg", "ey", "words_full", "words_he", "p_full", "evaluable"])
df = seg.merge(m, on=["tractate", "amud", "seg"])
df = df[df.evaluable.astype(str) == "True"].reset_index(drop=True)

WIN = 8
wins = []
for tr, g in df.groupby("tractate", sort=False):
    g = g.reset_index(drop=True)
    for st in range(0, max(len(g) - WIN + 1, 1), WIN // 2):
        w = g.iloc[st:st + WIN]
        wins.append({"tractate": tr, "win": st, "start": f"{w.iloc[0].amud}:{w.iloc[0].seg}",
                     "end": f"{w.iloc[-1].amud}:{w.iloc[-1].seg}",
                     "med_per100": 100 * (w.med_n_en.sum() + w.med_n_he.sum()) / (w.words_full.sum() + w.words_he.sum()),
                     "ey_share": w.ey.mean(), "model_p": w.p_full.mean(), "first_text": w.iloc[0].text})
wn = pd.DataFrame(wins).sort_values("med_per100", ascending=False)
used, keep = set(), []
for _, r in wn.iterrows():
    if any((r.tractate, r.win + k) in used for k in range(-7, 8)):
        continue
    used.add((r.tractate, r.win))
    keep.append(r)
    if len(keep) == 50:
        break
top = pd.DataFrame(keep)
top["sefaria_url"] = ("https://www.sefaria.org/" + top.tractate.str.replace(" ", "_") + "."
                      + top.start.str.replace(":", ".") + "-" + top.end.str.replace(":", "."))
top.round(3).to_csv(OUT / "medicine_passages.csv", index=False, encoding="utf-8-sig")
print(f"Top 50 medicine passages: in Ein Yaakov (>=50% of segments) {(top.ey_share >= .5).mean():.0%}, "
      f"partly (>0) {(top.ey_share > 0).mean():.0%}; model p>=0.31 {(top.model_p >= .31).mean():.0%}")
for _, r in top.head(50).iterrows():
    print(f"{r.tractate} {r.start}-{r.end} med {r.med_per100:.1f} EY {r.ey_share:.2f} model {r.model_p:.2f} | "
          f"{r.first_text[:95]}")
