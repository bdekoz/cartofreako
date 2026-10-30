#!/usr/bin/env python3
"""Download public, provisional MOE/Soramame PM2.5 and retain daily QC evidence.

No credentials. The service permits a rolling year and at most three months
per query. Hour 01..24 belongs to the supplied local (JST) observation date.
"""
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

BASE = 'https://soramame.env.go.jp'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fetch_window(job):
    pref, start, end, root = job
    raw = root / 'raw' / f'soramame-{pref}-{start}-{end}.json.gz'
    params = dict(Start_YM=start, End_YM=end, TDFKN_CD=pref, REQUEST_DATA='PM2_5')
    url = requests.Request('GET', BASE + '/soramame/api/data_search', params=params).prepare().url
    receipt = dict(prefecture=pref, start_month=start, end_month=end, url=url)
    if raw.exists():
        body = gzip.decompress(raw.read_bytes())
    else:
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=(20, 120))
                response.raise_for_status()
                body = response.content
                rows = response.json()
                if not isinstance(rows, list):
                    raise ValueError('Expected an array of hourly observations')
                raw.write_bytes(gzip.compress(body, mtime=0))
                break
            except (requests.RequestException, ValueError) as exc:
                if attempt == 2:
                    receipt['error'] = str(exc)
                    return receipt, []
                time.sleep(2 * (attempt + 1))
    rows = json.loads(body)
    receipt.update(raw_file=str(raw.relative_to(root)), sha256=digest(raw.read_bytes()),
                   uncompressed_sha256=digest(body), hourly_slots=len(rows))
    days, seen = {}, {}
    missing = negative = duplicates = conflicts = 0
    status_codes = {}
    for row in rows:
        key = (str(row['SKT_CD']), row['SKT_DATE'].replace('/', '-'), int(row['SKT_TIME']))
        assert 1 <= key[2] <= 24
        value = row.get('PM2_5', '')
        try:
            value = float(value)
        except (ValueError, TypeError):
            missing += 1
            continue
        if not math.isfinite(value) or value < 0:
            negative += 1
            continue
        # MOE/NIES and prefectural formats reserve 999x for missing,
        # unmeasured, calibration and instrument errors, not concentrations.
        if value >= 9990:
            code = str(int(value))
            status_codes[code] = status_codes.get(code, 0) + 1
            continue
        if key in seen:
            duplicates += 1
            if seen[key] != value:
                conflicts += 1
                seen[key] = None
            continue
        seen[key] = value
    for (station, day, hour), value in seen.items():
        if value is not None:
            days.setdefault((station, day), []).append(value)
    normalized = []
    for (station, day), values in sorted(days.items()):
        normalized.append(dict(source='jp-moe-soramame', country='JPN', station_id=station,
                               date=day, valid_hours=len(values),
                               mean_ug_m3=round(sum(values) / len(values), 6),
                               eligible=len(values) >= 18))
    receipt.update(nonnumeric_slots=missing, negative_values_excluded=negative,
                   numeric_status_codes_excluded=status_codes,
                   duplicate_hour_rows=duplicates, conflicting_hour_keys=conflicts,
                   station_days=len(normalized),
                   eligible_station_days=sum(r['eligible'] for r in normalized))
    print(f'Soramame {pref} {start}..{end}: {receipt["eligible_station_days"]} valid station-days', flush=True)
    return receipt, normalized


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stations', type=Path, required=True)
    parser.add_argument('--windows', nargs='+', default=['202511:202512', '202601:202603', '202604:202606', '202607:202609'])
    parser.add_argument('--prefectures', nargs='+', default=[f'{i:02}' for i in range(1, 48)])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'raw').mkdir(exist_ok=True)
    stations = {s['測定局コード']: s for s in csv.DictReader(args.stations.open())}
    (args.output / 'stations-soramame.csv').write_bytes(args.stations.read_bytes())
    jobs = [(pref, *window.split(':'), args.output) for pref in args.prefectures for window in args.windows]
    receipts, normalized, unmatched = [], [], set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for receipt, rows in pool.map(fetch_window, jobs):
            receipts.append(receipt)
            for row in rows:
                station = stations.get(row['station_id'])
                if station is None:
                    unmatched.add(row['station_id'])
                    continue
                row.update(latitude=float(station['緯度']), longitude=float(station['経度']),
                           station_name=station['測定局名称'], station_type=station['測定局種別'])
                normalized.append(row)
            # Save an inspectable checkpoint while the remaining prefectures run.
            (args.output / 'soramame-download-receipts.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n')
    normalized.sort(key=lambda r: (r['station_id'], r['date']))
    assert len({(r['station_id'], r['date']) for r in normalized}) == len(normalized)
    fields = ['source', 'country', 'station_id', 'station_name', 'station_type', 'latitude', 'longitude', 'date', 'valid_hours', 'mean_ug_m3', 'eligible']
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=fields)
    writer.writeheader()
    writer.writerows(normalized)
    target = args.output / 'soramame-station-days.csv.gz'
    target.write_bytes(gzip.compress(text.getvalue().encode(), mtime=0))
    report = dict(source='Japan Ministry of the Environment / Soramame',
                  retrieved_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  status='provisional observations; subject to later correction',
                  unit='micrograms per cubic metre', local_timezone='Asia/Tokyo',
                  daily_rule='at least 18 distinct nonnegative finite hourly concentrations excluding 999x status codes; hours 01..24 use the supplied JST date',
                  status_code_reference='https://www.env.go.jp/content/900402531.pdf (table 6-4-1); https://taiki-kanshi.wakayama.jp/wp-content/uploads/2024/10/hosoku.pdf',
                  spatial_rule='latest published station-code coordinates; unmatched historical stations excluded',
                  unmatched_station_ids=sorted(unmatched), windows=args.windows,
                  requested_prefectures=args.prefectures, failures=[r for r in receipts if 'error' in r],
                  stations=len({r['station_id'] for r in normalized}), station_days=len(normalized),
                  eligible_station_days=sum(r['eligible'] for r in normalized),
                  normalized_file=target.name, sha256=digest(target.read_bytes()),
                  coordinate_file_sha256=digest(args.stations.read_bytes()))
    (args.output / 'soramame-quality.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
