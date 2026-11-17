"""Name density per Bavli segment / amud / passage window, from the talmud-nlp-indexer gazetteers.

Hypothesis (Ezra, 17-Nov-2026): high density of names ~ aggadic sugya; few/no names ~ Stam (anonymous dialectic).

Input : Sefaria William Davidson Edition JSON (English + unvocalized Aramaic), gs://sefaria-export,
        local copy in ..\\talmud-names-discovery\\sefaria\\<Tractate>_{en,he}.json
        Gazetteers in .\\gazetteers\\ (downloaded from GitHub 17-Nov-2026).
Output: out\\segments.csv, out\\amudim.csv, out\\name_counts.csv
Run   : py -3.13 -I name_density.py
"""
import csv, html, json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
SEF = HERE.parent / "talmud-names-discovery" / "sefaria"
GAZ = HERE / "gazetteers"
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)

ORDER = ["Berakhot", "Shabbat", "Eruvin", "Pesachim", "Yoma", "Sukkah", "Beitzah", "Rosh_Hashanah", "Taanit",
         "Megillah", "Moed_Katan", "Chagigah", "Yevamot", "Ketubot", "Nedarim", "Nazir", "Sotah", "Gittin",
         "Kiddushin", "Bava_Kamma", "Bava_Metzia", "Bava_Batra", "Sanhedrin", "Makkot", "Shevuot", "Avodah_Zarah",
         "Horayot", "Zevachim", "Menachot", "Chullin", "Bekhorot", "Arakhin", "Temurah", "Keritot", "Meilah",
         "Tamid", "Niddah"]


def norm(s):
    return s.replace("'", "’").strip()


def load(name):
    return [norm(x) for x in (GAZ / name).read_text(encoding="utf-8").splitlines() if x.strip()]


# ---- gazetteer -> category (first list wins; bible beats talmud for shared entries) ----
cat = {}
for e in load("bible_names_gazetteer.txt"):
    cat.setdefault(e, "bible_person")
for e in load("talmud_names_gazetteer.txt"):
    cat.setdefault(e, "generic_person" if e[0].islower() else "talmud_person")
for e in load("talmud_toponyms_gazetteer.txt") + load("bible_places_gazetteer.txt"):
    cat.setdefault(e, "place")
for e in load("nations_and_demonyms_gazetteer.txt"):
    cat.setdefault(e, "nation")
CATS = ["talmud_person", "bible_person", "generic_person", "place", "nation"]

entries = sorted(cat, key=len, reverse=True)
NAME_RE = re.compile(r"(?<![\w’])(" + "|".join(re.escape(e) for e in entries) + r")(?![\w])")

# ---- Hebrew/Aramaic markers of stammaitic dialectic (anonymous give-and-take) ----
STAM_HE = ["תא שמע", "ת\"ש", "איבעיא להו", "מאי טעמא", "מ\"ט", "מיתיבי", "איתיביה", "תיובתא", "קשיא",
           "אי הכי", "הכא במאי עסקינן", "הכא במאי עסקי'", "לימא", "מנא הני מילי", "מנה\"מ", "פשיטא",
           "מאי איכא בין", "מאי שנא", "ממאי", "מאי קאמר", "בשלמא", "הניחא", "אלא מעתה", "והתניא", "והא"]
STAM_RE = re.compile("|".join(re.escape(s) for s in sorted(STAM_HE, key=len, reverse=True)))
# narrative markers in the Aramaic (aggadic story-telling)
NARR_HE = ["אמר ליה", "א\"ל", "אמרה ליה", "אמרו לו", "אמרו ליה", "מעשה ב", "הוה ", "אזל", "אתא ", "אתו ", "חזא",
           "יומא חד", "שמע", "נפק", "על ", "יתיב", "קם "]
NARR_RE = re.compile("|".join(re.escape(s) for s in ["יומא חד", "מעשה ב", "אזל", "אזלא", "אזלו", "חזייה", "חזא ",
                                                       "יתיב", "הוה קאזיל", "נפק", "אתא ", "אתו ", "אמרה ליה"]))
VERSE_RE = re.compile(r"\((?:[1-3] )?[A-Z][A-Za-z ]+ \d+:\d+(?:[–-]\d+)?\)")
TAG_RE = re.compile(r"<[^>]+>")
BOLD_RE = re.compile(r"<b>(.*?)</b>", re.S)
WORD_RE = re.compile(r"[\w’]+")


def clean(s):
    return html.unescape(TAG_RE.sub(" ", s)).replace("'", "’")


def daf_label(i):
    return f"{i // 2 + 1}{'ab'[i % 2]}"


def main():
    seg_rows, name_counts = [], {}
    for tr in ORDER:
        en = json.load(open(SEF / f"{tr}_en.json", encoding="utf-8"))["text"]
        he = json.load(open(SEF / f"{tr}_he.json", encoding="utf-8"))["text"]
        in_mishna = False
        for ai, amud in enumerate(en):
            for si, raw in enumerate(amud):
                if not raw:
                    continue
                # Mishna/Gemara state: the last header in the segment decides
                for m in re.finditer(r"(MISHNA|GEMARA):", raw):
                    in_mishna = m.group(1) == "MISHNA"
                full = clean(raw)
                bold = " ".join(clean(b) for b in BOLD_RE.findall(raw))
                hes = clean(he[ai][si]) if ai < len(he) and si < len(he[ai]) else ""
                row = {"tractate": tr.replace("_", " "), "amud": daf_label(ai), "seg": si + 1,
                       "ref": f"{tr.replace('_', ' ')} {daf_label(ai)}:{si + 1}",
                       "is_mishna": int(in_mishna),
                       "words_full": len(WORD_RE.findall(full)), "words_bold": len(WORD_RE.findall(bold)),
                       "words_he": len(hes.split()),
                       "verses": len(VERSE_RE.findall(full)),
                       "stam_he": len(STAM_RE.findall(hes)), "narr_he": len(NARR_RE.findall(hes))}
                for layer, txt in (("full", full), ("bold", bold)):
                    found = NAME_RE.findall(txt)
                    row[f"names_{layer}"] = len(found)
                    row[f"distinct_{layer}"] = len(set(found))
                    for c in CATS:
                        row[f"{c}_{layer}"] = sum(1 for f in found if cat[f] == c)
                    if layer == "full":
                        for f in found:
                            name_counts[f] = name_counts.get(f, 0) + 1
                row["names_list"] = "; ".join(sorted(set(NAME_RE.findall(full))))
                seg_rows.append(row)
        print(f"{tr}: {sum(1 for r in seg_rows if r['tractate'] == tr.replace('_', ' '))} segments", flush=True)

    cols = list(seg_rows[0])
    with open(OUT / "segments.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(seg_rows)
    with open(OUT / "name_counts.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "category", "mentions_full"])
        for n, c in sorted(name_counts.items(), key=lambda x: -x[1]):
            w.writerow([n, cat[n], c])
    print("segments:", len(seg_rows))


if __name__ == "__main__":
    main()
