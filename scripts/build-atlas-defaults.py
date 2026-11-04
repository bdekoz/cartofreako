#!/usr/bin/env python3
"""Compose the default atlas from ST2 inputs and the approved MSP presentation.

The dated editions remain inputs. Every output records its actual source and
presentation hashes; a new presentation never implies a new observation date.
"""
import argparse
import copy
import gzip
import hashlib
import importlib
import json
import math
from pathlib import Path
import re
import xml.sax

from atlas_presentation import settings, theme, css, paint
from cartofreako_style import STYLE
from legend_informatics import E, ROOT, NS, WIDTH, HEIGHT, digest, el, save, text, register_fonts

MSP = importlib.import_module('build-msp-speculations')
LAYOUT = importlib.import_module('revise-setouchi-plates')
SCALE = STYLE['atlas']['image_width_inches'] / WIDTH


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def read_svg(path):
    return E.parse(str(path), E.XMLParser(huge_tree=True)).getroot()


class Geometry(xml.sax.ContentHandler):
    """Order-sensitive audit of geometry, values and text, independent of paint."""
    def __init__(self):
        self.hash = hashlib.sha256()
        self.stack = []
        self.count = 0
        self.pending = []

    def flush(self):
        value = ''.join(self.pending).strip()
        if value:
            self.hash.update(value.encode())
        self.pending = []

    def startElement(self, name, attrs):
        self.flush()
        skip = (self.stack and self.stack[-1]) or attrs.get('data-presentation-only') == 'true'
        self.stack.append(skip)
        if skip:
            return
        ignored = {'style', 'fill', 'fill-opacity', 'stroke', 'stroke-opacity', 'stroke-width',
                   'opacity', 'data-atlas-presentation', 'data-sheet-background'}
        a = {k: v for k, v in attrs.items() if k not in ignored}
        self.hash.update(json.dumps([name, a], sort_keys=True).encode())
        self.count += name in ('path', 'circle', 'line', 'polygon', 'polyline', 'rect', 'use')

    def characters(self, value):
        if self.stack and not self.stack[-1] and value.strip():
            self.pending.append(value)

    def endElement(self, name):
        self.flush()
        if not self.stack.pop():
            self.hash.update(('</' + name + '>').encode())


def geometry(path):
    audit = Geometry()
    xml.sax.parse(str(path), audit)
    return {'sha256': audit.hash.hexdigest(), 'shapes': audit.count}


def use_scale(root, identifier):
    uses = root.xpath('//*[local-name()="use" and @*[local-name()="href"]="#' + identifier + '"]')
    if len(uses) != 1:
        raise ValueError('Expected one Japan source instance: ' + identifier)
    scale = 1.0
    for node in [uses[0], *uses[0].iterancestors()]:
        for value in re.findall(r'scale\(([^)]+)\)', node.get('transform', '')):
            numbers = list(map(float, value.replace(',', ' ').split()))
            if len(numbers) == 2 and numbers[0] != numbers[1]:
                raise ValueError('Nonuniform text scaling')
            scale *= numbers[0]
    return scale


def physical_labels(root, layer_ids, points, scale):
    for identifier in layer_ids:
        for layer in root.xpath('//*[@id="' + identifier + '"]'):
            layer.set('data-font-size-pt', str(points))
            for label in layer.xpath('.//*[local-name()="text"]'):
                label.set('font-size', str(points / 72 / scale))


def japan_source(root, approved, stem, config, recipe):
    old = root.xpath('//*[@id="source-content"]')[0]
    new = copy.deepcopy(approved.xpath('//*[@id="source-cartography"]')[0])
    new.set('id', 'source-content')
    old.getparent().replace(old, new)
    # The original Japan viewport/locator is retained; do not crop a celestial sky.
    scale = use_scale(root, 'source-content')
    if stem.endswith('global'):
        physical_labels(root, ('starlink-id', 'starlink-name'), recipe['variant']['global_starlink_font_size_pt'], scale)
    elif stem == 'astro-all-sky':
        physical_labels(root, ('labels',), config['astronomy_label_font_size_pt'], scale)
    return scale


def observer_groups(root, recipe):
    """Style the retained Setouchi observer without changing a propagated point."""
    source = root.xpath('//*[@id="source-content"]')[0]
    markers = source.xpath('.//*[@data-norad-id and local-name()="circle"]')
    if not markers:
        raise ValueError('Expected the pinned Setouchi observer circle population')
    profile = read(ROOT / 'assets.static/orbital-technosphere/20261103/orbital-technosphere-profile.json')
    fleets = [g for g in profile['catalogs']['groups'] if 'constellation' in g]
    scale = use_scale(root, 'source-content')
    groups = {}
    coordinates = []
    for marker in markers:
        x, y, radius = (float(marker.get(k)) for k in ('cx', 'cy', 'r'))
        coordinates.append((marker.get('data-norad-id'), x, y))
        memberships = set(re.split(r'[,;\s]+', marker.get('data-groups', '')))
        fleet = next((g['constellation'] for g in fleets if g['id'] in memberships), None)
        role = marker.get('data-role')
        group = fleet['id'] if fleet and role != 'debris' else role
        color = 'rgb(' + ','.join(map(str, fleet['color_rgb'])) + ')' if fleet and role != 'debris' else css(marker.attrib).get('fill')
        shape = ('x' if role == 'debris' else 'sunburst' if group == 'starlink' else
                 'square' if group == 'intelsat' else 'triangle' if role == 'earth-observation' else 'circle')
        if group not in groups:
            bank = el('g', id=group, data_display_group=group)
            bank.set('{'+MSP.ORBITAL.INKSCAPE+'}groupmode', 'layer')
            bank.set('{'+MSP.ORBITAL.INKSCAPE+'}label', fleet['name'] if fleet else group.replace('-', ' ').title())
            names = el('g', bank, id=group+'-name', data_font_size_pt=recipe['variant']['observer_starlink_font_size_pt'])
            names.set('{'+MSP.ORBITAL.INKSCAPE+'}groupmode', 'layer')
            names.set('{'+MSP.ORBITAL.INKSCAPE+'}label', 'name')
            names.set('style', 'display:inline' if group == 'starlink' else 'display:none')
            points = el('g', bank, id=group+'-locpoint')
            points.set('{'+MSP.ORBITAL.INKSCAPE+'}groupmode', 'layer')
            points.set('{'+MSP.ORBITAL.INKSCAPE+'}label', 'locpoint')
            groups[group] = (bank, names, points)
        bank, names, points = groups[group]
        marker.getparent().remove(marker)
        if shape != 'circle':
            marker.tag = '{'+NS+'}path'
            for key in ('cx', 'cy', 'r'):
                del marker.attrib[key]
            r = radius * (recipe['variant']['starlink_marker_linear_scale'] if group == 'starlink' else 1)
            if shape == 'x':
                d = f'M {x-r} {y-r} L {x+r} {y+r} M {x-r} {y+r} L {x+r} {y-r}'
            else:
                count = {'sunburst': 16, 'square': 4, 'triangle': 3}[shape]
                angle = math.pi/4 if shape == 'square' else -math.pi/2
                vertices = [(x+r*(.45 if shape == 'sunburst' and i%2 else 1)*math.cos(angle+2*math.pi*i/count),
                             y+r*(.45 if shape == 'sunburst' and i%2 else 1)*math.sin(angle+2*math.pi*i/count)) for i in range(count)]
                d = 'M '+' L '.join(f'{a:.12g} {b:.12g}' for a, b in vertices)+' Z'
            marker.set('d', d)
        marker.set('data-display-group', group)
        marker.set('data-marker-shape', shape)
        marker.set('data-source-center', f'{x} {y}')
        if group == 'starlink':
            marker.set('data-marker-linear-scale', str(recipe['variant']['starlink_marker_linear_scale']))
        # Legacy optical-candidate outlines can cover the smaller sunburst
        # interiors. The approved vendor encoding uses the fill/illumination.
        paint(marker.attrib, fill=color, stroke_opacity=0)
        if shape == 'x':
            paint(marker.attrib, fill='none', stroke='#000000', stroke_opacity=1, stroke_width=.009)
            el('path', points, d=marker.get('d'), data_presentation_only='true',
               fill='none', stroke=recipe['halo'], stroke_width=.0243)
        points.append(marker)
        label = text(names, x+radius*3.5, y, marker.get('data-name'),
                     recipe['variant']['observer_starlink_font_size_pt']/72/scale,
                     data_norad_id=marker.get('data-norad-id'))
        label.set('fill', recipe['text'])
        label.set('id', 'name-norad-'+marker.get('data-norad-id'))
    for old in source.xpath('./*[@id="labels"]'):
        source.remove(old)
    first = next((i for i, n in enumerate(source) if n.get('id', '').startswith('objects-')), len(source))
    for old in source.xpath('./*[starts-with(@id,"objects-")]'):
        source.remove(old)
    ordered = sorted(groups, key=lambda group: group != 'starlink')
    for i, group in enumerate(ordered):
        bank, names, points = groups[group]
        bank.set('data-object-count', str(len(names)))
        source.insert(first+i, bank)
    root.set('data-satellite-name-display', 'starlink-only')
    after = [(n.get('data-norad-id'), *map(float, n.get('data-source-center').split()))
             for n in source.xpath('.//*[@data-source-center]')]
    assert sorted(coordinates) == sorted(after)
    return groups


def legend_number(root, ordinal, recipe):
    nodes = root.xpath('//*[@id="plate-number"]')
    if not nodes:
        nodes = [n for n in root.xpath('//*[local-name()="text"]') if (n.text or '').startswith('Sources and class definitions:')]
    node = nodes[0] if nodes else text(root, 42.38, HEIGHT-.5, '', .5, text_anchor='end')
    node.set('id', 'plate-number')
    node.set('font-size', '.5')
    node.set('font-weight', '700')
    node.text = f'{ordinal:02d}'
    paint(node.attrib, fill=recipe['text'], stroke='none', stroke_opacity=0)


def scope_note(root, value, recipe):
    note = el('g', root, id='atlas-scope-note', data_presentation_only='true')
    for i, line in enumerate(MSP.ORBITAL.wrapped(value, 12/72, 38)):
        text(note, .8, 16.35+i*.23, line, 12/72).set('fill', recipe['text'])


def verify_subjects(out, config, recipe):
    """Check the physical styles and populations in the actual atlas SVGs."""
    result = {}
    for scope in ('world', 'japan'):
        for stem in config['subjects']+recipe.get('additional_subjects', []):
            root = read_svg(out/'maps'/scope/'svg'/(stem+'.svg'))
            scale = SCALE if scope == 'world' else use_scale(root, 'source-content')
            if stem.startswith('orbital'):
                points = root.xpath('//*[@data-norad-id and @data-marker-shape]')
                assert len({n.get('data-norad-id') for n in points}) == len(points)
                names = root.xpath('//*[@id="starlink-id"]' if stem.endswith('global') else '//*[@id="starlink-name"]')[0]
                assert css(names.attrib).get('display') != 'none'
                for label in names:
                    assert abs(float(label.get('font-size'))*72*scale-6) < 1e-8
                for bank in root.xpath('//*[substring(@id,string-length(@id)-4)="-name"]'):
                    if bank.get('id') != 'starlink-name' or stem.endswith('global'):
                        assert css(bank.attrib).get('display') == 'none'
                ordered = {n: i for i, n in enumerate(root.iter())}
                assert max(ordered[n] for n in names) < min(ordered[n] for n in points)
                for marker in points:
                    group, role = marker.get('data-display-group'), marker.get('data-role')
                    if group == 'starlink':
                        assert marker.get('data-marker-shape') == 'sunburst'
                        assert float(marker.get('data-marker-linear-scale')) == 1.5
                    if role == 'debris':
                        assert marker.get('data-marker-shape') == 'x'
                        assert css(marker.attrib)['stroke'] in ('rgb(0,0,0)', '#000000')
                    elif group == 'intelsat':
                        assert marker.get('data-marker-shape') == 'square'
                assert len(names) == sum(p.get('data-display-group') == 'starlink' for p in points)
                result[scope+'/'+stem] = {'objects': len(points), 'starlink_labels': len(names), 'physical_font_size_pt': 6}
                if stem.endswith('global'):
                    tracks = root.xpath('//*[@id="representative-ground-tracks"]/*[local-name()="path"]')
                    assert tracks and all(abs(float(css(p.attrib)['stroke-width'])-.024)<1e-10 for p in tracks)
            elif stem == 'astro-all-sky':
                labels = root.xpath('//*[@id="labels"]/*[local-name()="text"]')
                assert len(labels) == 35
                assert all(abs(float(n.get('font-size'))*72*scale-config['astronomy_label_font_size_pt']) < 1e-8 for n in labels)
                result[scope+'/'+stem] = {'labels': len(labels), 'physical_font_size_pt': 12}
            else:
                links = root.xpath('//*[@data-gateway-link="true"]')
                assert len(links) == 124
                assert all(css(n.attrib)['stroke'] == recipe['text'] and float(css(n.attrib)['stroke-opacity']) == 1 for n in links)
                result[scope+'/'+stem] = {'fiber_links': len(links)}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'output/setouchi-triennale-2028-st2')
    parser.add_argument('--output', type=Path, default=ROOT/'output/atlas')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--skip-exports', action='store_true')
    args = parser.parse_args()
    config, recipe = settings(STYLE)
    out = args.output.resolve()
    if out == args.source.resolve():
        parser.error('Default atlas output must be separate from its source edition')
    receipt_path = out/'sources/atlas-presentation.json'
    fingerprint = {'generation_style_sha256': digest(ROOT/'generation-style.json'),
                   'recipe_sha256': digest(ROOT/STYLE['atlas']['presentation']['recipe_file']),
                   'builder_sha256': digest(Path(__file__)), 'theme_sha256': digest(ROOT/'scripts/atlas_presentation.py')}
    if args.check:
        receipt = read(receipt_path)
        assert receipt['fingerprint'] == fingerprint, 'Stale atlas presentation'
        assert len(receipt['records']) == 152
        for source in receipt['inputs']:
            assert digest(ROOT/source['path']) == source['sha256'], source['path']
        for r in receipt['records']:
            assert digest(out/r['svg']) == r['svg_sha256'], r['svg']
            if not args.skip_exports:
                export = read(out/'sources/sheet-exports'/f"{r['kind']}-{r['scope']}-{r['stem']}.json")
                assert export['fingerprint']['svg_sha256'] == r['svg_sha256']
                for file in export['outputs'].values():
                    assert digest(out/file['path']) == file['sha256']
        subjects = verify_subjects(out, config, recipe)
        write(out/'sources'/('sheets-validation-svg.json' if args.skip_exports else 'sheets-validation.json'),
              {'status': 'passed', 'sheets': 152, 'exports_checked': not args.skip_exports, 'presentation': recipe['id'], 'subjects': subjects})
        print('Default atlas verified: 152 sheets / '+recipe['palette'])
        return
    cache_path = out/'sources/presentation-cache.json'
    previous = read(receipt_path) if receipt_path.exists() else read(cache_path) if cache_path.exists() else {}
    prior = {(r['kind'], r['scope'], r['stem']): r for r in previous.get('records', [])}
    theme_current = all(previous.get('fingerprint', {}).get(key) == fingerprint[key]
                        for key in ('generation_style_sha256', 'recipe_sha256', 'theme_sha256'))
    register_fonts()
    out.mkdir(parents=True, exist_ok=True)
    (out/'.gitignore').write_text('# Local default atlas build.\n*\n')
    base_path = args.source/'sources/separate-sheets.json'
    base = read(base_path)
    if len(base['records']) != 152:
        raise ValueError('Expected all 38 world/Japan map/legend pairs')
    approved = ROOT/STYLE['atlas']['presentation']['approved_delivery']
    manifest = read(approved/'manifest.json')
    assert manifest['recipe_sha256'] == digest(MSP.CONFIG), 'Rebuild the approved presentation first'
    inputs = {}
    def remember(path):
        path = path.resolve()
        inputs[str(path.relative_to(ROOT))] = digest(path)
    for path in (base_path, approved/'manifest.json', args.source/'sources/legend-catalog.json', args.source/'plate-source-bibliography.json'):
        remember(path)
    selected = {}
    for r in manifest['records']:
        if r['study'] != recipe['id']:
            continue
        archive = next(f for f in r['outputs'] if f['path'].endswith('.svg.gz'))
        path = approved/archive['path']
        assert digest(path) == archive['sha256']
        data = gzip.decompress(path.read_bytes())
        assert hashlib.sha256(data).hexdigest() == r['svg_sha256']
        selected[(r['subject'], r['kind'])] = (E.fromstring(data), path, r)
        remember(path)
    subjects = config['subjects'] + recipe.get('additional_subjects', [])
    assert len(selected) == 2*len(subjects)
    catalog = {r['stem']: r for r in read(args.source/'sources/legend-catalog.json')}
    book = read(args.source/'plate-source-bibliography.json')
    entries = {r['stem']: r for r in book['entries']}
    records = []
    work = out/'sources/presentation-work'
    work.mkdir(parents=True, exist_ok=True)
    observer = None
    # Maps first: the retained Japan observer supplies its new legend keys.
    for r in sorted(base['records'], key=lambda r: r['kind'] != 'map'):
        r = copy.deepcopy(r)
        stem, scope, kind = r['stem'], r['scope'], r['kind']
        source, target = args.source/r['svg'], out/r['svg']
        remember(source)
        cached = prior.get((kind, scope, stem))
        if (stem not in subjects and theme_current and cached and cached['presentation'] == 'st2-theme'
                and cached['presentation_source_sha256'] == digest(source) and target.exists()
                and digest(target) == cached['svg_sha256']):
            cached['source'] = str(source.resolve())
            cached.pop('combined_source_sha256', None)
            records.append(cached)
            print('cached', kind, scope, stem, flush=True)
            continue
        root = None
        origin = 'st2-theme'
        if stem in subjects and (scope == 'world' or (scope == 'japan' and kind == 'legend' and not stem.endswith('observer'))):
            root = copy.deepcopy(selected[(stem, kind)][0])
            source = selected[(stem, kind)][1]
            origin = 'approved-msp-5'
            if kind == 'map':
                r['framing_adjustment'] = selected[(stem, kind)][2]['framing']
            if scope == 'japan':
                scope_note(root, 'Japan companion: '+('shared all-sky context, with the Setouchi locator on the map.' if stem.startswith('astro') else 'geographic enlargement of the same dated world observations; not a Japan-only total.')+
                           (' Starlink labels remain 6 physical pt.' if stem.endswith('global') else ''), recipe)
        elif stem in subjects and scope == 'japan' and kind == 'map':
            root = read_svg(source)
            if stem.endswith('observer'):
                observer = observer_groups(root, recipe)
                remember(ROOT/'assets.static/orbital-technosphere/20261103/orbital-technosphere-profile.json')
                origin = 'retained-setouchi-observer'
            else:
                japan_source(root, selected[(stem, 'map')][0], stem, config, recipe)
                origin = 'approved-msp-5-japan-viewport'
        elif stem.endswith('observer') and stem in subjects and scope == 'japan' and kind == 'legend':
            root = read_svg(source)
            m = copy.deepcopy(catalog[stem])
            m['keys'] = []
            for group, (bank, names, points) in observer.items():
                symbol = copy.deepcopy(next(n for n in points if n.get('data-marker-shape')))
                label = bank.get('{'+MSP.ORBITAL.INKSCAPE+'}label')+' / '+str(len(names))
                symbols = [symbol]
                if symbol.get('data-marker-shape') == 'x':
                    halo = copy.deepcopy(symbol)
                    halo.attrib.clear()
                    halo.set('d', symbol.get('d'))
                    halo.set('data-presentation-only', 'true')
                    paint(halo.attrib, fill='none', stroke_opacity=1)
                    paint(halo.attrib, stroke=recipe['halo'], stroke_width=.0243)
                    symbols.insert(0, halo)
                m['keys'].append({'label': label, 'original_label': label, 'shapes': symbols})
            m['notes'] += ['Starlink names: 6 pt; sunbursts: 1.5×. Other names remain hidden.',
                           'Black x: debris. Intelsat: square. Remaining Earth observation: triangle.',
                           'Named groups follow memberships in the retained October source. Positions and observer are unchanged.']
            for group in list(root):
                if 'legend' in group.get('id', '') and group.get('id') != 'legend-paper':
                    root.remove(group)
            root.append(LAYOUT.make_legend(m, scope, args.source))
            origin = 'retained-setouchi-observer-legend'
        audit = None
        if root is not None:
            root.set('data-atlas-source-kind', origin)
            root.set('data-legend-companion' if kind == 'map' else 'data-map-companion', stem+('-legend.svg' if kind == 'map' else '.svg'))
            if kind == 'legend':
                legend_number(root, entries[stem]['ordinal'], recipe)
                for title in root.xpath('//*[@id="msp-print-note"]/*[local-name()="text"]')[:1]:
                    title.text = 'Atlas default / '+recipe['palette']
            temporary = work/f'{kind}-{scope}-{stem}.svg'
            save(root, temporary)
            theme(temporary, target, recipe, kind, stem)
            # Both passes must conserve every coordinate, object value and label.
            assert geometry(temporary) == geometry(target), stem+' presentation changed geometry'
            temporary.unlink()
        else:
            theme(source, target, recipe, kind, stem)
            audit = geometry(source)
            assert audit == geometry(target), stem+' presentation changed geometry'
        r.update(svg_sha256=digest(target), presentation_source=str(source.resolve().relative_to(ROOT)),
                 presentation_source_sha256=digest(source), presentation=origin,
                 source=str(source.resolve()), sheet_background=recipe['background'], geometry_audit=audit)
        r.pop('combined_source_sha256', None)
        records.append(r)
        write(cache_path, {'fingerprint': fingerprint, 'records': records})
        print('styled', kind, scope, stem, flush=True)
    book['edition'] = 'Cartofreako default atlas / '+recipe['palette']
    book['palette'] = recipe
    book['prepared_on'] = STYLE['reviewed_on']
    book['note'] = 'MSP 5 presentation with the approved November world updates. Japan observer retains its October Setouchi positions. Each separate legend is the authority for its map source dates.'
    book['sources']['msp-5-approved'] = {
        'title': 'Cartofreako MSP 5 / approved map and attribution pairs',
        'url': 'https://github.com/bdekoz/cartofreako/tree/main/'+STYLE['atlas']['presentation']['approved_delivery']+'/'+recipe['directory'],
        'period': 'Groundstations: 3 November 2026. Orbital world/global Japan: 2026-11-03T17:10:00Z. Astronomy: 2026-10-29T20:00:00Z.',
        'notes': 'The linked editable legend sheets retain complete provider citations, source ledgers and processing notes. Groundstation capabilities are evidence-based proxies, not measured throughput.',
        'license': 'Underlying provider/source terms remain recorded in each legend; no new rights are implied.',
        'upstream_sha256': digest(approved/'manifest.json')}
    for entry in book['entries']:
        entry['presentation'] = recipe['palette']+f" ground {recipe['background']} / type {recipe['text']}; source data colors retained. "+entry['presentation']
        if entry['stem'] in subjects:
            if entry['stem'].endswith('observer'):
                entry['japan_source_ids'] = list(dict.fromkeys(entry['japan_source_ids']+entry['source_ids']))
            entry['source_ids'] = ['msp-5-approved']
            entry['period_and_units'] = (
                '3 November 2026 source: 590 antenna records, 66 PoPs and 124 links; aperture and capability proxies.'
                if entry['stem'] == 'network-groundstations' else
                'Celestial directions / 2026-10-29T20:00:00Z; 685 selected objects and 35 labels.'
                if entry['stem'] == 'astro-all-sky' else
                'SGP4 positions / world 2026-11-03T17:10:00Z; Japan global shares that snapshot; Japan observer retains 2026-10-29T20:00:00Z.')
            entry['method'] = 'Approved MSP 5 sheet and source ledger; see the paired legend for exact counts, units and provider citations.'
            entry['interpretation'] = 'The separate map and legend retain the reviewed source observations and capability qualifications.'
            entry.pop('class_definition', None)
            entry['japan'] = ('Retained 2026-10-29T20:00:00Z Setouchi observer, 34.45°N / 133.99°E; new presentation, unchanged positions.'
                              if entry['stem'].endswith('observer') else 'Same observations as the approved world sheet; geographic detail or shared celestial context with locator.')
    importlib.import_module('build-setouchi-bibliography').write_outputs(book, out, None)
    base.update(schema='cartofreako-default-map-legend-sheets-v1', records=records, presentation=recipe['id'])
    write(out/'sources/separate-sheets.json', base)
    write(receipt_path, {'schema': 'cartofreako-default-atlas-v1', 'fingerprint': fingerprint,
                        'palette': recipe, 'astronomy_label_font_size_pt': config['astronomy_label_font_size_pt'],
                        'inputs': [{'path': path, 'sha256': value} for path, value in sorted(inputs.items())],
                        'records': records})
    print('Composed 152 default atlas sheets / '+recipe['palette'], flush=True)


if __name__ == '__main__':
    main()
