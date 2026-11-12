#!/usr/bin/env python3
"""Export the separate map and legend sheets, with compact legend previews."""
import argparse
from concurrent.futures import FIRST_COMPLETED,ThreadPoolExecutor,wait
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import re
import xml.etree.ElementTree as ET

from PIL import Image, ImageColor
from legend_informatics import ROOT,FONT_DIR,digest,font_environment
from cartofreako_style import STYLE
from dataset import redact

DPI=STYLE['atlas']['png_dpi']


def run_export_command(command, env, log):
    """Inkscape can exit zero after silently omitting undecodable images."""
    result = subprocess.run(command, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors='replace')
    log.write(redact(result.stdout))
    log.flush()
    result.check_returncode()
    if 'Pixbuf::create_' in result.stdout or 'D-Bus error' in result.stdout:
        raise RuntimeError('Inkscape could not decode linked image layers; see ' + str(log.name)
                           + '. Run with access to a working local D-Bus image decoder.')


def check_image_decoder(directory):
    """Check an actual linked PNG before starting the expensive atlas work."""
    directory.mkdir(parents=True, exist_ok=True)
    color = (37, 127, 221)
    Image.new('RGB', (16, 16), color).save(directory/'source.png')
    svg = directory/'linked-image.svg'
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" '
                   'xmlns:xlink="http://www.w3.org/1999/xlink" width="64" height="64">'
                   '<image xlink:href="source.png" width="64" height="64"/></svg>')
    rendered = directory/'rendered.png'
    with (directory/'inkscape.log').open('w') as log:
        run_export_command(['bash', str(ROOT/'scripts/run-inkscape.sh'), 'inkscape', str(svg),
                            '--export-area-page', '--export-filename='+str(rendered)],
                           font_environment(), log)
    with Image.open(rendered) as image:
        if image.size != (64, 64) or image.convert('RGB').getpixel((32, 32)) != color:
            raise RuntimeError('Inkscape linked-image pixel check failed: ' + str(rendered))
    print('Linked-image decoder preflight passed: actual PNG pixels verified', flush=True)


def sheet_pixels(svg, dpi=DPI):
    """Read physical page size, including A3 companions among atlas maps."""
    with svg.open('rb') as stream:
        attrs=next(ET.iterparse(stream,events=('start',)))[1].attrib
    factors={'in':1,'mm':1/25.4,'cm':1/2.54,'pt':1/72,'px':1/96,'':1/96}
    def pixels(value):
        match=re.fullmatch(r'([\d.]+)(in|mm|cm|pt|px)?',value)
        if not match:
            raise ValueError('Unsupported SVG physical page size: '+value)
        return round(float(match[1])*factors[match[2] or '']*dpi)
    return pixels(attrs['width']),pixels(attrs['height'])


def margin_boxes(svg, dimensions, dpi=DPI):
    """Check inside the sheet's declared clear margin, leaving a pixel inset."""
    with svg.open('rb') as stream:
        attrs=next(ET.iterparse(stream,events=('start',)))[1].attrib
    width,height=dimensions
    declared=attrs.get('data-frame-side-margin-inches')
    side=74
    if declared is not None:
        inches=float(declared)
        if not math.isfinite(inches) or inches <= 0 or inches*dpi >= width/2:
            raise ValueError('Invalid SVG side margin: '+declared)
        side=math.floor(inches*dpi)-1
        if side < 1:
            raise ValueError('SVG side margin is too narrow to validate: '+declared)
    return [(0,0,side,height),(width-side,0,width,height),
            (0,0,width,31),(0,height-31,width,height)]


def export_records(records, export, workers):
    """Keep only active sheets queued and report failure before joining them."""
    remaining=iter(records)
    results=[]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        active={}
        def submit():
            record=next(remaining,None)
            if record is not None:
                active[executor.submit(export,record)]=record
        for _ in range(workers):
            submit()
        while active:
            done,_=wait(active,return_when=FIRST_COMPLETED)
            for future in done:
                record=active.pop(future)
                try:
                    results.append(future.result())
                except BaseException:
                    key='-'.join(record[k] for k in ('kind','scope','stem'))
                    print('Export failed: '+key+'; remaining sheets cancelled; '
                          'waiting for active exports to finish',file=sys.stderr,flush=True)
                    for pending in active:
                        pending.cancel()
                    raise
            for _ in done:
                submit()
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery',type=Path,default=ROOT/'output/setouchi-triennale-2028-st2')
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--only',nargs='*')
    parser.add_argument('--check-image-decoder',action='store_true')
    args=parser.parse_args()
    if args.check_image_decoder:
        check_image_decoder(args.delivery.resolve())
        return
    env=font_environment();font_hash=digest(FONT_DIR/'provenance.json')
    manifest=json.loads((args.delivery/'sources/separate-sheets.json').read_text())
    receipts=args.delivery/'sources/sheet-exports';receipts.mkdir(parents=True,exist_ok=True)
    def export(record):
        kind,scope,stem=record['kind'],record['scope'],record['stem']
        svg=args.delivery/record['svg'];base=svg.parent.parent;name=svg.stem
        pdf=base/'pdf'/(name+'.pdf');png=base/'png'/(name+'.png');preview=base/'preview'/(name+'.png')
        key=f'{kind}-{scope}-{stem}';receipt=receipts/(key+'.json')
        background=record.get('sheet_background', 'white')
        dimensions=sheet_pixels(svg)
        fingerprint={'svg_sha256':digest(svg),'font_provenance_sha256':font_hash,'dpi':DPI,
                     'exporter':'separate-sheets-v4-declared-margins','exporter_sha256':digest(Path(__file__))}
        native=kind=='map' and stem.startswith('network-swarm-')
        if native:fingerprint.update(native_exporter_sha256=digest(ROOT/'scripts/export-native-swarm.py'),canvas_background=background)
        if receipt.exists():
            previous=json.loads(receipt.read_text())
            if previous['fingerprint']==fingerprint and all(
                    (args.delivery/r['path']).exists() and digest(args.delivery/r['path'])==r['sha256'] for r in previous['outputs'].values()):
                print('cached',key,flush=True);return previous
        for path in (pdf,png,preview):path.parent.mkdir(parents=True,exist_ok=True)
        start=time.monotonic()
        with (receipts/(key+'.log')).open('w') as log:
            if native:
                commands=[[sys.executable,str(ROOT/'scripts/export-native-swarm.py'),str(svg),'--pdf',str(pdf),
                           '--png',str(png),'--preview',str(preview),'--dpi',str(DPI),'--background',background]]
            else:
                commands=[['inkscape',str(svg),'--export-area-page','--export-filename='+str(pdf)],
                          ['inkscape',str(svg),'--export-area-page',f'--export-dpi={DPI}','--export-background='+background,
                           '--export-background-opacity=255','--export-png-color-mode=RGB_8','--export-filename='+str(png)]]
                if kind=='legend':commands.append(['inkscape',str(svg),'--export-area-drawing','--export-width=3840',
                           '--export-background='+background,'--export-background-opacity=255','--export-filename='+str(preview)])
            for command in commands:
                if command[0]=='inkscape':command=['bash',str(ROOT/'scripts/run-inkscape.sh'),*command]
                run_export_command(command,env,log)
        with Image.open(png) as image:
            assert image.size==dimensions,(key,image.size,dimensions)
            if kind=='map' and not native:
                image.thumbnail((3840,3840),Image.Resampling.LANCZOS);image.convert('RGB').save(preview)
            if kind=='map':
                # Test only the clear parts of the configured margin bands,
                # avoiding antialiasing at the exact image boundary.
                with Image.open(png) as full:
                    for box in margin_boxes(svg,dimensions):
                        assert full.crop(box).convert('RGB').getextrema()==tuple((v,v) for v in ImageColor.getrgb(background)),key+' margin'
        result={'kind':kind,'scope':scope,'stem':stem,'svg':record['svg'],'fingerprint':fingerprint,
                'elapsed_seconds':round(time.monotonic()-start,2),'pixel_dimensions':list(dimensions),
                'outputs':{key:{'path':str(path.relative_to(args.delivery)),'sha256':digest(path),'bytes':path.stat().st_size}
                           for key,path in [('pdf',pdf),('png',png),('preview',preview)]}}
        receipt.write_text(json.dumps(result,indent=2)+'\n');print('exported',key,result['elapsed_seconds'],flush=True)
        return result
    records=[r for r in manifest['records'] if not args.only or r['stem'] in args.only]
    records.sort(key=lambda r:(r['stem'] not in ('network-fiber','network-groundstations'),r['scope']!='world'))
    results=export_records(records,export,args.workers)
    results.sort(key=lambda r:(r['scope'],r['stem'],r['kind']))
    (args.delivery/'sources'/('sheet-export-manifest-selected.json' if args.only else 'sheet-export-manifest.json')).write_text(
        json.dumps({'records':results,'font_provenance_sha256':font_hash},indent=2)+'\n')
    print('Complete:',len(results),'separate sheets',flush=True)


if __name__=='__main__':main()
