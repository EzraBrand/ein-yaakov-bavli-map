# Ein Yaakov ↔ Bavli: a passage-to-segment map

**[`ein_yaakov_to_bavli.csv`](ein_yaakov_to_bavli.csv)** maps each passage of *Ein Yaakov* (Sefaria's digital text) to the passage of the Babylonian Talmud that it comes from. The Bavli reference uses Sefaria's segment numbers, which follow the Koren / Steinsaltz (William Davidson) edition and are also used by [Bekiut](https://bekiut.com). So each Ein Yaakov passage gets an exact page and section, for example `Berakhot 44b:10`.

Ein Yaakov on Sefaria has no daf references, so I made the map by matching the texts.

**Browse it:** https://ezrabrand.github.io/ein-yaakov-bavli-map/ (filter by tractate, search by ref or Hebrew words).

## The file

3,022 rows, one per Ein Yaakov passage that has a match in the Bavli.

| Column | Contents |
|---|---|
| `ey url - sefaria` | The Ein Yaakov passage on Sefaria, e.g. `https://www.sefaria.org/Ein_Yaakov%2C_Berakhot.6.25` |
| `sefaria url` | The Bavli range on Sefaria, e.g. `https://www.sefaria.org/Berakhot.44b.10` |
| `ey words` | Length of the Ein Yaakov passage, in words |
| `ey start` | The first words of the Ein Yaakov passage (no vowels) |
| `parallels elsewhere` | Other places in the same tractate where the same text also occurs (a repeated mishna, a parallel sugya). These are not part of the match. |

Rows with no Bavli match are not in the file: 95 passages that are only a section number or a chapter ending ("אין אגדות בפרק זה"), and 75 passages from tractates that have no Bavli (Eduyot, Middot, Kelim …).

## How the match works

1. **Normalise both texts:**
   - change maqaf to a space, then remove vowels and cantillation
   - remove text in parentheses (Ein Yaakov's verse references, Vilna's deleted readings)
   - write out common abbreviations (א"ל → אמר ליה, הקב"ה → הקדוש ברוך הוא …)
   - reduce each word to a consonant skeleton (no inner or final ו/י/א; final letters normalised)
2. **Compare word 4-grams.** A Bavli segment counts as "in Ein Yaakov" if at least 40% of its 4-grams occur in the Ein Yaakov text of the same tractate. The scores are strongly bimodal: most segments score near 0 or near 1.
3. **Assign** each such segment to the Ein Yaakov passage it shares the most 4-grams with. Each Ein Yaakov passage then gets the range of its segments.
4. **Parallels.** A matched range that is more than 40 segments away from the passage's main range is a repeated text. It goes to `parallels elsewhere`.
5. **Fallback.** 107 passages match no whole segment. They get a span from the 4-grams that occur only once in the tractate. Check these by hand; they are mostly short passages.

## Size check

- Ein Yaakov has 412k words, 22% of the 1.85M Aramaic words of the Bavli (Sefaria texts).
- The matched Bavli segments hold 20% of the Bavli's words, but only 16% of its segments, because aggadic segments are longer.
- The share varies by tractate: Berakhot 51%, Bava Kamma 9%, Zevachim 6% (word ratio).
- The median Ein Yaakov passage shares 72% of its 4-grams with its Bavli range. The rest is variant wording, Ein Yaakov's own additions, and editorial changes.

## What to know when you use it

- **Ein Yaakov takes the core and leaves the frame.** It often quotes a baraita or a story as one block and leaves out the Gemara's discussion around it. Example: Ein Yaakov Berakhot 6:25 has the whole food-and-health baraita of Berakhot 44b ("spleen is good for the teeth… cabbage for food, beets for healing…") without the comments between its clauses. In such places the Bavli range can be partial, or the passage can fall back to the anchor method.
- **Repeated texts are taken once.** For example, the remedies of Avodah Zarah 28a are in Ein Yaakov under Yoma (8:19–20), at the parallel in Yoma 84a. The map matches only within one tractate, so it cannot link such a passage across tractates.
- **Gaps.** When Ein Yaakov skips more than 3 segments inside one passage, `sefaria url` gives the whole span from the first to the last matched segment. 163 passages have such gaps.
- **Text versions.** Ein Yaakov is Sefaria's "merged" Hebrew version (Daat). Its wording sometimes differs from Vilna, partly because of censorship (e.g. Sanhedrin 107b). Matches with strongly variant wording can be weak or missing.

## Rebuild

The Sefaria texts are not in this repository. Download them from the public bucket `gs://sefaria-export` (no login needed):

- **Bavli**, all 37 tractates: `json/Talmud/Bavli/<Seder>/<Tractate>/English/William Davidson Edition - English.json` and `json/Talmud/Bavli/<Seder>/<Tractate>/Hebrew/William Davidson Edition - Aramaic.json`. Save them as `<Tractate>_en.json` and `<Tractate>_he.json` (e.g. `Bava_Batra_he.json`) in `../talmud-names-discovery/sefaria/`, or change `SEF` in `align_ein_yaakov.py`.
- **Ein Yaakov:** `json/Midrash/Aggadah/Ein Yaakov/Hebrew/merged.json`. Save it as `ein_yaakov_raw/ey_he_merged.json`.

Then:

```
py -3.13 -I align_ein_yaakov.py   # per-segment coverage -> out/  (~2 min)
py -3.13 -I map_ein_yaakov.py     # ein_yaakov_to_bavli.csv, plus a fuller local workbook in out/
py -3.13 -I check_omission.py Berakhot 44b   # per-segment check of any amud
py -3.13 -I build_page.py         # docs/index.html (GitHub Pages) from the CSV
```

`out/ein_yaakov_bavli_map.xlsx` (local only) also has the match share, the printed Ein Yaakov section number (where the text gives it), Bekiut links, and a sheet from the Bavli side (every Bavli segment → its Ein Yaakov passage).

## Background: aggada by numbers

This map grew out of an analysis in [`name-density-analysis/`](name-density-analysis/). That analysis asks whether biblical names and verse citations identify aggadic sugyot objectively. In short:
- **Biblical persons, places and verse citations** mark aggada: AUC 0.86 against Ein Yaakov.
- **Legal vocabulary** marks halakha: liable/exempt, permitted/prohibited, pure/impure.
- **Together** they reach AUC 0.91 and κ 0.64, and almost the same per-tractate ranking as Ein Yaakov (Spearman 0.94).
- **Names of sages carry no signal.** They are as frequent in halakha as in aggada.

The folder has its own README with the full report, and the scripts and results.

## Sources and licence

- **Bavli:** Sefaria, William Davidson Edition (Koren Noé Talmud with Steinsaltz commentary), CC-BY-NC.
- **Ein Yaakov:** Sefaria's Hebrew text (Daat).
- The short excerpts in the CSV come from these texts, under their licences.
- Code: MIT (see [LICENSE](LICENSE)).
