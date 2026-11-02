#!/usr/bin/env python3
"""Validate the ST31–ST33 delivery, including A4, CV content and local web pages."""
import argparse
import importlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup
from lxml import etree as E
from PIL import Image, ImageChops
from reportlab.lib.pagesizes import A4

from legend_informatics import ROOT, WIDTH, HEIGHT, digest

BUILD = importlib.import_module('build-setouchi-proposal')


def require(value, message):
    if not value:
        raise ValueError(message)


def pdf_text(path, first=None, last=None):
    command = ['pdftotext', '-layout']
    if first:
        command += ['-f', str(first), '-l', str(last or first)]
    return subprocess.check_output([*command, str(path), '-'], text=True)


def pdf_sizes(path, pages):
    info = subprocess.check_output(['pdfinfo', '-f', '1', '-l', str(pages), str(path)], text=True)
    actual = int(re.search(r'Pages:\s+(\d+)', info)[1])
    require(actual == pages, f'{path.name}: {actual} pages, expected {pages}')
    sizes = [tuple(map(float, size)) for size in re.findall(r'Page\s+\d+ size:\s+([\d.]+) x ([\d.]+)', info)]
    require(len(sizes) == pages, f'{path.name}: missing page dimensions')
    return sizes


def dimensions(actual, expected):
    return all(abs(a - b) < .35 for a, b in zip(actual, expected))


def inspect_atlases(output):
    receipt = json.loads((output / 'sources/atlas-revision.json').read_text())
    results = {}
    for scope, edition in receipt['editions'].items():
        path = output / edition['path']
        require(digest(path) == edition['sha256'], scope + ': atlas hash mismatch')
        sizes = pdf_sizes(path, 75)
        for i, size in enumerate(sizes):
            require(dimensions(size, A4 if i in (1, 2) else (WIDTH * 72, HEIGHT * 72)),
                    f'{scope}: wrong size on page {i+1}')
        cover = E.fromstring(subprocess.check_output(['pdftohtml', '-xml', '-zoom', '1', '-f', '1', '-l', '1', '-stdout',
                                                       str(output / 'sources' / f'title-page-{scope}.pdf')]))
        texts = cover.findall('.//text')
        values = [''.join(t.itertext()) for t in texts]
        require(values == ['CARTOFREAKO', receipt['generation_date'], scope.upper()], scope + ': cover wording')
        fonts = {f.get('id'): float(f.get('size')) for f in cover.findall('.//fontspec')}
        font_sizes = [fonts[t.get('font')] for t in texts]
        require(font_sizes[0] == font_sizes[2] and abs(font_sizes[1] * 2 - font_sizes[0]) <= 1,
                scope + ': title/date/scope font sizes')
        for text in texts:
            centre = float(text.get('left')) + float(text.get('width')) / 2
            require(abs(centre - WIDTH * 72 / 2) <= 1, scope + ': cover text not centered')
        require([float(t.get('top')) for t in texts] == sorted(float(t.get('top')) for t in texts),
                scope + ': cover line order')
        notes = pdf_text(path, 2)
        require(scope.title() + ' Atlas' in notes, scope + ': atlas name')
        require('111.76 × 48.39 cm' in notes, scope + ': centimetre dimensions')
        require('remain recorded in the development document.' in notes, scope + ': development reference')
        for old in ('ST2', 'Map image width', 'Centered margins', 'inches', '-inch'):
            require(old not in notes, scope + ': obsolete edition wording ' + old)
        index = pdf_text(path, 3)
        for value in BUILD.ATLAS.INDEX_TITLES.values():
            require(value in index, scope + ': missing index title ' + value)
        require(len(re.findall(r'Plate \d\d / PDF pages', index)) == 36, scope + ': index subject count')
        for sheet in edition['retained_sheets']:
            require(digest(ROOT / sheet['path']) == sheet['sha256'], 'Retained source changed: ' + sheet['path'])
        require(len(edition['retained_sheets']) == 72, scope + ': retained sheet count')
        # Text-layer comparison covers every output map and legend in the correct order.
        actual_pages = pdf_text(path, 4, 75).split('\f')[:72]
        for actual, sheet in zip(actual_pages, edition['retained_sheets']):
            require(actual.split() == pdf_text(ROOT / sheet['path']).split(),
                    f'{scope}: text or sequence mismatch on page {sheet["atlas_page"]}')
        results[scope] = {'pages': 75, 'all_page_dimensions_checked': True, 'cover_type_sizes_pt': font_sizes,
                          'cover_centering_and_order': True, 'edition_notes': True, 'index_titles': True,
                          'retained_sheet_checksums': 72, 'retained_page_text_comparisons': 72}
    return results


def inspect_application(output, temp):
    path = output / BUILD.PROPOSAL_NAME
    require(all(dimensions(size, A4) for size in pdf_sizes(path, 10)), 'Application must be ten A4 pages')
    require(path.stat().st_size < 2_000_000_000, 'Application exceeds file-size limit')
    text = pdf_text(path)
    page_text = text.split('\f')[:10]
    content = json.loads((output / 'sources/proposal-content.json').read_text())
    for i, page in enumerate(content):
        require(page['title'] in page_text[i], f'Application section shifted from page {i+1}')
    for obsolete in ('NN sections', 'TBD experts', 'ST2 Japan atlas'):
        require(obsolete not in text, 'Unresolved draft wording: ' + obsolete)
    require(BUILD.CANONICAL_URL in text, 'Canonical project URL absent from application')
    bbox_file = temp / 'application-bbox.html'
    subprocess.run(['pdftotext', '-bbox-layout', str(path), str(bbox_file)], check=True)
    xml = E.parse(str(bbox_file))
    ns = {'h': 'http://www.w3.org/1999/xhtml'}
    bounds = []
    for i, page in enumerate(xml.findall('.//h:page', ns), 1):
        words = page.findall('.//h:word', ns)
        require(words, f'Application page {i} has no text')
        for word in words:
            x0, y0, x1, y1 = [float(word.get(k)) for k in ('xMin', 'yMin', 'xMax', 'yMax')]
            require(0 <= x0 <= x1 <= A4[0] + .1 and 0 <= y0 <= y1 <= A4[1] + .1,
                    f'Application page {i} text extends off the sheet')
            require('�' not in (word.text or '') and '■' not in (word.text or ''), 'Missing text glyph')
        body = [w for w in words if 40 < float(w.get('yMin')) < 800]
        bounds.append({'page': i, 'body_bottom_pt': round(max(float(w.get('yMax')) for w in body), 2)})
    # The concise concept and selected CV each fit in less than half an A4 sheet.
    p1 = xml.findall('.//h:page', ns)[0]
    p10 = xml.findall('.//h:page', ns)[9]
    def y_for(page, start):
        for line in page.findall('.//h:line', ns):
            value = ' '.join(w.text or '' for w in line.findall('h:word', ns))
            if value.startswith(start):
                return float(line.get('yMin'))
        raise ValueError('Missing text marker ' + start)
    concept_start = y_for(p1, 'Concept')
    concept_end = y_for(p1, 'World · Water.')
    # This deliberately includes the map before its caption, giving an upper bound.
    require(concept_end - concept_start < A4[1] / 2, 'Concept is longer than half a page')
    cv_height = y_for(p10, 'References and visual sources') - y_for(p10, 'Selected CV')
    require(cv_height < A4[1] / 2, 'Selected CV is longer than half a page')
    figures = json.loads((output / 'sources/figure-provenance.json').read_text())
    for fig in figures:
        require(digest(output / fig['path']) == fig['sha256'] == fig['source']['sha256'], 'Figure bytes changed')
        require(digest(ROOT / fig['source']['path']) == fig['source']['sha256'], 'Figure source changed')
        require(all(use['effective_dpi'] >= 300 for use in fig['uses']), 'Figure below 300 dpi')
    budget = json.loads((output / 'sources/budget.json').read_text())
    subtotal = sum(item['amount'] for item in budget['items'])
    require(subtotal == budget['subtotal'] and budget['contingency'] == subtotal // 10, 'Budget arithmetic')
    require(budget['total'] == subtotal + budget['contingency'] <= 2_500_000, 'Budget total/ceiling')
    require(f'{budget["total"]:,}' in page_text[8], 'Budget total missing from PDF')
    return {'pages': 10, 'all_a4': True, 'bytes': path.stat().st_size, 'section_order': True,
            'text_bounds': bounds, 'concept_with_hero_upper_bound_pt': round(concept_end - concept_start, 2),
            'selected_cv_height_pt': round(cv_height, 2), 'distinct_source_figures': len(figures),
            'minimum_figure_dpi': min(use['effective_dpi'] for f in figures for use in f['uses']),
            'budget_total_jpy': budget['total']}


def inspect_cv(output):
    source = ROOT / 'assets.static/setouchi-triennale/20261101-art-cv-2p.pdf'
    target = output / BUILD.CV_A4_NAME
    require(all(dimensions(size, A4) for size in pdf_sizes(target, 2)), 'Full CV must be two A4 pages')
    original, converted = pdf_text(source), pdf_text(target)
    require(original.split() == converted.split(), 'CV text changed during conversion')
    def links(path):
        xml = subprocess.check_output(['pdftohtml', '-xml', '-stdout', str(path)], text=True)
        # A single annotation can span several text runs after PDF conversion.
        return set(re.findall(r'href="([^"]+)"', xml))
    link_targets = links(source)
    require(link_targets == links(target), 'CV hyperlink targets changed')
    images = subprocess.check_output(['pdfimages', '-list', str(target)], text=True).splitlines()[2:]
    require(not images, 'Converted CV unexpectedly contains raster images')
    fonts = subprocess.check_output(['pdffonts', str(target)], text=True).splitlines()[2:]
    require(len(fonts) == 3 and all(re.search(r'\s+yes\s+yes\s+yes\s+\d+\s+\d+', line) for line in fonts),
            'CV fonts must remain embedded, subset and Unicode mapped')
    return {'pages': 2, 'all_a4': True, 'all_text_tokens_preserved': True,
            'embedded_fonts': 3, 'raster_images': 0, 'hyperlink_targets_preserved': len(link_targets),
            'bytes': target.stat().st_size}


def local_links(output):
    results = []
    for name in ('index.html', 'proposal.html', 'wordpress/preview.html', 'wordpress/page-content.html'):
        path = output / name
        soup = BeautifulSoup(path.read_text(), 'html.parser')
        count = 0
        for item in soup.select('[href],[src]'):
            link = item.get('href', item.get('src'))
            url = urlparse(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (path.parent / unquote(url.path)).resolve()
            if target == output / 'sources/validation.json':
                continue  # Written atomically at the end of this validation.
            require(target.is_file(), f'{name}: missing local resource {link}')
            count += 1
        require(all(img.get('alt') for img in soup.select('img')), name + ': image missing alt text')
        results.append({'page': name, 'local_resources': count, 'alt_text': True})
    content = (output / 'wordpress/page-content.html').read_text()
    opened = re.findall(r'<!-- wp:([\w/-]+)', content)
    closed = re.findall(r'<!-- /wp:([\w/-]+)', content)
    require(opened == closed, 'Unbalanced WordPress blocks')
    metadata = json.loads((output / 'wordpress/page.json').read_text())
    require(metadata['page_id'] == 3175 and metadata['canonical_url'] == BUILD.CANONICAL_URL, 'WordPress destination')
    for media in json.loads((output / 'wordpress/media-manifest.json').read_text()):
        require(digest(output / media['path']) == media['sha256'], 'WordPress asset checksum')
    return results


def browser(output, temp):
    results = []
    for filename in ('index.html', 'proposal.html', 'wordpress/preview.html'):
        for width, height in ((1440, 1100), (390, 900)):
            # A fixed-size iframe gives an actual 390 px CSS viewport even on
            # Chrome versions which clamp the outer window to at least 500 px.
            wrapper = temp / 'browser.html'
            script = '''const f=document.createElement('iframe');
f.style.cssText='display:block;border:0;width:WIDTHpx;height:HEIGHTpx';
f.onload=()=>{const w=f.contentWindow,d=f.contentDocument;
 const images=[...d.images];const results={viewport:[w.innerWidth,w.innerHeight],
  no_horizontal_overflow:d.documentElement.scrollWidth<=w.innerWidth+1,
  loaded_images:images.length,all_images_loaded:images.every(i=>i.complete&&i.naturalWidth>0),
  headings:d.querySelectorAll('h1').length,links:d.querySelectorAll('a[href]').length};
 const p=document.createElement('pre');p.id='qa-result';p.textContent=JSON.stringify(results);document.body.append(p);};
f.src=URL;document.body.append(f);'''.replace('WIDTH', str(width)).replace('HEIGHT', str(height)).replace('URL', json.dumps((output / filename).as_uri()))
            wrapper.write_text('<!doctype html><meta charset="utf-8"><style>body{margin:0}</style><body><script>' + script + '</script>')
            command = ['google-chrome', '--headless', '--no-sandbox', '--disable-gpu', '--no-first-run',
                       '--disable-background-networking', '--allow-file-access-from-files',
                       '--user-data-dir=' + str(temp / 'chrome'), f'--window-size={max(width,500)},{height}',
                       '--virtual-time-budget=2500', '--dump-dom', wrapper.as_uri()]
            result = subprocess.run(command, text=True, capture_output=True, timeout=45, check=True)
            answer = BeautifulSoup(result.stdout, 'html.parser').select_one('#qa-result')
            require(answer is not None, f'Browser produced no result: {filename}: ' + result.stderr[-400:])
            values = json.loads(answer.get_text())
            require(values['viewport'] == [width, height], 'Browser viewport mismatch')
            require(values['no_horizontal_overflow'] and values['all_images_loaded'] and values['headings'] > 0,
                    f'Browser check failed: {filename} {width}: {values}')
            results.append(dict(values, page=filename, page_sha256=digest(output / filename)))
    return results


def raster_conservation(output, temp):
    receipt = json.loads((output / 'sources/atlas-revision.json').read_text())
    results = []
    for scope, stem, kind in (('world', 'water', 'map'), ('japan', 'water', 'map'),
                              ('world', 'network-fiber', 'legend'), ('japan', 'network-swarm-ge-1080p', 'map')):
        edition = receipt['editions'][scope]
        sheet = next(s for s in edition['retained_sheets'] if s['stem'] == stem and s['kind'] == kind)
        paths = [ROOT / sheet['path'], output / edition['path']]
        pngs = []
        for i, path in enumerate(paths):
            page = 1 if i == 0 else sheet['atlas_page']
            prefix = temp / f'comparison-{i}'
            subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-singlefile', '-scale-to', '1400',
                            '-png', str(path), str(prefix)], check=True, capture_output=True)
            pngs.append(prefix.with_suffix('.png'))
        with Image.open(pngs[0]) as before, Image.open(pngs[1]) as after:
            require(before.size == after.size and ImageChops.difference(before, after).getbbox() is None,
                    f'Atlas graphics changed: {scope} {stem} {kind}')
        results.append({'scope': scope, 'stem': stem, 'kind': kind, 'pixel_identical_at_1400_px': True})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'output/setouchi-triennale-2028-v3')
    parser.add_argument('--skip-browser', action='store_true')
    parser.add_argument('--browser-only', action='store_true', help='Finish browser checks on an otherwise validated delivery')
    args = parser.parse_args()
    output = args.output.resolve()
    validation_path = output / 'sources/validation.json'
    if args.browser_only:
        result = json.loads(validation_path.read_text())
        for item in result['validated_products']:
            require(digest(output / item['path']) == item['sha256'], 'Product changed since PDF validation')
        with tempfile.TemporaryDirectory(prefix='setouchi-v3-browser-') as tmp:
            result['browser'] = browser(output, Path(tmp))
        result['browser_checked'] = True
        BUILD.write_json(validation_path, result)
        BUILD.checksums(output)
        print('Passed: desktop and 390 px mobile browser checks for all three local pages.')
        return
    with tempfile.TemporaryDirectory(prefix='setouchi-v3-validation-') as tmp:
        temp = Path(tmp)
        result = {'status': 'passed', 'atlases': inspect_atlases(output),
                  'application': inspect_application(output, temp), 'cv_a4': inspect_cv(output),
                  'local_pages': local_links(output), 'raster_conservation': raster_conservation(output, temp),
                  'browser': [] if args.skip_browser else browser(output, temp),
                  'browser_checked': not args.skip_browser,
                  'remote_publication_verified': False}
    result['validated_products'] = [BUILD.record(output / name, output) for name in (
        BUILD.PROPOSAL_NAME, BUILD.CV_A4_NAME, 'setouchi-tri-explore-v3-world.pdf',
        'setouchi-tri-explore-v3-japan.pdf', 'index.html', 'proposal.html',
        'wordpress/preview.html', 'wordpress/page-content.html')]
    BUILD.write_json(validation_path, result)
    BUILD.checksums(output)
    print('Passed: 150 atlas pages, 10 A4 application pages, 2 A4 CV pages, source conservation and local web checks.')


if __name__ == '__main__':
    main()
