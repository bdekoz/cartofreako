#!/usr/bin/env python3
"""One-day, native-grid comparison; providers share some observations."""
import gzip
from datetime import date
import json
from pathlib import Path

import numpy as np

from ocean_temperature import NetCDF, digest, write_json

from viz_context import ocean_output
ROOT=ocean_output()


def main():
    source=sorted((ROOT/'research').glob('mgd_sst_glb_D*.txt.gz'))[-1]
    stamp=source.name.split('_D')[1][:8]
    observation=date(int(stamp[:4]),int(stamp[4:6]),int(stamp[6:8]))
    lines=gzip.decompress(source.read_bytes()).splitlines()
    assert list(map(int,lines[0].split()))==[observation.year,observation.month,observation.day]
    assert len(lines)==721 and all(len(line)==4320 for line in lines[1:])
    raw=np.frombuffer(b''.join(lines[1:]),dtype='S3').astype('int16').reshape(720,1440)
    jma=raw.astype(float)*.1;jma[(raw==888)|(raw==999)]=np.nan;jma=jma[::-1]
    path=ROOT/'cache/oisst/sst.day.mean.2026.nc'
    with NetCDF(path) as nc:
        times=nc.read('time');index=np.flatnonzero(times==(observation-date(1800,1,1)).days)
        assert len(index)==1
        oisst=nc.read('sst',start=(int(index[0]),0,0),count=(1,720,1440))[0]
        lat,lon=nc.read('lat'),nc.read('lon')
    with NetCDF(ROOT/'cache/oisst/icec.day.mean.2026.nc') as nc:
        ice=nc.read('icec',start=(int(index[0]),0,0),count=(1,720,1440))[0]
    valid=np.isfinite(jma)&np.isfinite(oisst)&~(np.isfinite(ice)&(ice>=.15-1e-6))
    w=np.broadcast_to(np.cos(np.deg2rad(lat))[:,None],valid.shape)
    rows=[]
    for label,domain in [('common global valid grid',np.ones(valid.shape,dtype=bool)),('Japan region 20–50N, 120–160E',(lat[:,None]>=20)&(lat[:,None]<=50)&(lon[None,:]>=120)&(lon[None,:]<=160))]:
        mask=domain&valid;difference=jma[mask]-oisst[mask]
        rows.append(dict(region=label,paired_centers=int(mask.sum()),jma_valid_centers=int((domain&np.isfinite(jma)).sum()),oisst_valid_centers_before_ice_screen=int((domain&np.isfinite(oisst)).sum()),
            oisst_valid_centers_after_ice_screen=int((domain&np.isfinite(oisst)&~(np.isfinite(ice)&(ice>=.15-1e-6))).sum()),
            area_weighted_mean_jma_minus_oisst_degC=float(np.average(difference,weights=w[mask])),
            area_weighted_rmse_degC=float(np.sqrt(np.average(difference**2,weights=w[mask]))),
            median_absolute_difference_degC=float(np.median(np.abs(difference))),p95_absolute_difference_degC=float(np.percentile(np.abs(difference),95))))
    write_json(ROOT/'data/jma-oisst-comparison.json',dict(date=str(observation),jma_sha256=digest(source),oisst_sha256=digest(path),jma_units='0.1 degree Celsius; 888 sea ice; 999 land/undetermined',jma_grid_order='north-to-south reversed to OISST south-to-north; longitudes already align',statistics=rows,limitations=['One date, not a multi-year validation.','Providers share satellite and in-situ inputs: agreement is not an independent accuracy estimate.','JMA real-time ice and missing codes excluded; OISST reported ice fraction >=0.15 excluded.','Native 0.25 degree centers and cosine-latitude area weights; no resampling.']))
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
