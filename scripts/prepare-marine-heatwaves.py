#!/usr/bin/env python3
"""Prepare event-day maps, complete event ledgers and monthly paired support."""
import argparse
import csv
from datetime import date
import gzip
import json
import shutil

import numpy as np

from ocean_stage_2 import OUTPUT,OCEAN,dates,slots,event_flags,event_edges,save_product,cutoff,matched_cutoff,matched_days,product_months
from ocean_stage_2 import ocean_array
from ocean_temperature import write_json,digest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--chunk',type=int,default=4096);a=p.parse_args()
    grid=dict(np.load(OCEAN/'work/grid.npz'));n=len(grid['cells']);base=OUTPUT/'work/baseline'
    mean=np.load(base/'mean.npy',mmap_mode='r');threshold=np.load(base/'threshold.npy',mmap_mode='r')
    source=[ocean_array(y) for y in (2024,2025,2026)]
    all_days=sum([dates(y,len(s)) for y,s in zip((2024,2025,2026),source)],[])
    periods=[(2025,'annual',date(2025,12,31)),(2025,'matched',matched_cutoff()),(2026,'annual',cutoff())]
    products=[];daily_dir=OUTPUT/'work/marine-daily';daily_dir.mkdir(parents=True,exist_ok=True)
    for year,period,period_end in periods:
        length=(period_end-all_days[0]).days+1;ds=all_days[:length];sl=slots(ds)
        first=ds.index(date(year,1,1));expected=length-first
        counts={k:np.zeros(n,dtype='uint16') for k in ('observed_days','eligible_days','event_days','exceedance_days','longest_duration','pending_days','edge_events')}
        counts['cumulative_intensity']=np.zeros(n,dtype='float64')
        monthly={k:np.zeros((12,n),dtype='float32') for k in ('eligible_days','event_days','cumulative_intensity')}
        path=OUTPUT/'data'/f'marine-events-{year}-{period}.csv.gz';path.parent.mkdir(parents=True,exist_ok=True)
        event_count=0
        with gzip.open(path,'wt',newline='') as f:
            writer=csv.writer(f);writer.writerow(['h3','start','end','observed_duration','days_in_period','intensity_in_period_degC_days','left_censored','right_censored'])
            for lo in range(0,n,a.chunk):
                hi=min(lo+a.chunk,n);values=np.concatenate([s[:,lo:hi] for s in source],axis=0)[:length].T.copy()
                flags=event_flags(values,threshold[lo:hi],ds)
                anomaly=values-mean[lo:hi][:,sl]
                subset=flags[:,first:];event=(subset&4)>0
                counts['observed_days'][lo:hi]=((subset&1)>0).sum(axis=1)
                counts['eligible_days'][lo:hi]=(((subset&1)>0)&((subset&32)==0)).sum(axis=1)
                counts['event_days'][lo:hi]=event.sum(axis=1)
                counts['exceedance_days'][lo:hi]=((subset&2)>0).sum(axis=1)
                counts['pending_days'][lo:hi]=((subset&32)>0).sum(axis=1)
                counts['cumulative_intensity'][lo:hi]=np.where(event,anomaly[:,first:],0).sum(axis=1,dtype='float64')
                for month in range(1,13):
                    ix=np.array([i for i,d in enumerate(ds) if d.year==year and d.month==month],dtype=int)
                    if not len(ix):continue
                    ev=(flags[:,ix]&4)>0
                    monthly['eligible_days'][month-1,lo:hi]=(((flags[:,ix]&1)>0)&((flags[:,ix]&32)==0)).sum(axis=1)
                    monthly['event_days'][month-1,lo:hi]=ev.sum(axis=1)
                    monthly['cumulative_intensity'][month-1,lo:hi]=np.where(ev,anomaly[:,ix],0).sum(axis=1)
                rows,starts=np.nonzero(flags&8);erows,ends=np.nonzero(flags&16);assert np.array_equal(rows,erows)
                for row,s,e in zip(rows,starts,ends):
                    if e<first:continue
                    clipped=max(s,first);span=e-clipped+1;idx=lo+row
                    left,right=event_edges(flags[row],s,e)
                    counts['longest_duration'][idx]=max(counts['longest_duration'][idx],span)
                    counts['edge_events'][idx]+=left or right
                    intensity=float(anomaly[row,clipped:e+1].sum(dtype='float64'))
                    writer.writerow([f'{int(grid["cells"][idx]):x}',ds[s],ds[e],e-s+1,span,format(intensity,'.9g'),int(left),int(right)])
                    event_count+=1
                np.savez_compressed(daily_dir/f'{year}-{period}-{lo:06d}.npz',flags=flags[:,first:],cells=grid['cells'][lo:hi])
                if lo%(a.chunk*16)==0:print(f'Marine {year} {period}: {hi}/{n}',flush=True)
        meta=save_product(f'marine-heatwave-{year}-{period}',{**counts,'cells':grid['cells'],'centers':grid['centers'],'weights':grid['weights']},
            {'family':'marine-heatwave','year':year,'period':period,'data_through':str(period_end),'expected_days':expected,
             'baseline':'1991–2020','event_count':event_count,'event_ledger':path.name,'event_ledger_sha256':digest(path),
             'censoring':'observed spans clipped to reporting interval; edge durations are lower bounds; pending short runs excluded from event-eligible denominator, retained in observed/pending counts'})
        np.savez_compressed(OUTPUT/'work'/f'marine-monthly-{year}-{period}.npz',**monthly)
        products.append(meta)
    # Compare the same eligible calendar-date/cell pairs, with both detectors
    # cut at the selected shared calendar endpoint. A full-year 2025 detector is never used for this pair.
    rows=[]
    for month in product_months():
        totals=np.zeros(4,dtype='float64')
        for lo in range(0,n,a.chunk):
            hi=min(lo+a.chunk,n);a1=np.load(daily_dir/f'2025-matched-{lo:06d}.npz')['flags'];a2=np.load(daily_dir/f'2026-annual-{lo:06d}.npz')['flags']
            ix=[i for i,d in enumerate(dates(2025,matched_days())) if d.month==month]
            pair=((a1[:,ix]&1)>0)&((a2[:,ix]&1)>0)&((a1[:,ix]&32)==0)&((a2[:,ix]&32)==0);w=grid['weights'][lo:hi,None]
            totals += [pair.sum(),np.sum(pair*w),np.sum(pair*((a1[:,ix]&4)>0)*w),np.sum(pair*((a2[:,ix]&4)>0)*w)]
        rows.append({'month':month,'paired_cell_days':int(totals[0]),'weighted_denominator':totals[1],
                     'event_fraction_2025':totals[2]/totals[1],'event_fraction_2026':totals[3]/totals[1]})
    write_json(OUTPUT/'data/marine-products.json',products)
    write_json(OUTPUT/'data/marine-matched-comparison.json',{'calendar':f'January 1–{cutoff().strftime("%B %d")} in each year','months':rows,
               'weighting':'sum cos(latitude) of fixed source centers; shared eligible cell-days; approximate area weighting'})


if __name__=='__main__':main()
