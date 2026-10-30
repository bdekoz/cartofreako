#!/usr/bin/env python3
"""Independent raw-record, coverage, legacy-conservation and delivery checks."""
from collections import defaultdict, Counter
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
from pathlib import Path
from lxml import etree as E
from PIL import Image

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[1]
RAW = ROOT / 'assets.static/anthropocene/asia-pm25'
DATA = OUT / 'sources/data/anthropocene'
quality = json.loads((DATA / 'pm25-enrichment-quality.json').read_text())
samples = []

# Recalculate individual station-days directly from hourly source records,
# including the Japanese 9999 regression and a high Chinese reported value.
for source, station, date in [('soramame', '04501010', '2026-02-06'),
                              ('cnemc', '3614A', '2025-03-27'),
                              ('openaq', '6956', '2025-12-19')]:
    hours = defaultdict(list)
    if source == 'soramame':
        rows = json.loads(gzip.decompress((RAW / 'raw/soramame-04-202601-202603.json.gz').read_bytes()))
        rows = [r for r in rows if str(r['SKT_CD']) == station and r['SKT_DATE'].replace('/', '-') == date]
        assert any(r['PM2_5'] == '9999' for r in rows)
        for r in rows:
            try:
                v = float(r['PM2_5'])
            except ValueError:
                continue
            if math.isfinite(v) and 0 <= v < 9990:
                hours[int(r['SKT_TIME'])].append(v)
    elif source == 'cnemc':
        with gzip.open(RAW / 'raw/china_sites_20250327.csv.gz', 'rt') as f:
            for r in csv.DictReader(f):
                if r['type'] == 'PM2.5' and r[station]:
                    v = float(r[station])
                    if math.isfinite(v) and v >= 0:
                        hours[int(r['hour'])].append(v)
    else:
        with gzip.open(RAW / 'raw/location-6956-20251219.csv.gz', 'rt') as f:
            for r in csv.DictReader(f):
                t = dt.datetime.fromisoformat(r['datetime'])
                if r['parameter'] == 'pm25' and t.date().isoformat() == date:
                    assert r['units'] == 'µg/m³'
                    v = float(r['value'])
                    if math.isfinite(v) and v >= 0:
                        hours[t.hour].append(v)
    mean = sum(sum(a) / len(a) for a in hours.values()) / len(hours)
    with gzip.open(RAW / f'{source}-station-days.csv.gz', 'rt') as f:
        row = next(r for r in csv.DictReader(f) if r['station_id'] == station and r['date'] == date)
    assert int(row['valid_hours']) == len(hours)
    assert abs(float(row['mean_ug_m3']) - mean) <= 0.00000051
    if source == 'soramame':
        assert len(hours) == 18 and mean < 35
    samples.append(dict(source=source, station=station, date=date, valid_hours=len(hours), mean_ug_m3=mean))

ledger = defaultdict(lambda: [0, 0])
seen = set()
with gzip.open(DATA / 'pm25-cell-days.csv.gz', 'rt') as f:
    for r in csv.DictReader(f):
        key = (int(r['year']), r['instrument_class'], r['h3'], r['date'])
        assert key not in seen
        seen.add(key)
        ledger[key[:3]][0] += 1
        ledger[key[:3]][1] += r['any_monitor_daily_mean_above_35'] == 'True'

for year in [2025, 2026]:
    stem = f'anthropocene-particulate-{year}'
    old = json.loads((ROOT / f'assets.static/anthropocene/{stem}.geojson').read_text())
    path = DATA / f'{stem}.geojson'
    new = json.loads(path.read_text())
    profile = json.loads((DATA / f'{stem}-profile.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == profile['data']['sha256']
    features = {f['id']: f['properties'] for f in new['features']}
    assert len(features) == len(new['features'])
    for f in old['features']:
        assert all(features[f['id']][k] == v for k, v in f['properties'].items())
    for (y, kind, cell), counts in ledger.items():
        if y != year:
            continue
        measured, high = (('pm25_measured_days', 'pm25_concentration_gt35_days') if kind == 'monitor'
                          else ('pm25_sensor_measured_days', 'pm25_sensor_gt35_days'))
        assert [features[cell][measured], features[cell][high]] == counts
        assert 0 <= counts[1] <= counts[0] <= (365 if year == 2025 else 301)
    for country in ['JPN', 'CHN', 'IND']:
        assert any(r['year'] == year and r['country'] == country and r['h3_cells'] > 0 for r in quality['country_coverage'])
    for scope in ['world', 'japan']:
        svg = next((OUT / f'plates/{scope}/svg').glob(stem + '-*.svg'))
        tree = E.parse(str(svg), E.XMLParser(huge_tree=True))
        for metric in ['pm25-measured-days', 'pm25-concentration-gt35-days', 'pm25-sensor-measured-days']:
            assert metric in svg.read_text()
        assert not tree.xpath('//*[local-name()="image"]')
        for suffix in ['pdf', 'png']:
            artifact = OUT / f'plates/{scope}/{suffix}' / (svg.stem + '.' + suffix)
            assert artifact.stat().st_mtime >= svg.stat().st_mtime
        with Image.open(OUT / f'plates/{scope}/png' / (svg.stem + '.png')) as im:
            assert im.size == (13200, 5716)
            im.verify()

assets = []
for p in sorted(RAW.iterdir()):
    if p.is_file():
        assets.append(dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
for row in quality['normalized_inputs']:
    assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256']
for name in ['soramame', 'cnemc', 'openaq']:
    assert not json.loads((RAW / f'{name}-quality.json').read_text())['failures']
(OUT / 'sources/pm25-source-assets.json').write_text(json.dumps(assets, indent=2) + '\n')
report = dict(status='passed', country_year_coverage=quality['country_coverage'],
              independent_raw_day_checks=samples, unique_cell_days=len(seen),
              legacy_feature_values_preserved=True, cell_day_ledger_matches_geojson=True,
              native_metric_layers_present=True, four_plate_triplets_current=True,
              raw_download_failures=0, extreme_value_review=quality['extreme_value_review'])
(OUT / 'sources/particulate-enrichment-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print('Verified PM2.5 raw days, sentinel exclusion, cell-day ledger, source hashes and four plate triplets')
