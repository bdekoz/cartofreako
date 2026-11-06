"""Build the selected website/print edition from checksum-pinned H3 plates."""
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import shutil
import subprocess

from lxml import etree
from PIL import Image

from setouchi_futures import (ROOT, SVG, digest, record_asset, render_svg,
                              resize_image, write_json)


def load_selection(item, scope):
    selection = item['prepared_plate']
    manifest = ROOT / selection['manifest']
    if digest(manifest) != selection['manifest_sha256']:
        raise ValueError('Selected plate manifest changed')
    records = json.loads(manifest.read_text())['plates']
    matches = [r for r in records if r['h3_resolution'] == selection['h3_resolution']
               and r['scope'] == scope and r['stem'] == item['stem']]
    if len(matches) != 1:
        raise ValueError('Selected plate resolution/subject/view is not available')
    record = matches[0]
    radiation = item.get('radiation_opacity')
    if radiation:
        if radiation['snapshot_sha256'] != record['fingerprint']['snapshot_sha256']:
            raise ValueError('Selected radiation product differs from the settings')
        profile = ROOT / radiation['profile']
        if digest(profile) != radiation['profile_sha256']:
            raise ValueError('Selected radiation profile changed')
        if json.loads(profile.read_text())['aggregation']['h3_resolution'] != selection['h3_resolution']:
            raise ValueError('Selected radiation profile uses another H3 resolution')
    source_settings = next(m for m in record['fingerprint']['baseline']['maps'] if m['stem'] == item['stem'])
    for key in ('background', 'land_outline'):
        if item.get(key) != source_settings.get(key):
            raise ValueError('Selected plate must be rebuilt for changed ' + key)
    for key in ('bands', 'scale_min', 'scale_max'):
        if item.get('radiation_opacity', {}).get(key) != source_settings.get('radiation_opacity', {}).get(key):
            raise ValueError('Selected plate must be rebuilt for changed radiation scale')
    bundle = manifest.parent
    for file in record['files']:
        path = (bundle / file['path']).resolve()
        if not path.is_relative_to(bundle.resolve()) or digest(path) != file['sha256']:
            raise ValueError('Selected plate artifact changed: ' + file['path'])
    resolution, stem = selection['h3_resolution'], item['stem']
    source = bundle / f'h3r{resolution}/maps/{scope}/{stem}.svg'
    tree = etree.parse(str(source))
    if tree.getroot().get('data-h3-resolution') != str(resolution):
        raise ValueError('Selected SVG does not contain the requested H3 resolution')
    if tree.getroot().get('data-trial-product-sha256') != record['fingerprint']['snapshot_sha256']:
        raise ValueError('Selected SVG product differs from the pinned record')
    return bundle, record


def file_record(path, output):
    return {'path': path.relative_to(output).as_posix(), 'sha256': digest(path),
            'bytes': path.stat().st_size}


def build_selected_plate(config, output, build, item, scope, env, bibliography):
    bundle, selected = load_selection(item, scope)
    resolution, stem = selected['h3_resolution'], item['stem']
    if config.get('analysis_h3_resolution') != resolution:
        raise ValueError('Selected plate differs from the edition analysis resolution')
    ident = f'{scope}-{stem}'
    fingerprint = {'selection': item, 'detail_width': config['detail_width'],
                   'card_widths': config['card_widths'], 'builder_sha256': digest(Path(__file__)),
                   'bibliography_sha256': digest(ROOT / config['atlas'] / 'plate-source-bibliography.json')}
    receipt = build / (ident + '.json')
    old = json.loads(receipt.read_text()) if receipt.exists() else None
    if old and old['fingerprint'] == fingerprint and all(
            (output / f['path']).exists() and digest(output / f['path']) == f['sha256']
            for f in old['assets'] + old['provenance']['print_files']):
        return old

    # Copy the validated print layers byte-for-byte. Regeneration does not
    # resample them or reapply the already baked-in outline/opacity styling.
    print_paths = []
    for file in selected['files']:
        source = bundle / file['path']
        if source.suffix not in ('.svg', '.pdf', '.png'):
            continue
        target = output / 'print' / source.relative_to(bundle / f'h3r{resolution}')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        print_paths.append(target)
    legend = output / f'print/legends/{scope}/{stem}-legend.svg'
    tree = etree.parse(str(legend))
    for text in tree.iter('{' + SVG + '}text'):
        if text.text and text.text.startswith(f'H3r{resolution} resolution trial'):
            text.text = text.text.replace('resolution trial', 'selected edition', 1)
    tree.getroot().set('data-selected-edition', 'setouchi-futures')
    tree.write(str(legend), xml_declaration=True, encoding='UTF-8')
    render_svg(legend, legend.with_suffix('.pdf'), env)

    title = f'{item["title"]} · {"World" if scope == "world" else "Japan / Setouchi"}'
    alt, caption = item[scope + '_alt'], item[scope + '_caption']
    assets = []
    raster = output / f'print/maps/{scope}/{stem}.png'
    bounds = item.get('japan_crop_inches') if scope == 'japan' else None
    with Image.open(raster) as master:
        detail = output / 'media' / (ident + '-detail.webp')
        resize_image(master, detail, config['detail_width'])
        assets.append(record_asset(output, detail, ident + '-detail', title, alt, caption))
        card = master
        if bounds:
            x0, y0, x1, y1 = bounds
            if not (0 <= x0 < x1 <= 44 and 0 <= y0 < y1 <= 19.052559):
                raise ValueError('Crop lies outside sheet')
            card = master.crop(tuple(round(v) for v in (
                x0 / 44 * master.width, y0 / 19.052559 * master.height,
                x1 / 44 * master.width, y1 / 19.052559 * master.height)))
        for width in config['card_widths']:
            path = output / 'media' / f'{ident}-{width}.webp'
            resize_image(card, path, width)
            assets.append(record_asset(output, path, f'{ident}-{width}', title, alt, caption))
    pdf = output / 'media' / (ident + '-legend.pdf')
    shutil.copyfile(legend.with_suffix('.pdf'), pdf)
    assets.append(record_asset(output, pdf, ident + '-legend', title + ' · Legend and sources'))

    entry = next(e for e in bibliography['entries'] if e['stem'] == stem)
    source_ids = list(dict.fromkeys(entry['source_ids'] + (entry.get('japan_source_ids', []) if scope == 'japan' else [])))
    base = bundle / f'h3r{resolution}'
    source = base / f'maps/{scope}/{stem}.svg'
    source_legend = base / f'legends/{scope}/{stem}-legend.svg'
    provenance = {
        'id': ident, 'source_svg': source.relative_to(ROOT).as_posix(), 'source_sha256': digest(source),
        'legend_svg': source_legend.relative_to(ROOT).as_posix(), 'legend_sha256': digest(source_legend),
        'selected_plate': deepcopy(item['prepared_plate']), 'h3_resolution': resolution,
        'product_sha256': selected['fingerprint']['snapshot_sha256'], 'layers': selected['layers'],
        'thumbnail_crop_inches': bounds, 'print_files': [file_record(p, output) for p in print_paths],
        'period_and_units': entry['period_and_units'],
        'interpretation': entry['interpretation'] + f' Selected H3r{resolution} edition uses original source-center sampling; '
            'gaps can lack sampled centers. Source-pixel footprints are not filled; finer indexing adds no observations.',
        'japan_context': entry['japan'] if scope == 'japan' else None,
        'sources': [{k: v for k, v in bibliography['sources'][s].items() if k != 'inputs'} for s in source_ids],
        'projection': 'Setouchi modified AuthaGraph; saved horizontal and Japan framing retained',
        'data_rendering': '300 dpi linked PNG layers; PDF embeds layers; reference vectors retained',
    }
    if item.get('radiation_opacity'):
        layer = next(l for l in selected['layers'] if l['id'] == 'surface-shortwave-radiation')
        provenance['selected_radiation_opacity'] = {
            **{k: item['radiation_opacity'][k] for k in ('bands', 'scale_min', 'scale_max')},
            'observed_cells': layer['observed_cells'], 'populated_bands': len(layer['band_counts'])}
        provenance['web_land_outline_overlay'] = item['land_outline']
    result = {'fingerprint': fingerprint, 'assets': assets, 'provenance': provenance}
    write_json(receipt, result)
    print(f'Prepared H3r{resolution} {ident}', flush=True)
    return result


def assemble_print_edition(config, output, maps):
    selected = [m['provenance'] for m in maps if m['provenance'].get('selected_plate')]
    if not selected:
        return None
    resolution = config['analysis_h3_resolution']
    directory = output / 'print'
    combined = []
    html = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            f'<title>Setouchi · H3r{resolution} plates</title>',
            '<style>body{font:18px/1.5 system-ui;background:#240413;color:#fcc553;margin:2rem}a{color:inherit}main{max-width:1100px;margin:auto}.grid{display:grid;grid-template-columns:1fr 1fr;gap:2rem}img{width:100%;height:auto}figure{margin:0 0 2rem}@media(max-width:781px){.grid{grid-template-columns:1fr}}</style><main>',
            f'<h1>Setouchi · H3r{resolution}</h1><p>Atmosphere and Temperature · 44 × 19.052559 inches.</p>',
            '<p><a href="../index.html">Website gallery</a> · <a href="../README.md">Settings and sources</a></p>',
            '<p>SVG files need their adjacent layers directory. PDFs embed the 300 dpi data layers. Source sampling and observation dates are unchanged.</p>']
    for scope in ('world', 'japan'):
        inputs = []
        html.append(f'<h2>{scope.title()}</h2><p><a href="{scope}.pdf">Combined maps and legends</a></p><div class="grid">')
        for item in config['maps']:
            if not item.get('prepared_plate'):
                continue
            stem = item['stem']
            map_base, legend_base = f'maps/{scope}/{stem}', f'legends/{scope}/{stem}-legend'
            inputs.extend([directory / (map_base + '.pdf'), directory / (legend_base + '.pdf')])
            html.append(f'<figure><a href="{map_base}.png"><img src="../media/{scope}-{stem}-1280.webp" alt="{escape(item[scope + "_alt"], quote=True)}"></a>'
                        f'<figcaption>{escape(item["title"])} · H3r{resolution}<br><a href="{map_base}.pdf">PDF</a> · '
                        f'<a href="{map_base}.svg">SVG</a> · <a href="{map_base}.png">PNG</a> · '
                        f'<a href="{legend_base}.pdf">Legend and sources</a></figcaption></figure>')
        html.append('</div>')
        target = directory / (scope + '.pdf')
        subprocess.run(['pdfunite', *map(str, inputs), str(target)], check=True)
        combined.append(file_record(target, output))
    html.append('</main></html>')
    (directory / 'index.html').write_text('\n'.join(html))
    return {'h3_resolution': resolution, 'map_legend_pairs': len(selected),
            'files': combined + [file_record(directory / 'index.html', output)]}
