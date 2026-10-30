#!/usr/bin/env python3
"""Source-indexed petroleum additions using current native AuthaGraph geometry."""
from pathlib import Path
from lxml import etree as E
import copy,csv,json,re,html,shutil,subprocess
OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[1]
BASE=ROOT/'assets.static/petroleum'
DATA=BASE/'normalized'
NS='http://www.w3.org/2000/svg'
def el(tag,parent=None,**a):
    e=E.Element('{'+NS+'}'+tag,nsmap={None:NS}) if parent is None else E.SubElement(parent,'{'+NS+'}'+tag)
    for k,v in a.items():e.set(k.replace('_','-'),str(v))
    return e
def txt(p,x,y,s,size=.25):el('text',p,x=x,y=y,font_family='Liberation Sans',font_size=size,fill='#152330').text=s
records=list(csv.DictReader((DATA/'eia-series.csv').open()))
values={r['iso3']:float(r['value']) for r in records if r['iso3'] and r['period']=='2025' and r['table'] in ['3b','3c'] and r['value']}
forecast={r['iso3']:float(r['value']) for r in csv.DictReader((DATA/'opec-liquids-supply.csv').open()) if r['period']=='2030'}
countries={r['iso3']:r for r in csv.DictReader((DATA/'opec-country-coverage.csv').open())}
source=next((OUT/'plates/world/svg').glob('*refinery*.svg'))
root=E.parse(str(source),E.XMLParser(huge_tree=True)).getroot()
geometry=root.xpath('//*[@id="resource-country-coverage"]')[0]
bins=[.1,.5,1,2,5,10,25]
colors=['#fff0c8', '#c59225', '#ca6924', '#865a3d', '#7d4e2d', '#800505', '#51372a']
items=[]
for stem,title,note in [
 ('petroleum-eia-liquids-2025','Petroleum and other liquid fuels / 2025','EIA Short-Term Energy Outlook, October 2026, tables 3b/3c. Annual historical/estimated production, million barrels/day. Includes crude, condensate, NGLs, other liquids and processing gain. 36 country observations; missing is not zero. Japan has no separate production entry in these tables.'),
 ('petroleum-opec-liquids-projection-2030','OPEC total liquids / 2030 projection','OPEC World Oil Outlook 2026, tables 4.1 and 8.7 and figures 4.7–4.11. Total liquids supply projection for 14 individually reported countries. Other countries remain missing; DoC and regional totals are not allocated. Source components and cell addresses are retained. Japan has no separate total-liquids projection in these series.'),
 ('petroleum-opec-country-coverage-2026','World Oil Outlook / country coverage','OPEC World Oil Outlook 2026: all 14 supplied workbooks and 202 worksheets retained. Country figures are indexed separately from regional definitions. Grey countries have no separately indexed country figure; no regional totals are allocated to countries. This plate measures source coverage, not oil production.')]:
    doc=el('svg',width='44in',height='19.052559in',viewBox='0 0 44 19.052559')
    el('title',doc).text=title;el('desc',doc).text=note
    el('rect',doc,width=44,height=19.052559,fill='#faf8f3')
    g=el('g',doc,id='petroleum-country-geometry')
    mapped=set()
    for e in geometry.iter():
        if E.QName(e).localname!='path':continue
        match=re.search(r'resource-(?:missing|value)-([A-Z]{3})-',e.get('id',''))
        if not match:continue
        code=match[1];mapped.add(code)
        if 'coverage' not in stem:
            v=(values if 'eia' in stem else forecast).get(code)
            fill='#d6d6d2' if v is None else colors[next((i for i,b in enumerate(bins) if v<=b),len(bins)-1)]
            label=f'{code}: no reported country value' if v is None else f'{code}: {v:g} million barrels/day, '+('2025 historical/estimate' if 'eia' in stem else '2030 PROJECTION')
        else:
            r=countries.get(code);numeric=r and int(r['numeric_country_cells'])>0
            fill='#865a3d' if numeric else '#d6d6d2' if r else '#f0ece6'
            label=f'{code}: '+('country figures indexed' if numeric else 'no separate country value assigned' if r else 'not matched in report register')
        p=el('path',g,d=e.get('d'),fill=fill,stroke=fill,stroke_width='.006',data_iso3=code)
        el('title',p).text=label
    if 'eia' in stem and 'BHR' not in mapped:
        point=subprocess.check_output([str(OUT/'build/project-points')],input='50.55 26.05\n',text=True).split()
        v=values['BHR'];color=colors[next(i for i,b in enumerate(bins) if v<=b)]
        e=el('circle',g,cx=point[0],cy=point[1],r='.045',fill=color,stroke='#333333',stroke_width='.008',data_iso3='BHR')
        el('title',e).text=f'Bahrain: {v:g} million barrels/day; point symbol because the 1:110m layer lacks a polygon'
    legend=el('g',doc,id='petroleum-legend')
    el('rect',legend,x=.6,y=15.8,width=20.8,height=2.9,fill='white',opacity='.97')
    txt(legend,.9,16.25,title,.37)
    if 'coverage' not in stem:
        for i,(color,b) in enumerate(zip(colors,bins)):
            el('rect',legend,x=.9+i*2.2,y=16.65,width=.45,height=.35,fill=color)
            txt(legend,1.45+i*2.2,16.93,'≤ '+str(b),.23)
        txt(legend,.9,17.5,'Million barrels/day · '+('2025 historical/estimate · EIA October 2026' if 'eia' in stem else '2030 PROJECTION · OPEC World Oil Outlook 2026'),.25)
        txt(legend,.9,18,'Grey = no separate value · '+('36 countries · Bahrain as point · includes processing gain' if 'eia' in stem else '14 country projections · no regional allocation'),.23)
    else:
        txt(legend,.9,16.9,'Blue = country figures indexed · Grey = no separate country figures',.26)
        txt(legend,.9,17.5,f'{len(countries)} countries/territories retained in register · small territories may lack map geometry',.23)
        txt(legend,.9,18,'All source cells retained · forecasts remain forecasts · no regional allocation',.23)
    el('metadata',doc).text=json.dumps({'source':str(DATA.relative_to(ROOT)),'projection_geometry':'current native resources generator','mapped_country_count':len(mapped),'note':note})
    dest=OUT/'plates/world/svg'/(stem+'-authagraph-44-19.052559.svg')
    E.ElementTree(doc).write(str(dest),encoding='UTF-8',xml_declaration=True)
    items.append(dict(stem=stem,title=title,note=note,destination=str(dest.parent),command=['python3',str(Path(__file__).resolve())]))
planpath=OUT/'sources/generation-plan.json';plan=json.loads(planpath.read_text())
plan['plates']=[i for i in plan['plates'] if not i['stem'].startswith('petroleum-')]+items
planpath.write_text(json.dumps(plan,indent=2)+'\n')

# A self-contained source browser; works from file:// with no fetch or network.
dataset={name:list(csv.DictReader((DATA/name).open())) for name in ['requested-country-coverage.csv','opec-country-coverage.csv','opec-country-cells.csv','opec-liquids-supply.csv','eia-series.csv','national-series.csv']}
payload=json.dumps(dataset,ensure_ascii=False).replace('</','<\\/')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Petroleum source explorer</title><style>body{font:16px system-ui;max-width:1400px;margin:40px auto;padding:0 24px;color:#17212b}h1{font-size:32px}p{max-width:1000px;line-height:1.5}table{border-collapse:collapse;font-size:13px;width:100%}td,th{padding:9px;border-bottom:1px solid #ddd;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#eaf0f5}input,select{font:inherit;padding:10px;margin:8px 12px 20px 0}#scroll{overflow:auto;max-height:70vh}td{max-width:400px;overflow-wrap:anywhere}a{color:#155b91}</style><h1>Petroleum / sources and country coverage</h1><p>OPEC World Oil Outlook 2026 plus independent EIA, ANP Brazil, Statistics Canada and UNSD evidence. Production, throughput, capacity and forecasts remain separate. A regional total is never assigned to each country in that region. Empty cells mean missing, never zero.</p><p>OPEC: all 14 workbooks, 202 worksheets and all nonempty cells are retained in the normalized source files. The country index provides direct worksheet/cell references; consult the original headings for component, growth and scenario definitions. Regional series remain in the full cell ledger.</p><label>Dataset <select id="dataset"></select></label><label>Search <input id="search" type="search" placeholder="Country, ISO3, metric, year"></label><p id="count"></p><div id="scroll"><table><thead></thead><tbody></tbody></table></div><p>Sources: <a href="https://publications.opec.org/woo">OPEC</a> · <a href="https://www.eia.gov/outlooks/steo/data.php?type=tables">EIA</a> · <a href="https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/anuario/anuario-estatistico-2026-dados-abertos">ANP</a> · <a href="https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2510006301">Statistics Canada</a>. Local source files and SHA256SUMS: assets.static/petroleum.</p><script>const data=PAYLOAD;const select=document.querySelector('#dataset'),search=document.querySelector('#search');for(const name of Object.keys(data)){const o=document.createElement('option');o.value=name;o.textContent=name;select.append(o)}function render(){const rows=data[select.value],q=search.value.toLowerCase(),filtered=rows.filter(r=>Object.values(r).some(v=>String(v).toLowerCase().includes(q)));document.querySelector('#count').textContent=filtered.length+' matching rows; showing up to 500. Source files contain every row.';const head=document.querySelector('thead'),body=document.querySelector('tbody');head.replaceChildren();body.replaceChildren();const keys=Object.keys(rows[0]),tr=document.createElement('tr');for(const k of keys){const th=document.createElement('th');th.textContent=k;tr.append(th)}head.append(tr);for(const r of filtered.slice(0,500)){const t=document.createElement('tr');for(const k of keys){const td=document.createElement('td');td.textContent=r[k];t.append(td)}body.append(t)}}select.onchange=render;search.oninput=render;render();</script></html>'''.replace('PAYLOAD',payload)
(OUT/'sources/petroleum-explorer.html').write_text(page)
for name in ['summary.json','requested-country-coverage.csv','opec-country-coverage.csv','national-series.csv']:
    shutil.copy2(DATA/name,OUT/'sources'/('petroleum-'+name))
print('Added three petroleum plates and offline source explorer')
