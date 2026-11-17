"""Write the deliverable CSVs with Sefaria + Bekiut links. Run after analyze.py, analyze2.py, analyze3.py."""
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent / "out"


def links(tr, start, end):
    t = tr.replace(" ", "_")
    a1, s1 = start.split(":")
    a2, s2 = end.split(":")
    rng = f"{a1}.{s1}-{s2}" if a1 == a2 else f"{a1}.{s1}-{a2}.{s2}"
    ref = f"{tr} {start}–{end}" if a1 != a2 else f"{tr} {a1}:{s1}–{s2}"
    return ref, f"https://www.sefaria.org/{t}.{rng}", f"https://bekiut.com/talmud/{t}/{a1}#{s1}"


def write(src, dst, n):
    df = pd.read_csv(OUT / src, encoding="utf-8-sig", keep_default_na=False).head(n)
    rows = []
    for i, r in enumerate(df.itertuples(), 1):
        ref, sef, bek = links(r.tractate, r.start, r.end)
        rows.append({"rank": i, "ref": ref, "sefaria_url": sef, "bekiut_url": bek,
                     "in_validation_set": "yes" if r.label else "",
                     "names_per100w": round(r.names_per100_full, 2),
                     "nonsage_names_per100w": round(r.nonsage_per100_full, 2),
                     "stam_markers_per100w_aramaic": round(r.stam_per100_he, 2),
                     "words_en": r.words_full, "names_found": r.names})
    pd.DataFrame(rows).to_csv(OUT / dst, index=False, encoding="utf-8-sig")
    print(dst, len(rows))


write("top_passages_nonsage.csv", "TOP_aggada_candidates_by_nonsage_names.csv", 60)
write("top_passages_allnames.csv", "TOP_passages_by_all_names.csv", 60)
write("lowest_passages.csv", "LOWEST_name_density_passages.csv", 40)

am = pd.read_csv(OUT / "amudim.csv", encoding="utf-8-sig")
am["sefaria_url"] = "https://www.sefaria.org/" + am.tractate.str.replace(" ", "_") + "." + am.amud
keep = ["tractate", "amud", "sefaria_url", "segments", "words_full", "names_full", "names_per100_full",
        "nonsage_per100_full", "talmud_person_full", "bible_person_full", "generic_person_full", "place_full",
        "nation_full", "verses_per100_full", "stam_per100_he", "gem_labels_per_seg", "relates_per_seg", "label"]
am[keep].rename(columns={"label": "in_validation_set"}).round(3) \
    .to_csv(OUT / "ALL_amudim_name_density.csv", index=False, encoding="utf-8-sig")
print("ALL_amudim_name_density.csv", len(am))
