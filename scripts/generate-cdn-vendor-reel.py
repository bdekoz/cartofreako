#!/usr/bin/env python3
"""Generate the default CDN honeycombs with Alpha60 canonical record accounting."""
from cartofreako_style import ROOT, STYLE, Projection, digest, el, txt, save, hexpoints, hexoffsets
from pathlib import Path
import argparse, collections, json, subprocess

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--projection',default=STYLE['default_projection'])
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--source-profile',type=Path,default=ROOT/'config/cdn-sources.json')
    parser.add_argument('--work-dir',type=Path)
    args=parser.parse_args()
    projection=Projection(args.projection,args.work_dir)
    DATA=projection.work/'cdn';DATA.mkdir(parents=True,exist_ok=True)
    cfg=json.loads(args.source_profile.read_text())
    def resolve(node):
        if isinstance(node,dict):
            for key,value in node.items():
                if isinstance(value,str) and (key in ['manifest','city_lookup','country_registry','path','file'] or value.endswith('.json')):
                    candidate=(args.source_profile.parent/value).resolve()
                    if candidate.is_file(): node[key]=str(candidate)
                else: resolve(value)
        elif isinstance(node,list):
            for child in node: resolve(child)
    resolve(cfg);cfg['vendors']=STYLE['cdn']['vendors']
    CONFIG=DATA/'loader-config.json';CONFIG.write_text(json.dumps(cfg,indent=2)+'\n')
    subprocess.run([str(ROOT/'build/export-cdn-records'),str(CONFIG),str(DATA)],check=True)
    audit=json.loads((DATA/'loader-audit.json').read_text())
    snapshot=Path(cfg['manifest']).stem.removeprefix('manifest.')
    width,height=projection.width,projection.height
    project=projection.project
    base=projection.base
    records=[json.loads(l) for l in (DATA/'records.jsonl').read_text().splitlines()]
    refs=[json.loads(l) for l in (DATA/'locality-references.jsonl').read_text().splitlines()]
    vendors={v['id']:v for v in cfg['vendors']}
    (DATA/'vendors.json').write_text(json.dumps(cfg['vendors'],indent=2)+'\n')
    plotted=[r for r in records if r['display_coordinates']]
    projected=project([r['display_coordinates'] for r in plotted])
    # Deterministic native-screen grouping. Keep evidence families and source /
    # inferred coordinates separate; never add locality claims to row weights.
    groups={}
    for r,(x,y) in zip(plotted,projected):
        key=(r['vendor_id'],r['disposition'],r['source_scope'],r['entity_type'],round(x/STYLE['cdn']['group_grid_in']),round(y/STYLE['cdn']['group_grid_in']))
        g=groups.setdefault(key,{'vendor':r['vendor_id'],'approximate':r['approximate'],'x':x,'y':y,'records':[],'names':[]})
        g['records'].append(r['record_id'])
        if r['display_name']:g['names'].append(r['display_name'])
    groups=sorted(groups.values(),key=lambda g:(g['vendor'],g['records'][0]))
    doc=base('Network CDN / '+snapshot,'Alpha60 r8 vendor palette, radial honeycombs and separate approximate-reference triangles. Symbols count typed source records, not unique facilities, traffic or power.')
    defs=el('defs',doc);layer=el('g',doc,id='cdn-honeycombs')
    cell=STYLE['cdn']['hex_radius_in']
    def honey(parent,x,y,n,color,opacity=STYLE['cdn']['fill_opacity']):
        for dx,dy in hexoffsets(min(n,STYLE['cdn']['record_cap']),cell):
            el('polygon',parent,points=hexpoints(x+dx,y+dy,cell*.94),fill=color,fill_opacity=opacity,stroke=color,stroke_opacity=1,stroke_width=STYLE['cdn']['outline_in'])
    for i,g in enumerate(groups):
        color=vendors[g['vendor']]['color'];x,y=g['x'],g['y'];n=len(g['records'])
        item=el('g',layer,data_group=i,data_records=n,data_approximate=str(g['approximate']).lower())
        el('title',item).text=f"{vendors[g['vendor']]['label']}: {n} source records; "+('approximate reference' if g['approximate'] else 'source coordinates')
        if g['approximate']:
            r=STYLE['cdn']['reference_radius_in'];points=f'{x},{y-r} {x+r*.866},{y+r*.5} {x-r*.866},{y+r*.5}'
            clip=el('clipPath',defs,id=f'cdn-triangle-{i}');el('polygon',clip,points=points)
            h=el('g',item,clip_path=f'url(#cdn-triangle-{i})');honey(h,x,y,37,color)
            el('polygon',item,points=points,fill='none',stroke=color,stroke_width=STYLE['cdn']['reference_outline_in'])
        else:honey(item,x,y,n,color)
    claims=el('g',doc,id='cdn-independent-locality-claims')
    independent=[r for r in refs if r['independent_mark']]
    for r,(x,y) in zip(independent,project([r['display_coordinates'] for r in independent])):
        color=vendors[r['vendor_id']]['color'];rr=STYLE['cdn']['reference_radius_in']
        p=el('polygon',claims,points=f'{x},{y-rr} {x+rr*.866},{y+rr*.5} {x-rr*.866},{y+rr*.5}',fill='none',stroke=color,stroke_width=STYLE['cdn']['reference_outline_in'],stroke_dasharray='.012 .006',data_claim=r['footprint_id'])
        el('title',p).text=r['display_name']+'; independent locality assertion; excluded from canonical weights'
    labels=el('g',doc,id='cdn-labels');taken=[];seen=set();label_counts=collections.Counter()
    for g in sorted(groups,key=lambda g:(-len(g['records']),g['records'][0])):
        if not g['names'] or label_counts[g['vendor']]>=STYLE['cdn']['maximum_labels_per_vendor']:continue
        name=collections.Counter(g['names']).most_common(1)[0][0]
        if name in seen:continue
        x,y=g['x'],g['y'];w=max(.25,len(name)*.085)
        if y>height-3.95 or y<.2 or x-w/2<.15 or x+w/2>width-.15 or any(abs(x-xx)<(w+ww)/2+.1 and abs(y-yy)<.30 for xx,yy,ww in taken):continue
        txt(labels,x,y,name,.18,text_anchor='middle',paint_order='stroke fill',stroke='white',stroke_width=.035,stroke_linejoin='round')
        taken.append((x,y,w));seen.add(name);label_counts[g['vendor']]+=1
    legend=el('g',doc,id='cdn-legend',transform=f'translate({width-44} {height-19.052559})')
    el('rect',legend,x=16.5,y=14.9,width=27,height=3.8,fill='white')
    txt(legend,43,15.35,'NETWORK CDN / '+snapshot,.38,text_anchor='end',font_weight='bold')
    used=sorted((v for v in vendors.values() if any(g['vendor']==v['id'] for g in groups)),key=lambda v:v['label'].lower())
    for i,v in enumerate(used):
        x=16.9+(i%5)*5.25;y=15.9+(i//5)*.29
        el('polygon',legend,points=hexpoints(x,y,.08),fill=v['color'],fill_opacity=STYLE['cdn']['fill_opacity'],stroke=v['color'],stroke_width=STYLE['cdn']['reference_outline_in'])
        txt(legend,x+.16,y,v['label'],.15)
    txt(legend,16.9,17.65,f"Honeycomb: typed source records (1 cell/record; cap {STYLE['cdn']['record_cap']}). Triangle: approximate city/area reference.",.18)
    txt(legend,16.9,17.98,'Dashed triangle: separate locality claim. Locations are not a verified census of active facilities.',.18)
    txt(legend,16.9,18.31,f"{audit['canonical_records']:,} records: {audit['source_coordinates']:,} source coordinates; {audit['derived_references']:,} references; {audit['unplotted']:,} unplotted. {len(independent)} separate claims.",.18)
    save(doc,args.output)
    (DATA/'display-groups.json').write_text(json.dumps(groups,indent=2)+'\n')
    audit.update(source_profile=str(args.source_profile.resolve()),manifest=cfg['manifest'],manifest_sha256=cfg['manifest_sha256'],projection=projection.name,style_sha256=digest(ROOT/'generation-style.json'),groups=len(groups),group_record_total=sum(len(g['records']) for g in groups),independent_claims=len(independent),fill_opacity=STYLE['cdn']['fill_opacity'],hex_radius_inches=cell,label_count=len(taken))
    assert audit['group_record_total']==audit['source_coordinates']+audit['derived_references']
    args.output.with_suffix('.provenance.json').write_text(json.dumps(audit,indent=2)+'\n')
    print('CDN atlas:',len(groups),'groups;',len(taken),'labels',flush=True)
if __name__=='__main__':main()
