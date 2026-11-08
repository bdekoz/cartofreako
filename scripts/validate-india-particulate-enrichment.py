#!/usr/bin/env python3
"""Validate scientific invariants and write a compact India delivery receipt."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args();root=args.root.resolve()
    inventory=json.loads((root/'inventory.json').read_text())
    canonical=[s['canonical_id'] for s in inventory['openaq_locations']]
    assert len(canonical)==len(set(canonical))
    national=[s['station_id'] for s in inventory['national_stations']]
    assert len(national)==len(set(national))
    daily=pd.read_csv(root/'observations/openaq-station-days.csv.gz')
    assert not daily.duplicated(['canonical_id','parameter','date']).any()
    assert daily.date.between('2025-01-01','2026-11-08').all()
    assert daily.valid_hours.between(1,24).all()
    assert (daily.eligible==(daily.valid_hours>=18)).all()
    assert np.isfinite(daily['mean']).all()
    assert (daily[daily.parameter.isin(['pm25','pm10'])]['mean']>=0).all()
    daily['year']=daily.date.str[:4]
    coverage=daily[daily.eligible].groupby(['year','station_type','parameter']).agg(
        stations=('canonical_id','nunique'),eligible_station_days=('date','size'),
        first=('date','min'),last=('date','max')).reset_index()
    fetch=pd.read_csv(root/'openaq/openaq-station-days.csv.gz')
    compare=fetch.merge(daily[daily.parameter.eq('pm25')],left_on=['station_id','date'],
                       right_on=['openaq_id','date'],validate='one_to_one',suffixes=('_fetch','_multi'))
    assert len(compare)==len(fetch)==len(daily[daily.parameter.eq('pm25')])
    assert (compare.valid_hours_fetch==compare.valid_hours_multi).all()
    assert (compare.eligible_fetch==compare.eligible_multi).all()
    difference=float((compare.mean_ug_m3-compare['mean']).abs().max())
    assert difference<0.0001  # CSV display precision differs between adapters.
    assert ((compare.mean_ug_m3>35)==(compare['mean']>35)).all()
    hourly_count=0
    for part in pd.read_csv(root/'observations/openaq-instrument-hours.csv.gz',chunksize=200000):
        assert not part.duplicated(['canonical_id','sensor_id','parameter','hour_local']).any()
        assert part.hour_local.str.endswith('+05:30').all()
        assert (pd.to_datetime(part.hour_local,utc=True)==pd.to_datetime(part.hour_utc,utc=True)).all()
        assert np.isfinite(part.value).all()
        hourly_count+=len(part)
    paired_count=negative_count=zero_denominator=0
    for part in pd.read_csv(root/'observations/openaq-paired-hours.csv.gz',chunksize=200000):
        assert np.allclose(part.value_pm10-part.value_pm25,part.coarse_ug_m3,atol=0.0001)
        assert not part.duplicated(['canonical_id','hour_local']).any()
        assert part.loc[part.coarse_ug_m3<0,'quality_flag'].notna().all()
        assert part.loc[part.value_pm10.eq(0),'pm25_pm10_ratio'].isna().all()
        paired_count+=len(part);negative_count+=int((part.coarse_ug_m3<0).sum())
        zero_denominator+=int(part.value_pm10.eq(0).sum())
    matched=pd.read_csv(root/'observations/matched-station-days-2025-2026.csv.gz')
    assert (matched.date_2025.str[5:]==matched.date_2026.str[5:]).all()
    assert not matched.duplicated(['canonical_id','parameter','date_2026']).any()
    assert matched[['valid_hours_2025','valid_hours_2026']].ge(18).all().all()
    xkdr=pd.read_csv(root/'observations/xkdr-2024-station-days.csv.gz')
    assert not xkdr.duplicated(['canonical_id','parameter','date']).any()
    assert xkdr.date.between('2024-01-01','2024-12-31').all()
    assert (xkdr.eligible==(xkdr.valid_hours>=18)).all()
    assert xkdr.valid_hours.between(1,24).all()
    assert np.isfinite(xkdr['mean']).all() and (xkdr['mean']>=0).all()
    xcoverage=xkdr[xkdr.eligible].groupby('parameter').agg(stations=('canonical_id','nunique'),
        eligible_station_days=('date','size'),first=('date','min'),last=('date','max')).reset_index()
    for filename,keys,expected in [
        ('station-month-coverage.csv.gz',['canonical_id','parameter','year_month'],int(daily.eligible.sum())),
        ('xkdr-2024-station-month-coverage.csv.gz',['station_id','parameter','year_month'],int(xkdr.eligible.sum()))]:
        matrix=pd.read_csv(root/'observations'/filename)
        assert not matrix.duplicated(keys).any()
        assert matrix.eligible_days.sum()==expected
        assert matrix.eligible_calendar_fraction.between(0,1).all()
        assert matrix.eligible_days.le(matrix.observed_days).all()
    fire=pd.read_csv(root/'context/firms-detections.csv.gz')
    assert fire.longitude.between(72,79).all() and fire.latitude.between(27,33).all()
    assert (fire.local_date<='2026-11-08').all()
    assert not fire.duplicated(['satellite','timestamp_utc','latitude','longitude']).any()
    fire_summary=fire[fire.primary_confidence].groupby('satellite').agg(detections=('latitude','size'),
        first=('local_date','min'),last=('local_date','max')).reset_index()
    dss=pd.read_csv(root/'context/iitm-model-contributions.csv.gz')
    assert dss.percent_total_pm25.between(0,100).all()
    assert not dss.renormalized.any()
    assert dss.issue_time_utc.isna().all()
    forecasts=dss[dss.evidence_kind.eq('published_model_forecast')]
    assert forecasts.composition_quality_flag.notna().all()
    model=np.load(root/'model/longpmind-2022-grid.npz')
    for key in ['pm25','pm10','pm25_november','pm10_november']:
        assert model[key].shape==(len(model['lat']),len(model['lon']))
        assert (model[key][np.isfinite(model[key])]>=0).all()
    profile_checks=[]
    pm25_quality=json.loads((root/'profiles/pm25-enrichment-quality.json').read_text())
    for year in [2025,2026]:
        data_path=root/f'profiles/anthropocene-particulate-{year}.geojson'
        profile=json.loads((root/f'profiles/anthropocene-particulate-{year}-profile.json').read_text())
        data=json.loads(data_path.read_text())
        assert sha(data_path)==profile['data']['sha256']
        assert next(c['sha256'] for c in pm25_quality['checks'] if c['year']==year)==profile['data']['sha256']
        for metric in profile['metrics']:
            key=metric['property'];values=[f['properties'].get(key,0) for f in data['features']]
            assert sum(values)==data['metadata']['metric_cell_day_totals'][key]
            assert sum(v>0 for v in values)==data['metadata']['metric_feature_counts'][key]
        for feature in data['features']:
            p=feature['properties']
            assert p.get('pm10_concentration_gt100_days',0)<=p.get('pm10_measured_days',0)
            assert p.get('pm25_concentration_gt35_days',0)<=p.get('pm25_measured_days',0)
        profile_checks.append(dict(year=year,sha256=profile['data']['sha256'],features=len(data['features'])))
    artifacts=[]
    for directory in ['observations','context','model','profiles','figures','atlas-preview']:
        for path in sorted((root/directory).glob('*')):
            if path.is_file():artifacts.append(dict(file=str(path.relative_to(root)),bytes=path.stat().st_size,sha256=sha(path)))
    report=dict(status='passed',requested_local_cutoff='2026-11-08',national_inventory_stations=len(national),
        selected_locations=len(canonical),crosswalk=inventory['match_counts'],
        openaq_coverage=coverage.to_dict('records'),openaq_instrument_hours=hourly_count,
        independent_pm25_normalization=dict(rows=len(compare),eligibility_and_hours_agree=True,
            maximum_serialized_mean_difference_ug_m3=difference,threshold_classifications_agree=True),
        paired_hours=paired_count,negative_coarse_hours=negative_count,zero_pm10_denominator_hours=zero_denominator,
        matched_station_days_by_parameter=matched.groupby('parameter').size().to_dict(),
        xkdr_2024_coverage=xcoverage.to_dict('records'),
        xkdr_missing_coordinate_stations=int(xkdr[xkdr.latitude.isna()].station_id.nunique()),
        fire_coverage=fire_summary.to_dict('records'),
        iitm_forecast_category_sums=forecasts.groupby('valid_date').percent_total_pm25.sum().to_dict(),
        model=json.loads((root/'model/model-manifest.json').read_text()),profile_checks=profile_checks,
        artifacts=artifacts,
        limits=['National 2025/2026 XKDR backfill requires a full-access key',
                'ERA5 not acquired; no CDS credentials configured',
                'FIRMS context is a rolling feed with partial boundary dates',
                'IITM issue/version metadata unavailable and forecast composition does not close',
                'LongPMInd independent held-out validation not established'])
    (root/'validation.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['artifacts','model','openaq_coverage']},indent=2))


if __name__=='__main__':main()
