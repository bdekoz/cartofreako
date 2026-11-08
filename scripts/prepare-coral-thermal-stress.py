#!/usr/bin/env python3
"""Sample NOAA CRW period maxima inside historical reef-locator grid cells.

The 0.25° WRI presence grid is a locator, not a present-day reef mask. All
original 0.05° CRW centers inside those locator cells are indexed at H3r5;
the maximum of valid samples is retained as a conservative exposure display.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np

from ocean_temperature import NetCDF, digest, h3_cell, write_json

ROOT=Path(__file__).resolve().parents[1]


def prepare(root):
    locator=ROOT/'assets.static/resources/coral-reefs-025deg.geojson'
    features=json.loads(locator.read_text())['features']
    source_cells=set()
    for f in features:
        ring=f['geometry']['coordinates'][0]
        west,east=min(p[0] for p in ring),max(p[0] for p in ring)
        south,north=min(p[1] for p in ring),max(p[1] for p in ring)
        assert abs(east-west-.25)<1e-6 and abs(north-south-.25)<1e-6
        # CRW latitudes descend from 89.975; longitudes ascend from -179.975.
        for row in range(round((90-north)*20),round((90-south)*20)):
            for col in range(round((west+180)*20),round((east+180)*20)):
                source_cells.add((row,col))
    rows,cols=np.array(sorted(source_cells)).T
    cells=np.array([h3_cell(89.975-r*.05,-179.975+c*.05) for r,c in zip(rows,cols)],dtype='uint64')
    inputs=json.loads((root/'cache/coral/manifest.json').read_text())
    products=[]
    for source in inputs:
        path=root/'cache/coral'/source['path']
        assert digest(path)==source['sha256']
        with NetCDF(path) as nc:
            attrs=nc.attributes()
            assert nc.attributes('degree_heating_week')['units']=='degree_Celsius_weeks'
            lat,lon=nc.read('lat'),nc.read('lon')
            assert np.allclose(lat,np.arange(89.975,-90,-.05),atol=1e-5)
            assert np.allclose(lon,np.arange(-179.975,180,.05),atol=1e-5)
            values=nc.read('degree_heating_week')[0][rows,cols]
            mask=nc.read('mask')[0][rows,cols]
        maxima={};members=defaultdict(int)
        for cell,value,flag in zip(cells,values,mask):
            if flag!=0 or not np.isfinite(value):continue
            key=f'{cell:x}';maxima[key]=max(maxima.get(key,0),float(value));members[key]+=1
        year=2026 if '20261107' in path.name else 2025
        period='matched' if '20251107' in path.name else 'annual'
        data={'schema':'cartofreako-coral-dhw-v1','year':year,'period':period,
              'units':'degree_Celsius_weeks','source':source,
              'source_time_coverage_start':attrs['time_coverage_start'],
              'source_time_coverage_end_exclusive':attrs['time_coverage_end'],
              'locator':{'path':str(locator.relative_to(ROOT)),'sha256':digest(locator),'year':2011,'source_grid_cells':len(features)},
              'method':'Maximum CRW period-maximum DHW among valid original 0.05° centers within each H3r5 cell and the WRI historical 0.25° reef-presence locator. No interpolation.',
              'claim_boundary':'Satellite-derived thermal exposure around historically mapped reefs; not observed bleaching, reef extent, mortality, or current coral condition.',
              'cells':[[key,round(value,2),members[key]] for key,value in sorted(maxima.items())]}
        output=root/'data'/f'coral-dhw-{year}-{period}.json'
        write_json(output,data)
        products.append({'path':str(output.relative_to(root)),'sha256':digest(output),'cells':len(maxima),'maximum_dhw':max(maxima.values()),'year':year,'period':period})
    write_json(root/'data/coral-products.json',products)
    print(json.dumps(products,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT/'output/ocean-temperature-20261108')
    prepare(p.parse_args().root)
