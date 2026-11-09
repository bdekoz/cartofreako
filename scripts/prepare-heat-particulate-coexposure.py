#!/usr/bin/env python3
"""Join the selected India PM2.5 monitors to containing CPC TMAX supports."""
import csv
from datetime import date,timedelta
import gzip
import hashlib
import json

import numpy as np

from ocean_stage_2 import ROOT,OUTPUT,NetCDF,cpc_path,cpc_dates,dates,slots,nonleap_indices,climatology,save_product,product_months,cutoff
from viz_context import input_path
from ocean_temperature import digest,write_json,h3_cell,h3_center

SOURCE=input_path('INDIA_OBSERVATIONS',ROOT/'output/india-particulate-20261108/enrichment/observations/openaq-station-days.csv.gz')


def containing_cell(lat,lon):
    if not -90<lat<90:raise ValueError('Invalid station latitude')
    return int(np.floor((90-lat)/.5))*720+int(np.floor((lon%360)/.5))


def read_observations(source=None):
    with gzip.open(source or SOURCE,'rt') as f:rows=[r for r in csv.DictReader(f) if r['parameter']=='pm25']
    seen=set();stations={}
    for r in rows:
        key=(r['canonical_id'],r['date'])
        if key in seen:raise ValueError('Duplicate canonical station/date: '+str(key))
        seen.add(key);assert r['unit']=='µg/m³'
        lat,lon=float(r['latitude']),float(r['longitude'])
        station={'id':r['canonical_id'],'name':r['station_name'],'source':r['source'],'openaq_id':r['openaq_id'],
             'latitude':lat,'longitude':lon,'monitor_class':'reference' if r['station_type']=='reference' else 'low-cost',
             'native_index':containing_cell(lat,lon),'h3':f'{h3_cell(lat,lon):x}'}
        native=station['native_index'];center_lat=89.75-.5*(native//720);center_lon=(.25+.5*(native%720)+180)%360-180
        a,b=np.deg2rad([lat,center_lat]);dlon=np.deg2rad(center_lon-lon)
        distance=2*6371.0088*np.arcsin(np.sqrt(np.sin((b-a)/2)**2+np.cos(a)*np.cos(b)*np.sin(dlon/2)**2))
        station.update(cpc_center=[center_lat,center_lon],cpc_center_distance_km=float(distance))
        if station['id'] in stations:assert stations[station['id']]==station,'Station metadata drift'
        stations[station['id']]=station
    return rows,sorted(stations.values(),key=lambda s:s['id'])


def heat_series(stations):
    folder=OUTPUT/'work/india';folder.mkdir(parents=True,exist_ok=True)
    indices=np.array([s['native_index'] for s in stations]);arrays={};receipts=[]
    for year in list(range(1991,2021))+[2025,2026]:
        path=folder/f'tmax-{year}.npy';source=cpc_path(year)
        key={'source_sha256':digest(source),'station_indices':hashlib.sha256(indices.tobytes()).hexdigest(),
             'implementation_sha256':digest(__file__)}
        receipt=path.with_suffix('.json');old=json.loads(receipt.read_text()) if receipt.exists() else {}
        with NetCDF(source) as nc:
            ds=cpc_dates(nc)
            if not path.exists() or old.get('inputs')!=key or old.get('sha256')!=digest(path):
                np.save(path,nc.read('tmax').reshape(len(ds),-1)[:,indices])
                write_json(receipt,{'inputs':key,'sha256':digest(path)})
        arrays[year]=np.load(path)
        if year==cutoff().year:
            arrays[year]=arrays[year][:(cutoff()-date(year,1,1)).days+1]
        receipts.append({'year':year,'file':str(source.resolve()),'sha256':digest(source),'data_through':str(ds[-1]),
                         'url':f'https://psl.noaa.gov/thredds/fileServer/Datasets/cpc_global_temp/tmax.{year}.nc'})
    values=np.stack([arrays[y][nonleap_indices(y)].T for y in range(1991,2021)],axis=1)
    mean,q,count,years=climatology(values)
    np.savez_compressed(folder/'baseline.npz',mean=mean,threshold=q,sample_count=count,year_count=years)
    write_json(OUTPUT/'data/india-cpc-inputs.json',receipts)
    return arrays,q


def station_states(pm,eligible,heat,threshold,days,pm_limit=35,shift=0):
    result=np.zeros(pm.shape,dtype='uint8')
    for i,d in enumerate(days):
        j=i+shift
        if j<0 or j>=len(heat):continue
        q=threshold[:,slots([d+timedelta(days=shift)])[0]]
        valid=eligible[i]&np.isfinite(pm[i])&np.isfinite(heat[j])&np.isfinite(q)
        result[i]=np.where(valid,1+(heat[j]>q).astype('uint8')+2*(pm[i]>pm_limit).astype('uint8'),0)
    return result


def counts(states):
    result={k:np.sum(states==i,axis=0).astype('uint16') for i,k in enumerate(['invalid_days','neither_days','heat_only_days','pm_only_days','both_days'])}
    result['eligible_days']=np.sum(states>0,axis=0).astype('uint16')
    result['fraction']=np.divide(result['both_days'],result['eligible_days'],out=np.full(states.shape[1],np.nan),where=result['eligible_days']>0)
    return result


def station_diagnostics(stations):
    write_json(OUTPUT/'data/india-station-crosswalk.json',{'source':str(SOURCE.resolve()),'source_sha256':digest(SOURCE),'stations':stations,
       'duplicates':0,'coordinates':'all retained daily coordinates checked for stability; no nearest-valid replacement for a missing containing CPC cell'})
    with gzip.open(OUTPUT/'data/india-station-days.csv.gz','rt') as f:
        states={(r['canonical_id'],r['date']):int(r['state']) for r in csv.DictReader(f)}
    products=json.loads((OUTPUT/'data/india-products.json').read_text());monthly=[]
    for product in products:
        ds=dates(product['year'],product['expected_days'])
        for station in stations:
            if station['monitor_class']!=product['monitor_class']:continue
            for month in sorted(set(d.month for d in ds)):
                selected=[d for d in ds if d.month==month]
                values=np.array([states.get((station['id'],str(d)),0) for d in selected])[:,None]
                monthly.append({'id':station['id'],'monitor_class':station['monitor_class'],'year':product['year'],
                    'period':product['period'],'month':month,'expected_days':len(selected),
                    **{key:(float(value[0]) if np.isfinite(value[0]) else None) for key,value in counts(values).items()}})
    write_json(OUTPUT/'data/india-station-monthly-coverage.json',{'grain':'canonical monitor, year, product window and month; absent days are ineligible',
        'station_ledger_sha256':digest(OUTPUT/'data/india-station-days.csv.gz'),'rows':monthly})


def main():
    (OUTPUT/'data').mkdir(parents=True,exist_ok=True);rows,stations=read_observations();heat,q=heat_series(stations)
    n=len(stations);bank={s['id']:i for i,s in enumerate(stations)};byyear={};sensitivity=[];ledger=[]
    for year in (2025,2026):
        ds=dates(year,len(heat[year]));pm=np.full((len(ds),n),np.nan);eligible=np.zeros(pm.shape,bool)
        for r in rows:
            d=date.fromisoformat(r['date'])
            if d.year!=year or d>ds[-1]:continue
            i=(d-ds[0]).days;j=bank[r['canonical_id']];pm[i,j]=float(r['mean'])
            eligible[i,j]=r['eligible']=='True' and int(r['valid_hours'])>=18
        states=station_states(pm,eligible,heat[year],q,ds);byyear[year]=(states,ds,pm,eligible)
        for limit in (25,35,50):
            for shift in (-1,0,1):
                variant=station_states(pm,eligible,heat[year],q,ds,limit,shift)
                for kind in ('reference','low-cost'):
                    ix=[i for i,s in enumerate(stations) if s['monitor_class']==kind]
                    common=(states[:,ix]>0)&(variant[:,ix]>0)
                    sensitivity.append({'year':year,'monitor_class':kind,'pm_limit_ug_m3':limit,'heat_date_shift_days':shift,
                      'common_eligible_station_days':int(common.sum()),'both_variant':int(np.sum(common&(variant[:,ix]==4))),
                      'both_primary_on_common_support':int(np.sum(common&(states[:,ix]==4)))})
        for r in rows:
            d=date.fromisoformat(r['date'])
            if d.year!=year or d>ds[-1]:continue
            i=(d-ds[0]).days;j=bank[r['canonical_id']];t=float(heat[year][i,j]);qt=float(q[j,slots([d])[0]])
            state=int(states[i,j]);reason='eligible' if state else 'insufficient PM hours' if not eligible[i,j] else 'missing heat/baseline'
            ledger.append([r['canonical_id'],r['date'],stations[j]['monitor_class'],r['sensor_id'],r['valid_hours'],r['mean'],
                t if np.isfinite(t) else '',qt if np.isfinite(qt) else '',state,reason])
        np.savez_compressed(OUTPUT/'work/india'/f'daily-{year}.npz',states=states,pm25=pm,pm_eligible=eligible,tmax=heat[year],threshold=q)
    products=[];station_summaries=[];matched=[]
    for kind in ('reference','low-cost'):
        selected=np.array([i for i,s in enumerate(stations) if s['monitor_class']==kind]);ss=[stations[i] for i in selected]
        s26=byyear[2026][0][:,selected];observed=np.flatnonzero(np.any(s26>0,axis=1));cutoff=int(observed[-1])+1 if len(observed) else 0
        for year,period,length in [(2025,'annual',365),(2025,'matched',cutoff),(2026,'annual',cutoff)]:
            states=byyear[year][0][:length,selected];summary=counts(states)
            for i,station in enumerate(ss):station_summaries.append({**station,'year':year,'period':period,'expected_days':length,
                **{k:(float(v[i]) if np.isfinite(v[i]) else None) for k,v in summary.items()}})
            # H3 cell-date union avoids multiplying days when monitors share a cell.
            cell_ids=np.array([int(s['h3'],16) for s in ss],dtype='uint64');cells=np.unique(cell_ids)
            union=np.zeros((length,len(cells)),dtype='uint8')
            for i,cell in enumerate(cells):
                group=states[:,cell_ids==cell];good=np.any(group>0,axis=1);both=np.any(group==4,axis=1)
                hot=np.any((group==2)|(group==4),axis=1);dirty=np.any((group==3)|(group==4),axis=1)
                # A joint day requires one monitor with BOTH conditions. Separate
                # monitor heat/PM flags must never manufacture a joint exposure.
                union[:,i]=np.where(good,np.where(both,4,np.where(hot,2,np.where(dirty,3,1))),0)
            values=counts(union)
            products.append(save_product(f'heat-particulate-coexposure-{year}-{period}-{kind}',
                {**values,'cells':cells,'centers':np.array([h3_center(c) for c in cells]),'monitor_counts':np.array([np.sum(cell_ids==c) for c in cells])},
                {'family':'heat-particulate-coexposure','year':year,'period':period,'monitor_class':kind,
                 'data_through':str(dates(year,length)[-1]),'expected_days':length,'station_count':len(ss),
                 'grain':'union of eligible local cell-dates; BOTH requires both conditions at the same station/date; reference and low-cost kept separate',
                 'baseline':'CPC TMAX 1991–2020 P90; PM2.5 daily mean >35 µg/m³ comparison threshold',
                 'calendar':'PM Asia/Kolkata local dates joined to CPC date labels; CPC max_period 06Z–06Z; not simultaneous hourly exposure'}))
        for month in product_months():
            ix=[i for i,d in enumerate(dates(2025,cutoff)) if d.month==month]
            a=byyear[2025][0][ix][:,selected];b=byyear[2026][0][ix][:,selected];common=(a>0)&(b>0)
            matched.append({'monitor_class':kind,'month':month,'paired_station_days':int(common.sum()),
                    'both_2025':int(np.sum(common&(a==4))),'both_2026':int(np.sum(common&(b==4)))})
    path=OUTPUT/'data/india-station-days.csv.gz'
    with gzip.open(path,'wt',newline='') as f:
        writer=csv.writer(f);writer.writerow(['canonical_id','date','monitor_class','sensor_id','valid_hours','pm25_ug_m3','cpc_tmax_degC','tmax_p90_degC','state','eligibility']);writer.writerows(ledger)
    write_json(OUTPUT/'data/india-station-summary.json',station_summaries)
    write_json(OUTPUT/'data/india-comparisons.json',{'matched_months':matched,'threshold_and_date_sensitivity':sensitivity})
    write_json(OUTPUT/'data/india-products.json',products)
    station_diagnostics(stations)
    print(f'India completed: {n} monitors; {len(ledger)} audited source station-days',flush=True)


if __name__=='__main__':main()
