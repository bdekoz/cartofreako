#!/usr/bin/env python3
"""Fetch public India inventory/backfill, FIRMS, IITM and LongPMInd inputs.

Uses the publisher's public 2024 demo access unless XKDR_API_KEY is configured.
Existing files are reused and checked. Use a new dated root for a new snapshot.
No registration, paid service, private endpoint or access-control workaround.
"""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import time

import requests


def checksum(path, algorithm='sha256'):
    result=hashlib.new(algorithm)
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):result.update(chunk)
    return result.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--end',default='2026-11-08')
    parser.add_argument('--xkdr-years',type=int,nargs='+',default=[2024,2025,2026])
    args=parser.parse_args();root=args.root.resolve();root.mkdir(parents=True,exist_ok=True)
    receipts=[];missing=[]
    prior={}
    for previous_path in [root/'acquisition-manifest.json',root/'raw/download-receipts.json']:
        if previous_path.exists():
            previous=json.loads(previous_path.read_text())
            for receipt in previous if isinstance(previous,list) else previous['receipts']:
                prior[receipt['file']]=receipt
    full_key=os.environ.get('XKDR_API_KEY')
    demo_key=None

    def retrieve(url,relative,headers=None,expected_bytes=None,md5=None):
        path=root/relative;path.parent.mkdir(parents=True,exist_ok=True)
        reused=path.exists();acquired=prior.get(relative,{}).get('retrieved_at_utc')
        if not reused:
            for attempt in range(3):
                try:
                    with requests.get(url,headers=headers,stream=True,timeout=(20,90)) as response:
                        response.raise_for_status()
                        with path.with_suffix(path.suffix+'.part').open('wb') as out:
                            for chunk in response.iter_content(1048576):out.write(chunk)
                    path.with_suffix(path.suffix+'.part').replace(path)
                    acquired=dt.datetime.now(dt.timezone.utc).isoformat()
                    break
                except requests.RequestException:
                    if attempt==2:raise
                    time.sleep(attempt+1)
        if expected_bytes is not None and path.stat().st_size!=expected_bytes:
            raise ValueError(f'Unexpected byte count: {path}')
        if md5 and checksum(path,'md5')!=md5:
            raise ValueError(f'Published checksum mismatch: {path}')
        sha=checksum(path)
        if reused and relative in prior and sha!=prior[relative]['sha256']:
            raise ValueError(f'Pinned cached input changed: {path}')
        receipt=dict(url=url,file=relative,bytes=path.stat().st_size,sha256=sha,
                     reused_cache=reused,retrieved_at_utc=acquired,
                     verified_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        receipts.append(receipt)
        return path

    def headers():
        nonlocal demo_key
        if full_key:return {'Authorization':'Bearer '+full_key}
        if demo_key is None:
            page=retrieve('https://airquality.xkdr.org/','raw/discovery/xkdr-site.html')
            match=re.search(r'aqi_demo_[A-Za-z0-9_-]+',page.read_text())
            if not match:raise ValueError('Publisher demo key not found; no key guessed')
            demo_key=match[0]
        return {'Authorization':'Bearer '+demo_key}

    for endpoint,name in [('stations','xkdr-stations.txt'),('files','xkdr-files.json'),('meta','xkdr-meta.json')]:
        relative='raw/discovery/'+name
        retrieve('https://airquality.xkdr.org/v1/'+endpoint,relative,
                 headers=None if (root/relative).exists() else headers())
    catalog=json.loads((root/'raw/discovery/xkdr-files.json').read_text())
    jobs=[]
    for year in args.xkdr_years:
        if year!=2024 and not full_key:
            missing.append(dict(source='XKDR',year=year,reason='Full-access API key absent; demo access is limited to 2024'))
            continue
        entries=[f for f in catalog['files'] if f.get('year')==year and f.get('kind')=='measurements']
        if not entries:missing.append(dict(source='XKDR',year=year,reason='No files in published catalog'))
        for f in entries:
            relative=f"raw/xkdr/{year}-{f['month']:02}.parquet"
            jobs.append(('https://airquality.xkdr.org/v1/files/'+f['key'],relative,
                         None if (root/relative).exists() else headers(),f['bytes'],None))
    firms=retrieve('https://firms.modaps.eosdis.nasa.gov/api/active_fire_files/all?format=json','raw/discovery/firms-catalog.json')
    for satellite in ['noaa20','noaa21']:
        for url in json.loads(firms.read_text())['csv'][satellite]['South Asia']:
            if '_7d' in url:jobs.append(('https://firms.modaps.eosdis.nasa.gov'+url,'raw/firms/'+Path(url).name,None,None,None))
    retrieve('https://ews.tropmet.res.in/dss/','raw/discovery/dss.txt')
    record=retrieve('https://zenodo.org/api/records/14557027','raw/discovery/zenodo-record.txt')
    record=json.loads(record.read_text())
    if record['metadata']['license']['id']!='cc-by-4.0':
        raise ValueError('LongPMInd license metadata changed')
    for f in record['files']:
        if f['key'] in ['pm25_monthly.zip','pm10_monthly.zip']:
            jobs.append((f['links']['self'],'raw/longpmind/'+f['key'],None,f['size'],f['checksum'].removeprefix('md5:')))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for path in pool.map(lambda job:retrieve(*job),jobs):print('Verified',path.name,flush=True)
    missing.append(dict(source='ERA5',reason='Not fetched by this public-source adapter; CDS-authenticated acquisition is separate',
                        cds_credentials_present=bool(os.environ.get('CDSAPI_KEY')) or (Path.home()/'.cdsapirc').exists()))
    manifest=dict(requested_data_through=args.end,checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  receipts=sorted(receipts,key=lambda r:r['file']),access_limits=missing,
                  recent_fire_limit='Public rolling seven-day feed only; not a historical fire archive',
                  forecast_limit='IITM chart data retain their forecast/history class and unknown issue time')
    (root/'acquisition-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'verified_files':len(receipts),'access_limits':missing},indent=2))


if __name__=='__main__':main()
