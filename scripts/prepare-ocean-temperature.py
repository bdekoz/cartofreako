#!/usr/bin/env python3
"""Prepare original-center H3r5 SST, anomalies and strict daily-mean records.

Preparation is offline. --wait-for-downloads can consume independently verified
year files as the fetcher completes them. Every cached year pins both raw inputs.
"""
from __future__ import annotations

import argparse
import calendar
from datetime import date, timedelta
import json
import os
from pathlib import Path
import time

import numpy as np

from ocean_temperature import NetCDF, digest, h3_cell, h3_center, write_json

EPOCH = date(1800, 1, 1)
ALGORITHM = 'oisst-h3r5-full-membership-v1'


def dates(nc, year):
    assert nc.attributes('time')['units'].startswith('days since 1800-01-01')
    days = [EPOCH + timedelta(days=int(v)) for v in nc.read('time')]
    assert days and days[0] == date(year, 1, 1)
    assert all(d.year == year for d in days)
    assert all(b-a == timedelta(days=1) for a, b in zip(days, days[1:]))
    return days


def calendar_slot(day):
    """366 fixed month/day slots: March never shifts across leap/nonleap years."""
    return (day.replace(year=2000)-date(2000, 1, 1)).days


def aggregate_day(sst, ice, indices, inverse, members):
    values = sst.ravel()[indices].astype('float64')
    concentration = ice.ravel()[indices]
    # PSL stores fractions despite the text attribute 'percent'. Its ice field
    # is sparse outside reported ice. Do not turn that mask into SST missingness.
    valid = np.isfinite(values) & ~(
        np.isfinite(concentration) & (concentration >= .15 - 1e-6))
    count = np.bincount(inverse[valid], minlength=len(members))
    total = np.bincount(inverse[valid], weights=values[valid], minlength=len(members))
    out = np.full(len(members), np.nan, dtype='float32')
    complete = count == members
    out[complete] = total[complete] / count[complete]
    return out


def grid(cache, work):
    source = cache/'lsmask.oisst.nc'
    key = {'source_sha256': digest(source), 'algorithm': ALGORITHM, 'implementation_sha256': digest(__file__)}
    receipt, target = work/'grid.json', work/'grid.npz'
    if receipt.exists() and target.exists() and json.loads(receipt.read_text()) == key:
        return dict(np.load(target))
    with NetCDF(source) as nc:
        mask = nc.read('lsmask').reshape(720, 1440)
        lat, lon = nc.read('lat'), nc.read('lon')
    assert np.allclose(lat, np.arange(-89.875, 90, .25))
    assert np.allclose(lon, np.arange(.125, 360, .25))
    assert mask[360,720] == 1 and mask[520,400] == 0  # Pacific / continental Asia
    indices = np.flatnonzero(mask.ravel() == 1)
    raw = np.fromiter((h3_cell(lat[i//1440], lon[i%1440]) for i in indices), dtype='uint64', count=len(indices))
    cells, inverse, members = np.unique(raw, return_inverse=True, return_counts=True)
    centers = np.array([h3_center(c) for c in cells])
    weights = np.bincount(inverse, weights=np.cos(np.deg2rad(lat[indices//1440])), minlength=len(cells))
    result = dict(indices=indices, inverse=inverse, members=members, cells=cells, centers=centers, weights=weights)
    np.savez_compressed(target, **result)
    write_json(receipt, key)
    print(f'Grid: {len(indices)} original ocean centers / {len(cells)} occupied H3r5 cells', flush=True)
    return result


def cache_year(cache, work, year, g):
    paths = [cache/f'{v}.day.mean.{year}.nc' for v in ('sst', 'icec')]
    sources = []
    for path in paths:
        receipt = json.loads(path.with_suffix('.nc.json').read_text())
        if digest(path) != receipt['sha256']:
            raise ValueError('Changed raw input ' + str(path))
        sources.append(receipt)
    key = {'algorithm': ALGORITHM, 'grid_sha256': digest(work/'grid.npz'), 'implementation_sha256': digest(__file__),
           'sources': [{k:r[k] for k in ('url','sha256','shape') if k in r} for r in sources]}
    target, receipt = work/f'{year}.npy', work/f'{year}.json'
    if target.exists() and receipt.exists():
        old = json.loads(receipt.read_text())
        if old['inputs'] == key and old['sha256'] == digest(target):
            return
    with NetCDF(paths[0]) as sst, NetCDF(paths[1]) as ice:
        sst_days, ice_days = dates(sst, year), dates(ice, year)
        days = sst_days[:min(len(sst_days),len(ice_days))]
        assert days == ice_days[:len(days)]
        assert sst.shape('sst') == (len(sst_days),720,1440)
        assert ice.shape('icec') == (len(ice_days),720,1440)
        assert sst.attributes('sst')['units'] == 'degC'
        assert ice.attributes('icec')['valid_range'] == [0.,1.]
        if year < 2026:
            assert len(days) == 365 + calendar.isleap(year)
        temporary = target.with_suffix('.part.npy')
        output = np.lib.format.open_memmap(temporary, mode='w+', dtype='float32', shape=(len(days),len(g['cells'])))
        for i, day in enumerate(days):
            args = dict(start=(i,0,0), count=(1,720,1440))
            output[i] = aggregate_day(sst.read('sst',**args),ice.read('icec',**args),g['indices'],g['inverse'],g['members'])
        output.flush(); del output
        temporary.replace(target)
        write_json(receipt, {'inputs': key, 'sha256': digest(target), 'dates': [d.isoformat() for d in days]})
    print(f'Cached {year}: {len(days)} daily H3 fields', flush=True)


def strict_records(value, high, low, history, minimum=30):
    eligible = np.isfinite(value) & (history >= minimum)
    # Values are float32 daily H3 means, compared with the same representation.
    return eligible, eligible & (value > high), eligible & (value < low)


def summarize(work, output, g, cutoff, snapshot_date=date(2026,11,8)):
    n = len(g['cells'])
    high = np.full((366,n), -np.inf, dtype='float32')
    low = np.full((366,n), np.inf, dtype='float32')
    history = np.zeros((366,n), dtype='uint8')
    climatology = np.zeros((366,n), dtype='float64')
    climate_count = np.zeros((366,n), dtype='uint8')
    months, profiles = [], []
    for year in range(1982,2027):
        data = np.load(work/f'{year}.npy', mmap_mode='r')
        receipt = json.loads((work/f'{year}.json').read_text())
        days = [date.fromisoformat(d) for d in receipt['dates']]
        if year == 2021:
            np.divide(climatology, climate_count, out=climatology, where=climate_count>0)
            climatology[climate_count<24] = np.nan
        if year in (2025,2026):
            # Twelve monthly rows per H3 cell remain inspectable for future
            # calendar-aligned comparisons; no zero substitution for missing.
            sums = {k: np.zeros((12,n), dtype='float64') for k in ('sst_sum','anomaly_sum')}
            counts = {k: np.zeros((12,n), dtype='uint16') for k in ('valid_days','anomaly_days','eligible_days','high_days','low_days')}
            matched = {k: np.zeros(n,dtype='float64') for k in ('sst_sum','anomaly_sum','valid_days','anomaly_days','eligible_days','high_days','low_days')}
        for i, day in enumerate(days):
            if year == 2026 and day > cutoff:
                continue
            slot, values = calendar_slot(day), data[i]
            valid = np.isfinite(values)
            if year in (2025,2026):
                m = day.month-1
                eligible, upper, lower = strict_records(values,high[slot],low[slot],history[slot])
                anomaly = values-climatology[slot]
                av = np.isfinite(anomaly)
                additions = {'sst_sum':np.where(valid,values,0), 'anomaly_sum':np.where(av,anomaly,0),
                             'valid_days':valid, 'anomaly_days':av, 'eligible_days':eligible,'high_days':upper,'low_days':lower}
                for key, value in additions.items():
                    (sums if key.endswith('_sum') else counts)[key][m] += value
                    if (day.month,day.day) <= (cutoff.month,cutoff.day):
                        matched[key] += value
            if 1991 <= year <= 2020:
                climatology[slot,valid] += values[valid]
                climate_count[slot,valid] += 1
            # Compare target first, only then extend the historical record.
            high[slot,valid] = np.maximum(high[slot,valid],values[valid])
            low[slot,valid] = np.minimum(low[slot,valid],values[valid])
            history[slot,valid] += 1
        if year not in (2025,2026):
            print(f'Baseline through {year}', flush=True)
            continue
        through = min(days[-1],cutoff) if year == 2026 else days[-1]
        arrays = {**sums, **counts, 'cells':g['cells'], 'centers':g['centers'], 'weights':g['weights']}
        np.savez_compressed(output/f'monthly-{year}.npz',**arrays)
        annual = {k:a.sum(axis=0) for k,a in {**sums,**counts}.items()}
        for period, values in [('annual',annual),('matched',matched)]:
            mean = np.divide(values['sst_sum'],values['valid_days'],out=np.full(n,np.nan),where=values['valid_days']>0)
            anomaly = np.divide(values['anomaly_sum'],values['anomaly_days'],out=np.full(n,np.nan),where=values['anomaly_days']>0)
            period_end = through if period=='annual' else date(year,cutoff.month,cutoff.day)
            expected_days = (period_end-date(year,1,1)).days+1
            # Eighty percent of calendar days is a rendering gate; raw counts
            # and means are retained even for cells below this threshold.
            mean[values['valid_days']<.8*expected_days] = np.nan
            anomaly[values['anomaly_days']<.8*expected_days] = np.nan
            result = {**values,'cells':g['cells'],'centers':g['centers'],'mean_sst':mean,'mean_anomaly':anomaly}
            path = output/f'water-temperature-{year}-{period}.npz'
            np.savez_compressed(path,**result)
            metadata = dict(schema='cartofreako-ocean-temperature-v1', year=year, period=period,
                data_through=period_end.isoformat(), snapshot_as_of=snapshot_date.isoformat(), h3_resolution=5,
                grid='NOAA OISST v2.1, 0.25 degree original ocean centers',
                aggregation='Arithmetic mean of all valid original centers in each H3 cell BEFORE historical comparisons; incomplete H3 membership masks the day.',
                record_baseline=f'1982–{year-1}', minimum_history_years=30, record_comparison='strict; daily mean SST, not TMAX/TMIN',
                anomaly_baseline='1991–2020 calendar-day mean; minimum 24 of 30 years',
                ice_policy='Exclude daily source cells with reported ice fraction >=0.15; retain sparse ice-field missing values where SST is valid. Fraction range 0..1 overrides misleading PSL percent label.',
                expected_days=expected_days, display_minimum_day_fraction=.8,
                preliminary_after=('2026-10-24' if year==2026 else None) if not os.environ.get('DATA_HTTP_CACHE') else None,
                provider_revision_status='Recent provider values may be revised; no per-day finality flag supplied by the yearly source',
                occupied_cells=n, displayed_sst_cells=int(np.isfinite(mean).sum()), displayed_anomaly_cells=int(np.isfinite(anomaly).sum()),
                high_record_cell_days=int(values['high_days'].sum()),low_record_cell_days=int(values['low_days'].sum()),
                data_file=path.name, sha256=digest(path), algorithm=ALGORITHM)
            write_json(output/f'water-temperature-{year}-{period}.json',metadata)
            profiles.append(metadata)
        for m in range(12):
            if m+1>through.month:
                continue
            w=g['weights']; valid=counts['valid_days'][m]>0; av=counts['anomaly_days'][m]>0
            months.append(dict(year=year,month=m+1,valid_cells=int(valid.sum()),
                sst_mean_degC=float(np.sum(sums['sst_sum'][m]*w)/np.sum(counts['valid_days'][m]*w)),
                anomaly_mean_degC=float(np.sum(sums['anomaly_sum'][m]*w)/np.sum(counts['anomaly_days'][m]*w)),
                weighting='H3 daily means weighted by summed cos(latitude) of source centers × valid day; source-supported approximation with changing coverage, not a fixed-area global ocean trend',
                high_record_cell_days=int(counts['high_days'][m].sum()),low_record_cell_days=int(counts['low_days'][m].sum()),
                eligible_cell_days=int(counts['eligible_days'][m].sum())))
        print(f'Prepared {year} through {through}',flush=True)
    write_json(output/'monthly-summary.json',months)
    write_json(output/'products.json',profiles)
    write_json(output/'input-ledger.json',{'algorithm':ALGORITHM,'years':[json.loads((work/f'{y}.json').read_text()) for y in range(1982,2027)]})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('output/ocean-temperature-20261108'))
    parser.add_argument('--cutoff',type=date.fromisoformat,default=date(2026,11,7))
    parser.add_argument('--snapshot-date',type=date.fromisoformat,default=date(2026,11,8))
    parser.add_argument('--wait-for-downloads',action='store_true')
    parser.add_argument('--cache-only',action='store_true')
    args=parser.parse_args()
    cache,work,output=args.root/'cache/oisst',args.root/'work',args.root/'data'
    work.mkdir(parents=True,exist_ok=True);output.mkdir(parents=True,exist_ok=True)
    g=grid(cache,work)
    pending=set(range(1982,2027))
    while pending:
        ready=[y for y in sorted(pending) if all((cache/f'{v}.day.mean.{y}.nc.json').exists() for v in ('sst','icec'))]
        for year in ready:
            cache_year(cache,work,year,g);pending.remove(year)
        if pending:
            if not args.wait_for_downloads:
                raise SystemExit('Missing pinned years: '+str(sorted(pending)))
            print('Waiting for '+str(len(pending))+' NOAA year pairs',flush=True)
            time.sleep(30)
    if not args.cache_only:
        summarize(work,output,g,args.cutoff,args.snapshot_date)


if __name__=='__main__':
    main()
