"""Build docs/index.html (GitHub Pages) from ein_yaakov_to_bavli.csv.

Run: py -3.13 -I build_page.py
"""
import csv
import html
import json
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
EY_ROOT = "https://www.sefaria.org/Ein_Yaakov%2C_"
SEF_ROOT = "https://www.sefaria.org/"

rows = list(csv.DictReader(open(ROOT / "ein_yaakov_to_bavli.csv", encoding="utf-8-sig")))
data = []
for r in rows:
    ey, bv = r["ey url - sefaria"], r["sefaria url"]
    data.append([ey[len(EY_ROOT):] if ey.startswith(EY_ROOT) else ey,
                 bv[len(SEF_ROOT):] if bv.startswith(SEF_ROOT) else bv,
                 int(r["ey words"] or 0), r["ey start"], r["parallels elsewhere"]])
tractates = list(dict.fromkeys(d[0].split(".")[0] for d in data))

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ein Yaakov to Bavli map</title>
<meta name="description" content="Every passage of Ein Yaakov mapped to its place in the Babylonian Talmud, with Sefaria links (Koren/Steinsaltz segment numbers).">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@400;500&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
<style>
:root {{ --bg:#fbfaf7; --fg:#1d1d1b; --muted:#6b6a65; --line:#e3e0d8; --head:#f1eee6; --link:#1f5f8b; --hit:#fff3c4; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#16171a; --fg:#e8e6e1; --muted:#a09d96; --line:#2d2f34; --head:#202226; --link:#8cc2ea; --hit:#4a3f12; }}
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 "Source Sans 3", system-ui, sans-serif; }}
main {{ max-width:1180px; margin:0 auto; padding:28px 16px 60px; }}
h1 {{ font-size:1.6rem; margin:0 0 6px; font-weight:600; }}
p {{ margin:6px 0; max-width:820px; }}
.muted {{ color:var(--muted); font-size:.92rem; }}
a {{ color:var(--link); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
.controls {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:18px 0 10px; }}
select, input {{ font:inherit; padding:6px 9px; border:1px solid var(--line); border-radius:6px; background:var(--bg); color:var(--fg); }}
input {{ flex:1 1 260px; }}
.wrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:8px; }}
table {{ border-collapse:collapse; width:100%; }}
th, td {{ padding:6px 10px; border-bottom:1px solid var(--line); vertical-align:top; text-align:left; }}
th {{ position:sticky; top:0; background:var(--head); font-weight:600; white-space:nowrap; }}
td.ref {{ white-space:nowrap; font-variant-numeric:tabular-nums; }}
td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
td.he {{ font-family:"Frank Ruhl Libre", serif; font-size:1.05rem; min-width:280px; }}
td.par {{ font-size:.88rem; color:var(--muted); }}
</style>
</head>
<body>
<main>
<h1>Ein Yaakov &rarr; Bavli</h1>
<p>Each passage of <i>Ein Yaakov</i> (Sefaria's text) with the place in the Babylonian Talmud that it comes from. The Bavli
references use Sefaria's segment numbers, which follow the Koren / Steinsaltz edition. The map was made by matching the
Hebrew/Aramaic texts; see the <a href="https://github.com/EzraBrand/ein-yaakov-bavli-map#readme">README</a> for the method and its limits.</p>
<p class="muted">{len(data):,} passages &middot; data: <a href="https://github.com/EzraBrand/ein-yaakov-bavli-map/blob/main/ein_yaakov_to_bavli.csv">ein_yaakov_to_bavli.csv</a>
&middot; built {date.today().strftime('%d-%b-%Y')} &middot; texts from Sefaria (Bavli: William Davidson Edition, CC-BY-NC)</p>
<div class="controls">
  <select id="tr" aria-label="Tractate"><option value="">All tractates</option>{"".join(f'<option>{html.escape(t)}</option>' for t in tractates)}</select>
  <input id="q" type="search" placeholder="Search a ref (Berakhot.44b) or Hebrew words" aria-label="Search">
  <span id="count" class="muted"></span>
</div>
<div class="wrap"><table>
<thead><tr><th>ey url - sefaria</th><th>sefaria url</th><th>ey words</th><th>ey start</th><th>parallels elsewhere</th></tr></thead>
<tbody id="tb"></tbody>
</table></div>
</main>
<script>
const D = {json.dumps(data, ensure_ascii=False)};
const tb = document.getElementById("tb"), q = document.getElementById("q"), tr = document.getElementById("tr"),
      count = document.getElementById("count");
const esc = s => s.replace(/[&<>"]/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}})[c]);
function render() {{
  const t = tr.value, s = q.value.trim().toLowerCase();
  const rows = D.filter(r => (!t || r[0].split(".")[0] === t) &&
    (!s || r[0].toLowerCase().includes(s) || r[1].toLowerCase().includes(s) || r[3].includes(q.value.trim()) || r[4].toLowerCase().includes(s)));
  tb.innerHTML = rows.map(r =>
    `<tr><td class="ref"><a href="https://www.sefaria.org/Ein_Yaakov%2C_${{r[0]}}" target="_blank" rel="noopener">${{esc(r[0])}}</a></td>` +
    `<td class="ref"><a href="https://www.sefaria.org/${{r[1]}}" target="_blank" rel="noopener">${{esc(r[1])}}</a></td>` +
    `<td class="num">${{r[2]}}</td><td class="he" dir="rtl" lang="he">${{esc(r[3])}}</td><td class="par">${{esc(r[4])}}</td></tr>`).join("");
  count.textContent = rows.length.toLocaleString() + " rows";
}}
q.addEventListener("input", render); tr.addEventListener("change", render); render();
</script>
</body>
</html>
"""
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs" / "index.html").write_text(page, encoding="utf-8")
print("docs/index.html:", len(data), "rows,", len(page) // 1024, "KB")
