#!/usr/bin/env python3
"""Compare bounded Voronoi, honeycomb and composition glyphs without inventing reef area."""
from plate_tools import *
import collections,json,hashlib,html
from shapely import MultiPoint, Point, voronoi_polygons
DATA=OUT/'sources/data/resources/coral-reefs-025deg.geojson'
DEST=OUT/'prototypes/coral-reef'
NAMES=['Low','Medium','High','Very high']
COLORS=[c['hex'] for c in json.loads((OUT/'sources/resource-color-assignments.json').read_text())['metrics']['coral-reef-threat']]
def cube_round(x,y,size):
    q=2*x/3/size;r=(-x/3+math.sqrt(3)*y/3)/size
    a,b,c=round(q),round(-q-r),round(r)
    da,db,dc=abs(a-q),abs(b+q+r),abs(c-r)
    if da>db and da>dc:a=-b-c
    elif db>dc:b=-a-c
    else:c=-a-b
    return a,c
def allocation(counts,cap=61):
    n=sum(counts)
    if n<=cap:return counts
    # Preserve every present class in a capped composition sample.
    result=[int(c>0) for c in counts];left=cap-sum(result)
    exact=[left*c/n for c in counts];base=[int(v) for v in exact]
    for i in range(4):result[i]+=base[i]
    for i in sorted(range(4),key=lambda i:(-(exact[i]-base[i]),i))[:cap-sum(result)]:result[i]+=1
    return result
def legend(doc,variant):
    g=el('g',doc,id='reef-legend');el('rect',g,x=17,y=15.35,width=26.3,height=3.35,fill='white')
    txt(g,42.9,15.8,'CORAL REEF / LOCAL THREAT / 2011',.37,text_anchor='end',font_weight='bold')
    for i,(c,n) in enumerate(zip(COLORS,NAMES)):
        el('rect',g,x=17.4+i*4.3,y=16.15,width=.45,height=.3,fill=c)
        txt(g,18+i*4.3,16.3,n,.22)
    desc={'honeycomb':'Radial honeycomb: one microhex per source grid cell, capped at 61 per group; class proportions retained.',
          'voronoi':'Bounded Voronoi: one cell per original source cell; display support clipped to 0.075 in from its centre.',
          'clusters':'Composition circles: area scales with source grid-cell count; sectors show threat-class shares.'}[variant]
    txt(g,17.4,16.95,desc,.20)
    txt(g,17.4,17.37,'7,215 occupied 0.25 degree cells; highest source threat per original cell. WRI Reefs at Risk Revisited 2011.',.20)
    txt(g,17.4,17.79,'Grouping is for legibility. Symbol areas are not reef area, threatened hectares or current reef condition.',.20)
    txt(g,17.4,18.21,'Solid izzi-hue colours. Blank: no mapped source cell. All memberships and class counts are retained.',.20)
def japan(doc,variant):
    view=json.loads((OUT/'sources/japan-view.json').read_text());box=view['world_viewbox'];scale=min(28/box[2],15/box[3])
    out=el('svg',width='44in',height='19.052559in',viewBox='0 0 44 19.052559',role='img')
    el('title',out).text='Japan coral threat / '+variant;el('rect',out,width=44,height=19.052559,fill='white')
    defs=el('defs',out);clip=el('clipPath',defs,id='reef-japan-crop');el('rect',clip,x=.7,y=2,width=28,height=15)
    outer=el('g',out,clip_path='url(#reef-japan-crop)');dx=.7+(28-box[2]*scale)/2-box[0]*scale;dy=2+(15-box[3]*scale)/2-box[1]*scale
    g=el('g',outer,transform=f'translate({dx} {dy}) scale({scale})')
    for child in doc:
        if child.get('id') in ['land','reef-groups']:g.append(copy.deepcopy(child))
    geo=json.loads((OUT/'sources/japan-boundary.geojson').read_text())['geometry'];rings=[r for poly in geo['coordinates'] for r in poly]
    for ring in rings:
        pts=project(ring);el('path',g,d='M '+' L '.join(f'{x} {y}' for x,y in pts)+' Z',fill='none',stroke='#202020',stroke_width=1/72/scale)
    txt(out,.7,.8,'JAPAN / CORAL REEF / '+variant.upper(),.48,font_weight='bold')
    txt(out,.7,1.4,'WRI 2011 historical baseline / AuthaGraph enlargement / display groups, not reef footprints',.23)
    for i,(c,n) in enumerate(zip(COLORS,NAMES)):
        el('rect',out,x=30,y=3+i*.6,width=.5,height=.35,fill=c);txt(out,30.8,3.18+i*.6,n,.28)
    notes=['Source: 0.25 degree presence grid derived from reef polygons.',
           'Each original grid cell retains its highest threat class.',
           'Source grid-cell count is not an area measurement.',
           'Groups show local class composition; labels describe the display.',
           'No present-day reef condition is inferred from the 2011 baseline.',
           'Japan coastline: 1 pt. Empty areas have no mapped source cells.']
    import textwrap
    y=6.1
    for note in notes:
        for line in textwrap.wrap(note,65):txt(out,30,y,line,.25);y+=.37
        y+=.35
    txt(out,.7,18.3,'PROTOTYPE / '+variant+' / Compare the global and Japan views before final exhibition selection.',.24)
    return out
def main():
    features=json.loads(DATA.read_text())['features'];coords=[]
    for f in features:
        ring=f['geometry']['coordinates'][0][:-1];coords.append((sum(p[0] for p in ring)/len(ring),sum(p[1] for p in ring)/len(ring)))
    pts=project(coords);groups={};size=.16
    for f,(x,y) in zip(features,pts):
        q,r=cube_round(x,y,size);g=groups.setdefault((q,r),{'x':1.5*size*q,'y':math.sqrt(3)*size*(r+q/2),'members':[],'counts':[0]*4,'coordinates':[]})
        g['members'].append(f['id']);g['counts'][f['properties']['threat_rank']-1]+=1;g['coordinates'].append([x,y])
    groups=list(groups.values());assert sum(sum(g['counts']) for g in groups)==len(features)==7215
    centroids=[(sum(p[0] for p in g['coordinates'])/len(g['coordinates']),sum(p[1] for p in g['coordinates'])/len(g['coordinates'])) for g in groups]
    cells=list(voronoi_polygons(MultiPoint(pts),ordered=True).geoms)
    totals=collections.Counter(f['properties']['threat_rank'] for f in features)
    for variant in ['voronoi','honeycomb','clusters']:
        doc=base('Coral reef threat / '+variant,'WRI 2011. Display grouping of 7,215 occupied grid cells; glyph extent is not measured reef area.')
        layer=el('g',doc,id='reef-groups')
        drawgroups=groups if variant!='voronoi' else [{'x':x,'y':y,'members':[f['id']],'counts':[int(k==f['properties']['threat_rank']-1) for k in range(4)]} for f,(x,y) in zip(features,pts)]
        for i,g in enumerate(drawgroups):
            x,y=g['x'],g['y'];n=sum(g['counts']);counts=g['counts']
            item=el('g',layer,data_group=i,data_cell_count=n,data_class_counts=','.join(map(str,counts)))
            el('title',item).text=f'{n} source grid cells; '+', '.join(f'{name}: {cnt}' for name,cnt in zip(NAMES,counts))
            if variant=='honeycomb':
                a=allocation(counts);k=0
                for rank,count in enumerate(a):
                    for dx,dy in hexoffsets(sum(a),.0175)[k:k+count]:
                        el('polygon',item,points=hexpoints(x+dx,y+dy,.016),fill=COLORS[rank],stroke='white',stroke_width=.0015)
                    k+=count
            elif variant=='voronoi':
                x,y=pts[i];shape=cells[i].intersection(Point(x,y).buffer(.075));rank=max(range(4),key=lambda r:(counts[r],r))
                if shape.is_empty:continue
                el('path',item,d='M '+' L '.join(f'{xx} {yy}' for xx,yy in shape.exterior.coords)+' Z',fill=COLORS[rank],stroke='white',stroke_width=.004)
            else:
                radius=min(.13,.022*math.sqrt(n));angle=-math.pi/2
                for rank,count in enumerate(counts):
                    if not count:continue
                    end=angle+2*math.pi*count/n
                    if count==n:el('circle',item,cx=x,cy=y,r=radius,fill=COLORS[rank])
                    else:
                        a=(x+radius*math.cos(angle),y+radius*math.sin(angle));b=(x+radius*math.cos(end),y+radius*math.sin(end))
                        d=f'M {x} {y} L {a[0]} {a[1]} A {radius} {radius} 0 {int(end-angle>math.pi)} 1 {b[0]} {b[1]} Z'
                        el('path',item,d=d,fill=COLORS[rank])
                    angle=end
        legend(doc,variant);save(doc,DEST/f'{variant}-world.svg');save(japan(doc,variant),DEST/f'{variant}-japan.svg')
        if variant=='honeycomb':save(doc,OUT/'plates/world/svg'/('resources-fauna-coral-reef-threat-2011'+SUFFIX+'.svg'))
    audit={'source':str(DATA),'source_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),'source_cells':len(features),'class_counts':dict(totals),'groups':len(groups),'macrohex_radius_inches':size,'microhex_radius_inches':.0175,'voronoi_max_radius_inches':.075,'circle_area_scale':'radius=min(0.13,0.022*sqrt(source_cell_count)) inches','display_cell_cap':61,'voronoi_seed_count':len(features),'selected':'honeycomb','reason':'Retains every threat class in each group and removes coincident symbol stacking; Voronoi exaggerates continuous coverage, circles hide small minority sectors at world scale.','all_memberships_conserved':True,'groups_ledger':groups}
    DEST.mkdir(parents=True,exist_ok=True);(DEST/'comparison.json').write_text(json.dumps(audit,indent=2)+'\n')
    print('Coral prototypes:',len(groups),'groups from',len(features),'cells',flush=True)
if __name__=='__main__':main()
