#!/usr/bin/env python3
"""Fetch selected, publicly documented OpenAQ stations from its key-free S3 archive."""
import argparse
from collections import defaultdict
import concurrent.futures
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import threading
import time
import xml.etree.ElementTree as E

from bs4 import BeautifulSoup
import requests

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


def list_files(location, year, root):
    path = root / 'raw' / f'openaq-{location}-{year}-index.xml'
    if not path.exists():
        params = {'list-type': '2', 'prefix': f'records/csv.gz/locationid={location}/year={year}/', 'max-keys': 1000}
        path.write_bytes(get(S3, params).content)
    tree = E.fromstring(path.read_bytes())
    ns = {'s': 'http://s3.amazonaws.com/doc/2006-03-01/'}
    assert tree.findtext('s:IsTruncated', namespaces=ns) == 'false'
    return [e.text for e in tree.findall('s:Contents/s:Key', ns)]


def fetch_file(job):
    key, root = job
    path = root / 'raw' / Path(key).name
    try:
        if not path.exists():
            path.write_bytes(get(S3 + key).content)
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
        return dict(key=key, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    pm25_rows=len(rows), negative_nonfinite_excluded=negative, wrong_unit_excluded=wrong_unit), rows
    except (requests.RequestException, ValueError) as exc:
        return dict(key=key, error=str(exc)), []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = args.output
    (root / 'raw').mkdir(parents=True, exist_ok=True)
    metadata = []
    keys = []
    for location, (name, provider, kind) in LOCATIONS.items():
        url = f'https://explore.openaq.org/locations/{location}'
        path = root / 'raw' / f'openaq-location-{location}.html'
        if not path.exists():
            path.write_bytes(get(url).content)
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
        for year in [2025, 2026]:
            available = list_files(location, year, root)
            keys.extend(available)
            print(f'OpenAQ {location} {year}: {len(available)} daily archive files', flush=True)
    receipts, observations = [], defaultdict(lambda: defaultdict(dict))
    duplicate = conflict = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for index, (receipt, rows) in enumerate(pool.map(fetch_file, [(k, root) for k in keys])):
            receipts.append(receipt)
            for location, sensor, stamp, lat, lon, value in rows:
                if not '2025-01-01' <= stamp[:10] <= '2026-10-28':
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
                print(f'OpenAQ files {index+1}/{len(keys)}', flush=True)
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
        name, provider, kind = LOCATIONS[location]
        normalized.append(dict(source='openaq-' + provider.lower(), country='IND', station_id=str(location),
                               station_name=name, station_type=kind, latitude=lat, longitude=lon,
                               date=date, valid_hours=hours, mean_ug_m3=round(mean, 6), eligible=hours >= 18,
                               sensor_id=sensor))
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=list(normalized[0]))
    writer.writeheader()
    writer.writerows(normalized)
    target = root / 'openaq-station-days.csv.gz'
    target.write_bytes(gzip.compress(text.getvalue().encode(), mtime=0))
    (root / 'openaq-locations.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (root / 'openaq-download-receipts.json').write_text(json.dumps(receipts, indent=2) + '\n')
    report = dict(source='OpenAQ public AWS archive; CPCB, AirNow, AirGradient providers',
                  retrieved_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  coverage='Selected Indian urban locations; not an exhaustive national inventory',
                  local_timezone='Asia/Kolkata', unit='micrograms per cubic metre',
                  daily_rule='At least 18 distinct valid hours; within-hour readings averaged; choose the sensor with the most valid hours per station-day, ties by sensor ID',
                  duplicate_timestamp_rows=duplicate, conflicting_timestamp_keys=conflict,
                  multiple_pm25_sensor_days=multiple_sensor_days, stations=len(LOCATIONS),
                  station_days=len(normalized), eligible_station_days=sum(r['eligible'] for r in normalized),
                  normalized_file=target.name, sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  failures=[r for r in receipts if 'error' in r])
    (root / 'openaq-quality.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
