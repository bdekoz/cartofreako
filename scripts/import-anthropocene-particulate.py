#!/usr/bin/env python3
"""Import checksummed local particulate periods; never contact a provider."""
import argparse
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from dataset import DatasetError, ROOT, atomic_json, data_root, digest, lock, redact, utcnow
from data_sources import copy_file

FIRMS_BASE = 'https://firms.modaps.eosdis.nasa.gov/api/area/csv'


def firms_url(source, start, days):
    key = os.environ.get('FIRMS_MAP_KEY')
    if not key:
        raise DatasetError('FIRMS_MAP_KEY is required to identify the acquisition cache')
    return f'{FIRMS_BASE}/{key}/{source}/world/{days}/{start}'


def receipt_path(cache, url):
    key = hashlib.sha256((url + '{}').encode()).hexdigest()
    return Path(cache)/'http'/(key + '.json')


def checked_object(cache, record):
    sha = record['sha256']
    if not re.fullmatch('[0-9a-f]{64}', sha):
        raise DatasetError('Invalid particulate cache checksum')
    obj = Path(cache)/'sha256'/sha
    if not obj.is_file() or obj.stat().st_size != record['bytes'] or digest(obj) != sha:
        raise DatasetError('Corrupted particulate cache object: ' + sha)
    return obj


def seed(cache, url, path, expected, manifest):
    receipt = receipt_path(cache, url)
    with lock(receipt.parent, receipt.stem):
        if receipt.exists():
            checked_object(cache, json.loads(receipt.read_text()))
            return False  # Prefer an existing provider-checked object.
        if digest(path) != expected:
            raise DatasetError('Changed local particulate input: ' + str(path))
        obj = Path(cache)/'sha256'/expected
        obj.parent.mkdir(parents=True, exist_ok=True)
        if obj.exists():
            checked_object(cache, {'sha256': expected, 'bytes': path.stat().st_size})
        else:
            fd, name = tempfile.mkstemp(prefix='.particulate-import-', dir=obj.parent)
            os.close(fd)
            temporary = Path(name)
            try:
                copy_file(path, temporary)
                if digest(temporary) != expected:
                    raise DatasetError('Local particulate input changed during import: ' + str(path))
                with temporary.open('rb') as stream:
                    os.fsync(stream.fileno())
                temporary.chmod(0o444)
                temporary.replace(obj)
            finally:
                temporary.unlink(missing_ok=True)
        atomic_json(receipt, {'url': redact(url), 'sha256': expected, 'bytes': path.stat().st_size,
                             'retrieved_at': None, 'checked_at': None, 'acquisition': 'pinned-local',
                             'imported_at': utcnow(), 'source_file': str(path),
                             'source_manifest_sha256': digest(manifest)})
        return True


def checksums(manifest):
    result = {}
    for line in manifest.read_text().splitlines():
        sha, name = line.split(maxsplit=1)
        if not re.fullmatch('[0-9a-f]{64}', sha):
            raise DatasetError('Invalid particulate checksum manifest: ' + str(manifest))
        parts = Path(name.lstrip('*')).parts
        relative = '/'.join(parts[-2:]) if len(parts) > 1 and parts[-2] in ('firms', 'cwfis') else parts[-1]
        if relative in result and result[relative] != sha:
            raise DatasetError('Conflicting particulate checksums: ' + relative)
        result[relative] = sha
    return result


def firms_period(path, start):
    """Only import contiguous, observed days from the named sensor's chunk."""
    dates = set()
    with path.open(newline='') as stream:
        rows = csv.DictReader(stream)
        if not {'latitude', 'longitude', 'acq_date'} <= set(rows.fieldnames or []):
            raise DatasetError('Invalid local FIRMS CSV: ' + str(path))
        for row in rows:
            dates.add(date.fromisoformat(row['acq_date']))
    if not dates:
        return None
    count = (max(dates) - start).days + 1
    if 1 <= count <= 5 and dates == {start + timedelta(days=n) for n in range(count)}:
        return count
    return None


def import_local(cache, directories, year):
    imported = 0
    selected = os.environ.get('ANTHROPOCENE_FIRMS_SOURCES', 'VIIRS_NOAA20_SP VIIRS_NOAA20_NRT').split()
    public = {}
    if year < datetime.now(timezone.utc).year:
        public = {
            f'daily_88101_{year}.zip': f'https://aqs.epa.gov/aqsweb/airdata/daily_88101_{year}.zip',
            f'hms_smoke{year}.zip': f'https://satepsanone.nesdis.noaa.gov/pub/FIRE/web/HMS/Smoke_Polygons/Shapefile/Annual_Bundles/hms_smoke{year}.zip',
            f'cwfis-{year}-hotspots.zip': f'https://cwfis.cfs.nrcan.gc.ca/downloads/hotspots/archive/{year}_hotspots.zip'}
    for raw in directories:
        raw = Path(raw).resolve()
        manifest = raw/'SHA256SUMS'
        if not manifest.is_file():
            continue
        expected = checksums(manifest)
        for name, url in public.items():
            path = raw/name
            if name in expected and path.is_file():
                imported += seed(cache, url, path, expected[name], manifest)
        for path in sorted((raw/'cwfis').glob('*.csv')):
            name = 'cwfis/' + path.name
            if name not in expected or not re.fullmatch(r'\d{8}\.csv', path.name):
                continue
            day = datetime.strptime(path.stem, '%Y%m%d').date()
            if day.year != year:
                continue
            with path.open() as stream:
                if not {'lat', 'lon', 'rep_date'} <= {name.strip() for name in next(csv.reader(stream), [])}:
                    raise DatasetError('Invalid local CWFIS CSV: ' + str(path))
            url = 'https://cwfis.cfs.nrcan.gc.ca/downloads/hotspots/' + path.name
            imported += seed(cache, url, path, expected[name], manifest)
        if not os.environ.get('FIRMS_MAP_KEY'):
            continue
        for path in sorted((raw/'firms').glob('*.csv')):
            name = 'firms/' + path.name
            match = re.fullmatch(r'\d+-(VIIRS_[A-Z0-9_]+)-(\d{4}-\d{2}-\d{2})\.csv', path.name)
            if name not in expected or not match or match[1] not in selected:
                continue
            start = date.fromisoformat(match[2])
            if start.year != year:
                continue
            # A five-day receipt already in shared cache needs no CSV scan.
            if receipt_path(cache, firms_url(match[1], start, 5)).exists():
                continue
            days = firms_period(path, start)
            if days:
                imported += seed(cache, firms_url(match[1], start, days), path, expected[name], manifest)
    return imported


def chunk_days(cache, source, start, maximum):
    # Preserve a previously downloaded short tail instead of asking for an
    # overlapping larger chunk when the provider publishes more days.
    for days in range(maximum, 0, -1):
        if receipt_path(cache, firms_url(source, start, days)).exists():
            return days
    return maximum


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=data_root()/'cache')
    parser.add_argument('--year', type=int)
    parser.add_argument('--data-directory', type=Path)
    parser.add_argument('--source', type=Path, action='append', help='explicit raw YEAR directory; repeatable')
    parser.add_argument('--chunk-source')
    parser.add_argument('--chunk-start', type=date.fromisoformat)
    parser.add_argument('--chunk-days', type=int, choices=range(1, 6))
    args = parser.parse_args()
    try:
        if args.chunk_source:
            if args.chunk_start is None or args.chunk_days is None:
                parser.error('chunk selection requires --chunk-start and --chunk-days')
            print(chunk_days(args.cache, args.chunk_source, args.chunk_start, args.chunk_days))
        else:
            if not args.year:
                parser.error('--year is required for local import')
            directories = args.source
            if directories is None:
                directories = [ROOT/f'assets.static/anthropocene/.raw/{args.year}']
                directories += sorted((args.cache.parent/'editions').glob(f'*/inputs/anthropocene/.raw/{args.year}'))
                if args.data_directory:
                    directories.append(args.data_directory/f'.raw/{args.year}')
            count = import_local(args.cache, dict.fromkeys(directories), args.year)
            print(f'Particulate cache: imported {count} verified completed periods (no provider requests)', flush=True)
        return 0
    except (DatasetError, OSError, ValueError, KeyError) as error:
        print('import-anthropocene-particulate: ' + redact(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
