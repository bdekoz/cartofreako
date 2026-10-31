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
from setouchi_world_framing import ANTARCTIC_TRANSLATION, SCALE, SHIFT, DX, DY


class WorldPayload(xml.sax.ContentHandler):
    """Compare every source shape, including split rings, in bounded memory.

    A multiset checksum ignores the intentional regrouping of Antarctic paths,
    while retaining coordinates, paint, metadata and inherited group attributes.
    Editorial ocean backing and reference land are excluded from this data checksum.
    """
    def __init__(self, framed=False):
        self.framed = framed
        self.stack = []
        self.active = not framed
        self.skip = 0
        self.total = 0
        self.counts = Counter()
        self.inset = None
        self.frame = None
        self.uses = []

    def add(self, value, kind):
        self.total = (self.total + int.from_bytes(hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).digest(), 'big')) % (1 << 256)
        self.counts[kind] += 1

    def startElement(self, name, attrs):
        a = {k: v for k, v in attrs.items() if not k.startswith('xmlns')}
        identifier = a.get('id', '')
        if not self.stack:
            self.stack.append((None, 'root'))
            return
        if self.framed and identifier in ('source-cartography', 'antarctica-consolidated-inset'):
            self.active = True
            if identifier == 'antarctica-consolidated-inset':
                self.inset = a['transform']
            self.stack.append((None, 'bank'))
            return
        if self.framed and identifier == 'st2-image-frame':
            self.frame = a['transform']
        if self.framed and name == 'use' and any(k.endswith(':href') and v == '#source-cartography' for k, v in a.items()):
            self.uses.append(a['transform'])
        if not self.active:
            self.stack.append((None, 'outside'))
            return
        rejected = (identifier in ('antarctica-source-infill', 'antarctica-reference-silhouette') or (not self.framed and len(self.stack) == 1 and
                    (name == 'rect' or identifier.endswith('-background') or 'legend' in identifier or identifier.endswith('-key'))))
        if self.skip or rejected:
            self.skip += 1
            self.stack.append((None, 'skip'))
            return
        if identifier.endswith('-antarctic-inset'):
            a['id'] = identifier.removesuffix('-antarctic-inset')
        ancestry = [entry for entry, kind in self.stack if entry is not None]
        if name == 'path':
            value = a.pop('d', '')
            if re.search('[AaCcQqSsTt]', value):
                self.add([ancestry, name, a, value], name)
            else:
                for points, closed in subpaths(value):
                    self.add([ancestry, name, a, [[float(f'{v:.12g}') for v in point] for point in points], closed], 'path_subpaths')
        elif name in ('circle', 'rect', 'polygon', 'polyline', 'line', 'ellipse', 'use'):
            self.add([ancestry, name, a], name)
        self.stack.append(([name, a] if name in ('g', 'defs', 'clipPath') else None, 'content'))

    def endElement(self, name):
        _, kind = self.stack.pop()
        if kind == 'skip':
            self.skip -= 1
        elif kind == 'bank':
            self.active = False

    def result(self):
        return f'{self.total:064x}', dict(self.counts)


def world_map(source, target, record):
    before, after = WorldPayload(), WorldPayload(framed=True)
    xml.sax.parse(str(source), before)
    xml.sax.parse(str(target), after)
    assert before.result() == after.result(), record['stem'] + ' source shapes, values or inherited styles changed'
    expected = f'translate({DX} {DY}) scale({SCALE})'
    assert after.frame == expected
    assert after.uses == [f'translate({n} 0)' for n in (SHIFT-WIDTH, SHIFT, SHIFT+WIDTH)]
    present = record['framing_adjustment']['antarctica_adjustment']['present']
    non_terrestrial = record['stem'] in ('geometry', 'graticules', 'orbital-technosphere-observer') or record['stem'].startswith('astro-')
    assert present != non_terrestrial, record['stem'] + ' missing or inappropriate Antarctic inset'
    if present:
        assert after.inset == f'translate({ANTARCTIC_TRANSLATION[0]:.12g} {ANTARCTIC_TRANSLATION[1]:.12g})'
    else:
        assert after.inset is None
    result = {'source_shape_multiset_sha256_sum': after.result()[0], 'shape_counts': dict(after.counts),
              'source_geometry_and_styles_conserved': True, 'common_cyclic_frame': True,
              'antarctica_at_common_lower_left_position': present}
    if record['stem'] == 'network-fiber':
        framing = importlib.import_module('study-setouchi-africa-framing')
        pairs = framing.boundary_pairs(E.parse(str(source)).getroot())
        assert len(pairs) == 14
        gap = max(SCALE*math.hypot(((p['left'][0]+SHIFT)%WIDTH)-((p['right'][0]+SHIFT)%WIDTH),p['left'][1]-p['right'][1]) for p in pairs)
        assert gap < 1e-10
        result.update(africa_matched_endpoint_pairs=14, africa_max_gap_inches=gap)
    return result


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
            if record.get('framing_adjustment'):result.update(world_map(source,svg,record))
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
