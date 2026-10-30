#!/usr/bin/env python3
"""Apply the current Alpha60 vendor-reel encodings to the native atlas map."""
from plate_tools import *
import collections, hashlib, json
ALPHA=Path('/home/bkoz/src/alpha60')
CONFIG=ALPHA/'config/cartography/cdn-vendor-video-20261023-r8.json'
DATA=OUT/'sources/data/cdn'
def main():
    subprocess.run([str(OUT/'build/load-cdn'),str(CONFIG),str(DATA)],check=True)
    cfg=json.loads(CONFIG.read_text());audit=json.loads((DATA/'loader-audit.json').read_text())
    assert [audit[k] for k in ('canonical_records','source_coordinates','derived_references','unplotted')]==[28243,13140,1405,13698]
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
        key=(r['vendor_id'],r['disposition'],r['source_scope'],r['entity_type'],round(x/.0625),round(y/.0625))
        g=groups.setdefault(key,{'vendor':r['vendor_id'],'approximate':r['approximate'],'x':x,'y':y,'records':[],'names':[]})
        g['records'].append(r['record_id'])
        if r['display_name']:g['names'].append(r['display_name'])
    groups=sorted(groups.values(),key=lambda g:(g['vendor'],g['records'][0]))
    doc=base('Network CDN / 21 October 2026','Alpha60 r8 vendor palette, radial honeycombs and separate approximate-reference triangles. Symbols count typed source records, not unique facilities, traffic or power.')
    defs=el('defs',doc);layer=el('g',doc,id='cdn-honeycombs')
    cell=cfg['scales']['hex_radius']*cfg['vendor_plates']['honeycomb_size_multiplier']/96
    def honey(parent,x,y,n,color,opacity=.33):
        for dx,dy in hexoffsets(min(n,320),cell):
            el('polygon',parent,points=hexpoints(x+dx,y+dy,cell*.94),fill=color,fill_opacity=opacity,stroke=color,stroke_opacity=1,stroke_width=.0035)
    for i,g in enumerate(groups):
        color=vendors[g['vendor']]['color'];x,y=g['x'],g['y'];n=len(g['records'])
        item=el('g',layer,data_group=i,data_records=n,data_approximate=str(g['approximate']).lower())
        el('title',item).text=f"{vendors[g['vendor']]['label']}: {n} source records; "+('approximate reference' if g['approximate'] else 'source coordinates')
        if g['approximate']:
            r=.09375;points=f'{x},{y-r} {x+r*.866},{y+r*.5} {x-r*.866},{y+r*.5}'
            clip=el('clipPath',defs,id=f'cdn-triangle-{i}');el('polygon',clip,points=points)
            h=el('g',item,clip_path=f'url(#cdn-triangle-{i})');honey(h,x,y,37,color)
            el('polygon',item,points=points,fill='none',stroke=color,stroke_width=.006)
        else:honey(item,x,y,n,color)
    claims=el('g',doc,id='cdn-independent-locality-claims')
    independent=[r for r in refs if r['independent_mark']]
    for r,(x,y) in zip(independent,project([r['display_coordinates'] for r in independent])):
        color=vendors[r['vendor_id']]['color'];rr=.09375
        p=el('polygon',claims,points=f'{x},{y-rr} {x+rr*.866},{y+rr*.5} {x-rr*.866},{y+rr*.5}',fill='none',stroke=color,stroke_width=.006,stroke_dasharray='.012 .006',data_claim=r['footprint_id'])
        el('title',p).text=r['display_name']+'; independent locality assertion; excluded from canonical weights'
    labels=el('g',doc,id='cdn-labels');taken=[];seen=set();label_counts=collections.Counter()
    for g in sorted(groups,key=lambda g:(-len(g['records']),g['records'][0])):
        if not g['names'] or label_counts[g['vendor']]>=5:continue
        name=collections.Counter(g['names']).most_common(1)[0][0]
        if name in seen:continue
        x,y=g['x'],g['y'];w=max(.25,len(name)*.085)
        if y>15.1 or y<.2 or x-w/2<.15 or x+w/2>43.85 or any(abs(x-xx)<(w+ww)/2+.1 and abs(y-yy)<.30 for xx,yy,ww in taken):continue
        txt(labels,x,y,name,.18,text_anchor='middle',paint_order='stroke fill',stroke='white',stroke_width=.035,stroke_linejoin='round')
        taken.append((x,y,w));seen.add(name);label_counts[g['vendor']]+=1
    legend=el('g',doc,id='cdn-legend')
    el('rect',legend,x=16.5,y=14.9,width=27,height=3.8,fill='white')
    txt(legend,43,15.35,'NETWORK CDN / 21 OCTOBER 2026',.38,text_anchor='end',font_weight='bold')
    used=sorted((v for v in vendors.values() if any(g['vendor']==v['id'] for g in groups)),key=lambda v:v['label'].lower())
    for i,v in enumerate(used):
        x=16.9+(i%5)*5.25;y=15.9+(i//5)*.29
        el('polygon',legend,points=hexpoints(x,y,.08),fill=v['color'],fill_opacity=.33,stroke=v['color'],stroke_width=.006)
        txt(legend,x+.16,y,v['label'],.15)
    txt(legend,16.9,17.65,'Honeycomb: typed source records (1 cell/record; cap 320). Triangle: approximate city/area reference.',.18)
    txt(legend,16.9,17.98,'Dashed triangle: separate locality claim. Locations are not a verified census of active facilities.',.18)
    txt(legend,16.9,18.31,'28,243 records: 13,140 source coordinates; 1,405 inferred references; 13,698 unplotted. 80 separate claims.',.18)
    save(doc,OUT/'plates/world/svg'/('network-cdn'+SUFFIX+'.svg'))
    (DATA/'display-groups.json').write_text(json.dumps(groups,indent=2)+'\n')
    audit.update(source_repository='/home/bkoz/src/cloud_cdn_cache.bkoz',source_revision=cfg['delivery']['source_revision'],manifest=cfg['manifest'],manifest_sha256=cfg['manifest_sha256'],visual_reference=str(CONFIG),visual_reference_sha256=hashlib.sha256(CONFIG.read_bytes()).hexdigest(),groups=len(groups),group_record_total=sum(len(g['records']) for g in groups),independent_claims=len(independent),fill_opacity=.33,hex_radius_inches=cell,label_count=len(taken),adaptation='Native AuthaGraph screen cells 0.0625 in; evidence types kept separate. At most five labels per vendor, collision filtered across all vendors. No Star-X crop or vendor video frames.')
    assert audit['group_record_total']==14545
    (OUT/'sources/cdn-refresh.json').write_text(json.dumps(audit,indent=2)+'\n')
    print('CDN atlas:',len(groups),'groups;',len(taken),'labels',flush=True)
if __name__=='__main__':main()
