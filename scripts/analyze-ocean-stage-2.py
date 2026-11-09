#!/usr/bin/env python3
"""Baseline sensitivity and source-backed scientific review figures."""
from datetime import date
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree

from ocean_stage_2 import OUTPUT,OCEAN,ROOT,dates,slots,nonleap_indices,climatology,event_flags,thermal_seasons,SEASON_STATUS
from ocean_stage_2 import ocean_array
from ocean_temperature import digest,write_json
from viz_context import cutoff, matched_cutoff, product_months


def baseline_sensitivity():
    grid=dict(np.load(OCEAN/'work/grid.npz'));points=grid['centers']
    locations=[('Japan east',35,145),('North Atlantic',45,-30),('South Pacific',-35,-150),('Indian Ocean',-20,80),
               ('Equatorial Pacific',0,-140),('Mediterranean',35,18),('Australia west',-25,110),('South Atlantic',-30,-20)]
    def xyz(p):
        lat,lon=np.deg2rad(p).T;return np.column_stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])
    _,indices=cKDTree(xyz(points)).query(xyz(np.array([[lat,lon] for _,lat,lon in locations])))
    baselines={}
    for first,last in [(1991,2020),(1982,2011)]:
        a=np.stack([ocean_array(y)[:,indices][nonleap_indices(y)].T for y in range(first,last+1)],axis=1)
        baselines[first]=climatology(a)[:2]
    source=[ocean_array(y)[:,indices] for y in (2024,2025,2026)]
    all_days=dates(2024)+dates(2025)+dates(2026,len(source[-1]));a=np.concatenate(source).T
    rows=[]
    for year in (2025,2026):
        end=all_days.index(matched_cutoff(year))+1;start=all_days.index(date(year,1,1));flags={}
        for first,(mean,q) in baselines.items():flags[first]=event_flags(a[:,:end],q,all_days[:end])[:,start:]
        common=((flags[1991]&1)>0)&((flags[1982]&1)>0)&((flags[1991]&32)==0)&((flags[1982]&32)==0)
        for i,(name,lat,lon) in enumerate(locations):
            r={'location':name,'requested_latitude':lat,'requested_longitude':lon,'h3':f'{int(grid["cells"][indices[i]]):x}',
               'center':points[indices[i]].tolist(),'year':year,'common_eligible_days':int(common[i].sum())}
            for first in (1982,1991):
                q=baselines[first][1][i];finite=q[np.isfinite(q)]
                event=common[i]&((flags[first][i]&4)>0)
                r[f'event_days_baseline_{first}']=int(event.sum())
                r[f'mean_p90_baseline_{first}']=float(finite.mean()) if len(finite) else None
                anomaly=a[i,start:end]-baselines[first][0][i,slots(all_days[start:end])]
                r[f'cumulative_intensity_baseline_{first}_degC_days']=float(anomaly[event].sum(dtype='float64'))
            rows.append(r)
    write_json(OUTPUT/'data/baseline-sensitivity.json',{'scope':'eight nearest source-supported illustrative locations; not a global sensitivity estimate','rows':rows})


def method_examples():
    """Retain the exact daily series used by the event/season illustration."""
    examples=json.loads((OUTPUT/'data/baseline-sensitivity.json').read_text())['rows']
    selected=next(r for r in examples if r['location']=='Japan east' and r['year']==2026)
    cells=np.load(OCEAN/'work/grid.npz')['cells'];i=int(np.flatnonzero(cells==int(selected['h3'],16))[0])
    source=[ocean_array(y)[:,i] for y in (2024,2025,2026)]
    ds=dates(2024)+dates(2025)+dates(2026,len(source[-1]));values=np.concatenate(source)
    mean=np.load(OUTPUT/'work/baseline/mean.npy',mmap_mode='r')[i]
    q=np.load(OUTPUT/'work/baseline/threshold.npy',mmap_mode='r')[i]
    flags=event_flags(values[None,:],q[None,:],ds)[0]
    def number(value):return float(value) if np.isfinite(value) else None
    season={k:number(v[0]) for k,v in thermal_seasons(values[None,:],mean[None,:],ds,2026).items()}
    rows=[]
    for j,d in enumerate(ds):
        if d.year!=2026:continue
        s=slots([d])[0]
        rows.append({'date':d.isoformat(),'sst_degC':number(values[j]),'seasonal_mean_degC':number(mean[s]),
                     'p90_degC':number(q[s]),'event_flags':int(flags[j])})
    receipts={str((OCEAN/'work'/f'{y}.json').relative_to(ROOT)):digest(OCEAN/'work'/f'{y}.json') for y in (2024,2025,2026)}
    result={'location':selected['location'],'h3':selected['h3'],'center':selected['center'],
            'year':2026,'cutoff':str(cutoff()),'season':season,'season_status':SEASON_STATUS[int(season['status'])],
            'baseline_receipt_sha256':digest(OUTPUT/'data/baseline.json'),'source_receipts_sha256':receipts,'rows':rows}
    write_json(OUTPUT/'data/method-example.json',result)


def seasonal_sensitivity():
    grid=dict(np.load(OCEAN/'work/grid.npz'));n=len(grid['cells']);mean=np.load(OUTPUT/'work/baseline/mean.npy',mmap_mode='r')
    source=[ocean_array(y) for y in (2024,2025,2026)]
    ds=dates(2024)+dates(2025)+dates(2026,len(source[-1]));result=[]
    for year in (2025,2026):
        for gate in (1,3):
            counts=np.zeros(8,dtype='int64')
            for lo in range(0,n,4096):
                hi=min(n,lo+4096);v=np.concatenate([s[:,lo:hi] for s in source]).T.copy()
                values=thermal_seasons(v,mean[lo:hi],ds,year,amplitude=gate)
                counts+=np.bincount(values['status'].astype(int),minlength=8)
            result.append({'year':year,'minimum_amplitude_degC':gate,'status_counts':dict(zip(SEASON_STATUS,map(int,counts)))})
    write_json(OUTPUT/'data/season-amplitude-sensitivity.json',result)


def figures():
    folder=OUTPUT/'figures';folder.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.facecolor':'#240413','figure.facecolor':'#240413','savefig.facecolor':'#240413',
      'text.color':'#fff6e3','axes.labelcolor':'#fff6e3','xtick.color':'#fff6e3','ytick.color':'#fff6e3','svg.fonttype':'none'})
    sources=[]
    def read(name):
        path=OUTPUT/'data'/name;sources.append({'file':str(path.relative_to(OUTPUT)),'sha256':digest(path)})
        return json.loads(path.read_text())
    def finish(fig,name,caption):
        fig.text(.07,.025,caption,fontsize=9);fig.subplots_adjust(bottom=.18,top=.83,wspace=.3)
        for ax in fig.axes:
            ax.grid(axis='y',alpha=.18,color='white')
            for spine in ax.spines.values():spine.set_color('#9e8994')
        for ext in ('png','svg','pdf'):fig.savefig(folder/(name+'.'+ext),dpi=180)
        plt.close(fig)
        # Generated XML has no intentional trailing whitespace.
        svg=folder/(name+'.svg');svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
        write_json(folder/(name+'.json'),{'sources':sources.copy(),'outputs':{ext:digest(folder/(name+'.'+ext)) for ext in ('png','svg','pdf')}})
    marine=read('marine-matched-comparison.json')['months'];coastal=read('coastal-comparisons.json')['matched_months']
    india=[r for r in read('india-comparisons.json')['matched_months'] if r['monitor_class']=='reference']
    fig,axes=plt.subplots(1,3,figsize=(15,5));fig.suptitle('Matched daily support / 2025 and 2026',x=.07,ha='left',fontsize=19,color='#fcc553')
    for ax,rows,title,den in zip(axes,[marine,coastal,india],['Ocean event days','Coastal joint days','India reference-monitor joint days'],[None,'paired_pair_days','paired_station_days']):
        for year,color in [(2025,'#8da0cb'),(2026,'#fcc553')]:
            values=[100*r[f'event_fraction_{year}'] if den is None else 100*r[f'both_{year}']/r[den] if r[den] else np.nan for r in rows]
            ax.plot([r['month'] for r in rows],values,'o-',color=color,label=str(year),markersize=4)
        ax.set_title(title,color='#fcc553',fontsize=11);ax.set_ylabel('Percent of shared eligible days');ax.set_ylim(bottom=0)
        ax.set_xticks(list(product_months()),[__import__('calendar').month_abbr[m] for m in product_months()])
    leg=axes[0].legend(frameon=False)
    for text in leg.get_texts():text.set_color('#fff6e3')
    finish(fig,'matched-cooccurrence',f'Ocean cutoff {cutoff()}; coastal and India use their actual shorter shared eligible support. Different populations and grains; no pooled exposure score.')
    seasons=read('season-products.json');fig,ax=plt.subplots(figsize=(13,5));left=np.zeros(2)
    colors=['#6cbf9a','#948ca5','#514858','#a787bc','#c0a15d','#a1bacb','#fcc553','#db758e']
    for status,color in zip(SEASON_STATUS,colors):
        values=np.array([r['status_counts'][status] for r in seasons]);ax.barh([0,1],values,left=left,color=color,label=status);left+=values
    ax.set_yticks([0,1],['2025 season','2026 season']);ax.set_xlabel('Source-supported H3 cells (counts, not ocean-area percentages)')
    ax.set_title('Season definitions and observation limits',loc='left',color='#fcc553',fontsize=17)
    fig.subplots_adjust(right=.70)
    leg=ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=9,frameon=False)
    for text in leg.get_texts():text.set_color('#fff6e3')
    finish(fig,'season-coverage',f'Warm-peak year labels; ocean observations through {cutoff()}. An open season has no observed final length. Weak/multiple cycles remain undefined.')
    stations=read('india-station-summary.json');selected=[r for r in stations if r['monitor_class']=='reference' and r['year']==2026 and r['period']=='annual']
    selected.sort(key=lambda r:r['eligible_days']);ids=[r['id'] for r in selected]
    old={r['id']:r for r in stations if r['monitor_class']=='reference' and r['year']==2025 and r['period']=='matched'}
    fig,ax=plt.subplots(figsize=(13,9));yy=np.arange(len(ids))
    for shift,rows,color,label in [(-.17,[old[i] for i in ids],'#8da0cb','2025 matched'),(.17,selected,'#fcc553','2026 eligible window')]:
        ax.barh(yy+shift,[100*r['eligible_days']/r['expected_days'] for r in rows],height=.32,color=color,label=label)
    ax.set_yticks(yy,[r['name']+' / '+r['id'] for r in selected],fontsize=8);ax.set_xlim(0,100);ax.axvline(80,color='#fff6e3',linestyle=':',linewidth=1)
    ax.set_xlabel('Joint eligible station-days / labeled calendar window (%)');ax.set_title('India reference-monitor coverage',loc='left',fontsize=17,color='#fcc553')
    leg=ax.legend(loc='lower right',frameon=False)
    for text in leg.get_texts():text.set_color('#fff6e3')
    fig.subplots_adjust(left=.40)
    finish(fig,'india-station-coverage','Selected stations only. Dotted line: 80% display gate. Year comparisons of joint heat–PM days use the same station and calendar-date pairs.')
    sample=read('method-example.json');rows=sample['rows'];x=np.array([date.fromisoformat(r['date']) for r in rows])
    sst=np.array([r['sst_degC'] for r in rows]);mean=np.array([r['seasonal_mean_degC'] for r in rows]);q=np.array([r['p90_degC'] for r in rows]);flags=np.array([r['event_flags'] for r in rows])
    fig,axes=plt.subplots(1,2,figsize=(15,5.8));fig.suptitle('Two different measures / Japan east, 2026',x=.07,ha='left',fontsize=18,color='#fcc553')
    for ax in axes:
        ax.plot(x,sst,color='#fcc553',linewidth=1,label='Observed daily SST')
        ax.plot(x,mean,color='#8da0cb',linewidth=1.3,label='1991–2020 seasonal mean')
        ax.set_ylabel('Temperature (°C)');ax.set_xlim(x[0],x[-1]);ax.tick_params(axis='x',rotation=25)
    axes[0].plot(x,q,color='#db758e',linewidth=1.2,label='Seasonal 90th percentile')
    axes[0].fill_between(x,sst,mean,where=(flags&4)>0,color='#fcc553',alpha=.28,label='Confirmed event span / intensity')
    axes[0].set_title('Five-day events, observed gaps ≤2 days',color='#fcc553',fontsize=11)
    season=sample['season'];axes[1].axhline(season['threshold'],color='#a7d5b9',linestyle='--',label='Local warm-season midpoint')
    axes[1].set_title('Seven-day persistent seasonal transitions',color='#fcc553',fontsize=11)
    for ax in axes:
        leg=ax.legend(loc='upper left',fontsize=8,frameon=False)
        for text in leg.get_texts():text.set_color('#fff6e3')
    detail=f"H3 {sample['h3']}; {sample['center'][0]:.2f}°N, {sample['center'][1]:.2f}°E. Season status: {sample['season_status']}."
    if season['onset_departure'] is not None:detail+=f" Onset departure: {season['onset_departure']:+.0f} days."
    if season['length'] is not None:detail+=f" Completed length: {season['length']:.0f} days."
    finish(fig,'event-season-example',detail+f'\nDaily ocean observations end {cutoff()}; shading includes observed joined gaps. This location illustrates definitions, not a regional estimate.')


if __name__=='__main__':
    baseline_sensitivity();seasonal_sensitivity();method_examples();figures()
    print('Baseline/season sensitivity and four scientific figures complete',flush=True)
