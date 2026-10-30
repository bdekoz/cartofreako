#!/usr/bin/env python3
"""Task-local refresh with the verified UNSD SDMX endpoint, retaining raw evidence."""
from pathlib import Path
import concurrent.futures,csv,json,subprocess,zipfile
from lxml import etree
OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[1]
RAW=OUT/'sources/resources-raw'
RAW.mkdir(exist_ok=True)
JOBS={
'natural-earth.zip':'https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip',
'irena-2026.pdf':'https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2026/Mar/IRENA_DAT_RE_capacity_statistics_2026.pdf',
'usgs-mcs2026.pdf':'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026.pdf',
'iaea-rds-2-45.pdf':'https://www-pub.iaea.org/MTCD/publications/PDF/RDS-2-45_web.pdf',
'reefs-at-risk-present.kmz':'https://wriorg.s3.amazonaws.com/s3fs-public/reefs_at_risk_revisited_present.kmz',
'undata-sdmx.csv':'https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY,/A..GR.086/?startPeriod=2018&format=csv',
}
CODES=['AG.PRD.FOOD.XD','AG.LND.FRST.ZS','ER.FSH.PROD.MT','IP.PAT.RESD','SE.ADT.LITR.ZS','SE.SEC.CUAT.UP.ZS','SE.TER.CUAT.BA.ZS','SE.TER.CUAT.MS.ZS','SP.POP.0014.TO','SP.POP.1519.FE.5Y','SP.POP.1519.MA.5Y','SP.POP.2024.FE.5Y','SP.POP.2024.MA.5Y','SP.POP.2529.FE.5Y','SP.POP.2529.MA.5Y','SP.POP.6064.FE.5Y','SP.POP.6064.MA.5Y','SP.POP.65UP.TO','SP.POP.TOTL','SP.POP.TOTL.FE.IN','SP.POP.TOTL.MA.IN']
for code in CODES:JOBS[f'cartofreako-wb-{code}.json']=f'https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=20000'
def fetch(item):
 name,url=item
 target=RAW/name
 if target.is_file() and target.stat().st_size>100:return (name,0)
 p=subprocess.run(['curl','--fail','--silent','--show-error','--location','--connect-timeout','15','--max-time','120','--output',str(target)+'.part',url],capture_output=True,text=True)
 if p.returncode==0:Path(str(target)+'.part').replace(target)
 print(name,p.returncode,p.stderr.strip(),flush=True)
 return (name,p.returncode)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(fetch,JOBS.items()))
(RAW/'download-manifest.json').write_text(json.dumps({'date':'2026-10-29','urls':JOBS,'results':results},indent=2)+'\n')
if any(code for _,code in results):raise SystemExit('Some source downloads failed; baseline preserved.')
with zipfile.ZipFile(RAW/'natural-earth.zip') as z:z.extractall(RAW/'natural-earth')
dsd=etree.parse(str(OUT/'sources/undata-energy-dsd.xml'))
names={e.get('id'):' '.join(e.xpath('./*[local-name()="Name"]/text()')) for e in dsd.xpath('//*[local-name()="Codelist"][@id="CL_AREA_NRG"]/*[local-name()="Code"]')}
rows=list(csv.DictReader((RAW/'undata-sdmx.csv').open()))
assert len(rows)>600
assert all(x['COMMODITY']=='GR' and x['TRANSACTION']=='086' and x['FREQ']=='A' and x['UNIT_MEASURE']=='TN' and x['UNIT_MULT']=='3' for x in rows)
assert len({(x['REF_AREA'],x['TIME_PERIOD']) for x in rows})==len(rows)
with (RAW/'undata-refinery.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Country or Area','Commodity - Transaction','Year','Unit','Quantity','Quantity Footnotes'])
 for x in rows:w.writerow([names[x['REF_AREA']],'Total refinery throughput',x['TIME_PERIOD'],'Metric tons, thousand',x['OBS_VALUE'],'1' if x['OBS_STATUS']=='E' else ''])
preparer=OUT/'build/prepare-resources-current.py'
code=(ROOT/'scripts/prepare-resources-data.py').read_text().replace('SNAPSHOT_DATE = "2026-08-06"','SNAPSHOT_DATE = "2026-10-29"')
code=code.replace('from osgeo import ogr','').replace('ogr.UseExceptions()','')
start=code.index('def prepare_reef_grid(')
end=code.index('\ndef wb_metric_values(',start)
cached_reef = f"""def prepare_reef_grid(source, output):
    # WRI's 2011 file is unchanged. Reuse the verified normalized grid.
    import shutil
    require(hashlib.sha256(source.read_bytes()).hexdigest() == "e0a8ae274f212dc8e7dc05bd50054a8b6fa67786d0b201579ee71cd46cac4bcd", "WRI source changed; full grid re-preparation required")
    original = Path({str(ROOT/'assets.static/resources/coral-reefs-025deg.geojson')!r})
    shutil.copy2(original, output)
    return json.loads(output.read_text())["cartofreako"]

"""
code=code[:start]+cached_reef+code[end:]
preparer.write_text(code)
args=['python3',str(preparer),'--natural-earth-shapefile',str(RAW/'natural-earth/ne_110m_admin_0_countries.shp'),'--natural-earth-archive',str(RAW/'natural-earth.zip'),'--irena-pdf',str(RAW/'irena-2026.pdf'),'--iaea-pdf',str(RAW/'iaea-rds-2-45.pdf'),'--usgs-pdf',str(RAW/'usgs-mcs2026.pdf'),'--refinery-csv',str(RAW/'undata-refinery.csv'),'--reef-kmz',str(RAW/'reefs-at-risk-present.kmz'),'--world-bank-cache',str(RAW),'--output-dir',str(OUT/'sources/data/resources-current')]
raise SystemExit(subprocess.run(args).returncode)
