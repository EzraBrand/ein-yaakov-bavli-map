"""Align Ein Yaakov (Sefaria 'merged' Hebrew) to Bavli segments by shared word 4-grams.

For each Bavli segment (Vilna Aramaic, Sefaria), coverage = share of its 4-grams that occur in the Ein Yaakov
text of the same tractate. Spelling is reduced to a consonant skeleton (no nikud, no matres ו/י/א, final letters
normalised) so plene/defective spelling does not block a match.
Also records, for each Ein Yaakov passage, where in the Bavli it lands (first/last matched segment).

Output: out/ey_segment_coverage.csv, out/ey_passages_aligned.csv
Run: py -3.13 -I align_ein_yaakov.py
"""
import csv, json, re, sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
SEF = HERE.parent / "talmud-names-discovery" / "sefaria"
OUT = HERE / "out"
EY = json.load(open(HERE / "ein_yaakov_raw" / "ey_he_merged.json", encoding="utf-8"))["text"]
N = 4

NAME_MAP = {"Eiruvin": "Eruvin", "Pesakhim": "Pesachim", "Khagigah": "Chagigah", "Ketubbot": "Ketubot",
            "Zevakhim": "Zevachim", "Menakhot": "Menachot", "Khullin": "Chullin", "Rosh Hashanah": "Rosh_Hashanah",
            "Moed Katan": "Moed_Katan", "Bava Kamma": "Bava_Kamma", "Bava Metzia": "Bava_Metzia",
            "Bava Batra": "Bava_Batra", "Avodah Zarah": "Avodah_Zarah"}
FINALS = str.maketrans("ךםןףץ", "כמנפצ")
TAG = re.compile(r"<[^>]+>")
NIKUD = re.compile(r"[֑-ׇ]")


MAQAF = re.compile("[־\\-]")
PAREN = re.compile(r"\([^)]*\)")  # Bavli: deleted readings; Ein Yaakov: verse references
GERSH = re.compile("[׳״\"'’”]")
# common abbreviations, written out (applied after nikud removal, on words with geresh/gershayim)
ABBR = {"א\"ל": "אמר ליה", "א\"ר": "אמר רבי", "ת\"ר": "תנו רבנן", "ת\"ש": "תא שמע", "מ\"ט": "מאי טעמא",
        "הקב\"ה": "הקדוש ברוך הוא", "ר'": "רבי", "רשב\"י": "רבי שמעון בן יוחאי", "ריב\"ל": "רבי יהושע בן לוי",
        "רשב\"ג": "רבן שמעון בן גמליאל", "אע\"פ": "אף על פי", "א\"כ": "אם כן", "וכו'": "", "וגו'": "",
        "ע\"ז": "עבודה זרה", "ק\"ו": "קל וחומר", "כ\"ש": "כל שכן", "א\"צ": "אין צריך", "ה\"ז": "הרי זה",
        "ע\"י": "על ידי", "ב\"ה": "בית הלל", "ב\"ש": "בית שמאי", "ת\"ח": "תלמיד חכם", "ת\"ל": "תלמוד לומר",
        "ד\"א": "דבר אחר", "ר\"ל": "ריש לקיש", "ריב\"ז": "רבן יוחנן בן זכאי", "בר\"ה": "בראש השנה"}
ABBR_RE = re.compile(r"(?<![א-ת])(" + "|".join(re.escape(k).replace('\\"', "[\"״]")
                                                            .replace("'", "['׳]") for k in ABBR)
                     + r")(?![א-ת])")


def _expand(m):
    return ABBR.get(m.group(0).replace("״", '"').replace("׳", "'"), m.group(0))


def skel_words(s):
    s = MAQAF.sub(" ", TAG.sub(" ", s))
    s = NIKUD.sub("", s)
    s = PAREN.sub(" ", s)
    s = ABBR_RE.sub(_expand, s)
    s = re.sub(r"[^א-ת\s]", " ", s).translate(FINALS)
    out = []
    for w in s.split():
        k = re.sub(r"(?<=.)[ויא]", "", w)  # keep a leading vav/yod/alef, drop inner/final matres
        if k:
            out.append(k)
    return out


def grams(ws):
    return [" ".join(ws[i:i + N]) for i in range(len(ws) - N + 1)]


def flat(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, list):
        for y in x:
            yield from flat(y)


def main():
    seg_rows, pas_rows = [], []
    for ey_name, chapters in EY.items():
        tr = NAME_MAP.get(ey_name, ey_name)
        if not (SEF / f"{tr}_he.json").exists():
            print("skip (no Bavli):", ey_name)
            continue
        he = json.load(open(SEF / f"{tr}_he.json", encoding="utf-8"))["text"]
        # index Bavli 4-grams -> segment positions
        pos = defaultdict(list)
        segs = []
        for ai, amud in enumerate(he):
            for si, s in enumerate(amud):
                g = grams(skel_words(s))
                segs.append((ai, si, g))
                for x in set(g):
                    pos[x].append(len(segs) - 1)
        ey_grams = set()
        for ci, ch in enumerate(chapters):
            for pi, p in enumerate(ch if isinstance(ch, list) else [ch]):
                text = " ".join(flat(p))
                g = grams(skel_words(text))
                ey_grams.update(g)
                hits = [pos[x][0] for x in g if len(pos.get(x, [])) == 1]  # unique anchors only
                hits.sort()
                if hits:
                    lo, hi = hits[len(hits) // 10], hits[-(len(hits) // 10) - 1]  # trim 10% outliers
                    a1, s1, _ = segs[lo]
                    a2, s2, _ = segs[hi]
                    span = f"{a1 // 2 + 1}{'ab'[a1 % 2]}:{s1 + 1}-{a2 // 2 + 1}{'ab'[a2 % 2]}:{s2 + 1}"
                else:
                    span = ""
                pas_rows.append({"ey_tractate": ey_name, "chapter": ci + 1, "passage": pi + 1,
                                 "ey_words": len(text.split()), "ey_4grams": len(g), "unique_anchor_hits": len(hits),
                                 "anchor_share": round(len(hits) / max(len(g), 1), 3), "bavli_span": span,
                                 "ey_start": NIKUD.sub("", TAG.sub("", text))[:80]})
        covered = 0
        for ai, si, g in segs:
            cov = sum(1 for x in g if x in ey_grams) / len(g) if g else None
            seg_rows.append({"tractate": tr.replace("_", " "), "amud": f"{ai // 2 + 1}{'ab'[ai % 2]}", "seg": si + 1,
                             "he_4grams": len(g), "ey_coverage": "" if cov is None else round(cov, 3)})
            covered += bool(cov and cov >= 0.5)
        print(f"{tr}: {len(segs)} segments, {covered} with EY coverage >= 0.5", flush=True)
    for name, rows in (("ey_segment_coverage.csv", seg_rows), ("ey_passages_aligned.csv", pas_rows)):
        with open(OUT / name, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, list(rows[0]))
            w.writeheader()
            w.writerows(rows)


if __name__ == "__main__":
    main()
