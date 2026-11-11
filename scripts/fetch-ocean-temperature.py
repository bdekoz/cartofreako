#!/usr/bin/env python3
"""Pin public NOAA OISST inputs; resume interrupted downloads without mixing revisions."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

import requests

from ocean_temperature import NetCDF, digest, write_json

BASE = 'https://psl.noaa.gov/thredds/fileServer/Datasets/noaa.oisst.v2.highres/'
RANGE_SIZE = 8 * 1024**2


def fetch(name, directory):
    path, receipt = directory / name, directory / (name + '.json')
    if os.environ.get('DATA_HTTP_CACHE'):
        from data_http import fetch as checked_fetch
        record = checked_fetch(BASE + name, path, os.environ['DATA_HTTP_CACHE'], range_size=RANGE_SIZE)
        with NetCDF(path) as nc:
            shape = nc.shape('sst' if name.startswith('sst.') else 'icec' if name.startswith('icec.') else 'lsmask')
            if shape[-2:] != (720, 1440):
                raise ValueError('Unexpected native OISST grid: ' + str(shape))
        record['shape'] = shape
        write_json(receipt, record)
        print('freshness-checked ' + name, flush=True)
        return record
    if path.exists() and receipt.exists():
        record = json.loads(receipt.read_text())
        if digest(path) == record['sha256']:
            print('verified ' + name, flush=True)
            return record
        raise ValueError('Digest mismatch: ' + str(path))
    url = BASE + name
    for attempt in range(6):
        try:
            head = requests.get(url, headers={'Range': 'bytes=0-0'}, timeout=(30, 90), stream=True)
            head.raise_for_status()
            total = int(head.headers.get('Content-Range', '').split('/')[-1]) if head.status_code == 206 else int(head.headers['Content-Length'])
            identity = {'url': url, 'bytes': total, 'last_modified': head.headers.get('Last-Modified'), 'etag': head.headers.get('ETag')}
            head.close()
            part, info = path.with_suffix('.nc.part'), path.with_suffix('.nc.part.json')
            if part.exists() and (not info.exists() or json.loads(info.read_text()) != identity):
                part.unlink()
            write_json(info, identity)
            offset = part.stat().st_size if part.exists() else 0
            if offset > total:
                raise ValueError('Partial download larger than remote file')
            while offset < total:
                # The NOAA proxy can truncate long responses. Small ranges are
                # independently checked and resumed on the next attempt.
                end = min(total-1, offset + RANGE_SIZE - 1)
                headers = {'Range': f'bytes={offset}-{end}'}
                if identity['last_modified']:
                    headers['If-Unmodified-Since'] = identity['last_modified']
                response = requests.get(url, headers=headers, timeout=(30, 180), stream=True)
                response.raise_for_status()
                if response.status_code == 206:
                    expected = f'bytes {offset}-{end}/{total}'
                    if response.headers.get('Content-Range') != expected:
                        raise ValueError('Unexpected range: ' + str(response.headers))
                elif offset:
                    raise ValueError('Server did not honor resume range')
                with part.open('ab' if offset else 'wb') as target:
                    for block in response.iter_content(1024**2):
                        target.write(block)
                response.close()
                offset = part.stat().st_size
            if part.stat().st_size != total:
                raise ValueError('Incomplete response for ' + name)
            with NetCDF(part) as nc:
                shape = nc.shape('sst' if name.startswith('sst.') else 'icec' if name.startswith('icec.') else 'lsmask')
                if shape[-2:] != (720, 1440):
                    raise ValueError('Unexpected native OISST grid: ' + str(shape))
            record = {**identity, 'retrieved_at': datetime.now(timezone.utc).isoformat(), 'sha256': digest(part), 'shape': shape}
            part.replace(path)
            write_json(receipt, record)
            info.unlink(missing_ok=True)
            print('downloaded ' + name + ' ' + str(total), flush=True)
            return record
        except (requests.RequestException, ValueError, RuntimeError) as error:
            print(f'retry {attempt+1} {name}: {error}', flush=True)
            if attempt == 5:
                raise
            time.sleep(min(30, 2**attempt))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--start-year', type=int, default=1982)
    parser.add_argument('--end-year', type=int, default=2026)
    parser.add_argument('--workers', type=int, default=2, choices=(1, 2, 3))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    # Targets first, then climatology, then the remaining record history.
    years = sorted(range(args.start_year, args.end_year+1), key=lambda y: (y not in (2025, 2026), not 1991 <= y <= 2020, y))
    names = ['lsmask.oisst.nc'] + [f'{var}.day.mean.{year}.nc' for year in years for var in ('sst', 'icec')]
    records, failures = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch, name, args.output): name for name in names}
        for future in as_completed(futures):
            try:
                records.append(future.result())
            except Exception as error:
                failures.append({'file': futures[future], 'error': str(error)})
            write_json(args.output / 'manifest.json', {'schema': 'oisst-downloads-v1', 'files': sorted(records, key=lambda r:r['url']), 'failures': failures})
    if failures:
        raise SystemExit(f'{len(failures)} failed downloads; see manifest.json')


if __name__ == '__main__':
    main()
