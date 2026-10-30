#!/usr/bin/env python3
"""Export the separate map and legend sheets, with compact legend previews."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image
from legend_informatics import ROOT,FONT_DIR,digest,font_environment


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery',type=Path,default=ROOT/'output/setouchi-triennale-2028-st2')
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--only',nargs='*')
    args=parser.parse_args();env=font_environment();font_hash=digest(FONT_DIR/'provenance.json')
    manifest=json.loads((args.delivery/'sources/separate-sheets.json').read_text())
    receipts=args.delivery/'sources/sheet-exports';receipts.mkdir(parents=True,exist_ok=True)
    def export(record):
        kind,scope,stem=record['kind'],record['scope'],record['stem']
        svg=args.delivery/record['svg'];base=svg.parent.parent;name=svg.stem
        pdf=base/'pdf'/(name+'.pdf');png=base/'png'/(name+'.png');preview=base/'preview'/(name+'.png')
        key=f'{kind}-{scope}-{stem}';receipt=receipts/(key+'.json')
        fingerprint={'svg_sha256':digest(svg),'font_provenance_sha256':font_hash,'dpi':300,'exporter':'separate-sheets-v1'}
        if receipt.exists():
            previous=json.loads(receipt.read_text())
            if previous['fingerprint']==fingerprint and all(
                    (args.delivery/r['path']).exists() and digest(args.delivery/r['path'])==r['sha256'] for r in previous['outputs'].values()):
                print('cached',key,flush=True);return previous
        for path in (pdf,png,preview):path.parent.mkdir(parents=True,exist_ok=True)
        start=time.monotonic()
        native=kind=='map' and stem.startswith('network-swarm-')
        with (receipts/(key+'.log')).open('w') as log:
            if native:
                commands=[[sys.executable,str(ROOT/'scripts/export-native-swarm.py'),str(svg),'--pdf',str(pdf),
                           '--png',str(png),'--preview',str(preview),'--dpi','300']]
            else:
                commands=[['inkscape',str(svg),'--export-area-page','--export-filename='+str(pdf)],
                          ['inkscape',str(svg),'--export-area-page','--export-dpi=300','--export-background=white',
                           '--export-background-opacity=255','--export-png-color-mode=RGB_8','--export-filename='+str(png)]]
                if kind=='legend':commands.append(['inkscape',str(svg),'--export-area-drawing','--export-width=3840',
                           '--export-background=white','--export-background-opacity=255','--export-filename='+str(preview)])
            for command in commands:subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        with Image.open(png) as image:
            assert image.size==(13200,5716),(key,image.size)
            if kind=='map' and not native:
                image.thumbnail((3840,3840),Image.Resampling.LANCZOS);image.convert('RGB').save(preview)
            if kind=='map':
                # Test only the clear parts of the expected white margin bands,
                # avoiding antialiasing at the exact image boundary.
                with Image.open(png) as full:
                    for box in [(0,0,74,5716),(13126,0,13200,5716),(0,0,13200,31),(0,5685,13200,5716)]:
                        assert all(v==(255,255) for v in full.crop(box).convert('RGB').getextrema()),key+' margin'
        result={'kind':kind,'scope':scope,'stem':stem,'svg':record['svg'],'fingerprint':fingerprint,
                'elapsed_seconds':round(time.monotonic()-start,2),'pixel_dimensions':[13200,5716],
                'outputs':{key:{'path':str(path.relative_to(args.delivery)),'sha256':digest(path),'bytes':path.stat().st_size}
                           for key,path in [('pdf',pdf),('png',png),('preview',preview)]}}
        receipt.write_text(json.dumps(result,indent=2)+'\n');print('exported',key,result['elapsed_seconds'],flush=True)
        return result
    records=[r for r in manifest['records'] if not args.only or r['stem'] in args.only]
    records.sort(key=lambda r:(r['stem'] not in ('network-fiber','network-groundstations'),r['scope']!='world'))
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures=[executor.submit(export,r) for r in records]
        results=[f.result() for f in as_completed(futures)]
    results.sort(key=lambda r:(r['scope'],r['stem'],r['kind']))
    (args.delivery/'sources'/('sheet-export-manifest-selected.json' if args.only else 'sheet-export-manifest.json')).write_text(
        json.dumps({'records':results,'font_provenance_sha256':font_hash},indent=2)+'\n')
    print('Complete:',len(results),'separate sheets',flush=True)


if __name__=='__main__':main()
