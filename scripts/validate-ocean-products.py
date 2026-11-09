#!/usr/bin/env python3
"""Validate full ocean products, direct calendar references, exports and links."""
import argparse
import calendar
from datetime import date
import json
from pathlib import Path

from lxml import etree as E
import numpy as np

from ocean_temperature import NetCDF, digest, write_json

from viz_context import ocean_output, snapshot_date
ROOT=ocean_output()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--data-only',action='store_true')
    root=parser.parse_args();data_only=root.data_only;root=root.root
    ledger=json.loads((root/'data/input-ledger.json').read_text())
    assert len(ledger['years'])==45
    acquisition=json.loads((root/'cache/oisst/manifest.json').read_text())
    assert len(acquisition['files'])==91 and not acquisition['failures']
    grid_receipt=json.loads((root/'work/grid.json').read_text())
    mask=next(r for r in acquisition['files'] if r['url'].endswith('/lsmask.oisst.nc'))
    assert mask['sha256']==grid_receipt['source_sha256']
    write_json(root/'data/acquisition-manifest.json',acquisition)
    write_json(root/'data/grid-membership.json',grid_receipt)
    for year in range(1982,2027):
        for variable in ('sst','icec'):
            with NetCDF(root/'cache/oisst'/f'{variable}.day.mean.{year}.nc') as nc:
                np.testing.assert_allclose(nc.read('lat'),np.arange(-89.875,90,.25))
                np.testing.assert_allclose(nc.read('lon'),np.arange(.125,360,.25))
    grid=np.load(root/'work/grid.npz');centers=grid['centers']
    # Geographic anchors select test cells; they do not interpolate map values.
    anchors=[(-5,-140),(35,140),(25,65),(0,-30),(70,-150),(-65,80),(15,125),(40,-65)]
    indices=[int(np.argmin((centers[:,0]-lat)**2+(centers[:,1]-lon)**2)) for lat,lon in anchors]
    by_year={}
    for year in range(1982,2027):
        rows=np.load(root/'work'/f'{year}.npy',mmap_mode='r')
        dates=json.loads((root/'work'/f'{year}.json').read_text())['dates']
        by_year[year]={day[5:]:rows[i,indices].astype(float) for i,day in enumerate(dates)}
    reference_checks=[]
    for year in (2025,2026):
        for period in ('annual','matched'):
            path=root/'data'/f'water-temperature-{year}-{period}.npz'
            metadata=json.loads(path.with_suffix('.json').read_text());product=np.load(path)
            assert metadata['sha256']==digest(path)
            assert metadata['snapshot_as_of']==str(snapshot_date())
            last=metadata['data_through'][5:];days=sorted(day for day in by_year[year] if day<=last)
            assert metadata['expected_days']==len(days)
            for name in ('valid_days','anomaly_days','eligible_days','high_days','low_days'):
                values=product[name];assert np.all(values>=0) and np.all(values<=len(days))
                np.testing.assert_array_equal(values,np.floor(values))
            assert np.all(product['high_days']+product['low_days']<=product['eligible_days'])
            assert np.all(product['eligible_days']<=product['valid_days'])
            assert np.all(product['anomaly_days']<=product['valid_days'])
            assert np.array_equal(np.isfinite(product['mean_sst']),product['valid_days']>=.8*len(days))
            assert np.array_equal(np.isfinite(product['mean_anomaly']),product['anomaly_days']>=.8*len(days))
            totals={k:np.zeros(len(indices)) for k in ('valid_days','anomaly_days','eligible_days','high_days','low_days','sst_sum','anomaly_sum')}
            for day in days:
                value=by_year[year][day]
                prior=np.array([by_year[y][day] for y in range(1982,year)])
                climate=np.array([by_year[y][day] for y in range(1991,2021)])
                for j,target in enumerate(value):
                    if not np.isfinite(target):continue
                    totals['valid_days'][j]+=1;totals['sst_sum'][j]+=target
                    history=prior[:,j][np.isfinite(prior[:,j])]
                    baseline=climate[:,j][np.isfinite(climate[:,j])]
                    if len(history)>=30:
                        totals['eligible_days'][j]+=1
                        totals['high_days'][j]+=target>max(history)
                        totals['low_days'][j]+=target<min(history)
                    if len(baseline)>=24:
                        totals['anomaly_days'][j]+=1;totals['anomaly_sum'][j]+=target-sum(baseline)/len(baseline)
            for name,expected in totals.items():np.testing.assert_allclose(product[name][indices],expected,rtol=1e-10,atol=1e-8,err_msg=f'{year} {period} {name}')
            reference_checks.append({'year':year,'period':period,'days':len(days),'independent_reference_cells':len(indices)})
        months=np.load(root/'data'/f'monthly-{year}.npz')
        annual=np.load(root/'data'/f'water-temperature-{year}-annual.npz')
        for name in totals:np.testing.assert_allclose(months[name].sum(axis=0),annual[name])
        for month in range(1,13):
            through=json.loads((root/'data'/f'water-temperature-{year}-annual.json').read_text())['data_through'][5:]
            maximum=sum(int(day[:2])==month and day<=through for day in by_year[year])
            assert np.all(months['valid_days'][month-1]<=maximum)
    sheets=[]
    if not data_only:
        manifest=json.loads((root/'preview-manifest.json').read_text())
        assert not manifest['provisional_sst_only']
        assert len(manifest['products'])==9 and len(manifest['records'])==36
        for row in manifest['records']:
            for field in ('svg','pdf','preview'):assert digest(root/row[field])==row[field+'_sha256']
            path=root/row['svg'];tree=E.parse(str(path),E.XMLParser(huge_tree=True));svg=tree.getroot()
            assert svg.get('data-canonical-plate-id')==row['stem']
            if row['kind']=='map':
                assert svg.get('data-h3-resolution')=='5'
                assert not tree.xpath('//*[@id="cpc-temperature-coverage" or @id="cpc-temperature-record-high-days" or @id="cpc-temperature-record-low-days"]')
                for node in tree.xpath('//*[local-name()="image"]'):
                    ref=node.get('{http://www.w3.org/1999/xlink}href') or node.get('href')
                    if ref and not ref.startswith('data:'):assert (path.parent/ref).is_file(),ref
            sheets.append(row['svg'])
    write_json(root/'validation.json',{'status':'passed','reference_checks':reference_checks,
               'native_grids_checked':90,'occupied_h3_cells':len(grid['cells']),
               'checked_export_sheets':len(sheets),'data_only':data_only,
               'products_sha256':digest(root/'data/products.json'),'script_sha256':digest(Path(__file__))})
    print(f'Ocean validation passed: 90 native grids, 32 independently recomputed cell-periods, {len(sheets)} exported sheets')


if __name__=='__main__':main()
