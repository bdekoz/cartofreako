#!/usr/bin/env python3
"""Assemble the ST2 atlas, paired local review, contact sheets and receipt."""
import argparse
from html import escape
import json
from pathlib import Path
import re
import subprocess

from PIL import Image,ImageDraw,ImageFont
from legend_informatics import ROOT, FONT_DIR, SUFFIX, WIDTH, HEIGHT, digest, register_fonts
from setouchi_delivery import STANDARD_FILES


def page_count(path):
    info=subprocess.check_output(['pdfinfo',str(path)],text=True)
    return int(re.search(r'Pages:\s+(\d+)',info)[1])


def build(output):
    register_fonts()
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4,A3,landscape
    from reportlab.lib.utils import ImageReader
    book=json.loads((output/'plate-source-bibliography.json').read_text())
    entries=book['entries']
    exports=json.loads((output/'sources/sheet-export-manifest.json').read_text())['records']
    assert len(entries)==38 and len(exports)==152
    by_key={(r['stem'],r['scope'],r['kind']):r for r in exports}
    published=json.loads((output/STANDARD_FILES).read_text())['records']
    by_filename={(r['stem'],r['scope'],r['kind']):r for r in published}
    def path(entry,scope,kind,sheet='map'):
        return Path(by_filename[(entry['stem'],scope,sheet)]['files'][kind]['path'])
    proof=output/'proofs/43p5-antarctica-left';proof.mkdir(parents=True,exist_ok=True)
    proof_html=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
                '<title>Shifted network proof / Antarctica consolidated</title><style>body{font:18px/1.5 system-ui;max-width:1600px;margin:2rem auto;padding:0 1rem;color:#292722}img{width:100%;height:auto}a{color:#503b75}p{max-width:85ch}figure{margin:2rem 0}details{border:1px solid #ccc;padding:1rem}</style>',
                '<h1>Shifted network proof</h1><p>43.5-inch image on a 44-inch sheet; horizontal move +4.35 inches. Antarctica is deliberately consolidated at the lower left. Network data are unchanged. Every map has a separate legend and data bibliography.</p>',
                '<p><a href="setouchi-network-separated-proof.pdf">Four-sheet full-size PDF</a> · <a href="../../index.html">All 38 world/Japan pairs</a></p>']
    proof_pdfs=[]
    for stem in ('network-fiber','network-groundstations'):
        e=next(e for e in entries if e['stem']==stem)
        proof_html.append('<h2>'+escape(e['title'])+'</h2>')
        for sheet in ('map','legend'):
            links=' · '.join(f'<a href="../../{path(e,"world",kind,sheet)}">{sheet.title()} {kind.upper()}</a>' for kind in ('svg','pdf','png'))
            content=f'<figure><img src="../../{path(e,"world","preview",sheet)}" alt="{stem} {sheet}"><figcaption>{links}</figcaption></figure>'
            proof_html.append(content if sheet=='map' else '<details><summary>Legend and data bibliography</summary>'+content+'</details>')
            proof_pdfs.append(str(output/path(e,'world','pdf',sheet)))
    (proof/'index.html').write_text('\n'.join(proof_html)+'</html>\n')
    subprocess.run(['pdfunite',*proof_pdfs,str(proof/'setouchi-network-separated-proof.pdf')],check=True)
    controls='''<div class="controls"><label>Find a plate <input id="search" type="search" placeholder="Fiber, Japan, temperature…"></label><label>Scope <select id="scope"><option value="both">World + Japan</option><option value="world">World</option><option value="japan">Japan</option></select></label><p id="count" aria-live="polite">38 subjects · 76 plates</p></div>'''
    html=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
          '<title>Setouchi 2028 — ST2 review</title><style>body{font:18px/1.5 system-ui;color:#292722;background:#faf9f6;margin:0;padding:2rem}main,header{max-width:1800px;margin:auto}h1,h2{line-height:1.15}h1{font-size:clamp(2rem,5vw,4rem)}a{color:#503b75}p{max-width:85ch}.controls{display:flex;gap:1.5rem;align-items:end;flex-wrap:wrap;padding:1rem;background:#fff;border:1px solid #ddd;position:sticky;top:0;z-index:2}input,select{font:inherit;padding:.5rem;max-width:100%;box-sizing:border-box}label{display:grid;gap:.25rem}.pair{border-top:1px solid #ccc;padding:2rem 0}.plates{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}figure{margin:0;background:white;border:1px solid #ddd}img{display:block;width:100%;height:auto}figcaption{padding:.75rem}.downloads{display:flex;gap:1rem;flex-wrap:wrap}code{overflow-wrap:anywhere}small{display:block;color:#555}.note{padding:1rem;border-left:4px solid #503b75;background:white}button{font:inherit} [hidden]{display:none!important}@media(max-width:800px){body{padding:1rem}.plates{grid-template-columns:1fr}.controls{position:static}}</style>',
          '<header><p>CARTOFREAKO / SETOUCHI TRIENNALE 2028</p><h1>ST2 plate review</h1><p>38 world/Japan pairs: 76 legend-free maps and 76 separate legend sheets. Each legend contains its data bibliography. The outlined plate number is 36 pt bold, with white fill and a fully opaque black 0.5 pt stroke.</p>',
          '<p class="note"><strong>Approved two-sheet format for every plate:</strong> <a href="setouchi-tri-explore-v2.pdf">Open the complete 154-page proof</a>. Each world and Japan cartography/data sheet is followed immediately by its separate legend/data bibliography sheet. Standard PNG, PDF and SVG downloads use the same separation.</p>',
          '<p class="downloads"><a href="setouchi-tri-explore-v2.pdf">All plates PDF</a><a href="proofs/43p5-antarctica-left/index.html">Approved network sample</a><a href="plate-source-bibliography.json">Source ledger</a><a href="contact-sheets/contact-sheets.pdf">Contact sheets</a><a href="prototypes/africa-framing/index.html">Earlier framing comparisons</a><a href="sources/sheets-validation.json">Validation</a></p>',
          '<p>Map image width is 43.5 inches on a 44 × 19.052559-inch sheet, with proportional scaling and centered margins. The world fiber and groundstation maps use the approved horizontal move; other map registrations are retained. PDF and SVG are full-size masters; PNGs are 300 dpi. Print at actual size to evaluate physical line weights.</p>',controls,'</header><main>']
    for e in entries:
        title=f"{e['ordinal']:02d} · {e['title']}"
        html.append(f'<section class="pair" data-search="{escape((e["stem"]+" "+e["title"]).lower(),quote=True)}" id="{e["stem"]}"><h2>{escape(title)}</h2><p>{escape(e["interpretation"])}</p><p><a href="plate-source-bibliography.html#plate-{e["ordinal"]:02d}">Sources, dates and class definitions</a></p><div class="plates">')
        for scope in ('world','japan'):
            html.append(f'<figure data-scope="{scope}"><a href="{path(e,scope,"png")}"><img loading="lazy" width="2200" height="953" src="{path(e,scope,"preview")}" alt="{escape(title)} — {scope}"></a><figcaption><strong>{scope.title()}</strong><span class="downloads">'+
                        ' '.join(f'<a href="{path(e,scope,kind)}">{label}</a>' for kind,label in [('svg','SVG'),('pdf','PDF'),('png','300 dpi PNG')])+
                        f'</span><small>Map SHA-256: <code>{by_key[(e["stem"],scope,"map")]["fingerprint"]["svg_sha256"][:16]}…</code></small>'+
                        '<details><summary>Separate legend and data bibliography</summary>'+
                        f'<a href="{path(e,scope,"png","legend")}"><img loading="lazy" src="{path(e,scope,"preview","legend")}" alt="{escape(title)} — {scope} legend and bibliography"></a><span class="downloads">'+
                        ' '.join(f'<a href="{path(e,scope,kind,"legend")}">Legend {label}</a>' for kind,label in [('svg','SVG'),('pdf','PDF'),('png','300 dpi PNG')])+
                        '</span></details></figcaption></figure>')
        html.append('</div></section>')
    html.append('''</main><script>const search=document.querySelector('#search'),scope=document.querySelector('#scope');function update(){let subjects=0,plates=0;const query=search.value.trim().toLowerCase();for(const row of document.querySelectorAll('.pair')){row.hidden=!row.dataset.search.includes(query);if(!row.hidden)subjects++;for(const figure of row.querySelectorAll('figure')){figure.hidden=scope.value!=='both'&&figure.dataset.scope!==scope.value;if(!row.hidden&&!figure.hidden)plates++;}}document.querySelector('#count').textContent=`${subjects} subjects · ${plates} plates`;}search.addEventListener('input',update);scope.addEventListener('change',update);</script></html>''')
    (output/'index.html').write_text('\n'.join(html)+'\n')
    contact=output/'contact-sheets';contact.mkdir(exist_ok=True)
    pdf=Canvas(str(contact/'contact-sheets.pdf'),pagesize=landscape(A3));pw,ph=landscape(A3)
    font=ImageFont.truetype(str(FONT_DIR/'AtkinsonHyperlegible-Regular.ttf'),23)
    for scope in ('world','japan'):
        for page in range(4):
            sheet=Image.new('RGB',(2400,2900),'white');draw=ImageDraw.Draw(sheet)
            draw.text((40,20),f'Setouchi ST2 / {scope.title()} / {page+1}',font=font,fill='#292722')
            subset=entries[page*10:(page+1)*10]
            for i,e in enumerate(subset):
                col,row=i%2,i//2;x,y=40+col*1180,90+row*560
                with Image.open(output/path(e,scope,'preview')) as image:
                    image=image.convert('RGB');image.thumbnail((1130,490),Image.Resampling.LANCZOS);sheet.paste(image,(x,y))
                title=f"{e['ordinal']:02d} · {e['title']}"
                if draw.textlength(title,font=font)>1130:
                    while draw.textlength(title+'…',font=font)>1130:title=title[:-1]
                    title+='…'
                draw.text((x,y+495),title,font=font,fill='#292722')
            png=contact/f'{scope}-{page+1}.png';sheet.save(png)
            pdf.setFont('Atkinson-Bold',18);pdf.drawString(30,ph-30,f'Setouchi ST2 / {scope.title()} / {page+1}')
            # Four columns × three rows on A3 landscape for an inspectable compact PDF.
            for i,e in enumerate(subset):
                col,row=i%4,i//4;x=30+col*(pw-60)/4;y=ph-85-row*245
                image=output/path(e,scope,'preview');iw=(pw-90)/4;ih=iw*HEIGHT/WIDTH
                pdf.drawImage(ImageReader(image),x,y-ih,width=iw,height=ih)
                pdf.setFont('Atkinson-Regular',8);label=f"{e['ordinal']:02d} {e['title']}"
                pdf.drawString(x,y-ih-16,label[:55])
            pdf.showPage()
    pdf.save()
    cover=output/'sources/revision-cover.pdf';canvas=Canvas(str(cover),pagesize=A4);w,h=A4
    canvas.setTitle('Setouchi Triennale 2028 — ST2 revised atlas')
    canvas.setFont('Atkinson-Bold',32);canvas.drawString(42,h-82,'Setouchi Triennale 2028')
    canvas.setFont('Atkinson-Bold',24);canvas.drawString(42,h-122,'ST2 revised atlas')
    canvas.setFont('Atkinson-Regular',13)
    lines=['38 world/Japan pairs · 76 maps + 76 legend/source sheets','Legend informatics · bibliography on each legend · Africa framing',
           'Prepared 30 October 2026','',
           'Atlas sheets: 44 × 19.052559 inches.','All maps have separate legend and bibliography sheets.',
           'Map image width 43.5 inches, scale 98.863636%.',
           'Centered margins: 0.25 inches left/right, 0.108253 top/bottom.',
           'World fiber/groundstations shift +4.35 printed inches.','',
           'The Africa proof reconnects 14 matched cable endpoint pairs.',
           'Antarctica is deliberately consolidated at the lower left.',
           'The displayed Antarctic position is not geographically accurate.','',
           'A new legend does not update an observation period.',
           'Each legend records its providers, snapshots and methods.',
           'Physical proofing, Japanese captions and exhibition decisions',
           'remain recorded in the ST2 development document.']
    for i,line in enumerate(lines):canvas.drawString(42,h-180-i*24,line)
    canvas.showPage();canvas.setFont('Atkinson-Bold',22);canvas.drawString(42,h-48,'Plate index')
    canvas.setFont('Atkinson-Regular',10);canvas.drawString(42,h-70,'World map, world legend/sources, Japan map, Japan legend/sources.')
    for i,e in enumerate(entries):
        col,row=i//19,i%19;x=42+col*260;y=h-110-row*34
        canvas.setFont('Atkinson-Bold',9);canvas.drawString(x,y,f"Plate {e['ordinal']:02d} / PDF pages {3+4*i}–{6+4*i}")
        canvas.setFont('Atkinson-Regular',8)
        label=e['title'];canvas.drawString(x,y-12,label[:54])
    canvas.setFont('Atkinson-Regular',10);canvas.drawString(42,52,'Plate numbers identify subjects; PDF page positions are separate.')
    canvas.save()
    documents=[cover]+[output/path(e,scope,'pdf',sheet) for e in entries for scope in ('world','japan') for sheet in ('map','legend')]
    aggregate=output/'setouchi-tri-explore-v2.pdf'
    subprocess.run(['pdfunite',*[str(p) for p in documents],str(aggregate)],check=True)
    expected=sum(page_count(p) for p in documents);assert page_count(aggregate)==expected
    products=[output/'index.html',aggregate,output/STANDARD_FILES,output/'plate-source-bibliography.json',output/'plate-source-bibliography.pdf',
              output/'plate-source-bibliography.html',contact/'contact-sheets.pdf']
    manifest={'edition':'Setouchi 2028 ST2','plate_pairs':38,'maps':76,'legend_source_sheets':76,'aggregate_pages':expected,
              'aggregate_contents':[{'path':str(p.relative_to(output)),'pages':page_count(p)} for p in documents],
              'products':[{'path':str(p.relative_to(output)),'sha256':digest(p),'bytes':p.stat().st_size} for p in products],
              'plate_export_manifest_sha256':digest(output/'sources/sheet-export-manifest.json')}
    (output/'sources/revision-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Built 76-map/76-legend review, 8 contact sheets and {expected}-page aggregate PDF.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'output/setouchi-triennale-2028-st2')
    args=parser.parse_args();build(args.output)


if __name__=='__main__':main()
