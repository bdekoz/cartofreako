#!/usr/bin/env python3
"""Compute the pinned 1991–2020 local seasonal mean and percentile in chunks."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from ocean_stage_2 import ROOT,OUTPUT,OCEAN,CONFIG,climatology,nonleap_indices
from ocean_temperature import digest,write_json


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--chunk',type=int,default=4096)
    p.add_argument('--limit',type=int);a=p.parse_args()
    out=OUTPUT/'work/baseline';out.mkdir(parents=True,exist_ok=True)
    grid=np.load(OCEAN/'work/grid.npz');n=len(grid['cells'])
    inputs=[json.loads((OCEAN/'work'/f'{y}.json').read_text()) for y in range(1991,2021)]
    climate_code=(ROOT/'scripts/ocean-stage-2-kernels.cc').read_text().split('// Flags:')[0]
    key={'config_sha256':digest(CONFIG),'climatology_kernel_sha256':hashlib.sha256(climate_code.encode()).hexdigest(),
         'source_arrays':[r['sha256'] for r in inputs],'grid_sha256':digest(OCEAN/'work/grid.npz')}
    write_json(out/'inputs.json',key)
    arrays=[np.load(OCEAN/'work'/f'{y}.npy',mmap_mode='r') for y in range(1991,2021)]
    indices=[nonleap_indices(y) for y in range(1991,2021)]
    start=time.monotonic()
    for lo in range(0,min(n,a.limit or n),a.chunk):
        hi=min(lo+a.chunk,n);path=out/f'{lo:06d}-{hi:06d}.npz';receipt=path.with_suffix('.json')
        if path.exists() and receipt.exists():
            old=json.loads(receipt.read_text())
            if old['inputs']==key and old['sha256']==digest(path):continue
        data=np.empty((hi-lo,30,365),dtype='float32')
        for y,(source,index) in enumerate(zip(arrays,indices)):
            data[:,y,:]=np.asarray(source[:,lo:hi])[index].T
        mean,q,count,years=climatology(data)
        np.savez_compressed(path,mean=mean,threshold=q,sample_count=count,year_count=years,cells=grid['cells'][lo:hi])
        write_json(receipt,{'inputs':key,'sha256':digest(path),'start':lo,'stop':hi})
        print(f'Baseline {hi}/{n}; {time.monotonic()-start:.1f}s',flush=True)
    if a.limit:return
    targets={k:np.lib.format.open_memmap(out/(k+'.npy'),mode='w+',dtype=dtype,shape=(n,366))
             for k,dtype in [('mean','float32'),('threshold','float32'),('sample_count','uint16'),('year_count','uint8')]}
    for lo in range(0,n,a.chunk):
        hi=min(lo+a.chunk,n);part=np.load(out/f'{lo:06d}-{hi:06d}.npz')
        for k,target in targets.items():target[lo:hi]=part[k]
    for target in targets.values():target.flush()
    write_json(OUTPUT/'data/baseline.json',{'inputs':key,'cells':n,'baseline':[1991,2020],
         'files':{str((out/(k+'.npy')).relative_to(OUTPUT)):digest(out/(k+'.npy')) for k in targets},
         'support':'minimum pooled observations/distinct years among 31 smoothing windows; February 29 interpolated',
         'method':'11-day circular nonleap pool; linear P90; leap interpolation; complete 31-day circular mean'})


if __name__=='__main__':main()
