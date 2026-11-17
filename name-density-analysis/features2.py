"""Second feature set per segment: medicine, narrative (sage stories), dialogue, halakhic vocabulary.

Counted on both the Aramaic (Sefaria Vilna text, no nikud) and the English (full Koren/Steinsaltz).
Output: out/segments_feat2.csv (tractate, amud, seg + counts)
Run: py -3.13 -I features2.py
"""
import csv
import html
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
SEF = HERE.parent.parent / "talmud-names-discovery" / "sefaria"
OUT = HERE / "out"
TAG = re.compile(r"<[^>]+>")


def he_re(words):  # whole-word (with optional prefix letters) Aramaic patterns
    return re.compile(r"(?<![א-ת])[ודהבלכמש]{0,2}(?:" + "|".join(words) + r")(?![א-ת])")


def en_re(words):
    return re.compile(r"\b(?:" + "|".join(words) + r")\b", re.I)


LEX = {
    # medicine, body, remedies, demons
    "med_he": he_re(["סמא", "סמנא", "אסותא", "רפואה", "רפואת", "לסו", "ליתי", "לייתי", "נישתי", "לישתי", "לשתי",
                     "ליכול", "מעלי", "קשה", "קשין", "חולי", "חולה", "חלשא", "חמימי", "צמרמורתא", "אישתא", "כיפי",
                     "דמא", "עינא", "עיניה", "לבא", "מעיא", "טחול", "כוליא", "שיני", "שדא", "שדים", "שידא",
                     "מזיקין", "רוח רעה", "קצירא", "לחש", "חמרא", "דובשא", "תומא", "סילקא", "כשותא", "מיא"]),
    "med_en": en_re(["remed(?:y|ies)", "cure[sd]?", "heal(?:s|ed|ing)?", "illness(?:es)?", "ill", "sick(?:ness)?",
                     "fever", "physician", "doctor", "disease", "ailment", "pain", "harmful", "beneficial",
                     "intestines?", "spleen", "liver", "kidneys?", "stomach", "bowels?", "eyes? (?:pain|ailment)",
                     "blindness", "demons?", "spirit of", "danger(?:ous)?", "bloodletting", "let blood",
                     "drink", "eat(?:s|ing)?", "wine", "honey", "garlic", "beets?", "dates", "vegetables?",
                     "potion", "incantation", "amulet"]),
    # narrative / story-telling
    "narr_he": he_re(["יומא חד", "זימנא חדא", "פעם אחת", "מעשה ב", "אזל", "אזלא", "אזלו", "אזיל", "אתא", "אתאי",
                      "אתו", "אתיוה", "חזייה", "חזא", "חזינא", "נפק", "נפקא", "נפקו", "על לגביה", "סליק", "נחית",
                      "אקלע", "איקלע", "איקלעו", "יתיב", "יתבי", "הוה קאזיל", "הוה יתיב", "שכיב", "נח נפשיה",
                      "ההוא גברא", "ההיא איתתא", "ההוא מרבנן", "ההוא סבא", "ההוא ינוקא", "קם", "קמו", "שדריה",
                      "שקליה", "שקל", "רהט", "בכה", "בכי", "חלש", "אישתמיט", "אשכחיה", "אשכח", "אשכחוה"]),
    "narr_en": en_re(["relates", "recounts", "incident", "once", "one day", "went", "came to", "came before",
                      "arrived", "found", "saw", "a certain (?:man|woman|person|elder|heretic|gentile|student)",
                      "wept", "cried", "died", "fell ill", "dream(?:ed|t)?", "story", "happened"]),
    # dialogue
    "dial_he": he_re(["אמר ליה", "אמרה ליה", "אמר לה", "אמרו ליה", "אמרו לו", "אמר להו", "אמר להם", "אמרה לו",
                      "א\"ל", "אמ' ליה"]),
    # halakhic vocabulary
    "law_he": he_re(["חייב", "חייבין", "חייבת", "פטור", "פטורין", "פטורה", "מותר", "מותרין", "מותרת", "אסור",
                     "אסורין", "אסורה", "טמא", "טמאה", "טמאין", "טהור", "טהורה", "טהורין", "כשר", "כשרה",
                     "כשרין", "פסול", "פסולה", "פסולין", "זכאי", "קנה", "לא קנה", "מקודשת", "מגורשת", "יצא",
                     "לא יצא", "מעשר", "תרומה", "קרבן", "שבת", "חטאת", "עולה", "שלמים", "גט", "קידושין",
                     "ממון", "נזק", "שבועה", "ערבה", "ספק"]),
    "law_en": en_re(["liable", "exempt", "permitted", "prohibited", "forbidden", "impure", "impurity", "pure",
                     "purity", "fit", "unfit", "valid", "invalid", "obligat(?:ed|ion)", "acquire[sd]?",
                     "acquisition", "betroth(?:ed|al)", "bill of divorce", "halakha", "offering", "tithes?",
                     "teruma", "Shabbat", "court", "oath", "damages?", "payment", "pay", "owner", "ruling",
                     "the mishna", "the baraita", "in accordance with the opinion of"]),
}


def main():
    rows = []
    for p in sorted(SEF.glob("*_en.json")):
        tr = p.name[:-8]
        en = json.load(open(p, encoding="utf-8"))["text"]
        he = json.load(open(SEF / f"{tr}_he.json", encoding="utf-8"))["text"]
        for ai, amud in enumerate(en):
            for si, raw in enumerate(amud):
                if not raw:
                    continue
                e = html.unescape(TAG.sub(" ", raw))
                h = TAG.sub(" ", he[ai][si]) if ai < len(he) and si < len(he[ai]) else ""
                r = {"tractate": tr.replace("_", " "), "amud": f"{ai // 2 + 1}{'ab'[ai % 2]}", "seg": si + 1}
                for k, rx in LEX.items():
                    r[k] = len(rx.findall(h if k.endswith("_he") else e))
                rows.append(r)
        print(tr, flush=True)
    with open(OUT / "segments_feat2.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
