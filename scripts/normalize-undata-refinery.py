#!/usr/bin/env python3
"""Convert official UNSD SDMX throughput CSV to the resources preparer's schema."""
import csv
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv)!=4:
    raise SystemExit('usage: normalize-undata-refinery.py SDMX.csv ENERGY-DSD.xml OUTPUT.csv')
source,structure,destination=map(Path,sys.argv[1:])
ns={'s':'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure','c':'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common'}
root=ET.parse(structure)
codes=root.findall('.//s:Codelist[@id="CL_AREA_NRG"]/s:Code',ns)
names={c.attrib['id']:c.findtext('c:Name',namespaces=ns) for c in codes}
rows=list(csv.DictReader(source.open()))
def require(condition,message):
    if not condition:raise ValueError(message)
require(rows and names,'empty SDMX data or area codelist')
keys=set()
result=[]
for r in rows:
    require((r['FREQ'],r['COMMODITY'],r['TRANSACTION'],r['UNIT_MEASURE'],r['UNIT_MULT'])==('A','GR','086','TN','3'), 'unexpected refinery measure or unit')
    key=(r['REF_AREA'],r['TIME_PERIOD'])
    require(key not in keys, f'duplicate area/year {key}')
    keys.add(key)
    require(r['REF_AREA'] in names, f'unknown area {r["REF_AREA"]}')
    require(math.isfinite(float(r['OBS_VALUE'])) and float(r['OBS_VALUE'])>=0,'invalid throughput')
    require(r['OBS_STATUS'] in ['A','E'],'unknown observation status; review before promotion')
    result.append([names[r['REF_AREA']],'Total refinery throughput',r['TIME_PERIOD'],'Metric tons, thousand',r['OBS_VALUE'],'1' if r['OBS_STATUS']=='E' else ''])
with destination.open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Country or Area','Commodity - Transaction','Year','Unit','Quantity','Quantity Footnotes']);w.writerows(result)
print(f'Normalized {len(result)} annual refinery observations; unit: thousand metric tonnes')
