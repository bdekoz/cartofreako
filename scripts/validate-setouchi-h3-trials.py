#!/usr/bin/env python3
"""Validate trial provenance, SVG layers, decoded PDF images, and local review."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from lxml import etree
from PIL import Image
from legend_informatics import ROOT, digest
from setouchi_futures import write_json


def browser_check(output, qa):
    import base64
    import functools
    import http.server
    import runpy
    import tempfile
    import threading
    import time
    from urllib.request import urlopen
    helpers = runpy.run_path(str(ROOT / 'scripts/run-wasm-browser-smoke.py'))
    handler = functools.partial(helpers['QuietHandler'], directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    records = []
    chrome = client = None
    try:
        with tempfile.TemporaryDirectory(prefix='setouchi-h3-browser-') as profile:
            chrome = subprocess.Popen(['google-chrome', '--headless=new', '--no-sandbox', '--disable-gpu',
                '--disable-background-networking', '--no-first-run', '--remote-debugging-port=0',
                '--user-data-dir='+profile, 'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            port_file = Path(profile) / 'DevToolsActivePort'
            deadline = time.monotonic()+20
            while not port_file.exists():
                if chrome.poll() is not None or time.monotonic()>deadline: raise RuntimeError('Chrome did not start')
                time.sleep(.1)
            port=int(port_file.read_text().splitlines()[0])
            with urlopen(f'http://127.0.0.1:{port}/json/list',timeout=5) as response:
                target=next(t for t in json.load(response) if t['type']=='page')
            client=helpers['DevToolsSocket'](target['webSocketDebuggerUrl'])
            client.call('Page.enable');client.call('Runtime.enable')
            for width,height in [(1440,1100),(390,900)]:
                client.call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False})
                url=f'http://127.0.0.1:{server.server_port}/'+output.relative_to(ROOT).as_posix()+'/index.html'
                client.call('Page.navigate',{'url':url})
                deadline=time.monotonic()+30
                while not helpers['page_value'](client,"document.readyState==='complete' && document.images.length===12"):
                    if time.monotonic()>deadline:raise RuntimeError('Trial review did not load')
                    time.sleep(.1)
                helpers['page_value'](client,"[...document.images].forEach(i=>i.loading='eager')")
                decoded=client.call('Runtime.evaluate',{'expression':"(async()=>{await Promise.all([...document.images].map(i=>i.decode()));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return true})()",'awaitPromise':True,'returnByValue':True})
                if decoded.get('exceptionDetails'):raise ValueError('A gallery image failed to decode')
                check=helpers['page_value'](client,"""(()=>({width:innerWidth,figures:document.images.length,
                    decoded:[...document.images].every(i=>i.complete&&i.naturalWidth>0),
                    alt:[...document.images].every(i=>i.alt.length>0),
                    no_overflow:document.documentElement.scrollWidth<=innerWidth+1,
                    columns:getComputedStyle(document.querySelector('.grid')).gridTemplateColumns.split(' ').length}))()""")
                if not all(check[k] for k in ('decoded','alt','no_overflow')) or check['columns']!=(3 if width>800 else 1):
                    raise ValueError('Trial gallery layout check failed: '+str(check))
                records.append(check)
                for index in (range(4) if width>800 else range(1)):
                    helpers['page_value'](client,f"document.querySelectorAll('section')[{index}].scrollIntoView()")
                    client.call('Runtime.evaluate',{'expression':'new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))','awaitPromise':True})
                    capture=client.call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False})
                    (qa/f'{width}-{index}.png').write_bytes(base64.b64decode(capture['data']))
    finally:
        if client:client.close()
        if chrome:chrome.terminate();chrome.wait(timeout=10)
        server.shutdown();server.server_close()
    return records


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'output/setouchi-h3-trials-20261106')
    parser.add_argument('--browser',action='store_true')
    args=parser.parse_args(); output=args.output.resolve()
    delivery=json.loads((output/'plates.json').read_text())
    products=json.loads((output/'products.json').read_text())
    records=delivery['plates']
    expected={(r,s,stem) for r in [5,8] for s in ['world','japan']
              for stem in ['cloud-atmosphere','anthropocene-temperature-2026']}
    if len(records)!=8 or {(p['h3_resolution'],p['scope'],p['stem']) for p in records}!=expected:
        raise ValueError('Expected eight requested map/legend pairs')
    checked=[]
    for record in records:
        for item in record['files']:
            if digest(output/item['path'])!=item['sha256']:raise ValueError('Changed trial artifact: '+item['path'])
        source=ROOT/record['source_svg'];legend=ROOT/record['legend_svg']
        if digest(source)!=record['fingerprint']['source_sha256'] or digest(legend)!=record['fingerprint']['legend_sha256']:
            raise ValueError('Atlas source changed')
        stem,scope,resolution=record['stem'],record['scope'],record['h3_resolution']
        path=output/f'h3r{resolution}/maps/{scope}/{stem}.svg'
        tree=etree.parse(str(path));original=etree.parse(str(source))
        if tree.getroot().get('data-h3-resolution')!=str(resolution):raise ValueError('Wrong plate resolution')
        layers={r['id'] for r in record['layers']}
        def reference_paths(doc):
            return Counter((p.get('id'),p.get('d')) for p in doc.iter('{http://www.w3.org/2000/svg}path')
                           if not any(a.get('id') in layers for a in p.iterancestors()))
        if reference_paths(tree)!=reference_paths(original):raise ValueError('Reference geometry changed: '+str(path))
        images=tree.xpath('//*[local-name()="image"]')
        if len(images)!=len(layers):raise ValueError('Missing data image layer')
        for image in images:
            linked=path.parent/image.get('{http://www.w3.org/1999/xlink}href')
            with Image.open(linked) as raster:
                if raster.width<1000 or raster.height<1000:raise ValueError('Unexpectedly small data raster')
                raster.verify()
        if stem=='cloud-atmosphere':
            outlines=tree.xpath('//*[@id="web-land-outlines"]')
            if len(outlines)!=1 or outlines[0]!=outlines[0].getparent()[-1]:raise ValueError('Atmosphere outlines are not on top')
        # Inkscape can exit 0 while substituting a tiny red-X image when its
        # D-Bus decoder is unavailable. Inspect the PDF's actual image objects.
        pdf=path.with_suffix('.pdf')
        listing=subprocess.check_output(['pdfimages','-list',str(pdf)],text=True)
        image_rows=[line.split() for line in listing.splitlines() if re.match(r'\s*\d+\s+\d+\s+image\s',line)]
        if not image_rows or any(int(row[3])<1000 or int(row[4])<1000 for row in image_rows):
            raise ValueError('PDF contains missing-image placeholders: '+str(pdf))
        with Image.open(path.with_suffix('.png')) as image:
            if image.size!=(13200,5716):raise ValueError('Incorrect full-sheet PNG dimensions')
        text=subprocess.check_output(['pdftotext',str(output/f'h3r{resolution}/legends/{scope}/{stem}-legend.pdf'),'-'],text=True)
        if f'H3r{resolution}' not in text or 'H3 resolution 3' in text:
            raise ValueError('Stale resolution in trial legend')
        product=next(p for p in products['products'] if p['h3_resolution']==resolution and p['stem']==stem)
        if tree.getroot().get('data-trial-product-sha256')!=product['snapshot_sha256']:
            raise ValueError('Map does not identify its trial product')
        checked.append({'resolution':resolution,'scope':scope,'stem':stem,'reference_geometry_retained':True,
                        'data_layers':len(images),'decoded_pdf_images':len(image_rows),'legend_resolution_checked':True})
    soup=BeautifulSoup((output/'index.html').read_text(),'html.parser')
    if len(soup.select('figure img'))!=12:raise ValueError('Expected r3/r5/r8 comparisons for four plates')
    for node in soup.select('[href], [src]'):
        value=node.get('href') or node.get('src')
        if not urlsplit(value).scheme and not value.startswith('#') and not (output/unquote(value.split('#')[0])).exists():
            raise ValueError('Broken review link: '+value)
    baseline=ROOT/'output/setouchi-futures-20261106'
    previous=json.loads((baseline/'validation.json').read_text())
    if digest(baseline/'prepared.json')!=previous['prepared_sha256'] or digest(baseline/'index.html')!=previous['preview_sha256']:
        raise ValueError('Saved H3r3 delivery changed')
    result={'schema':'cartofreako-setouchi-h3-validation-v1','plates':checked,'pairs':8,'comparison_figures':12,
            'baseline_unchanged':True,'plates_sha256':digest(output/'plates.json'),
            'products_sha256':digest(output/'products.json'),'browser':[]}
    if args.browser:
        qa=ROOT/'build/setouchi-h3-trials-qa';qa.mkdir(parents=True,exist_ok=True)
        result['browser']=browser_check(output,qa)
    write_json(output/'validation.json',result)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
