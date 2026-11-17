"""Third pass: Steinsaltz voice labels ("The Gemara asks", "The baraita ...") per amud, vs name density."""
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
SEF = HERE.parent / "talmud-names-discovery" / "sefaria"
OUT = HERE / "out"
am = pd.read_csv(OUT / "amudim.csv", encoding="utf-8-sig")
GEM = re.compile(r"The Gemara (?:asks|answers|explains|rejects|raises|challenges|suggests|clarifies|resolves|"
                 r"refutes|notes|cites|concludes|infers|questions|attempts|proves|objects)")
BAR = re.compile(r"(?:The|that|a|this) (?:baraita|Tosefta|tanna)\b")
REL = re.compile(r"The Gemara (?:relates|recounts|tells)")

rows = []
for tr in am.tractate.unique():
    en = json.load(open(SEF / f"{tr.replace(' ', '_')}_en.json", encoding="utf-8"))["text"]
    for ai, amud in enumerate(en):
        if not amud:
            continue
        txt = re.sub(r"<[^>]+>", "", " ".join(amud))
        rows.append({"tractate": tr, "amud": f"{ai // 2 + 1}{'ab'[ai % 2]}", "gem_labels": len(GEM.findall(txt)),
                     "baraita_refs": len(BAR.findall(txt)), "relates": len(REL.findall(txt))})
lab = pd.DataFrame(rows)
am = am.merge(lab, on=["tractate", "amud"], how="left")
for c in ["gem_labels", "baraita_refs", "relates"]:
    am[c + "_per_seg"] = am[c] / am.segments

am["dec"] = pd.qcut(am.names_per100_full.rank(method="first"), 10, labels=range(1, 11))
t = am.groupby("dec", observed=True).agg(names=("names_per100_full", "median"),
                                          stam_he=("stam_per100_he", "mean"),
                                          gemara_labels=("gem_labels_per_seg", "mean"),
                                          baraita=("baraita_refs_per_seg", "mean"),
                                          relates=("relates_per_seg", "mean"),
                                          aggada_share=("label", "mean"))
print("Amudim by decile of name density (full English): means")
print(t.round(3).to_string())
print("\nSpearman with names_per100_full:")
for c in ["stam_per100_he", "gem_labels_per_seg", "baraita_refs_per_seg", "relates_per_seg"]:
    print(f"  {c:22s} {am.names_per100_full.corr(am[c], method='spearman'):+.3f}   "
          f"with nonsage {am.nonsage_per100_full.corr(am[c], method='spearman'):+.3f}   "
          f"with sage-only {(100 * am.talmud_person_full / am.words_full).corr(am[c], method='spearman'):+.3f}")
am.to_csv(OUT / "amudim.csv", index=False, encoding="utf-8-sig")
