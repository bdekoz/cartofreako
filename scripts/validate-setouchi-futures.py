#!/usr/bin/env python3
"""Check the local Setouchi gallery package; optionally inspect it in Chrome."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from setouchi_futures import ROOT, digest, load_config, write_json
from setouchi_futures_publish import load_prepared, parse_blocks, used_keys


def browser_checks(output, temp):
    """Use the existing CDP client and real image completion, rather than virtual time."""
    import base64
    import functools
    import http.server
    import runpy
    import threading
    import time
    from urllib.request import urlopen
    helpers = runpy.run_path(str(ROOT / 'scripts/run-wasm-browser-smoke.py'))
    handler = functools.partial(helpers['QuietHandler'], directory=str(output))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    records = []
    chrome = client = None
    try:
        with tempfile.TemporaryDirectory(prefix='setouchi-browser-') as profile:
            chrome = subprocess.Popen(['google-chrome', '--headless=new', '--no-sandbox', '--disable-gpu',
                '--disable-background-networking', '--no-first-run', '--remote-debugging-port=0',
                '--user-data-dir=' + profile, 'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            port_file = Path(profile) / 'DevToolsActivePort'
            deadline = time.monotonic() + 15
            while not port_file.exists():
                if chrome.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError('Chrome could not start its local DevTools connection')
                time.sleep(.05)
            port = int(port_file.read_text().splitlines()[0])
            with urlopen(f'http://127.0.0.1:{port}/json/list', timeout=5) as response:
                target = next(t for t in json.load(response) if t['type'] == 'page')
            client = helpers['DevToolsSocket'](target['webSocketDebuggerUrl'])
            client.call('Page.enable')
            client.call('Runtime.enable')

            def evaluate(expression):
                return helpers['page_value'](client, expression)

            def wait_for(expression):
                deadline = time.monotonic() + 20
                while not evaluate(expression):
                    if time.monotonic() > deadline:
                        raise ValueError('Timed out waiting for browser: ' + expression)
                    time.sleep(.1)

            def finish_image_paint():
                # `complete` means fetched, not painted: decoding="async" can
                # otherwise leave a correctly loaded image blank in a capture.
                result = client.call('Runtime.evaluate', {
                    'expression': """(async()=>{
                        await Promise.all([...document.images].map(i=>i.decode()));
                        await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
                        return true;
                    })()""", 'awaitPromise': True, 'returnByValue': True})
                if result.get('exceptionDetails') or result.get('result', {}).get('value') is not True:
                    raise ValueError('Browser could not decode and paint the gallery images')

            for width, height in [(1440, 1100), (390, 900)]:
                client.call('Emulation.setDeviceMetricsOverride', {'width': width, 'height': height,
                            'deviceScaleFactor': 1, 'mobile': False})
                url = f'http://127.0.0.1:{server.server_port}/index.html?viewport={width}'
                client.call('Page.navigate', {'url': url})
                wait_for('location.href===' + json.dumps(url) +
                         " && document.readyState==='complete' && document.images.length===13")
                lazy = evaluate("[...document.images].every(i=>i.loading==='lazy')")
                evaluate("[...document.images].forEach(i=>{i.loading='eager';})")
                wait_for("[...document.images].every(i=>i.complete&&i.naturalWidth>0)")
                for section in ['World', 'Japan / Setouchi', 'Hamonshū Revisited']:
                    section_json = json.dumps(section)
                    evaluate("(()=>{const h=[...document.querySelectorAll('h3')].find(h=>h.textContent===" + section_json +
                             ");scrollTo(0,h.getBoundingClientRect().top+scrollY-20);})()")
                    finish_image_paint()
                    values = evaluate("""(()=>{const images=[...document.images];return {
                        viewport:[innerWidth,innerHeight], no_horizontal_overflow:document.documentElement.scrollWidth<=innerWidth+1,
                        image_count:images.length,all_images_loaded:images.every(i=>i.complete&&i.naturalWidth>0),
                        all_have_alt:images.every(i=>i.alt.length>0),
                        stacked_on_phone:innerWidth>781||[...document.querySelectorAll('.wp-block-columns')].every(r=>getComputedStyle(r).display==='block'),
                        gallery_sections:[...document.querySelectorAll('h3')].map(h=>h.textContent),
                        images_inside_viewport:images.every(i=>i.getBoundingClientRect().right<=innerWidth+1),
                        hamonshu_heights:images.slice(-3).map(i=>Math.round(i.getBoundingClientRect().height))};})()""")
                    values.update(section=section, lazy_loading_declared=lazy, images_decoded_before_capture=True)
                    for key in ['no_horizontal_overflow', 'all_images_loaded', 'all_have_alt', 'lazy_loading_declared', 'stacked_on_phone', 'images_inside_viewport']:
                        if not values[key]:
                            raise ValueError(f'{width} {section}: failed {key}')
                    if values['viewport'] != [width, height] or len(set(values['hamonshu_heights'])) != 1:
                        raise ValueError('Unexpected viewport or unequal Hamonshū frames')
                    stem = f'{width}-' + ('world' if section == 'World' else 'japan' if section.startswith('Japan') else 'hamonshu')
                    data = client.call('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': False})
                    (temp / (stem + '.png')).write_bytes(base64.b64decode(data['data']))
                    records.append(values)
    finally:
        if client:
            client.close()
        if chrome:
            chrome.terminate()
            chrome.wait(timeout=10)
        server.shutdown()
        server.server_close()
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / load_config()['output'])
    parser.add_argument('--browser', action='store_true')
    parser.add_argument('--qa-dir', type=Path, default=ROOT / 'build/setouchi-futures-qa')
    args = parser.parse_args()
    output = args.output.resolve()
    prepared = load_prepared(output)
    document = BeautifulSoup((output / 'index.html').read_text(), 'html.parser')
    broken = []
    for node in document.select('[href], [src]'):
        value = node.get('href') or node.get('src')
        if not urlsplit(value).scheme and not value.startswith('#'):
            if not (output / unquote(value.split('#')[0])).exists():
                broken.append(value)
    if broken:
        raise ValueError('Broken local links: ' + ', '.join(broken))
    if len(document.select('figure img')) != 13:
        raise ValueError('Expected ten maps and three Hamonshū details')
    blocks = parse_blocks((output / 'gallery-blocks.html').read_text())
    if sum(b['name'] == 'image' for b in blocks) != 13:
        raise ValueError('Wrong WordPress figure count')
    sources_checked = 0
    atlas_sources_checked = 0
    selected_plates = []
    for item in prepared['provenance']:
        if 'source_svg' in item:
            for source_key, hash_key in [('source_svg', 'source_sha256'), ('legend_svg', 'legend_sha256')]:
                if digest(ROOT / item[source_key]) != item[hash_key]:
                    raise ValueError('Atlas master changed: ' + item['id'])
                sources_checked += 1
                if not item.get('selected_plate'):
                    atlas_sources_checked += 1
        if item.get('selected_plate'):
            from setouchi_selected_plates import load_selection
            scope, stem = item['id'].split('-', 1)
            settings = next(m for m in prepared['config']['maps'] if m['stem'] == stem)
            _, selected = load_selection(settings, scope)
            resolution = prepared['config']['analysis_h3_resolution']
            if item['h3_resolution'] != resolution or selected['h3_resolution'] != resolution:
                raise ValueError('Mixed H3 resolutions in selected edition')
            if item['product_sha256'] != selected['fingerprint']['snapshot_sha256']:
                raise ValueError('Selected product differs from provenance')
            for file in item['print_files']:
                if digest(output / file['path']) != file['sha256']:
                    raise ValueError('Changed selected print artifact: ' + file['path'])
            legend = subprocess.check_output(['pdftotext', str(output / ('media/' + item['id'] + '-legend.pdf')), '-'], text=True)
            if f'H3r{resolution} selected edition' not in legend or 'H3 resolution 3' in legend:
                raise ValueError('Selected legend uses a stale resolution')
            selected_plates.append({'id': item['id'], 'h3_resolution': resolution,
                                    'product_sha256': item['product_sha256'], 'print_files_checked': len(item['print_files'])})
    if prepared.get('selected_print'):
        expected = {(scope + '-' + m['stem']) for scope in ['world', 'japan']
                    for m in prepared['config']['maps'] if m.get('prepared_plate')}
        if {p['id'] for p in selected_plates} != expected:
            raise ValueError('Missing selected print plates')
        for file in prepared['selected_print']['files']:
            if digest(output / file['path']) != file['sha256']:
                raise ValueError('Changed combined print file')
            if file['path'].endswith('.pdf'):
                info = subprocess.check_output(['pdfinfo', str(output / file['path'])], text=True)
                pages = next(int(line.split(':')[1]) for line in info.splitlines() if line.startswith('Pages:'))
                if pages != len(expected):
                    raise ValueError('Combined print PDF has the wrong page count')
        print_page = BeautifulSoup((output / 'print/index.html').read_text(), 'html.parser')
        for node in print_page.select('[href], [src]'):
            value = node.get('href') or node.get('src')
            if not urlsplit(value).scheme and not (output / 'print' / unquote(value.split('#')[0])).exists():
                raise ValueError('Broken print index link: ' + value)
    for scope in ['world', 'japan']:
        pdf = output / f'media/{scope}-network-fiber-legend.pdf'
        text = subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True)
        if 'Amber (web edition)' not in text or 'Submarine cables: Black' in text:
            raise ValueError('Fiber legend text does not match the web variation')
    radiation = []
    for item in prepared['provenance']:
        record = item.get('web_radiation_opacity') or item.get('selected_radiation_opacity')
        if not record:
            continue
        if record.get('inputs'):
            for name in ('snapshot', 'profile'):
                if digest(ROOT / record['inputs'][name]) != record['inputs'][name + '_sha256']:
                    raise ValueError('Radiation source changed: ' + name)
        pdf = output / ('media/' + item['id'] + '-legend.pdf')
        legend = subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True)
        if (f'{record["bands"]} opacity bands' not in legend
                or 'Missing observations are not zero.' not in legend):
            raise ValueError('Radiation legend does not describe the opacity scale')
        radiation.append({'id': item['id'], 'bands': record['bands'], 'observed_cells': record['observed_cells'],
                          'populated_bands': record['populated_bands'], 'legend_verified': True})
    brief = subprocess.check_output(['pdfinfo', str(output / 'outreach/brief.pdf')], text=True)
    if not any(line.startswith('Pages:') and line.split()[-1] == '1' for line in brief.splitlines()):
        raise ValueError('Outreach brief must fit on one A4 page')
    result = {'schema': 'cartofreako-setouchi-futures-validation-v1', 'status': 'local-only',
        'prepared_sha256': digest(output / 'prepared.json'), 'preview_sha256': digest(output / 'index.html'),
        'media_assets': len(prepared['assets']), 'upload_assets': len(used_keys(prepared)),
        'figures': 13, 'map_legend_pairs': 10, 'unchanged_atlas_masters': atlas_sources_checked,
        'source_sheets_checked': sources_checked, 'selected_h3_plates': selected_plates,
        'broken_local_links': broken, 'fiber_legend_text_verified': True, 'outreach_pdf_pages': 1,
        'radiation_opacity': radiation, 'browser': []}
    if args.browser:
        args.qa_dir.mkdir(parents=True, exist_ok=True)
        result['browser'] = browser_checks(output, args.qa_dir.resolve())
    write_json(output / 'validation.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
