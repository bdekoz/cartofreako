#!/usr/bin/env python3
"""Compare years only on the same valid H3 cell-days and calendar window."""
import json
from pathlib import Path

import numpy as np

from ocean_temperature import digest, write_json

from viz_context import ocean_output, cutoff, matched_days, product_months
ROOT=ocean_output()


def ratio(value, denominator):
    return value/denominator if denominator else None


def main():
    g=np.load(ROOT/'work/grid.npz');lat,lon=g['centers'].T;weights=g['weights']
    a=np.load(ROOT/'work/2025.npy',mmap_mode='r');b=np.load(ROOT/'work/2026.npy',mmap_mode='r')
    days_a=json.loads((ROOT/'work/2025.json').read_text())['dates']
    days_b=json.loads((ROOT/'work/2026.json').read_text())['dates']
    assert all(x[5:]==y[5:] for x,y in zip(days_a[:matched_days()],days_b[:matched_days()]))
    regions={'global source-supported ocean':np.ones(len(lat),bool),'Japan 20–50N / 120–160E':(lat>=20)&(lat<=50)&(lon>=120)&(lon<=160),
             'Northern Hemisphere':lat>0,'Southern Hemisphere':lat<0,'tropics 20S–20N':abs(lat)<=20}
    totals={key:dict(paired_cell_days=0,weight_sum=0.,sst_2025_weighted_sum=0.,sst_2026_weighted_sum=0.) for key in regions}
    per_month={key:[] for key in regions}
    for month in product_months():
        monthly={key:dict(paired_cell_days=0,weight_sum=0.,sst_2025_weighted_sum=0.,sst_2026_weighted_sum=0.) for key in regions}
        for day_index in [i for i,d in enumerate(days_b[:matched_days()]) if int(d[5:7])==month]:
            x,y=a[day_index],b[day_index];paired=np.isfinite(x)&np.isfinite(y)
            for key,region in regions.items():
                valid=paired&region;w=weights[valid]
                row=monthly[key];row['paired_cell_days']+=int(valid.sum());row['weight_sum']+=float(w.sum())
                row['sst_2025_weighted_sum']+=float(np.dot(x[valid],w));row['sst_2026_weighted_sum']+=float(np.dot(y[valid],w))
        for key,row in monthly.items():
            for field,value in row.items():totals[key][field]+=value
            per_month[key].append(dict(month=month,days=sum(d[5:7]==f'{month:02d}' for d in days_b[:matched_days()]),
                                      sst_2025_degC=ratio(row['sst_2025_weighted_sum'],row['weight_sum']),sst_2026_degC=ratio(row['sst_2026_weighted_sum'],row['weight_sum']),
                                      difference_2026_minus_2025_degC=ratio(row['sst_2026_weighted_sum']-row['sst_2025_weighted_sum'],row['weight_sum']),paired_cell_days=row['paired_cell_days']))
    rows=[]
    for key,row in totals.items():
        rows.append(dict(region=key,paired_cell_days=row['paired_cell_days'],sst_2025_degC=ratio(row['sst_2025_weighted_sum'],row['weight_sum']),sst_2026_degC=ratio(row['sst_2026_weighted_sum'],row['weight_sum']),
                         difference_2026_minus_2025_degC=ratio(row['sst_2026_weighted_sum']-row['sst_2025_weighted_sum'],row['weight_sum']),months=per_month[key]))
    write_json(ROOT/'data/matched-comparison.json',dict(period=f'January 1–{cutoff().strftime("%B %d")}, each year; {matched_days()} calendar days',
        method='At each H3 cell and calendar day, retain the pair only if both years are valid. Identical paired cell-day support and weights in the two means; sum-of-source-center cos(latitude) weights approximate ocean area. Region membership uses H3 centers.',
        climate_interpretation='A one-year difference is not an attribution result or a long-term trend. The final month may be partial.',regions=rows,
        inputs=[dict(path=f'work/{y}.npy',sha256=digest(ROOT/'work'/f'{y}.npy')) for y in (2025,2026)]))
    print(json.dumps([{k:v for k,v in r.items() if k!='months'} for r in rows],indent=2))


if __name__=='__main__':main()
