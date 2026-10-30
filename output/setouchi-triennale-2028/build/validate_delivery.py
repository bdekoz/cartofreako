#!/usr/bin/env python3
from pathlib import Path
from lxml import etree as E
from PIL import Image
import concurrent.futures,csv,json,math,re,subprocess,hashlib,openpyxl
OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[1]
plan=json.loads((OUT/'sources/generation-plan.json').read_text())
assert len(plan['plates'])==38
assert len({r['stem'] for r in plan['plates']})==38
results=[]
def check_plate(path):
    scope=path.parents[1].name
    # Millions of native swarm circles do not need to live in memory at once.
    context=E.iterparse(str(path),events=('start','end'),huge_tree=True)
    _,root=next(context)
    assert math.isclose(float(root.get('width').removesuffix('in')),44)
    assert math.isclose(float(root.get('height').removesuffix('in')),19.052559)
    for event,element in context:
        if event=='end':
            element.clear()
            while element.getprevious() is not None:
                element.getparent().remove(element.getparent()[0])
    pdf=path.parent.parent/'pdf'/path.with_suffix('.pdf').name
    png=path.parent.parent/'png'/path.with_suffix('.png').name
    info=subprocess.check_output(['pdfinfo',str(pdf)],text=True)
    assert re.search(r'Pages:\s+1\b',info)
    size=re.search(r'Page size:\s+([\d.]+) x ([\d.]+)',info)
    assert abs(float(size[1])-3168)<.02 and abs(float(size[2])-1371.784248)<.02
    with Image.open(png) as im:
        assert im.size==(13200,5716),(png,im.size)
        assert all(abs(x-300)<.01 for x in im.info['dpi'])
        im.verify()
    assert pdf.stat().st_mtime>=path.stat().st_mtime and png.stat().st_mtime>=path.stat().st_mtime,('stale export',path)
    return dict(scope=scope,stem=path.stem,status='ok',inches=[44,19.052559],pixels=[13200,5716],dpi=300)
files=[]
for scope in ['world','japan']:
    found=sorted((OUT/f'plates/{scope}/svg').glob('*.svg'));assert len(found)==38,(scope,len(found))
    for fmt in ['pdf','png']:assert len(list((OUT/f'plates/{scope}/{fmt}').glob('*.'+fmt)))==38
    files+=found
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(check_plate,files))
catalogs=[]
for p in sorted((OUT/'catalogs').glob('*.pdf')):
    info=subprocess.check_output(['pdfinfo',str(p)],text=True);assert re.search(r'Pages:\s+4\b',info)
    text=subprocess.check_output(['pdftotext',str(p),'-'],text=True);assert 'Human review' in text and 'Total' in text
    catalogs.append(dict(file=str(p.relative_to(OUT)),pages=4,status='ok'))
assert len(catalogs)==9
info=subprocess.check_output(['pdfinfo',str(OUT/'proposal/shared-sea-atlas_application-draft.pdf')],text=True);assert re.search(r'Pages:\s+8\b',info)
base=ROOT/'assets.static/petroleum';data=base/'normalized'
summary=json.loads((data/'summary.json').read_text());assert summary['workbooks']==14 and summary['worksheets']==202
books={p.name:openpyxl.load_workbook(p,data_only=True) for p in (base/'opec/data').glob('*.xlsx')}
evidence=[json.loads(l) for l in (data/'opec-workbook-cells.jsonl').read_text().splitlines()]
independent_count=sum(c.value is not None for book in books.values() for sheet in book for row in sheet for c in row)
assert independent_count==len(evidence)==17920
for r in evidence:
    v=books[r['workbook']][r['sheet']][r['cell']].value
    if hasattr(v,'isoformat'):v=v.isoformat()
    assert v==r['value'],r
liquids=list(csv.DictReader((data/'opec-liquids-supply.csv').open()))
for r in liquids:
    expected=sum(books[r['workbook']][r['sheet']][c.strip()].value for c in r['cells'].split('+'))
    assert math.isclose(expected,float(r['value']),rel_tol=1e-12)
    if int(r['period'])>2025:assert r['basis']=='projection'
assert len({r['iso3'] for r in liquids if r['period']=='2030'})==14
eia=list(csv.DictReader((data/'eia-series.csv').open()))
for code in ['RUS','BRA','CAN','VEN','MEX','USA']:
    records=[r for r in eia if r['iso3']==code and r['period']=='2025' and r['metric']=='petroleum-and-other-liquid-fuels-production']
    assert records and len({r['value'] for r in records})==1
assert {'crude-oil-production','crude-oil-production-capacity','surplus-crude-oil-production-capacity','unplanned-production-outages'}<={r['metric'] for r in eia}
for stem,count in [('petroleum-eia-liquids-2025',36),('petroleum-opec-liquids-projection-2030',14)]:
    p=next((OUT/'plates/world/svg').glob(stem+'-*.svg'));r=E.parse(str(p))
    codes={e.get('data-iso3') for e in r.xpath('//*[@data-iso3]') if e.get('fill') not in ['#d6d6d2','#f0ece6']}
    assert len(codes)==count,(stem,len(codes))
for row in csv.DictReader((data/'national-series.csv').open()):
    if row['iso3']=='CAN' and row['period'] in ['2024','2025']:assert row['months']=='12'
options=json.loads((OUT/'proposal/options.json').read_text());assert len(options)==9
for o in options:assert o['total']==sum(v for _,v in o['budget'])
report=dict(status='passed',plates=results,catalogs=catalogs,application_pages=8,opec_cells_verified=independent_count,petroleum_focus_countries=['RUS','BRA','CAN','VEN','MEX','USA'],notes=['Representative visual review recorded separately; machine checks cover every plate format.','Data periods and human review gates are in sources/data-quality.md and the development document.'])
(OUT/'sources/validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'Passed: {len(results)} plate triplets, 9 catalogs, 8-page application, {independent_count:,} OPEC cells and petroleum measures')
