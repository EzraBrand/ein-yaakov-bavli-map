"""Check whether given Bavli amudim are in Ein Yaakov: per-segment coverage, loose 3-gram search over ALL of
Ein Yaakov, and the neighbouring Ein Yaakov passages.  Usage: py -3.13 -I check_omission.py Berakhot 44b ..."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from align_ein_yaakov import EY, NAME_MAP, NIKUD, SEF, TAG, flat, skel_words  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"
seg = pd.read_csv(OUT / "bavli_segments_ein_yaakov.csv", encoding="utf-8-sig", keep_default_na=False)
eng = pd.read_csv(OUT / "segments.csv", encoding="utf-8-sig", keep_default_na=False, usecols=["ref", "is_mishna"])
# all of Ein Yaakov as one 3-gram set, with the passage of each 3-gram
where = {}
for k, chs in EY.items():
    for ci, ch in enumerate(chs):
        for pi, p in enumerate(ch):
            w = skel_words(" ".join(flat(p)))
            for i in range(len(w) - 2):
                where.setdefault(" ".join(w[i:i + 3]), f"{k} {ci + 1}:{pi + 1}")

args = sys.argv[1:]
for tr, am in zip(args[::2], args[1::2]):
    trf = tr.replace(" ", "_")
    he = json.load(open(SEF / f"{trf}_he.json", encoding="utf-8"))["text"]
    d = int(am[:-1])
    ai = 2 * (d - 1) + (am[-1] == "b")
    en = json.load(open(SEF / f"{trf}_en.json", encoding="utf-8"))["text"][ai]
    print(f"\n===== {tr.replace('_', ' ')} {am} =====")
    for si, s in enumerate(he[ai]):
        w = skel_words(s)
        g3 = [" ".join(w[i:i + 3]) for i in range(len(w) - 2)]
        hits = [where[x] for x in g3 if x in where]
        top = pd.Series(hits).value_counts().head(1)
        r = seg[(seg.tractate == tr.replace("_", " ")) & (seg.amud == am) & (seg.seg == si + 1)]
        cov = r.ey_coverage.iloc[0] if len(r) else ""
        ref = r.ey_ref.iloc[0] if len(r) else ""
        eng_txt = TAG.sub("", en[si])[:85] if si < len(en) else ""
        print(f"{am}:{si + 1:<3} cov4={cov!s:5} loose3={len(hits) / max(len(g3), 1):.2f} "
              f"best={top.index[0] if len(top) else '-':20s} {ref:28s} | {eng_txt}")
