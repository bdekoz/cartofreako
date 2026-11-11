#!/usr/bin/env python3
"""Pin public NOAA OISST inputs; resume interrupted downloads without mixing revisions."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

import requests

from dataset import DatasetError
from ocean_temperature import NetCDF, digest, write_json

BASE = 'https://psl.noaa.gov/thredds/fileServer/Datasets/noaa.oisst.v2.highres/'
RANGE_SIZE = 8 * 1024**2


def stage_history(source, directory, *, start_year=1982, end_year=2024):
    """Reuse verified local baseline inputs without issuing provider requests."""
    source, directory = Path(source), Path(directory)
    names = ['lsmask.oisst.nc'] + [f'{var}.day.mean.{year}.nc'
             for year in range(start_year, end_year + 1) for var in ('sst', 'icec')]
    inputs = []
    # Check the whole inventory before staging anything or starting refreshes.
    for name in names:
        path, receipt = source / name, source / (name + '.json')
        if not path.is_file() or not receipt.is_file():
            raise DatasetError(f'Missing local OISST history: {path}; set OCEAN_HISTORY_DIR to '
                               'a complete verified archive. Historical years are never fetched automatically.')
        record = json.loads(receipt.read_text())
        if (record.get('url') != BASE + name or not record.get('sha256')
                or record.get('bytes') != path.stat().st_size):
            raise DatasetError('Invalid local OISST history receipt: ' + str(receipt))
        inputs.append((name, path, record))
    directory.mkdir(parents=True, exist_ok=True)
    records = []
    for name, path, record in inputs:
        descriptor, temporary_name = tempfile.mkstemp(prefix='.' + name + '-', dir=directory)
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            copied = subprocess.run(['cp', '--reflink=auto', str(path), str(temporary)],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if copied.returncode:
                shutil.copyfile(path, temporary)
            if digest(temporary) != record['sha256']:
                raise DatasetError('Changed local OISST history: ' + str(path))
            variable = 'sst' if name.startswith('sst.') else 'icec' if name.startswith('icec.') else 'lsmask'
            with NetCDF(temporary) as nc:
                shape = nc.shape(variable)
                if shape[-2:] != (720, 1440) or list(shape) != record.get('shape'):
                    raise DatasetError('Unexpected local OISST history grid: ' + str(path))
            temporary.replace(directory / name)
        finally:
            temporary.unlink(missing_ok=True)
        pinned = {**record, 'acquisition': 'policy-cache', 'cache_policy': 'pinned-oisst-history',
                  'history_source': str(path.resolve())}
        write_json(directory / (name + '.json'), pinned)
        records.append(pinned)
        print('verified local OISST history ' + name + ' (no provider request)', flush=True)
    return records


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
    parser.add_argument('--start-year', type=int, default=2025, help='first year to refresh remotely (default: 2025)')
    parser.add_argument('--end-year', type=int, default=2026)
    parser.add_argument('--history-dir', type=Path, help='verified local 1982–2024 OISST archive and land mask')
    parser.add_argument('--workers', type=int, default=2, choices=(1, 2, 3))
    args = parser.parse_args()
    if not 1982 <= args.start_year <= args.end_year:
        parser.error('years must satisfy 1982 <= start-year <= end-year')
    args.output.mkdir(parents=True, exist_ok=True)
    records = (stage_history(args.history_dir, args.output, end_year=args.start_year - 1)
               if args.history_dir else [])
    # Targets first, then climatology, then the remaining record history.
    years = sorted(range(args.start_year, args.end_year+1), key=lambda y: (y not in (2025, 2026), not 1991 <= y <= 2020, y))
    names = ([] if args.history_dir else ['lsmask.oisst.nc']) + [f'{var}.day.mean.{year}.nc' for year in years for var in ('sst', 'icec')]
    failures = []
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
