"""Ein Yaakov passage <-> Bavli segment mapping table (Sefaria refs, Koren/Steinsaltz segmentation).

Each Bavli segment whose 4-gram coverage by Ein Yaakov is >= 0.4 is assigned to the Ein Yaakov passage it shares
the most 4-grams with. Each Ein Yaakov passage then gets the Bavli ranges of its assigned segments (a new range
starts after a gap of more than GAP segments). Passages with no assigned segment get an anchor-based fallback span.

Output: ein_yaakov_to_bavli.csv (repository root, the published table),
        out/ein_yaakov_bavli_map.csv (one row per Ein Yaakov passage, all columns),
        out/bavli_segments_ein_yaakov.csv (one row per Bavli segment),
        out/ein_yaakov_bavli_map.xlsx (both sheets + notes)
Run: py -3.13 -I map_ein_yaakov.py
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from align_ein_yaakov import EY, NAME_MAP, NIKUD, SEF, TAG, flat, grams, skel_words  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"
TH, GAP, FAR = 0.4, 3, 40


def amud(ai):
    return f"{ai // 2 + 1}{'ab'[ai % 2]}"


def rng(tr, a1, s1, a2, s2):
    t = tr.replace(" ", "_")
    if (a1, s1) == (a2, s2):
        return f"{tr} {a1}:{s1}", f"https://www.sefaria.org/{t}.{a1}.{s1}"
    if a1 == a2:
        return f"{tr} {a1}:{s1}–{s2}", f"https://www.sefaria.org/{t}.{a1}.{s1}-{s2}"
    return f"{tr} {a1}:{s1}–{a2}:{s2}", f"https://www.sefaria.org/{t}.{a1}.{s1}-{a2}.{s2}"


ey_rows, seg_rows = [], []
for ey_name, chapters in EY.items():
    tr_file = NAME_MAP.get(ey_name, ey_name)
    if not (SEF / f"{tr_file}_he.json").exists():
        for ci, ch in enumerate(chapters):
            for pi, p in enumerate(ch):
                ey_rows.append({"ey_ref": f"Ein Yaakov, {ey_name} {ci + 1}:{pi + 1}", "ey_tractate": ey_name,
                                "note": "no Bavli tractate (Mishna-only tractate)"})
        continue
    tr = tr_file.replace("_", " ")
    he = json.load(open(SEF / f"{tr_file}_he.json", encoding="utf-8"))["text"]
    segs = [(ai, si, grams(skel_words(s))) for ai, a in enumerate(he) for si, s in enumerate(a)]
    # Ein Yaakov passages and a 4-gram -> passage index
    pas, idx = [], defaultdict(set)
    for ci, ch in enumerate(chapters):
        for pi, p in enumerate(ch):
            text = " ".join(flat(p))
            g = grams(skel_words(text))
            pas.append({"ci": ci, "pi": pi, "text": text, "grams": set(g)})
            for x in g:
                idx[x].add(len(pas) - 1)
    allg = set(idx)
    seg_base = len(seg_rows)
    assigned = defaultdict(list)
    bavli_pos = defaultdict(list)
    for k, (ai, si, g) in enumerate(segs):
        for x in set(g):
            bavli_pos[x].append(k)
        cov = sum(x in allg for x in g) / len(g) if g else 0
        best, share = None, 0
        if g and cov >= TH:
            c = Counter(p for x in g for p in idx.get(x, ()))
            best, n = c.most_common(1)[0]
            share = n / len(g)
            assigned[best].append(k)
        seg_rows.append({"bavli_ref": f"{tr} {amud(ai)}:{si + 1}", "tractate": tr, "amud": amud(ai), "seg": si + 1,
                         "ey_coverage": round(cov, 3) if g else "",
                         "ey_ref": "" if best is None else f"Ein Yaakov, {ey_name} {pas[best]['ci'] + 1}:{pas[best]['pi'] + 1}",
                         "ey_share_of_segment": round(share, 3) if best is not None else "", "note": ""})
    for k, p in enumerate(pas):
        ref = f"Ein Yaakov, {ey_name} {p['ci'] + 1}:{p['pi'] + 1}"
        url = f"https://www.sefaria.org/{quote('Ein_Yaakov,_' + ey_name.replace(' ', '_'))}.{p['ci'] + 1}.{p['pi'] + 1}"
        plain = NIKUD.sub("", TAG.sub("", p["text"]))
        row = {"ey_ref": ref, "ey_url": url, "ey_tractate": ey_name, "ey_chapter": p["ci"] + 1,
               "ey_passage": p["pi"] + 1, "ey_words": len(plain.split()), "ey_start": plain[:90]}
        ks = sorted(assigned.get(k, []))
        if ks:
            runs, cur = [], [ks[0]]
            for x in ks[1:]:
                if x - cur[-1] > GAP + 1:
                    runs.append(cur)
                    cur = [x]
                else:
                    cur.append(x)
            runs.append(cur)
            # parallels: runs far from the main (largest) run are repeated texts elsewhere in the tractate
            main = max(runs, key=len)
            far = [r for r in runs if min(abs(r[0] - main[-1]), abs(main[0] - r[-1])) > FAR]
            runs = [r for r in runs if r not in far]
            row["parallels_elsewhere"] = "; ".join(
                rng(tr, amud(segs[r[0]][0]), segs[r[0]][1] + 1, amud(segs[r[-1]][0]), segs[r[-1]][1] + 1)[0] for r in far)
            for r in far:
                for x in r:
                    seg_rows[seg_base + x]["ey_ref"] = ""
                    seg_rows[seg_base + x]["note"] = f"parallel of {ref}"
            ks = [x for r in runs for x in r]
            refs = [rng(tr, amud(segs[r[0]][0]), segs[r[0]][1] + 1, amud(segs[r[-1]][0]), segs[r[-1]][1] + 1) for r in runs]
            matched = set().union(*(set(segs[x][2]) for x in ks)) & p["grams"]
            row.update({"bavli_ranges": "; ".join(r[0] for r in refs), "bavli_first_ref": refs[0][0].split("–")[0],
                        "sefaria_url": refs[0][1] if len(refs) == 1 else
                        rng(tr, amud(segs[ks[0]][0]), segs[ks[0]][1] + 1, amud(segs[ks[-1]][0]), segs[ks[-1]][1] + 1)[1],
                        "bekiut_url": f"https://bekiut.com/talmud/{tr_file}/{amud(segs[ks[0]][0])}#{segs[ks[0]][1] + 1}",
                        "n_ranges": len(refs), "n_bavli_segments": len(ks),
                        "ey_match_share": round(len(matched) / max(len(p["grams"]), 1), 3), "method": "assigned"})
        else:  # fallback: unique 4-gram anchors in the Bavli
            hits = sorted(bavli_pos[x][0] for x in p["grams"] if len(bavli_pos.get(x, [])) == 1)
            if len(hits) >= 3:
                lo, hi = hits[len(hits) // 10], hits[-(len(hits) // 10) - 1]
                r = rng(tr, amud(segs[lo][0]), segs[lo][1] + 1, amud(segs[hi][0]), segs[hi][1] + 1)
                row.update({"bavli_ranges": r[0], "bavli_first_ref": r[0].split("–")[0], "sefaria_url": r[1],
                            "n_ranges": 1, "n_bavli_segments": hi - lo + 1,
                            "ey_match_share": round(len(hits) / max(len(p["grams"]), 1), 3),
                            "method": "anchors (weak: shares only part of a segment)"})
            else:
                row.update({"method": "none", "note": "no match (heading, note, or text not in this Bavli tractate)"})
        ey_rows.append(row)
    print(f"{tr}: {len(pas)} Ein Yaakov passages, {sum(1 for k in range(len(pas)) if assigned.get(k))} assigned",
          flush=True)

ey = pd.DataFrame(ey_rows)

# printed Ein Yaakov section number (siman) at the start of a passage: keep only if it continues the sequence
GV = dict(zip("אבגדהוזחטיכלמנסעפצקרשת", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200,
                                          300, 400]))


def gval(tok):
    tok = tok.replace('"', "").replace("״", "").replace("'", "")
    if not tok or len(tok) > 4 or any(c not in GV for c in tok):
        return None
    vals = [GV[c] for c in tok]
    return sum(vals) if vals == sorted(vals, reverse=True) else None


simans, last = [], {}
for _, r in ey.iterrows():
    s = str(r.get("ey_start", "") or "")
    first = s.split(" ")[0] if s else ""
    v = gval(first)
    prev = last.get(r.ey_tractate, 0)
    if v is not None and prev < v <= prev + 6:
        last[r.ey_tractate] = v
        simans.append(v)
    else:
        simans.append("")
ey.insert(5, "ey_printed_siman", simans)
sg = pd.DataFrame(seg_rows)
ey.to_csv(OUT / "ein_yaakov_bavli_map.csv", index=False, encoding="utf-8-sig")
sg.to_csv(OUT / "bavli_segments_ein_yaakov.csv", index=False, encoding="utf-8-sig")
notes = pd.DataFrame({"notes": [
    "Built 17-Nov-2026 by map_ein_yaakov.py (talmud-name-density).",
    "Ein Yaakov: Sefaria 'Ein Yaakov' Hebrew merged.json (gs://sefaria-export). Bavli: Sefaria William Davidson "
    "Aramaic; segment numbers = Sefaria/Koren-Steinsaltz segments, as used by Bekiut.",
    f"Match: consonant-skeleton word 4-grams. A Bavli segment is Ein Yaakov if >= {TH:.0%} of its 4-grams occur in "
    "Ein Yaakov of the same tractate; it is assigned to the passage it shares most 4-grams with.",
    f"bavli_ranges: several ranges when Ein Yaakov skips more than {GAP} segments inside one passage.",
    "ey_match_share: share of the Ein Yaakov passage's 4-grams found in its Bavli segments (low = variant wording, "
    "editorial additions, or text that Ein Yaakov placed elsewhere).",
    "method=anchors: no Bavli segment reached the threshold; the span is from unique shared 4-grams only - check by hand.",
    "ey_printed_siman: the printed Ein Yaakov section number where the Sefaria text starts with it (about 40% of "
    "passages; some tractates, e.g. Shabbat, have none; in places the number is a separate one-word passage, "
    "method=none).",
    "Coverage is per Koren/Steinsaltz segment. Where Ein Yaakov quotes a baraita without the Gemara's discussion "
    "between its clauses (e.g. Berakhot 44b, Ein Yaakov Berakhot 6:25), each segment holds one clause plus "
    "discussion and scores low; such passages can be missing from Bavli_segments_in_EY."]})
with pd.ExcelWriter(OUT / "ein_yaakov_bavli_map.xlsx") as xw:
    ey.to_excel(xw, sheet_name="EinYaakov_to_Bavli", index=False)
    sg[sg.ey_ref != ""].to_excel(xw, sheet_name="Bavli_segments_in_EY", index=False)
    notes.to_excel(xw, sheet_name="notes", index=False)
print("\nEin Yaakov passages:", len(ey), ey.method.value_counts(dropna=False).to_dict())
print("ranges per assigned passage:", ey[ey.method == "assigned"].n_ranges.value_counts().sort_index().to_dict())
print("ey_match_share quartiles (assigned):", ey[ey.method == "assigned"].ey_match_share.quantile([.25, .5, .75]).tolist())

# slim CSV for GitHub: passages with a Bavli match only (rows with a note are dropped), user's column order
gh = ey[ey.note.fillna("") == ""] if "note" in ey else ey
gh = gh[["ey_url", "sefaria_url", "ey_words", "ey_start", "parallels_elsewhere"]].rename(columns={
    "ey_url": "ey url - sefaria", "sefaria_url": "sefaria url", "ey_words": "ey words", "ey_start": "ey start",
    "parallels_elsewhere": "parallels elsewhere"})
gh["ey words"] = gh["ey words"].astype("Int64")
gh.to_csv(OUT.parent / "ein_yaakov_to_bavli.csv", index=False, encoding="utf-8-sig")
print("GitHub CSV rows:", len(gh))
