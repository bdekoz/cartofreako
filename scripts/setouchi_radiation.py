"""Value-based shortwave opacity for the existing Setouchi atmosphere artwork."""
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import subprocess

from lxml import etree

from legend_informatics import ROOT, digest

SVG = 'http://www.w3.org/2000/svg'
LAYER = 'surface-shortwave-radiation'


def band_for(value, settings):
    low, high, bands = settings['scale_min'], settings['scale_max'], settings['bands']
    if not (math.isfinite(low) and math.isfinite(high) and low < high):
        raise ValueError('Radiation scale must have finite, increasing limits')
    if not isinstance(bands, int) or bands < 2:
        raise ValueError('Radiation opacity requires at least two bands')
    if not math.isfinite(value):
        raise ValueError('Radiation observations must be finite')
    fraction = max(0, min(1, (value - low) / (high - low)))
    return math.floor(fraction * (bands - 1) + 0.5)


def prepare_cells(settings, build):
    profile, snapshot = ROOT / settings['profile'], ROOT / settings['snapshot']
    if digest(profile) != settings['profile_sha256'] or digest(snapshot) != settings['snapshot_sha256']:
        raise ValueError('Radiation inputs do not match the dated atmosphere snapshot')
    helper = ROOT / 'build/setouchi-futures-tools/export-atmosphere-cells'
    subprocess.run(['make', '-s', helper.relative_to(ROOT).as_posix()], cwd=ROOT, check=True)
    fingerprint = {'snapshot_sha256': digest(snapshot), 'profile_sha256': digest(profile),
                   'exporter_sha256': digest(helper), 'styler_sha256': digest(Path(__file__))}
    target, receipt = build / 'radiation-cells.json', build / 'radiation-cells-inputs.json'
    cached = json.loads(receipt.read_text()) if receipt.exists() else None
    if (not target.exists() or not cached or cached.get('fingerprint') != fingerprint
            or cached.get('cells_sha256') != digest(target)):
        temporary = target.with_suffix('.tmp')
        subprocess.run([str(helper), str(profile), str(snapshot), str(temporary)], check=True)
        temporary.replace(target)
        receipt.write_text(json.dumps({'fingerprint': fingerprint, 'cells_sha256': digest(target)}, indent=2) + '\n')
    data = json.loads(target.read_text())
    if data.get('schema') != 'cartofreako-atmosphere-cell-paths-v1' or data.get('projection') != 'authagraph':
        raise ValueError('Unsupported radiation cell export')
    return {'data': data, 'fingerprint': fingerprint,
            'inputs': {'snapshot': settings['snapshot'], 'profile': settings['profile'], **fingerprint}}


def apply_opacity(tree, data, settings):
    """Regroup the original polygons; fail if their dates or geometry differ."""
    groups = tree.xpath('//*[@id=$ident]', ident=LAYER)
    metadata = tree.xpath('//*[@id="cloud-atmosphere-metadata"]')
    if len(groups) != 1 or len(metadata) != 1:
        raise ValueError('Expected one radiation layer and atmosphere metadata record')
    meta = metadata[0]
    if (meta.get('data-observation-jaxa-jasmes-swr-end') != data['observation_end_utc']
            or int(meta.get('data-feature-count')) != data['feature_count']
            or int(meta.get('data-h3-resolution')) != data['h3_resolution']
            or data['missing_semantics'] != 'unobserved-not-zero'):
        raise ValueError('Radiation snapshot does not match the plate provenance')
    group = groups[0]
    original = {int(p.get('data-bin')): p for p in group if etree.QName(p).localname == 'path'}
    if set(original) != set(range(1, 7)):
        raise ValueError('Expected the six original radiation paths')
    source_bins = defaultdict(list)
    seen = set()
    for cell in data['cells']:
        if cell['h3'] in seen or not 0.2 <= cell['valid_fraction'] <= 1:
            raise ValueError('Duplicate or insufficient-quality radiation cell')
        seen.add(cell['h3'])
        band_for(cell['value'], settings)
        source_bins[cell['source_bin']].append(cell)
    if set(source_bins) != set(original):
        raise ValueError('Radiation source bands differ from the plate')
    for number, old in original.items():
        cells = source_bins[number]
        reconstructed = ' '.join(''.join(c['path'] for c in cells).split())
        if (len(cells) != int(old.get('data-cell-count'))
                or reconstructed != ' '.join(old.get('d').split())):
            raise ValueError('Radiation cell geometry differs from the existing plate')

    buckets, counts = defaultdict(list), Counter()
    bands = settings['bands']
    for cell in data['cells']:
        band = band_for(cell['value'], settings)
        # The original six stroke widths remain unchanged for every cell.
        # A level crossing a width boundary needs two paths with the same alpha.
        buckets[band, cell['source_bin']].append(cell)
        counts[band] += 1
    for old in original.values():
        group.remove(old)
    for (band, source_bin), cells in sorted(buckets.items()):
        old = original[source_bin]
        attrs = {key: value for key, value in old.attrib.items()
                 if key not in ('d', 'id', 'style', 'data-bin', 'data-cell-count')}
        style = {key.strip(): value.strip() for key, value in
                 (part.split(':', 1) for part in old.get('style').split(';') if ':' in part)}
        style['stroke-opacity'] = f'{band / (bands - 1):.9g}'
        attrs.update(id=f'{LAYER}-opacity-{band + 1:03d}-width-{source_bin}',
                     d=''.join(c['path'] for c in cells),
                     style=';'.join(f'{key}:{value}' for key, value in style.items()))
        attrs.update({'data-opacity-band': str(band + 1), 'data-source-bin': str(source_bin),
                      'data-cell-count': str(len(cells)),
                      'data-value-min': str(min(c['value'] for c in cells)),
                      'data-value-max': str(max(c['value'] for c in cells))})
        etree.SubElement(group, '{' + SVG + '}path', attrs)
    group.set('data-opacity-bands', str(bands))
    group.set('data-opacity-domain', f'{settings["scale_min"]} {settings["scale_max"]} W/m2')
    group.set('data-opacity-mapping', 'nearest linear level; 0 to 1 inclusive')
    values = [c['value'] for c in data['cells']]
    return {'bands': bands, 'populated_bands': len(counts), 'path_groups': len(buckets),
            'observed_cells': len(values), 'value_range_w_m2': [min(values), max(values)],
            'scale_w_m2': [settings['scale_min'], settings['scale_max']],
            'opacity_range': [0, 1], 'mapping': 'nearest of equally spaced opacity levels',
            'band_cell_counts': [counts[i] for i in range(bands)],
            'observation_end_utc': data['observation_end_utc'],
            'missing_semantics': data['missing_semantics'], 'geometry_verified_unchanged': True,
            'source_color_and_line_widths_retained': True}


def update_legend(tree, settings, background):
    """Explain the shared scale and show its steps against the map background."""
    bands = settings['bands']
    low, high = settings['scale_min'], settings['scale_max']
    labels = [n for n in tree.iter('{' + SVG + '}text')
              if (n.text or '').startswith('Shortwave radiation ·')]
    if len(labels) != 1:
        raise ValueError('Expected one shortwave legend label')
    labels[0].text = f'Shortwave radiation · {low:g}–{high:g} W/m² · {bands} opacity bands · 15 Oct'
    for node in tree.iter('{' + SVG + '}text'):
        if (node.text or '').startswith('Land outlines above data;'):
            node.text = 'Land outlines above data; no land fill. Missing observations are not zero.'
    parent = tree.xpath('//*[@id="legend-informatics"]')[0]
    bottom = max(float(n.get('y')) for n in parent.iter('{' + SVG + '}text')
                 if n.get('x') == '42.38' and 0 < float(n.get('y', '0')) < 18)
    y, x, width = max(9.2, bottom + 0.75), 31.0, 10.0
    if y + 2.3 >= 18:
        raise ValueError('Radiation opacity key does not fit the legend sheet')
    key = etree.SubElement(parent, '{' + SVG + '}g', id='web-radiation-opacity-key')

    def text(value, x_pos, y_pos, size=0.2, anchor='start'):
        node = etree.SubElement(key, '{' + SVG + '}text',
            {'x': str(x_pos), 'y': str(y_pos), 'font-family': 'Atkinson Hyperlegible',
             'font-size': str(size), 'fill': '#fcc553', 'text-anchor': anchor})
        node.text = value

    text(f'Radiation opacity · {bands} bands', x, y, 0.25)
    text('Stronger cells are more opaque; the same scale applies to both views.', x, y + 0.4, 0.17)
    etree.SubElement(key, '{' + SVG + '}rect',
        {'x': str(x), 'y': str(y + 0.65), 'width': str(width), 'height': '0.65', 'fill': background})
    for band in range(bands):
        xx = x + (band + 0.5) * width / bands
        etree.SubElement(key, '{' + SVG + '}line',
            {'x1': str(xx), 'x2': str(xx), 'y1': str(y + 0.72), 'y2': str(y + 1.23),
             'stroke': '#f0bd45', 'stroke-opacity': f'{band / (bands - 1):.9g}',
             'stroke-width': str(width / bands * 0.8)})
    for fraction, anchor in [(0, 'start'), (0.5, 'middle'), (1, 'end')]:
        value = low + (high - low) * fraction
        text(f'{value:g} W/m² · {fraction:.0%}', x + width * fraction, y + 1.65, 0.18, anchor)
    text('Low values fade to transparent. Missing observations are not zero.', x, y + 2.1, 0.17)
