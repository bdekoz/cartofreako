#!/usr/bin/env python3
"""Independent data calculations, full ledger checks, and sheet receipts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date,datetime,timedelta
import gzip
import json
from pathlib import Path
import re

import geopandas as gpd
from lxml import etree as E
import numpy as np
import pandas as pd
from PIL import Image
import shapely as shp

from ocean_stage_2 import ROOT,OUTPUT,OCEAN,CONFIG,dates,nonleap_indices,NetCDF,cpc_path
from ocean_stage_2 import ocean_array
from ocean_temperature import digest,write_json
from viz_context import cutoff


def reference_climate(years):
    """Independent NumPy implementation; does not call the compiled kernel."""
    raw_mean=np.full(366,np.nan);raw_q=np.full(366,np.nan)
    for d in range(365):
        pool=np.asarray(years[:,[(d+k)%365 for k in range(-5,6)]],dtype='float64')
        valid=np.isfinite(pool)
        if np.sum(np.any(valid,axis=1))<24 or valid.sum()<264:continue
        s=d if d<59 else d+1
        raw_mean[s]=pool[valid].mean();raw_q[s]=np.quantile(pool[valid],.9,method='linear')
    for a in (raw_mean,raw_q):a[59]=(a[58]+a[60])/2
    return tuple(np.convolve(np.pad(a,(15,15),mode='wrap'),np.ones(31)/31,mode='valid') for a in (raw_mean,raw_q))


def reference_events(values,q,mean,ds,first):
    slot=np.array([(d.replace(year=2000)-date(2000,1,1)).days for d in ds]);threshold=q[slot]
    valid=np.isfinite(values)&np.isfinite(threshold);hot=valid&(values>threshold)
    transitions=np.diff(np.r_[False,hot,False].astype(int));starts=np.flatnonzero(transitions==1);ends=np.flatnonzero(transitions==-1)-1
    spans=[];pending=np.zeros(len(ds),bool)
    for s,e in zip(starts,ends):
        if e-s+1<5:
            if s==0 or e==len(ds)-1 or not valid[s-1] or not valid[e+1]:pending[s:e+1]=True
            continue
        if spans and s-spans[-1][1]-1<=2 and valid[spans[-1][1]+1:s].all():spans[-1]=(spans[-1][0],e)
        else:spans.append((s,e))
    mask=np.zeros(len(ds),bool);longest=0
    for s,e in spans:
        mask[s:e+1]=True
        if e>=first:longest=max(longest,e-max(s,first)+1)
    return {'eligible_days':int((valid[first:]&~pending[first:]).sum()),'observed_days':int(valid[first:].sum()),
       'pending_days':int(pending[first:].sum()),'event_days':int(mask[first:].sum()),'longest_duration':longest,
       'exceedance_days':int(hot[first:].sum()),'cumulative_intensity':float(np.where(mask[first:],values[first:]-mean[slot[first:]],0).sum(dtype='float64'))}


def verify_sources():
    tasks=[]
    for year in range(1982,2027):
        receipt=json.loads((OCEAN/'work'/f'{year}.json').read_text());tasks.append((OCEAN/'work'/f'{year}.npy',receipt['sha256']))
    for row in json.loads((OUTPUT/'data/cpc-inputs.json').read_text())['inputs']:tasks.append((ROOT/row['path'],row['sha256']))
    for row in json.loads((OUTPUT/'data/stage-2-acquisition.json').read_text())['inputs']:tasks.append((OUTPUT/row['file'],row['sha256']))
    def check(item):
        p,h=item;assert digest(p)==h,str(p);return str(p)
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(check,tasks))
    return len(tasks)


def ocean_checks():
    grid=dict(np.load(OCEAN/'work/grid.npz'));n=len(grid['cells'])
    # Eight geographical examples plus a systematic sample spanning H3 order.
    sensitivity=json.loads((OUTPUT/'data/baseline-sensitivity.json').read_text())['rows']
    bank={int(c):i for i,c in enumerate(grid['cells'])};indices=sorted(set([bank[int(r['h3'],16)] for r in sensitivity]+list(np.linspace(0,n-1,12,dtype=int))))
    inputs=[ocean_array(y) for y in range(1991,2021)]
    mean=np.load(OUTPUT/'work/baseline/mean.npy',mmap_mode='r');q=np.load(OUTPUT/'work/baseline/threshold.npy',mmap_mode='r')
    refs={}
    for i in indices:
        x=np.stack([a[nonleap_indices(y),i] for a,y in zip(inputs,range(1991,2021))]);refs[i]=reference_climate(x)
        for actual,expected in [(mean[i],refs[i][0]),(q[i],refs[i][1])]:np.testing.assert_allclose(actual,expected,atol=4e-6,rtol=0,equal_nan=True)
    ds=dates(2024)+dates(2025)+dates(2026,(cutoff()-date(2026,1,1)).days+1)
    target=np.concatenate([ocean_array(y)[:,indices] for y in (2024,2025,2026)])
    products=json.loads((OUTPUT/'data/marine-products.json').read_text());ledgers=0
    for meta in products:
        a=dict(np.load(OUTPUT/'data'/meta['data_file']));end=ds.index(date.fromisoformat(meta['data_through']))+1;first=ds.index(date(meta['year'],1,1))
        for j,i in enumerate(indices):
            # Use stored float32 climatology for strict comparisons, after its
            # independent higher-precision check, to preserve exact ties.
            expected=reference_events(target[:end,j],q[i],mean[i],ds[:end],first)
            for k,v in expected.items():np.testing.assert_allclose(a[k][i],v,atol=1e-4 if k=='cumulative_intensity' else 0,rtol=0)
        path=OUTPUT/'data'/meta['event_ledger'];assert digest(path)==meta['event_ledger_sha256']
        ledger=pd.read_csv(path);ledgers+=len(ledger);assert len(ledger)==meta['event_count']
        grouped=ledger.groupby('h3').agg(days=('days_in_period','sum'),longest=('days_in_period','max'),intensity=('intensity_in_period_degC_days','sum'))
        grouped=grouped.reindex([f'{int(c):x}' for c in a['cells']],fill_value=0)
        np.testing.assert_array_equal(grouped.days,a['event_days']);np.testing.assert_array_equal(grouped.longest,a['longest_duration'])
        np.testing.assert_allclose(grouped.intensity,a['cumulative_intensity'],atol=1e-4,rtol=1e-8)
        assert np.all(a['event_days']<=a['eligible_days']);assert np.all(a['eligible_days']+a['pending_days']==a['observed_days'])
    return {'independent_calendar_baselines':len(indices),'independent_cell_periods':len(indices)*len(products),'reconciled_event_rows':ledgers}


def season_checks():
    """Independent run-table calculation on actual Northern/Southern cells."""
    def transitions(values,threshold,persistence=7):
        candidates=[]
        for state,mask in [(1,values>threshold),(0,values<threshold)]:
            changes=np.diff(np.r_[False,mask,False].astype(int))
            for start,end in zip(np.flatnonzero(changes==1),np.flatnonzero(changes==-1)):
                if end-start>=persistence:candidates.append((start,state))
        warm=False;onsets=[];ends=[]
        for start,state in sorted(candidates):
            if state and not warm:onsets.append(start);warm=True
            elif not state and warm:ends.append(start);warm=False
        return onsets,ends
    def calculate(values,mean,ds,year):
        from ocean_stage_2 import SEASON_FIELDS
        result={key:np.nan for key in SEASON_FIELDS};result['status']=2
        if not np.isfinite(mean).all():return result
        cool=int(np.argmin(mean));peak=int(np.argmax(mean));amplitude=mean[peak]-mean[cool];threshold=(mean[peak]+mean[cool])/2
        result.update(amplitude=amplitude,threshold=threshold)
        if amplitude<2:result['status']=1;return result
        starts,ends=transitions(np.roll(mean,-cool),threshold)
        if len(starts)!=1 or not ends or ends[0]<starts[0]:result['status']=3;return result
        baseyear=year if cool<peak else year-1
        def calendar(offset):
            offset=int(offset)
            slot=(cool+offset)%366;y=baseyear+(cool+offset)//366;d=date(2000,1,1)+timedelta(days=slot)
            try:return d.replace(year=y)
            except ValueError:return date(y,2,28)
        first,last=calendar(0),calendar(366);start=(first-ds[0]).days;stop=(last-ds[0]).days
        begin=max(0,start);end=min(len(ds),stop);sample=values[begin:end];finite=np.isfinite(sample)
        result.update(baseline_onset_slot=(cool+starts[0])%366,baseline_end_slot=(cool+ends[0])%366,
                      observed_warm_days=int(np.sum(sample>threshold)),valid_days=int(finite.sum()),available_days=len(sample))
        missing=np.flatnonzero(~finite);bad=int(missing[0]) if len(missing) else None
        observed,finished=transitions(sample,threshold)
        if start<0 or (bad is not None and (not observed or bad<observed[0]+7)):result['status']=5;return result
        if not observed:result['status']=4;return result
        if len(observed)>1:result['status']=7;return result
        departure=(ds[begin+observed[0]]-calendar(starts[0])).days;cycle=(last-first).days
        while departure>cycle//2:departure-=cycle
        while departure<-(cycle//2):departure+=cycle
        result['onset_departure']=departure
        if bad is not None and (not finished or bad<finished[0]+7):result.update(status=5,onset_departure=np.nan);return result
        if not finished:result['status']=6;return result
        length=finished[0]-observed[0]
        result.update(status=0,length=length,length_departure=length-(calendar(ends[0])-calendar(starts[0])).days)
        return result
    grid=dict(np.load(OCEAN/'work/grid.npz'));bank={int(c):i for i,c in enumerate(grid['cells'])}
    samples=json.loads((OUTPUT/'data/baseline-sensitivity.json').read_text())['rows']
    indices=sorted(set([bank[int(r['h3'],16)] for r in samples]+list(np.linspace(0,len(bank)-1,12,dtype=int))))
    values=np.concatenate([ocean_array(y)[:,indices] for y in (2024,2025,2026)])
    ds=dates(2024)+dates(2025)+dates(2026,(cutoff()-date(2026,1,1)).days+1);mean=np.load(OUTPUT/'work/baseline/mean.npy',mmap_mode='r')
    for year in (2025,2026):
        actual=dict(np.load(OUTPUT/'data'/f'ocean-thermal-season-{year}.npz'))
        for column,i in enumerate(indices):
            expected=calculate(values[:,column],mean[i],ds,year)
            for key,value in expected.items():np.testing.assert_allclose(actual[key][i],value,atol=2e-6,rtol=0,equal_nan=True,err_msg=f'{year}/{i}/{key}')
    return {'independent_season_cell_years':2*len(indices)}


def coastal_checks():
    p=dict(np.load(OUTPUT/'data/coastal-pairing.npz'));meta=json.loads((OUTPUT/'data/coastal-pairing.json').read_text())
    assert digest(OUTPUT/'data/coastal-pairing.npz')==meta['pairing_sha256']
    for name,sha in meta['source_geometries'].items():assert digest(ROOT/name)==sha
    from viz_context import input_path
    folder=input_path('NATURAL_EARTH_DIR', ROOT/'assets.static/natural-earth/10m-physical-vectors')
    land=shp.union_all(gpd.read_file(folder/'ne_10m_land.shp').geometry.to_numpy());shp.prepare(land)
    ocean=gpd.read_file(folder/'ne_10m_ocean.shp').geometry.iloc[0];shp.prepare(ocean)
    assert np.all(shp.contains_xy(land,p['centers'][:,1],p['centers'][:,0]))
    assert np.all(p['distance_km']<=100)
    ids=p['members'];op=p['ocean_centers'][ids];shore=np.repeat(p['shore'],np.diff(p['offsets']),axis=0)
    assert np.all(shp.contains_xy(ocean,op[:,1],op[:,0]))
    assert np.all(np.abs(op[:,1]-shore[:,1])<180)
    # Separate vector geometry evaluation of every saved line of sight.
    origin=shore[:,::-1];end=op[:,::-1];start=origin+(end-origin)*1e-5
    for lo in range(0,len(ids),10000):
        lines=shp.linestrings(np.stack([start[lo:lo+10000],end[lo:lo+10000]],axis=1))
        assert not np.any(shp.intersects(land,lines))
    weights=np.load(OCEAN/'work/grid.npz')['weights'];chosen=np.linspace(0,len(p['centers'])-1,8,dtype=int)
    for year in (2025,2026):
        computed=np.load(OUTPUT/'work/coastal'/f'ocean100-{year}.npy',mmap_mode='r')
        ocean_daily=np.load(OCEAN/'work'/f'{year}.npy',mmap_mode='r')[:len(computed)]
        native=np.load(OUTPUT/'work/coastal'/f'land-{year}.npy',mmap_mode='r')
        with NetCDF(cpc_path(year)) as nc:
            for i in chosen:
                members=p['members'][p['offsets'][i]:p['offsets'][i+1]];v=ocean_daily[:,members];expected=np.sum(v*weights[members],axis=1)/weights[members].sum()
                np.testing.assert_allclose(computed[:,i],expected,atol=4e-6,rtol=0,equal_nan=True)
                index=int(p['native_indices'][i]);raw=nc.read('tmax',(0,index//720,index%720),(len(native),1,1)).ravel()
                np.testing.assert_array_equal(raw,native[:,i])
    for kind in ('land','ocean100'):
        baseline=np.load(OUTPUT/'work/coastal'/(kind+'-baseline.npz'))['threshold']
        for i in chosen[:4]:
            years=np.stack([np.load(OUTPUT/'work/coastal'/f'{kind}-{y}.npy',mmap_mode='r')[nonleap_indices(y),i] for y in range(1991,2021)])
            _,q=reference_climate(years);np.testing.assert_allclose(baseline[i],q,atol=5e-6,rtol=0,equal_nan=True)
    for m in json.loads((OUTPUT/'data/coastal-products.json').read_text()):
        a=dict(np.load(OUTPUT/'data'/m['data_file']));assert np.all(a['both_days']<=a['eligible_days'])
        np.testing.assert_array_equal(sum(a[k] for k in ('neither_days','land_only_days','other_only_days','both_days')),a['eligible_days'])
        np.testing.assert_array_equal(a['eligible_days']+a['invalid_days'],np.full(len(a['cells']),m['expected_days']))
    return {'coastal_pairs':len(p['cells']),'line_of_sight_memberships':len(ids),'independent_pair_years':16,'independent_land_ocean_baselines':8}


def india_checks():
    cross=json.loads((OUTPUT/'data/india-station-crosswalk.json').read_text());assert digest(ROOT/cross['source'])==cross['source_sha256']
    ledger=pd.read_csv(OUTPUT/'data/india-station-days.csv.gz');assert not ledger.duplicated(['canonical_id','date']).any()
    expected=np.where((ledger.valid_hours>=18)&ledger.cpc_tmax_degC.notna()&ledger.tmax_p90_degC.notna(),
        1+(ledger.cpc_tmax_degC>ledger.tmax_p90_degC).astype(int)+2*(ledger.pm25_ug_m3>35).astype(int),0)
    np.testing.assert_array_equal(expected,ledger.state)
    assert set(ledger.monitor_class)=={'reference','low-cost'}
    stations={s['id']:s for s in cross['stations']};checked=[]
    with NetCDF(cpc_path(2026)) as nc:
        lat,lon=nc.read('lat'),nc.read('lon')
        for station in stations.values():
            i=station['native_index'];center=[float(lat[i//720]),float((lon[i%720]+180)%360-180)]
            np.testing.assert_allclose(station['cpc_center'],center,atol=1e-6,rtol=0)
            assert abs(station['latitude']-center[0])<=.25 and abs(station['longitude']-center[1])<=.25
            a,b=np.deg2rad([station['latitude'],center[0]]);dlon=np.deg2rad(station['longitude']-center[1])
            distance=6371.0088*np.arccos(np.clip(np.sin(a)*np.sin(b)+np.cos(a)*np.cos(b)*np.cos(dlon),-1,1))
            np.testing.assert_allclose(station['cpc_center_distance_km'],distance,atol=1e-6,rtol=0)
    monthly=json.loads((OUTPUT/'data/india-station-monthly-coverage.json').read_text())
    assert monthly['station_ledger_sha256']==digest(OUTPUT/'data/india-station-days.csv.gz')
    groups=pd.DataFrame(monthly['rows']).groupby(['id','year','period']).sum(numeric_only=True)
    for row in json.loads((OUTPUT/'data/india-station-summary.json').read_text()):
        sums=groups.loc[(row['id'],row['year'],row['period'])]
        for key in ('expected_days','eligible_days','invalid_days','neither_days','heat_only_days','pm_only_days','both_days'):assert sums[key]==row[key]
    for sid in sorted(stations)[::4]:
        rows=ledger[(ledger.canonical_id==sid)&(ledger.valid_hours>=18)]
        for year in ('2025','2026'):
            group=rows[rows.date.str.startswith(year)]
            if group.empty:continue
            row=group.iloc[-1];s=stations[sid]
            from dataset import binding, context
            raw_folder=(binding('INDIA_METADATA').parent/'openaq/raw' if context(required=False)
                        else ROOT/'output/india-particulate-20261108/enrichment/openaq/raw')
            # Archive file labels are not observation calendars. In particular,
            # an AirNow midnight can appear in the preceding day's archive.
            raw_paths=[raw_folder/f'location-{s["openaq_id"]}-{(date.fromisoformat(row.date)+timedelta(days=k)):%Y%m%d}.csv.gz' for k in (-1,0,1)]
            raw_paths=[p for p in raw_paths if p.exists()]
            frame=pd.concat([pd.read_csv(raw) for raw in raw_paths],ignore_index=True);frame=frame[(frame.parameter=='pm25')&(frame.sensors_id==row.sensor_id)]
            frame['local']=pd.to_datetime(frame.datetime,utc=True).dt.tz_convert('Asia/Kolkata')
            frame=frame[frame.local.dt.strftime('%Y-%m-%d')==row.date];frame=frame[(frame.value>=0)&np.isfinite(frame.value)]
            # Reject conflicting duplicate timestamps, then average readings
            # within a local hour and give each distinct hour equal weight.
            bad=frame.groupby('datetime').value.transform('nunique')>1;frame=frame[~bad].drop_duplicates('datetime')
            hourly=frame.groupby(frame.local.dt.floor('h')).value.mean()
            assert len(hourly)==row.valid_hours
            np.testing.assert_allclose(hourly.mean(),row.pm25_ug_m3,atol=1e-5,rtol=0)
            with NetCDF(cpc_path(int(year))) as nc:
                d=(date.fromisoformat(row.date)-date(int(year),1,1)).days;idx=s['native_index']
                temperature=nc.read('tmax',(d,idx//720,idx%720),(1,1,1)).item()
                np.testing.assert_allclose(temperature,row.cpc_tmax_degC,atol=1e-6)
            checked.append({'station':sid,'date':row.date,'hours':len(hourly),'raw_sha256':{raw.name:digest(raw) for raw in raw_paths}})
    # Matched calendar dates must use the same canonical monitor on both sides.
    eligible=ledger[ledger.state>0].copy();eligible['month_day']=eligible.date.str[5:]
    a=eligible[eligible.date.str.startswith('2025')];b=eligible[eligible.date.str.startswith('2026')]
    paired=a.merge(b,on=['canonical_id','month_day','monitor_class'],suffixes=('_2025','_2026'),validate='one_to_one')
    for row in json.loads((OUTPUT/'data/india-comparisons.json').read_text())['matched_months']:
        p=paired[(paired.monitor_class==row['monitor_class'])&(paired.month_day.str[:2].astype(int)==row['month'])]
        assert len(p)==row['paired_station_days']
        for year in (2025,2026):assert int(np.sum(p[f'state_{year}']==4))==row[f'both_{year}']
    return {'station_day_rows':len(ledger),'canonical_monitors':len(stations),'station_month_coverage_rows':len(monthly['rows']),
            'independent_hourly_checks':checked,'matched_station_days':len(paired)}


def sheet_checks():
    from dataset import context
    selected=context(required=False)
    registry=selected[1]['registry'] if selected else json.loads((ROOT/'config/data-products.json').read_text())
    definitions=registry['optional_families']
    expected_views=sum(len(f['periods'])*(sum(len(metrics) for metrics in f['classes'].values())
                       if 'classes' in f else len(f['metrics'])) for f in definitions.values())
    manifest=json.loads((OUTPUT/'preview-manifest.json').read_text());records=manifest['records'];assert len(records)==4*expected_views
    keys=[(r['stem'],r['metric'],r['period'],r['monitor_class'],r['scope'],r['kind']) for r in records]
    assert len(set(keys))==4*expected_views
    assert all((*key[:-1], 'legend' if key[-1]=='map' else 'map') in keys for key in keys)
    for r in records:
        for k in ('svg','pdf','preview'):assert digest(OUTPUT/r[k])==r[k+'_sha256'],r[k]
        assert (OUTPUT/r['pdf']).read_bytes().startswith(b'%PDF-')
        tree=E.parse(str(OUTPUT/r['svg']),E.XMLParser(huge_tree=True))
        for node in tree.xpath('//*[local-name()="image"]'):
            href=node.get('{http://www.w3.org/1999/xlink}href') or node.get('href')
            if href and not href.startswith('data:'):assert ((OUTPUT/r['svg']).parent/href).resolve().exists(),href
        with Image.open(OUTPUT/r['preview']) as im:
            assert im.width==(1920 if r['kind']=='map' else 2200)
            assert im.height>500
        if r['kind']=='map':
            assert not tree.xpath('//*[@id="cpc-temperature-record-high-days" or @id="cpc-temperature-record-low-days"]')
            companion=tree.getroot().get('data-legend-companion');assert ((OUTPUT/r['svg']).parent/companion).resolve().exists()
    index=(OUTPUT/'index.html').read_text();links=re.findall(r'(?:href|src)="([^"#]+)"',index)
    for link in links:
        if not re.match(r'\w+://',link):
            if link=='validation.json':continue
            assert (OUTPUT/link).resolve().exists(),link
    for product in manifest['products']:
        meta=product['metadata'];assert digest(OUTPUT/'data'/meta['data_file'])==meta['sha256']
    figures=list((OUTPUT/'figures').glob('*.json'));assert len(figures)==4
    for receipt in figures:
        f=json.loads(receipt.read_text())
        for source in f['sources']:assert digest(OUTPUT/source['file'])==source['sha256']
        for ext,sha in f['outputs'].items():assert digest(receipt.with_suffix('.'+ext))==sha
    return {'exported_sheets':len(records),'measure_period_views':len(manifest['products']),'scientific_figures':len(figures),'index_links_checked':len(links)}


def provenance():
    return {'method_config_sha256':digest(CONFIG),'checked_at':datetime.now().astimezone().isoformat(),
       'implementation_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [
           *[ROOT/'scripts'/name for name in ('ocean_stage_2.py','ocean-stage-2-kernels.cc','project-stage-2-points.cc',
               'prepare-ocean-climate-baseline.py','prepare-marine-heatwaves.py','prepare-ocean-thermal-seasons.py',
               'prepare-coastal-compound-heat.py','prepare-heat-particulate-coexposure.py')],
           *sorted((ROOT/'scripts').glob('*stage-2*.py')),ROOT/'tests/test-ocean-stage-2.py']}}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-only',action='store_true');p.add_argument('--exports-only',action='store_true');a=p.parse_args()
    if a.exports_only:
        result=json.loads((OUTPUT/'validation-data.json').read_text())
        assert result['status']=='passed' and result['method_config_sha256']==digest(CONFIG)
        result.update(sheet_checks())
    else:
        result={'status':'passed','source_files_verified':verify_sources()};print('Source hashes verified',flush=True)
        for check in (ocean_checks,season_checks,coastal_checks,india_checks):result.update(check());print(check.__name__+' passed',flush=True)
        write_json(OUTPUT/'validation-data.json',{**result,'data_only':True,**provenance()})
        if not a.data_only:result.update(sheet_checks())
    result.update(data_only=a.data_only,**provenance())
    write_json(OUTPUT/('validation-data.json' if a.data_only else 'validation.json'),result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('implementation_sha256','independent_hourly_checks')},indent=2),flush=True)


if __name__=='__main__':main()
