#!/usr/bin/env python3
"""Render H3r5 SST, coral exposure, anomaly and daily-record review plates."""
import argparse
from copy import deepcopy
from html import escape
import json
import math
import os
from pathlib import Path
import subprocess

from lxml import etree as E
import numpy as np

from atlas_review_sheets import ROOT, NS, FG, el, legend, export, font_environment
from ocean_temperature import digest, write_json
from viz_context import ocean_output, atlas_root, cutoff, snapshot_date
from setouchi_h3_trials import settings_for

TEMPLATE='anthropocene-land-temperature-2026'
SST_BOUNDS=[0,5,10,15,20,25,28,30]
SST_COLORS=['#243b81','#3066a5','#438cae','#69afbc','#9fcac3','#d6d5a1','#e8b168','#dc794c','#b74348']
ANOMALY_BOUNDS=[-2,-1,-.5,0,.5,1,2]
ANOMALY_COLORS=['#355da8','#6395ce','#a1c5e7','#e4ebee','#f3e3b6','#eab46e','#d37c4a','#b54150']
DHW_BOUNDS=[4,8,12,16,20]
DHW_COLORS=['#eee9d5','#ffd772','#ffa05b','#f4596d','#cb71f0','#9cecf1']
HIGH_BOUNDS=[5,10,20,30,40]
HIGH_COLORS=['#fff0ac','#ffd36e','#ed9c40','#cf652d','#a53939','#7c2446']


def rgba(value,alpha=1):
    return [int(value[i:i+2],16)/255 for i in (1,3,5)]+[alpha]


def styles(colors,outline=False):
    return {str(i):{'fill':rgba(c,0 if outline else 1),'stroke':rgba(c,1 if outline else 0),
                    'width':.010 if outline else 0} for i,c in enumerate(colors)}


def classify(value,bounds,side='right'):
    return int(np.searchsorted(bounds,value,side=side))


def layer(id,cells,values,bounds,mask=None,side='right'):
    valid=np.isfinite(values)
    if mask is not None:valid &= mask
    indices=np.flatnonzero(valid);bins=np.searchsorted(bounds,values[indices],side=side)
    return {'id':id,'cells':[[f'{cells[i]:x}',round(float(values[i]),5),int(b)] for i,b in zip(indices,bins)]}


def frame(atlas,scope,stem,title,tiles,rendered,settings,root,metadata):
    source=atlas/'maps'/scope/'svg'/(TEMPLATE+'.svg')
    if not source.exists():source=source.with_name(TEMPLATE.replace('anthropocene-land-temperature','anthropocene-temperature')+'.svg')
    tree=E.parse(str(source),E.XMLParser(huge_tree=True));doc=tree.getroot()
    doc.set('data-canonical-plate-id',stem);doc.set('data-h3-resolution','5')
    doc.set('data-data-through',metadata['data_through'])
    doc.set('data-legend-companion',f'../../../legends/{scope}/svg/{stem}-legend.svg')
    doc.set('data-source-grid','OISST 0.25 degree original centers; CRW 0.05 degree original centers')
    for n in doc.xpath('./*[local-name()="title"]'):n.text=title
    anchor=doc.xpath('//*[@id="cpc-temperature-coverage"]')[0];parent=anchor.getparent();position=parent.index(anchor)
    for n in doc.xpath('//*[@id="cpc-temperature-coverage" or @id="cpc-temperature-record-high-days" or @id="cpc-temperature-record-low-days" or @id="anthropocene-temperature-metadata"]'):
        n.getparent().remove(n)
    meta=el('metadata',id='ocean-temperature-metadata');meta.text=json.dumps(metadata);parent.insert(position,meta);position+=1
    # The current world frame applies its approved cyclic movement to these
    # source-space data layers exactly as it does to the land-temperature map.
    view=next(v for v in settings['views'] if v['id']==scope)
    for l in rendered['layers']:
        t=next(t for t in l['tiles'] if t['scope']==scope)
        group=el('g',id=l['id'],data_metric=l['id']);parent.insert(position,group);position+=1
        x,y,w,h=view['bounds']
        image=el('image',group,x=x,y=y,width=w,height=h,preserveAspectRatio='none')
        destination=root/'maps'/scope/'svg'/(stem+'.svg')
        image.set('{http://www.w3.org/1999/xlink}href',os.path.relpath(tiles/t['file'],destination.parent))
    return doc


def prepare_sst_preview(root):
    """A usable SST preview can precede the full historical record download."""
    g=np.load(root/'work/grid.npz')
    for year in (2025,2026):
        path=root/'data'/f'water-temperature-{year}-annual.npz'
        if path.exists():continue
        data=np.load(root/'work'/f'{year}.npy',mmap_mode='r')
        valid=np.isfinite(data).sum(axis=0);mean=np.nanmean(data,axis=0)
        mean[valid<.8*len(data)]=np.nan
        np.savez_compressed(path,cells=g['cells'],mean_sst=mean,valid_days=valid)
        write_json(path.with_suffix('.json'),dict(year=year,period='annual',data_through=f'{year}-12-31' if year==2025 else str(cutoff()),expected_days=len(data),analysis_stage='sst-only-preview',grid='NOAA OISST 0.25 degree original ocean centers',h3_resolution=5,sha256=digest(path),occupied_cells=len(g['cells']),displayed_sst_cells=int(np.isfinite(mean).sum())))


def make_legend(stem,title,mode,metadata,scope,period,coral):
    year=metadata['year'];days=metadata['expected_days']
    cutoff=metadata['data_through']
    subtitle=f'{year}-01-01 through {cutoff} / {days} days / '+scope.title()
    if mode=='sst':
        labels=['Below 0','0 to <5','5 to <10','10 to <15','15 to <20','20 to <25','25 to <28','28 to <30','30 or warmer']
        sections=[{'title':'Mean sea-surface temperature / °C','keys':list(zip(SST_COLORS,labels)),
                   'notes':['Mean of daily mean SST. At least 80% valid days required. Ocean surface, not subsurface heat content.']},
                  {'title':'Coral thermal exposure / °C-weeks','keys':[(c,l,'outline') for c,l in zip(DHW_COLORS,['0 to <4','4 to <8','8 to <12','12 to <16','16 to <20','20 or greater'])],
                   'notes':['Outlines: maximum Degree Heating Week during this period. DHW accumulates qualifying thermal stress over a rolling 12-week window.','Satellite exposure near historical reef locators; not observations of bleaching or mortality.']},
                  {'title':'Comparing the years','notes':['2025 full-year and 2026 year-to-date totals have different temporal support.','Use the matched 2025 calendar window when comparing with 2026; its actual endpoint is recorded on the legend.','DHW is a period maximum, not an annual heat sum. Early-January DHW can include stress from the preceding year.']}]
    elif mode=='anomaly':
        labels=['Below −2','−2 to <−1','−1 to <−0.5','−0.5 to <0','0 to <0.5','0.5 to <1','1 to <2','2 or warmer']
        sections=[{'title':'Mean SST anomaly / °C','keys':list(zip(ANOMALY_COLORS,labels))},
                  {'title':'Reference period','notes':['1991–2020 calendar-day climatology derived from the same H3 daily-mean SST series.','At least 24 valid reference years per calendar day; at least 80% target days for the displayed mean.','The PSL-supplied legacy anomaly field uses a different climatology. This atlas computes its own 1991–2020 anomalies.']},
                  {'title':'Interpretation','notes':['An anomaly is a difference from the local seasonal reference, not the ocean’s absolute temperature.','No coral bleaching status is inferred from this anomaly.','Warm/cool colors use fixed boundaries in both years and both geographic views.']}]
    else:
        sections=[{'title':'Record-high daily means / days','keys':list(zip(HIGH_COLORS,['1–5','6–10','11–20','21–30','31–40','More than 40']))},
                  {'title':'Record-low daily means / days','keys':[(c,l,'outline') for c,l in zip(['#bdd7e7','#6baed6','#2171b5'],['1–5','6–20','More than 20'])],
                   'notes':['Neutral coverage: zero record highs. Blank: insufficient record-comparison coverage.','Only days with at least 30 valid earlier calendar years are eligible. Ties do not count.']},
                  {'title':'Record definition','notes':[f'Strict daily-mean SST records against 1982–{year-1}, matching calendar month and day.','The target value is compared before entering history. Thus 2025 is not in its own baseline; it is in the 2026 baseline.','This is the ocean counterpart to land record-day counts, but SST is a daily mean; land uses daily TMAX and TMIN.']}]
    notes=['Actual H3 resolution 5 boundaries. Original 0.25° OISST centers are averaged per H3 cell before temporal comparisons; incomplete sample membership masks that cell-day. No interpolation or source-footprint filling.',
           'Daily reported sea-ice concentration ≥15% is excluded. The PSL ice field stores fractions (0–1) despite its percent label; its sparse missing mask is retained separately from SST validity.',
           f'Fixed bins across years. Recent NOAA values may be revised; snapshot {snapshot_date()}, ocean cutoff {cutoff}. Land-temperature plates retain their own source cutoff.']
    if mode=='sst':notes.append('Coral: original 0.05° CRW centers within the WRI 2011 0.25° reef-presence locator; maximum valid DHW per H3 cell. The locator is historical and coarser than present reef boundaries.')
    sources=['NOAA OISST v2.1 / https://www.ncei.noaa.gov/products/optimum-interpolation-sst',
             'NOAA PSL yearly files / https://psl.noaa.gov/thredds/catalog/Datasets/noaa.oisst.v2.highres/catalog.html']
    if mode=='sst':sources += ['NOAA Coral Reef Watch DHW / https://coralreefwatch.noaa.gov/product/5km/index_5km_dhw.php','WRI Reefs at Risk Revisited (2011) / https://www.wri.org/research/reefs-risk-revisited']
    return legend(stem,title,subtitle,sections,notes,sources)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ocean_output())
    p.add_argument('--sst-only',action='store_true')
    p.add_argument('--dpi',type=int,default=300)
    a=p.parse_args();root=a.root.resolve();atlas=atlas_root();env=font_environment()
    subprocess.run(['make','build/setouchi-h3-tools/render-cells'],cwd=ROOT,check=True)
    if a.sst_only:prepare_sst_preview(root)
    source_stem=TEMPLATE if (atlas/'maps/world/svg'/(TEMPLATE+'.svg')).exists() else TEMPLATE.replace('anthropocene-land-temperature','anthropocene-temperature')
    settings=settings_for(atlas,source_stem,a.dpi)
    settings['styles']={'sst':styles(SST_COLORS),'anomaly':styles(ANOMALY_COLORS),'coral-dhw':styles(DHW_COLORS,True),
                        'record-coverage':styles(['#706269']),'record-high-days':styles(HIGH_COLORS),
                        'record-low-days':styles(['#bdd7e7','#6baed6','#2171b5'],True)}
    all_records=[];products=[]
    for year,period in ([(2025,'annual'),(2026,'annual')] if a.sst_only else [(2025,'annual'),(2026,'annual'),(2025,'matched')]):
        data_path=root/'data'/f'water-temperature-{year}-{period}.npz'
        data=np.load(data_path);meta=json.loads(data_path.with_suffix('.json').read_text())
        if not a.sst_only and meta.get('analysis_stage')=='sst-only-preview':raise ValueError('Historical preparation has not completed')
        cells=data['cells'];expected=meta['expected_days']
        coral=json.loads((root/'data'/f'coral-dhw-{year}-{period}.json').read_text())
        coral_layer={'id':'coral-dhw','cells':[[c,v,classify(v,DHW_BOUNDS)] for c,v,n in coral['cells']]}
        for mode in (['sst'] if a.sst_only else ['sst','anomaly','records']):
            suffix='-anomaly' if mode=='anomaly' else ''
            stem=f'anthropocene-water-temperature{suffix}-{year}'
            title=('Sea-surface temperature and coral heat stress' if mode=='sst' else 'Sea-surface temperature anomaly' if mode=='anomaly' else 'Sea-surface temperature records')+f' / {year}'
            directory=root if period=='annual' else root/'matched'
            if mode=='records':directory=directory/'record-days'
            tile_dir=root/'tiles'/f'{year}-{period}-{mode}';tile_dir.mkdir(parents=True,exist_ok=True)
            if mode=='sst':layers=[layer('sst',cells,data['mean_sst'],SST_BOUNDS),coral_layer]
            elif mode=='anomaly':layers=[layer('anomaly',cells,data['mean_anomaly'],ANOMALY_BOUNDS)]
            else:
                eligible=data['eligible_days']>=.8*expected
                layers=[layer('record-coverage',cells,np.ones(len(cells)),[],eligible),
                        layer('record-high-days',cells,data['high_days'],HIGH_BOUNDS,eligible&(data['high_days']>0),side='left'),
                        layer('record-low-days',cells,data['low_days'],[5,20],eligible&(data['low_days']>0),side='left')]
            payload={'schema':'cartofreako-ocean-render-v1','layers':layers}
            write_json(tile_dir/'data.json',payload);write_json(tile_dir/'settings.json',settings)
            fingerprint={'data_sha256':digest(tile_dir/'data.json'),'settings_sha256':digest(tile_dir/'settings.json'),'renderer_sha256':digest(ROOT/'build/setouchi-h3-tools/render-cells')}
            receipt=tile_dir/'inputs.json';old=json.loads(receipt.read_text()) if receipt.exists() else None
            if not old or old['fingerprint']!=fingerprint or not all((tile_dir/f).exists() and digest(tile_dir/f)==h for f,h in old['files'].items()):
                subprocess.run([str(ROOT/'build/setouchi-h3-tools/render-cells'),'ocean',str(data_path.with_suffix('.json')),str(tile_dir/'data.json'),str(tile_dir/'settings.json'),str(tile_dir)],check=True)
                rendered=json.loads((tile_dir/'render.json').read_text())
                files=['render.json']+[t['file'] for l in rendered['layers'] for t in l['tiles']]
                write_json(receipt,{'fingerprint':fingerprint,'files':{f:digest(tile_dir/f) for f in files}})
            rendered=json.loads((tile_dir/'render.json').read_text())
            for scope in ('world','japan'):
                tree=frame(atlas,scope,stem,title,tile_dir,rendered,settings,directory,meta)
                record=export(directory,stem,scope,'map',tree,env)
                sheet=make_legend(stem,title,mode,meta,scope,period,coral)
                legend_record=export(directory,stem,scope,'legend',sheet,env)
                for r in (record,legend_record):
                    for k in ('svg','pdf','preview'):r[k]=str((directory/r[k]).relative_to(root))
                    r.update(mode=mode,period=period,year=year)
                    all_records.append(r)
            products.append(dict(stem=stem,title=title,mode=mode,period=period,year=year,metadata=meta,tiles_receipt=str(receipt.relative_to(root))))
            print(f'Built {stem} / {mode} / {period}',flush=True)
    write_json(root/'preview-manifest.json',dict(schema='cartofreako-ocean-previews-v1',products=products,records=all_records,provisional_sst_only=a.sst_only))
    parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Water temperature / stage one</title><style>body{background:#240413;color:#fcc553;font:18px sans-serif;margin:2rem}a{color:inherit}img{width:100%;height:auto}article{margin:3rem 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:1.4rem}@media(max-width:900px){.pair{display:block}}</style><h1>Water temperature / stage one</h1><p>Dataset-specific snapshot. 2025: complete year; 2026: selected year-to-date window. Use matched periods for year-to-year comparisons. These are optional research previews.</p>']
    if a.sst_only:parts.append('<p>Initial SST/coral previews. Historical record and anomaly preparation is still running.</p>')
    for product in products:
        period_label='1 January–'+cutoff().strftime('%B %d') if product['period']=='matched' else 'Year to date: through '+cutoff().strftime('%B %d') if product['year']==2026 else 'Complete year'
        parts.append('<article><h2>'+escape(product['title'])+'</h2><p>'+period_label+'</p><div class="pair">')
        for scope in ('world','japan'):
            rr=[r for r in all_records if all(r[k]==product[k] for k in ('stem','mode','period')) and r['scope']==scope]
            m=next(r for r in rr if r['kind']=='map');l=next(r for r in rr if r['kind']=='legend')
            parts.append('<div><h3>'+scope.title()+'</h3><a href="'+m['preview']+'"><img alt="'+escape(scope.title()+' — '+product['title']+' — '+period_label)+'" src="'+m['preview']+'"></a><p><a href="'+m['svg']+'">Map SVG</a> · <a href="'+m['pdf']+'">Map PDF</a> · <a href="'+l['preview']+'">Legend preview</a> · <a href="'+l['pdf']+'">Legend/source PDF</a> · <a href="'+l['svg']+'">Legend SVG</a></p></div>')
        parts.append('</div></article>')
    (root/'index.html').write_text('\n'.join(parts)+'</html>\n')


if __name__=='__main__':main()
