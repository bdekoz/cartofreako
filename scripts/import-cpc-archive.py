#!/usr/bin/env python3
"""Import verified 1979–2025 CPC archives for reuse by current data updates."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from dataset import DatasetError, ROOT, atomic_json, data_root, digest, lock, utcnow

LAST_ARCHIVE_YEAR = 2025
BASES = ('https://psl.noaa.gov/thredds/fileServer/Datasets/cpc_global_temp',
         'https://downloads.psl.noaa.gov/Datasets/cpc_global_temp')
SCHEMA = 'cartofreako-cpc-archive-v1'


def object_path(cache, record):
    sha = record['sha256']
    if not re.fullmatch(r'[0-9a-f]{64}', sha):
        raise DatasetError('Invalid CPC archive object checksum')
    path = cache / 'sha256' / sha
    if not path.is_file() or path.stat().st_size != record['bytes'] or digest(path) != sha:
        raise DatasetError('Corrupted CPC archive object: ' + str(path))
    return path


def validate_netcdf(path, variable):
    result = subprocess.run([os.environ.get('GDALINFO', 'gdalinfo'), f'NETCDF:{path}:{variable}'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=60)
    if result.returncode:
        raise DatasetError(f'Unreadable CPC {variable} NetCDF: {path}; {result.stderr.strip()}')


def read_manifest(cache):
    path = cache / 'cpc-archive/manifest.json'
    if not path.exists():
        return {'schema': SCHEMA, 'archive_through': LAST_ARCHIVE_YEAR, 'files': {}}
    value = json.loads(path.read_text())
    if value.get('schema') != SCHEMA or value.get('archive_through') not in (2024, LAST_ARCHIVE_YEAR):
        raise DatasetError('Unsupported CPC archive manifest')
    value['archive_through'] = LAST_ARCHIVE_YEAR
    return value


def cached_remote(cache, name):
    candidates = []
    for base in BASES:
        url = base + '/' + name
        key = hashlib.sha256((url + '{}').encode()).hexdigest()
        path = cache / 'http' / (key + '.json')
        if path.exists():
            record = json.loads(path.read_text())
            if record['url'] != url:
                raise DatasetError('CPC HTTP receipt URL mismatch: ' + str(path))
            candidates.append(record)
    return max(candidates, key=lambda r: datetime.fromisoformat(r['checked_at'])) if candidates else None


def import_archive(source, cache, start=1979, end=LAST_ARCHIVE_YEAR):
    source, cache = Path(source).resolve(), Path(cache).resolve()
    if not 1979 <= start <= end <= LAST_ARCHIVE_YEAR:
        raise DatasetError('Archive import supports 1979–2025 only; 2026 requires incremental updates')
    checksum_file = source / 'SHA256SUMS'
    expected = {}
    for line in checksum_file.read_text().splitlines():
        sha, name = line.split(maxsplit=1)
        name = name.removeprefix('*').removeprefix('./')
        if not re.fullmatch(r'[0-9a-f]{64}', sha) or not re.fullmatch(r'(tmax|tmin)\.\d{4}\.nc', name):
            raise DatasetError('Invalid CPC source checksum manifest entry')
        if name in expected:
            raise DatasetError('Duplicate CPC checksum manifest entry: ' + name)
        expected[name] = sha
    source_manifest_sha = digest(checksum_file)
    counts = {'existing_archive': 0, 'adopted_http': 0, 'imported_local': 0}
    with lock(cache / 'cpc-archive', 'import'):
        manifest = read_manifest(cache)
        for year in range(start, end + 1):
            for variable in ('tmax', 'tmin'):
                name = f'{variable}.{year}.nc'
                if name in manifest['files']:
                    object_path(cache, manifest['files'][name])
                    counts['existing_archive'] += 1
                    continue
                prior = cached_remote(cache, name)
                if prior:
                    path = object_path(cache, prior)
                    origin = 'verified-http-cache'
                    counts['adopted_http'] += 1
                else:
                    path = source / name
                    if name not in expected or not path.is_file() or digest(path) != expected[name]:
                        raise DatasetError('Missing or changed local CPC archive: ' + str(path))
                    prior = {'sha256': expected[name], 'bytes': path.stat().st_size,
                             'url': BASES[0] + '/' + name, 'retrieved_at': None, 'checked_at': None}
                    origin = 'local-checksum-manifest'
                    counts['imported_local'] += 1
                validate_netcdf(path, variable)
                obj = cache / 'sha256' / prior['sha256']
                obj.parent.mkdir(parents=True, exist_ok=True)
                if obj.exists():
                    object_path(cache, prior)
                else:
                    fd, temporary = tempfile.mkstemp(prefix='.cpc-import-', dir=obj.parent)
                    os.close(fd)
                    temporary = Path(temporary)
                    try:
                        shutil.copyfile(path, temporary)
                        if digest(temporary) != prior['sha256']:
                            raise DatasetError('CPC source changed during import: ' + name)
                        with temporary.open('rb') as stream:
                            os.fsync(stream.fileno())
                        temporary.chmod(0o444)
                        temporary.replace(obj)
                    finally:
                        temporary.unlink(missing_ok=True)
                manifest['files'][name] = {
                    'sha256': prior['sha256'], 'bytes': prior['bytes'], 'url': prior['url'],
                    'acquisition': 'pinned-local', 'archive_year': year, 'origin': origin,
                    'imported_at': utcnow(), 'retrieved_at': prior.get('retrieved_at'),
                    'provider_checked_at': prior.get('checked_at'),
                    'source_file': str(path),
                    'source_manifest_sha256': source_manifest_sha if origin == 'local-checksum-manifest' else None}
                # Each verified object is durable and resumable independently.
                atomic_json(cache / 'cpc-archive/manifest.json', manifest)
                print(f'CPC archive: {name}: {origin}', file=sys.stderr, flush=True)
        report = {**counts, 'files': 2 * (end - start + 1), 'start_year': start, 'end_year': end,
                  'total_pinned_files': len(manifest['files']),
                  'bytes': sum(manifest['files'][f'{v}.{y}.nc']['bytes']
                               for y in range(start, end + 1) for v in ('tmax', 'tmin')),
                  'verified_at': utcnow(), 'source_manifest_sha256': source_manifest_sha}
        atomic_json(cache / 'cpc-archive/import-report.json', report)
        return report


def stage_archive(directory, cache, start, end, *, missing_only=False):
    """Materialize pinned bytes without making or claiming a provider request."""
    directory, cache = Path(directory), Path(cache)
    manifest = read_manifest(cache)
    staged = []
    for year in range(start, min(end, LAST_ARCHIVE_YEAR) + 1):
        for variable in ('tmax', 'tmin'):
            name = f'{variable}.{year}.nc'
            target = directory / name
            if missing_only and target.exists():
                continue
            record = manifest['files'].get(name)
            if record is None:
                continue
            obj = object_path(cache, record)
            directory.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(name + '.archive-copy')
            temporary.unlink(missing_ok=True)
            try:
                try:
                    os.link(obj, temporary)
                except OSError:
                    shutil.copyfile(obj, temporary)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
            atomic_json(target.with_name(name + '.receipt.json'),
                        {**record, 'acquisition': 'policy-cache', 'cache_policy': 'pinned-cpc-archive',
                         'verified_at': utcnow()})
            staged.append(name)
    return staged


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'assets.static/anthropocene/.raw/cpc')
    parser.add_argument('--cache', type=Path, default=Path(os.environ.get('DATA_HTTP_CACHE', data_root() / 'cache')))
    parser.add_argument('--start-year', type=int, default=1979)
    parser.add_argument('--end-year', type=int, default=LAST_ARCHIVE_YEAR)
    parser.add_argument('--stage-directory', type=Path, help='stage already imported archives; print their filenames')
    parser.add_argument('--missing-only', action='store_true', help='preserve all existing destination files when staging')
    args = parser.parse_args()
    if not 1979 <= args.start_year <= args.end_year <= 9999:
        parser.error('invalid CPC year range')
    try:
        if args.stage_directory:
            for name in stage_archive(args.stage_directory, args.cache, args.start_year, args.end_year,
                                      missing_only=args.missing_only):
                print(name)
        else:
            print(json.dumps(import_archive(args.source, args.cache, args.start_year, args.end_year), indent=2))
    except (DatasetError, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print('import-cpc-archive: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
