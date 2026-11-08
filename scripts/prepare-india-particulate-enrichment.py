#!/usr/bin/env python3
"""Prepare source-separated India particulate observations and contextual layers.

Inputs are pinned local OpenAQ CSVs, XKDR Parquet, FIRMS CSVs, IITM HTML and
LongPMInd monthly NetCDF archives. No network requests occur during preparation.
"""
import argparse
import calendar
from collections import Counter
import datetime as dt
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import zipfile

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.io import netcdf_file

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
PARAMETERS = {'pm25', 'pm10', 'wind_speed', 'wind_direction', 'temperature', 'relativehumidity'}
UNITS = {'pm25': 'µg/m³', 'pm10': 'µg/m³', 'wind_speed': 'm/s',
         'wind_direction': 'deg', 'temperature': '°C', 'relativehumidity': '%'}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def save_csv(path, rows):
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(filename=str(path), mode='wb', mtime=0) as binary:
        with io.TextIOWrapper(binary, encoding='utf-8', newline='') as stream:
            frame.to_csv(stream, index=False, float_format='%.8g')


def normalize_value(parameter, unit, raw):
    """Return a normalized value plus a reason when it is ineligible."""
    unit = str(unit).replace('μ', 'µ')
    accepted = {'pm25': {'µg/m³', 'µg/m3', 'ug/m3'},
                'pm10': {'µg/m³', 'µg/m3', 'ug/m3'},
                'wind_speed': {'m/s'}, 'wind_direction': {'deg'},
                'temperature': {'c', '°C'}, 'relativehumidity': {'%'}}
    if unit not in accepted[parameter]:
        return math.nan, 'unsupported_unit'
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return math.nan, 'nonnumeric'
    if not math.isfinite(value):
        return math.nan, 'nonfinite'
    if parameter != 'temperature' and value < 0:
        return math.nan, 'negative'
    if parameter == 'wind_direction' and value > 360:
        return math.nan, 'direction_out_of_range'
    if parameter == 'relativehumidity' and value > 100:
        return math.nan, 'humidity_out_of_range'
    return value, ''


def circular_mean(values):
    radians = np.deg2rad(values)
    x, y = np.cos(radians).mean(), np.sin(radians).mean()
    if math.hypot(x, y) < 1e-8:
        return math.nan
    return float(np.rad2deg(math.atan2(y, x)) % 360)


def distance_km(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    value = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6371 * 2 * math.asin(min(1, math.sqrt(value)))


def name_tokens(name):
    return set(re.findall(r'[a-z0-9]+', name.lower().replace('new delhi', 'delhi').split(' - ')[0]))


def match_station(name, provider, lat, lon, stations):
    """Only accept one close, name-compatible upstream identity; retain ambiguity."""
    candidates = []
    for row in stations:
        if row.get('latitude') is None or row.get('longitude') is None:
            continue
        if (provider == 'CPCB') != (row['source'] == 'cpcb_caaqm'):
            continue
        distance = distance_km((lat, lon), (row['latitude'], row['longitude']))
        a, b = name_tokens(name), name_tokens(row['station_name'])
        similarity = len(a & b) / len(a | b) if a | b else 0
        if distance <= 0.5 and (similarity >= 0.5 or provider == 'AirNow'):
            candidates.append((distance, row))
    if len(candidates) == 1:
        return candidates[0][1], 'coordinate_and_name_match'
    return None, 'ambiguous_match' if candidates else 'unmatched'


def explorer_metadata(path, location):
    text = path.read_text()
    if not re.search(r'code:"IN"', text):
        raise ValueError(f'India country metadata missing: {path}')
    names = re.search(r'\{id:' + str(location) + r',name:("(?:\\.|[^"\\])*")', text)
    coords = re.search(r'coordinates:(?:\$R\[\d+\]=)?\{latitude:([\d.eE+-]+),longitude:([\d.eE+-]+)', text)
    if not names or not coords:
        raise ValueError(f'Explorer metadata schema changed: {path}')
    return json.loads(names[1]), float(coords[1]), float(coords[2])


def make_inventory(root, locations):
    document = json.loads((root/'raw/discovery/xkdr-stations.txt').read_text())
    if document['meta']['truncated']:
        raise ValueError('Incomplete national station inventory')
    national = document['data']
    records = []
    for row in locations:
        path = root/'openaq/raw'/f"openaq-location-{row['id']}.html"
        name, lat, lon = explorer_metadata(path, row['id'])
        match, status = match_station(name, row['provider'], lat, lon, national) if row['kind'] == 'reference' else (None, 'separate_air_sensor')
        records.append(dict(row, official_name=name, latitude=lat, longitude=lon,
                            xkdr_station_id=match['station_id'] if match else '',
                            canonical_id=(match['source']+':'+match['station_id']) if match else 'openaq:'+str(row['id']),
                            state=match['state_name'] if match else '',
                            city=match['city_name'] if match else '', match_status=status,
                            coordinates_status='current metadata; historical relocations not independently verified',
                            metadata_sha256=digest(path)))
    canonical = [r['canonical_id'] for r in records]
    if len(canonical) != len(set(canonical)):
        raise ValueError('Multiple selected OpenAQ locations map to the same upstream station; reconcile before aggregation')
    save_json(root/'inventory.json', dict(schema_version=1, requested_as_of='2026-11-08',
              national_inventory_source='XKDR CPCB/AirNow metadata', national_archive_stations=len(national),
              national_inventory_is_not_current_observation_coverage=True,
              national_stations=national, openaq_locations=records,
              match_counts=dict(Counter(r['match_status'] for r in records))))
    return records, national


def hourly_and_daily(raw):
    """One pollutant/instrument/hour, then deterministic station-day selection."""
    frame = raw.copy()
    keys = ['sensor_id', 'parameter', 'datetime_local']
    frame['conflict'] = frame.groupby(keys, dropna=False)['value'].transform('nunique') > 1
    frame['conflict'] |= frame.groupby(keys, dropna=False)['quality_flag'].transform('nunique') > 1
    for col in ['latitude', 'longitude']:
        frame['conflict'] |= frame.groupby(keys, dropna=False)[col].transform('nunique') > 1
    frame.loc[frame['conflict'], 'quality_flag'] = 'conflicting_duplicate'
    frame.loc[frame['conflict'], 'value'] = np.nan
    frame = frame.drop_duplicates(keys, keep='first')
    valid = frame[frame['quality_flag'].eq('') & frame['value'].notna()].copy()
    valid['hour_local'] = valid['datetime_local'].str[:13] + ':00:00+05:30'
    grouped = valid.groupby(['sensor_id', 'parameter', 'hour_local'], sort=True)
    hour = grouped.agg(value=('value', 'mean'), samples=('value', 'size'),
                       latitude=('latitude', 'first'), longitude=('longitude', 'first'),
                       latitude_count=('latitude', 'nunique'), longitude_count=('longitude', 'nunique')).reset_index()
    hour = hour[(hour.latitude_count == 1) & (hour.longitude_count == 1)].copy()
    direction = valid[valid.parameter.eq('wind_direction')]
    if not direction.empty:
        circular = direction.groupby(['sensor_id', 'parameter', 'hour_local'])['value'].apply(circular_mean)
        mask = hour.parameter.eq('wind_direction')
        hour.loc[mask, 'value'] = [circular.loc[tuple(row)] for row in hour.loc[mask, ['sensor_id', 'parameter', 'hour_local']].itertuples(index=False, name=None)]
    hour = hour[hour.value.notna()].copy()
    hour['date'] = hour.hour_local.str[:10]
    hour['hour_utc'] = pd.to_datetime(hour.hour_local, utc=True).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    daily = hour.groupby(['sensor_id', 'parameter', 'date']).agg(
        valid_hours=('hour_local', 'nunique'), mean=('value', 'mean'), maximum_hourly=('value', 'max'),
        latitude=('latitude', 'first'), longitude=('longitude', 'first'),
        latitude_count=('latitude', 'nunique'), longitude_count=('longitude', 'nunique')).reset_index()
    daily = daily[(daily.latitude_count == 1) & (daily.longitude_count == 1)].copy()
    daily = daily.sort_values(['parameter', 'date', 'valid_hours', 'sensor_id'], ascending=[True, True, False, True])
    daily = daily.drop_duplicates(['parameter', 'date'])
    daily['eligible'] = daily.valid_hours >= 18
    direction = hour[hour.parameter.eq('wind_direction')]
    if not direction.empty:
        circular = direction.groupby(['sensor_id', 'parameter', 'date'])['value'].apply(circular_mean)
        mask = daily.parameter.eq('wind_direction')
        daily.loc[mask, 'mean'] = [circular.loc[tuple(row)] for row in daily.loc[mask, ['sensor_id', 'parameter', 'date']].itertuples(index=False, name=None)]
    selected = daily[['sensor_id', 'parameter', 'date']].assign(selected=True)
    hour = hour.merge(selected, how='left', on=['sensor_id', 'parameter', 'date'], validate='many_to_one')
    hour['selected'] = hour['selected'].eq(True)
    hour['unit'] = hour.parameter.map(UNITS)
    return frame, hour, daily


def paired_hours(hour):
    selected = hour[hour.selected]
    a = selected[selected.parameter.eq('pm25')]
    b = selected[selected.parameter.eq('pm10')]
    pair = a.merge(b, on=['hour_local', 'hour_utc', 'date'], suffixes=('_pm25', '_pm10'), validate='one_to_one')
    same = np.isclose(pair.latitude_pm25, pair.latitude_pm10, atol=1e-6, rtol=0) & np.isclose(pair.longitude_pm25, pair.longitude_pm10, atol=1e-6, rtol=0)
    pair = pair[same].copy()
    pair['coarse_ug_m3'] = pair.value_pm10 - pair.value_pm25
    pair['pm25_pm10_ratio'] = pair.value_pm25 / pair.value_pm10.replace(0, np.nan)
    pair['quality_flag'] = np.where(pair.coarse_ug_m3 < 0, 'pm25_exceeds_pm10', '')
    pair.loc[pair.value_pm10.eq(0), 'quality_flag'] = 'zero_pm10_denominator'
    return pair


def episodes(daily):
    result = []
    thresholds = {'pm25': [('atlas_35', 35), ('who_2021_24h', 15), ('india_naaqs_24h', 60)],
                  'pm10': [('who_2021_24h', 45), ('india_naaqs_24h', 100)]}
    for (station, parameter), group in daily.groupby(['canonical_id', 'parameter']):
        if parameter not in thresholds:
            continue
        eligible = group[group.eligible].sort_values('date')
        known = set(eligible.date)
        for benchmark, threshold in thresholds[parameter]:
            high = eligible[eligible['mean'] > threshold]
            run = []
            for row in high.to_dict('records') + [None]:
                if run and (row is None or (dt.date.fromisoformat(row['date'])-dt.date.fromisoformat(run[-1]['date'])).days != 1):
                    start, end = run[0]['date'], run[-1]['date']
                    result.append(dict(canonical_id=station, parameter=parameter, benchmark=benchmark,
                        threshold_ug_m3=threshold, start=start, end=end, observed_days=len(run),
                        peak_daily_mean=max(r['mean'] for r in run),
                        left_censored=(dt.date.fromisoformat(start)-dt.timedelta(days=1)).isoformat() not in known,
                        right_censored=(dt.date.fromisoformat(end)+dt.timedelta(days=1)).isoformat() not in known))
                    run = []
                if row:
                    run.append(row)
    return result


def prepare_openaq(root, inventory, end):
    output = root/'observations'; output.mkdir(parents=True, exist_ok=True)
    all_daily, all_pairs, coverage, receipts = [], [], [], []
    raw_out = gzip.open(output/'openaq-normalized-records.csv.gz', 'wt')
    hourly_out = gzip.open(output/'openaq-instrument-hours.csv.gz', 'wt')
    pair_out = gzip.open(output/'openaq-paired-hours.csv.gz', 'wt')
    headers = [True, True, True]
    qa = Counter()
    try:
        for station in inventory:
            records = []
            for path in sorted((root/'openaq/raw').glob(f"location-{station['id']}-*.csv.gz")):
                frame = pd.read_csv(path, dtype={'value': str, 'datetime': str}, keep_default_na=False)
                frame = frame[frame.parameter.isin(PARAMETERS)].copy()
                frame = frame[(frame.datetime.str[:10] >= '2025-01-01') & (frame.datetime.str[:10] <= end)]
                if frame.empty:
                    continue
                if not frame.datetime.str.endswith('+05:30').all():
                    raise ValueError(f'Unexpected timezone in {path}')
                frame['source_file'] = path.name
                records.append(frame)
                receipts.append({'file':str(path.relative_to(root)), 'sha256':digest(path)})
            if not records:
                coverage.append(dict(openaq_id=station['id'], status='no_records'))
                continue
            frame = pd.concat(records, ignore_index=True).rename(columns={'value':'raw_value','units':'raw_unit','sensors_id':'sensor_id','datetime':'datetime_local','lat':'latitude','lon':'longitude'})
            normalized = [normalize_value(p, u, v) for p,u,v in zip(frame.parameter,frame.raw_unit,frame.raw_value)]
            frame['value'] = [v for v,_ in normalized]
            frame['quality_flag'] = [f for _,f in normalized]
            bad_coords = ~np.isfinite(frame.latitude) | ~np.isfinite(frame.longitude) | ~frame.latitude.between(6,37) | ~frame.longitude.between(67,98)
            frame.loc[bad_coords, 'quality_flag'] = 'invalid_coordinates'
            frame.loc[bad_coords, 'value'] = np.nan
            frame['unit'] = frame.parameter.map(UNITS)
            frame['canonical_id'] = station['canonical_id']
            frame['datetime_utc'] = pd.to_datetime(frame.datetime_local, utc=True).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            raw, hour, daily = hourly_and_daily(frame)
            pair = paired_hours(hour)
            for target in [hour, daily, pair]:
                target['canonical_id'] = station['canonical_id']
                target['openaq_id'] = station['id']
                target['station_name'] = station['official_name']
                target['station_type'] = station['kind']
                target['source'] = 'openaq-' + station['provider'].lower()
                target['state'] = station['state']
            for i,(target,stream) in enumerate([(raw,raw_out),(hour,hourly_out),(pair,pair_out)]):
                if not target.empty:
                    target.to_csv(stream,index=False,header=headers[i],float_format='%.8g'); headers[i]=False
            qa.update(raw.quality_flag.value_counts().to_dict())
            qa['identical_or_conflicting_duplicate_rows_removed'] += len(frame)-len(raw)
            all_daily.append(daily)
            if not pair.empty:
                aggregate = pair.groupby('date').agg(paired_hours=('hour_local','nunique'),
                    pm25_mean=('value_pm25','mean'),pm10_mean=('value_pm10','mean'),
                    negative_coarse_hours=('coarse_ug_m3',lambda s:int((s<0).sum()))).reset_index()
                aggregate['canonical_id'] = station['canonical_id']
                aggregate['eligible'] = aggregate.paired_hours >= 18
                aggregate['coarse_mean_ug_m3'] = aggregate.pm10_mean-aggregate.pm25_mean
                aggregate['pm25_pm10_ratio'] = aggregate.pm25_mean/aggregate.pm10_mean.replace(0,np.nan)
                all_pairs.append(aggregate)
            print(f"Prepared OpenAQ {station['id']}: {len(hour)} instrument-hours",flush=True)
    finally:
        raw_out.close(); hourly_out.close(); pair_out.close()
    daily = pd.concat(all_daily, ignore_index=True)
    daily['year_month'] = daily.date.str[:7]
    daily['unit'] = daily.parameter.map(UNITS)
    save_csv(output/'openaq-station-days.csv.gz', daily)
    save_csv(output/'openaq-paired-days.csv.gz', pd.concat(all_pairs,ignore_index=True))
    save_csv(output/'episodes.csv.gz', episodes(daily))
    monthly = daily.groupby(['canonical_id','openaq_id','state','station_type','parameter','year_month']).agg(
        observed_days=('date','nunique'),eligible_days=('eligible','sum'),valid_hours=('valid_hours','sum')).reset_index()
    monthly['expected_days'] = monthly.year_month.map(lambda s: min(calendar.monthrange(int(s[:4]),int(s[5:]))[1], int(end[-2:])) if s == end[:7] else calendar.monthrange(int(s[:4]),int(s[5:]))[1])
    monthly['eligible_fraction'] = monthly.eligible_days/monthly.expected_days
    save_csv(output/'station-month-coverage.csv.gz',monthly)
    # Fixed station/date cohort, equal calendar windows, separate pollutants.
    matched=[]
    for parameter in ['pm25','pm10']:
        g=daily[daily.eligible & daily.parameter.eq(parameter) & daily.station_type.eq('reference')].copy()
        g['month_day']=g.date.str[5:];g['year']=g.date.str[:4]
        pair=g[g.year.eq('2025')].merge(g[g.year.eq('2026')],on=['canonical_id','month_day'],suffixes=('_2025','_2026'),validate='one_to_one')
        pair['parameter']=parameter
        matched.append(pair[['canonical_id','parameter','date_2025','date_2026','valid_hours_2025','valid_hours_2026','mean_2025','mean_2026']])
    save_csv(output/'matched-station-days-2025-2026.csv.gz',pd.concat(matched,ignore_index=True))
    save_json(output/'openaq-preparation-quality.json',dict(quality_flags=dict(qa),
        raw_files=receipts, station_days=len(daily), station_count=int(daily.openaq_id.nunique()),
        interpretation='Provisional provider observations; 18-hour daily research completeness, not regulatory certification'))
    return daily


def prepare_xkdr(root, stations):
    inventory={r['station_id']:r for r in stations}
    daily_rows=[];quality=Counter();inputs=[]
    out=root/'observations';out.mkdir(exist_ok=True)
    with gzip.open(out/'xkdr-2024-hours.csv.gz','wt') as stream:
        first=True
        for path in sorted((root/'raw/xkdr').glob('2024-*.parquet')):
            frame=pq.read_table(path,filters=[('parameter_name','in',['PM2.5','PM10'])]).to_pandas()
            frame['parameter']=frame.parameter_name.map({'PM2.5':'pm25','PM10':'pm10'})
            normalized=[normalize_value(p,u,v) for p,u,v in zip(frame.parameter,frame.unit,frame.value)]
            frame['raw_value']=frame.value;frame['value']=[v for v,_ in normalized]
            frame['quality_flag']=[f for _,f in normalized]
            keys=['station_id','parameter','collected_at']
            conflicts=frame.groupby(keys)['value'].transform('nunique')>1
            conflicts |= frame.groupby(keys)['quality_flag'].transform('nunique')>1
            frame.loc[conflicts,'quality_flag']='conflicting_duplicate';frame.loc[conflicts,'value']=np.nan
            quality['duplicate_rows_removed']+=int(frame.duplicated(keys).sum())
            frame=frame.drop_duplicates(keys)
            quality.update(frame.quality_flag.value_counts().to_dict())
            frame['canonical_id']=frame.source+':'+frame.station_id
            frame['hour_local']=pd.to_datetime(frame.collected_at).dt.floor('h')
            hour=frame[frame.quality_flag.eq('')].groupby(['station_id','canonical_id','parameter','hour_local']).agg(value=('value','mean')).reset_index()
            hour['date']=hour.hour_local.dt.strftime('%Y-%m-%d')
            hour['hour_utc']=hour.hour_local.dt.tz_localize('Asia/Kolkata').dt.tz_convert('UTC').dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            hour['hour_local']=hour.hour_local.dt.strftime('%Y-%m-%dT%H:%M:%S+05:30')
            hour['unit']=hour.parameter.map(UNITS)
            hour.to_csv(stream,index=False,header=first,float_format='%.8g');first=False
            daily=hour.groupby(['station_id','canonical_id','parameter','date']).agg(valid_hours=('hour_local','nunique'),mean=('value','mean'),maximum_hourly=('value','max')).reset_index()
            daily['eligible']=daily.valid_hours>=18
            for col,source_col in [('latitude','latitude'),('longitude','longitude'),('state','state_name'),('city','city_name')]:
                daily[col]=daily.station_id.map(lambda v:inventory.get(v,{}).get(source_col))
            daily_rows.append(daily)
            inputs.append(dict(file=str(path.relative_to(root)),sha256=digest(path),raw_particulate_records=len(frame)))
            print(f'Prepared XKDR {path.name}: {len(hour)} hours',flush=True)
    daily=pd.concat(daily_rows,ignore_index=True)
    save_csv(out/'xkdr-2024-station-days.csv.gz',daily)
    matrix=daily.groupby(['station_id','state','parameter'],dropna=False).agg(observed_days=('date','nunique'),eligible_days=('eligible','sum')).reset_index()
    save_csv(out/'xkdr-2024-station-coverage.csv.gz',matrix)
    save_json(out/'xkdr-quality.json',dict(year=2024,station_count=int(daily.station_id.nunique()),station_days=len(daily),
        eligible_station_days=int(daily.eligible.sum()),missing_coordinate_station_days=int(daily.latitude.isna().sum()),
        quality_flags=dict(quality),inputs=inputs,license='CC BY 4.0; credit XKDR, CPCB and US Department of State/AirNow',
        overlap_policy='2024 backfill is separate from OpenAQ 2025/2026; never union mirrors as extra stations',
        access_limit='No full-access XKDR key configured; 2025/2026 national backfill not acquired'))
    return daily


def coverage_tables(root, inventory, national, end):
    """Include empty months explicitly as zero coverage, never zero pollution."""
    output=root/'observations'
    daily=pd.read_csv(output/'openaq-station-days.csv.gz')
    months=pd.period_range('2025-01',end[:7],freq='M').astype(str)
    combinations=daily[['canonical_id','parameter']].drop_duplicates()
    grid=combinations.merge(pd.DataFrame({'year_month':months}),how='cross')
    grouped=daily.groupby(['canonical_id','parameter','year_month']).agg(
        observed_days=('date','nunique'),eligible_days=('eligible','sum'),valid_hours=('valid_hours','sum')).reset_index()
    monthly=grid.merge(grouped,how='left',on=['canonical_id','parameter','year_month'],validate='one_to_one')
    counts=['observed_days','eligible_days','valid_hours']
    monthly[counts]=monthly[counts].fillna(0).astype(int)
    lookup=pd.DataFrame(inventory)[['canonical_id','id','state','kind']].rename(columns={'id':'openaq_id','kind':'station_type'})
    monthly=monthly.merge(lookup,on='canonical_id',validate='many_to_one')
    monthly['calendar_days_in_requested_window']=monthly.year_month.map(lambda s:
        int(end[-2:]) if s==end[:7] else calendar.monthrange(int(s[:4]),int(s[5:]))[1])
    monthly['eligible_calendar_fraction']=monthly.eligible_days/monthly.calendar_days_in_requested_window
    save_csv(output/'station-month-coverage.csv.gz',monthly)
    xdaily=pd.read_csv(output/'xkdr-2024-station-days.csv.gz')
    xdaily['year_month']=xdaily.date.str[:7]
    xgrid=pd.DataFrame(national)[['station_id','state_name']].rename(columns={'state_name':'state'})
    xgrid=xgrid.merge(pd.DataFrame({'parameter':['pm25','pm10']}),how='cross').merge(
        pd.DataFrame({'year_month':pd.period_range('2024-01','2024-12',freq='M').astype(str)}),how='cross')
    grouped=xdaily.groupby(['station_id','parameter','year_month']).agg(
        observed_days=('date','nunique'),eligible_days=('eligible','sum'),valid_hours=('valid_hours','sum')).reset_index()
    xmonthly=xgrid.merge(grouped,how='left',on=['station_id','parameter','year_month'],validate='one_to_one')
    xmonthly[counts]=xmonthly[counts].fillna(0).astype(int)
    xmonthly['calendar_days_in_requested_window']=xmonthly.year_month.map(lambda s:calendar.monthrange(2024,int(s[5:]))[1])
    xmonthly['eligible_calendar_fraction']=xmonthly.eligible_days/xmonthly.calendar_days_in_requested_window
    save_csv(output/'xkdr-2024-station-month-coverage.csv.gz',xmonthly)
    state=xmonthly.groupby(['state','parameter','year_month'],dropna=False).agg(
        archive_inventory_stations=('station_id','nunique'),
        stations_with_eligible_days=('eligible_days',lambda s:int((s>0).sum())),
        eligible_station_days=('eligible_days','sum')).reset_index()
    save_csv(output/'xkdr-2024-state-month-coverage.csv.gz',state)
    save_json(output/'coverage-semantics.json',dict(
        zero='Zero counts mean no records or eligible observations in the ingested snapshot; never zero concentration',
        denominator='Calendar days in the requested window, not independently verified station operational uptime',
        xkdr_inventory='Archive-wide 558 stations; matrix inclusion does not imply activity during 2024',
        openaq_parameters='Pollutants/weather fields observed at least once for each selected location; unreported parameters are not imputed'))


def parse_dss(html):
    records=[]
    for variable,kind in [('data','published_model_forecast'),('data2','published_model_daily_history')]:
        section=re.search(r'const '+variable+r'\s*=\s*\{(.*?)\n\s*\};',html,re.S)
        if not section:
            raise ValueError(f'IITM chart {variable} missing; schema changed')
        labels=json.loads(re.search(r'labels\s*:\s*(\[.*?\])',section[1],re.S)[1])
        series=re.findall(r"label:\s*'([^']+)'.*?data:\s*(\[.*?\])",section[1],re.S)
        for label,values in series:
            values=json.loads(values)
            if len(values)!=len(labels):raise ValueError('IITM label/value mismatch')
            for stamp,value in zip(labels,values):
                if not math.isfinite(value) or not 0<=value<=100:raise ValueError('Invalid IITM percent')
                records.append(dict(valid_date=stamp[:10],published_time_label=stamp,source_category=label,
                    percent_total_pm25=value,evidence_kind=kind,issue_time_utc='',forecast_lead_hours='',
                    model_version='',time_metadata_status='not supplied in captured chart',
                    receptor='Delhi',unit='percent of modeled ambient PM2.5'))
    forecast=pd.DataFrame(records).query("evidence_kind == 'published_model_forecast'")
    totals=forecast.groupby('valid_date').percent_total_pm25.sum().to_dict()
    for row in records:
        total=totals.get(row['valid_date']) if row['evidence_kind']=='published_model_forecast' else None
        row['published_category_sum_percent']=total
        row['composition_quality_flag']='published_categories_do_not_sum_to_100' if total is not None and abs(total-100)>0.1 else ''
        # Preserve the publisher's numbers. A source inconsistency is not a
        # reason to rescale them into an apparently closed composition.
        row['renormalized']=False
    return records


def prepare_context(root, daily, end):
    out=root/'context';out.mkdir(exist_ok=True)
    fire=[];receipts=[]
    for path in sorted((root/'raw/firms').glob('*.csv')):
        f=pd.read_csv(path,dtype={'acq_time':str})
        f['timestamp_utc']=pd.to_datetime(f.acq_date+' '+f.acq_time.str.zfill(4),format='%Y-%m-%d %H%M',utc=True)
        f['local_date']=f.timestamp_utc.dt.tz_convert('Asia/Kolkata').dt.strftime('%Y-%m-%d')
        # Explicit cross-border geographic box, not a state or country polygon.
        f=f[f.longitude.between(72,79)&f.latitude.between(27,33)&(f.local_date<=end)].copy()
        f['primary_confidence']=f.confidence.astype(str).str.lower().isin(['n','h','nominal','high'])
        f['region']='72–79E, 27–33N; cross-border northwestern airshed box'
        f['timestamp_utc']=f.timestamp_utc.dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        f['source_file']=path.name
        fire.append(f);receipts.append(dict(file=str(path.relative_to(root)),sha256=digest(path)))
    fire=pd.concat(fire,ignore_index=True).drop_duplicates(['satellite','timestamp_utc','latitude','longitude'])
    save_csv(out/'firms-detections.csv.gz',fire)
    f=fire[fire.primary_confidence].groupby(['satellite','local_date']).agg(detections=('latitude','size'),summed_detection_frp_mw=('frp','sum')).reset_index()
    save_csv(out/'firms-satellite-days.csv.gz',f)
    dss=parse_dss((root/'raw/discovery/dss.txt').read_text())
    save_csv(out/'iitm-model-contributions.csv.gz',dss)
    # Actual station weather and PM remain measurements. Missing fire days stay null.
    eligible=daily[daily.eligible.eq(True)]
    delhi=eligible[eligible.openaq_id.eq(235)].pivot(index='date',columns='parameter',values='mean').reset_index()
    hours=daily[daily.openaq_id.eq(235)].pivot(index='date',columns='parameter',values='valid_hours').add_suffix('_valid_hours').reset_index()
    delhi=delhi.merge(hours,on='date',validate='one_to_one')
    for satellite,g in f.groupby('satellite'):
        delhi=delhi.merge(g[['local_date','detections']].rename(columns={'local_date':'date','detections':f'fire_detections_{satellite}'}),on='date',how='left',validate='one_to_one')
    history=pd.DataFrame(dss).query("evidence_kind == 'published_model_daily_history'")
    delhi=delhi.merge(history[['valid_date','percent_total_pm25']].rename(columns={'valid_date':'date','percent_total_pm25':'iitm_modeled_stubble_percent'}),on='date',how='left',validate='one_to_one')
    save_csv(out/'delhi-episode-context.csv.gz',delhi)
    save_json(out/'context-manifest.json',dict(fire_inputs=receipts,dss_sha256=digest(root/'raw/discovery/dss.txt'),
        region_bbox=[72,27,79,33],fire_count_semantics='Detections by satellite, not unique fires or crop-burning attribution',
        frp_semantics='Sum of instantaneous detection FRP in MW, not integrated energy or emissions',
        fire_first_date=fire.local_date.min(),fire_last_date=fire.local_date.max(),
        dss_issue_time_status='unknown; captured chart dates retained without invented issue times or lead times',
        date_alignment='Monitor/fire dates are IST; IITM daily chart labels are joined as published, with timezone not independently specified',
        dss_forecast_category_totals={r['valid_date']:r['published_category_sum_percent'] for r in dss if r['evidence_kind']=='published_model_forecast'},
        dss_composition_status='Published forecast categories exceed 100 percent; retained with quality flags, never renormalized or used as a closed source-share composition',
        forecast_fire_assumption='IITM states future stubble contributions use climatological fire counts/emissions',
        era5_status='not acquired: no CDS credentials configured; measured station weather retained as a separately labeled input',
        interpretation='Descriptive join only. No causal source shares inferred from fire/PM correlations. Missing days are null.'))


def prepare_model(root):
    out=root/'model';out.mkdir(exist_ok=True)
    arrays={};metadata={};invalid=[]
    for parameter in ['pm25','pm10']:
        archive=root/'raw/longpmind'/f'{parameter}_monthly.zip'
        member=f'{parameter}_monthly/{parameter}_arr_10km_2022_monthly.nc'
        with zipfile.ZipFile(archive) as z:
            body=z.read(member)
        with netcdf_file(io.BytesIO(body),mmap=False) as ds:
            lat=ds.variables['lat'][:].copy();lon=ds.variables['lon'][:].copy()
            months=ds.variables['month'][:].copy();values=ds.variables[parameter][:].copy()
            if list(months) not in [list(range(1,13)),list(range(12))]:raise ValueError('Unexpected model month coordinate')
            if values.shape!=(12,len(lat),len(lon)):raise ValueError('Unexpected model dimensions')
            negative=values<0
            for month_index,lat_index,lon_index in zip(*np.where(negative)):
                invalid.append(dict(parameter=parameter,month=int(month_index)+1,
                    latitude=float(lat[lat_index]),longitude=float(lon[lon_index]),
                    raw_value=float(values[month_index,lat_index,lon_index]),quality_flag='negative_model_value'))
            # Preserve invalid values in the audit; mask instead of clipping.
            values[negative]=np.nan
            if arrays and (not np.array_equal(arrays['lat'],lat) or not np.array_equal(arrays['lon'],lon)):
                raise ValueError('PM model grids do not align')
            arrays.update(lat=lat,lon=lon)
            # Require all months, then day-weight monthly means for a 2022 mean.
            valid=np.isfinite(values).all(axis=0)
            annual=np.average(values,axis=0,weights=[calendar.monthrange(2022,m)[1] for m in range(1,13)])
            annual[~valid]=np.nan
            arrays[parameter]=annual;arrays[parameter+'_november']=values[10]
            metadata[parameter]=dict(archive_sha256=digest(archive),member=member,member_sha256=hashlib.sha256(body).hexdigest(),
                variable_units_attribute=getattr(ds.variables[parameter],'units',b'').decode() if isinstance(getattr(ds.variables[parameter],'units',b''),bytes) else str(getattr(ds.variables[parameter],'units','')),
                negative_monthly_values_masked=int(negative.sum()),finite_annual_cells=int(valid.sum()))
    latgrid,longrid=np.meshgrid(arrays['lat'],arrays['lon'],indexing='ij')
    valid=np.isfinite(arrays['pm25'])&np.isfinite(arrays['pm10'])
    frame=pd.DataFrame({'latitude':latgrid[valid],'longitude':longrid[valid],
        'pm25_annual_ug_m3':arrays['pm25'][valid],'pm10_annual_ug_m3':arrays['pm10'][valid],
        'pm25_november_ug_m3':arrays['pm25_november'][valid],'pm10_november_ug_m3':arrays['pm10_november'][valid]})
    save_csv(out/'longpmind-2022-native-grid.csv.gz',frame)
    save_csv(out/'invalid-model-values.csv.gz',pd.DataFrame(invalid,
        columns=['parameter','month','latitude','longitude','raw_value','quality_flag']))
    np.savez_compressed(out/'longpmind-2022-grid.npz',**arrays)
    features=[dict(type='Feature',geometry=dict(type='Point',coordinates=[r.longitude,r.latitude]),
        properties=dict(year=2022,evidence_kind='modeled_reconstruction',pm25_annual_ug_m3=r.pm25_annual_ug_m3,
            pm10_annual_ug_m3=r.pm10_annual_ug_m3,pm25_november_ug_m3=r.pm25_november_ug_m3,
            pm10_november_ug_m3=r.pm10_november_ug_m3)) for r in frame.itertuples()]
    save_json(out/'longpmind-2022.geojson',dict(type='FeatureCollection',features=features,
        metadata=dict(evidence_kind='modeled_reconstruction',year=2022,grid_step_degrees=[float(np.diff(arrays['lon'])[0]),float(np.diff(arrays['lat'])[0])],
            unit='µg/m³',unit_provenance='LongPMInd research paper; pollutant NetCDF units attribute absent',
            doi='10.5281/zenodo.14557027',license='CC BY 4.0',
            spatial_support='Source nominal 10 km grid; points locate native grid centers, not monitoring stations')))
    save_json(out/'model-manifest.json',dict(product='LongPMInd',version='v2',doi='10.5281/zenodo.14557027',
        archive_period='1980–2022',prepared_year=2022,license='CC BY 4.0',files=metadata,
        unit='µg/m³',unit_provenance='Research paper; NetCDF pollutant variable omits a units attribute',
        annual_method='Calendar-day-weighted monthly means; require 12 finite, nonnegative months',
        negative_value_policy='Raw negative model values retained in invalid-model-values.csv.gz; masked, not clipped to zero',
        paired_export_cells=len(frame),
        observed_coverage_contribution=0,independent_validation='Not established: no verified held-out 2022 station set acquired',
        limitations='Historical modeled layer only; no 2025/2026 gap filling, local source attribution, or finer resolution claim'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--end',default='2026-11-08')
    parser.add_argument('--locations',type=Path,default=Path('scripts/data/india-openaq-locations-20261108.json'))
    parser.add_argument('--only',choices=['observations','context','model','xkdr','coverage','all'],default='all')
    args=parser.parse_args();root=args.root.resolve()
    locations=json.loads(args.locations.read_text())['locations']
    inventory,national=make_inventory(root,locations)
    if args.only in ['observations','all']:daily=prepare_openaq(root,inventory,args.end)
    elif args.only=='context':daily=pd.read_csv(root/'observations/openaq-station-days.csv.gz',keep_default_na=False)
    if args.only in ['xkdr','all']:prepare_xkdr(root,national)
    if args.only in ['context','all']:prepare_context(root,daily,args.end)
    if args.only in ['model','all']:prepare_model(root)
    if args.only in ['coverage','all']:coverage_tables(root,inventory,national,args.end)
    print('Prepared India enrichment:',root,flush=True)


if __name__=='__main__':
    main()
