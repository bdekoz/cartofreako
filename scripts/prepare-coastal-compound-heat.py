#!/usr/bin/env python3
"""Geometry-audited coastal pairings and date-aligned land/ocean extremes."""
from datetime import date
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely as shp
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix,save_npz,load_npz

from ocean_stage_2 import ROOT,OUTPUT,OCEAN,CONFIG,NetCDF,cpc_path,cpc_dates,dates,slots,nonleap_indices,climatology,save_product
from ocean_temperature import digest,write_json,h3_cell

EARTH=6371.0088


def xyz(latlon):
    a=np.deg2rad(latlon);lat,lon=a[:,0],a[:,1]
    return np.column_stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])


def kilometers(chord):
    return 2*EARTH*np.arcsin(np.clip(chord/2,0,1))


def geometries():
    root=ROOT/'assets.static/natural-earth/10m-physical-vectors'
    land=shp.union_all(gpd.read_file(root/'ne_10m_land.shp').geometry.to_numpy())
    ocean=gpd.read_file(root/'ne_10m_ocean.shp').geometry.iloc[0]
    coast=gpd.read_file(root/'ne_10m_coastline.shp').geometry.to_numpy()
    # <=0.05-degree shoreline samples bound nominal reference-point spacing.
    points=shp.get_coordinates(shp.segmentize(coast,.05))[:,::-1]
    shp.prepare(land);shp.prepare(ocean)
    receipts={str(p.relative_to(ROOT)):digest(p) for name in ('land','ocean','coastline')
              for ext in ('shp','shx','dbf','prj') if (p:=root/f'ne_10m_{name}.{ext}').exists()}
    return land,ocean,points,receipts


def sea_visible(anchor,points,land):
    """Reject dateline-spanning planar segments and any intervening land.

    Endpoints are separated from the coast by 1 metre along the segment to
    avoid classifying the shared shoreline endpoint as a land intersection.
    Conservative dateline omissions are recorded; no wrapped straight line.
    """
    coords=np.asarray(points)[:,::-1];start=np.asarray(anchor)[::-1]
    delta=coords-start;ok=np.abs(delta[:,0])<180
    starts=start+delta*1e-5
    lines=shp.linestrings(np.stack([starts,coords],axis=1))
    return ok & ~shp.intersects(land,lines)


def build_pairs():
    folder=OUTPUT/'work/coastal';folder.mkdir(parents=True,exist_ok=True)
    target=folder/'pairs.npz'
    receipt=OUTPUT/'data/coastal-pairing.json'
    old=json.loads(receipt.read_text()) if receipt.exists() else {}
    if target.exists() and old.get('implementation_sha256')==digest(__file__) and old.get('grid_sha256')==digest(OCEAN/'work/grid.npz'):
        if all(digest(ROOT/p)==h for p,h in old['source_geometries'].items()):return dict(np.load(target))
    land,ocean,coast,receipts=geometries();tree=cKDTree(xyz(coast))
    with NetCDF(cpc_path(2025)) as nc:
        lat,lon=nc.read('lat'),nc.read('lon');lon=np.where(lon>180,lon-360,lon)
        available=np.zeros((360,720),bool)
        for i in range(0,365,30):available|=np.isfinite(nc.read('tmax',(i,0,0),(1,360,720))[0])
    yy,xx=np.meshgrid(lat,lon,indexing='ij');points=np.column_stack([yy.ravel(),xx.ravel()])
    valid=available.ravel() & shp.contains_xy(land,points[:,1],points[:,0])
    indices=np.flatnonzero(valid);dist,nearest=tree.query(xyz(points[indices]),workers=8);distance=kilometers(dist)
    keep=distance<=100;indices=indices[keep];distance=distance[keep];shore=coast[nearest[keep]]
    grid=dict(np.load(OCEAN/'work/grid.npz'));ocean_points=grid['centers'];ocean_points=ocean_points.copy()
    ocean_points[:,1]=(ocean_points[:,1]+180)%360-180
    ocean_good=shp.contains_xy(ocean,ocean_points[:,1],ocean_points[:,0]);oi=np.flatnonzero(ocean_good)
    otree=cKDTree(xyz(ocean_points[oi]));candidates=otree.query_ball_point(xyz(shore),2*np.sin(100/(2*EARTH)),workers=8)
    kept=[];members=[];members50=[];rejections={'no_visible_ocean':0,'dateline_candidates':0,'land_barrier_candidates':0}
    for i,near in enumerate(candidates):
        ids=oi[np.array(near,dtype=int)]
        if not len(ids):rejections['no_visible_ocean']+=1;continue
        visibility=sea_visible(shore[i],ocean_points[ids],land)
        rejections['dateline_candidates']+=int(np.sum(np.abs(ocean_points[ids,1]-shore[i,1])>=180))
        rejections['land_barrier_candidates']+=int(np.sum(~visibility))
        ids=ids[visibility]
        if not len(ids):rejections['no_visible_ocean']+=1;continue
        d=kilometers(np.linalg.norm(xyz(ocean_points[ids])-xyz(shore[i:i+1]),axis=1))
        kept.append(i);members.append(ids);members50.append(ids[d<=50] if distance[i]<=50 else np.array([],int))
        if i%2000==0:print(f'Coastal geometry {i}/{len(indices)}',flush=True)
    k=np.array(kept);pairs=dict(native_indices=indices[k],centers=points[indices[k]],shore=shore[k],distance_km=distance[k],
             cells=np.array([h3_cell(*p) for p in points[indices[k]]],dtype='uint64'))
    np.savez_compressed(target,**pairs)
    for radius,memberlist in [(100,members),(50,members50)]:
        rr=[];cc=[];ww=[]
        for row,ids in enumerate(memberlist):
            rr.extend([row]*len(ids));cc.extend(ids);ww.extend(grid['weights'][ids])
        matrix=csr_matrix((ww,(rr,cc)),shape=(len(k),len(grid['cells'])))
        save_npz(folder/f'weights-{radius}.npz',matrix)
    # Curated table retains the actual memberships, not only a digest of a cache.
    np.savez_compressed(OUTPUT/'data/coastal-pairing.npz',**pairs,
         ocean_cells=grid['cells'],ocean_centers=ocean_points,
         offsets=np.concatenate([[0],np.cumsum([len(m) for m in members])]),members=np.concatenate(members),
         offsets50=np.concatenate([[0],np.cumsum([len(m) for m in members50])]),members50=np.concatenate(members50))
    write_json(OUTPUT/'data/coastal-pairing.json',{'source_geometries':receipts,'pair_count':len(k),
        'implementation_sha256':digest(__file__),'grid_sha256':digest(OCEAN/'work/grid.npz'),
        'geometry':'native CPC center in Natural Earth land; nearest shoreline sample at <=0.05° spacing; ocean H3 center in Natural Earth ocean; line from shore to ocean center must not intersect land',
        'distance':'spherical great-circle; nominal 100 km gates; shoreline reference uncertainty <= about 3 km from sampling; dateline-spanning planar segments conservatively excluded',
        'support':'fixed Stage 1 H3 native-center membership; pair mean weighted by sum cos(native latitude); pair geometry uses H3 centers and does not resolve subcell coastlines',
        'rejections':rejections,'pairing_sha256':digest(OUTPUT/'data/coastal-pairing.npz')})
    return pairs


def prepare_series(pairs):
    folder=OUTPUT/'work/coastal';receipts=[]
    matrices={r:load_npz(folder/f'weights-{r}.npz') for r in (100,50)}
    for year in list(range(1991,2021))+[2025,2026]:
        paths={k:folder/f'{k}-{year}.npy' for k in ['land','ocean100','ocean50']}
        path=cpc_path(year)
        key={'land_sha256':digest(path),'ocean_sha256':json.loads((OCEAN/'work'/f'{year}.json').read_text())['sha256'],
             'pairing_sha256':digest(OUTPUT/'data/coastal-pairing.npz'),'implementation_sha256':digest(__file__)}
        receipt=folder/f'inputs-{year}.json';old=json.loads(receipt.read_text()) if receipt.exists() else {}
        cached=old.get('inputs')==key and all(p.exists() and digest(p)==old.get('files',{}).get(k) for k,p in paths.items())
        with NetCDF(path) as nc:
            ds=cpc_dates(nc);attrs=nc.attributes('tmax')
            if not cached:
                data=nc.read('tmax').reshape(len(ds),-1)[:,pairs['native_indices']]
                np.save(paths['land'],data)
        receipts.append({'year':year,'path':str(path.relative_to(ROOT)),'sha256':digest(path),
                         'dates':[str(ds[0]),str(ds[-1])],'max_period':attrs['max_period'],'valid_range':attrs['valid_range'],
                         'url':f'https://psl.noaa.gov/thredds/fileServer/Datasets/cpc_global_temp/tmax.{year}.nc'})
        ocean=np.load(OCEAN/'work'/f'{year}.npy',mmap_mode='r')
        assert len(ds)==len(ocean)
        for radius,m in matrices.items():
            dest=paths[f'ocean{radius}']
            if cached:continue
            result=np.full((len(ds),len(pairs['cells'])),np.nan,dtype='float32')
            total=np.asarray(m.sum(axis=1)).ravel();binary=m.copy();binary.data[:]=1
            expected=np.diff(m.indptr)
            for lo in range(0,len(ds),16):
                values=np.asarray(ocean[lo:lo+16]);good=np.isfinite(values)
                sums=m.dot(np.where(good,values,0).T);counts=binary.dot(good.astype('float32').T)
                average=np.divide(sums,total[:,None],out=np.full(sums.shape,np.nan),where=total[:,None]>0)
                average[counts!=expected[:,None]]=np.nan
                result[lo:lo+16]=average.T
            np.save(dest,result)
        write_json(receipt,{'inputs':key,'files':{k:digest(p) for k,p in paths.items()}})
        print(f'Coastal daily support {year}',flush=True)
    write_json(OUTPUT/'data/cpc-inputs.json',{'inputs':receipts,'calendar':'provider date labels; max_period 6z to 6z; not an identical OISST or India local observation window',
      'range_policy':'declared -90..50°C valid_range is honored even where actual_range metadata exceeds 50°C; those values remain excluded'})


def baseline(kind,n):
    folder=OUTPUT/'work/coastal';path=folder/(kind+'-baseline.npz')
    key={'daily_arrays':[digest(folder/f'{kind}-{y}.npy') for y in range(1991,2021)],'config':digest(CONFIG),
         'implementation_sha256':digest(ROOT/'scripts/ocean-stage-2-kernels.cc')}
    receipt=path.with_suffix('.json');old=json.loads(receipt.read_text()) if receipt.exists() else {}
    if path.exists() and old.get('inputs')==key and old.get('sha256')==digest(path):return dict(np.load(path))
    output={k:np.empty((n,366),dtype='float32' if k in ('mean','threshold') else 'uint16') for k in ('mean','threshold','count','years')}
    arrays=[np.load(folder/f'{kind}-{y}.npy',mmap_mode='r') for y in range(1991,2021)]
    for lo in range(0,n,4096):
        hi=min(lo+4096,n);data=np.empty((hi-lo,30,365),dtype='float32')
        for i,y in enumerate(range(1991,2021)):data[:,i]=arrays[i][nonleap_indices(y),lo:hi].T
        for k,v in zip(output,climatology(data)):output[k][lo:hi]=v
    np.savez_compressed(path,**output);write_json(receipt,{'inputs':key,'sha256':digest(path)});return output


def joint_states(land,water,land_q,water_q,ds):
    ql=land_q[:,slots(ds)].T;qw=water_q[:,slots(ds)].T
    valid=np.isfinite(land)&np.isfinite(water)&np.isfinite(ql)&np.isfinite(qw)
    return np.where(valid,1+(land>ql).astype('uint8')+2*(water>qw).astype('uint8'),0).astype('uint8')


def summarize_states(states):
    n=states.shape[1];result={k:np.sum(states==i,axis=0).astype('uint16') for i,k in enumerate(['invalid_days','neither_days','land_only_days','other_only_days','both_days'])}
    result['eligible_days']=(states>0).sum(axis=0).astype('uint16')
    result['fraction']=np.divide(result['both_days'],result['eligible_days'],out=np.full(n,np.nan),where=result['eligible_days']>0)
    return result


def main():
    (OUTPUT/'data').mkdir(parents=True,exist_ok=True);pairs=build_pairs();prepare_series(pairs)
    folder=OUTPUT/'work/coastal';n=len(pairs['cells']);landq=baseline('land',n)['threshold'];products=[];flags={}
    for radius in (100,50):
        oq=baseline(f'ocean{radius}',n)['threshold']
        for year in (2025,2026):
            land=np.load(folder/f'land-{year}.npy');water=np.load(folder/f'ocean{radius}-{year}.npy')
            flags[radius,year]=joint_states(land,water,landq,oq,dates(year,len(land)))
            np.save(folder/f'states-{radius}-{year}.npy',flags[radius,year])
            if radius!=100:continue
            for period,length in [('annual',len(land)),('matched',311)]:
                if year==2026 and period=='matched':continue
                values=summarize_states(flags[radius,year][:length])
                products.append(save_product(f'coastal-compound-heat-{year}-{period}',{**values,**pairs},
                 {'family':'coastal-compound-heat','year':year,'period':period,'data_through':str(dates(year,length)[-1]),'expected_days':length,
                  'baseline':'1991–2020 local P90; native land TMAX and fixed adjacent-ocean mean','calendar':'date-aligned co-occurrence; CPC specifies 06Z–06Z'}))
    matched=[]
    for month in range(1,12):
        ix=[i for i,d in enumerate(dates(2025,311)) if d.month==month];a=flags[100,2025][ix];b=flags[100,2026][ix]
        common=(a>0)&(b>0);den=int(common.sum())
        matched.append({'month':month,'paired_pair_days':den,'both_2025':int(np.sum(common&(a==4))),'both_2026':int(np.sum(common&(b==4)))})
    sensitivity=[]
    for year in (2025,2026):
        a=flags[100,year];b=flags[50,year];common=(a>0)&(b>0)
        sensitivity.append({'year':year,'shared_pair_days':int(common.sum()),'both_100km':int(np.sum(common&(a==4))),
           'both_50km':int(np.sum(common&(b==4))),'disagreeing_states':int(np.sum(common&(a!=b)))})
    write_json(OUTPUT/'data/coastal-products.json',products)
    write_json(OUTPUT/'data/coastal-comparisons.json',{'matched_months':matched,'distance_sensitivity_common_support':sensitivity})


if __name__=='__main__':main()
