#!/usr/bin/env python3
"""Validate separate legends, print margins and preserved data after the approved layout edits."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib
import json
import math
from pathlib import Path
import re
import subprocess
import xml.sax

from lxml import etree as E
from PIL import Image
from antarctica_inset import subpaths
from legend_informatics import ROOT,WIDTH,HEIGHT,digest
from setouchi_delivery import standard_files


class Payload(xml.sax.ContentHandler):
    def __init__(self):
        self.hash=hashlib.sha256();self.text=[];self.counts=Counter();self.stack=[];self.skip=0;self.legends=0;self.frame=None
    def emit(self,value):self.hash.update(json.dumps(value,sort_keys=True,separators=(',',':')).encode())
    def startElement(self,name,attrs):
        a=dict(attrs);identifier=a.get('id','')
        if not self.stack:self.stack.append('root');return
        if 'legend' in identifier and name=='g':self.legends+=1
        rejected=(name=='g' and ('legend' in identifier or identifier.endswith('-key'))) or identifier in ('st2-sheet-paper','st2-frame-definitions')
        if self.skip or rejected:self.skip+=1;self.stack.append('skip');return
        if identifier in ('st2-image-frame','st2-image-window'):
            if identifier=='st2-image-frame':self.frame=a['transform']
            self.stack.append('wrapper');return
        self.stack.append('content');self.emit(['start',name,a])
        if name in ('path','circle','rect','polygon','polyline','line','ellipse','use'):self.counts[name]+=1
    def characters(self,value):
        if not self.skip:self.text.append(value)
    def endElement(self,name):
        kind=self.stack.pop()
        if kind=='skip':self.skip-=1
        elif kind=='content':self.emit(['end',name])
    def result(self):return self.hash.hexdigest(),hashlib.sha256(' '.join(''.join(self.text).split()).encode()).hexdigest(),dict(self.counts)


def tree_hash(node):
    digest=hashlib.sha256()
    def visit(node):
        digest.update(json.dumps([E.QName(node).localname,sorted(node.attrib.items()),' '.join((node.text or '').split())],separators=(',',':')).encode())
        for child in node:visit(child)
        digest.update(b'/')
    visit(node);return digest.hexdigest()


def land_parts(group):
    result={}
    for node in group.iter():
        if E.QName(node).localname!='path':continue
        key=node.get('id').removesuffix('-antarctic-inset')
        result.setdefault(key,[]).extend(subpaths(node.get('d','')))
    return result


def special_map(source,target,record):
    original=E.parse(str(source)).getroot();revised=E.parse(str(target)).getroot()
    groups=(['network-fiber-itu-terrestrial','network-fiber','network-fiber-landings'] if record['stem']=='network-fiber'
            else ['starlink-gateway-links','starlink-gateways-20250902'])
    for identifier in groups:
        a=original.xpath('//*[@id=$id]',id=identifier);b=revised.xpath('//*[@id=$id]',id=identifier)
        assert len(a)==len(b)==1
        assert tree_hash(a[0])==tree_hash(b[0]),'Network data changed: '+identifier
    before=land_parts(original.xpath('//*[@id="terrestrial-land"]')[0])
    after=land_parts(revised.xpath('//*[@id="terrestrial-land"]')[0])
    inset=revised.xpath('//*[@id="antarctica-consolidated-inset"]')
    assert len(inset)==1
    for key,value in land_parts(inset[0]).items():after.setdefault(key,[]).extend(value)
    assert before.keys()==after.keys()
    maximum_error=0;points=0
    for key,parts in before.items():
        unmatched=list(after[key]);assert len(parts)==len(unmatched)
        for vertices,closed in parts:
            match=None
            for index,(candidate,candidate_closed) in enumerate(unmatched):
                if closed!=candidate_closed or len(vertices)!=len(candidate):continue
                if max(abs(x-y) for x,y in zip(vertices[0],candidate[0]))>1e-8:continue
                error=max(abs(a-b) for p,q in zip(vertices,candidate) for a,b in zip(p,q))
                if error<1e-8:match=index;maximum_error=max(maximum_error,error);points+=len(vertices);break
            assert match is not None,'Lost or changed land path: '+key
            unmatched.pop(match)
    adjustment=record['framing_adjustment'];bounds=adjustment['antarctica_adjustment']['inset_bounds_inches']
    assert 0<bounds[0]<bounds[2]<7 and 12<bounds[1]<bounds[3]<HEIGHT
    assert len(revised.xpath('//*[@id="source-cartography"]'))==1
    assert not revised.xpath('//*[@id="legend-informatics"]')
    result={'data_layers_unchanged':groups,'land_vertices_conserved':points,'land_coordinate_roundtrip_max_error_inches':maximum_error,
            'single_antarctic_inset':True,'antarctic_inset_bounds_source_inches':bounds}
    if record['stem']=='network-fiber':
        framing=importlib.import_module('study-setouchi-africa-framing')
        pairs=framing.boundary_pairs(original);assert len(pairs)==14
        shift=adjustment['shift'];scale=adjustment['scale']
        gap=max(scale*math.hypot(((p['left'][0]+shift)%WIDTH)-((p['right'][0]+shift)%WIDTH),p['left'][1]-p['right'][1]) for p in pairs)
        assert gap<1e-10;result.update(africa_matched_endpoint_pairs=14,africa_max_gap_inches=gap)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery',type=Path,default=ROOT/'output/setouchi-triennale-2028-st2')
    parser.add_argument('--skip-exports',action='store_true')
    args=parser.parse_args();out=args.delivery
    manifest=json.loads((out/'sources/separate-sheets.json').read_text())
    book=json.loads((out/'plate-source-bibliography.json').read_text());entries={e['stem']:e for e in book['entries']}
    assert len(manifest['records'])==152
    def check(record):
        kind,scope,stem=record['kind'],record['scope'],record['stem'];svg=out/record['svg'];entry=entries[stem]
        assert digest(svg)==record['svg_sha256']
        result={'kind':kind,'scope':scope,'stem':stem,'svg_sha256':record['svg_sha256']}
        if kind=='legend':
            root=E.parse(str(svg)).getroot();numbers=root.xpath('//*[@id="plate-number"]')
            assert len(numbers)==1;number=numbers[0]
            expected={'font-size':'0.5','font-weight':'700','font-style':'normal','fill':'#ffffff','fill-opacity':'1',
                      'stroke':'#000000','stroke-opacity':'1','opacity':'1'}
            assert number.text==f"{entry['ordinal']:02d}"
            assert all(number.get(k)==v for k,v in expected.items())
            assert abs(float(number.get('stroke-width'))*72-.5)<1e-12
            assert not any((n.text or '').startswith('Sources and class definitions:') for n in root.iter())
            panels=root.xpath('//*[@id="plate-source-bibliography"]');assert len(panels)==1
            urls=set(panels[0].xpath('.//@xlink:href',namespaces={'xlink':'http://www.w3.org/1999/xlink'}))
            identifiers=entry['source_ids']+(entry['japan_source_ids'] if scope=='japan' else [])
            for identifier in identifiers:assert book['sources'][identifier]['url'] in urls,stem+' missing '+identifier
            result.update(plate_number='36 pt bold / white fill / black 0.5 pt outline / 100% opacity',source_ids=identifiers)
        else:
            source=out/record['source'];assert digest(source)==record['combined_source_sha256']
            if record.get('framing_adjustment'):result.update(special_map(source,svg,record))
            else:
                before=Payload();after=Payload();xml.sax.parse(str(source),before);xml.sax.parse(str(svg),after)
                assert before.result()==after.result(),stem+'/'+scope+' payload changed'
                assert after.legends==0
                numbers=[float(n) for n in re.findall(r'[-+]?[\d.]+',after.frame)]
                assert all(abs(a-b)<1e-12 for a,b in zip(numbers,[.25,(HEIGHT-HEIGHT*43.5/44)/2,43.5/44]))
                result.update(original_data_tree_conserved=True,shape_counts=dict(after.counts))
        if not args.skip_exports:
            receipt=json.loads((out/'sources/sheet-exports'/f'{kind}-{scope}-{stem}.json').read_text())
            assert receipt['fingerprint']['svg_sha256']==record['svg_sha256']
            for value in receipt['outputs'].values():assert digest(out/value['path'])==value['sha256']
            with Image.open(out/receipt['outputs']['png']['path']) as image:assert image.size==(13200,5716)
            info=subprocess.check_output(['pdfinfo',str(out/receipt['outputs']['pdf']['path'])],text=True)
            w,h=map(float,re.search(r'Page size:\s+([\d.]+) x ([\d.]+)',info).groups())
            assert abs(w/72-WIDTH)<.001 and abs(h/72-HEIGHT)<.001
            result['exports_verified']=True
        print('validated',kind,scope,stem,flush=True);return result
    with ThreadPoolExecutor(max_workers=2) as executor:records=list(executor.map(check,manifest['records']))
    receipt={'status':'passed','maps':76,'legend_source_sheets':76,'exports_checked':not args.skip_exports,'records':records}
    if not args.skip_exports:
        publication=standard_files(out,check=True)
        receipt['standard_plate_files_checked']=publication['files']
    (out/'sources'/('sheets-validation-svg.json' if args.skip_exports else 'sheets-validation.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    print('All 152 sheets passed.',flush=True)


if __name__=='__main__':main()
