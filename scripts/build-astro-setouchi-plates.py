#!/usr/bin/env python3
"""Style native astronomy SVGs in Setouchi wine/amber with separate source plates."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from html import escape
import json
import os
from pathlib import Path
import shutil
import subprocess

from lxml import etree as E
from PIL import Image

from atlas_presentation import settings, theme
from atlas_review_sheets import legend
from cartofreako_style import STYLE
from dataset import ROOT, atomic_json, digest
from legend_informatics import el, font_environment, save

LAYERS = ('celestial-reference', 'stars', 'exoplanet-hosts', 'deep-sky', 'solar-system', 'transients')
KINDS = ('star', 'exoplanet-host', 'sun', 'moon', 'planet', 'asteroid', 'comet', 'galaxy',
         'supernova-remnant', 'nebula', 'black-hole', 'x-ray-binary', 'active-galaxy', 'quasar',
         'gamma-ray-burst', 'magnetar-burst-candidate', 'x-ray-transient')
PRODUCTS = {'all-sky': 'All-sky celestial context', 'ground-multiband': 'San Francisco ground observer',
            'hubble': 'Hubble Space Telescope observer'}


def parse(path):
    return E.parse(str(path), E.XMLParser(huge_tree=True)).getroot()


def normalized(node):
    return (E.QName(node).localname, sorted(node.attrib.items()), (node.text or '').strip(),
            [normalized(child) for child in node if isinstance(child.tag, str)])


def scientific_layers(root):
    return {key: normalized(root.xpath('//*[@id=$key]', key=key)[0]) for key in LAYERS}


def dimensions(root):
    x, y, width, height = map(float, root.get('viewBox').split())
    if x or y or min(width, height) <= 0:
        raise ValueError('Expected a native zero-origin astronomy frame')
    return width, height


def make_map(source, destination, companion, recipe, label_points):
    original = parse(source)
    root = deepcopy(original)
    width, height = dimensions(root)
    # All five landscape projections retain a 43.5-inch image width. Star-X
    # retains its native portrait frame with a 43.5-inch image height.
    scale = STYLE['atlas']['image_width_inches'] / max(width, height)
    frame = el('g', id='setouchi-astronomy-frame',
               transform=f'translate({width*(1-scale)/2} {height*(1-scale)/2}) scale({scale})')
    for child in list(root):
        if E.QName(child).localname not in ('title', 'desc', 'metadata', 'defs'):
            root.remove(child)
            frame.append(child)
    root.append(el('rect', id='st2-sheet-paper', width=width, height=height, fill=recipe['background']))
    root.append(frame)
    for label in root.xpath('//*[@id="labels"]//*[local-name()="text"]'):
        label.set('font-size', str(label_points/72/scale))
    root.set('data-sheet-kind', 'map')
    root.set('data-marker-color-policy', 'preserve-source-astronomy')
    root.set('data-legend-companion', os.path.relpath(companion, destination.parent))
    root.set('data-source-svg-sha256', digest(source))
    root.set('data-image-scale', str(scale))
    temporary = destination.with_suffix('.theme-source.svg')
    save(root, temporary)
    theme(temporary, destination, recipe, 'map')
    temporary.unlink()
    result = parse(destination)
    if scientific_layers(original) != scientific_layers(result):
        raise ValueError('Astronomical geometry or symbol colors changed: '+source.name)
    before = [(n.get('x'), n.get('y'), n.text) for n in original.xpath('//*[@id="labels"]/*')]
    after = [(n.get('x'), n.get('y'), n.text) for n in result.xpath('//*[@id="labels"]/*')]
    if before != after:
        raise ValueError('Astronomy labels or positions changed')
    return original


def make_legend(source, destination, map_path, title, profile, recipe, input_hash):
    metadata = source.xpath('//*[@id="astro-metadata"]')[0]
    markers = source.xpath('//*[@data-kind]')
    counts = Counter(n.get('data-kind') for n in markers)
    kinds = [kind for kind in KINDS if counts[kind]]
    kinds += sorted(set(counts)-set(KINDS))
    keys = [(recipe['text'], f'{kind.replace("-", " ").title()} / {counts[kind]:,}', 'circle') for kind in kinds]
    timestamp = metadata.get('data-timestamp')
    observer = profile['observer']
    observer_notes = [observer['name'], 'Calculation: '+timestamp,
                      'Instrument: '+profile['instrumentation']['name'],
                      'Bands: '+', '.join(profile['instrumentation']['bands'])]
    if observer['kind'] == 'terrestrial':
        lat, lon = observer['latitude_deg'], observer['longitude_deg_east']
        observer_notes += [f'Observer: {abs(lat):g} degrees {"N" if lat>=0 else "S"}, '
                           f'{abs(lon):g} degrees {"E" if lon>=0 else "W"}.',
                           'Sun altitude: '+metadata.get('data-sun-altitude-deg')+' degrees.',
                           f'Plotted: {counts["star"]} stars and {counts["exoplanet-host"]} exoplanet hosts.']
    else:
        observer_notes += ['Hubble element epoch: '+metadata.get('data-orbit-element-epoch'),
                           'Earth-limb avoidance: '+str(observer['earth_limb_avoidance_deg'])+' degrees.',
                           'Sun avoidance: '+str(observer['sun_avoidance_deg'])+' degrees.']
    method = ['Selected catalogs and source-declared epochs; this is not a census of the sky.',
              'Stellar glyph size encodes catalog magnitude; stellar color follows the source color-index bins.',
              'Aquamarine outlined circles mark confirmed-exoplanet host systems.',
              'Planet filled glyphs use the retained fixed display radius; tiny dashed outlines encode true angular size.',
              'Rays are decorative fixed-point marks, not measured flux or physical extent.',
              f'Transient lookback: {profile["dynamic_events"]["lookback_days"]:g} days; '
              f'{len(source.xpath("//*[@id='transients']//*[@data-kind]"))} plotted transient records.']
    subtitle = timestamp+' / '+f'{len(markers):,} plotted objects / {len(source.xpath("//*[@id='labels']/*"))} labels'
    sheet = legend(map_path.stem, title, subtitle,
                   [{'title': 'Objects plotted / exact counts', 'keys': keys},
                    {'title': 'Observer and instrument', 'notes': observer_notes},
                    {'title': 'Reading this map', 'notes': method}],
                   ['Native object positions, source colors and visibility decisions are retained. '
                    'Zero plotted objects of a class do not establish absence from the sky.',
                    'Setouchi wine/amber is presentation. The ground observer remains San Francisco; '
                    'this color treatment does not relocate the observer or update source observation epochs.'],
                   ['Gaia / ESA: https://gea.esac.esa.int/archive/; NASA Exoplanet Archive: https://exoplanetarchive.ipac.caltech.edu/',
                    'NASA/JPL Solar System Dynamics: https://ssd.jpl.nasa.gov/; curated sources: per-object data-source attributes in the map SVG.',
                    'Hubble elements: '+metadata.get('data-orbit-source', 'not used for this ground-profile product'),
                    'Exact copied profiles, catalog hashes and individual object source URLs: sources/input-manifest.json'])
    # The shared template's fixed date is replaced with the actual sky time.
    for node in sheet.xpath('//*[local-name()="text"]'):
        if (node.text or '').startswith('CARTOFREAKO  /'):
            node.text = 'CARTOFREAKO / '+timestamp+' / Separate astronomy map and source plate'
    # Replace the template's generic circles with enlarged copies of actual
    # source glyphs. Neither sample colors nor their internal shapes change.
    icons = sheet.xpath('./*[local-name()="circle"]')
    for kind, icon in zip(kinds, icons, strict=True):
        sample = next(n for n in markers if n.get('data-kind') == kind)
        cx, cy, radius = (float(sample.get(k)) for k in ('cx', 'cy', 'r'))
        rays = source.xpath('//*[@id=$key]', key='stationary-rays-'+sample.get('id'))
        # Ray ornaments extend to three times the circle radius. Keep the
        # complete example within its key row and away from adjacent labels.
        key_radius = .07 if rays else .14
        glyph = el('g', id='key-'+kind, data_legend_kind=kind, data_source_object_id=sample.get('id'),
                   transform=f'translate({icon.get("cx")} {icon.get("cy")}) scale({key_radius/radius}) translate({-cx} {-cy})')
        copy = deepcopy(sample)
        for key in list(copy.attrib):
            if key == 'id' or key.startswith('data-'):
                del copy.attrib[key]
        glyph.append(copy)
        for ray_group in rays:
            copy = deepcopy(ray_group)
            for n in copy.iter():
                n.attrib.pop('id', None)
            glyph.append(copy)
        sheet.replace(icon, glyph)
    sheet.append(deepcopy(metadata))
    sheet.set('data-map-companion', os.path.relpath(map_path, destination.parent))
    sheet.set('data-input-manifest-sha256', input_hash)
    sheet.set('data-atlas-presentation', recipe['id'])
    save(sheet, destination)
    return dict(counts)


def export(record, output, env, dpi):
    svg = output/record['svg']
    folder = svg.parent.parent
    paths = {suffix: folder/suffix/(svg.stem+'.'+suffix) for suffix in ('pdf', 'png')}
    paths['preview'] = folder/'preview'/(svg.stem+'.png')
    log = output/'sources/export-logs'/(record['kind']+'-'+svg.stem+'.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    runner = ['bash', str(ROOT/'scripts/run-inkscape.sh'), 'inkscape', str(svg), '--export-area-page']
    with log.open('w') as stream:
        for suffix in ('pdf', 'png'):
            command = runner+['--export-filename='+str(paths[suffix])]
            if suffix == 'png':
                command += [f'--export-dpi={dpi}', '--export-background=#240413',
                            '--export-background-opacity=255', '--export-png-color-mode=RGB_8']
            subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
    with Image.open(paths['png']) as image:
        expected = tuple(round(v*dpi) for v in record['size_inches'])
        if any(abs(a-b)>1 for a,b in zip(image.size, expected)):
            raise ValueError('Wrong PNG dimensions: '+str(svg))
        record['pixel_dimensions'] = list(image.size)
        image.thumbnail((2560, 2560), Image.Resampling.LANCZOS)
        image.convert('RGB').save(paths['preview'])
    record['outputs'] = {key: {'path': str(path.relative_to(output)), 'sha256': digest(path),
                                'bytes': path.stat().st_size} for key,path in paths.items()}
    print('Exported', record['kind'], svg.stem, flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='native astronomy output directory')
    parser.add_argument('--data-dir', type=Path, required=True, help='matching refreshed astronomy input directory')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--dpi', type=int, default=STYLE['atlas']['png_dpi'])
    args = parser.parse_args()
    if min(args.workers, args.dpi) <= 0:
        parser.error('--workers and --dpi must be positive')
    args.source, args.data_dir, args.output = (p.resolve() for p in (args.source, args.data_dir, args.output))
    sources = sorted(args.source.glob('*/svg/astro-*.svg'))
    if not sources:
        parser.error('No native astronomy SVGs found')
    config, recipe = settings(STYLE)
    inputs = []
    for path in sorted(args.data_dir.glob('*')):
        if path.suffix in ('.json', '.csv') or path.name == 'SHA256SUMS':
            target = args.output/'sources/data'/path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            inputs.append({'path': str(target.relative_to(args.output)), 'sha256': digest(path)})
    urls = sorted({url for path in sources for url in parse(path).xpath('//*[@data-source]/@data-source')})
    manifest = {'schema': 'cartofreako-astro-setouchi-inputs-v1', 'source_directory': str(args.data_dir),
                'inputs': inputs, 'object_source_urls': urls, 'palette': recipe,
                'style_sha256': digest(ROOT/'generation-style.json')}
    manifest_path = args.output/'sources/input-manifest.json'
    atomic_json(manifest_path, manifest)
    records, entries = [], []
    for source in sources:
        projection = source.parent.parent.name
        raw = parse(source)
        metadata = raw.xpath('//*[@id="astro-metadata"]')[0]
        filename = metadata.get('data-profile')
        profile = json.loads((args.data_dir/filename).read_text())
        if metadata.get('data-timestamp') != profile['timestamp']:
            raise ValueError('Input profile timestamp does not match source SVG')
        map_path = args.output/'maps'/projection/'svg'/source.name
        legend_path = args.output/'legends'/projection/'svg'/(source.stem+'-legend.svg')
        title = 'Astronomy / '+PRODUCTS['all-sky' if metadata.get('data-product')=='all-sky' else metadata.get('data-observer-id')]
        title += ' / '+projection.replace('-', ' ').title()
        original = make_map(source, map_path, legend_path, recipe, config['astronomy_label_font_size_pt'])
        counts = make_legend(original, legend_path, map_path, title, profile, recipe, digest(manifest_path))
        for kind,path in (('map', map_path), ('legend', legend_path)):
            records.append({'stem': source.stem, 'projection': projection, 'kind': kind,
                            'svg': str(path.relative_to(args.output)), 'svg_sha256': digest(path),
                            'source_svg': str(source), 'source_svg_sha256': digest(source),
                            'timestamp': profile['timestamp'], 'counts': counts,
                            'size_inches': list(dimensions(parse(path)))})
        entries.append({'stem': source.stem, 'projection': projection, 'title': title})
    env = font_environment()
    Image.MAX_IMAGE_PIXELS = 200_000_000
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(lambda r: export(r, args.output, env, args.dpi), records))
    receipt = {'schema': 'cartofreako-astro-setouchi-plates-v1', 'palette': recipe, 'dpi': args.dpi,
               'input_manifest_sha256': digest(manifest_path), 'records': records}
    atomic_json(args.output/'sources/plates.json', receipt)
    pdfs = [str(args.output/r['outputs']['pdf']['path']) for r in records]
    if shutil.which('pdfunite'):
        subprocess.run(['pdfunite', *pdfs, str(args.output/'astro-setouchi-map-and-legend-plates.pdf')], check=True)
    page = ['<!doctype html><meta charset="utf-8"><title>Astronomy / Setouchi wine and amber</title>',
            '<style>body{background:#240413;color:#fcc553;font:18px sans-serif;margin:2rem}a{color:inherit}.pair{display:flex;gap:1rem}.sheet{width:49%}img{width:100%}article{margin:3rem 0}</style>',
            '<h1>Astronomy / Setouchi wine and amber</h1><p>Refreshed calculation: '+escape(records[0]['timestamp'])
            +'. Separate map and legend plates; native projections and source symbol colors retained.</p>',
            '<p><a href="astro-setouchi-map-and-legend-plates.pdf">Combined map/legend PDF</a></p>']
    for entry in entries:
        page.append('<article><h2>'+escape(entry['title'])+'</h2><div class="pair">')
        for record in (r for r in records if r['stem']==entry['stem']):
            page.append('<div class="sheet"><p>'+record['kind'].title()+' / ' +
                        ' · '.join('<a href="'+escape(record['outputs'][key]['path'])+'">'+key.upper()+'</a>' for key in ('pdf','png'))
                        +' · <a href="'+record['svg']+'">SVG</a></p><img src="'+record['outputs']['preview']['path']+'"></div>')
        page.append('</div></article>')
    (args.output/'index.html').write_text('\n'.join(page)+'\n')
    print(f'Complete: {len(entries)} map/legend pairs in {args.output}', flush=True)


if __name__ == '__main__':
    main()
