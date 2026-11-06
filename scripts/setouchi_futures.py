"""Reproducible web assets and native WordPress blocks for the Setouchi page."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
from html import escape
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.request import urlopen

from bs4 import BeautifulSoup
from lxml import etree
from PIL import Image

from legend_informatics import ROOT, digest, font_environment
from setouchi_radiation import prepare_cells, apply_opacity, update_legend as radiation_legend

SCHEMA = "cartofreako-setouchi-futures-prepared-v1"
SVG = "http://www.w3.org/2000/svg"
DEFAULT_MANIFEST = ROOT / "config/setouchi-futures-20261106.json"


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def load_config(path=DEFAULT_MANIFEST):
    config = json.loads(Path(path).read_text())
    if config.get("schema") != "cartofreako-setouchi-futures-v1":
        raise ValueError("Unsupported futures manifest")
    if len({m['stem'] for m in config['maps']}) != len(config['maps']):
        raise ValueError("Duplicate map stem")
    if not re.fullmatch(r"[a-z][a-z0-9-]+", config['anchor']):
        raise ValueError("Invalid gallery anchor")
    return config


def css_values(element):
    return dict(part.split(":", 1) for part in element.get('style', '').split(';') if ':' in part)


def set_style(element, **values):
    style = {key.strip(): val.strip() for key, val in css_values(element).items()}
    style.update({key.replace('_', '-'): str(value) for key, value in values.items()})
    element.set('style', ';'.join(f'{key}:{value}' for key, value in style.items()))


def background_variation(tree, color):
    """Repaint the sheet and nested background rectangles without touching data."""
    original = tree.getroot().get('data-sheet-background')
    if not original or not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        raise ValueError('A declared source background and a six-digit target color are required')
    count = 0
    for element in tree.iter('{' + SVG + '}rect'):
        style = {key.strip(): value.strip() for key, value in css_values(element).items()}
        if style.get('fill', element.get('fill')) == original:
            element.set('fill', color)
            set_style(element, fill=color)
            count += 1
    if not count:
        raise ValueError('No source background rectangles found')
    tree.getroot().set('data-sheet-background', color)
    return {'from': original, 'to': color, 'rectangles': count, 'geometry_changed': False}


def land_outline_overlay(tree, settings):
    """Draw existing coastlines last, preserving every viewport transform and clip."""
    color, opacity = settings['color'], settings['opacity']
    width = settings.get('width_pt')
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', color) or not 0 <= opacity <= 1:
        raise ValueError('Invalid land outline paint')
    if width is not None and (not math.isfinite(width) or width <= 0):
        raise ValueError('Land outline width must be positive and finite')
    frames = tree.xpath('//*[@id="st2-image-frame"]')
    coastlines = tree.xpath('//*[@id="terrestrial-coastline"]')
    if len(frames) != 1 or len(coastlines) != 1:
        raise ValueError('Expected one image frame and coastline group')
    frame, coastline = frames[0], coastlines[0]
    source = coastline.getparent()
    definitions = source.getparent()
    if etree.QName(definitions).localname != 'defs':
        raise ValueError('Expected coastlines in the shared source definition')
    href = '{http://www.w3.org/1999/xlink}href'
    uses = [n for n in frame.iter('{' + SVG + '}use')
            if n.get(href, n.get('href')) == '#' + source.get('id')]
    if not uses:
        raise ValueError('No placed views of the source cartography')
    overlay = etree.Element('{' + SVG + '}g', id='web-land-outlines')
    overlay.set('data-layer-order', 'top')

    def view_scale(node):
        # These plate viewports use translation and uniform scaling. Nominal
        # point weights exclude the common outer Setouchi image-frame scale.
        scale = 1.0
        while node is not frame:
            transform = node.get('transform', '')
            pattern = r'(translate|scale)\s*\(([^)]*)\)'
            if re.sub(pattern, '', transform).strip(' ,\t\n'):
                raise ValueError('Unsupported outline viewport transform')
            for kind, args in re.findall(pattern, transform):
                if kind == 'scale':
                    values = [float(v) for v in re.split(r'[\s,]+', args.strip())]
                    if len(values) not in (1, 2) or not math.isfinite(values[0]) or values[0] <= 0:
                        raise ValueError('Invalid outline viewport scale')
                    if len(values) == 2 and not math.isclose(values[0], values[1]):
                        raise ValueError('Outline point width requires uniform scaling')
                    scale *= values[0]
            node = node.getparent()
            if node is None:
                raise ValueError('Outline placement is outside the image frame')
        return scale

    scales = {view_scale(use) for use in uses}
    if len(scales) != 1:
        raise ValueError('Shared coastline views must have the same scale')

    def wrapper_for(node):
        ancestors = []
        parent = node.getparent()
        while parent is not frame:
            if parent is None or etree.QName(parent).localname == 'defs':
                raise ValueError('Outline placement is outside the rendered image frame')
            ancestors.append(parent)
            parent = parent.getparent()
        target = overlay
        for ancestor in reversed(ancestors):
            # Keep clipping, transforms, and presentation, without duplicating IDs.
            attrs = {key: value for key, value in ancestor.attrib.items() if key != 'id'}
            target = etree.SubElement(target, ancestor.tag, attrs)
        return target

    for use in uses:
        placed = deepcopy(use)
        placed.attrib.pop('id', None)
        placed.set(href if href in placed.attrib else 'href', '#terrestrial-coastline')
        wrapper_for(use).append(placed)
    # Remove coastlines from the data composition; the new overlay references
    # their original paths from a separate definition, avoiding a double stroke.
    definitions.append(coastline)
    groups = [(coastline, scales.pop())]
    inset = tree.xpath('//*[@id="terrestrial-coastline-antarctic-inset"]')
    for group in inset:
        scale = view_scale(group)
        target = wrapper_for(group)
        target.append(group)
        groups.append((group, scale))
    paths = 0
    for group, scale in groups:
        for path in group.iter('{' + SVG + '}path'):
            paint = {'stroke': color, 'stroke_opacity': opacity}
            if width is not None:
                paint['stroke_width'] = f'{width / 72 / scale:.12g}'
            set_style(path, **paint)
            paths += 1
    frame.append(overlay)
    return {'layer': 'web-land-outlines', 'position': 'top', 'color': color, 'opacity': opacity,
            'paths': paths, 'placed_views': len(uses), 'antarctica_inset': bool(inset),
            'geometry_changed': False, 'line_widths_changed': width is not None,
            'nominal_width_pt': width, 'width_reference': 'before Setouchi image-frame scaling'}


def fiber_variation(tree, config, legend=False):
    """Change display paint only; all path geometry, dash classes, and data stay put."""
    color = config['fiber_ocean_color']
    if legend:
        changes = 0
        for element in tree.iter():
            if etree.QName(element).localname == 'line' and element.get('stroke') in ('#000', '#000000'):
                element.set('stroke', color)
                element.set('stroke-opacity', str(config['fiber_ocean_opacity']))
                changes += 1
            if element.text:
                element.text = element.text.replace('Submarine cables: Black.', 'Submarine cables: Amber (web edition).')
        if changes != 3:
            raise ValueError(f'Expected three submarine legend swatches; found {changes}')
    else:
        groups = tree.xpath('//*[@id="network-fiber"]')
        if len(groups) != 1:
            raise ValueError('Expected one submarine fiber group')
        changes = 0
        for element in groups[0].iter():
            if etree.QName(element).localname in ('path', 'polyline', 'line'):
                set_style(element, stroke=color, stroke_opacity=config['fiber_ocean_opacity'])
                changes += 1
        if changes != 767:
            raise ValueError(f'Pinned fiber source changed: expected 767 routes, found {changes}')
    tree.getroot().set('data-web-fiber-variation', f'{color}; opacity={config["fiber_ocean_opacity"]}')
    return changes


def record_asset(output, path, key, title, alt='', caption=''):
    record = {'key': key, 'path': path.relative_to(output).as_posix(), 'sha256': digest(path),
              'bytes': path.stat().st_size, 'title': title, 'alt': alt, 'caption': caption}
    if path.suffix.lower() in ('.png', '.webp', '.jpg'):
        with Image.open(path) as image:
            record.update(width=image.width, height=image.height)
    return record


def render_svg(source, target, env, width=None):
    args = ['inkscape', str(source), '--export-area-page', '--export-filename=' + str(target)]
    if width:
        args.append('--export-width=' + str(width))
    result = subprocess.run(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode:
        raise RuntimeError(f'Render failed: {source.name}: {result.stderr[-1200:]}')


def resize_image(image, path, width):
    target = image.copy()
    target.thumbnail((width, width * 4), Image.Resampling.LANCZOS)
    target.convert('RGB').save(path, 'WEBP', quality=94, method=6)


def build_map(config, output, build, item, scope, env, bibliography, radiation=None):
    stem = item['stem']
    ident = f'{scope}-{stem}'
    atlas = ROOT / config['atlas']
    source = atlas / 'maps' / scope / 'svg' / (stem + '.svg')
    legend = atlas / 'legends' / scope / 'svg' / (stem + '-legend.svg')
    fingerprint = {'source_sha256': digest(source), 'legend_sha256': digest(legend),
                   'settings': item, 'background': config['background'],
                   'fiber': [config['fiber_ocean_color'], config['fiber_ocean_opacity']],
                   'widths': [config['detail_width'], config['card_widths']],
                   'builder_sha256': digest(Path(__file__)),
                   'bibliography_sha256': digest(atlas / 'plate-source-bibliography.json')}
    if radiation:
        fingerprint['radiation_inputs'] = radiation['fingerprint']
    receipt_path = build / (ident + '.json')
    if receipt_path.exists():
        old = json.loads(receipt_path.read_text())
        if old['fingerprint'] == fingerprint and all((output / a['path']).exists() and
                digest(output / a['path']) == a['sha256'] for a in old['assets']):
            return old
    working = source
    working_legend = legend
    counts = None
    background = None
    outlines = None
    radiation_result = None
    if item.get('background') or item.get('land_outline') or radiation:
        tree = etree.parse(str(working))
        if item.get('background'):
            background = background_variation(tree, item['background'])
        if item.get('land_outline'):
            outlines = land_outline_overlay(tree, item['land_outline'])
        if radiation:
            radiation_result = apply_opacity(tree, radiation['data'], item['radiation_opacity'])
        working = build / (ident + '.svg')
        tree.write(str(working), xml_declaration=True, encoding='UTF-8')
    if stem == 'network-fiber':
        tree = etree.parse(str(working))
        count = fiber_variation(tree, config)
        working = build / (ident + '.svg')
        tree.write(str(working), xml_declaration=True, encoding='UTF-8')
        tree = etree.parse(str(legend))
        swatches = fiber_variation(tree, config, legend=True)
        working_legend = build / (ident + '-legend.svg')
        tree.write(str(working_legend), xml_declaration=True, encoding='UTF-8')
        counts = {'route_paths': count, 'legend_swatches': swatches,
                  'color': config['fiber_ocean_color'], 'opacity': config['fiber_ocean_opacity'],
                  'geometry_changed': False}
    if radiation:
        tree = etree.parse(str(working_legend))
        radiation_legend(tree, item['radiation_opacity'], item.get('background', config['background']))
        working_legend = build / (ident + '-legend.svg')
        tree.write(str(working_legend), xml_declaration=True, encoding='UTF-8')
    raster = build / (ident + '.png')
    render_svg(working, raster, env, config['detail_width'])
    title = f'{item["title"]} · {"World" if scope == "world" else "Japan / Setouchi"}'
    alt, caption = item[scope + '_alt'], item[scope + '_caption']
    assets = []
    with Image.open(raster) as master:
        path = output / 'media' / (ident + '-detail.webp')
        resize_image(master, path, config['detail_width'])
        assets.append(record_asset(output, path, ident + '-detail', title, alt, caption))
        bounds = item.get('japan_crop_inches') if scope == 'japan' else None
        if bounds:
            x0, y0, x1, y1 = bounds
            if not (0 <= x0 < x1 <= 44 and 0 <= y0 < y1 <= 19.052559):
                raise ValueError('Crop lies outside sheet')
            card = master.crop((round(x0 / 44 * master.width), round(y0 / 19.052559 * master.height),
                                round(x1 / 44 * master.width), round(y1 / 19.052559 * master.height)))
        else:
            card = master.copy()
        for width in config['card_widths']:
            path = output / 'media' / f'{ident}-{width}.webp'
            resize_image(card, path, width)
            assets.append(record_asset(output, path, f'{ident}-{width}', title, alt, caption))
    path = output / 'media' / (ident + '-legend.pdf')
    render_svg(working_legend, path, env)
    assets.append(record_asset(output, path, ident + '-legend', title + ' · Legend and sources'))
    entry = deepcopy(next(e for e in bibliography['entries'] if e['stem'] == stem))
    source_ids = list(dict.fromkeys(entry['source_ids'] + (entry.get('japan_source_ids', []) if scope == 'japan' else [])))
    # Keep the small, human-readable source record; full input inventories remain in the atlas ledger.
    provenance = {
        'id': ident, 'source_svg': source.relative_to(ROOT).as_posix(),
        'source_sha256': fingerprint['source_sha256'],
        'legend_svg': legend.relative_to(ROOT).as_posix(),
        'legend_sha256': fingerprint['legend_sha256'],
        'thumbnail_crop_inches': bounds, 'fiber_variation': counts,
        'period_and_units': entry['period_and_units'], 'interpretation': entry['interpretation'],
        'japan_context': entry['japan'] if scope == 'japan' else None,
        'sources': [{k: v for k, v in bibliography['sources'][s].items() if k != 'inputs'} for s in source_ids],
        'projection': 'Setouchi modified AuthaGraph; existing observer geometry retained for sky subjects',
        'atlas_presentation': entry['presentation'], 'world_framing': entry.get('world_presentation') if scope == 'world' else None,
    }
    if counts:
        provenance['interpretation'] = provenance['interpretation'].replace('black submarine routes: 0.5 pt, 75% opacity',
            'amber submarine routes at full opacity in this web edition; source widths retained')
    if background:
        provenance['web_background_variation'] = background
    if outlines:
        provenance['web_land_outline_overlay'] = outlines
    if radiation_result:
        provenance['web_radiation_opacity'] = {**radiation_result, 'inputs': radiation['inputs']}
        provenance['interpretation'] += (
            f' Web edition: shortwave cell opacity uses {radiation_result["bands"]} equally spaced levels '
            'from transparent at 0 to opaque at 400 W/m², on the same scale in both views.')
    result = {'fingerprint': fingerprint, 'assets': assets, 'provenance': provenance}
    write_json(receipt_path, result)
    print('Prepared', ident, flush=True)
    return result


def build_hamonshu(config, output, item, local_root, allow_download):
    ident, book = item['id'], item['book']
    relative = f'review/hamonshu-v2-book{book}/images/{ident}.jpg'
    url = 'https://situationshipin.space/' + relative
    original = output / 'media' / (ident + '-detail.jpg')
    local = local_root / relative
    if original.exists() and digest(original) == item['sha256']:
        pass
    elif local.exists() and digest(local) == item['sha256']:
        shutil.copyfile(local, original)
    elif allow_download:
        with urlopen(url, timeout=30) as response:
            data = response.read()
        if sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Hamonshū source checksum changed: ' + ident)
        original.write_bytes(data)
    else:
        raise ValueError('Missing verified crop ' + ident + '; set --hamonshu-root or --download-sources')
    assets = [record_asset(output, original, ident + '-detail', item['title'], item['alt'], item['caption'])]
    with Image.open(original) as image:
        for width in config['card_widths']:
            path = output / 'media' / f'{ident}-{width}.webp'
            resize_image(image, path, width)
            assets.append(record_asset(output, path, f'{ident}-{width}', item['title'], item['alt'], item['caption']))
    return {'assets': assets, 'provenance': {'id': ident, 'source_url': url, 'sha256': item['sha256'],
            'review_url': f'https://situationshipin.space/review/hamonshu-v2-book{book}/',
            'credit': 'Mori Yūzan, Hamonshū (1903). Segmented for the Izzi review collection.'}}


def block(name, html, attrs=None):
    suffix = ' ' + json.dumps(attrs, ensure_ascii=False, separators=(',', ':')) if attrs else ''
    return f'<!-- wp:{name}{suffix} -->\n{html}\n<!-- /wp:{name} -->\n'


def gallery_blocks(prepared, media=None, local=False):
    """Native core blocks inherit the installed WordPress theme's typography."""
    config = prepared['config']
    assets = {a['key']: a for a in prepared['assets']}

    def asset_url(key):
        if media is not None:
            return media[key]['url']
        return assets[key]['path'] if local else '{{asset:' + key + '}}'

    def figure(ident, title, caption, alt, legend=None, review=None, background=None):
        key = ident + '-1280'
        image = assets[key]
        ratio = '4/3' if review else '44/19.052559'
        ground = '#f4efe4' if review else (background or config['background'])
        attrs = {'sizeSlug': 'full', 'linkDestination': 'custom', 'aspectRatio': ratio, 'scale': 'contain'}
        cls = ''
        if media is not None:
            attrs['id'] = media[key]['id']
            cls = f' class="wp-image-{attrs["id"]}"'
        # WordPress generates responsive sizes for media IDs. Local previews use the prepared derivatives.
        responsive = (f' srcset="{escape(asset_url(ident + "-640"), quote=True)} 640w, '
                      f'{escape(asset_url(key), quote=True)} 1280w" sizes="(max-width: 781px) 100vw, 50vw"') if local else ''
        credit = f'<strong>{escape(title)}</strong><br>{escape(caption)}'
        if legend:
            credit += f'<br><a href="{escape(asset_url(legend), quote=True)}">Legend &amp; sources</a>'
        if review:
            credit += f'<br><a href="{escape(review, quote=True)}">Book review</a>'
        html = (f'<figure class="wp-block-image size-full"><a href="{escape(asset_url(ident + "-detail"), quote=True)}">'
                f'<img src="{escape(asset_url(key), quote=True)}" alt="{escape(alt, quote=True)}"'
                f' width="{image["width"]}" height="{image["height"]}" loading="lazy" decoding="async"'
                f' style="aspect-ratio:{ratio};object-fit:contain;background:{ground}"{cls}{responsive}></a>'
                f'<figcaption class="wp-element-caption">{credit}</figcaption></figure>')
        return block('image', html, attrs)

    def row(figures):
        columns = ''.join(block('column', '<div class="wp-block-column">' + fig + '</div>') for fig in figures)
        return block('columns', '<div class="wp-block-columns">' + columns + '</div>')

    body = ''
    for scope, title in [('world', 'World'), ('japan', 'Japan / Setouchi')]:
        body += block('heading', f'<h3 class="wp-block-heading">{title}</h3>', {'level': 3})
        figures = [figure(scope + '-' + item['stem'], item['title'], item[scope + '_caption'], item[scope + '_alt'],
                          legend=scope + '-' + item['stem'] + '-legend', background=item.get('background'))
                   for item in config['maps']]
        # Four geographic images in two native two-column rows; a panorama gives the observer sky room.
        for start in range(0, len(figures), 2):
            subset = figures[start:start + 2]
            body += row(subset) if len(subset) == 2 else subset[0]
    body += block('paragraph', '<p>Cartofreako · Benjamin De Kosnik. Geographic plates use the modified Setouchi AuthaGraph layout. '
                  'Observer plates retain their own sky geometry and dated reference points. Data credits accompany each legend.</p>')
    body += block('heading', '<h3 class="wp-block-heading">Hamonshū Revisited</h3>', {'level': 3})
    body += row([figure(item['id'], item['title'], item['caption'], item['alt'],
                        review=f'https://situationshipin.space/review/hamonshu-v2-book{item["book"]}/') for item in config['hamonshu']])
    body += block('paragraph', '<p>Mori Yūzan, <em>Hamonshū</em> (1903). Three water-pattern details, segmented for the Izzi review collection.</p>')
    return block('group', f'<div id="{config["anchor"]}" class="wp-block-group setouchi-futures-gallery">\n{body}</div>',
                 {'anchor': config['anchor'], 'className': 'setouchi-futures-gallery', 'layout': {'type': 'default'}})


PREVIEW_CSS = """
* { box-sizing: border-box; }
body { margin: 0; color: #252525; background: #fff; font: 18px/1.6 Georgia, serif; }
main { max-width: 1100px; padding: 28px 24px 72px; margin: auto; }
h1, h2, h3 { line-height: 1.2; font-weight: 400; }
h1 { font-size: 2rem; } h2 { font-size: 1.65rem; margin-top: 3rem; }
h3 { font-size: 1.4rem; margin: 2.5rem 0 1.2rem; }
a { color: inherit; text-underline-offset: .16em; }
.wp-block-columns { display: flex; gap: 26px; margin: 0 0 30px; align-items: flex-start; }
.wp-block-column { flex: 1; min-width: 0; }
.wp-block-image { margin: 0 0 30px; }
.wp-block-column .wp-block-image { margin: 0; }
.wp-block-image img { display: block; max-width: 100%; height: auto; width: 100%; }
.wp-element-caption { font-size: .85rem; line-height: 1.5; margin-top: 12px; }
.wp-element-caption a { display: inline-block; padding: 4px 0; }
.preview-note { font: 14px/1.5 system-ui, sans-serif; padding: 16px; border: 1px solid #ddd; background: #fafafa; }
.preview-note p { margin: 0 0 8px; } .preview-note p:last-child { margin-bottom: 0; }
:focus-visible { outline: 3px solid #225caa; outline-offset: 4px; }
@media(max-width:781px) { .wp-block-columns { display: block; margin-bottom: 0; } .wp-block-column { margin-bottom: 30px; } main { padding: 20px 16px 48px; } }
"""


def write_preview(prepared, output):
    fragment = gallery_blocks(prepared, local=True)
    html = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Cartofreako × Setouchi · gallery preview</title><style>' + PREVIEW_CSS + '</style></head><body><main>'
            '<h1>Cartofreako × Setouchi</h1><aside class="preview-note"><p><strong>Local insertion preview</strong></p>'
            '<p>Place these galleries after the existing three lists and before “Two atlases, one shared table.”</p>'
            '<p>Preview type is a temporary reading style. Published blocks inherit the WordPress theme; '
            'the Star-X reference page’s exact styling is awaiting access.</p>'
            '<p><a href="README.md">Production notes</a> · <a href="outreach/brief.pdf">Illustrated brief</a></p></aside>'
            + fragment + '<hr><h2>Two atlases, one shared table</h2>'
            '<p class="preview-note">The existing page continues here. Its current text and lists are preserved by the publisher.</p>'
            '</main></body></html>')
    (output / 'index.html').write_text(html)
    (output / 'gallery-blocks.html').write_text(gallery_blocks(prepared))


def build_brief(prepared, output):
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.utils import ImageReader
    from legend_informatics import register_fonts
    register_fonts()
    directory = output / 'outreach'
    directory.mkdir(exist_ok=True)
    canvas = Canvas(str(directory / 'brief.pdf'), pagesize=(595.276, 841.89), invariant=1)
    canvas.setTitle('Cartofreako × Setouchi — an invitation to exchange ideas')
    canvas.setAuthor('Benjamin De Kosnik')
    canvas.setFillColor(HexColor('#252525'))
    canvas.setFont('Atkinson-Bold', 22)
    canvas.drawString(35, 795, 'Cartofreako × Setouchi')
    canvas.setFont('Atkinson-Regular', 10)
    for i, line in enumerate(['A proposed public atlas studio · Benjamin De Kosnik',
                              'Maps, drawing, folding, and printmaking as ways to explore possible futures.',
                              'Selected studies for a conversation with Hajime Narukawa · 6 November 2026']):
        canvas.drawString(35, 775 - i * 15, line)
    lookup = {a['key']: a for a in prepared['assets']}

    def picture(key, x, y, w, h, caption):
        canvas.drawImage(ImageReader(str(output / lookup[key]['path'])), x, y, w, h,
                         preserveAspectRatio=True, anchor='c', mask='auto')
        canvas.setFont('Atkinson-Regular', 9)
        canvas.drawString(x, y - 14, caption)

    picture('world-water-1280', 35, 584, 255, 137, 'Water · World')
    picture('japan-water-1280', 305, 584, 255, 137, 'Water · Japan / Setouchi')
    picture('world-orbital-technosphere-observer-1280', 35, 338, 525, 209,
            'Orbital sky · San Francisco reference · 3 November 2026, 17:10 UTC')
    for item, x in zip(prepared['config']['hamonshu'], [35, 215, 395]):
        picture(item['id'] + '-1280', x, 178, 165, 121, item['title'])
    canvas.setFont('Atkinson-Regular', 9)
    lines = ['Mori Yūzan, Hamonshū (1903). Details segmented for the Izzi review collection.',
             'Geographic artwork: Cartofreako’s modified AuthaGraph layout; projection by Hajime Narukawa.',
             'Water: Natural Earth. Orbital sources: see the companion atlas legend.',
             'The studio and any participation remain proposed. A short exchange would be welcome.']
    for i, line in enumerate(lines):
        canvas.drawString(35, 132 - i * 14, line)
    canvas.setFont('Atkinson-Regular', 10)
    url = prepared['config']['page_url']
    canvas.drawString(35, 55, url)
    canvas.linkURL(url, (35, 51, 560, 65), relative=0)
    canvas.showPage()
    canvas.save()
    (directory / 'first-contact.md').write_text(
        '# Unsent introduction to Hajime Narukawa\n\n'
        'Suggested route: https://narukawa-lab.jp/contact/\n\n'
        '**Subject:** Cartofreako × Setouchi — AuthaGraph, print, and a public atlas studio\n\n'
        'Dear Professor Narukawa,\n\n'
        'I am Benjamin De Kosnik, an artist and engineer developing Cartofreako, an atlas project connecting maps, networks, and printmaking. '
        'For a proposed public atlas studio at Setouchi 2028, I am pairing World and Japan views of water, atmosphere, temperature records, fiber networks, '
        'and satellites with activities in drawing, folding, and printing.\n\n'
        'Your work with AuthaGraph, especially the connection between geometry and making in the AuthaGraph Stamp project, '
        'is closely related to the questions I hope visitors will explore. I would value your perspective on using map projection as a tool for a public workshop.\n\n'
        'Would you be open to a brief conversation or a short exchange by email? The project overview is here:\n' + url + '\n\n'
        'Best wishes,\nBenjamin De Kosnik\n\n'
        '---\nPrepared locally; not sent. The accompanying brief is one A4 page. '
        'Use the updated page link after publication; the live page has not received these new galleries yet.\n')


def prepare(manifest=DEFAULT_MANIFEST, output=None, workers=2, hamonshu_root=None, download=False):
    config = load_config(manifest)
    output = Path(output or ROOT / config['output']).resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'media').mkdir(exist_ok=True)
    build = ROOT / 'build/setouchi-futures' / sha256(str(output).encode()).hexdigest()[:12]
    build.mkdir(parents=True, exist_ok=True)
    bibliography = json.loads((ROOT / config['atlas'] / 'plate-source-bibliography.json').read_text())
    env = font_environment()
    radiation = {item['stem']: prepare_cells(item['radiation_opacity'], build)
                 for item in config['maps'] if item.get('radiation_opacity')}
    tasks = [(item, scope) for scope in ['world', 'japan'] for item in config['maps']]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(build_map, config, output, build, item, scope, env, bibliography,
                                   radiation.get(item['stem'])) for item, scope in tasks]
        maps = [future.result() for future in futures]
    crops = [build_hamonshu(config, output, item, Path(hamonshu_root or ROOT.parent / 'situationshipin.space'), download)
             for item in config['hamonshu']]
    prepared = {'schema': SCHEMA, 'config': config, 'config_sha256': digest(Path(manifest)),
                'assets': [a for result in maps + crops for a in result['assets']],
                'provenance': [result['provenance'] for result in maps + crops],
                'theme_status': 'inherited-on-WordPress; live reference not yet verified',
                'publication_status': 'local-only'}
    write_json(output / 'prepared.json', prepared)
    write_preview(prepared, output)
    build_brief(prepared, output)
    (output / '.gitignore').write_text('private/\npublish-plan.json\npublish-receipt.json\n*.local.json\n')
    return output, prepared
