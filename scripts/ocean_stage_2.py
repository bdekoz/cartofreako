"""Stage 2 shared dates, pinned parameters and compiled scientific kernels."""
from __future__ import annotations

import ctypes as C
from datetime import date, timedelta
import json
import os
from pathlib import Path
import subprocess

import numpy as np

from ocean_temperature import NetCDF, digest, write_json

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'output/ocean-temperature-stage-2-20261108'
OCEAN = ROOT/'output/ocean-temperature-20261108'
CONFIG = ROOT/'config/ocean-stage-2-20261108.json'


def config():
    value=json.loads(CONFIG.read_text())
    fixed={'baseline':[1991,2020],'calendar_window_days':11,'circular_smoothing_days':31,
           'percentile':90,'quantile_interpolation':'linear','minimum_baseline_years':24,
           'minimum_baseline_samples_fraction':.8,'minimum_period_coverage':.8,'h3_resolution':5}
    if any(value[k]!=v for k,v in fixed.items()):
        raise ValueError('This method version requires the pinned Stage 2 parameters; implement and validate a new method version before changing them')
    nested={
        'marine_heatwave':{'minimum_consecutive_days':5,'maximum_observed_gap_days':2},
        'thermal_season':{'minimum_amplitude_degC':2,'persistence_days':7,'sensitivity_amplitudes_degC':[1,3],'sensitivity_persistence_days':[5,10]},
        'coastal':{'maximum_land_to_coast_km':100,'ocean_neighborhood_km':100,'sensitivity_distance_km':50},
        'particulate':{'daily_pm25_comparison_ug_m3':35,'minimum_distinct_hours':18,'sensitivity_thresholds_ug_m3':[25,50],'timezone':'Asia/Kolkata'}}
    if any(value[group][k]!=v for group,settings in nested.items() for k,v in settings.items()):
        raise ValueError('The implementation requires the pinned event, season, coastal and particulate parameters')
    return value


def dates(year, count=None):
    start=date(year,1,1)
    return [start+timedelta(days=i) for i in range(count if count is not None else (date(year+1,1,1)-start).days)]


def slots(days):
    return np.array([(d.replace(year=2000)-date(2000,1,1)).days for d in days],dtype='int32')


def nonleap_indices(year):
    return [i for i,d in enumerate(dates(year)) if (d.month,d.day)!=(2,29)]


def kernel():
    config()
    source=ROOT/'scripts/ocean-stage-2-kernels.cc'
    target=ROOT/'build/ocean-stage-2-kernels.so'
    receipt=target.with_suffix('.json')
    key={'source':digest(source),'flags':['-O3','-std=c++17','-fopenmp','-shared','-fPIC']}
    if not target.exists() or not receipt.exists() or json.loads(receipt.read_text())!=key:
        subprocess.run(['g++',*key['flags'],str(source),'-o',str(target)],check=True)
        write_json(receipt,key)
    os.environ.setdefault('OMP_NUM_THREADS','12')
    lib=C.CDLL(str(target))
    lib.climate.argtypes=[C.c_int,C.c_int]+[C.c_void_p]*5
    lib.events.argtypes=[C.c_int,C.c_int]+[C.c_void_p]*4
    lib.seasons.argtypes=[C.c_int,C.c_int,C.c_void_p,C.c_void_p,C.c_void_p,C.c_int,C.c_float,C.c_void_p]
    return lib


def climatology(data):
    """Input cell × baseline year × nonleap calendar day; outputs cell × 366.

    Linear 90th percentile of 11-day circular calendar samples, then a
    31-day circular mean. February 29 is interpolated before smoothing.
    Every pooled window needs 24 years and 80% of its expected samples;
    smoothing requires every constituent window, with no NaN interpolation.
    """
    a=np.ascontiguousarray(data,dtype='float32')
    assert a.ndim==3 and a.shape[2]==365
    n,y,_=a.shape
    mean=np.empty((n,366),dtype='float32');q=np.empty_like(mean)
    count=np.empty((n,366),dtype='uint16');years=np.empty((n,366),dtype='uint8')
    kernel().climate(n,y,*[x.ctypes.data for x in (a,mean,q,count,years)])
    return mean,q,count,years


def event_flags(values, threshold, days):
    a=np.ascontiguousarray(values,dtype='float32');q=np.ascontiguousarray(threshold,dtype='float32')
    s=slots(days);out=np.empty(a.shape,dtype='uint8')
    assert a.shape[1]==len(days) and q.shape==(len(a),366)
    kernel().events(len(a),len(days),*[x.ctypes.data for x in (a,q,s,out)])
    return out


def event_edges(flags,start,end):
    left=start==0 or not bool(flags[start-1]&1)
    following=flags[end+1:min(end+4,len(flags))]
    right=end>=len(flags)-3 or not np.all((following&1)>0) or np.any((following&32)>0)
    return bool(left),bool(right)


SEASON_FIELDS=['amplitude','threshold','baseline_onset_slot','baseline_end_slot','onset_departure',
               'length','length_departure','observed_warm_days','valid_days','available_days','status']
SEASON_STATUS=['complete','weak seasonal amplitude','incomplete climatology','multiple baseline seasons',
               'onset not observed','missing transition support','open season','multiple observed seasons']


def thermal_seasons(values,mean,days,year,persistence=7,amplitude=2):
    a=np.ascontiguousarray(values,dtype='float32');m=np.ascontiguousarray(mean,dtype='float32')
    calendar=np.empty((3,366),dtype='int32')
    for iy,y in enumerate((year-1,year,year+1)):
        for s,d in enumerate(dates(2000)):
            try:target=d.replace(year=y)
            except ValueError:target=date(y,2,28)
            calendar[iy,s]=(target-days[0]).days
    out=np.empty((len(a),11),dtype='float32')
    kernel().seasons(len(a),len(days),a.ctypes.data,m.ctypes.data,calendar.ctypes.data,
                     persistence,amplitude,out.ctypes.data)
    return {k:out[:,i] for i,k in enumerate(SEASON_FIELDS)}


def cpc_path(year):
    refreshed=OUTPUT/'cache/cpc'/f'tmax.{year}.nc'
    return refreshed if refreshed.exists() else ROOT/'assets.static/anthropocene/.raw/cpc'/f'tmax.{year}.nc'


def cpc_dates(nc):
    assert nc.attributes('time')['units']=='hours since 1900-01-01 00:00:00'
    result=[date(1900,1,1)+timedelta(hours=float(x)) for x in nc.read('time')]
    assert all(b-a==timedelta(days=1) for a,b in zip(result,result[1:]))
    return result


def save_product(name, arrays, metadata):
    path=OUTPUT/'data'/(name+'.npz');path.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(path,**arrays)
    meta={'schema':'cartofreako-ocean-stage-2-product-v1','snapshot_as_of':'2026-11-08',
          'method_config_sha256':digest(CONFIG),'data_file':path.name,'sha256':digest(path),**metadata}
    write_json(path.with_suffix('.json'),meta)
    return meta
