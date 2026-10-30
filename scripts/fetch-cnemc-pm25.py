#!/usr/bin/env python3
"""Ingest hourly CNEMC concentrations from Wang Xiaolei's public Quotsoft archive."""
import argparse
import concurrent.futures
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import time

import requests

BASE = 'https://quotsoft.net/air/data/'


def fetch_day(job):
    day, root, stations = job
    stamp = day.strftime('%Y%m%d')
    url = BASE + f'china_sites_{stamp}.csv'
    path = root / 'raw' / f'china_sites_{stamp}.csv.gz'
    receipt = dict(date=day.isoformat(), url=url)
    if path.exists():
        body = gzip.decompress(path.read_bytes())
    else:
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=(20, 90))
                response.raise_for_status()
                body = response.content
                if not body.lstrip(b'\xef\xbb\xbf').startswith(b'date,hour,type,'):
                    raise ValueError('Archive response is not the documented hourly CSV')
                path.write_bytes(gzip.compress(body, mtime=0))
                break
            except (requests.RequestException, ValueError) as exc:
                if attempt == 2 or (isinstance(exc, requests.HTTPError) and exc.response.status_code == 404):
                    return dict(receipt, error=str(exc)), []
                time.sleep(2 * (attempt + 1))
    rows = list(csv.DictReader(io.StringIO(body.decode('utf-8-sig'))))
    pm = [r for r in rows if r['type'] == 'PM2.5']
    assert all(r['date'] == stamp for r in pm)
    unique = {}
    negative = missing = conflicts = 0
    for row in pm:
        hour = int(row['hour'])
        assert 0 <= hour < 24
        for station in stations:
            if station not in row:
                continue
            try:
                value = float(row[station])
            except (ValueError, TypeError):
                missing += 1
                continue
            if not math.isfinite(value) or value < 0:
                negative += 1
                continue
            key = (station, hour)
            if key in unique and unique[key] != value:
                conflicts += 1
                unique[key] = None
            else:
                unique[key] = value
    values = {}
    for (station, hour), value in unique.items():
        if value is not None:
            values.setdefault(station, []).append(value)
    result = []
    for station, vals in sorted(values.items()):
        result.append(dict(source='cnemc-quotsoft', country='CHN', station_id=station,
                           date=day.isoformat(), valid_hours=len(vals),
                           mean_ug_m3=round(sum(vals) / len(vals), 6), eligible=len(vals) >= 18,
                           **stations[station]))
    codes = set(rows[0]) - {'date', 'hour', 'type'} if rows else set()
    receipt.update(raw_file=str(path.relative_to(root)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                   pm25_hour_rows=len(pm), raw_station_columns=len(codes),
                   unmatched_station_codes=sorted(codes - set(stations)),
                   negative_nonfinite_excluded=negative, missing_values=missing,
                   conflicting_hours=conflicts, eligible_station_days=sum(r['eligible'] for r in result))
    print(f'CNEMC {day}: {receipt["eligible_station_days"]} valid station-days', flush=True)
    return receipt, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--start', default='2025-01-01')
    parser.add_argument('--through', default='2026-10-28')
    args = parser.parse_args()
    root = args.output
    (root / 'raw').mkdir(parents=True, exist_ok=True)
    source = root / 'stations-cnemc-20220213.csv'
    stations = {}
    excluded_coordinates = []
    for s in csv.DictReader(source.open(encoding='utf-8-sig')):
        try:
            lat, lon = float(s['纬度']), float(s['经度'])
            assert 15 < lat < 55 and 70 < lon < 140
        except (ValueError, AssertionError):
            excluded_coordinates.append(s['监测点编码'])
            continue
        assert s['监测点编码'] not in stations
        stations[s['监测点编码']] = dict(station_name=s['监测点名称'], station_type='government monitor',
                                           city=s['城市'], latitude=lat, longitude=lon)
    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.through)
    dates = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
    receipts, rows = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for receipt, data in pool.map(fetch_day, [(d, root, stations) for d in dates]):
            receipts.append(receipt)
            rows.extend(data)
            if len(receipts) % 20 == 0:
                (root / 'cnemc-download-receipts.json').write_text(json.dumps(receipts, indent=2) + '\n')
    fields = ['source', 'country', 'station_id', 'station_name', 'station_type', 'city', 'latitude', 'longitude', 'date', 'valid_hours', 'mean_ug_m3', 'eligible']
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    target = root / 'cnemc-station-days.csv.gz'
    target.write_bytes(gzip.compress(text.getvalue().encode(), mtime=0))
    (root / 'cnemc-download-receipts.json').write_text(json.dumps(receipts, indent=2) + '\n')
    report = dict(source='CNEMC via Wang Xiaolei / Quotsoft public archive',
                  retrieved_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  requested_dates=[args.start, args.through],
                  station_coordinate_inventory_date='2022-02-13',
                  coordinate_inventory_url='https://github.com/bryt888/hfaw/blob/3cd38dc7a3feb285ef143301455fb03748b572f5/AQI/data/stations_20220213.csv',
                  coordinate_file_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  coordinate_limit='Historical station-code join, not a current surveyed inventory; unmatched/new/relocated stations need further review.',
                  coordinate_rows_rejected=excluded_coordinates,
                  concentration_unit='micrograms per cubic metre', local_timezone='Asia/Shanghai',
                  daily_rule='Mean of at least 18 distinct nonnegative valid hourly PM2.5 observations; PM2.5_24h and AQI rows excluded',
                  failures=[r for r in receipts if 'error' in r],
                  stations=len({r['station_id'] for r in rows}), station_days=len(rows),
                  eligible_station_days=sum(r['eligible'] for r in rows),
                  normalized_file=target.name, sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    (root / 'cnemc-quality.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
