"""A3 companion sheets: physical type, source-preserving keys and three sections."""
from copy import deepcopy
import html
import importlib
import json

from lxml import etree as E
from reportlab.pdfbase import pdfmetrics

from legend_informatics import el, register_fonts

WIDTH, HEIGHT = 420 / 25.4, 297 / 25.4
PAPER, INK = '#fcc553', '#240413'
SECTIONS = ('Legend', 'Data sources', 'How to read this plate')


def wrap(value, points, width, bold=False):
    font = 'Atkinson-Bold' if bold else 'Atkinson-Regular'
    fits = lambda s: pdfmetrics.stringWidth(s, font, points) / 72 <= width
    lines, line = [], ''
    for word in str(value).split():
        if line and not fits(line + ' ' + word):
            lines.append(line)
            line = ''
        while not fits(word):
            cut = len(word) - 1
            while cut and not fits(word[:cut]):
                cut -= 1
            if not cut:
                raise ValueError('Column is narrower than a glyph')
            lines.append(word[:cut])
            word = word[cut:]
        line = (line + ' ' + word).strip()
    if line:
        lines.append(line)
    return lines


def text(parent, x, y, value, points=11, bold=False, role='body'):
    node = el('text', parent, x=x, y=y, font_family='Atkinson Hyperlegible',
              font_size=points / 72, font_weight='700' if bold else '400', fill=INK,
              data_type_role=role, data_font_size_pt=points)
    node.text = str(value)
    return node


def native_content(group):
    """Recover exact key labels/shapes and prose, without source font transforms."""
    revised = importlib.import_module('revise-setouchi-plates')
    keys, notes = revised.legend_content(group)
    return ([{'label': k['label'], 'symbols': [E.tostring(s, encoding='unicode') for s in k['shapes']]}
             for k in keys], notes)


def _symbol(parent, item, x, y, index):
    revised = importlib.import_module('revise-setouchi-plates')
    if isinstance(item, dict):
        nodes = [E.fromstring(value.encode()) for value in item['symbols']]
        bounds = [revised.shape_bounds(n) for n in nodes]
        x0, y0 = min(b[0] for b in bounds), min(b[1] for b in bounds)
        x1, y1 = max(b[2] for b in bounds), max(b[3] for b in bounds)
        scale = min(.30 / max(x1-x0, .001), .22 / max(y1-y0, .001))
        group = el('g', parent, id=f'legend-symbol-{index}',
                   transform=f'translate({x+.16} {y-.045}) scale({scale}) translate({-(x0+x1)/2} {-(y0+y1)/2})')
        for node in nodes:
            for child in node.iter():
                child.attrib.pop('id', None)
            group.append(node)
        return item['label']
    color, label = item[:2]
    shape = item[2] if len(item) > 2 else 'rect'
    if shape == 'outline':
        el('rect', parent, x=x, y=y-.15, width=.32, height=.23, fill='none', stroke=color, stroke_width=.025)
    elif shape == 'circle':
        el('circle', parent, cx=x+.16, cy=y-.04, r=.115, fill=color)
    elif shape == 'triangle':
        el('polygon', parent, points=f'{x+.16},{y-.17} {x},{y+.07} {x+.32},{y+.07}', fill=color)
    elif shape == 'line':
        el('line', parent, x1=x, x2=x+.32, y1=y-.04, y2=y-.04, stroke=color, stroke_width=.025)
    else:
        el('rect', parent, x=x, y=y-.15, width=.32, height=.23, fill=color)
    return label


def legend(stem, title, subtitle, sections, notes, sources, *, observer=None, scope=None):
    # Accept observer from retained pre-removal models without rendering or
    # serializing it again during a legend-only refresh.
    register_fonts()
    scope = scope or next((v for v in ('japan', 'india', 'world') if v in subtitle.lower()), 'world')
    if not sources:
        raise ValueError('A plate-specific bibliography is required: ' + stem)
    model = dict(stem=stem, title=title, subtitle=subtitle, sections=sections, notes=notes,
                 sources=sources, scope=scope)
    root = el('svg', width='420mm', height='297mm', viewBox=f'0 0 {WIDTH} {HEIGHT}', role='img',
              data_canonical_plate_id=stem, data_sheet_kind='legend', data_legend_style='a3-v3',
              data_sheet_background=PAPER, data_palette_reversed='true')
    el('title', root).text = title + ' / legend and data sources'
    el('metadata', root, id='atlas-legend-model').text = json.dumps(model, ensure_ascii=False)
    el('rect', root, id='legend-paper', width=WIDTH, height=HEIGHT, fill=PAPER)
    y = .65
    for line in wrap(title, 27, WIDTH-.9, True):
        text(root, .45, y, line, 27, True, 'title')
        y += .43
    for line in wrap(subtitle, 12, WIDTH-.9):
        text(root, .45, y, line, 12, role='subtitle')
        y += .23
    top = max(1.65, y+.30)
    col = (WIDTH-1.30)/3
    xs = [.45, .65+col, .85+2*col]
    bottom = HEIGHT-.65

    def paragraph(parent, x, y, value, width=col, points=11, bold=False, role='body'):
        rows = wrap(value, points, width, bold)
        for line in rows:
            text(parent, x, y, line, points, bold, role)
            y += points/72*1.35
        return y+.11

    def heading(parent, x, y, value):
        return paragraph(parent, x, y, value, points=15, bold=True, role='heading')+.12

    key = el('g', root, id='legend', data_section='Legend')
    y = heading(key, xs[0], top, 'Legend')
    how = list(notes)
    count = 0
    for section in sections:
        if section.get('keys'):
            y = paragraph(key, xs[0], y, section['title'], points=11, bold=True)+.08
            for item in section['keys']:
                label = _symbol(key, item, xs[0], y, count)
                count += 1
                y = paragraph(key, xs[0]+.47, y, label, width=col-.47)-.015
        how.extend(section['title'] + ': ' + p for p in section.get('notes', []))
    if not count:
        y = paragraph(key, xs[0], y, 'The companion map uses the geographic or celestial features described in the reading notes. No quantitative class key is supplied by this source.')
    if y > bottom:
        raise ValueError(f'Legend keys exceed A3: {stem}, {y:.2f}')

    bibliography = el('g', root, id='data-sources', data_section='Data sources')
    source_y = heading(bibliography, xs[2], top, 'Data sources')
    for source in sources:
        source_y = paragraph(bibliography, xs[2], source_y, source, points=10.5, role='source')
    if source_y > bottom:
        raise ValueError(f'Data bibliography exceeds A3: {stem}, {source_y:.2f}')
    reading = el('g', root, id='how-to-read', data_section='How to read this plate')
    y = heading(reading, xs[1], top, 'How to read this plate')
    x = xs[1]
    for value in how or ['Use the separate data bibliography to distinguish the source reference period from the dataset acquisition date.']:
        needed = len(wrap(value, 11, col))*11/72*1.35+.11
        if y+needed > bottom and x == xs[1]:
            x, y = xs[2], source_y+.3
            y = heading(reading, x, y, 'How to read this plate (continued)')
        y = paragraph(reading, x, y, value)
        if y > bottom:
            raise ValueError(f'Reading notes exceed A3: {stem}, {y:.2f}')
    text(root, .45, HEIGHT-.3, f'CARTOFREAKO / {scope.upper()} / LEGEND AND DATA SOURCES / A3 LANDSCAPE / 420 x 297 mm', 9, role='footer')
    return root


def validate_legend(root):
    register_fonts()
    width, height = root.get('width'), root.get('height')
    def mm(value):
        return float(value[:-2])*25.4 if value.endswith('in') else float(value[:-2])
    if abs(mm(width)-420) > .001 or abs(mm(height)-297) > .001:
        raise ValueError('Legend must be landscape A3')
    if root.get('data-palette-reversed') != 'true':
        raise ValueError('Legend must use the reversed palette')
    papers = root.xpath('./*[local-name()="rect"]')
    if not papers or papers[0].get('fill') != PAPER:
        raise ValueError('Legend paper must use the light palette color')
    labels = {' '.join(''.join(n.itertext()).split()) for n in root.xpath('//*[local-name()="text"]')}
    if (root.get('data-observer-notes') is not None or
            root.xpath('//*[@id="observer-note" or @id="observer-notes"]') or
            any(label.lower() in ('observer note', 'observer notes') for label in labels)):
        raise ValueError('Legend must not contain an Observer note section')
    if not set(SECTIONS).issubset(labels):
        raise ValueError('Legend is missing a required section: ' + str(set(SECTIONS)-labels))
    for node in root.xpath('//*[local-name()="text"]'):
        if node.get('font-family') != 'Atkinson Hyperlegible' or node.get('fill') != INK:
            raise ValueError('Legend text must use Atkinson Hyperlegible in wine')
        if any(parent.get('transform') for parent in node.iterancestors()):
            raise ValueError('Legend typography must not inherit scale transforms')
        points = float(node.get('font-size'))*72
        if min(abs(points-size) for size in (9,10.5,11,12,15,27)) > 1e-6:
            raise ValueError('Legend type falls outside the approved physical scale')
        value = ' '.join(''.join(node.itertext()).split())
        width = pdfmetrics.stringWidth(value,'Atkinson-Bold' if node.get('font-weight')=='700' else 'Atkinson-Regular',points)/72
        x,y = float(node.get('x')),float(node.get('y'))
        if node.get('text-anchor')=='middle':x-=width/2
        elif node.get('text-anchor')=='end':x-=width
        if x < 0 or x+width > WIDTH+.001 or y-points/72 < 0 or y > HEIGHT:
            raise ValueError('Legend text crosses its page: '+value)
    return True


def update_a3_sources(root, sources):
    """Retain the accepted v3 symbols and reading notes; supply bound citations."""
    register_fonts()
    remove_observer_note(root)
    names = {'Symbols / full source population':'Legend',
             'How to read the plate':'How to read this plate', 'Sources / calculation':'Data sources'}
    for node in root.xpath('//*[local-name()="text"]'):
        if node.text in names:
            node.text = names[node.text]
    col = (WIDTH-1.3)/3
    x = .85+2*col
    for group in root.xpath('./*[@id="data-sources"]'):
        root.remove(group)
    for node in list(root):
        if E.QName(node).localname == 'text' and float(node.get('x','0')) >= x-.001:
            root.remove(node)
    group = el('g', root, id='data-sources', data_section='Data sources')
    text(group, x, 1.65, 'Data sources', 15, True, 'heading')
    y = 2.05
    for source in sources:
        for line in wrap(source, 10.5, col):
            text(group, x, y, line, 10.5, role='source')
            y += 10.5/72*1.35
        y += .12
    if y > HEIGHT-.65:
        raise ValueError('A3 source bibliography overflow')
    root.set('data-legend-style','a3-v3')
    root.set('data-sheet-background', PAPER)
    return root


def remove_observer_note(root):
    """Remove the retained SLSL section and close its gap without scaling type."""
    root.attrib.pop('data-observer-notes', None)
    for group in root.xpath('//*[@id="observer-note" or @id="observer-notes"]'):
        group.getparent().remove(group)
    headings = [node for node in root.xpath('./*[local-name()="text"]')
                if (node.text or '').lower() in ('observer note', 'observer notes')]
    for heading in headings:
        x, top = float(heading.get('x')), float(heading.get('y'))
        root.remove(heading)
        reading = [node for node in root.xpath('./*[local-name()="text"]')
                   if node.text in ('How to read the plate', 'How to read this plate')
                   and abs(float(node.get('x'))-x) < .001]
        if reading:
            start = float(reading[0].get('y'))
            for node in root.xpath('./*[local-name()="text"]'):
                if abs(float(node.get('x'))-x) < .001 and float(node.get('y')) >= start:
                    node.set('y', str(float(node.get('y'))-start+top))
    return root
