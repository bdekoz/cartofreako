#!/usr/bin/env python3
from pathlib import Path
import html,json,hashlib,subprocess
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
OUT=Path(__file__).resolve().parents[1]
plan=json.loads((OUT/'sources/generation-plan.json').read_text())
plates=plan['plates'];suffix='-authagraph-44-19.052559'
e=html.escape
parts=['''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cartofreako / Setouchi 2028</title><style>body{font:16px system-ui;margin:36px auto;padding:0 24px;max-width:1440px;color:#17212b;background:#fff}h1{font-size:38px;font-weight:650}h2{font-size:24px;margin-top:40px}h3{font-size:19px}p{line-height:1.5;max-width:1000px}a{color:#155b91}.links a{display:inline-block;margin:6px 18px 6px 0}article{border-top:1px solid #ccd5dd;padding:20px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}img{width:100%;height:auto;border:1px solid #ddd}small{line-height:1.5;display:block;color:#44515e}.catalogs{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.catalogs a{border:1px solid #ccd5dd;padding:16px;text-decoration:none}input{font:inherit;padding:10px;min-width:300px;margin:20px 0}@media(max-width:750px){.pair,.catalogs{grid-template-columns:1fr}h1{font-size:30px}}</style><h1>Cartofreako / Setouchi 2028</h1><p>38 world plates and 38 Japan companions, with SVG and PDF masters and 300 dpi PNGs. Nine show catalogs explore three exhibitions, three events and three site installations. Prepared 29 October 2026.</p><p>Recommended proposal: <strong>Shared Sea Atlas</strong>, an indoor exhibition to develop with an Awashima host. The eight-page application draft leaves room for verified CV and prior work within the ten-page limit.</p><div class="links"><a href="setouchi-tri-explore-v1.pdf">Complete exploration · PDF</a><a href="proposal/shared-sea-atlas_application-draft.pdf">Application draft · PDF</a><a href="proposal/proposal-and-options.md">Proposal and options</a><a href="proposal/atlas-contact-sheets.pdf">Atlas contact sheets · PDF</a><a href="proposal/petroleum-source-annex.pdf">Petroleum source annex · PDF</a><a href="sources/petroleum-explorer.html">Explore petroleum sources</a><a href="sources/data-quality.md">Data dates and limits</a><a href="sources/resource-color-key.html">Resource colour key</a><a href="prototypes/coral-reef/index.html">Coral prototype comparison</a><a href="proposal/visual-revisions-and-coral-prototypes.pdf">Visual revisions · PDF</a><a href="../../docs/pages/data/anthropocene-particulate.md">Particulate sources and coverage</a><a href="../../docs/development/20261029_particulate_data_enrichement_explore.md">Japan / Asia-28 particulate findings</a><a href="../../docs/development/20261029_setouchi_triennale_explore.md">Human reviews and next steps</a></div><p>Observation periods vary. Some particulate and infrastructure layers retain earlier snapshots. OPEC future values are projections. Country totals do not measure individual islands; celestial companions use sky context. Full details are in the source notes.</p><h2>Show catalogs</h2><div class="catalogs">''']
for p in sorted((OUT/'catalogs').glob('*.pdf')):parts.append(f'<a href="catalogs/{e(p.name)}">{e(p.stem.replace("_"," "))}<small>Four-page PDF · concept, layout, budget and review</small></a>')
parts.append('</div><h2>Print plates</h2><p>Each sheet: 44 × 19.052559 in. PNG: 13,200 × 5,716 pixels. PDFs retain vector artwork; the world swarm PDF embeds fonts and other plate PDFs outline text. Source SVG retains text. Use a physical colour and legibility proof before production.</p><label>Find a plate <input id="find" type="search" placeholder="Water, Japan, petroleum, sky…"></label><div id="plates">')
for p in plates:
    parts.append(f'<article data-search="{e((p["title"]+" "+p["stem"]).lower())}"><h3>{e(p["title"])}</h3><div class="pair">')
    for scope,label in [('world','World'),('japan','Japan companion')]:
        stem=p['stem']+suffix+('-japan' if scope=='japan' else '')
        parts.append(f'<div><img loading="lazy" src="previews/{scope}/{stem}.png" alt="{e(label+": "+p["title"])}"><div class="links"><strong>{label}</strong> ')
        for ext in ['svg','pdf','png']:parts.append(f'<a href="plates/{scope}/{ext}/{stem}.{ext}">{ext.upper()}</a>')
        parts.append('</div></div>')
    parts.append(f'</div><small>{e(p["note"])}</small></article>')
parts.append('</div><script>document.querySelector("#find").oninput=e=>{const q=e.target.value.toLowerCase();document.querySelectorAll("article").forEach(a=>a.hidden=!a.dataset.search.includes(q))}</script></html>')
(OUT/'index.html').write_text(''.join(parts))
pdfmetrics.registerFont(TTFont('AtlasSans','/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf'))
w,h=landscape(A4);c=canvas.Canvas(str(OUT/'proposal/atlas-contact-sheets.pdf'),pagesize=(w,h));c.setTitle('Cartofreako / Setouchi 2028 / atlas contact sheets')
for scope in ['world','japan']:
    for start in range(0,len(plates),9):
        c.setFont('AtlasSans',18);c.drawString(32,h-35,('World' if scope=='world' else 'Japan companions')+' / '+str(start+1)+'–'+str(min(start+9,len(plates))))
        for j,p in enumerate(plates[start:start+9]):
            col,row=j%3,j//3;x=32+col*260;y=h-80-row*165
            stem=p['stem']+suffix+('-japan' if scope=='japan' else '')
            image=OUT/f'previews/{scope}/{stem}.png';assert image.exists()
            c.drawImage(str(image),x,y-110,width=242,height=104.8)
            c.setFont('AtlasSans',8)
            title=p['title']
            while pdfmetrics.stringWidth(title,'AtlasSans',8)>245:title=title[:-2]
            c.drawString(x,y-125,title)
        c.setFont('AtlasSans',8);c.drawString(32,20,'Study edition · 29 October 2026 · See individual plates and source notes for units and dates.');c.showPage()
c.save()
readme='''# Cartofreako / Setouchi Triennale 2028

Open [index.html](index.html) for the visual inventory and all downloads.
See [GIT-CONTENTS.md](GIT-CONTENTS.md) for the versioned review package and local print exports.

The [aggregate exploration PDF](setouchi-tri-explore-v1.pdf) brings together all
38 world/Japan pairs, nine catalogs, the application draft, contact sheets,
petroleum annex, resource colour key, coral prototypes, source notes and pending human reviews. Vector maps remain
zoomable; the PDF is a study volume, separate from the application packet.

- 38 world plates and 38 Japan companions; SVG, PDF and 300 dpi PNG (228 print files).
- Nine four-page catalogs: three exhibitions, three events, three installations.
- Eight-page [application draft](proposal/shared-sea-atlas_application-draft.pdf),
  [proposal/options](proposal/proposal-and-options.md), ten-page contact sheets,
  and four-page petroleum source annex.
- [Offline petroleum explorer](sources/petroleum-explorer.html),
  [source periods and limits](sources/data-quality.md), machine validation and checksums.

Full print size: 44 × 19.052559 inches; PDF 3,168 × 1,371.784248 points;
PNG 13,200 × 5,716 pixels, 300 dpi. Historical layers remain explicitly dated.
No application, payment, outreach or publication has been performed.

Petroleum source assets are in `../../assets.static/petroleum`. OPEC's 14 supplied
workbooks are all retained, with independent EIA, ANP and Statistics Canada data.
The existing global refinery layer uses the repaired official UNSD endpoint.

## Reproduce the delivered files from pinned local inputs

The compiled generators and exact compilation command are in `build/`; the
code revisions are in `sources/repository-state.json`. Keep the current
Cartofreako checkout, sibling izzi headers, Natural Earth files and sibling
cloud_cdn_cache.bkoz and Alpha60 sample/cache dependencies available at their recorded paths. No network refresh is needed
to reproduce the maps from the pinned sources.

The native swarm run requires the extracted cumulative documents in
`build/swarm-runtime/cache`, the sibling Alpha60 executable/data, the recorded
IPinfo database and `build/swarm-runtime/earth-ck-44-22.svg`. Raw participant
cache files and native render intermediates are ignored by Git and excluded
from the delivery inventory. Their hashes and extraction inventory remain in
`sources/swarm-cache-extraction.json` and `sources/swarm-refresh.json`.
`build_swarm.py --compose-only` reuses an existing native render.

```bash
python3 output/setouchi-triennale-2028/build/render_world.py
python3 scripts/prepare-petroleum-data.py
python3 output/setouchi-triennale-2028/build/build_petroleum.py
python3 output/setouchi-triennale-2028/build/build_japan.py
python3 output/setouchi-triennale-2028/build/export_plates.py
python3 output/setouchi-triennale-2028/build/build_catalogs.py
python3 output/setouchi-triennale-2028/build/build_index.py
python3 output/setouchi-triennale-2028/build/build_resource_key.py
PYTHONPATH=/tmp/cartofreako-pdf-deps python3 output/setouchi-triennale-2028/build/build_visual_annex.py
PYTHONPATH=/tmp/cartofreako-pdf-deps python3 output/setouchi-triennale-2028/build/build_aggregate.py
python3 output/setouchi-triennale-2028/build/validate_delivery.py
PYTHONPATH=/tmp/cartofreako-pdf-deps python3 output/setouchi-triennale-2028/build/verify_refinements.py
```

These are repository-root commands. `refresh_resources.py` is the task's raw
download/preparation helper; rerunning it is a new data refresh and requires
checking revised source metadata and observation-year labels before promotion.
The delivery uses the finalized `sources/data/resources` profile, not the
intermediate `resources-current` directory. NOAA historical raw files are
read-only symlinks to the existing local cache.

Human review and next steps are appended to
`../../docs/development/20261029_setouchi_triennale_explore.md`.
'''
(OUT/'README.md').write_text(readme)
print('Wrote index, README and ten-page atlas contact sheets')
