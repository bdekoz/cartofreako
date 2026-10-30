#!/usr/bin/env python3
"""Produce legend-free cartographic sheets and separate legend sheets for every pair."""
import argparse
import copy
import importlib
import json
from pathlib import Path
import xml.sax
from xml.sax.saxutils import XMLGenerator

from legend_informatics import E,ROOT,WIDTH,HEIGHT,SUFFIX,digest,el,save,register_fonts
from legend_sources import bibliography
from setouchi_delivery import COMPOSITION

SCALE=43.5/WIDTH
DX=(WIDTH-WIDTH*SCALE)/2
DY=(HEIGHT-HEIGHT*SCALE)/2
FRAMING={'scale':SCALE,'shift':4.4,'offset':0.0}


class MapOnly(xml.sax.ContentHandler):
    def __init__(self,stream,legend_name):
        self.writer=XMLGenerator(stream,encoding='utf-8');self.stream=stream
        self.depth=0;self.skip=0;self.legend_name=legend_name
    def startDocument(self):self.writer.startDocument()
    def startElement(self,name,attrs):
        a=dict(attrs)
        if not self.depth:
            a['data-legend-style']='separate-sheet';a['data-image-width-in']='43.5'
            a['data-legend-companion']=self.legend_name
            self.writer.startElement(name,a)
            self.stream.write(f'<rect id="st2-sheet-paper" width="44" height="{HEIGHT}" fill="white"/>'
                f'<defs id="st2-frame-definitions"><clipPath id="st2-image-clip"><rect width="44" height="{HEIGHT}"/></clipPath></defs>'
                f'<g id="st2-image-frame" transform="translate({DX} {DY}) scale({SCALE})">'
                '<g id="st2-image-window" clip-path="url(#st2-image-clip)">')
        elif self.skip or (name=='g' and ('legend' in a.get('id','') or a.get('id','').endswith('-key'))):
            self.skip+=1
        else:self.writer.startElement(name,a)
        self.depth+=1
    def characters(self,value):
        if not self.skip:self.writer.characters(value)
    def endElement(self,name):
        self.depth-=1
        if self.skip:self.skip-=1;return
        if not self.depth:self.stream.write('</g></g>')
        self.writer.endElement(name)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery',type=Path,default=ROOT/'output/setouchi-triennale-2028-st2')
    parser.add_argument('--source-delivery',type=Path,default=ROOT/'output/setouchi-triennale-2028')
    parser.add_argument('--only',nargs='*')
    parser.add_argument('--legends-only',action='store_true')
    args=parser.parse_args();register_fonts()
    revised=importlib.import_module('revise-setouchi-plates')
    framing=importlib.import_module('study-setouchi-africa-framing')
    catalog=json.loads((args.delivery/'sources/legend-catalog.json').read_text())
    book=json.loads((args.delivery/'plate-source-bibliography.json').read_text())
    entries={e['stem']:e for e in book['entries']}
    prior_path=args.delivery/'sources/separate-sheets.json'
    prior={(r['kind'],r['scope'],r['stem']):r for r in json.loads(prior_path.read_text())['records']} if prior_path.exists() else {}
    records=[]
    for m in catalog:
        stem=m['stem']
        if args.only and stem not in args.only:continue
        m=copy.deepcopy(m)
        for key in m['keys']:key['shapes']=[E.fromstring(s.encode()) for s in key.pop('symbols')]
        for scope in ('world','japan'):
            source=args.delivery/COMPOSITION/'plates'/scope/'svg'/(stem+SUFFIX+('-japan' if scope=='japan' else '')+'.svg')
            target=args.delivery/'maps'/scope/'svg'/(stem+'.svg')
            legend_target=args.delivery/'legends'/scope/'svg'/(stem+'-legend.svg')
            target.parent.mkdir(parents=True,exist_ok=True)
            special=scope=='world' and stem in ('network-fiber','network-groundstations')
            adjustment=None
            if args.legends_only:
                adjustment=prior[('map',scope,stem)].get('framing_adjustment')
            elif special:
                adjustment=framing.make_plate(source,'cyclic-43p5-antarctica-left',FRAMING,target,
                                             with_legend=False,consolidate_antarctica=True)
            else:
                with target.open('w') as stream:xml.sax.parse(str(source),MapOnly(stream,legend_target.name))
            legend=copy.deepcopy(m)
            if special:
                legend['notes'].append('Antarctica is deliberately displaced and consolidated at the lower left. Its displayed position is not geographically accurate; network routes and landing data are retained.')
                legend['notes'].append('AuthaGraph frame shifted horizontally by 10% of image width. All artwork scaled to a 43.5-inch image on the 44-inch sheet.')
            else:legend['notes'].append('Cartographic image width: 43.5 inches on a 44-inch sheet; artwork scaled proportionally to 98.863636%.')
            if stem=='network-fiber':legend['notes'].append('Printed route stroke: 0.494318 pt at 75% opacity (0.5 pt before proportional reduction).')
            document=el('svg',width='44in',height=f'{HEIGHT}in',viewBox=f'0 0 {WIDTH} {HEIGHT}',role='img',
                        data_sheet_kind='legend',data_map_companion=target.name)
            el('title',document).text=scope.title()+' / '+m['stem']+' / legend'
            el('desc',document).text='Standalone legend. The matching cartographic and data sheet contains no legend.'
            legend_group=revised.make_legend(legend,scope,args.source_delivery)
            for node in legend_group.iter():
                if E.QName(node).localname=='text' and (node.text or '').startswith('Sources and class definitions:'):
                    node.text=f"{m['ordinal']:02d}";node.set('id','plate-number')
                    node.set('font-size',str(36/72));node.set('font-weight','700');node.set('font-style','normal')
                    node.set('fill','#ffffff');node.set('fill-opacity','1')
                    node.set('stroke','#000000');node.set('stroke-opacity','1')
                    node.set('stroke-width',str(.5/72));node.set('opacity','1')
            document.append(legend_group)
            bibliography(document,entries[stem],book['sources'],scope)
            save(document,legend_target)
            for kind,path in [('map',target),('legend',legend_target)]:
                records.append({'kind':kind,'scope':scope,'stem':stem,'svg':str(path.relative_to(args.delivery)),
                                'svg_sha256':digest(path),'combined_source_sha256':digest(source),
                                'source':str(source.relative_to(args.delivery)),
                                'image_width_inches':43.5 if kind=='map' else None,
                                'scale':SCALE if kind=='map' else 1.0,
                                'framing_adjustment':adjustment if kind=='map' else None})
            print('separated',scope,stem,flush=True)
    target=args.delivery/'sources/separate-sheets.json'
    if args.only and target.exists():
        previous=json.loads(target.read_text());updates={(r['kind'],r['scope'],r['stem']):r for r in records}
        previous['records']=[updates.get((r['kind'],r['scope'],r['stem']),r) for r in previous['records']]
        target.write_text(json.dumps(previous,indent=2)+'\n')
    else:
        target.write_text(json.dumps({'schema':'setouchi-separate-map-legend-sheets-v1','sheet_inches':[WIDTH,HEIGHT],
                         'map_image_inches':[43.5,HEIGHT*SCALE],'scale':SCALE,'margins_inches':[DX,DY,DX,DY],
                         'records':records},indent=2)+'\n')


if __name__=='__main__':main()
