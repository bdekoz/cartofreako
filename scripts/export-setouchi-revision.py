#!/usr/bin/env python3
"""Export combined composition intermediates under sources/composition, never plates/."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

from legend_informatics import ROOT, FONT_DIR, WIDTH, HEIGHT, SUFFIX, digest, font_environment
from setouchi_delivery import COMPOSITION


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery', type=Path, default=ROOT/'output/setouchi-triennale-2028-st2')
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--only', nargs='*')
    args = parser.parse_args()
    env = font_environment()
    revision = json.loads((args.delivery/'sources/legend-revision.json').read_text())
    font_hash = digest(FONT_DIR/'provenance.json')
    sources = args.delivery/COMPOSITION/'exports'
    sources.mkdir(parents=True, exist_ok=True)

    def export(record):
        scope, stem = record['scope'], record['stem']
        name = stem+SUFFIX+('-japan' if scope=='japan' else '')
        svg = args.delivery/COMPOSITION/'plates'/scope/'svg'/(name+'.svg')
        pdf = args.delivery/COMPOSITION/'plates'/scope/'pdf'/(name+'.pdf')
        png = args.delivery/COMPOSITION/'plates'/scope/'png'/(name+'.png')
        preview = args.delivery/COMPOSITION/'previews'/scope/(name+'.png')
        receipt = sources/(scope+'-'+stem+'.json')
        fingerprint = {'svg_sha256':digest(svg), 'font_provenance_sha256':font_hash,
                       'dpi':300, 'exporter':'setouchi-st2-v1'}
        if receipt.exists():
            previous = json.loads(receipt.read_text())
            if previous['fingerprint']==fingerprint and all(
                    path.exists() and digest(path)==previous['outputs'][key]['sha256']
                    for key,path in [('pdf',pdf),('png',png),('preview',preview)]):
                print('cached',scope,stem,flush=True)
                return previous
        for path in (pdf,png,preview):path.parent.mkdir(parents=True,exist_ok=True)
        start=time.monotonic()
        with (sources/(scope+'-'+stem+'.log')).open('w') as log:
            if stem.startswith('network-swarm-'):
                commands=[[sys.executable,str(ROOT/'scripts/export-native-swarm.py'),str(svg),
                           '--pdf',str(pdf),'--png',str(png),'--preview',str(preview),'--dpi','300']]
            else:
                commands=[['inkscape',str(svg),'--export-area-page','--export-filename='+str(pdf)],
                          ['inkscape',str(svg),'--export-area-page','--export-dpi=300',
                           '--export-background=white','--export-background-opacity=255',
                           '--export-png-color-mode=RGB_8','--export-filename='+str(png)]]
            for command in commands:
                subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        with Image.open(png) as image:
            if image.size!=(round(WIDTH*300),round(HEIGHT*300)):
                raise ValueError('Unexpected sheet dimensions: '+str(png)+' '+str(image.size))
            pixels=image.size
            if not stem.startswith('network-swarm-'):
                image.thumbnail((2200,2200),Image.Resampling.LANCZOS)
                image.convert('RGB').save(preview)
        result={'scope':scope,'stem':stem,'fingerprint':fingerprint,'pixel_dimensions':pixels,
                'sheet_inches':[WIDTH,HEIGHT],'elapsed_seconds':round(time.monotonic()-start,2),
                'outputs':{key:{'path':str(path.relative_to(args.delivery)),'sha256':digest(path),'bytes':path.stat().st_size}
                           for key,path in [('pdf',pdf),('png',png),('preview',preview)]}}
        receipt.write_text(json.dumps(result,indent=2)+'\n')
        print('exported',scope,stem,result['elapsed_seconds'],flush=True)
        return result

    selected=[r for r in revision['records'] if not args.only or r['stem'] in args.only]
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures=[executor.submit(export,r) for r in selected]
        results=[future.result() for future in as_completed(futures)]
    results.sort(key=lambda r:(r['scope'],r['stem']))
    (args.delivery/COMPOSITION/('export-manifest-selected.json' if args.only else 'export-manifest.json')).write_text(
        json.dumps({'font_provenance_sha256':font_hash,'records':results},indent=2)+'\n')


if __name__=='__main__':main()
