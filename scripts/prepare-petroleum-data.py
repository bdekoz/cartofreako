#!/usr/bin/env python3
"""Normalize local petroleum sources without mixing measures or inventing countries.

Requires openpyxl and the system iso-codes JSON. No network calls. Source files
remain untouched. Run from the repository root after downloading the sources.
"""
from pathlib import Path
import calendar
import collections
import csv
import hashlib
import json
import re
import subprocess
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'assets.static/petroleum'
OUT = BASE / 'normalized'
OUT.mkdir(exist_ok=True)
iso = json.loads(Path('/usr/share/iso-codes/json/iso_3166-1.json').read_text())['3166-1']
lookup = {n.casefold(): c['alpha_3'] for c in iso for n in [c['name'], c.get('official_name',''), c.get('common_name','')] if n}
aliases = {'US':'USA','USA':'USA','UK':'GBR','Russia':'RUS','IR Iran':'IRN','Iran':'IRN','Venezuela':'VEN','Bolivia':'BOL','Brunei':'BRN','Korea':'KOR','South Korea':'KOR','Korea (Republic of)':'KOR','Vietnam':'VNM','Türkiye':'TUR','Congo (Brazzaville)':'COG','Congo (Democratic Republic of the)':'COD','People’s Republic of China':'CHN','Korea (Democratic People’s Republic of)':'PRK','China, Hong Kong SAR':'HKG','Cameroon (United Republic of)':'CMR','Gambia (The)':'GMB','Cape Verde':'CPV','Lao People’s Democratic Republic':'LAO','Micronesia (Federated States of)':'FSM','Moldova (Republic of)':'MDA','Republic of North Macedonia':'MKD','São Tomé and Príncipe':'STP','St. Kitts and Nevis':'KNA','St. Lucia':'LCA','St. Pierre et Miquelon':'SPM','St. Vincent and the Grenadines':'VCT','British Virgin Islands':'VGB','Tanzania':'TZA','Bolivia (Plurinational State of)':'BOL','Taiwan':'TWN','Ivory Coast':'CIV','United States Virgin Islands':'VIR','Congo (Democratic Republic of)':'COD','Congo, Dem Rep':'COD','Sao Tome / Principe':'STP','Gambia, The':'GMB'}
lookup.update({k.casefold(): v for k,v in aliases.items()})
def country(v):
    return lookup.get(str(v).strip().rstrip('*').casefold(), '')
def writecsv(name, rows, fields=None):
    fields=fields or list(rows[0])
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def yearof(value):
    if hasattr(value,'year'):return value.year
    if isinstance(value,(int,float)) and 1900<=value<=2100 and int(value)==value:return int(value)
    return None

# Lossless workbook evidence: retain every non-empty cell, including footnotes,
# merged ranges and display formats. Country index is supplementary, not a
# lossy replacement for the regional and scenario tables.
cells=[];sheets=[];countrycells=[];countryrefs=collections.defaultdict(set)
for path in sorted((BASE/'opec/data').glob('*.xlsx')):
    book=openpyxl.load_workbook(path,data_only=True)
    for s in book:
        title=str(s['A2'].value or s.title);unit=str(s['A3'].value or '')
        grid=[[c.value for c in row] for row in s]
        title_countries={code for name,code in lookup.items() if re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',title.casefold()) and len(name)>2}
        # Specific country chart titles; no attribution from a multi-country title.
        title_country=next(iter(title_countries)) if len(title_countries)==1 else ''
        if title.startswith('US '):title_country='USA'
        if title.startswith('UK '):title_country='GBR'
        numeric=0
        for row in s:
            for c in row:
                if c.value is None:continue
                value=c.value
                if hasattr(value,'isoformat'):value=value.isoformat()
                item=dict(workbook=path.name,sheet=s.title,title=title,unit=unit,cell=c.coordinate,row=c.row,column=c.column,value=value,number_format=c.number_format)
                cells.append(item)
                if isinstance(value,(int,float)) and not isinstance(value,bool):
                    numeric+=1
                    left=[s.cell(c.row,k).value for k in range(1,c.column)]
                    above=[s.cell(k,c.column).value for k in range(5,c.row)]
                    row_iso=next((country(v) for v in left if country(v)), '')
                    col_iso=next((country(v) for v in reversed(above) if country(v)), '')
                    code=row_iso or col_iso or title_country
                    if code:
                        refs=[str(v) for v in left if v is not None]
                        headers=[str(v) for v in above if v is not None and not isinstance(v,(int,float))]
                        year_headers=[s.cell(k,c.column).value for k in range(5,min(c.row,8))]
                        years=[yearof(v) for v in (year_headers+left) if yearof(v) is not None]
                        # Year headers themselves remain in the cell ledger only.
                        if 1900<=value<=2100 and c.row<=7:continue
                        countrycells.append(dict(iso3=code,workbook=path.name,sheet=s.title,title=title,unit=unit,cell=c.coordinate,row_labels=' | '.join(refs),column_labels=' | '.join(headers),year=years[-1] if years else '',value=value,basis='projection' if years and years[-1]>2025 else 'source-defined; see worksheet'))
                        countryrefs[code].add(path.name+' / '+s.title)
        sheets.append(dict(workbook=path.name,sheet=s.title,title=title,unit=unit,numeric_cells=numeric,merged_ranges=[str(r) for r in s.merged_cells.ranges]))
with (OUT/'opec-workbook-cells.jsonl').open('w') as f:
    for r in cells:f.write(json.dumps(r,ensure_ascii=False)+'\n')
(OUT/'opec-worksheets.json').write_text(json.dumps(sheets,indent=2,ensure_ascii=False)+'\n')
writecsv('opec-country-cells.csv',countrycells)

textpath=OUT/'woo-2026.txt'
subprocess.run(['pdftotext','-layout',str(BASE/'opec/woo-2026.pdf'),str(textpath)],check=True)
report=textpath.read_text()
annex=report[report.rfind('OECD                                                              NON-OECD COUNTRIES'):]
# Keep all regional definitions (Annexes B, C and D).
annex_labels=[]
for line in annex.splitlines():
    for label in re.split(r'\s{3,}',line.strip()):
        if country(label):annex_labels.append((label,country(label)))
coverage={code:dict(iso3=code,country=next((c['name'] for c in iso if c['alpha_3']==code),code),in_regional_definitions=False,numeric_country_cells=0,worksheets='') for code in countryrefs}
# Also retain individually named geographies elsewhere in the report.
named_mentions=[]
for label,code in [(c['name'],c['alpha_3']) for c in iso]+list(aliases.items()):
    if len(label)>3 and re.search(r'(?<![A-Za-z])'+re.escape(label)+r'(?![A-Za-z])',report):
        named_mentions.append((label,code))
for label,code in named_mentions:
    coverage.setdefault(code,dict(iso3=code,country=label,in_regional_definitions=False,numeric_country_cells=0,worksheets=''))
for label,code in annex_labels:
    coverage.setdefault(code,dict(iso3=code,country=label,in_regional_definitions=True,numeric_country_cells=0,worksheets=''))['in_regional_definitions']=True
for code,r in coverage.items():
    r['numeric_country_cells']=sum(x['iso3']==code for x in countrycells)
    r['worksheets']='; '.join(sorted(countryrefs[code]))
    r['coverage_note']='country figures retained; inspect metric and period' if r['numeric_country_cells'] else 'included in regional definitions; no separately indexed country value' if r['in_regional_definitions'] else 'named in report; no separately indexed country value'
# The report also retains a historical geography that has no current ISO code.
if 'Netherlands Antilles' in annex:
    coverage['ANT']=dict(iso3='ANT',country='Netherlands Antilles (historical geography)',in_regional_definitions=True,numeric_country_cells=0,worksheets='',coverage_note='source regional definition retained; no allocation to successor territories')
writecsv('opec-country-coverage.csv',sorted(coverage.values(),key=lambda r:r['country']))

# Explicitly comparable OPEC total-liquids country series. The five additional
# country charts are stacked mutually exclusive production components. Preserve
# the component cell references for independent reconciliation.
liquids=[]
for chapter,sheet in [(4,'Table 4.1'),(8,'Table 8.7')]:
    path=next((BASE/'opec/data').glob(f'*Chapter {chapter}*Tables.xlsx'))
    s=openpyxl.load_workbook(path,data_only=True)[sheet]
    for row in s:
        code=country(s.cell(row[0].row,2).value)
        if not code:continue
        for col in range(3,9):
            value=s.cell(row[0].row,col);header=next(i for i in range(5,9) if yearof(s.cell(i,3).value)==2025);year=yearof(s.cell(header,col).value)
            if year and isinstance(value.value,(int,float)):
                liquids.append(dict(iso3=code,period=year,value=value.value,unit='million barrels/day',basis='projection' if year>2025 else 'OPEC baseline estimate',workbook=path.name,sheet=sheet,cells=value.coordinate,derivation='reported country total'))
path=next((BASE/'opec/data').glob('*Chapter 4*Figures.xlsx'));book=openpyxl.load_workbook(path,data_only=True)
for number,code in [(7,'NOR'),(8,'GBR'),(9,'BRA'),(10,'ARG'),(11,'QAT')]:
    s=book[f'Figure 4.{number}']
    for col in range(3,s.max_column+1):
        year=yearof(s.cell(6,col).value)
        if year is None:continue
        component=[s.cell(row,col) for row in range(7,s.max_row+1) if isinstance(s.cell(row,col).value,(int,float)) and s.cell(row,2).value is not None]
        assert component
        liquids.append(dict(iso3=code,period=year,value=sum(c.value for c in component),unit='million barrels/day',basis='projection' if year>2025 else 'OPEC baseline estimate',workbook=path.name,sheet=s.title,cells=' + '.join(c.coordinate for c in component),derivation='sum of stacked production components; see original row labels'))
assert len({(r['iso3'],r['period']) for r in liquids})==len(liquids)
assert len({r['iso3'] for r in liquids if r['period']==2030})==14
writecsv('opec-liquids-supply.csv',liquids)

# EIA: all rows, all quarters and annual values. Regional totals never join a
# country. Duplicate countries across 3b/3c remain separately attributable.
eia=[]
periods=[f'{y}-Q{q}' for y in [2025,2026,2027] for q in [1,2,3,4]]+['2025','2026','2027']
for table in ['3b','3c','3d']:
    p=BASE/f'eia-usa/steo-2026-10-table{table}.pdf';t=p.with_suffix('.txt')
    subprocess.run(['pdftotext','-layout',str(p),str(t)],check=True)
    section='production'
    for n,line in enumerate(t.read_text().splitlines(),1):
        if line.strip()=='Crude oil production capacity':section='crude-oil-production-capacity'
        if line.strip()=='Surplus crude oil production capacity':section='surplus-crude-oil-production-capacity'
        if 'Unplanned production outages' in line:section='unplanned-production-outages'
        match=re.match(r'\s*(.*?)\s*\.{3,}\s+(.+)',line)
        if not match:match=re.match(r'\s*(.*?)\s{2,}((?:\d+\.\d+|-)(?:\s+(?:\d+\.\d+|-)){14})\s*$',line)
        if not match:continue
        label=match[1].strip();values=match[2].split()
        if len(values)!=15 or not all(re.fullmatch(r'-|\d+\.\d+',v) for v in values):continue
        for period,value in zip(periods,values):
            eia.append(dict(source='EIA STEO October 2026',table=table,source_file=str(p.relative_to(BASE)),line=n,entity=label,iso3=country(label),metric=section if section!='production' else 'crude-oil-production' if table=='3d' else 'petroleum-and-other-liquid-fuels-production',period=period,value='' if value=='-' else float(value),unit='million barrels/day',basis='historical/estimate' if period.startswith('2025') else 'estimate/forecast',missing=value=='-'))
writecsv('eia-series.csv',eia)

# ANP annual country sums keep the source's crude/condensate and total feed
# definitions. Do not turn volume into mass without a density observation.
national=[]
for table,metric,unit in [('13','crude-and-condensate-production','thousand barrels/year'),('36','fresh-refinery-feed','barrels/day')]:
    p=BASE/f'anp-brazil/anuario-2026-tabela2-{table}.csv'
    with p.open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f,delimiter=';'))
    fields=list(rows[0]);totals=collections.defaultdict(float)
    for r in rows:totals[int(r['ANO'])]+=float(r[fields[-1]].replace(',','.'))
    for year,value in sorted(totals.items()):
        national.append(dict(source='ANP Anuario 2026',iso3='BRA',metric=metric,period=str(year),value=value,unit=unit,basis='reported-statistic',source_file=str(p.relative_to(BASE)),derivation=f'sum of {fields[0]} categories; metadata-tabela2-{table}.pdf defines units',months=''))
    if table=='36':
        for year in sorted(totals):
            crude=sum(float(r[fields[-1]].replace(',','.')) for r in rows if int(r['ANO'])==year and r['ORIGEM'].startswith('Petróleo'))
            national.append(dict(source='ANP Anuario 2026',iso3='BRA',metric='crude-and-condensate-refinery-feed',period=str(year),value=crude,unit='barrels/day',basis='reported-statistic',source_file=str(p.relative_to(BASE)),derivation='national + imported petroleum; excludes other reprocessed feed',months=''))
p=BASE/'statistics-canada/25100063.csv'
with p.open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
for measure in ['Crude oil production','Equivalent products production','Input to Canadian refineries']:
    for year in ['2024','2025','2026']:
        series=[r for r in rows if r['GEO']=='Canada' and r['REF_DATE'].startswith(year) and r['Supply and disposition']==measure and r['UOM']=='Cubic metres']
        assert len({r['REF_DATE'] for r in series})==len(series)
        if not series:continue
        assert all(r['VALUE'] and r['SCALAR_FACTOR']=='units' for r in series)
        national.append(dict(source='Statistics Canada 25-10-0063-01',iso3='CAN',metric=measure,period=year if len(series)==12 else year+'-YTD',value=sum(float(r['VALUE']) for r in series),unit='cubic metres',basis='reported-statistic; may be revised',source_file=str(p.relative_to(BASE)),derivation='sum monthly national series; no provincial double count',months=len(series)))
# USA refinery input, kept separate from finished product output.
p=BASE/'eia-usa/steo-2026-10-table4b.txt'
for n,line in enumerate(p.read_text().splitlines(),1):
    if re.match(r'\s*Crude oil\s*\.',line):
        vals=re.findall(r'\d+\.\d+',line)
        if len(vals)==15:
            for year,value in zip(['2025','2026','2027'],vals[-3:]):
                national.append(dict(source='EIA STEO October 2026 table 4b',iso3='USA',metric='crude-oil-refinery-input',period=year,value=float(value),unit='million barrels/day',basis='historical/estimate' if year=='2025' else 'estimate/forecast',source_file=str(p.relative_to(BASE)),derivation=f'annual column, line {n}',months=''))
writecsv('national-series.csv',national)
focus=['RUS','BRA','CAN','VEN','MEX','USA','JPN']
summary=[]
for code in focus:
    v=next((r for r in eia if r['iso3']==code and r['period']=='2025' and r['table'] in ['3b','3c'] and r['value']!=''),None)
    summary.append(dict(iso3=code,eia_liquids_2025_mbpd=v['value'] if v else '',eia_source_table=v['table'] if v else '',opec_numeric_cells=coverage.get(code,{}).get('numeric_country_cells',0),national_rows=sum(r['iso3']==code for r in national),note='EIA liquids includes NGLs, other liquids and processing gain; not crude-only or throughput' if v else 'no separately listed EIA STEO production value; retain UNSD refinery data'))
writecsv('requested-country-coverage.csv',summary)
manifest=dict(workbooks=len(list((BASE/'opec/data').glob('*.xlsx'))),worksheets=len(sheets),nonempty_cells=len(cells),numeric_country_cells=len(countrycells),opec_countries_and_territories=len(coverage),countries_with_indexed_numeric_cells=sum(bool(v) for v in countryrefs.values()),eia_records=len(eia),eia_country_count=len({r['iso3'] for r in eia if r['iso3']}),national_records=len(national),focus=summary)
(OUT/'summary.json').write_text(json.dumps(manifest,indent=2)+'\n')
(BASE/'SHA256SUMS').write_text(''.join(digest(p)+'  '+str(p.relative_to(BASE))+'\n' for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps(manifest,indent=2))
