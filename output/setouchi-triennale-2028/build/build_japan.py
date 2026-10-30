#!/usr/bin/env python3
"""Japan companions: native-projection crops, explicit celestial context sheets."""
from pathlib import Path
from lxml import etree as E
import copy, json, os, subprocess, textwrap, zipfile, sys
OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[1]
NS='http://www.w3.org/2000/svg'
XL='http://www.w3.org/1999/xlink'
SUFFIX='-authagraph-44-19.052559'
JAPAN_OUTLINE_PT=1.0
PARSER=E.XMLParser(huge_tree=True)
def el(name,parent=None,**attrs):
    e=E.Element('{'+NS+'}'+name,nsmap={None:NS}) if parent is None else E.SubElement(parent,'{'+NS+'}'+name)
    for k,v in attrs.items():e.set(k.replace('_','-'),str(v))
    return e
def text(parent,x,y,value,size=.28,weight='normal',color='#202020'):
    e=el('text',parent,x=x,y=y,font_family='Liberation Sans',font_size=size,font_weight=weight,fill=color)
    e.text=value
    return e
def lines(parent,x,y,value,width=62,size=.23):
    for line in textwrap.wrap(value,width=width):
        text(parent,x,y,line,size);y+=size*1.5
    return y
def project(coords):
    p=subprocess.run([str(OUT/'build/project-points')],input=''.join(f'{x} {y}\n' for x,y in coords),capture_output=True,text=True,check=True)
    return [tuple(map(float,line.split())) for line in p.stdout.splitlines()]
def bounds(coords,pad=.12):
    pts=project(coords);xs,ys=zip(*pts)
    return [min(xs)-pad,min(ys)-pad,max(xs)-min(xs)+2*pad,max(ys)-min(ys)+2*pad]
def view(parent,x,y,w,h,box,ref='source-content'):
    clipid=f'viewport-{len(parent)}-{str(x).replace(".","-")}-{str(y).replace(".","-")}'
    clip=el('clipPath',parent,id=clipid,clipPathUnits='userSpaceOnUse')
    el('rect',clip,x=x,y=y,width=w,height=h)
    outer=el('g',parent,clip_path=f'url(#{clipid})')
    scale=min(w/box[2],h/box[3])
    dx=x+(w-box[2]*scale)/2-box[0]*scale
    dy=y+(h-box[3]*scale)/2-box[1]*scale
    v=el('g',outer,transform=f'translate({dx} {dy}) scale({scale})')
    u=el('use',v);u.set('{'+XL+'}href','#'+ref)
    return v

country_dir=OUT/'sources/japan-admin0-10m'
country_dir.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT/'sources/japan-admin0-10m.zip') as z:z.extractall(country_dir)
country_json=country_dir/'japan.geojson'
if not country_json.exists():
    subprocess.run(['ogr2ogr','-f','GeoJSON',str(country_json),str(country_dir/'ne_10m_admin_0_countries.shp'),'-where',"ADM0_A3 = 'JPN'"],check=True)
features=json.loads(country_json.read_text())['features'];assert len(features)==1
geo=features[0]['geometry']
(OUT/'sources/japan-boundary.geojson').write_text(json.dumps({'type':'Feature','properties':{'source':'Natural Earth 1:10m Admin 0','iso3':'JPN'},'geometry':geo})+'\n')
rings=[ring for poly in geo['coordinates'] for ring in poly] if geo['type']=='MultiPolygon' else geo['coordinates']
projected=[project(r) for r in rings]
coords=[pt for ring in rings for pt in ring]
box=bounds(coords,.2)
setobox=bounds([(lon,lat) for lon in [131.5,132.5,133.5,134.5,135.5] for lat in [33.2,34,34.8,35.5]],.04)
mark=project([(133.99,34.45)])[0]
(OUT/'sources/japan-view.json').write_text(json.dumps({'country':'JPN','boundary_source':'Natural Earth Admin 0, 1:10m','world_viewbox':box,'setouchi_viewbox':setobox,'reference_point':{'lon':133.99,'lat':34.45,'meaning':'conceptual Setouchi reference, not a confirmed venue'},'native_reference_point':mark},indent=2)+'\n')

plan=json.loads((OUT/'sources/generation-plan.json').read_text())
data=OUT/'sources/data'
inputs=OUT/'build/japan-sky'
inputs.mkdir(exist_ok=True)
env=dict(os.environ,NATURAL_EARTH_DIR=str(ROOT/'assets.static/natural-earth/10m-physical-vectors'),CARTOFREAKO_LABEL_FONT='atkinson_hyperlegible')
sky_profiles=[]
profile=json.loads((data/'astronomy/astro-profile.json').read_text())
profile['name']='Setouchi ground multi-band sky'
profile['observer'].update(name='Setouchi reference, Japan',latitude_deg=34.45,longitude_deg_east=133.99,elevation_m=0)
path=data/'astronomy/astro-setouchi-profile.json';path.write_text(json.dumps(profile,indent=2)+'\n')
sky_profiles.append(('astro-observer-ground-multiband','astro',['authagraph','observer',str(path)]))
profile=json.loads((data/'orbital-technosphere/orbital-technosphere-profile.json').read_text())
profile['name']='Setouchi Orbital Technosphere'
profile['reference_point'].update(name='Setouchi reference, Japan',latitude_deg=34.45,longitude_deg_east=133.99,elevation_m=0,capture_method='Explicit conceptual Setouchi reference; venue unconfirmed')
path=data/'orbital-technosphere/orbital-setouchi-profile.json';path.write_text(json.dumps(profile,indent=2)+'\n')
sky_profiles.append(('orbital-technosphere-observer','orbiting',['authagraph','observer',str(path)]))
for stem,gen,args in sky_profiles:
    if len(sys.argv)>1 and stem not in sys.argv[1:]:continue
    with (OUT/'logs'/f'japan-sky-{stem}.log').open('w') as log:
        subprocess.run([str(OUT/'build'/('generate-'+gen)),*args],cwd=inputs,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
res_profile=json.loads((data/'resources/resources-profile.json').read_text())
values=json.loads((data/'resources/resources-values.json').read_text())['records']
metric_map={f['id']+'-'+m.get('output_tag',''):m for f in res_profile['families'] for m in f['metrics'] if m.get('output_tag')}
records={r['family']+':'+r['metric']:r for r in values if r['iso3']=='JPN'}
results=[]
dest=OUT/'plates/japan/svg';dest.mkdir(parents=True,exist_ok=True)
for item in plan['plates']:
    if len(sys.argv)>1 and item['stem'] not in sys.argv[1:]:continue
    stem=item['stem'];sky=stem.startswith('astro-') or stem=='orbital-technosphere-observer'
    if stem.startswith('network-swarm-'):
        if not (dest/(stem+SUFFIX+'-japan.svg')).exists():
            subprocess.run(['python3',str(OUT/'build/build_swarm.py'),'--compose-only','--band',stem.removeprefix('network-swarm-')],check=True)
        results.append({'stem':stem,'kind':'authagraph-swarm-detail','projection':'AuthaGraph','file':'plates/japan/svg/'+stem+SUFFIX+'-japan.svg'})
        continue
    src=(inputs if stem in [p[0] for p in sky_profiles] else OUT/'plates/world/svg')/(stem+SUFFIX+'.svg')
    root=E.parse(str(src),PARSER).getroot()
    if stem=='network-fiber':
        # Preserve a physical 0.5 pt route stroke after the Japan enlargement.
        # Native SVG coordinates are inches; landing symbols remain separate.
        route_scale=min(28/box[2],15/box[3])
        for route in root.iter():
            if route.get('data-fiber-route')!='true' and route.get('data-itu-fiber-route')!='true':continue
            style=dict(part.strip().split(':',1) for part in route.get('style','').split(';') if ':' in part)
            style['stroke-width']=f'{0.5/72/route_scale:.12g}'
            style['stroke-opacity']='0.75'
            route.set('style','; '.join(f'{k}:{v}' for k,v in style.items()))
        for landing in root.xpath('//*[@data-fiber-landing="true"]'):
            landing.set('r',f'{float(landing.get("r"))*0.5:.12g}')
            style=dict(part.strip().split(':',1) for part in landing.get('style','').split(';') if ':' in part)
            style['stroke-width']=f'{0.5/72/route_scale:.12g}'
            landing.set('style','; '.join(f'{k}:{v}' for k,v in style.items()))
    elif stem=='cloud-atmosphere':
        detail_scale=min(28/box[2],15/box[3])
        for coast in root.xpath('//*[@id="terrestrial-coastline"]//*[local-name()="path"]'):
            style=dict(part.strip().split(':',1) for part in coast.get('style','').split(';') if ':' in part)
            style['stroke-width']=f'{JAPAN_OUTLINE_PT/72/detail_scale:.12g}'
            coast.set('style','; '.join(f'{k}:{v}' for k,v in style.items()))
    elif stem=='water':
        # Keep physical strokes independent of the Japan enlargement.
        # Water's separate coastline layer must match the shared Japan outline.
        detail_scale=min(28/box[2],15/box[3])
        for coast in root.xpath('//*[@id="coastline"]//*[local-name()="path"]'):
            style=dict(part.strip().split(':',1) for part in coast.get('style','').split(';') if ':' in part)
            style['stroke-width']=f'{JAPAN_OUTLINE_PT/72/detail_scale:.12g}'
            coast.set('style','; '.join(f'{k}:{v}' for k,v in style.items()))
        for river in root.xpath('//*[@id="rivers"]//*[local-name()="path"]'):
            style=dict(part.strip().split(':',1) for part in river.get('style','').split(';') if ':' in part)
            style['stroke-width']=f'{1.5/72/detail_scale:.12g}'
            river.set('style','; '.join(f'{k}:{v}' for k,v in style.items()))
    elif stem=='network-cdn':
        label_scale=min(28/box[2],15/box[3])
        for label in root.xpath('//*[@id="cdn-labels"]/*[local-name()="text"]'):
            label.set('font-size',str(.18/label_scale))
            label.set('stroke-width',str(.035/label_scale))
    doc=el('svg',width='44in',height='19.052559in',viewBox='0 0 44 19.052559',role='img')
    el('title',doc).text='Japan / '+item['title']
    el('desc',doc).text=('Setouchi sky context; celestial axes, not a geographic crop. ' if sky else 'Japan enlargement of the parent AuthaGraph plate in the native projection. ')+item['note']
    defs=el('defs',doc);content=el('g',defs,id='source-content')
    legends=[]
    for child in root:
        if E.QName(child).localname not in ['title','desc']:
            if 'legend' in child.get('id',''):legends.append(copy.deepcopy(child))
            content.append(copy.deepcopy(child))
    el('rect',doc,width=44,height=19.052559,fill='white')
    text(doc,.7,.8,'JAPAN / '+item['title'],.5,'bold')
    text(doc,.7,1.35,'SETOUCHI TRIENNALE 2028  /  CARTOFREAKO  /  STUDY EDITION · 29 OCT 2026',.21,color='#555555')
    mainbox=[0,0,44,19.052559] if sky else box
    main=view(doc,.7,2,28,15,mainbox)
    if not sky:
        for ring in projected:
            d='M '+' L '.join(f'{x:.6f} {y:.6f}' for x,y in ring)+' Z'
            el('path',main,d=d,fill='none',stroke='#202020',stroke_width=JAPAN_OUTLINE_PT/72/min(28/box[2],15/box[3]),opacity='.8',data_japan_outline='true')
        el('circle',main,cx=mark[0],cy=mark[1],r='.045',fill='#fae63d',stroke='#111',stroke_width='.012')
    text(doc,30,2.35,'READ THIS PLATE',.3,'bold')
    if sky:
        explanation = ('Sky calculated from Setouchi, Japan, at '+plan['instant']+'. The map shows celestial directions. It is not a map of Japanese territory.' if stem in [p[0] for p in sky_profiles] else 'This parent plate uses celestial coordinates. A geographic Japan crop is not defined. The full sky is retained here; the locator below supplies Japan context. Hubble visibility does not describe a ground view from Japan.' if 'hubble' in stem else 'This all-sky atlas uses celestial coordinates. A geographic Japan crop is not defined. The shared sky is retained here; the locator below supplies Japan context.')
    else:
        explanation='Japan is outlined in black. The yellow point marks a conceptual Setouchi reference (34.45 N, 133.99 E), not an agreed exhibition site. The crop preserves AuthaGraph geometry and the parent plate scale.'
    y=lines(doc,30,2.9,explanation,width=70,size=.235)
    metric=metric_map.get(stem)
    if metric:
        family=next(f['id'] for f in res_profile['families'] if metric in f['metrics'])
        row=records.get(family+':'+metric['id'])
        y+=.45;text(doc,30,y,'JAPAN VALUE',.25,'bold');y+=.5
        if row:
            text(doc,30,y,f"{row['value']:,.2f}".rstrip('0').rstrip('.'),.55,'bold');y+=.45
            y=lines(doc,30,y,f"{metric['unit']} · observation year {row['year']} · {row['state']}",size=.24)
        elif metric.get('spatial'):
            y=lines(doc,30,y,'Spatial layer; no single Japan country value is defined.',size=.24)
        else:y=lines(doc,30,y,'No reported Japan value in this source. Missing is not zero.',size=.24)
    y=max(y+.4,6)
    text(doc,30,y,'SOURCE AND LIMIT',.25,'bold');y+=.45
    # The raw snapshot dictionary is retained in the manifest, not printed as prose.
    note=item['note']
    if stem.startswith('anthropocene-'):
        prof=json.loads(Path(item['command'][2]).read_text())
        snap=prof.get('snapshot',{})
        note=f"Observation cutoff: {snap.get('data_through','source-specific')}. "+('Partial 2026 year. ' if '2026' in stem else '2025 calendar; source coverage varies. ')+note.split('}. ')[-1]
    y=lines(doc,30,y,note,width=73,size=.22)
    if stem.startswith('anthropocene-particulate-'):
        year=int(stem.rsplit('-',1)[1])
        coverage=json.loads((data/'anthropocene/pm25-enrichment-quality.json').read_text())['country_coverage']
        jp=next(r for r in coverage if r['year']==year and r['country']=='JPN' and r['instrument_class']=='monitor')
        text(doc,30,9.4,'JAPAN / MEASURED PM2.5',.25,'bold')
        lines(doc,30,9.9,f"{jp['stations']:,} reporting stations; {jp['h3_cells']} observed H3 cells. {jp['first_date']} to {jp['last_date']}. Teal rings show valid measured days; orange crosses show days when any monitor's daily mean exceeded 35 micrograms per cubic metre. At least 18 valid hours per station-day; provisional MOE data. A covered cell without an orange cross has no qualifying exceedance in its available records.",width=73,size=.22)
    if stem=='network-cdn':
        import math
        vendors=json.loads((OUT/'sources/data/cdn/vendors.json').read_text())
        used={json.loads(line)['vendor_id'] for line in (OUT/'sources/data/cdn/records.jsonl').read_text().splitlines() if json.loads(line)['display_coordinates']}
        vendors=sorted([v for v in vendors if v['id'] in used],key=lambda v:v['label'].lower())
        text(doc,30,9.25,'VENDORS / SAME COLOURS',.24,'bold')
        for i,v in enumerate(vendors):
            x=30+(i%2)*6.25;y=9.75+(i//2)*.36
            points=' '.join(f'{x+.085*math.cos(math.pi*j/3)},{y+.085*math.sin(math.pi*j/3)}' for j in range(6))
            el('polygon',doc,points=points,fill=v['color'],fill_opacity='.33',stroke=v['color'],stroke_width='.006')
            text(doc,x+.18,y,v['label'],.205)
        lines(doc,30,15.4,'Hexagons count typed source records (cap 320). Solid triangles mark approximate references; dashed triangles are separate locality claims.',width=76,size=.22)
    elif not sky and legends:
        legend=legends[0]
        query=subprocess.run(['inkscape',str(src),'--query-id='+legend.get('id'),'--query-x','--query-y','--query-width','--query-height'],capture_output=True,text=True,check=True,env=dict(env,INKSCAPE_PROFILE_DIR=str(OUT/'build/inkscape-config/japan-legend-query')))
        bx,by,bw,bh=[float(v)/96 for v in query.stdout.splitlines()[-4:]]
        scale=min(12.5/bw,3.2/bh)
        holder=el('g',doc,transform=f'translate({30-bx*scale} {13.5-by*scale}) scale({scale})')
        legend.set('id','japan-parent-legend');holder.append(legend)
        text(doc,30,13.1,'PARENT LEGEND · SAME UNITS AND COLOURS',.2,color='#555555')
    # Compact original or geographic locator at the bottom of the right column.
    if sky:
        land=E.parse(str(OUT/'plates/world/svg'/('earth'+SUFFIX+'.svg')),PARSER).getroot()
        landg=el('g',defs,id='japan-earth-context')
        for child in land:
            if E.QName(child).localname not in ['title','desc']:
                child=copy.deepcopy(child)
                for e in child.iter():
                    if e.get('id'):e.set('id','locator-'+e.get('id'))
                landg.append(child)
        v=view(doc,30,10.7,12.5,5.8,box,'japan-earth-context')
        el('circle',v,cx=mark[0],cy=mark[1],r='.055',fill='#fae63d',stroke='#111',stroke_width='.014')
        text(doc,30,10.35,'JAPAN / GEOGRAPHIC LOCATOR',.24,'bold')
    else:
        text(doc,.7,17.75,'ENLARGEMENT OF THE GLOBAL PLATE · COASTLINES 1:10m; RESOURCE COUNTRIES 1:110m',.22,color='#555555')
    text(doc,.7,18.45,'44 × 19.052559 in · Vector master · PNG 300 dpi · Country totals do not resolve individual islands.',.22,color='#555555')
    text(doc,30,18.45,'Reference and source notes: sources/generation-plan.json',.19,color='#555555')
    target=dest/(stem+SUFFIX+'-japan.svg')
    E.ElementTree(doc).write(str(target),encoding='UTF-8',xml_declaration=True)
    results.append({'stem':stem,'kind':'celestial-context' if sky else 'geographic-enlargement','file':str(target.relative_to(OUT))})
    print('Japan',stem,flush=True)
manifest=OUT/'sources/japan-companions.json'
if len(sys.argv)>1 and manifest.exists():
    results=[r for r in json.loads(manifest.read_text()) if r['stem'] not in sys.argv[1:]]+results
manifest.write_text(json.dumps(results,indent=2)+'\n')
