#!/usr/bin/env python3
"""Experimental local warm seasons with explicit undefined and open states."""
import argparse
import numpy as np

from ocean_stage_2 import OUTPUT,OCEAN,dates,thermal_seasons,SEASON_FIELDS,SEASON_STATUS,save_product,cutoff
from ocean_stage_2 import ocean_array
from ocean_temperature import write_json


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--chunk',type=int,default=4096);a=p.parse_args()
    grid=np.load(OCEAN/'work/grid.npz');n=len(grid['cells'])
    mean=np.load(OUTPUT/'work/baseline/mean.npy',mmap_mode='r')
    source=[ocean_array(y) for y in (2024,2025,2026)]
    ds=sum([dates(y,len(s)) for y,s in zip((2024,2025,2026),source)],[])
    products=[]
    for year in (2025,2026):
        fields={k:np.full(n,np.nan,dtype='float32') for k in SEASON_FIELDS}
        sensitivity={str(p):np.zeros(len(SEASON_STATUS),dtype='int64') for p in (5,7,10)}
        for lo in range(0,n,a.chunk):
            hi=min(n,lo+a.chunk);values=np.concatenate([s[:,lo:hi] for s in source],axis=0).T.copy()
            for persistence in (5,7,10):
                data=thermal_seasons(values,mean[lo:hi],ds,year,persistence)
                sensitivity[str(persistence)]+=np.bincount(data['status'].astype(int),minlength=len(SEASON_STATUS))
                if persistence==7:
                    for k in fields:fields[k][lo:hi]=data[k]
            if lo%(a.chunk*16)==0:print(f'Seasons {year}: {hi}/{n}',flush=True)
        amplitudes={str(gate):int(np.sum(fields['amplitude']>=gate)) for gate in (1,2,3)}
        products.append(save_product(f'ocean-thermal-season-{year}',{**fields,'cells':grid['cells'],'centers':grid['centers'],'weights':grid['weights']},
           {'family':'ocean-thermal-season','year':year,'period':'season','data_through':str(cutoff()),'baseline':'1991–2020',
            'season_year':'year of expected climatological warm peak; full available adjacent-year context',
            'status_codes':dict(enumerate(SEASON_STATUS)),
            'status_counts':{name:int(np.sum(fields['status']==i)) for i,name in enumerate(SEASON_STATUS)},
            'sensitivity_persistence_status_counts':{p:dict(zip(SEASON_STATUS,map(int,counts))) for p,counts in sensitivity.items()},
            'amplitude_eligible_cells':amplitudes}))
    write_json(OUTPUT/'data/season-products.json',products)


if __name__=='__main__':main()
