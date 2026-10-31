"""One cyclic print frame for every world sheet, including streamed native swarms.

Only terrestrial silhouettes and their attached country fills move to the
editorial Antarctic inset. Geophysical fields, network observations and celestial
coordinates keep their source registration within the common cyclic frame.
"""
import copy
import io
from pathlib import Path
import xml.sax
from xml.sax.saxutils import XMLGenerator

from antarctica_inset import subpaths, serialize, antarctic_cap, antarctic_part
from legend_informatics import E, WIDTH, HEIGHT, XL, SUFFIX, digest, el, legend_group

SCALE = 43.5 / WIDTH
SHIFT = 4.4
DX, DY = .25, (HEIGHT - HEIGHT * SCALE) / 2
# Exactly the translation approved in the network proof. Use it for every
# layer, rather than fitting each source's differently simplified coastline.
ANTARCTIC_TRANSLATION = (-37.3872, HEIGHT - .45 - 17.0519)
LAND = {'land', 'terrestrial-land', 'petroleum-country-geometry'}
COAST = {'coastline', 'terrestrial-coastline', 'minor-islands', 'ice'}
OCEAN = {'ocean', 'bathymetry', 'bathymetry-roulette', 'bathymetry-hamonshu'}
MOVABLE = LAND | COAST | OCEAN


class Collect(xml.sax.ContentHandler):
    """Read basemap layers into memory; never retain the native swarm circles."""
    def __init__(self):
        self.depth = 0
        self.capture = None
        self.layers = {}
        self.background = '#ffffff'
        self.root = {}

    def startElement(self, name, attrs):
        a = dict(attrs)
        if not self.depth:
            self.root = a
        elif self.depth == 1:
            identifier = a.get('id', '')
            if identifier in MOVABLE or identifier.endswith('-background') or name == 'rect':
                self.capture = (identifier, name, a)
                self.buffer = io.StringIO()
                self.writer = XMLGenerator(self.buffer, encoding='utf-8')
        if self.capture:
            self.writer.startElement(name, a)
        self.depth += 1

    def characters(self, value):
        if self.capture:
            self.writer.characters(value)

    def endElement(self, name):
        self.depth -= 1
        if self.capture:
            self.writer.endElement(name)
            if self.depth == 1:
                identifier, tag, attrs = self.capture
                node = E.fromstring(self.buffer.getvalue().encode(), E.XMLParser(huge_tree=True))
                if identifier in MOVABLE:
                    self.layers[identifier] = node
                elif 'display:none' not in attrs.get('style', '').replace(' ', ''):
                    rectangle = node if tag == 'rect' else next((n for n in node if E.QName(n).localname == 'rect'), None)
                    if rectangle is not None:
                        style = dict(s.strip().split(':', 1) for s in rectangle.get('style', '').split(';') if ':' in s)
                        self.background = rectangle.get('fill', style.get('fill', self.background))
                self.capture = None


def partition(node, cap, changes):
    """Split terrestrial paths without altering a vertex or inherited style."""
    if E.QName(node).localname == 'path':
        value = node.get('d', '')
        # Curved symbol paths are not terrestrial polygon components.
        if any(c in value for c in 'AaCcQqSsTt'):
            return None
        parts = subpaths(value)
        chosen, remaining = [], []
        for points, closed in parts:
            bounded = all(35 < x < WIDTH and 9 < y < HEIGHT for x, y in points)
            (chosen if bounded and antarctic_part(points, closed, cap) else remaining).append((points, closed))
        if not chosen:
            return None
        changes.append({'id': node.get('id'), 'iso3': node.get('data-iso3'),
                        'subpaths': len(chosen), 'vertices': sum(len(p) for p, _ in chosen)})
        result = copy.deepcopy(node)
        result.set('d', serialize(chosen))
        if result.get('id'):
            result.set('id', result.get('id') + '-antarctic-inset')
        node.set('d', serialize(remaining))
        return result
    result = E.Element(node.tag, node.attrib, nsmap=node.nsmap)
    if result.get('id'):
        result.set('id', result.get('id') + '-antarctic-inset')
    result.text = node.text
    for child in node:
        piece = partition(child, cap, changes)
        if piece is not None:
            result.append(piece)
    return result if len(result) else None


class Body(xml.sax.ContentHandler):
    def __init__(self, stream, replacements):
        self.stream, self.replacements = stream, replacements
        self.writer = XMLGenerator(stream, encoding='utf-8')
        self.depth = self.skip = 0

    def startElement(self, name, attrs):
        a = dict(attrs)
        if self.depth == 0:
            self.depth += 1
            return
        identifier = a.get('id', '')
        if self.skip:
            self.skip += 1
        elif self.depth == 1 and identifier in self.replacements:
            self.stream.write(E.tostring(self.replacements[identifier], encoding='unicode'))
            self.skip = 1
        elif self.depth == 1 and (name == 'rect' or identifier.endswith('-background') or legend_group(identifier)):
            self.skip = 1
        else:
            self.writer.startElement(name, a)
        self.depth += 1

    def characters(self, value):
        if self.depth > 1 and not self.skip:
            self.writer.characters(value)

    def endElement(self, name):
        self.depth -= 1
        if self.skip:
            self.skip -= 1
        elif self.depth:
            self.writer.endElement(name)


def make_plate(source, destination, legend_name):
    source, destination = Path(source), Path(destination)
    collected = Collect()
    xml.sax.parse(str(source), collected)
    cap = antarctic_cap()
    inset = el('g', id='antarctica-consolidated-inset',
               transform=f'translate({ANTARCTIC_TRANSLATION[0]:.12g} {ANTARCTIC_TRANSLATION[1]:.12g})')
    changes = []
    for identifier, layer in collected.layers.items():
        if identifier in OCEAN:
            continue
        piece = partition(layer, cap, changes=changes)
        if piece is not None:
            inset.append(piece)
    if collected.layers.keys() & LAND and not len(inset):
        raise ValueError('A world terrestrial layer must yield the Antarctic inset')
    infill = None
    reference_sha256 = None
    if collected.layers.keys() & OCEAN:
        # Ocean polygons encode land as negative space. Close that negative
        # silhouette explicitly; do not delete depth contours or ocean rings.
        reference = Collect()
        earth = source.parent / ('earth' + SUFFIX + '.svg')
        reference_sha256 = digest(earth)
        xml.sax.parse(str(earth), reference)
        land = partition(reference.layers['land'], cap, changes=[])
        land.set('id', 'antarctica-source-infill-shape')
        infill = el('g', id='antarctica-source-infill', data_presentation_only='true',
                    data_note='Editorial ocean backing for displaced Antarctic silhouette; not measured depth')
        ocean = next(layer for identifier, layer in collected.layers.items() if identifier in OCEAN)
        first = next(ocean.iter('path'))
        style = dict(s.strip().split(':', 1) for s in first.get('style', '').split(';') if ':' in s)
        color = first.get('fill', style.get('fill', '#9faac3'))
        opacity = float(first.get('fill-opacity', style.get('fill-opacity', '1')))
        if opacity == 0 or color == 'none':
            # Hamonshu is drawn with strokes; its invisible placeholder fill
            # is nearly black and must not become the editorial ocean color.
            color = first.get('stroke', style.get('stroke', '#9faac3'))
            opacity = float(first.get('stroke-opacity', style.get('stroke-opacity', '1')))
        for path in land.iter('path'):
            d = path.get('d')
            path.attrib.clear()
            path.attrib.update({'d': d, 'fill': color, 'stroke': color, 'stroke-width': '.006', 'fill-rule': 'evenodd'})
            if opacity != 1:
                path.set('fill-opacity', str(opacity));path.set('stroke-opacity', str(opacity))
        infill.append(land)
        if not len(inset):
            # Decorative bathymetry studies use the same displaced land void.
            silhouette = copy.deepcopy(land)
            silhouette.set('id', 'antarctica-reference-silhouette')
            for path in silhouette.iter('path'):
                path.set('fill', '#ffffff');path.set('stroke', '#ffffff')
                if opacity != 1:
                    path.set('fill-opacity', '1');path.set('stroke-opacity', '1')
            inset.append(silhouette)
    doc = el('svg', width='44in', height=f'{HEIGHT}in', viewBox=f'0 0 {WIDTH} {HEIGHT}', role='img',
             data_framing_variant='cyclic-43p5-antarctica-left', data_source_sha256=digest(source),
             data_legend_style='separate-sheet', data_legend_companion=legend_name,
             data_image_width_in='43.5', data_cyclic_shift_in=SHIFT)
    el('rect', doc, id='st2-sheet-paper', width=WIDTH, height=HEIGHT, fill='white')
    defs = el('defs', doc)
    defs.append(E.Comment('SOURCE-CARTOGRAPHY'))
    clip = el('clipPath', defs, id='cyclic-frame', clipPathUnits='userSpaceOnUse')
    el('rect', clip, width=WIDTH, height=HEIGHT)
    frame = el('g', doc, id='st2-image-frame', transform=f'translate({DX} {DY}) scale({SCALE})')
    el('rect', frame, id='st2-image-background', width=WIDTH, height=HEIGHT, fill=collected.background)
    plot = el('g', frame, id='st2-image-window', clip_path='url(#cyclic-frame)')
    for offset in (SHIFT-WIDTH, SHIFT, SHIFT+WIDTH):
        use = el('use', plot, transform=f'translate({offset} 0)')
        use.set('{'+XL+'}href', '#source-cartography')
    if len(inset):
        frame.append(inset)
    prefix, suffix = E.tostring(doc, encoding='unicode').split('<!--SOURCE-CARTOGRAPHY-->')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.svg.tmp')
    with temporary.open('w') as stream:
        stream.write(prefix + '<g id="source-cartography">')
        if infill is not None:
            stream.write(E.tostring(infill, encoding='unicode'))
        xml.sax.parse(str(source), Body(stream, collected.layers))
        stream.write('</g>' + suffix)
    temporary.replace(destination)
    return {'variant': 'cyclic-43p5-antarctica-left', 'scale': SCALE, 'shift': SHIFT, 'offset': 0,
            'translation_inches': [DX, DY], 'sheet_inches': [WIDTH, HEIGHT],
            'image_inches': [43.5, HEIGHT*SCALE], 'cyclic_move_on_sheet_inches': SHIFT*SCALE,
            'all_artwork_scaled_proportionally': True, 'legend_included': False,
            'non_terrestrial_data_coordinates_unchanged': True,
            'editorial_land_reference_sha256': reference_sha256,
            'antarctica_adjustment': {'translation_source_inches': list(ANTARCTIC_TRANSLATION),
                                     'present': bool(len(inset)), 'changed_paths': changes,
                                     'scope': 'terrestrial silhouettes, coastlines, ice and attached country fills; editorial ocean backing closes the old land void'}}
