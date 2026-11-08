#!/usr/bin/env python3
"""Build dated atlas inputs with expanded PM2.5 and separate measured PM10."""
import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('asia', ROOT/'scripts/prepare-asia-pm25.py')
asia = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(asia)


def cell_days(daily):
    """Union observed dates; several stations in one cell never inflate days."""
    measured, high = defaultdict(set), defaultdict(set)
    for row in daily.itertuples():
        if not row.eligible:
            continue
        if not 18 <= row.valid_hours <= 24:
            raise ValueError('Invalid eligible-day hour count')
        cell = asia.h3_cell(row.latitude, row.longitude)
        key = (int(row.date[:4]), cell)
        measured[key].add(row.date)
        if row.mean > 100:
            high[key].add(row.date)
    return measured, high


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--other-asia-inputs', type=Path, default=ROOT/'assets.static/anthropocene/asia-pm25')
    parser.add_argument('--end', default='2026-11-08')
    args = parser.parse_args()
    root = args.root.resolve()
    inputs, output = root/'atlas-inputs', root/'profiles'
    inputs.mkdir(exist_ok=True); output.mkdir(exist_ok=True)
    for name in ['soramame', 'cnemc', 'openaq']:
        source = (root/'openaq' if name == 'openaq' else args.other_asia_inputs)/f'{name}-station-days.csv.gz'
        shutil.copyfile(source, inputs/source.name)
    quality = json.loads((root/'openaq/openaq-quality.json').read_text())
    subprocess.run([sys.executable, str(ROOT/'scripts/prepare-asia-pm25.py'),
                    '--input', str(inputs), '--output', str(output),
                    '--as-of-utc', quality['retrieved_at_utc'], '--data-through', args.end], check=True)
    pm25_quality=json.loads((output/'pm25-enrichment-quality.json').read_text())
    daily = pd.read_csv(root/'observations/openaq-station-days.csv.gz')
    daily = daily[daily.parameter.eq('pm10') & daily.station_type.eq('reference') & (daily.date <= args.end)]
    measured, high = cell_days(daily)
    properties = [
        ('pm10_measured_days', 'India PM10 valid monitor days (at least 18 hours)', '#355c9a', 'ring', 300),
        ('pm10_concentration_gt100_days', 'India monitor daily PM10 >100 µg/m³ days', '#9d642d', 'cross-square', 120),
    ]
    checks, ledger = [], []
    for year in [2025, 2026]:
        stem = f'anthropocene-particulate-{year}'
        data_path, profile_path = output/f'{stem}.geojson', output/f'{stem}-profile.json'
        data, profile = json.loads(data_path.read_text()), json.loads(profile_path.read_text())
        old_totals = data['metadata']['metric_cell_day_totals'].copy()
        old_properties = {f['id']: f['properties'].copy() for f in data['features']}
        features = {f['id']: f for f in data['features']}
        for (row_year, cell), dates in sorted(measured.items()):
            if row_year != year:
                continue
            if cell not in features:
                features[cell] = dict(type='Feature', id=cell,
                    geometry=dict(type='Point', coordinates=asia.center(cell)), properties={'h3': cell})
            threshold_dates = high[(year, cell)]
            assert threshold_dates <= dates
            features[cell]['properties'].update(pm10_measured_days=len(dates),
                                                pm10_concentration_gt100_days=len(threshold_dates))
            ledger.extend(dict(year=year, h3=cell, date=date,
                any_monitor_daily_mean_above_100=date in threshold_dates) for date in sorted(dates))
        for prop, title, color, shape, scale in properties:
            profile['metrics'].append(dict(id='air-quality-exposure:'+prop.replace('_', '-'),
                property=prop, family='air-quality-exposure', title=title, enabled=True,
                scale_days=scale, color=color, shape=shape, sources=['openaq-cpcb']))
            data['metadata']['metric_cell_day_totals'][prop] = sum(f['properties'].get(prop, 0) for f in features.values())
            data['metadata']['metric_feature_counts'][prop] = sum(f['properties'].get(prop, 0) > 0 for f in features.values())
        eligible = daily[daily.eligible & daily.date.str.startswith(str(year))]
        coverage = dict(stations=int(eligible.openaq_id.nunique()), eligible_station_days=len(eligible),
            first_date=eligible.date.min(), last_date=eligible.date.max(),
            unit='µg/m³', minimum_hours=18, threshold_exclusive=100,
            interpretation='Research daily completeness and threshold comparison; not formal NAAQS compliance',
            aggregation='Union of local H3 r4 cell-days; any eligible station over threshold; absent is unknown')
        data['metadata'].update(pm10_coverage=coverage, feature_count=len(features),
            pm10_input=dict(path=str((root/'observations/openaq-station-days.csv.gz').relative_to(ROOT)),
                            sha256=hashlib.sha256((root/'observations/openaq-station-days.csv.gz').read_bytes()).hexdigest()))
        data['features'] = [features[cell] for cell in sorted(features, key=lambda value:int(value,16))]
        assert all(data['metadata']['metric_cell_day_totals'][key] == value for key,value in old_totals.items())
        assert all(all(features[cell]['properties'].get(key)==value for key,value in props.items())
                   for cell,props in old_properties.items())
        profile['thresholds'].update(pm10_minimum_valid_hours_per_day=18,
                                    pm10_concentration_threshold_exclusive_ug_m3=100)
        # Plain wording also avoids the legacy SVG text path double-escaping >.
        for metric in profile['metrics']:
            metric['title']=metric['title'].replace('>', 'above ')
        profile['description'] += ' Selected India PM10 coverage and >100 µg/m³ days have separate legends; historical modeled fields are separate files.'
        data_path.write_text(json.dumps(data, ensure_ascii=False, separators=(',',':'), allow_nan=False)+'\n')
        profile['data']['sha256'] = hashlib.sha256(data_path.read_bytes()).hexdigest()
        profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
        stage_check=next(check for check in pm25_quality['checks'] if check['year']==year)
        stage_check['pm25_stage_sha256']=stage_check['sha256']
        stage_check['sha256']=profile['data']['sha256']
        stage_check['output_features']=len(features)
        checks.append(dict(year=year, existing_metrics_preserved=True, pm10_coverage=coverage,
            pm10_cell_days={prop:data['metadata']['metric_cell_day_totals'][prop] for prop,*_ in properties},
            sha256=profile['data']['sha256']))
    pd.DataFrame(ledger).to_csv(output/'pm10-cell-days.csv.gz', index=False,
                                compression={'method':'gzip','mtime':0})
    (output/'india-profile-quality.json').write_text(json.dumps(dict(status='passed', checks=checks),indent=2)+'\n')
    pm25_quality['postprocessed_with_pm10']=True
    pm25_quality['digest_semantics']='sha256 pins the final PM2.5/PM10 GeoJSON; pm25_stage_sha256 records the intermediate PM2.5-only build'
    (output/'pm25-enrichment-quality.json').write_text(json.dumps(pm25_quality,indent=2)+'\n')
    print('Built expanded India profiles:',output)


if __name__ == '__main__':
    main()
