"""Diagnose Ein Yaakov coverage: word counts, unmatched EY text, and why 4-grams fail."""
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from align_ein_yaakov import EY, NAME_MAP, SEF, flat, grams, skel_words, NIKUD, TAG  # noqa: E402

he_words = ey_words = 0
for tr in [NAME_MAP.get(k, k) for k in EY]:
    p = SEF / f"{tr}_he.json"
    if p.exists():
        he_words += sum(len(TAG.sub(" ", s).split()) for a in json.load(open(p, encoding="utf-8"))["text"] for s in a)
ey_words = sum(len(NIKUD.sub("", TAG.sub(" ", s)).split()) for v in EY.values() for s in flat(v))
print(f"Bavli Aramaic words (Sefaria): {he_words:,}   Ein Yaakov words (merged.json): {ey_words:,}   "
      f"ratio {ey_words / he_words:.1%}")

# per-tractate word ratio
for k in ["Berakhot", "Bava Kamma", "Zevakhim"]:
    tr = NAME_MAP.get(k, k)
    b = sum(len(s.split()) for a in json.load(open(SEF / f"{tr}_he.json", encoding="utf-8"))["text"] for s in a)
    e = sum(len(NIKUD.sub("", TAG.sub(" ", s)).split()) for s in flat(EY[k]))
    print(f"  {k}: EY/Bavli words {e / b:.1%}")

# what share of EY 4-grams exist anywhere in the same Bavli tractate?
k = "Berakhot"
bav = set()
for a in json.load(open(SEF / "Berakhot_he.json", encoding="utf-8"))["text"]:
    for s in a:
        bav.update(grams(skel_words(s)))
eyg = [g for s in flat(EY[k]) for g in grams(skel_words(s))]
print(f"\nBerakhot: share of EY 4-grams found in Bavli Berakhot: {sum(g in bav for g in eyg) / len(eyg):.1%}")
# sample of EY words that are not in the Bavli vocabulary
bvoc = Counter(w for a in json.load(open(SEF / "Berakhot_he.json", encoding="utf-8"))["text"] for s in a
               for w in skel_words(s))
eyw = [w for s in flat(EY[k]) for w in skel_words(s)]
miss = Counter(w for w in eyw if w not in bvoc)
print("EY word tokens not in Bavli Berakhot vocabulary:", f"{sum(miss.values()) / len(eyw):.1%}")
print("most common:", miss.most_common(40))
random.seed(1)
s = random.choice([x for x in flat(EY[k]) if len(x) > 400])
print("\nSample EY passage (raw):\n", s[:700])
