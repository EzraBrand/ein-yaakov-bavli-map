"""Amud-level table: Ein Yaakov share vs the names+verses model; plus a recall breakdown of what the model misses."""
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent / "out"
df = pd.read_csv(OUT / "segments_ey.csv", encoding="utf-8-sig", keep_default_na=False)
df = df[df.evaluable.astype(str) == "True"]
T = 0.27  # best-F1 threshold, names+verses model (ey_compare.py, EY cut-off 0.4)
TF = 0.31  # best-F1 threshold, full model with set 2

g = df.groupby(["tractate", "amud"], sort=False).agg(
    segments=("ey", "size"), ein_yaakov_share=("ey", "mean"), model_mean_p=("p_names_verses", "mean"), full_model_mean_p=("p_full", "mean"),
    model_share=("p_names_verses", lambda s: (s >= T).mean()), bible_persons=("bible_person_full", "sum"),
    verses=("verses", "sum"), sage_names=("talmud_person_full", "sum"), stam_markers=("stam_he", "sum")).reset_index()
g.insert(2, "sefaria_url", "https://www.sefaria.org/" + g.tractate.str.replace(" ", "_") + "." + g.amud)
g.round(3).to_csv(OUT / "ALL_amudim_ein_yaakov_vs_model.csv", index=False, encoding="utf-8-sig")
print("amudim:", len(g), " Spearman EY share vs model share:",
      round(g.ein_yaakov_share.corr(g.model_mean_p, method="spearman"), 3))

ey = df[df.ey == 1].copy()
ey["no_bible_ctx"] = (ey.bible_person_sm4 == 0) & (ey.verses == 0)
ey["hit"] = ey.p_names_verses >= T
print(f"\nEin Yaakov segments: {len(ey)}; found by model: {ey.hit.mean():.1%}")
print(f"  with a biblical name or verse in the segment: {(~ey.no_bible_ctx).mean():.1%} of EY segments, "
      f"model recall there {ey[~ey.no_bible_ctx].hit.mean():.1%}")
print(f"  with no biblical name in +/-4 segments and no verse: {ey.no_bible_ctx.mean():.1%}, "
      f"model recall there {ey[ey.no_bible_ctx].hit.mean():.1%}")
non = df[df.ey == 0]
print(f"Non-EY segments flagged by model: {(non.p_names_verses >= T).mean():.1%}")
ey["hit_full"] = ey.p_full >= TF
print(f"\nFull model (set 2): EY segments found {ey.hit_full.mean():.1%}; "
      f"with biblical context {ey[~ey.no_bible_ctx].hit_full.mean():.1%}; "
      f"without biblical context {ey[ey.no_bible_ctx].hit_full.mean():.1%}; "
      f"non-EY flagged {(non.p_full >= TF).mean():.1%}")
