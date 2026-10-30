#!/usr/bin/env python3
"""Independently verify map conservation, bibliography coverage and print exports."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.sax

from PIL import Image
from legend_informatics import ROOT, SUFFIX, WIDTH, HEIGHT, digest


class MapAudit(xml.sax.ContentHandler):
    """Hash the full non-editorial tree, including inherited transforms/styles."""
    def __init__(self,scope):
        self.scope=scope;self.depth=0;self.skip=0;self.hash=hashlib.sha256()
        self.shapes=Counter();self.legends=Counter();self.text_parts=[]
    def emit(self,value):self.hash.update(json.dumps(value,sort_keys=True,separators=(',',':')).encode())
    def startElement(self,name,attrs):
        a=dict(attrs);identifier=a.get('id','')
        editorial=name=='g' and ('legend' in identifier or identifier.endswith('-key') or identifier=='detail-notes')
        if editorial:self.legends[identifier]+=1
        if self.scope=='japan' and self.depth==1 and name in ('text','polygon'):editorial=True
        self.depth+=1
        if self.skip or editorial:self.skip+=1;return
        if self.depth==1:a.pop('data-legend-style',None)
        self.emit(['start',name,a])
        if name in ('path','circle','ellipse','rect','polygon','polyline','line','use'):self.shapes[name]+=1
    def characters(self,value):
        # All map text is compared as normalized text in a separate ordered list;
        # parser chunk boundaries and serialization whitespace are immaterial.
        if not self.skip:self.text_parts.append(value)
    def endElement(self,name):
        self.depth-=1
        if self.skip:self.skip-=1;return
        self.emit(['end',name])
    def result(self):
        return {'tree_sha256':self.hash.hexdigest(),'text_sha256':hashlib.sha256(' '.join(''.join(self.text_parts).split()).encode()).hexdigest(),
                'shape_counts':dict(self.shapes),'legends':dict(self.legends)}


def audit(path,scope):
    handler=MapAudit(scope);xml.sax.parse(str(path),handler);return handler.result()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'output/setouchi-triennale-2028')
    parser.add_argument('--output',type=Path,default=ROOT/'output/setouchi-triennale-2028-st2')
    parser.add_argument('--skip-exports',action='store_true')
    parser.add_argument('--reuse-map-audit',action='store_true',help='Reuse a passed map audit only while both complete SVG hashes still match')
    args=parser.parse_args()
    revision=json.loads((args.output/'sources/legend-revision.json').read_text())
    book=json.loads((args.output/'plate-source-bibliography.json').read_text())
    assert len(revision['records'])==76 and len(book['entries'])==38
    cached={}
    cache=args.output/'sources/validation-map-only.json'
    if args.reuse_map_audit and cache.exists():
        previous=json.loads(cache.read_text())
        if previous.get('status')=='passed':cached={(r['stem'],r['scope']):r for r in previous['records']}

    def verify(record):
        stem,scope=record['stem'],record['scope'];name=stem+SUFFIX+('-japan' if scope=='japan' else '')
        source=args.source/'plates'/scope/'svg'/(name+'.svg');target=args.output/'plates'/scope/'svg'/(name+'.svg')
        assert digest(source)==record['source_sha256'], 'Source changed: '+str(source)
        assert digest(target)==record['output_sha256'], 'Revision changed: '+str(target)
        prior=cached.get((stem,scope),{})
        if prior.get('source_sha256')==record['source_sha256'] and prior.get('svg_sha256')==record['output_sha256']:
            result={**prior,'map_audit_reused':True}
        else:
            before=audit(source,scope);after=audit(target,scope)
            for key in ('tree_sha256','text_sha256','shape_counts'):
                assert before[key]==after[key],f'{stem}/{scope}: map {key} changed'
            if record['status']=='revised':assert after['legends']=={'legend-informatics':1},f'{stem}/{scope}: legacy legend retained'
            else:assert digest(source)==digest(target)
            result={'stem':stem,'scope':scope,'map_tree_unchanged':True,'shape_counts':after['shape_counts'],
                    'source_sha256':record['source_sha256'],'svg_sha256':record['output_sha256']}
        if not args.skip_exports:
            export=json.loads((args.output/'sources/exports'/(scope+'-'+stem+'.json')).read_text())
            assert export['fingerprint']['svg_sha256']==record['output_sha256']
            for key,r in export['outputs'].items():assert digest(args.output/r['path'])==r['sha256'],f'Export mismatch: {key}/{stem}'
            with Image.open(args.output/export['outputs']['png']['path']) as image:assert image.size==(13200,5716)
            info=subprocess.check_output(['pdfinfo',str(args.output/export['outputs']['pdf']['path'])],text=True)
            w,h=map(float,re.search(r'Page size:\s+([\d.]+) x ([\d.]+)',info).groups())
            assert abs(w/72-WIDTH)<.001 and abs(h/72-HEIGHT)<.001
            result['exports']='SVG/PDF/300 dpi PNG and preview verified'
        print('validated',scope,stem,flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as executor:results=list(executor.map(verify,revision['records']))
    for entry in book['entries']:
        assert entry['source_ids'] and entry['japan_source_ids']
        for identifier in entry['source_ids']+entry['japan_source_ids']:assert identifier in book['sources']
    report={'status':'passed','plate_pairs':38,'plates':76,'bibliography_sources':len(book['sources']),
            'full_non_editorial_tree_conserved':True,'exports_checked':not args.skip_exports,'records':results}
    (args.output/'sources'/('validation-map-only.json' if args.skip_exports else 'validation.json')).write_text(json.dumps(report,indent=2)+'\n')
    print('All 76 plates passed; all 38 pairs have source attribution.',flush=True)


if __name__=='__main__':main()
