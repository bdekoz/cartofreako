#!/usr/bin/env python3
"""Merge audited Asian PM2.5 cell-days into existing source-separated atlases."""
import argparse
from collections import defaultdict
import csv
import ctypes as C
import gzip
import hashlib
import io
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LatLng(C.Structure):
    _fields_ = [('lat', C.c_double), ('lng', C.c_double)]


LIB = C.CDLL('libh3.so')
LIB.latLngToCell.argtypes = [C.POINTER(LatLng), C.c_int, C.POINTER(C.c_uint64)]
LIB.cellToLatLng.argtypes = [C.c_uint64, C.POINTER(LatLng)]


def h3_cell(lat, lon):
    coord, result = LatLng(math.radians(lat), math.radians(lon)), C.c_uint64()
    assert LIB.latLngToCell(C.byref(coord), 4, C.byref(result)) == 0
    return f'{result.value:x}'


def center(cell):
    coord = LatLng()
    assert LIB.cellToLatLng(int(cell, 16), C.byref(coord)) == 0
    return [math.degrees(coord.lng), math.degrees(coord.lat)]


REFERENCE_SOURCES = ['jp-moe-soramame', 'cnemc-quotsoft', 'openaq-cpcb', 'openaq-airnow']
METRICS = [
    ('pm25_measured_days', 'PM2.5 valid monitor days (at least 18 hours)', '#087f82', 'ring', 300, REFERENCE_SOURCES),
    ('pm25_concentration_gt35_days', 'Monitor daily PM2.5 >35 µg/m³ days', '#cd5a2a', 'cross-square', 120, REFERENCE_SOURCES),
    ('pm25_sensor_measured_days', 'AirGradient valid sensor days (separate)', '#b33b99', 'diamond', 300, ['openaq-airgradient']),
    ('pm25_sensor_gt35_days', 'AirGradient daily PM2.5 >35 µg/m³ days', '#722278', 'circle', 120, ['openaq-airgradient']),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'assets.static/anthropocene/asia-pm25')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    coverage = defaultdict(lambda: defaultdict(set))
    exceed = defaultdict(lambda: defaultdict(set))
    countries = defaultdict(lambda: dict(stations=set(), cells=set(), days=set(), station_days=0, over35_station_days=0, minimum=math.inf, maximum=-math.inf))
    source_stats = defaultdict(lambda: dict(stations=set(), dates=set(), eligible_station_days=0))
    input_files, seen, coord_cache = [], set(), {}
    extreme_review = []
    for name in ['soramame', 'cnemc', 'openaq']:
        path = args.input / f'{name}-station-days.csv.gz'
        input_files.append(dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        with gzip.open(path, 'rt') as stream:
            for row in csv.DictReader(stream):
                if row['eligible'].lower() != 'true':
                    continue
                assert 18 <= int(row['valid_hours']) <= 24
                value = float(row['mean_ug_m3'])
                assert math.isfinite(value) and value >= 0
                if value > 250:
                    extreme_review.append({k: row[k] for k in ['source', 'country', 'station_id', 'date', 'valid_hours', 'mean_ug_m3']})
                key = (row['source'], row['station_id'], row['date'])
                assert key not in seen, f'Duplicate station-day: {key}'
                seen.add(key)
                year = int(row['date'][:4])
                assert year in [2025, 2026]
                coords = (float(row['latitude']), float(row['longitude']))
                if coords not in coord_cache:
                    coord_cache[coords] = h3_cell(*coords)
                cell = coord_cache[coords]
                kind = 'sensor' if row['source'] == 'openaq-airgradient' else 'monitor'
                group = (year, kind)
                coverage[group][cell].add(row['date'])
                if value > 35:
                    exceed[group][cell].add(row['date'])
                stat = countries[(year, row['country'], kind)]
                stat['stations'].add((row['source'], row['station_id']))
                stat['cells'].add(cell)
                stat['days'].add(row['date'])
                stat['station_days'] += 1
                stat['over35_station_days'] += value > 35
                stat['minimum'] = min(stat['minimum'], value)
                stat['maximum'] = max(stat['maximum'], value)
                ss = source_stats[(year, row['source'])]
                ss['stations'].add(row['station_id'])
                ss['dates'].add(row['date'])
                ss['eligible_station_days'] += 1
    country_rows = []
    for (year, country, kind), stat in sorted(countries.items()):
        country_rows.append(dict(year=year, country=country, instrument_class=kind,
                                 stations=len(stat['stations']), h3_cells=len(stat['cells']),
                                 first_date=min(stat['days']), last_date=max(stat['days']),
                                 distinct_dates=len(stat['days']), valid_station_days=stat['station_days'],
                                 station_days_above_35=stat['over35_station_days'],
                                 daily_mean_min_ug_m3=stat['minimum'], daily_mean_max_ug_m3=stat['maximum']))
    source_definitions = {
        'jp-moe-soramame': ('Japan MOE / Soramame provisional government monitors', 'https://soramame.env.go.jp/'),
        'cnemc-quotsoft': ('China CNEMC hourly monitor data via Wang Xiaolei / Quotsoft; 2022 station-coordinate join', 'https://quotsoft.net/air/'),
        'openaq-cpcb': ('Selected Indian CPCB government monitors via OpenAQ public archive', 'https://openaq-data-archive.s3.amazonaws.com/'),
        'openaq-airnow': ('Selected Indian AirNow government monitors via OpenAQ public archive', 'https://openaq-data-archive.s3.amazonaws.com/'),
        'openaq-airgradient': ('One Indian AirGradient low-cost sensor; not a reference monitor; CC BY 4.0', 'https://explore.openaq.org/locations/5728639'),
    }
    checks, ledger = [], []
    for year in [2025, 2026]:
        stem = f'anthropocene-particulate-{year}'
        profile = json.loads((ROOT / f'assets.static/anthropocene/{stem}-profile.json').read_text())
        base_path = ROOT / f'assets.static/anthropocene/{stem}.geojson'
        data = json.loads(base_path.read_text())
        old_totals = data['metadata']['metric_cell_day_totals'].copy()
        old_features = {f['id']: f for f in data['features']}
        features = {f['id']: json.loads(json.dumps(f)) for f in data['features']}
        profile['snapshot'].update(as_of_utc='2026-10-29T23:00:00Z', data_through=f'{year}-12-31' if year == 2025 else '2026-10-28')
        profile['thresholds'].update(pm25_concentration_threshold_exclusive_ug_m3=35, pm25_minimum_valid_hours_per_day=18)
        profile['description'] += ' Asian measured PM2.5 and AirGradient sensor observations are separate from EPA AQI and smoke.'
        for prop, title, color, shape, scale, sources in METRICS:
            profile['metrics'].append(dict(id='air-quality-exposure:' + prop.replace('_', '-'), property=prop,
                                           family='air-quality-exposure', title=title, enabled=True,
                                           scale_days=scale, color=color, shape=shape, sources=sources))
        for source, (title, url) in source_definitions.items():
            stats = source_stats[(year, source)]
            profile['sources'].append(dict(id=source, status='included', coverage=title,
                                           available_through=max(stats['dates']) if stats['dates'] else None,
                                           url=url))
        for kind, measured, over in [('monitor', 'pm25_measured_days', 'pm25_concentration_gt35_days'), ('sensor', 'pm25_sensor_measured_days', 'pm25_sensor_gt35_days')]:
            for cell, dates in sorted(coverage[(year, kind)].items()):
                if cell not in features:
                    features[cell] = dict(type='Feature', id=cell, geometry=dict(type='Point', coordinates=center(cell)), properties={'h3': cell})
                high = exceed[(year, kind)].get(cell, set())
                assert high <= dates
                features[cell]['properties'].update({measured: len(dates), over: len(high)})
                for date in sorted(dates):
                    ledger.append(dict(year=year, instrument_class=kind, h3=cell, date=date, any_monitor_daily_mean_above_35=date in high))
        data['features'] = [features[k] for k in sorted(features, key=lambda k: int(k, 16))]
        meta = data['metadata']
        meta.update(snapshot_as_of_utc=profile['snapshot']['as_of_utc'], feature_count=len(features),
                    legacy_source_snapshot_as_of_utc=json.loads(base_path.read_text())['metadata']['snapshot_as_of_utc'],
                    pm25_coverage=[r for r in country_rows if r['year'] == year],
                    pm25_zero_semantics='A zero threshold count is asserted only when the corresponding measured-days property is positive; absent coverage is unknown.',
                    pm25_aggregation='Unique local cell-days with any eligible monitor; threshold is any monitor daily mean >35 ug/m3, not a cell-wide concentration or a national AQI.',
                    pm25_input_files=input_files)
        for metric in profile['metrics']:
            prop = metric['property']
            meta['metric_cell_day_totals'][prop] = sum(f['properties'].get(prop, 0) for f in features.values())
            meta['metric_feature_counts'][prop] = sum(f['properties'].get(prop, 0) > 0 for f in features.values())
        assert all(meta['metric_cell_day_totals'][p] == v for p, v in old_totals.items())
        assert all(all(features[k]['properties'].get(p) == v for p, v in f['properties'].items()) for k, f in old_features.items())
        target = args.output / f'{stem}.geojson'
        target.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n')
        profile['data']['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        (args.output / f'{stem}-profile.json').write_text(json.dumps(profile, ensure_ascii=False, indent=2) + '\n')
        checks.append(dict(year=year, legacy_features_preserved=True, legacy_totals_unchanged=True,
                           output_features=len(features), added_metrics={p: meta['metric_cell_day_totals'][p] for p, *_ in METRICS},
                           sha256=profile['data']['sha256']))
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=list(ledger[0]))
    writer.writeheader()
    writer.writerows(ledger)
    (args.output / 'pm25-cell-days.csv.gz').write_bytes(gzip.compress(text.getvalue().encode(), mtime=0))
    report = dict(status='passed', normalized_inputs=input_files, country_coverage=country_rows, checks=checks,
                  extreme_value_review=dict(threshold_daily_mean_ug_m3=250, station_days=len(extreme_review), action='Retained provider-reported values pending station/operator quality review; 250 is a review trigger, not a validity cutoff or health standard.'),
                  interpretation='Counts describe available monitored days, not annual rates or national exposure. China and Japan coverage differ from selected Indian urban sites. Sensor observations remain separate.')
    (args.output / 'pm25-extreme-value-review.json').write_text(json.dumps(extreme_review, indent=2) + '\n')
    (args.output / 'pm25-enrichment-quality.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
