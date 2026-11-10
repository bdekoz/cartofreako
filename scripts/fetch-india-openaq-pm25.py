#!/usr/bin/env python3
"""Fetch selected Indian OpenAQ PM2.5 station-days, preserving downloaded archives."""
import argparse
from collections import Counter, defaultdict
import concurrent.futures
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import threading
import time
import shutil
import xml.etree.ElementTree as E

from bs4 import BeautifulSoup
import requests
from dataset import atomic_json, digest, lock

PROJECT = Path(__file__).resolve().parents[1]

S3 = 'https://openaq-data-archive.s3.amazonaws.com/'
# Spatially distributed, documented reference monitors; this is an explicitly
# selected urban sample, not an exhaustive inventory or a country mean.
LOCATIONS = {
    8118: ('New Delhi', 'AirNow', 'reference'),
    8039: ('Mumbai', 'AirNow', 'reference'),
    235: ('Anand Vihar, Delhi', 'CPCB', 'reference'),
    6956: ('Powai, Mumbai', 'CPCB', 'reference'),
    5655: ('Velachery, Chennai', 'CPCB', 'reference'),
    10851: ('Bidhannagar, Kolkata', 'CPCB', 'reference'),
    5548: ('BTM Layout, Bengaluru', 'CPCB', 'reference'),
    5631: ('Maninagar, Ahmedabad', 'CPCB', 'reference'),
    2456: ('Talkatora, Lucknow', 'CPCB', 'reference'),
    407: ('Zoo Park, Hyderabad', 'CPCB', 'reference'),
    220265: ('Rajbagh, Srinagar', 'CPCB', 'reference'),
    3409498: ('Residency Area, Indore', 'CPCB', 'reference'),
    5646: ('Plammoodu, Thiruvananthapuram', 'CPCB', 'reference'),
    10599: ('Rajbansi Nagar, Patna', 'CPCB', 'reference'),
    3409430: ('Mansarovar, Jaipur', 'CPCB', 'reference'),
    233415: ('Sector 22, Chandigarh', 'CPCB', 'reference'),
    5728639: ('Bemina, Srinagar', 'AirGradient', 'air-sensor'),
}
TLS = threading.local()


class ArchiveCache:
    """Reuse verified daily bytes across editions and adopt earlier local downloads."""
    def __init__(self, directory, output, reuse_from=()):
        self.directory, self.output = Path(directory), Path(output)
        candidates = [self.output/'raw', *map(Path, reuse_from)]
        data = Path(os.environ.get('DATA_ROOT', PROJECT/'.cartofreako/data'))
        candidates += sorted(data.glob('editions/*/inputs/india/openaq/raw'), reverse=True)
        for pattern in ('*/openaq/raw', '*/*/openaq/raw'):
            candidates += sorted((PROJECT/'output').glob(pattern))
        candidates += [PROJECT/'assets.static/anthropocene/asia-pm25/raw']
        self.reuse = list(dict.fromkeys(p.resolve() for p in candidates if p.is_dir()))
        self.expected = {}
        for folder in self.reuse:
            receipts = folder.parent/'openaq-download-receipts.json'
            if receipts.is_file():
                self.expected[folder] = {Path(r['key']).name:r['sha256'] for r in
                                         json.loads(receipts.read_text()) if r.get('sha256')}

    def materialize(self, cached, name):
        target = self.output/'raw'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.resolve() == cached.resolve():
            return target
        temporary = target.with_name(name+'.part')
        temporary.unlink(missing_ok=True)
        # Cache inodes are read-only and are replaced, never edited in place.
        # Completed editions therefore retain their exact earlier bytes.
        try:
            os.link(cached, temporary)
        except OSError:
            shutil.copyfile(cached, temporary)
        temporary.replace(target)
        return target

    def get(self, name, url, loader, refresh=False):
        cached = self.directory/'raw'/name
        receipt = self.directory/'receipts'/(name+'.json')
        with lock(self.directory/'locks', hashlib.sha256(name.encode()).hexdigest()):
            prior = json.loads(receipt.read_text()) if receipt.exists() else None
            if cached.exists() and prior and digest(cached) != prior['sha256']:
                raise ValueError('Cached OpenAQ archive checksum changed: '+name)
            acquisition = 'cache-reused'
            if refresh or not cached.exists():
                adopted = None if refresh else next((p/name for p in self.reuse if (p/name).is_file()), None)
                if adopted:
                    body = adopted.read_bytes()
                    expected = self.expected.get(adopted.parent, {}).get(name)
                    if expected and hashlib.sha256(body).hexdigest()!=expected:
                        raise ValueError('Earlier OpenAQ download checksum changed: '+str(adopted))
                    acquisition = 'cache-imported'
                else:
                    body = loader()
                    acquisition = 'downloaded'
                if name.endswith('.csv.gz'):
                    decoded = gzip.decompress(body).decode('utf-8-sig')
                    required = {'location_id','sensors_id','datetime','lat','lon','parameter','units','value'}
                    if not required.issubset(csv.DictReader(io.StringIO(decoded)).fieldnames or []):
                        raise ValueError('Invalid OpenAQ archive columns: '+name)
                cached.parent.mkdir(parents=True, exist_ok=True)
                write_cache(cached, body)
                cached.chmod(0o444)
                prior = {'url':url,'sha256':digest(cached),
                         'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat() if acquisition=='downloaded' else None,
                         'imported_from':str(adopted) if adopted else None}
                atomic_json(receipt, prior)
            elif prior is None:
                prior = {'url':url,'sha256':digest(cached),'retrieved_at_utc':None,'imported_from':None}
                atomic_json(receipt, prior)
            return self.materialize(cached, name), {**prior, 'acquisition':acquisition}


def write_cache(path, body):
    # Replacement preserves earlier snapshots that share immutable cache inodes.
    temporary = path.with_name(path.name + '.part')
    temporary.write_bytes(body)
    temporary.replace(path)


def get(url, params=None):
    if not hasattr(TLS, 'session'):
        TLS.session = requests.Session()
    for attempt in range(3):
        try:
            r = TLS.session.get(url, params=params, timeout=(15, 60))
            r.raise_for_status()
            return r
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)


def list_files(location, year, root, refresh=False, cache=None):
    path = root / 'raw' / f'openaq-{location}-{year}-index.xml'
    params = {'list-type': '2', 'prefix': f'records/csv.gz/locationid={location}/year={year}/', 'max-keys': 1000}
    if cache is not None:
        path, _ = cache.get(path.name, S3+'?prefix='+params['prefix'], lambda:get(S3, params).content, refresh)
    elif refresh or not path.exists():
        write_cache(path, get(S3, params).content)
    tree = E.fromstring(path.read_bytes())
    ns = {'s': 'http://s3.amazonaws.com/doc/2006-03-01/'}
    assert tree.findtext('s:IsTruncated', namespaces=ns) == 'false'
    return [e.text for e in tree.findall('s:Contents/s:Key', ns)]


def fetch_file(job):
    key, root, refresh, cache = job
    path = root / 'raw' / Path(key).name
    try:
        path, acquisition = cache.get(path.name, S3+key, lambda:get(S3+key).content, refresh)
        rows = []
        negative = wrong_unit = 0
        for r in csv.DictReader(io.StringIO(gzip.decompress(path.read_bytes()).decode('utf-8-sig'))):
            if r['parameter'].lower() != 'pm25':
                continue
            if r['units'].replace('μ', 'µ') not in ['µg/m³', 'µg/m3', 'ug/m3']:
                wrong_unit += 1
                continue
            try:
                value = float(r['value'])
            except ValueError:
                continue
            if not math.isfinite(value) or value < 0:
                negative += 1
                continue
            stamp = dt.datetime.fromisoformat(r['datetime'])
            assert stamp.utcoffset() == dt.timedelta(hours=5, minutes=30)
            rows.append((int(r['location_id']), int(r['sensors_id']), stamp.isoformat(),
                         float(r['lat']), float(r['lon']), value))
        return dict(key=key, **acquisition,
                    pm25_rows=len(rows), negative_nonfinite_excluded=negative, wrong_unit_excluded=wrong_unit), rows
    except (requests.RequestException, ValueError, OSError, EOFError) as exc:
        return dict(key=key, error=str(exc)), []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--cache-dir', type=Path,
                        default=Path(os.environ.get('DATA_ROOT', PROJECT/'.cartofreako/data'))/'cache/india-openaq',
                        help='Persistent raw archive cache shared across update runs')
    parser.add_argument('--reuse-from', action='append', type=Path, default=[],
                        help='Earlier raw download directory to import without network requests; repeatable')
    parser.add_argument('--locations-json', type=Path,
                        help='Versioned location inventory with id, name, provider and kind fields')
    parser.add_argument('--start', type=dt.date.fromisoformat, default=dt.date(2025, 1, 1))
    parser.add_argument('--end', type=dt.date.fromisoformat, default=dt.date(2026, 10, 28),
                        help='Inclusive observation-date cutoff in Asia/Kolkata')
    parser.add_argument('--refresh-index', action='store_true',
                        help='Refresh cached archive listings to discover newly published days')
    parser.add_argument('--refresh-since', type=dt.date.fromisoformat,
                        help='Redownload cached daily files from this date to capture revisions')
    args = parser.parse_args()
    if args.start > args.end:
        parser.error('--start must not be after --end')
    locations = LOCATIONS
    coverage_description = 'Selected Indian urban locations; not an exhaustive national inventory'
    if args.locations_json:
        inventory = json.loads(args.locations_json.read_text())
        records = inventory['locations']
        locations = {int(r['id']): (r['name'], r['provider'], r['kind']) for r in records}
        if not locations or len(locations) != len(records):
            parser.error('Location IDs must be nonempty and unique')
        if any(r.get('country') != 'IND' for r in records):
            parser.error('This adapter requires country=IND for every location')
        coverage_description = inventory['coverage']
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    root = args.output
    (root / 'raw').mkdir(parents=True, exist_ok=True)
    cache = ArchiveCache(args.cache_dir, root, args.reuse_from)
    metadata = []
    keys = []
    for location, (name, provider, kind) in locations.items():
        url = f'https://explore.openaq.org/locations/{location}'
        path = root / 'raw' / f'openaq-location-{location}.html'
        path, _ = cache.get(path.name, url, lambda:get(url).content)
        html = path.read_text()
        soup = BeautifulSoup(html, 'html.parser')
        description = soup.get_text(' ', strip=True)
        assert provider in description and 'PM2.5' in description
        assert ('Reference grade' if kind == 'reference' else 'Air sensor') in description
        # The source declares location country; do not infer from its time zone.
        assert re.search(r'code:"IN"', html), f'Country not verified for {location}'
        row = dict(id=location, country='IND', name=name, provider=provider, kind=kind,
                   metadata_url=url, metadata_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        metadata.append(row)
        for year in range(args.start.year, args.end.year + 1):
            available = list_files(location, year, root, args.refresh_index, cache)
            keys.extend(available)
            print(f'OpenAQ {location} {year}: {len(available)} daily archive files', flush=True)
    receipts, observations = [], defaultdict(lambda: defaultdict(dict))
    duplicate = conflict = 0
    jobs = []
    for key in keys:
        file_date = dt.datetime.strptime(Path(key).name.rsplit('-', 1)[1][:8], '%Y%m%d').date()
        # Archive partitions can differ from local observation dates. Keep a
        # one-day margin and apply the exact inclusive limit to each row below.
        if args.start - dt.timedelta(days=1) <= file_date <= args.end + dt.timedelta(days=1):
            refresh = args.refresh_since is not None and file_date >= args.refresh_since
            jobs.append((key, root, refresh, cache))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for index, (receipt, rows) in enumerate(pool.map(fetch_file, jobs)):
            receipts.append(receipt)
            for location, sensor, stamp, lat, lon, value in rows:
                if not args.start.isoformat() <= stamp[:10] <= args.end.isoformat():
                    continue
                assert 6 < lat < 37 and 67 < lon < 98
                group = observations[(location, stamp[:10])][sensor]
                if stamp in group:
                    duplicate += 1
                    if group[stamp] != (lat, lon, value):
                        conflict += 1
                        group[stamp] = None
                else:
                    group[stamp] = (lat, lon, value)
            if (index + 1) % 250 == 0:
                print(f'OpenAQ files {index+1}/{len(jobs)}', flush=True)
                (root / 'openaq-download-receipts.json').write_text(json.dumps(receipts, indent=2) + '\n')
    normalized = []
    multiple_sensor_days = 0
    for (location, date), sensors in sorted(observations.items()):
        daily = []
        for sensor, readings in sensors.items():
            hours = defaultdict(list)
            coords = set()
            for stamp, values in readings.items():
                if values is None:
                    continue
                lat, lon, value = values
                coords.add((lat, lon))
                hours[stamp[:13]].append(value)
            if not hours:
                continue
            # Exclude relocated/ambiguous daily records instead of assigning a
            # measurement to an invented average coordinate.
            if len(coords) != 1:
                continue
            vals = [sum(v)/len(v) for v in hours.values()]
            daily.append((len(vals), sensor, sum(vals)/len(vals), next(iter(coords))))
        if not daily:
            continue
        multiple_sensor_days += len(daily) > 1
        hours, sensor, mean, (lat, lon) = sorted(daily, key=lambda d: (-d[0], d[1]))[0]
        name, provider, kind = locations[location]
        normalized.append(dict(source='openaq-' + provider.lower(), country='IND', station_id=str(location),
                               station_name=name, station_type=kind, latitude=lat, longitude=lon,
                               date=date, valid_hours=hours, mean_ug_m3=round(mean, 6), eligible=hours >= 18,
                               sensor_id=sensor))
    if not normalized:
        raise ValueError('No valid PM2.5 station-days in the requested interval')
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=list(normalized[0]))
    writer.writeheader()
    writer.writerows(normalized)
    target = root / 'openaq-station-days.csv.gz'
    target.write_bytes(gzip.compress(text.getvalue().encode(), mtime=0))
    (root / 'openaq-locations.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (root / 'openaq-download-receipts.json').write_text(json.dumps(receipts, indent=2) + '\n')
    report = dict(source='OpenAQ public AWS archive; CPCB, AirNow, AirGradient providers',
                  retrieval_started_at_utc=started_at,
                  retrieved_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  requested_start=args.start.isoformat(), requested_end=args.end.isoformat(),
                  observed_first_date=min(r['date'] for r in normalized),
                  observed_last_date=max(r['date'] for r in normalized),
                  eligible_last_date=max((r['date'] for r in normalized if r['eligible']), default=None),
                  archive_indexes_refreshed=args.refresh_index,
                  raw_cache_policy='preserve-downloaded-daily-files',
                  raw_cache_directory=str(args.cache_dir),
                  raw_acquisition_counts=dict(Counter(r.get('acquisition','failed') for r in receipts)),
                  raw_files_refreshed_since=args.refresh_since.isoformat() if args.refresh_since else None,
                  coverage=coverage_description,
                  location_inventory=str(args.locations_json) if args.locations_json else 'legacy built-in selection',
                  local_timezone='Asia/Kolkata', unit='micrograms per cubic metre',
                  daily_rule='At least 18 distinct valid hours; within-hour readings averaged; choose the sensor with the most valid hours per station-day, ties by sensor ID',
                  duplicate_timestamp_rows=duplicate, conflicting_timestamp_keys=conflict,
                  multiple_pm25_sensor_days=multiple_sensor_days, stations=len(locations),
                  station_days=len(normalized), eligible_station_days=sum(r['eligible'] for r in normalized),
                  normalized_file=target.name, sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  failures=[r for r in receipts if 'error' in r])
    (root / 'openaq-quality.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
