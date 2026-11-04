#!/usr/bin/env python3
"""Build a 44-inch by 200-mm, four-palette proof from the approved MSP 5 SVGs."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageChops
from reportlab.pdfbase import pdfmetrics

from legend_informatics import E, ROOT, NS, XL, digest, el, font_environment, register_fonts, save, text

CONFIG = ROOT/'config/msp-speculations-20261103.json'
DELIVERY = ROOT/'output/msp-speculations-20261103'
NAME = 'msp-4-ink-profile.20261104'
WIDTH, HEIGHT, PANEL_WIDTH = 44.0, 20/2.54, 10.5
SCALE = 43.5/44
DX, DY, SHIFT = .25, (19.052559-19.052559*SCALE)/2, 4.4
CROP_WIDTH, CROP_HEIGHT = 9.85, 1.15
SAMPLES = [
    ('astro-all-sky', 'ASTRONOMY / ALL SKY', 12, (10.0, 8.5), 3.20),
    ('orbital-technosphere-global', 'ORBITAL / GLOBAL', 6, (18.25, 13.25), 4.76),
    ('orbital-technosphere-observer', 'ORBITAL / OBSERVER', 6, (31.0, 7.75), 6.32),
]


def rgb(color):
    return 'rgb('+','.join(str(int(color[i:i+2], 16)) for i in (1, 3, 5))+')'


def label(parent, x, y, value, points, color, **attrs):
    node = text(parent, x, y, value, points/72, **attrs)
    node.set('fill', color)
    return node


def bounds(node):
    """Conservative source-coordinate bounds for point marks and their labels."""
    tag = E.QName(node).localname
    if tag == 'text':
        x, y = float(node.get('x')), float(node.get('y'))
        match = re.fullmatch(r'([\d.eE+-]+)(pt|px)?', node.get('font-size'))
        if match is None:
            return None
        size = float(match[1])*(96/72 if match[2] == 'pt' else 1)
        value = ''.join(node.itertext())
        width = pdfmetrics.stringWidth(value, 'Atkinson-Regular', size)
        return x-.1, y-size*1.6-.1, x+width+.1, y+size*.6+.1
    if tag == 'circle':
        x, y = float(node.get('cx')), float(node.get('cy'))
        radius = float(node.get('r'))+.1
        return x-radius, y-radius, x+radius, y+radius
    if tag == 'path':
        # Satellite symbols contain only straight M/L/Z paths, including x marks.
        if re.search(r'[AaCcQqSsTtHhVv]', node.get('d', '')):
            return None
        numbers = list(map(float, re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?', node.get('d', ''))))
        if numbers and len(numbers)%2 == 0:
            xs, ys = numbers[::2], numbers[1::2]
            return min(xs)-.1, min(ys)-.1, max(xs)+.1, max(ys)+.1
    return None


def crop(root, origin, prefix=None):
    """Retain the existing frame at 1:1 scale; prune only off-crop objects.

    Keep all names/IDs belonging to a retained NORAD ID, including hidden name
    layers. Basemap and trajectory paths are clipped without changing vertices.
    """
    root = copy.deepcopy(root)
    x, y = origin
    root.set('width', str(CROP_WIDTH)+'in')
    root.set('height', str(CROP_HEIGHT)+'in')
    root.set('viewBox', f'{x} {y} {CROP_WIDTH} {CROP_HEIGHT}')
    root.set('overflow', 'hidden')
    if prefix is None:
        return root
    region = ((x-DX)/SCALE-SHIFT, (y-DY)/SCALE,
              (x+CROP_WIDTH-DX)/SCALE-SHIFT, (y+CROP_HEIGHT-DY)/SCALE)
    def overlaps(node):
        box = bounds(node)
        return box is None or not (box[2] < region[0] or box[0] > region[2] or box[3] < region[1] or box[1] > region[3])
    objects = root.xpath('//*[@data-norad-id]')
    retained = {n.get('data-norad-id') for n in objects if overlaps(n)}
    for node in objects:
        if node.get('data-norad-id') not in retained:
            node.getparent().remove(node)
    if not objects:
        for node in root.xpath('//*[@data-kind] | //*[@id="labels"]/*[local-name()="text"]'):
            if not overlaps(node):
                node.getparent().remove(node)
    for group in root.xpath('//*[@data-object-count]'):
        group.set('data-source-object-count', group.get('data-object-count'))
        markers = group.xpath('.//*[@data-norad-id and @data-marker-shape]')
        group.set('data-object-count', str(len(markers)))
    identifiers = {n.get('id'): prefix+'-'+n.get('id') for n in root.xpath('//*[@id]')}
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        for key, value in list(node.attrib.items()):
            if key == 'id':
                node.set(key, identifiers[value])
            elif key in ('data-locpoint-id', 'data-name-id') and value in identifiers:
                node.set(key, identifiers[value])
            elif key == '{'+XL+'}href' and value.startswith('#'):
                node.set(key, '#'+identifiers[value[1:]])
            elif 'url(#' in value:
                node.set(key, re.sub(r'url\(#([^)]*)\)', lambda m: 'url(#'+identifiers[m[1]]+')', value))
    root.set('data-crop-source-inches', ' '.join(map(str, (x, y, CROP_WIDTH, CROP_HEIGHT))))
    root.set('data-source-print-scale', '1')
    return root


def export(svg, output, env, *, width=None, dpi=None):
    command = ['inkscape', str(svg), '--export-area-page', '--export-filename='+str(output)]
    if width:
        command.append('--export-width='+str(width))
    if dpi:
        command += ['--export-dpi='+str(dpi), '--export-background-opacity=255', '--export-png-color-mode=RGB_8']
    subprocess.run(command, env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def validate_svg(root, recipes):
    assert root.get('width') == '44in' and root.get('height') == '20cm'
    panels = root.xpath('//*[@data-palette-panel]')
    assert len(panels) == 4
    for index, panel in enumerate(panels):
        assert float(panel.get('data-width-in')) == PANEL_WIDTH
        swatches = panel.xpath('.//*[@data-color-swatch]')
        assert [n.get('fill') for n in swatches] == [rgb(recipes[index][key]) for key in ('background', 'text')]
        strings = [''.join(n.itertext()) for n in panel.xpath('.//*[@data-rgb-label]')]
        assert strings == [n.get('fill') for n in swatches]
        crops = panel.xpath('.//*[local-name()="svg" and @data-crop-source-inches]')
        assert len(crops) == 3
        for sample in crops:
            assert float(sample.get('width')) == CROP_WIDTH
            assert float(sample.get('height')) == CROP_HEIGHT
            assert list(map(float, sample.get('viewBox').split()))[2:] == [CROP_WIDTH, CROP_HEIGHT]
            for group in sample.xpath('.//*[@data-font-size-pt]'):
                for node in group.xpath('./*[local-name()="text"]'):
                    assert abs(float(node.get('font-size'))*SCALE*72-float(group.get('data-font-size-pt'))) < 1e-8
    ids = [n.get('id') for n in root.xpath('//*[@id]')]
    assert len(ids) == len(set(ids)), 'Duplicate embedded SVG ID'
    id_set = set(ids)
    for node in root.iter():
        for key, value in node.attrib.items():
            if key == '{'+XL+'}href' and value.startswith('#'):
                assert value[1:] in id_set
            for target in re.findall(r'url\(#([^)]*)\)', value):
                assert target in id_set


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DELIVERY/'msp-speculation-5')
    parser.add_argument('--work', type=Path, default=ROOT/'build/msp-ink-profile-20261104')
    args = parser.parse_args()
    register_fonts()
    env = font_environment()
    config = json.loads(CONFIG.read_text())
    manifest = json.loads((DELIVERY/'manifest.json').read_text())
    assert digest(CONFIG) == manifest['recipe_sha256']
    recipes = [r for r in config['studies'] if r.get('family') == 'msp-speculation-5']
    assert len(recipes) == 4
    args.output.mkdir(parents=True, exist_ok=True)
    args.work.mkdir(parents=True, exist_ok=True)
    root = el('svg', width='44in', height='20cm', viewBox=f'0 0 {WIDTH} {HEIGHT}', role='img',
              data_product='msp-5-four-palette-ink-proof', data_date='2026-11-04')
    el('title', root).text = 'MSP 5 / four-palette ink proof / 44 inches by 20 cm'
    el('desc', root).text = ('Four 10.5-inch panels with paired Randoma11y RGB swatches and identical, '
                            'original-scale astronomy, orbital global and orbital observer crops. '
                            'Intended RGB values; printed hue is to be evaluated on the physical proof.')
    el('rect', root, width=WIDTH, height=HEIGHT, fill='white')
    definitions = el('defs', root)
    label(root, 1, .45, 'MSP 5 / FOUR-PALETTE INK PROOF', 28, '#000000', font_weight='700')
    label(root, 43, .45, '04 NOV 2026', 18, '#000000', text_anchor='end')
    label(root, 1, .77, '44 in × 200 mm  /  four 10.5 in panels  /  map crops at 1:1 print scale', 14, '#000000')
    label(root, 43, .77, 'Epson Stylus Pro 9000 / metallic glossy paper', 14, '#000000', text_anchor='end')
    inputs = []
    comparisons = []
    for i, recipe in enumerate(recipes):
        px = 1+i*PANEL_WIDTH
        left = px+.325
        panel = el('g', root, id=recipe['randoma11y_pair'], data_palette_panel=recipe['randoma11y_pair'], data_width_in=PANEL_WIDTH)
        el('rect', panel, x=px, y=1.0, width=PANEL_WIDTH, height=6.65, fill=rgb(recipe['background']))
        link = el('a', panel, id=recipe['randoma11y_pair']+'-randoma11y')
        link.set('{'+XL+'}href', recipe['source_url'])
        label(link, left, 1.36, f'{i+1:02d} / '+recipe['palette'], 22, rgb(recipe['text']), font_weight='700')
        for j, role in enumerate(('background', 'text')):
            x = left+j*5.05
            value = rgb(recipe[role])
            el('rect', link, x=x, y=1.58, width=4.8, height=.60, fill=value,
               stroke=rgb(recipe['text']), stroke_width=1/72, data_color_swatch=role)
            label(link, x, 2.46, value, 18, rgb(recipe['text']), data_rgb_label=role)
            label(link, x+4.8, 2.46, recipe[role], 12, rgb(recipe['text']), text_anchor='end')
        label(link, left, 2.77, recipe['source_url'].removeprefix('https://'), 12, rgb(recipe['text']), text_decoration='underline')
        for subject, title, size, origin, top in SAMPLES:
            record = next(r for r in manifest['records'] if r['study'] == recipe['id'] and r['subject'] == subject and r['kind'] == 'map')
            archive = next(f for f in record['outputs'] if f['path'].endswith('.svg.gz'))
            source = DELIVERY/archive['path']
            assert digest(source) == archive['sha256']
            data = gzip.decompress(source.read_bytes())
            assert hashlib.sha256(data).hexdigest() == record['svg_sha256']
            original = E.fromstring(data)
            prefix = recipe['randoma11y_pair']+'-'+subject
            sample = crop(original, origin, prefix)
            # SVG viewport units match its viewBox dimensions: no fit-to-panel scale.
            sample.set('x', str(left)); sample.set('y', str(top))
            sample.set('width', str(CROP_WIDTH)); sample.set('height', str(CROP_HEIGHT))
            label(panel, left, top-.13, title, 12, rgb(recipe['text']), font_weight='700')
            label(panel, left+CROP_WIDTH, top-.13, f'{size} pt labels / 1:1', 12, rgb(recipe['text']), text_anchor='end')
            # Explicit parent-coordinate clipping also works in Inkscape's PDF
            # exporter, which does not consistently clip nested SVG overflow.
            clip_id = prefix+'-crop-window'
            clip = el('clipPath', definitions, id=clip_id, clipPathUnits='userSpaceOnUse')
            el('rect', clip, x=left, y=top, width=CROP_WIDTH, height=CROP_HEIGHT)
            window = el('g', panel, id=prefix+'-sample', clip_path=f'url(#{clip_id})',
                        data_sample_subject=subject, data_print_scale=1)
            window.append(sample)
            el('rect', panel, x=left, y=top, width=CROP_WIDTH, height=CROP_HEIGHT,
               fill='none', stroke=rgb(recipe['text']), stroke_opacity=.55, stroke_width=.5/72)
            inputs.append({'palette': recipe['randoma11y_pair'], 'subject': subject,
                           'path': str(source.relative_to(ROOT)), 'sha256': archive['sha256'],
                           'source_svg_sha256': record['svg_sha256'], 'crop_inches': [*origin, CROP_WIDTH, CROP_HEIGHT],
                           'sample_scale': 1, 'label_size_pt': size})
            if i == 0:
                # Compare pruned payload against an unmodified source crop at 300 dpi.
                baseline = args.work/(subject+'-baseline.svg')
                candidate = args.work/(subject+'-crop.svg')
                save(crop(original, origin), baseline)
                check = copy.deepcopy(sample)
                check.attrib.pop('x'); check.attrib.pop('y')
                check.set('width', str(CROP_WIDTH)+'in'); check.set('height', str(CROP_HEIGHT)+'in')
                save(check, candidate)
                for path in (baseline, candidate):
                    export(path, path.with_suffix('.png'), env, dpi=300)
                with Image.open(baseline.with_suffix('.png')) as a, Image.open(candidate.with_suffix('.png')) as b:
                    assert a.size == b.size == (2955, 345)
                    assert ImageChops.difference(a.convert('RGB'), b.convert('RGB')).getbbox() is None, subject+' crop changed the rendered source'
                comparisons.append({'subject': subject, 'dpi': 300, 'pixel_equal_to_unmodified_crop': True})
            print('Composed', recipe['randoma11y_pair'], subject, flush=True)
    label(root, 1, 7.80, 'Print at 100% / no fit-to-page. Low cyan + light magenta reported; grays reportedly shift violet. Compare the physical proof.', 10, '#000000')
    label(root, 43, 7.80, NAME, 10, '#000000', text_anchor='end')
    receipt = {'schema': 'cartofreako-msp-ink-proof-v1', 'date': '2026-11-04', 'source_family': 'msp-speculation-5',
               'filename': NAME, 'sheet_inches': [WIDTH, HEIGHT], 'sheet_mm': [WIDTH*25.4, 200],
               'panel_width_inches': PANEL_WIDTH, 'side_margins_inches': [1, 1], 'png_dpi': 300,
               'builder_sha256': digest(Path(__file__)), 'recipe_sha256': digest(CONFIG),
               'source_manifest_sha256': digest(DELIVERY/'manifest.json'),
               'font_sha256': digest(ROOT/'assets/fonts/atkinson-hyperlegible/provenance.json'),
               'palettes': [{'name': r['palette'], 'background': rgb(r['background']), 'foreground': rgb(r['text']),
                             'url': r['source_url']} for r in recipes], 'inputs': inputs, 'crop_checks': comparisons}
    el('metadata', root, id='ink-proof-provenance').text = json.dumps(receipt, sort_keys=True)
    validate_svg(root, recipes)
    svg = args.output/(NAME+'.svg'); pdf = svg.with_suffix('.pdf'); png = svg.with_suffix('.png')
    save(root, svg)
    export(svg, pdf, env)
    export(svg, png, env, dpi=300)
    preview = args.work/(NAME+'-preview.png')
    with Image.open(png) as im:
        assert im.size == (13200, 2362)
        rendered = im.convert('RGB')
        for i, recipe in enumerate(recipes):
            for j, role in enumerate(('background', 'text')):
                center = (round((1+i*PANEL_WIDTH+.325+j*5.05+2.4)*300), round(1.88*300))
                expected = tuple(int(recipe[role][n:n+2], 16) for n in (1, 3, 5))
                assert rendered.getpixel(center) == expected, 'Rendered swatch obscured or recolored'
        im.thumbnail((3840, 3840), Image.Resampling.LANCZOS)
        im.save(preview)
    info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
    width, height = map(float, re.search(r'Page size:\s+([\d.]+) x ([\d.]+)', info).groups())
    assert abs(width-3168)<.01 and abs(height-200/25.4*72)<.01
    links = subprocess.check_output(['pdfinfo', '-url', str(pdf)], text=True)
    assert all(r['source_url'] in links for r in recipes), 'Missing clickable Randoma11y PDF links'
    receipt['validation'] = {'svg_dimensions_and_panels': True, 'rgb_swatch_labels_match': True,
                             'all_eight_rendered_swatch_centers_match_rgb': True,
                             'embedded_ids_unique_and_references_resolve': True, 'png_dimensions': [13200, 2362],
                             'pdf_page_points': [width, height], 'randoma11y_pdf_links': 4}
    receipt['outputs'] = [{'path': p.name, 'sha256': digest(p), 'bytes': p.stat().st_size} for p in (svg, png, pdf)]
    svg.with_suffix('.provenance.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('Built and verified', svg, png, pdf, sep='\n', flush=True)


if __name__ == '__main__':
    main()
