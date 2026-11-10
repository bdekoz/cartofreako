#!/usr/bin/env python3
"""Retain a local CPC year prefix and append only missing NOAA daily subsets."""
import argparse
import ctypes as C
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.parse import urlencode
import xml.etree.ElementTree as E

import numpy as np

from data_http import fetch
from data_sources import netcdf_days
from dataset import DatasetError, ROOT, atomic_json, data_root, digest, lock, utcnow
from ocean_temperature import NetCDF

SCHEMA = 'cartofreako-cpc-incremental-v1'
SUBSETS = 'https://psl.noaa.gov/thredds/ncss/grid/Datasets/cpc_global_temp'


def time_units(units):
    kind, origin = units.split(' since ', 1)
    scale = {'hour': 3600, 'day': 86400, 'second': 1}[kind.lower().rstrip('s')]
    start = datetime.fromisoformat(origin.replace(' UTC', '').strip())
    return scale, start.replace(tzinfo=timezone.utc) if start.tzinfo is None else start


def inventory(path, year):
    root = E.parse(path).getroot()
    axis = next((node for node in root.iter() if node.tag.rsplit('}', 1)[-1] == 'axis'
                 and node.get('name') == 'time'), None)
    if axis is None:
        raise DatasetError('CPC subset inventory has no time axis')
    attrs = {node.get('name'): node.get('value') for node in axis
             if node.tag.rsplit('}', 1)[-1] == 'attribute'}
    values = next(node for node in axis if node.tag.rsplit('}', 1)[-1] == 'values')
    scale, start = time_units(attrs['units'])
    count = int(values.get('npts'))
    first, last = float(values.get('start')), float(values.get('end'))
    step = float(values.get('resolution', values.get('increment', '0')))
    if count < 1 or (count > 1 and (step * scale != 86400 or
            abs(last - first - step * (count - 1)) > 1e-6)):
        raise DatasetError('CPC inventory does not describe contiguous daily observations')
    beginning, ending = start + timedelta(seconds=first * scale), start + timedelta(seconds=last * scale)
    if beginning.date() != date(year, 1, 1) or ending.year != year:
        raise DatasetError('CPC inventory has unexpected year boundaries')
    return ending.date()


def layout(path, variable):
    days = netcdf_days(path, variable)
    with NetCDF(path) as nc:
        lat, lon = nc.read('lat'), nc.read('lon')
        if (nc.shape(variable) != (len(days), 360, 720) or
                not np.array_equal(lat, np.arange(89.75, -90, -.5)) or
                not np.array_equal(lon, np.arange(.25, 360, .5))):
            raise DatasetError('CPC subset changed the native grid or its orientation')
        return days, nc.attributes(variable), nc.attributes('time')['units']


def checked_object(cache, record):
    path = cache / 'sha256' / record['sha256']
    if not path.is_file() or path.stat().st_size != record['bytes'] or digest(path) != record['sha256']:
        raise DatasetError('CPC incremental cache checksum mismatch: ' + str(path))
    return path


def keep_object(source, cache):
    sha = digest(source)
    obj = cache / 'sha256' / sha
    obj.parent.mkdir(parents=True, exist_ok=True)
    if obj.exists():
        checked_object(cache, {'sha256': sha, 'bytes': source.stat().st_size})
    else:
        fd, temporary = tempfile.mkstemp(prefix='.cpc-current-', dir=obj.parent)
        os.close(fd)
        temporary = Path(temporary)
        try:
            shutil.copyfile(source, temporary)
            if digest(temporary) != sha:
                raise DatasetError('CPC source changed during local import')
            with temporary.open('rb') as stream:
                os.fsync(stream.fileno())
            temporary.chmod(0o444)
            temporary.replace(obj)
        finally:
            temporary.unlink(missing_ok=True)
    return {'sha256': sha, 'bytes': source.stat().st_size}


def seed_current(cache, variable, year, seeds=()):
    index = cache / 'cpc-current' / f'{variable}.{year}.json'
    if index.exists():
        record = json.loads(index.read_text())
        if record.get('schema') != SCHEMA or record['variable'] != variable or record['year'] != year:
            raise DatasetError('Unsupported CPC incremental cache record')
        checked_object(cache, record)
        return record
    name = f'{variable}.{year}.nc'
    candidates = list(map(Path, seeds)) if seeds else [ROOT / 'assets.static/anthropocene/.raw/cpc' / name,
                  ROOT / 'output/ocean-temperature-stage-2-20261108/cache/cpc' / name,
                  *sorted((data_root() / 'editions').glob('*/inputs/anthropocene/.raw/cpc/' + name))]
    choices = []
    for path in dict.fromkeys(candidates):
        if not path.is_file():
            continue
        expected = None
        checksum_file = path.parent / 'SHA256SUMS'
        if checksum_file.exists():
            expected = next((line.split()[0] for line in checksum_file.read_text().splitlines()
                             if line.split()[-1].removeprefix('./') == name), None)
        receipt = path.with_name(name + '.receipt.json')
        if receipt.exists():
            expected = json.loads(receipt.read_text())['sha256']
        if path.parent == ROOT / 'output/ocean-temperature-stage-2-20261108/cache/cpc':
            acquired = json.loads((path.parents[2] / 'data/stage-2-acquisition.json').read_text())
            expected = next(row['sha256'] for row in acquired['inputs'] if Path(row['file']).name == name)
        sha = digest(path)
        if expected and sha != expected:
            raise DatasetError('Changed CPC seed checksum: ' + str(path))
        days, _, _ = layout(path, variable)
        if days[0] != date(year, 1, 1) or days[-1].year != year:
            raise DatasetError('CPC seed must start January 1 with a contiguous time axis')
        choices.append((days[-1], path, sha, bool(expected)))
    if not choices:
        raise DatasetError('No local CPC year prefix; supply --seed or explicitly bootstrap with CPC_INCREMENTAL=0')
    through, source, sha, verified = max(choices, key=lambda row: row[0])
    record = {**keep_object(source, cache), 'schema': SCHEMA, 'variable': variable, 'year': year,
              'data_through': str(through), 'cache_policy': 'append-only-daily-cpc',
              'acquisition': 'pinned-local-seed', 'parts': [],
              'seed': {'file': str(source.resolve()), 'sha256': sha, 'manifest_verified': verified},
              'assembled_at': utcnow()}
    atomic_json(index, record)
    print(f'CPC {variable} {year}: retained local observations through {through}', flush=True)
    return record


def validate_part(path, variable, day, seed_attrs):
    days, attrs, _ = layout(path, variable)
    if days != [day]:
        raise DatasetError(f'CPC subset returned {days}, expected exactly {day}')
    for key, default in (('units', None), ('missing_value', None), ('valid_range', None),
                         ('scale_factor', 1), ('add_offset', 0), ('max_period', None)):
        if not np.array_equal(attrs.get(key, default), seed_attrs.get(key, default)):
            raise DatasetError('CPC subset changed scientific metadata: ' + key)


def append_parts(source, parts, target, variable):
    """Append validated arrays through libnetcdf, preserving the existing prefix."""
    days, attrs, units = layout(source, variable)
    scale, origin = time_units(units)
    shutil.copyfile(source, target)
    with NetCDF(source) as original:
        history = original.attributes().get('history', '')
    lib = NetCDF.lib
    handle, varid, timeid, unlimited = C.c_int(), C.c_int(), C.c_int(), C.c_int()
    checker = NetCDF.__new__(NetCDF)
    checker.check(lib.nc_open(str(target).encode(), 1, C.byref(handle)))
    try:
        checker.check(lib.nc_inq_unlimdim(handle, C.byref(unlimited)))
        checker.check(lib.nc_inq_varid(handle, variable.encode(), C.byref(varid)))
        checker.check(lib.nc_inq_varid(handle, b'time', C.byref(timeid)))
        dimensions = (C.c_int * 3)()
        checker.check(lib.nc_inq_vardimid(handle, varid, dimensions))
        if unlimited.value != dimensions[0]:
            raise DatasetError('CPC seed needs an unlimited time dimension for incremental append')
        low, high = attrs['actual_range']
        last_value = None
        for day, path in parts:
            if day != days[-1] + timedelta(days=1):
                raise DatasetError('CPC incremental append would leave a date gap')
            with NetCDF(path) as part:
                data = np.ascontiguousarray(part.read(variable, decode=False), dtype='float32')
                part_scale, part_origin = time_units(part.attributes('time')['units'])
                values = np.ascontiguousarray(((part_origin - origin).total_seconds() +
                         part.read('time', decode=False).astype('float64') * part_scale) / scale)
            offset = len(days)
            checker.check(lib.nc_put_vara_float(handle, varid,
                (C.c_size_t * 3)(offset, 0, 0), (C.c_size_t * 3)(1, 360, 720),
                data.ctypes.data_as(C.POINTER(C.c_float))))
            checker.check(lib.nc_put_vara_double(handle, timeid,
                (C.c_size_t * 1)(offset), (C.c_size_t * 1)(1),
                values.ctypes.data_as(C.POINTER(C.c_double))))
            valid = np.isfinite(data) & (np.abs(data) < 1e30)
            if valid.any():
                low, high = min(low, float(data[valid].min())), max(high, float(data[valid].max()))
            last_value = float(values[-1])
            days.append(day)
        checker.check(lib.nc_redef(handle))
        text = (history + '\n' + utcnow() + ' cartofreako: appended missing daily CPC subsets; existing dates retained').encode()
        checker.check(lib.nc_put_att_text(handle, -1, b'history', C.c_size_t(len(text)), text))
        if last_value is not None:
            with NetCDF(source) as original:
                first_value = float(original.read('time', start=(0,), count=(1,), decode=False)[0])
            checker.check(lib.nc_put_att_double(handle, timeid, b'actual_range', 6, C.c_size_t(2),
                (C.c_double * 2)(first_value, last_value)))
            checker.check(lib.nc_put_att_float(handle, varid, b'actual_range', 5, C.c_size_t(2),
                (C.c_float * 2)(low, high)))
        checker.check(lib.nc_enddef(handle))
        checker.check(lib.nc_sync(handle))
    finally:
        checker.check(lib.nc_close(handle))
    if netcdf_days(target, variable) != days:
        raise DatasetError('Assembled CPC time axis failed validation')


def materialize(cache, record, output):
    obj = checked_object(cache, record)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + '.incremental-copy')
    temporary.unlink(missing_ok=True)
    try:
        try:
            os.link(obj, temporary)
        except OSError:
            shutil.copyfile(obj, temporary)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    atomic_json(output.with_name(output.name + '.receipt.json'), record)


def update(variable, year, cache, output=None, *, seeds=(), seed_only=False,
           subset_base=SUBSETS, as_of=None, fetcher=None):
    cache = Path(cache)
    fetcher = fetcher or fetch
    folder = cache / 'cpc-current'
    with lock(folder, f'{variable}.{year}'):
        record = seed_current(cache, variable, year, seeds)
        if seed_only:
            if output:
                materialize(cache, record, output)
            return record
        source = checked_object(cache, record)
        _, attrs, _ = layout(source, variable)
        base = subset_base.rstrip('/') + f'/{variable}.{year}.nc'
        listing = folder / 'inventory' / f'{variable}.{year}.xml'
        checked = fetcher(base + '/dataset.xml', listing, cache,
                          same_day_cache=os.environ.get('CPC_HTTP_DAILY_CACHE', '1') != '0')
        published = inventory(listing, year)
        through = date.fromisoformat(record['data_through'])
        if published < through:
            raise DatasetError('CPC provider time axis moved backwards; existing prefix retained')
        boundary = as_of or datetime.now(timezone.utc)
        limit = min(published, boundary.date() - timedelta(days=1), date(year, 12, 31))
        record = {**record, 'inventory_url': base + '/dataset.xml',
                  'inventory_checked_at': checked['checked_at'], 'published_through': str(published),
                  'pending_start': str(through + timedelta(days=1)) if limit > through else None,
                  'pending_through': str(limit) if limit > through else None}
        atomic_json(folder / f'{variable}.{year}.json', record)
        parts, receipts = [], []
        day = through + timedelta(days=1)
        while day <= limit:
            url = base + '?' + urlencode({'var': variable, 'time': str(day) + 'T00:00:00Z', 'accept': 'netcdf4'})
            path = folder / 'parts' / f'{variable}.{year}' / (str(day) + '.nc')
            receipt_path = path.with_name(path.name + '.receipt.json')
            if path.exists() and receipt_path.exists():
                receipt = json.loads(receipt_path.read_text())
                if receipt['sha256'] != digest(path) or receipt['url'] != url:
                    raise DatasetError('Changed cached CPC daily subset: ' + str(path))
            else:
                print(f'CPC {variable} {year}: fetching new observation {day}', flush=True)
                receipt = fetcher(url, path, cache, same_day_cache=True)
            validate_part(path, variable, day, attrs)
            parts.append((day, path))
            receipts.append({'date': str(day), 'url': url, 'sha256': receipt['sha256'],
                             'provider_checked_at': receipt['checked_at']})
            day += timedelta(days=1)
        if parts:
            with tempfile.TemporaryDirectory(prefix='assemble-', dir=folder) as temporary:
                candidate = Path(temporary) / f'{variable}.{year}.nc'
                append_parts(source, parts, candidate, variable)
                record = {**record, **keep_object(candidate, cache), 'data_through': str(parts[-1][0]),
                          'parts': [*record['parts'], *receipts], 'acquisition': 'incremental-local-assembly',
                          'assembled_at': utcnow()}
        record = {**record, 'inventory_url': base + '/dataset.xml',
                  'inventory_checked_at': checked['checked_at'], 'published_through': str(published),
                  'cache_policy': 'append-only-daily-cpc', 'pending_start': None, 'pending_through': None}
        atomic_json(folder / f'{variable}.{year}.json', record)
        if output:
            materialize(cache, record, output)
        print(f'CPC {variable} {year}: through {record["data_through"]}; '
              f'{len(parts)} missing days added; existing observations retained', flush=True)
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variable', choices=('tmax', 'tmin'), required=True)
    parser.add_argument('--year', type=int, default=2026)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--cache', type=Path, default=Path(os.environ.get('DATA_HTTP_CACHE', data_root() / 'cache')))
    parser.add_argument('--seed', action='append', type=Path, default=[])
    parser.add_argument('--seed-only', action='store_true', help='import the best local prefix without provider requests')
    parser.add_argument('--subset-base', default=os.environ.get('CPC_SUBSET_BASE_URL', SUBSETS))
    parser.add_argument('--as-of', default=os.environ.get('DATA_UPDATE_AS_OF'))
    args = parser.parse_args()
    try:
        as_of = datetime.fromisoformat(args.as_of) if args.as_of else None
        if as_of and (as_of.utcoffset() is None or as_of.utcoffset().total_seconds() != 0):
            raise DatasetError('--as-of must be UTC with an explicit timezone')
        update(args.variable, args.year, args.cache.expanduser().resolve(), args.output,
               seeds=args.seed, seed_only=args.seed_only, subset_base=args.subset_base, as_of=as_of)
    except (DatasetError, OSError, ValueError, KeyError, StopIteration, RuntimeError, E.ParseError) as error:
        print('fetch-cpc-current-year: ' + str(error) + '; saved prefix and downloaded day subsets retained', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
