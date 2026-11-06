"""Compose resolution trials using existing Setouchi frames and source paint."""
from copy import deepcopy
from html import escape
import json
import math
from pathlib import Path
import re
import shutil
import subprocess

from lxml import etree
from PIL import Image

from legend_informatics import ROOT, digest, font_environment
from setouchi_futures import (SVG, background_variation, land_outline_overlay,
                              resize_image, write_json)
from setouchi_radiation import update_legend

HREF = '{http://www.w3.org/1999/xlink}href'


def render_svg(source, target, env, width=None):
    args = ['inkscape', str(source), '--export-area-page', '--export-filename=' + str(target)]
    if width: args.append('--export-width=' + str(width))
    result = subprocess.run(args, env=env, text=True, capture_output=True)
    if result.returncode or 'Pixbuf::create_' in result.stderr or 'D-Bus error' in result.stderr:
        raise RuntimeError('Inkscape could not decode/render the trial layers. Its local image decoder '
                           'needs a working D-Bus connection. ' + result.stderr[-1500:])


def metadata(path):
    # Both deterministic preparers write small metadata before their features.
    with path.open() as source:
        start = source.read(65536)
    offset = start.index('"metadata":') + len('"metadata":')
    return json.JSONDecoder().raw_decode(start[offset:].lstrip())[0]


def parse_style(text):
    values = dict((k.strip(), v.strip()) for k, v in
                  (p.split(':', 1) for p in text.split(';') if ':' in p))
    def color(name):
        match = re.fullmatch(r'rgb\((\d+),(\d+),(\d+)\)', values[name])
        if not match:
            raise ValueError('Expected source RGB paint: ' + text)
        return [int(c) / 255 for c in match.groups()] + [float(values[name + '-opacity'])]
    return {'fill': color('fill'), 'stroke': color('stroke'), 'width': float(values['stroke-width'])}


def settings_for(atlas, stem, dpi):
    world = etree.parse(str(atlas / 'maps/world/svg' / (stem + '.svg')))
    japan = etree.parse(str(atlas / 'maps/japan/svg' / (stem + '.svg')))
    styles = {}
    for node in world.xpath('//*[@data-bin or @id="cpc-covered-cells"]'):
        styles.setdefault(node.getparent().get('id'), {})[node.get('data-bin', '0')] = parse_style(node.get('style'))
    if stem == 'cloud-atmosphere':
        # The original snapshot has no sixth-bin rain path; a finer grid can.
        styles['precipitation-rate'].setdefault('6', {
            'fill': [41/255, 127/255, 184/255, .7],
            'stroke': [41/255, 127/255, 184/255, .7], 'width': .0025})
    uses = japan.xpath('//*[local-name()="use" and @xlink:href="#source-content"]',
                       namespaces={'xlink': 'http://www.w3.org/1999/xlink'})
    if len(uses) != 1:
        raise ValueError('Expected one Japan data viewport')
    view = uses[0].getparent()
    match = re.fullmatch(r'translate\(([-.\d]+) ([-.\d]+)\) scale\(([-.\d]+)\)', view.get('transform'))
    if not match:
        raise ValueError('Unexpected Japan viewport transform')
    tx, ty, scale = map(float, match.groups())
    clip_id = view.getparent().get('clip-path').removeprefix('url(#').removesuffix(')')
    rect = japan.xpath('//*[@id=$ident]/*[local-name()="rect"]', ident=clip_id)[0]
    x, y, width, height = (float(rect.get(k)) for k in ['x', 'y', 'width', 'height'])
    pad = .06  # Include strokes crossing the viewport before the SVG clips them.
    bounds = [(x-tx)/scale-pad, (y-ty)/scale-pad, width/scale+2*pad, height/scale+2*pad]
    return {'styles': styles, 'views': [
        {'id': 'world', 'bounds': [0, 0, 44, 19.052559], 'pixels_per_unit': dpi},
        {'id': 'japan', 'bounds': bounds, 'pixels_per_unit': dpi*scale}],
        'radiation_opacity': {'bands': 100, 'scale_min': 0, 'scale_max': 400}}


def prepare_tiles(config, product, atlas):
    for key in ('profile', 'snapshot'):
        if digest(ROOT / product[key]) != product[key + '_sha256']:
            raise ValueError('Changed trial input: ' + product[key])
    build = ROOT / config['build'] / f'h3r{product["h3_resolution"]}' / product['subject']
    build.mkdir(parents=True, exist_ok=True)
    settings = settings_for(atlas, product['stem'], config['data_raster_dpi'])
    helper = ROOT / 'build/setouchi-h3-tools/render-cells'
    settings_path = build / 'render-settings.json'
    write_json(settings_path, settings)
    fingerprint = {'settings': settings, 'renderer_sha256': digest(helper),
                   'snapshot_sha256': product['snapshot_sha256'], 'profile_sha256': product['profile_sha256']}
    receipt = build / 'render-inputs.json'
    old = json.loads(receipt.read_text()) if receipt.exists() else None
    if not (old and old['fingerprint'] == fingerprint and
            all((build / f).exists() and digest(build / f) == sha for f, sha in old['files'].items())):
        print(f'Rendering {product["subject"]} H3r{product["h3_resolution"]} cell tiles', flush=True)
        subprocess.run([str(helper), product['subject'], str(ROOT / product['profile']),
                        str(ROOT / product['snapshot']), str(settings_path), str(build)], check=True)
        rendered = json.loads((build / 'render.json').read_text())
        files = ['render.json'] + [t['file'] for layer in rendered['layers'] for t in layer['tiles']]
        old = {'fingerprint': fingerprint, 'files': {f: digest(build / f) for f in files}}
        write_json(receipt, old)
    rendered = json.loads((build / 'render.json').read_text())
    if old.get('single_hue_rgb') != 1:
        # Cairo stores premultiplied 8-bit color. Unpremultiplication can vary
        # RGB at faint pixels even when the source is a single fixed hue.
        # Preserve the exact alpha plane and restore that declared source hue.
        # This also compresses much better than those rounding variations.
        for layer in rendered['layers']:
            colors = {tuple(round(v*255) for v in style[part][:3])
                      for style in settings['styles'][layer['id']].values()
                      for part in ('fill','stroke') if style[part][3] > 0}
            if len(colors) == 1:
                color = next(iter(colors))
                for tile in layer['tiles']:
                    path = build / tile['file']
                    with Image.open(path) as original:
                        alpha = original.getchannel('A')
                        normalized = Image.new('RGB', original.size, color)
                        normalized.putalpha(alpha)
                        normalized.save(path, compress_level=9)
        old['single_hue_rgb'] = 1
        old['files'] = {f: digest(build/f) for f in old['files']}
        write_json(receipt, old)
    if rendered['h3_resolution'] != product['h3_resolution']:
        raise ValueError('Renderer used the wrong H3 resolution')
    return build, settings, rendered


def map_tree(source, product, build, settings, rendered, item, scope, data_metadata, directory):
    tree = etree.parse(str(source))
    root = tree.getroot()
    root.set('data-h3-resolution', str(product['h3_resolution']))
    root.set('data-h3-trial', 'source-center aggregation; actual cell boundaries; no interpolation')
    root.set('data-data-rendering', '300-dpi linked transparent PNG layers; PDF embeds layers; reference geometry remains vector')
    root.set('data-trial-product-sha256', product['snapshot_sha256'])
    root.set('data-legend-companion', f'../../legends/{scope}/{product["stem"]}-legend.svg')
    view = next(v for v in settings['views'] if v['id'] == scope)
    for layer in rendered['layers']:
        groups = tree.xpath('//*[@id=$ident]', ident=layer['id'])
        if len(groups) != 1:
            raise ValueError('Expected one source data layer: ' + layer['id'])
        group = groups[0]
        for child in list(group): group.remove(child)
        tile = next(t for t in layer['tiles'] if t['scope'] == scope)
        path = build / tile['file']
        group.set('data-observed-cells', str(layer['observed_cells']))
        group.set('data-visible-cells', str(tile['visible_cells']))
        group.set('data-h3-resolution', str(product['h3_resolution']))
        linked = directory / 'layers' / (product['stem'] + '-' + layer['id'] + '.png')
        linked.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, linked)
        attrs = dict(zip(['x', 'y', 'width', 'height'], map(str, view['bounds'])))
        attrs.update({'preserveAspectRatio': 'none', HREF: linked.relative_to(directory).as_posix()})
        etree.SubElement(group, '{' + SVG + '}image', attrs)
    meta = tree.xpath('//*[@id=$ident]', ident=(
        'cloud-atmosphere-metadata' if product['subject'] == 'atmosphere' else 'anthropocene-temperature-metadata'))[0]
    meta.set('data-h3-resolution', str(product['h3_resolution']))
    meta.set('data-feature-count', str(data_metadata['feature_count'] if 'feature_count' in data_metadata else rendered['feature_count']))
    if product['subject'] == 'temperature':
        meta.set('data-covered-cell-count', str(data_metadata['covered_cell_count']))
        for attr, metric in [('data-record-high-total', 'cpc_temperature_record_high_days'),
                             ('data-record-low-total', 'cpc_temperature_record_low_days')]:
            meta.set(attr, str(data_metadata['metric_totals'][metric]))
        meta.set('data-cell-domain', 'source-grid-centers')
        meta.set('data-workflow', 'Anthropocene NOAA CPC source-center temperature trial')
        meta.set('data-geojson-sha256', product['snapshot_sha256'])
        meta.set('data-missing-semantics', 'zero valid days or no stored sample center is unobserved')
    if item.get('background'): background_variation(tree, item['background'])
    if item.get('land_outline'): land_outline_overlay(tree, item['land_outline'])
    return tree


def legend_tree(source, product, rendered, item, baseline, data_metadata):
    tree = etree.parse(str(source))
    resolution = product['h3_resolution']
    for node in tree.iter('{' + SVG + '}text'):
        if node.text:
            node.text = node.text.replace('H3 resolution 3', f'H3 resolution {resolution}')
            if product['subject'] == 'temperature':
                node.text = node.text.replace('11,945', f'{data_metadata["covered_cell_count"]:,}')
                node.text = node.text.replace('Neutral land: zero; blank: unobserved',
                                              'Neutral observed cells: zero; blank: no valid sample')
    if product['subject'] == 'atmosphere':
        update_legend(tree, item['radiation_opacity'], item['background'])
    group = etree.SubElement(tree.getroot(), '{' + SVG + '}g', id='h3-resolution-trial-notes')
    notes = [f'H3r{resolution} resolution trial · original observation dates and sampling retained',
             'Actual H3 cell boundaries; original source-center values reaggregated directly at this resolution.',
             'Unoccupied cells have no sampled center: unobserved, not zero. Source-pixel footprints are not filled.',
             'Finer indexing adds no observations. Data layers render at 300 dpi; PDF embeds them. Outlines and type remain vector.',
             ('Atmosphere: maximum 720 samples per raster axis, quality masks retained; radiation uses the same 100 opacity levels.'
              if product['subject'] == 'atmosphere' else
              'Temperature: 0.5° CPC centers; daily spatial means precede strict record comparisons. Counts are not spatially summed.')]
    for i, note in enumerate(notes):
        element = etree.SubElement(group, '{' + SVG + '}text', x='.8', y=str(16.1+i*.34),
                  **{'font-family': 'Atkinson Hyperlegible', 'font-size': '.20', 'fill': '#fcc553'})
        element.text = note
    tree.getroot().set('data-h3-resolution', str(resolution))
    return tree


def file_record(path, output):
    return {'path': path.relative_to(output).as_posix(), 'sha256': digest(path), 'bytes': path.stat().st_size}


def build_plate(config, product, atlas, item, baseline, scope, build, settings, rendered, env):
    output = ROOT / config['output']
    resolution, stem = product['h3_resolution'], product['stem']
    dest = output / f'h3r{resolution}'
    data_metadata = metadata(ROOT / product['snapshot'])
    source = atlas / 'maps' / scope / 'svg' / (stem + '.svg')
    legend = atlas / 'legends' / scope / 'svg' / (stem + '-legend.svg')
    receipt = build / (scope + '-plate.json')
    fingerprint = {'builder_sha256': digest(Path(__file__)), 'source_sha256': digest(source),
                   'legend_sha256': digest(legend), 'render_sha256': digest(build / 'render.json'),
                   'tiles_sha256': digest(build / 'render-inputs.json'), 'baseline': baseline,
                   'snapshot_sha256': product['snapshot_sha256'],
                   'export_contract': 'linked-png-checked-decoder-v1'}
    old = json.loads(receipt.read_text()) if receipt.exists() else None
    if old and old['fingerprint'] == fingerprint and all(
            (output / f['path']).exists() and digest(output / f['path']) == f['sha256'] for f in old['files']):
        return old
    files = []
    for kind, tree in [
        ('maps', map_tree(source, product, build, settings, rendered, item, scope, data_metadata, dest / 'maps' / scope)),
        ('legends', legend_tree(legend, product, rendered, item, baseline, data_metadata))]:
        directory = dest / kind / scope
        directory.mkdir(parents=True, exist_ok=True)
        svg = directory / (stem + ('-legend' if kind == 'legends' else '') + '.svg')
        tree.write(str(svg), xml_declaration=True, encoding='UTF-8')
        pdf = svg.with_suffix('.pdf')
        render_svg(svg, pdf, env)
        files.extend([file_record(svg, output), file_record(pdf, output)])
        if kind == 'maps':
            files.extend(file_record(p, output) for p in sorted((directory/'layers').glob(stem+'-*.png')))
            png, detail, card = svg.with_suffix('.png'), svg.with_suffix('.webp'), svg.with_name(stem+'-1280.webp')
            render_svg(svg, png, env, 44 * config['data_raster_dpi'])
            with Image.open(png) as image:
                resize_image(image, detail, baseline['detail_width'])
                bounds = item.get('japan_crop_inches') if scope == 'japan' else None
                if bounds:
                    x0,y0,x1,y1 = bounds
                    image = image.crop(tuple(round(v) for v in [x0/44*image.width, y0/19.052559*image.height,
                                                               x1/44*image.width, y1/19.052559*image.height]))
                resize_image(image, card, 1280)
            files.extend(file_record(p, output) for p in [png, detail, card])
    record = {'scope': scope, 'stem': stem, 'h3_resolution': resolution,
              'source_svg': source.relative_to(ROOT).as_posix(), 'legend_svg': legend.relative_to(ROOT).as_posix(),
              'fingerprint': fingerprint, 'files': files, 'layers': rendered['layers']}
    write_json(receipt, record)
    print(f'Exported H3r{resolution} {scope} {stem}', flush=True)
    return record


def write_review(config, records):
    output = ROOT / config['output']
    html = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>Setouchi — H3 resolution trials</title><style>body{margin:0;background:#240413;color:#fcc553;font:18px/1.5 system-ui}main{max-width:1800px;margin:auto;padding:2rem}h1,h2{font-weight:400}a{color:#fcc553}p{max-width:80ch}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}figure{margin:0;border:1px solid #8f6446;padding:.7rem}img{width:100%;height:auto}figcaption{padding:.5rem 0}small{display:block}section{margin:3rem 0}nav a{margin-right:1rem}@media(max-width:800px){.grid{grid-template-columns:1fr}main{padding:1rem}}</style><main>',
            '<h1>Setouchi · H3r3 / H3r5 / H3r8</h1>',
            '<p>Atmosphere and 2026 temperature records, World and Japan. These trials keep the original dates, sampled source centers, colors, and line weights. H3r3 is the saved website baseline. H3r5 and H3r8 show actual finer cell geometry.</p>',
            '<p>Finer cells do not add observations. Gaps can mean there was no sampled center in that cell; source-pixel footprints are not filled. At r8, source spacing and fixed stroke widths can dominate the appearance. The atmosphere sampling cap remains 720 per raster axis; temperature uses the original 0.5° grid.</p>',
            '<p>Maps and source legends are separate 44-inch sheets. Dense data layers render at 300 dpi; coastlines, solar contours, and text remain vectors. PDFs are self-contained; keep the adjacent layers folder with each SVG. Click a preview for the full-resolution PNG, or download its PDF/SVG.</p>',
            '<nav><a href="products.json">Data products</a><a href="plates.json">Plate provenance</a></nav>']
    for stem, title in [('cloud-atmosphere','Atmosphere'),('anthropocene-temperature-2026','Temperature records · 2026')]:
        for scope in ['world','japan']:
            html.append(f'<section><h2>{title} · {scope.title()}</h2><div class="grid">')
            baseline = f'../setouchi-futures-20261106/media/{scope}-{stem}'
            html.append(f'<figure><a href="{baseline}-detail.webp"><img loading="lazy" src="{baseline}-1280.webp" alt="H3r3 {title} {scope}"></a><figcaption>H3r3 · saved baseline<br><a href="{baseline}-legend.pdf">Legend &amp; sources</a></figcaption></figure>')
            for record in sorted((r for r in records if r['scope']==scope and r['stem']==stem),key=lambda r:r['h3_resolution']):
                resolution=record['h3_resolution']; base=f'h3r{resolution}/maps/{scope}/{stem}'
                legend=f'h3r{resolution}/legends/{scope}/{stem}-legend.pdf'
                count=record['layers'][0]['observed_cells']
                html.append(f'<figure><a href="{base}.png"><img loading="lazy" src="{base}-1280.webp" alt="H3r{resolution} {title} {scope}"></a><figcaption>H3r{resolution} · source-center trial<small>{count:,} '+('radiation observations' if stem=='cloud-atmosphere' else 'covered temperature cells')+f' in the shared global product</small><a href="{base}.pdf">PDF</a> · <a href="{base}.svg">SVG</a> · <a href="{legend}">Legend &amp; sources</a></figcaption></figure>')
            html.append('</div></section>')
    html.append('</main></html>')
    (output / 'index.html').write_text('\n'.join(html))


def build_plates(config, products):
    baseline = json.loads((ROOT / config['baseline']['path']).read_text())
    atlas = ROOT / baseline['atlas']
    subprocess.run(['make', '-s', 'build/setouchi-h3-tools/render-cells'], cwd=ROOT, check=True)
    env = font_environment()
    records = []
    for product in products:
        build, settings, rendered = prepare_tiles(config, product, atlas)
        item = next(m for m in baseline['maps'] if m['stem'] == product['stem'])
        for scope in ['world', 'japan']:
            records.append(build_plate(config, product, atlas, item, baseline, scope, build, settings, rendered, env))
    output = ROOT / config['output']
    write_json(output / 'plates.json', {'schema': 'cartofreako-setouchi-h3-trial-plates-v1',
        'config': config, 'plates': records, 'publication_status': 'local-only'})
    write_review(config, records)
    (output / '.gitattributes').write_text('* -text\n*.png binary\n*.webp binary\n*.pdf binary\n')
    for resolution in sorted({p['h3_resolution'] for p in products}):
        for scope in ['world', 'japan']:
            inputs=[]
            for stem in ['cloud-atmosphere','anthropocene-temperature-2026']:
                inputs.extend([output/f'h3r{resolution}/maps/{scope}/{stem}.pdf',
                               output/f'h3r{resolution}/legends/{scope}/{stem}-legend.pdf'])
            if all(p.exists() for p in inputs):
                subprocess.run(['pdfunite', *map(str,inputs), str(output/f'h3r{resolution}/{scope}.pdf')],check=True)
