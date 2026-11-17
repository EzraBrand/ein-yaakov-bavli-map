# Name density as a proxy for aggada (and for Stam) in the Bavli

17-Nov-2026. Hypothesis (Ezra): a high density of names indicates an aggadic sugya; few or no names indicate a high level of Stam.

## Data

Setup: the Sefaria texts are not in this repository. Download the Bavli JSON (`json/Talmud/Bavli/...`, English William Davidson + Aramaic) and `json/Midrash/Aggadah/Ein Yaakov/Hebrew/merged.json` from the public bucket `gs://sefaria-export`. The scripts read the Bavli files as `../talmud-names-discovery/sefaria/<Tractate>_{en,he}.json` and Ein Yaakov from `ein_yaakov_raw/ey_he_merged.json`. Sefaria's William Davidson text is CC-BY-NC; the short text excerpts in `out/` come from it and from Sefaria's Ein Yaakov.


- **Text:** Sefaria William Davidson Edition (Koren/Steinsaltz English + unvocalized Aramaic), all 37 tractates, from the public bucket `gs://sefaria-export` (local copy downloaded 15-Oct-2026 in `..\talmud-names-discovery\sefaria\`). Refs are Sefaria segment refs (`Gittin 56a:3`), so each result cites an exact page and segment. Bekiut links use the same segment numbers.
- **Gazetteers:** `EzraBrand/talmud-nlp-indexer/data`, downloaded 17-Nov-2026 via `gh api` into `gazetteers\` (talmud names 3,880, toponyms 679, Bible names 585, Bible places 43, nations 60).
- **Matching:** longest match first, case-sensitive, word boundaries. Categories: `talmud_person` (sages and other Talmudic people), `bible_person`, `generic_person` (lowercase entries: "a certain Sadducee", "a pious man"), `place`, `nation`. Mishna segments are excluded; only Gemara is counted.
- **Two text layers:** *bold* = literal translation of the Aramaic; *full* = bold + Steinsaltz gloss. In narrative the Aramaic often says only "he said to him", and the gloss supplies the name. So the full layer counts the characters that are present in the story.
- **Units:** amud (5,317 amudim with 150+ English words), and passage windows of 8 consecutive Gemara segments (step 4; 19,070 windows). Sefaria has no sugya boundaries, so these windows are a substitute for sugyot.
- **Validation set:** 28 well-known aggadic passages (116 amudim), for example Gittin 55b–58a (Kamtza), Bava Batra 73a–75b (Rabba bar bar Ḥana), Megillah 10b–16b (Esther), Sanhedrin 93a–99a (Messiah), Bava Metzia 83b–86a. I chose them from memory; the script checks that each range contains a keyword (all 28 pass). List in `analyze.py`.
- **Stam proxies (independent of the names):** (1) Aramaic dialectic markers per 100 words (תא שמע, מיתיבי, איתיביה, תיובתא, קשיא, אי הכי, הכא במאי עסקינן, לימא, פשיטא, בשלמא, והא …); (2) the Koren editors' voice labels "The Gemara asks / answers / rejects …" per segment.

## Results

### 1. Name density does predict aggada — but not because of the sages

AUC = probability that a random aggadic amud scores higher than a random other amud (0.5 = no signal).

| Measure (per 100 English words, amud level) | AUC | Median aggada | Median other |
|---|---|---|---|
| All names, full English | **0.85** | 3.93 | 1.92 |
| All names, bold (literal translation) only | 0.63 | 4.20 | 3.27 |
| Talmudic persons only (sages etc.) | 0.49 | 1.46 | 1.54 |
| Bible persons | 0.86 | 1.19 | 0.00 |
| Places | 0.78 | 0.27 | 0.00 |
| Nations / demonyms | 0.75 | 0.11 | 0.00 |
| Generic persons ("a certain man") | 0.68 | 0.06 | 0.00 |
| **Non-sage names (Bible + generic + place + nation)** | **0.89** | 1.94 | 0.16 |
| Non-sage names without Bible persons | 0.82 | | |
| Bible verse citations (comparison) | 0.83 | 0.67 | 0.11 |
| Aramaic Stam markers (comparison) | 0.19 (= 0.81 inverted) | 0.32 | 1.23 |

Points:
- **Sage names carry no signal (AUC 0.49).** Halakhic sugyot are full of attributions ("Rav Yehuda said that Shmuel said"), as many as aggadic ones. The hypothesis holds only for names *other than* the sages: biblical figures, places, nations, anonymous characters.
- The bold-only layer is weak (0.63): aggadic stories name their characters less often in the Aramaic itself; the gloss adds the names.
- Results are the same for 8-segment windows (all names 0.82, non-sage 0.87).
- Of the 10% of amudim with the most names, 12% are in the validation set, against 0–3% in deciles 1–9. The validation set covers only a part of the aggada, so the true share is higher.

### 2. "Few names = Stam" is not supported

| Decile of name density | 1 (fewest) | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 (most) |
|---|---|---|---|---|---|---|---|---|---|---|
| Names /100 words (median) | 0.58 | 1.01 | 1.30 | 1.57 | 1.81 | 2.09 | 2.38 | 2.74 | 3.26 | 4.40 |
| Aramaic Stam markers /100 words (mean) | 1.32 | 1.54 | 1.49 | 1.59 | 1.42 | 1.38 | 1.36 | 1.30 | 1.13 | 0.95 |
| "The Gemara asks/answers…" per segment | 0.62 | 0.59 | 0.55 | 0.53 | 0.50 | 0.49 | 0.49 | 0.43 | 0.40 | 0.39 |

- The editors' Stam labels fall steadily as names rise (Spearman −0.25), so there is a moderate signal.
- The Aramaic Stam markers are flat over deciles 1–8 and drop only in deciles 9–10 (Spearman −0.15). The drop is the aggada effect, not a Stam effect.
- The lowest-name passages are of two kinds: Stam give-and-take (Bava Batra 159a, Zevachim 89b–90a, Bekhorot 6a) **and anonymous tannaitic material** — baraitot and midrash halakha (Nazir 48a–b, 44a), which has no names and no Stam markers. "No names" means "anonymous", not "Stam".
- Sage-name density alone has no correlation with the Aramaic Stam markers (+0.00).

### 3. What the top passages are

`out\TOP_aggada_candidates_by_nonsage_names.csv` (60 non-overlapping passages). 18 are in the validation set. My quick reading of the other 42: most are aggadic midrash on biblical narrative that is not in my set (Sanhedrin 19b Michal and Merab; Sanhedrin 49a Joab; Bava Batra 14b–15a authors of the biblical books; Sanhedrin 69b; Yoma 10a; Pesachim 87b, 119a; Sotah 33b–36b; Sanhedrin 107b Gehazi). About 8 are halakhic geography or genealogy, where place names are dense for a legal reason: Arakhin 32a (walled cities), Makkot 9b–10a (cities of refuge), Gittin 6a and Kiddushin 72a (borders of Babylonia), Bekhorot 55a (the Jordan), Chullin 3b–4a (Samaritans). I did not read every passage in full.

## Conclusion

The hypothesis works with one refinement: **count non-sage names** (biblical persons, places, nations, anonymous characters). That measure finds aggada with AUC 0.89. The raw count of all names works less well (0.85), and the sage names add nothing. The reverse claim does not hold in a simple form: few names indicate anonymous text, which is Stam or anonymous baraita. A better Stam measure is the dialectic markers themselves, or the absence of *sage* attributions in an amud that is not a baraita.

Limits: the validation set is small and my own choice; the 8-segment window is not a real sugya; the Stam marker list is short; the full layer depends on the Steinsaltz gloss.

## Part 2 (17-Nov-2026): biblical names and verses vs Ein Yaakov

### Label from Ein Yaakov

- Source: Sefaria `Ein Yaakov` Hebrew `merged.json` from `gs://sefaria-export` (anonymous gcloud), in `ein_yaakov_raw\` (not in git). Structure: tractate → chapter → passage. No daf references.
- Alignment (`align_ein_yaakov.py`), in four steps:
  1. Change maqaf to a space, then remove nikud.
  2. Remove parentheses (Ein Yaakov verse references; Vilna deleted readings).
  3. Write out common abbreviations (א"ל, הקב"ה, ת"ר …).
  4. Reduce each word to a consonant skeleton (no inner/final ו/י/א, final letters normalised).

  Then match word 4-grams. A Bavli segment is "Ein Yaakov" if 40% or more of its 4-grams occur in the Ein Yaakov text of the same tractate. 72% of Ein Yaakov's own 4-grams find a match in Bavli Berakhot; the rest is real textual variation.
- **Size check:** Ein Yaakov has 412k words, which is 22% of the 1.85M Aramaic words of the Bavli. Ein Yaakov segments hold 20% of the Bavli Aramaic words, but only 16% of the segments, because aggadic segments are longer. Ein Yaakov's share varies by tractate: Berakhot 51%, Bava Kamma 9%, Zevachim 6% (word ratio).
- **Coverage is bimodal:** 61,530 segments ≤ 0.05 and 10,112 ≥ 0.6. Spot checks:
  - In: Gittin 56a, Sanhedrin 19b/49a, Bava Metzia 59b.
  - Out: Arakhin 32a, Nazir 48a.
- **Result:** 11,360 of 70,510 Gemara segments (16.1%) are Ein Yaakov.
- **First version bug (fixed):** I deleted the maqaf together with the vowels, so word pairs were glued (כל־שכן → `כלשכנ`). Ein Yaakov's verse references also became junk tokens. That version gave only 14% of segments.
- **Remaining noise:** Ein Yaakov sometimes has another (partly censored) wording, for example Sanhedrin 107b and Avodah Zarah 4b.

### AUC against Ein Yaakov (segment level; k = window of ±k segments)

| Feature | k=0 | k=2 | k=4 | k=8 |
|---|---|---|---|---|
| Bible persons | 0.69 | 0.80 | 0.83 | 0.85 |
| Verse citations | 0.66 | 0.78 | 0.79 | 0.80 |
| Bible persons + verses | 0.73 | 0.83 | 0.84 | 0.85 |
| **Non-sage names + verses** | 0.76 | 0.85 | 0.86 | **0.86** |
| Places + nations + generic persons | 0.59 | 0.69 | 0.73 | 0.74 |
| All names | 0.68 | 0.74 | 0.75 | 0.76 |
| Sage names | 0.52 | 0.52 | 0.52 | 0.51 |
| Aramaic Stam markers (inverted) | 0.57 | 0.67 | 0.70 | 0.73 |
| **Halakhic vocabulary, English (inverted)** | 0.79 | 0.85 | **0.86** | 0.85 |
| Halakhic vocabulary, Aramaic (inverted) | 0.59 | 0.69 | 0.72 | 0.75 |
| Narrative words, English | 0.57 | 0.64 | 0.66 | 0.68 |
| Narrative words, Aramaic | 0.53 | 0.57 | 0.58 | 0.58 |
| Dialogue (אמר ליה …) | 0.53 | 0.56 | 0.57 | 0.58 |
| Medicine words, Aramaic / English | 0.52 / 0.51 | | 0.57 / 0.56 | 0.59 / 0.58 |

Logistic regression, trained on 36 tractates and tested on the one left out (`ey_compare.py`):

| Features | AUC | F1 | Precision | Recall | κ |
|---|---|---|---|---|---|
| Verses only | 0.79 | 0.48 | 0.43 | 0.55 | 0.37 |
| Bible persons + verses | 0.84 | 0.59 | 0.62 | 0.57 | 0.52 |
| All name groups + verses | 0.87 | 0.62 | 0.63 | 0.62 | 0.55 |
| + Aramaic Stam/narrative markers | 0.88 | 0.63 | 0.62 | 0.65 | 0.56 |
| **+ set 2 (medicine, narrative, dialogue, halakhic vocabulary)** | **0.91** | **0.70** | 0.68 | 0.71 | **0.64** |
| Set 2 + Stam only (no names, no verses) | 0.88 | 0.61 | 0.58 | 0.65 | 0.53 |

- Sage names: no signal, again (0.52), on an independent label of 11,360 segments.
- **Halakhic vocabulary is the single strongest feature** (0.86 inverted). Its terms: liable/exempt, permitted/prohibited, pure/impure, fit/unfit, acquire, betroth, offering, court, oath, damages. Names + verses and halakhic vocabulary are close to independent views, so together they reach 0.91.
- Per tractate, Ein Yaakov's share and the model's mean probability correlate at Spearman 0.80 (names + verses), and at **0.94** with set 2 added.
- The Ein Yaakov segments with no biblical name within ±4 segments and no verse are 16.9%. The model finds 4.8% of them with names + verses, and **33%** with set 2. Recall on all Ein Yaakov segments goes from 62% to 71%, and false positives go down from 7.1% to 6.4% of the other segments.

### Where they disagree (`disagree_*.csv`)

**Ein Yaakov has it, the names + verses model misses it:**
- Medicine and folk remedies: Gittin 68b–70a, Pesachim 110a–112a, Chullin 105b.
- Stories about sages: Bava Metzia 83b–84b, Kiddushin 81a (Rabbi Meir and Satan), Ketubot 17a, Megillah 27b–28a, Bava Batra 58a (Rabbi Bena'a), Nedarim 49a.
- Ethics and conduct: Kiddushin 31b–32a (honouring parents), Ketubot 105b (bribery), Kiddushin 80b, Shabbat 140b.

**The model flags it, Ein Yaakov leaves it out:**
- **Halakhic midrash on biblical narrative, mostly in Kodashim.** Examples:
  - Zevachim 101a, the death of Aaron's sons
  - Zevachim 59b–60a, Moses's altar
  - Keritot 5b, the anointing of kings
  - Arakhin 12b, priestly watches
  - Bava Batra 111b–113a, tribal inheritance

  Of the top 300 model windows, 68% of those in Kodashim are in Ein Yaakov, against 94% in the other orders.
- **Halakhic geography** (see below).
- **Aggada that Ein Yaakov really omits** (checked by phrase search):
  - Berakhot 56b: the dream verses ("one who sees a river in a dream…")
  - Megillah 14b–15a: end of the prophetesses passage
  - Sanhedrin 43a: the five disciples of Yeshu — censorship
  - Sanhedrin 82a: Zimri and Pinḥas, in a halakhic frame

### Halakhic geography (examples)

In these passages, place names are dense, but the question is legal, and the geography serves the halakha.
- **Bekhorot 55a:**
  - Halakhic question: Rabbi Meir holds that the Jordan divides flocks for the animal tithe. The Gemara asks why: is it a Torah border (Joshua 18:20, Numbers 34:12), or only because animals cannot cross?
  - The geography: a baraita traces the Jordan from the Cave of Pamyas through Lake Ḥula (Sea of Sivkhi), the Sea of Tiberias and the Dead Sea to the Great Sea. It says the name "Jordan" applies only from Beit Jericho southward. Rabbi Yoḥanan derives "Jordan" from *yored* (it descends) from Dan.
  - The legal use: the river's source matters for vows. Rav Kahana: one who vows off the water of the Cave of Pamyas may not drink from the whole Jordan. Rav Yehuda: one who vows off the Euphrates may not drink any water, because it is the source of all water.
  - So it is natural-history aggada in form, with a vow-law use.
- **Arakhin 32a–b:**
  - The mishna lists the walled cities "from the time of Joshua" (Tzippori, Gush Ḥalav, Yodfat, Gamla, Gedod, Ḥadid, Ono, Jerusalem). This matters because a house sold in a walled city becomes the buyer's after one year (Leviticus 25:30).
  - A baraita places Gamla in the Galilee, Gedod in Transjordan, and Ḥadid, Ono and Jerusalem in Judea. Abaye and Rava read the baraita in two ways.
  - Then the passage moves into history. Rabbi Yishmael son of Rabbi Yosei says the returning exiles from Babylonia "discovered and sanctified" these cities. This leads to the question whether the first sanctification of the land held for its time only or for ever. It goes on to Nehemiah 8:17 ("since the days of Joshua son of Nun"), which becomes aggada about Ezra.
  - So here the line between halakha and aggada falls inside one sugya.
- Other examples: Bava Batra 118b–119a (the division of the land), Gittin 6a and Kiddushin 72a (the borders of Babylonia, for divorce documents and for lineage), Makkot 9b–10a (cities of refuge), Avodah Zarah 26b–27a.

### Correction: Ein Yaakov takes the core and leaves the frame (`check_omission.py`)

I first wrote that Ein Yaakov leaves out Berakhot 44b, Bekhorot 55a and Arakhin 32b. I checked each segment (4-gram coverage, a 3-gram search over all of Ein Yaakov, and the Ein Yaakov passage it matches). This was wrong for all three. Ein Yaakov keeps the aggadic core and drops the halakhic discussion around it:

| Bavli | In Ein Yaakov | Not in Ein Yaakov |
|---|---|---|
| Berakhot 44a–b | 44a:5–6 (Rav Dimi on the fruits of the land), 44b:8 (eggs), and the **whole** food-and-health baraita as one text (Ein Yaakov Berakhot 6:25: "spleen is good for the teeth… cabbage for food, beets for healing… woe to the house the turnip passes through") | blessing halakha; the Gemara's comments between the clauses of the baraita |
| Bekhorot 55a–b | 55a:17 (Jordan = *yored* from Dan), 55a:22–55b:5 (the Euphrates, the rivers of Eden, "Yuval" = Euphrates), as Ein Yaakov Bekhorot 9:1–2 | the tithe question (is the Jordan a border?); the course of the Jordan; the vow cases |
| Arakhin 32b–33a | 32b:10–33a:7 (the sanctification in Ezra's time, Joshua's prayer, counting Jubilees, Josiah ruled the ten tribes), as Ein Yaakov Arakhin 8:3 | the walled-city list, the baraita on Gamla, Gedod and Ono, and the dispute about it |

Three effects make an amud look "left out" when it is not:
1. **Interleaving.** The Bavli interleaves a baraita with the Gemara's discussion. Ein Yaakov quotes the baraita as one block, and each Steinsaltz segment (one clause plus its discussion) gets a low score. The 8-segment windows then look "not in Ein Yaakov".
2. **Parallels.** Ein Yaakov takes a repeated text once, in one place. For example, the remedies in Avodah Zarah 28a are in Ein Yaakov under Yoma (8:19–20, the parallel at Yoma 84a). Coverage is per tractate, so the other copy counts as left out.
3. **The geography frame.** In Bekhorot 55a the place names are dense in the *halakhic* part (the tithe border), and Ein Yaakov leaves that part out. The natural-history core, which has fewer names, is in Ein Yaakov.

**Theory (for checking):** Ein Yaakov's unit is the aggadic statement taken out of its halakhic frame. Ibn Ḥabib cuts the legal argument even when it is full of biblical names, places or medicine. He keeps the statement, story or baraita that can stand alone. This explains the Kodashim halakhic midrash and the "halakhic geography" (the frame is left out), and the medicine pattern (remedy lists inside Shabbat law are left out; stories and conduct rules are kept).

## Part 3: medicine in Ein Yaakov

`medicine.py` ranks 8-segment passages by a narrow remedy vocabulary:
- Aramaic: סמא, אסותא, מעלי, קשה ל, שידא, ליתי …
- English: remedy, cure, illness, harmful to, demons, bloodletting …

It then checks Ein Yaakov coverage. Of the top 50 passages, 36% are in Ein Yaakov and 58% are in it at least in part.

Pattern: Ein Yaakov takes medicine when it is a free-standing collection or story. It leaves out medicine that sits inside a halakhic discussion.

| Passage | Frame | Ein Yaakov |
|---|---|---|
| Gittin 68b–70a (the remedy collection) | free-standing | 100% |
| Pesachim 111b (harmful spirits) | free-standing | 88% |
| Shabbat 67a (incantations for boils) | list under "ways of the Amorite" | 75% |
| Nedarim 41a, 49a (illness stories) | stories | 75–88% |
| Shabbat 61a–62a (amulets) | carrying on Shabbat | the conduct rules (61a:6–11, shoes) are in; the amulets are out |
| Shabbat 109b–110b (kos ikarin, remedy list) | healing on Shabbat | the snake-bite story (110a:1) is in; the remedy list is out |
| Avodah Zarah 28a–b (Rabbi Yoḥanan's physician) | healing on Shabbat / by gentiles | the remedies are in Ein Yaakov under Yoma 8:19–20 (parallel Yoma 84a) |
| Berakhot 44b (spleen, foods and health) | blessings | the whole baraita is in (Ein Yaakov Berakhot 6:25); the discussion is out |
| Bava Kamma 85a (bringing a doctor) | damages | 25–50% |

Limit: the narrow list still catches blood (דם) in Keritot, Niddah and Zevachim, where the topic is halakhic blood, not medicine. A list without blood terms would be cleaner.

### Ideas for a better medicine proxy

- A short Aramaic remedy formula: `ליתי … ולישחוק … ולישתי` (let him bring, crush, drink), with quantities (`תלתא`, `שבעה`, `כזית`) and plant and food names together. This formula has almost no use in halakha.
- Body-part words without legal context: few halakhic terms within ±4 segments, and no blood terms.
- Demons and incantations as their own group (שידא, מזיקין, לחש, קמיע), because Ein Yaakov treats them differently from plain medicine.

## What this means

The names + verses proxy finds **scriptural aggada** (midrash on biblical figures and verses) objectively: AUC 0.86 and κ 0.55 against Ein Yaakov. With halakhic vocabulary added as a negative signal, the model reaches AUC 0.91 and κ 0.64, and almost the same tractate ranking as Ein Yaakov (Spearman 0.94).

The remaining disagreements are mostly differences in definition, not errors:
- Ein Yaakov takes sage stories and ethics, and medicine that comes as a free-standing collection or story.
- It leaves out the halakhic frame: halakhic midrash on biblical narrative (Kodashim), the legal part of geography passages, remedy lists inside Shabbat law. It also leaves out some passages for censorship, and takes parallel texts only once.

### The model in short

Each Bavli segment is scored with the 8–16 segments around it (about one sugya), using two opposite kinds of evidence:
1. **For aggada:** biblical persons, verse citations, places, nations, and anonymous characters ("a certain man"), per 100 English words.
2. **Against aggada:** legal vocabulary (liable/exempt, permitted/prohibited, pure/impure, fit/unfit, acquire, betroth, offering, court, oath, damages) and Aramaic Stam markers (תא שמע, מיתיבי, קשיא …).

A plain logistic regression weighs these features. It is trained on 36 tractates and tested on the one left out, with Ein Yaakov as the label. The names of sages are deliberately not a feature, because they occur equally in both kinds of text. In one line: **aggada is where the Bible and its characters are dense and the legal vocabulary is thin.**

## Part 4: Ein Yaakov ↔ Bavli mapping table (`map_ein_yaakov.py`)

**In this repository:** `out/ein_yaakov_to_bavli.csv` — one row per Ein Yaakov passage that has a Bavli match (3,022 rows), with the columns `ey url - sefaria`, `sefaria url` (the Bavli range in Sefaria/Koren-Steinsaltz segments), `ey words`, `ey start`, `parallels elsewhere`. Rows without a Bavli match (section numbers, chapter endings, Mishna-only tractates) are left out. Rows from the weak anchor method are included.

`map_ein_yaakov.py` also writes a fuller local workbook, `out\ein_yaakov_bavli_map.xlsx` (not in the repository), with three sheets:
- **EinYaakov_to_Bavli:** one row per Ein Yaakov passage (3,192). Columns:
  - Sefaria ref and link (`Ein Yaakov, Berakhot 6:25`)
  - the printed Ein Yaakov section number, where the text gives it
  - the Bavli range(s) in Sefaria/Koren-Steinsaltz segments (`Berakhot 44b:10`), with Sefaria and Bekiut links
  - number of segments, and the match share
  - parallels found elsewhere in the tractate
- **Bavli_segments_in_EY:** every Bavli segment that is in Ein Yaakov, with its Ein Yaakov passage.
- **notes:** method and limits.

Results:
- 2,915 passages are assigned to Bavli segments. 2,752 of them map to one continuous range, and 163 to 2–4 ranges (Ein Yaakov skips material).
- 107 passages have only a weak anchor-based span (method=anchors).
- 95 have no match: printed section numbers alone, chapter endings, "אין אגדות בפרק זה".
- 75 are in Mishna-only tractates (Eduyot, Middot …).
- The median match share is 0.72. Below about 0.5, check by hand: it means variant wording or text that Ein Yaakov placed elsewhere.
- A repeated text far from the passage's main range (more than 40 segments away) goes to `parallels_elsewhere`, not into the mapping. This happened for 185 passages, for example Berakhot 2a:5 / 9a:8.

## Files (`out\`)

| File | Contents |
|---|---|
| `TOP_aggada_candidates_by_nonsage_names.csv` | 60 passages, Sefaria + Bekiut links, names found |
| `TOP_passages_by_all_names.csv` | 60 passages ranked by all names |
| `LOWEST_name_density_passages.csv` | 40 passages with the fewest names |
| `ALL_amudim_name_density.csv` | every amud: counts per category, densities, Stam proxies, validation flag |
| `segments.csv` | every segment (81,481), counts and the names found |
| `name_counts.csv` | mentions per gazetteer entry |
| `ALL_amudim_ein_yaakov_vs_model.csv` | every amud: Ein Yaakov share, model probability, Sefaria link |
| `segments_ey.csv` | every Gemara segment with Ein Yaakov coverage and model probability |
| `ey_passages_aligned.csv` | every Ein Yaakov passage with its Bavli span |
| `ein_yaakov_to_bavli.csv` | Ein Yaakov passage -> Bavli range, Sefaria links (Part 4) |
| `bavli_segments_ein_yaakov.csv` | every Bavli segment -> Ein Yaakov passage |
| `medicine_passages.csv` | top 50 medicine passages with Ein Yaakov share |
| `segments_feat2.csv` | set 2 counts per segment |
| `disagree_model_yes_ey_no.csv`, `disagree_ey_yes_model_no.csv` | 40 + 40 disagreement passages |

## Run

```
py -3.13 -I name_density.py      # ~10 min, segments.csv
py -3.13 -I analyze.py           # amudim.csv, windows.csv, AUCs
py -3.13 -I analyze2.py          # categories, deciles, ranked passages
py -3.13 -I analyze3.py          # editors' voice labels
py -3.13 -I build_outputs.py     # deliverable CSVs
py -3.13 -I align_ein_yaakov.py  # ~2 min, Ein Yaakov -> Bavli segments
py -3.13 -I ey_compare.py        # AUCs (needs features2.py first) and leave-one-tractate-out model
py -3.13 -I ey_disagree.py       # disagreement lists
py -3.13 -I features2.py         # set 2 counts (run before ey_compare.py)
py -3.13 -I ey_outputs.py        # amud table, recall breakdown
py -3.13 -I medicine.py          # medicine passages
py -3.13 -I map_ein_yaakov.py    # Ein Yaakov <-> Bavli mapping table
py -3.13 -I check_omission.py Berakhot 44b   # per-segment check of any amud
```
