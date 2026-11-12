#!/usr/bin/env python3
"""Separate AuthaGraph map/legend sheets for the four Stage 2 prototypes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from html import escape
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import subprocess

from lxml import etree as E
import numpy as np

from atlas_review_sheets import legend,save,font_environment
from ocean_stage_2 import ROOT,OUTPUT
from viz_context import atlas_root, cutoff, snapshot_date
from ocean_temperature import digest,write_json
from setouchi_h3_trials import settings_for

spec=importlib.util.spec_from_file_location('ocean_maps',ROOT/'scripts/build-ocean-temperature-plates.py')
maps=importlib.util.module_from_spec(spec);spec.loader.exec_module(maps)

SEQ=['#70616d','#fee3a4','#fdc65d','#ef963e','#ed665c','#d94e83','#c698ec']
DIV=['#4b7cbc','#77a8d4','#b6d4e5','#eee8d4','#efc079','#e28d61','#d75069']
METRICS={
 'event_days':('Days in marine heatwave events','days',[1,7,14,30,60,120],SEQ,['0','1–6','7–13','14–29','30–59','60–119','120 or more']),
 'longest_duration':('Longest observed event span','days',[1,7,14,30,60,120],SEQ,['0','1–6','7–13','14–29','30–59','60–119','120 or more']),
 'cumulative_intensity':('Cumulative marine heatwave intensity','°C-days',[.000001,25,50,100,200,400],SEQ,['0 or less','Above 0 to <25','25 to <50','50 to <100','100 to <200','200 to <400','400 or more']),
 'onset_departure':('Warm-season onset departure','days',[-60,-30,-7,7,30,60],DIV,['Earlier by >60','−60 to <−30','−30 to <−7','−7 to <7','7 to <30','30 to <60','Later by 60 or more']),
 'length':('Completed local warm-season length','days',[30,60,90,120,180,240],SEQ,['Below 30','30–59','60–89','90–119','120–179','180–239','240 or more']),
 'length_departure':('Warm-season length departure','days',[-60,-30,-7,7,30,60],DIV,['Shorter by >60','−60 to <−30','−30 to <−7','−7 to <7','7 to <30','30 to <60','Longer by 60 or more']),
 'observed_warm_days':('Observed local warm days','days',[1,30,60,90,120,180],SEQ,['0','1–29','30–59','60–89','90–119','120–179','180 or more']),
 'both_days':('Date-aligned joint heat days','days',[1,7,14,30,60,120],SEQ,['0','1–6','7–13','14–29','30–59','60–119','120 or more']),
 'fraction':('Joint days / shared eligible days','fraction',[.000001,.05,.1,.2,.35,.5],SEQ,['0','Above 0 to <5%','5 to <10%','10 to <20%','20 to <35%','35 to <50%','50% or more'])}


def render_layers(tile_dir,layers,settings,metadata):
    """Reuse identical support/quality layers across measure variants."""
    renderer=ROOT/'build/setouchi-h3-tools/render-cells';renderer_hash=digest(renderer)
    def location(layer,config):
        key={'layer':layer,'style':config['styles'][layer['id']],'views':config['views'],'renderer':renderer_hash}
        return OUTPUT/'tiles/layer-cache'/hashlib.sha256(json.dumps(key,sort_keys=True).encode()).hexdigest()
    def valid_cache(folder):
        p=folder/'receipt.json'
        if not p.exists():return False
        return all((folder/f).exists() and digest(folder/f)==h for f,h in json.loads(p.read_text())['files'].items())
    def link(source,target):
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            if digest(source)==digest(target):return
            target.unlink()
        os.link(source,target)
    # Seed the shared cache from earlier validated per-view renders, before
    # replacing their settings. This also makes style corrections cheap.
    receipt=tile_dir/'inputs.json'
    if receipt.exists():
        old=json.loads(receipt.read_text())
        if old['inputs']=={'data':digest(tile_dir/'data.json'),'settings':digest(tile_dir/'settings.json'),'renderer':renderer_hash} and all((tile_dir/f).exists() and digest(tile_dir/f)==h for f,h in old['files'].items()):
            previous=json.loads((tile_dir/'data.json').read_text());old_settings=json.loads((tile_dir/'settings.json').read_text());old_render=json.loads((tile_dir/'render.json').read_text())
            for layer in previous['layers']:
                folder=location(layer,old_settings)
                if valid_cache(folder):continue
                folder.mkdir(parents=True,exist_ok=True);render=next(r for r in old_render['layers'] if r['id']==layer['id'])
                for tile in render['tiles']:link(tile_dir/tile['file'],folder/tile['file'])
                write_json(folder/'render.json',{'layers':[render]})
                files=['render.json']+[t['file'] for t in render['tiles']]
                write_json(folder/'receipt.json',{'files':{f:digest(folder/f) for f in files}})
    combined={'subject':'ocean','projection':'authagraph','h3_resolution':5,'layers':[]}
    for layer in layers:
        folder=location(layer,settings);folder.mkdir(parents=True,exist_ok=True)
        if not valid_cache(folder):
            config={**settings,'styles':{layer['id']:settings['styles'][layer['id']]}}
            write_json(folder/'data.json',{'schema':'cartofreako-ocean-render-v1','layers':[layer]});write_json(folder/'settings.json',config)
            subprocess.run([str(renderer),'ocean',str(metadata),str(folder/'data.json'),str(folder/'settings.json'),str(folder)],check=True)
            render=json.loads((folder/'render.json').read_text());files=['render.json']+[t['file'] for r in render['layers'] for t in r['tiles']]
            write_json(folder/'receipt.json',{'files':{f:digest(folder/f) for f in files}})
        result=json.loads((folder/'render.json').read_text())['layers'][0]
        for tile in result['tiles']:link(folder/tile['file'],tile_dir/tile['file'])
        combined['layers'].append(result)
    write_json(tile_dir/'data.json',{'schema':'cartofreako-ocean-render-v1','layers':layers});write_json(tile_dir/'settings.json',settings)
    render_path=tile_dir/'render.json'
    if not render_path.exists() or json.loads(render_path.read_text())!=combined:write_json(render_path,combined)
    files=['render.json']+[t['file'] for l in combined['layers'] for t in l['tiles']]
    write_json(receipt,{'inputs':{'data':digest(tile_dir/'data.json'),'settings':digest(tile_dir/'settings.json'),'renderer':renderer_hash},'files':{f:digest(tile_dir/f) for f in files}})
    return combined


def india_view(settings):
    points=[(lat,lon) for lat in np.linspace(6,38,17) for lon in np.linspace(67,99,17)]
    result=subprocess.run([str(ROOT/'build/stage-2-project-points')],input=''.join(f'{lat} {lon}\n' for lat,lon in points),text=True,capture_output=True,check=True)
    xy=np.array([[float(v) for v in line.split()] for line in result.stdout.splitlines()]);lo=xy.min(axis=0)-.12;hi=xy.max(axis=0)+.12
    bounds=[*lo,*(hi-lo)];scale=min(42/bounds[2],16/bounds[3])
    settings['views'].append({'id':'india','bounds':bounds,'pixels_per_unit':min(1900,300*scale)})
    return bounds


def frame(scope,stem,title,tile_dir,rendered,settings,directory,meta):
    if scope!='india':doc=maps.frame(atlas_root(),scope,stem,title,tile_dir,rendered,settings,directory,meta)
    else:
        adapted=deepcopy(rendered)
        for layer in adapted['layers']:
            layer['tiles']=[dict(t,scope='japan') for t in layer['tiles'] if t['scope']=='india']
        config=deepcopy(settings);view=next(v for v in config['views'] if v['id']=='india');view['id']='japan';config['views']=[view]
        doc=maps.frame(atlas_root(),'japan',stem,title,tile_dir,adapted,config,directory,meta,display_scope='india')
        use=doc.xpath('//*[local-name()="use" and @xlink:href="#source-content"]',namespaces={'xlink':'http://www.w3.org/1999/xlink'})[0]
        viewport=use.getparent();clip=viewport.getparent().get('clip-path')[5:-1]
        rect=doc.xpath('//*[@id=$id]/*[local-name()="rect"]',id=clip)[0]
        x,y,w,h=[float(rect.get(k)) for k in ('x','y','width','height')];bx,by,bw,bh=view['bounds'];scale=min(w/bw,h/bh)
        viewport.set('transform',f'translate({x+(w-bw*scale)/2-bx*scale} {y+(h-bh*scale)/2-by*scale}) scale({scale})')
        doc.set('data-legend-companion',f'../../../legends/india/svg/{stem}-legend.svg')
    doc.set('data-source-grid',meta['support']);doc.set('data-stage','2');doc.set('data-metric',meta['metric'])
    doc.set('data-prototype','true')
    return doc


def export_sheet(directory,stem,scope,kind,tree,env,root):
    suffix='' if kind=='map' else '-legend';folder=directory/('maps' if kind=='map' else 'legends')/scope
    svg=folder/'svg'/(stem+suffix+'.svg');save(tree,svg)
    pdf=folder/'pdf'/(stem+suffix+'.pdf');pdf.parent.mkdir(parents=True,exist_ok=True)
    png=directory/'previews'/scope/(stem+suffix+'.png');png.parent.mkdir(parents=True,exist_ok=True)
    receipt=directory/'work'/f'{stem}-{scope}-{kind}.json';key={'svg_sha256':digest(svg)}
    old=json.loads(receipt.read_text()) if receipt.exists() else None
    # Tile content hashes are embedded in SVG metadata, so source identity
    # covers linked images as well as the text and frame.
    if not old or old['inputs']!=key or not all(p.exists() and digest(p)==old['files'].get(p.suffix) for p in (pdf,png)):
        for target in (pdf,png):
            args=['bash',str(ROOT/'scripts/run-inkscape.sh'),'inkscape',str(svg),'--export-area-page','--export-filename='+str(target)]
            if target==png:args.append('--export-width='+str(1920 if kind=='map' else 2200))
            run=subprocess.run(args,env=env,text=True,capture_output=True)
            if run.returncode or 'Pixbuf::create_' in run.stderr:raise RuntimeError(run.stderr[-1500:])
        write_json(receipt,{'inputs':key,'files':{p.suffix:digest(p) for p in (pdf,png)}})
    return {'stem':stem,'scope':scope,'kind':kind,**{k:str(p.relative_to(root)) for k,p in [('svg',svg),('pdf',pdf),('preview',png)]},
         **{k+'_sha256':digest(p) for k,p in [('svg',svg),('pdf',pdf),('preview',png)]}}


def make_legend(stem,title,metric,meta,scope):
    label,unit,bounds,colors,labels=METRICS[metric];family=meta['family']
    if family=='marine-heatwave':
        method=['Local daily SST above its seasonal 90th percentile for at least five consecutive days. Qualifying events may join across at most two observed cooler days. Missing or ice days never bridge.',
                'Fixed 1991–2020 baseline: 11-day pools, 31-day smoothing. Strict threshold ties do not exceed. Event spans include bridged cooler days.']
        interpretation=['Intensity is signed SST minus seasonal mean, summed over event-span days. Longest span is clipped to the displayed interval.',
                        'Fine pale outlines: event boundary is unobserved, or a short run is pending. Pending runs are excluded from event-eligible denominators. Matched views use the selected shared calendar cutoff.']
    elif family=='ocean-thermal-season':
        method=['Experimental local seasonal index. Threshold is the midpoint of the smoothed climatological minimum and maximum; amplitude must be at least 2°C. Seven persistent days define each crossing.',
                'Season is anchored at the local cool phase and labeled by expected warm-peak year. Adjacent-year observations are used; this is not an ecological season definition.']
        interpretation=['Onset: negative means earlier. Length departure: negative means shorter. Completed length requires both observed transitions.',
                        'Gray support has weak, ambiguous or missing season definitions. White outlines are open seasons. Observed warm days are not a final season length.']
    elif family=='coastal-compound-heat':
        method=['Native CPC TMAX and a fixed adjacent-ocean average each exceed their own 1991–2020 seasonal 90th percentile. No five-day event condition is imposed.',
                '100 km coastal pairing with Natural Earth shoreline and land-barrier checks. Fixed source-supported ocean members; no “any nearby hot cell” selection.']
        interpretation=['Date-aligned co-occurrence. CPC specifies a 06:00–06:00 UTC maximum window; ocean and land daily windows are not assumed identical.',
                        'Fraction uses days when BOTH sources and thresholds are valid. Association does not establish a mechanism or ecological impact.']
    else:
        method=['Selected India monitors: daily PM2.5 >35 µg/m³ and containing CPC TMAX above its local 1991–2020 seasonal 90th percentile. At least 18 distinct valid PM hours.',
                '35 µg/m³ is an atlas comparison threshold, not a safety boundary. '+meta['monitor_class'].title()+' monitors only; classes remain separate.']
        interpretation=['PM Asia/Kolkata dates align with CPC date labels, whose maximum window is 06:00–06:00 UTC. This does not establish hourly simultaneous exposure.',
                        'Each H3 cell-date counts once; BOTH conditions must occur at the same monitor. Selected stations do not form a national exposure surface.']
    periods='Local season / adjacent-year context' if family=='ocean-thermal-season' else ('Matched window' if meta['period']=='matched' else 'Full year' if meta['year']==2025 else 'Year to date')
    subtitle=f'{meta["year"]} / {periods} / source through {meta["data_through"]} / {scope.title()}'
    sections=[{'title':label+' / '+unit,'keys':list(zip(colors,labels))},
              {'title':'Definition','notes':method},{'title':'Reading the result','notes':interpretation}]
    notes=[meta['support'],'Shared scale boundaries across years and views. Gray outlines show source support below the measure’s eligibility rule. Empty space is not an observed zero.',
           'Counts and fractions require at least 80% eligible days in the labeled interval; completed seasons additionally require supported transitions. Actual dates and exclusions are retained in the data ledger.',
           'Local prototype edition with source-specific dates in the selected input ledger. Recent provider values may be revised. No attribution, population exposure or coral-bleaching outcome is inferred.']
    if scope=='japan':notes.append('Yellow point: retained conceptual Setouchi geographic reference, 34.45°N / 133.99°E.')
    sources=['NOAA OISST v2.1 / https://www.ncei.noaa.gov/products/optimum-interpolation-sst',
             'Method, inputs, tables and validation: data/ and validation.json in this dataset output']
    if family in ('coastal-compound-heat','heat-particulate-coexposure'):sources.append('CPC Global Temperature / https://psl.noaa.gov/thredds/catalog/Datasets/cpc_global_temp/catalog.html')
    if family=='heat-particulate-coexposure':sources.append('OpenAQ public archive / selected CPCB, AirNow and separate AirGradient monitors; actual station-days in data/india-station-days.csv.gz')
    return legend(stem,title,subtitle,sections,notes,sources)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--families',nargs='*',default=['marine','season','coastal','india']);p.add_argument('--workers',type=int,default=int(os.environ.get('ASSET_JOBS','2')));p.add_argument('--index-only',action='store_true');a=p.parse_args()
    if a.index_only:
        manifest=json.loads((OUTPUT/'preview-manifest.json').read_text())
        write_index(manifest['products'],manifest['records']);return
    subprocess.run(['make','build/setouchi-h3-tools/render-cells','build/stage-2-project-points'],cwd=ROOT,check=True)
    settings=settings_for(atlas_root(),maps.TEMPLATE,300);india_view(settings)
    env=font_environment();env['TMPDIR']=str(ROOT/'build/tmp')
    entries=[]
    for f in a.families:entries+=json.loads((OUTPUT/'data'/f'{f}-products.json').read_text())
    records=[];products=[];futures=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for meta in entries:
            family=meta['family'];data=dict(np.load(OUTPUT/'data'/meta['data_file']));cells=data['cells']
            metrics={'marine-heatwave':['event_days','longest_duration','cumulative_intensity'],
                     'ocean-thermal-season':['onset_departure','length','length_departure','observed_warm_days'],
                     'coastal-compound-heat':['both_days','fraction'],
                     'heat-particulate-coexposure':['both_days'] if meta.get('monitor_class')=='low-cost' else ['both_days','fraction']}[family]
            scope_list=('world','india') if family=='heat-particulate-coexposure' else ('world','japan')
            for metric in metrics:
                stem=f'anthropocene-{family}-{meta["year"]}'
                variant=f'{meta["period"]}/{metric}'+('/'+meta['monitor_class'] if 'monitor_class' in meta else '')
                directory=OUTPUT/family/variant;tile_dir=OUTPUT/'tiles'/family/str(meta['year'])/variant;tile_dir.mkdir(parents=True,exist_ok=True)
                label,unit,bounds,colors,labels=METRICS[metric];title=label+f' / {meta["year"]}'
                value=data[metric].astype('float64').copy()
                if family=='ocean-thermal-season':
                    observed=np.isfinite(data['threshold']);eligible=np.isfinite(value)
                    if metric=='observed_warm_days':eligible&=(data['valid_days']>=.8*data['available_days'])&(data['available_days']>0)
                    edge=data['status']==6
                    support='OISST 0.25° original centers aggregated to H3r5 with fixed complete membership. Undefined cycles remain explicit; 2025 and 2026 labels refer to expected warm-peak years.'
                else:
                    observed=data.get('observed_days',data['eligible_days'])>0;eligible=data['eligible_days']>=.8*meta['expected_days'];edge=data.get('edge_events',np.zeros(len(cells)))>0
                    if family=='marine-heatwave':edge|=data['pending_days']>0
                    support='OISST 0.25° original centers aggregated to H3r5 with fixed complete membership.' if family=='marine-heatwave' else 'Native CPC coastal pairs displayed at their land-center H3r5 cell; where multiple pairs share a cell, mapped values are their arithmetic mean.' if family=='coastal-compound-heat' else 'Station-supported H3r5 cell-day unions; no interpolation. Hollow supports below 80% coverage remain visible. Monitor/date ledger retains individual observations.'
                value[~eligible]=np.nan
                # A few polar native land centers may share an H3. Preserve
                # the raw pairs and explicitly render their within-cell mean.
                unique,inverse=np.unique(cells,return_inverse=True)
                if len(unique)!=len(cells):
                    good=np.isfinite(value);count=np.bincount(inverse[good],minlength=len(unique));sums=np.bincount(inverse[good],weights=value[good],minlength=len(unique))
                    value=np.divide(sums,count,out=np.full(len(unique),np.nan),where=count>0)
                    observed=np.bincount(inverse,weights=observed,minlength=len(unique))>0;edge=np.bincount(inverse,weights=edge,minlength=len(unique))>0;cells_render=unique
                else:cells_render=cells
                config=deepcopy(settings);config['views']=[v for v in config['views'] if v['id'] in scope_list]
                config['styles']={'support':maps.styles(['#786c78'],True),'value':maps.styles(colors),'open-edge':maps.styles(['#fff6e3'],True)}
                for s in config['styles']['support'].values():s['width']=.006
                if family in ('marine-heatwave','ocean-thermal-season'):
                    for s in config['styles']['open-edge'].values():s['width']=.002
                layers=[maps.layer('support',cells_render,np.ones(len(cells_render)),[],observed),maps.layer('value',cells_render,value,bounds)]
                if np.any(edge):layers.append(maps.layer('open-edge',cells_render,np.ones(len(cells_render)),[],edge&np.isfinite(value)))
                rendered=render_layers(tile_dir,layers,config,OUTPUT/'data'/meta['data_file']);receipt=tile_dir/'inputs.json'
                expanded={**meta,'metric':metric,'support':support,'tile_receipt_sha256':digest(receipt)}
                for scope in scope_list:
                    tree=frame(scope,stem,title,tile_dir,rendered,config,directory,expanded)
                    sheet=make_legend(stem,title,metric,expanded,scope)
                    for kind,doc in [('map',tree),('legend',sheet)]:
                        future=pool.submit(export_sheet,directory,stem,scope,kind,doc,env,OUTPUT)
                        futures.append((future,{'family':family,'metric':metric,'period':meta['period'],'year':meta['year'],'monitor_class':meta.get('monitor_class')}))
                products.append({'stem':stem,'title':title,'metric':metric,'variant':variant,'metadata':expanded})
                print(f'Stage 2 sheets queued: {stem} / {variant}',flush=True)
        for future,extra in futures:records.append({**future.result(),**extra})
    manifest=OUTPUT/'preview-manifest.json'
    if manifest.exists():
        old=json.loads(manifest.read_text());families={e['family'] for e in entries}
        records=[r for r in old['records'] if r['family'] not in families]+records
        products=[r for r in old['products'] if r['metadata']['family'] not in families]+products
    write_json(manifest,{'schema':'cartofreako-stage-2-previews-v1','products':products,'records':records})
    write_index(products,records)
    print(f'Exported {len(records)} Stage 2 sheets',flush=True)


def write_index(products,records):
    methods_href=os.path.relpath(ROOT/"docs/development/20261108_anthropocene_ocean_temperature_stage_2.md",OUTPUT)
    html=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Anthropocene / Stage 2</title><style>body{background:#240413;color:#fcc553;font:18px sans-serif;margin:2rem}a{color:inherit}img{width:100%;height:auto}.pair{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}article{margin:3rem 0}@media(max-width:900px){.pair{display:block}}</style><h1>Anthropocene / Stage 2</h1><p>Local prototype review / dataset-specific observation windows. Separate map and legend/source sheets. Ocean, CPC and India monitor cutoffs are recorded separately in each legend. Use matched support for year comparisons.</p><p><a href="'+methods_href+'">Methods and completion record</a> · <a href="data/india-station-summary.json">Station coverage</a> · <a href="validation.json">Validation</a></p>']
    html.append('<h2>Comparisons and coverage</h2><p><a href="figures/matched-cooccurrence.png">Matched monthly comparisons</a> · <a href="figures/season-coverage.png">Season definitions and coverage</a> · <a href="figures/india-station-coverage.png">India monitor coverage</a> · <a href="figures/event-season-example.png">Event and season example</a></p>')
    for product in products:
        m=product['metadata'];rr=[r for r in records if r['stem']==product['stem'] and r['metric']==product['metric'] and r['period']==m['period'] and r['monitor_class']==m.get('monitor_class')]
        html.append('<article><h2>'+escape(product['title'])+'</h2><p>'+escape(product['variant']+' / source through '+m['data_through'])+'</p><div class="pair">')
        for record in [r for r in rr if r['kind']=='map']:
            l=next(r for r in rr if r['scope']==record['scope'] and r['kind']=='legend')
            html.append(f'<div><h3>{escape(record["scope"].title())}</h3><a href="{record["preview"]}"><img alt="{escape(product["title"]+" / "+record["scope"])}" src="{record["preview"]}"></a><p><a href="{record["pdf"]}">Map PDF</a> · <a href="{record["svg"]}">Map SVG</a> · <a href="{l["preview"]}">Legend preview</a> · <a href="{l["pdf"]}">Legend PDF</a> · <a href="{l["svg"]}">Legend SVG</a></p></div>')
        html.append('</div></article>')
    (OUTPUT/'index.html').write_text('\n'.join(html)+'</html>\n')


if __name__=='__main__':main()
