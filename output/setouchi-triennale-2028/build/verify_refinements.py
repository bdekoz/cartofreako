#!/usr/bin/env python3
"""Verify physical PDF strokes and data-class conservation after the atlas revisions."""
from pathlib import Path
from lxml import etree as E
from pypdf import PdfReader
from pypdf.generic import ContentStream
from pypdf._configuration import overwrite_configuration
import json,math,collections,re
# These locally generated vector maps exceed the default two-million-token budget.
overwrite_configuration(stream_parsing_work_maximum_count=100_000_000)
OUT=Path(__file__).resolve().parents[1]
def pdf_strokes(path):
    reader=PdfReader(path);found=[]
    def walk(stream,resources,state=None):
        state=dict(state or {'det':1.,'width':1.,'opacity':1.,'rgb':(0.,0.,0.)});stack=[]
        for operands,op in ContentStream(stream,reader).operations:
            if op==b'q':stack.append(dict(state))
            elif op==b'Q':state=stack.pop()
            elif op==b'cm':
                a,b,c,d,_,_=map(float,operands);state['det']*=a*d-b*c
            elif op==b'w':state['width']=float(operands[0])
            elif op==b'RG':state['rgb']=tuple(map(float,operands))
            elif op==b'G':state['rgb']=(float(operands[0]),)*3
            elif op==b'gs':
                g=resources.get('/ExtGState',{}).get(operands[0]);g=g.get_object() if g else {}
                if '/CA' in g:state['opacity']=float(g['/CA'])
            elif op==b'Do':
                item=resources.get('/XObject',{}).get(operands[0]);item=item.get_object() if item else None
                if item and item.get('/Subtype')=='/Form':
                    child=dict(state);a,b,c,d,_,_=map(float,item.get('/Matrix',[1,0,0,1,0,0]));child['det']*=a*d-b*c
                    walk(item,item.get('/Resources',resources),child)
            elif op in (b'S',b's',b'B',b'B*',b'b',b'b*'):
                found.append({'width':state['width']*math.sqrt(abs(state['det'])),'opacity':state['opacity'],'rgb':state['rgb']})
    page=reader.pages[0];walk(page.get_contents(),page['/Resources']);return found
def main():
    water={};fiber={};coastlines={}
    for scope in ['world','japan']:
        strokes=pdf_strokes(next((OUT/f'plates/{scope}/pdf').glob('water-*.pdf')))
        a=[s for s in strokes if abs(s['opacity']-.85)<1e-6 and max(abs(x-y/255) for x,y in zip(s['rgb'],[76,145,181]))<1e-4]
        target=.75 if scope=='world' else 1.5
        assert a and all(abs(s['width']-target)<2e-5 for s in a),(scope,a[:2])
        water[scope]={'stroke_operations':len(a),'effective_points':sorted({round(s['width'],7) for s in a}),'opacity':.85}
        coast=[s for s in strokes if abs(s['opacity']-.9)<1e-6 and max(abs(x-y/255) for x,y in zip(s['rgb'],[65,75,75]))<1e-4]
        coast_target=1.8 if scope=='world' else 1.0
        assert coast and all(abs(s['width']-coast_target)<2e-5 for s in coast),(scope,coast[:2])
        coastlines[scope]={'stroke_operations':len(coast),'effective_points':sorted({round(s['width'],7) for s in coast}),'opacity':.9}
        strokes=pdf_strokes(next((OUT/f'plates/{scope}/pdf').glob('network-fiber-*.pdf')))
        a=[s for s in strokes if abs(s['opacity']-.75)<1e-6]
        assert a and all(abs(s['width']-.5)<2e-5 for s in a),(scope,a[:2])
        fiber[scope]={'stroke_operations':len(a),'effective_points':sorted({round(s['width'],7) for s in a}),'opacity':.75}
    p=OUT/'sources/water-river-style.json';d=json.loads(p.read_text());d['pdf_graphics']=water;p.write_text(json.dumps(d,indent=2)+'\n')
    p=OUT/'sources/fiber-style.json';d=json.loads(p.read_text());d['pdf_graphics']=fiber;p.write_text(json.dumps(d,indent=2)+'\n')
    p=OUT/'sources/water-coastline-style.json'
    p.write_text(json.dumps({'reference':'Japan / Rare-earth mine production, shared 1 pt Japan outline','japan_coastline_effective_points':1,'pdf_graphics':coastlines,'reason':'Compensate the separate Natural Earth coastline layer for the 4.422099x Japan enlargement.'},indent=2)+'\n')
    temp=json.loads((OUT/'sources/temperature-classification.json').read_text());parser=E.XMLParser(huge_tree=True)
    for year,record in temp['years'].items():
        root=E.parse(str(next((OUT/'plates/world/svg').glob(f'anthropocene-temperature-{year}-*.svg'))),parser)
        paths=root.xpath('//*[@id="cpc-temperature-record-high-days"]/*[local-name()="path"]')
        counts=[int(p.get('data-cell-count')) for p in paths];assert counts==record['class_counts'][1:]
        assert sum(counts)+record['class_counts'][0]==record['covered_cells']
    palette=json.loads((OUT/'sources/resource-color-assignments.json').read_text());all_rgb=[tuple(c['rgb']) for colors in palette['metrics'].values() for c in colors]
    assert len(all_rgb)==len(set(all_rgb))==70
    palette_text=Path('/home/bkoz/src/izzi/src/izzi-svg-color-palettes.inc').read_text().split('izzi_hue_palette =',1)[1].split('};',1)[0]
    named_hues=set(re.findall(r'color::(\w+)',palette_text))
    assert all(c['name'] in named_hues for colors in palette['metrics'].values() for c in colors)
    for p in (OUT/'plates/world/svg').glob('resources-*.svg'):
        root=E.parse(str(p),parser)
        for e in root.xpath('//*[@id="resource-country-coverage"]//*[local-name()="path"]'):
            style=dict(part.strip().split(':',1) for part in e.get('style','').split(';') if ':' in part)
            if 'fill-opacity' in style:assert float(style['fill-opacity'])==1,p
    reef=json.loads((OUT/'prototypes/coral-reef/comparison.json').read_text());groups=reef['groups_ledger']
    assert len(groups)==844 and sum(sum(g['counts']) for g in groups)==7215
    ids=[i for g in groups for i in g['members']];assert len(ids)==len(set(ids))==7215
    assert [sum(g['counts'][i] for g in groups) for i in range(4)]==[reef['class_counts'][str(i)] for i in range(1,5)]
    for variant in ['voronoi','honeycomb','clusters']:
        root=E.parse(str(OUT/f'prototypes/coral-reef/{variant}-world.svg'),parser)
        gs=root.xpath('//*[@id="reef-groups"]/*[local-name()="g"]')
        assert sum(int(g.get('data-cell-count')) for g in gs)==7215
    cdn=json.loads((OUT/'sources/cdn-refresh.json').read_text());assert cdn['group_record_total']==13140+1405
    output={'status':'passed','pdf_rivers':water,'pdf_water_coastlines':coastlines,'pdf_fiber_routes':fiber,'temperature_bin_counts_match_sources':True,'distinct_named_resource_colors':70,'resource_data_fill_opacity':1,'reef_memberships_conserved':7215,'cdn_plotted_record_conservation':14545,'note':'Swarm geometry and opacity are separately audited in swarm-refresh.json; native source counts are retained.'}
    (OUT/'sources/refinement-validation.json').write_text(json.dumps(output,indent=2)+'\n')
    print('Verified PDF river/fiber widths, temperature bins, solid resource colours, reef memberships and CDN accounting',flush=True)
if __name__=='__main__':main()
