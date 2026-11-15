#!/usr/bin/env python3
"""Freeze Cartofreako book content and invoke the generic Izzi production tool."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def value(node):
    return ' '.join(''.join(node.itertext()).split())


def crop_image(asset, label, box, frame):
    return {'asset': asset, 'crop': [round(box[0]/frame[0], 9), round(box[1]/frame[1], 9),
                                     round(box[2]/frame[0], 9), round(box[3]/frame[1], 9)], 'alt': label}


def legend_content(path, pdf_asset):
    root = E.parse(str(path)).getroot()
    frame = list(map(float, root.get('viewBox').split()))[2:]
    models = root.xpath('./*[local-name()="metadata"][@id="atlas-legend-model"]')
    if models:
        model = json.loads(models[0].text)
        group = root.xpath('./*[@id="legend"]')[0]
        labels = [node for node in group if E.QName(node).localname == 'text' and abs(float(node.get('x'))-.92) < .001]
        cursor, sections = 0, []
        for original in model['sections']:
            section = {'title': original['title'], 'paragraphs': original.get('notes', []), 'keys': []}
            for item in original.get('keys', []):
                label = item['label'] if isinstance(item, dict) else item[1]
                first = labels[cursor]
                assembled = value(first); cursor += 1
                while assembled != label and cursor < len(labels) and label.startswith(assembled):
                    assembled += ' '+value(labels[cursor]); cursor += 1
                if assembled != label:
                    raise ValueError(f'Symbol/label mismatch in {path}: {label!r} != {assembled!r}')
                y = float(first.get('y'))
                section['keys'].append({'label': label, 'image': crop_image(pdf_asset, label, [.43, y-.19, .37, .31], frame)})
            sections.append(section)
        if cursor != len(labels):
            raise ValueError('Unconsumed legend labels: '+str(path))
        if cursor == 0:
            fallback = ' '.join(value(node) for node in group if E.QName(node).localname == 'text'
                                and node.get('data-type-role') == 'body' and node.get('font-weight') != '700')
            if fallback:
                sections.insert(0, {'title': 'Legend', 'paragraphs': [fallback]})
        sections.append({'title': 'How to read this plate', 'paragraphs': model['notes']})
        sections.append({'title': 'Data sources', 'role': 'sources', 'paragraphs': model['sources']})
        return model['title'], model['subtitle'], sections, {'method': 'embedded legend model', 'model_sha256': hashlib.sha256(models[0].text.encode()).hexdigest(), 'key_count': cursor}
    # SLSL legends retain actual SVG text and symbol groups. Recover paragraphs
    # from source line spacing; never OCR a raster or infer symbol semantics.
    texts = root.xpath('.//*[local-name()="text"]')
    title, subtitle = value(texts[0]), value(texts[1])
    consumed = {texts[0], texts[1]}
    keys = []
    for symbol in root.xpath('./*[starts-with(@id,"key-")]'):
        if E.QName(symbol).localname != 'g':
            continue
        background, label_node = symbol.getprevious(), symbol.getnext()
        if E.QName(label_node).localname != 'text':
            raise ValueError('Unexpected SLSL legend symbol structure: '+str(path))
        label = value(label_node); consumed.add(label_node)
        if E.QName(background).localname == 'rect':
            box = [float(background.get(k)) for k in ('x', 'y', 'width', 'height')]
            box = [box[0]-.02, box[1]-.02, box[2]+.04, box[3]+.04]
        else:
            center = re.match(r'translate\(([-.\d]+) ([-.\d]+)\)', symbol.get('transform', ''))
            if not center:
                raise ValueError('Missing symbol center: '+str(path))
            x, y = map(float, center.groups()); box = [x-.18, y-.18, .36, .36]
        keys.append({'label': label, 'image': crop_image(pdf_asset, label, box, frame)})
    for symbol in root.xpath('./*[starts-with(@id,"aperture-key-")]'):
        label_node = symbol.getnext(); consumed.add(label_node)
        label = 'Aperture size / '+value(label_node)
        center = re.match(r'translate\(([-.\d]+) ([-.\d]+)\)', symbol.get('transform', ''))
        if not center:
            raise ValueError('Missing aperture symbol center')
        x, y = map(float, center.groups())
        keys.append({'label': label, 'image': crop_image(pdf_asset, label, [x-.41, y-.41, .82, .82], frame)})
    key_heading = next((value(n) for n in texts[2:] if float(n.get('font-size', 0)) >= .2), 'Legend')
    sections = [{'title': key_heading, 'keys': keys, 'paragraphs': []}]
    paragraphs, current, last = [], '', None
    current_title, role = 'Legend notes', None

    def flush_paragraph():
        nonlocal current
        if current:
            paragraphs.append(current); current = ''

    def flush_section():
        nonlocal paragraphs
        flush_paragraph()
        if paragraphs:
            section = {'title': current_title, 'paragraphs': paragraphs}
            if role:
                section['role'] = role
            sections.append(section)
        paragraphs = []

    footer_count = 0
    for node in texts:
        if node in consumed:
            continue
        x, y, size = (float(node.get(k)) for k in ('x', 'y', 'font-size'))
        if y > frame[1]-.6:
            footer_count += 1; continue
        text = value(node)
        if size >= .2:
            flush_section(); current_title = text
            role = 'sources' if 'source' in text.lower() else None
            last = None; continue
        if last and (abs(x-last[0]) > .2 or y-last[1] > size*1.8 or y <= last[1]):
            flush_paragraph()
        current = (current+' '+text).strip(); last = (x, y)
    flush_section()
    if not any(s.get('role') == 'sources' for s in sections):
        raise ValueError('Source section missing from '+str(path))
    return title, subtitle, sections, {'method': 'original SVG text and symbol swatches',
                                     'source_text_nodes': len(texts), 'footer_nodes_omitted': footer_count,
                                     'key_count': len(keys), 'source_date': root.get('data-calculation-or-source-date')}


def prepare(kind, destination, layout='portrait'):
    world = kind == 'world'
    base = (ROOT/'output/data-edition/20261111/atlas' if world else ROOT/'output/starlink-star-light-v3-20261109').resolve()
    source = base/('atlas-world.20261112.v3.pdf' if world else 'starlink-star-light-v3.pdf')
    stem = 'atlas-world.20261112.v3' if world else 'starlink-star-light.v3'
    if layout == 'spread':
        stem = stem.removesuffix('.v3')+'.v4'
    assets = {}
    def asset(identifier, path, expected=None):
        path = path.resolve(); checksum = digest(path)
        if expected and checksum != expected:
            raise ValueError('Source receipt mismatch: '+str(path))
        assets[identifier] = {'path': str(path), 'sha256': checksum}
        return identifier
    asset('source-book', source)
    if world:
        ledger = json.loads((base/'sources/current-books.json').read_text())
        book = next(b for b in ledger['books'] if b['scope'] == 'world')
        if assets['source-book']['sha256'] != book['sha256']:
            raise ValueError('World book changed since its receipt')
        rows = book['inputs'][1:]
        if len(rows) != 78:
            raise ValueError('World book must have 39 map/legend pairs')
        pairs = [(rows[i]['path'], rows[i+1]['path'], rows[i]['sha256'], rows[i+1]['sha256'], 'world') for i in range(0, len(rows), 2)]
        asset('source-ledger', base/'sources/current-books.json')
        asset('source-dataset', base/'sources/dataset.json')
        asset('source-bibliography', base/'sources/plate-bibliography.json')
        mobile = base/'atlas-world.20261112.v3.mobile.pdf'
        mobile_receipt = json.loads((base/'sources/atlas-world.20261112.v3.mobile.json').read_text())
        if mobile_receipt['source']['sha256'] != assets['source-book']['sha256']:
            raise ValueError('Mobile source is a different World edition')
        asset('mobile-book', mobile, mobile_receipt['output']['sha256'])
        frontmatter = subprocess.check_output(['pdftotext', '-f', '1', '-l', '2', '-layout', str(source), '-'], text=True)
        titles = [re.sub(r'^\d+\s+', '', line.strip()) for line in frontmatter.splitlines() if re.match(r'^\d\d ', line.strip())]
        if len(titles) != 39:
            raise ValueError('World contents inventory is incomplete')
        source_status = [line.strip() for line in frontmatter.split('\f')[0].splitlines() if line.strip()]
    else:
        ledger = json.loads((base/'manifest.json').read_text()); asset('source-ledger', base/'manifest.json')
        asset('input-ledger', base/'sources/input-manifest.json')
        records = ledger['records']; pairs = []
        for record in records:
            if record['kind'] != 'map':
                continue
            legend = next(r for r in records if r['kind']=='legend' and r['plate']==record['plate'] and r['scope']==record['scope'])
            a, b = record['outputs']['pdf'], legend['outputs']['pdf']
            pairs.append((a['path'], b['path'], a['sha256'], b['sha256'], record['scope']))
        if len(pairs) != 8:
            raise ValueError('Starlink book must have eight map/legend pairs')
    for role in ('Regular', 'Bold'):
        asset('font-'+role.lower(), ROOT/f'assets/fonts/atkinson-hyperlegible/AtkinsonHyperlegible-{role}.ttf')
        fallback = next(Path('/usr/share/fonts').rglob('DejaVuSans.ttf' if role=='Regular' else 'DejaVuSans-Bold.ttf'))
        asset('fallback-'+role.lower(), fallback)
    asset('cmyk-profile', Path('/usr/share/ghostscript/iccprofiles/default_cmyk.icc'))
    chapters, extraction = [], []
    for n, (map_path, legend_path, map_hash, legend_hash, scope) in enumerate(pairs):
        name = Path(map_path).stem; identifier = name+'-'+scope
        map_asset = asset(identifier+'-map', base/map_path, map_hash)
        legend_asset = asset(identifier+'-legend', base/legend_path, legend_hash)
        svg = base/str(Path(legend_path).with_suffix('.svg')).replace('/pdf/', '/svg/')
        asset(identifier+'-legend-svg', svg)
        map_svg = base/str(Path(map_path).with_suffix('.svg')).replace('/pdf/', '/svg/')
        asset(identifier+'-map-svg', map_svg)
        title, subtitle, sections, evidence = legend_content(svg, legend_asset)
        title = titles[n] if world else title+' / '+scope.upper()
        caption = 'Complete overview. Fine labels and individual marks require enlargement; use the readable key and accompanying detail views.'
        image = {'asset': map_asset, 'alt': title+'. '+subtitle+'. The legend and reading notes describe the symbols and interpretation.', 'caption': caption}
        chapter = {'id': identifier, 'title': title, 'subtitle': subtitle, 'image': image, 'sections': sections}
        if layout in ('landscape', 'spread'):
            # Keep source sections intact. These indices identify the original
            # context paragraph that must share the facing page with every key.
            context = next((i for i, section in enumerate(sections)
                            if section.get('paragraphs') and section.get('role') != 'sources'), None)
            chapter['facing_context'] = [[context, 0]] if context is not None else []
        if world:
            chapter['ebook_image'] = {**image, 'asset': 'mobile-book', 'page': 3+2*n}
        # These crops enlarge original artwork to approximately native label
        # size; full coverage is always retained in the overview above.
        if not world or name in ('astro-all-sky', 'orbital-technosphere-observer', 'cloud-atmosphere', 'network-groundstations'):
            crop = [.43, .32, .14, .32]
            detail_title = 'Enlarged detail'
            if 'astro-all-sky' in name:
                crop = [.36, .30, .14, .32]; detail_title = 'Celestial field / enlarged detail'
            elif 'groundstations' in name:
                crop = [.40, .28, .14, .32]; detail_title = 'Ground infrastructure / enlarged detail'
                if scope == 'world':
                    crop = [.65, .20, .14, .32]
            elif 'observer' in name:
                detail_title = 'Observer sky / enlarged detail'
                if world and name == 'orbital-technosphere-observer':
                    crop = [.25, .10, .10, .21]
            chapter['details'] = [{**image, 'crop': crop, 'title': detail_title,
                                   'caption': 'An enlarged section of the original artwork. The complete overview and its key retain the full context.'}]
        chapters.append(chapter)
        extraction.append({'chapter': identifier, 'legend_sha256': digest(svg), **evidence})
    title = 'Cartofreako: World Atlas' if world else 'Starlink Star Light v3'
    intro = ['This A4 edition brings the complete selected collection into a book with readable legends and source notes.',
             ('All 39 maps and companion legends from atlas-world.20261112.v3.pdf are included in their original sequence.' if world
              else 'All eight SLSL1-SLSL4 World and USA views are included, with their original companion legends.'),
             'Cartography and source selection: Cartofreako. Publication layout and digital production: Izzi.',
             'Source observation dates remain specific to each plate. An acquisition or publication date does not make historical measurements current.']
    if world:
        intro += ['Original edition frontmatter: '+ ' / '.join(source_status[:4]),
                  'Original source acquisition status: '+ '; '.join(source_status[4:])]
    else:
        intro += ['The celestial context retains the 29 October 2026 source time; orbital views use 9 November 2026 at 01:12 UTC; ground infrastructure retains the 3 November source snapshot. These dates differ from those of the World atlas.']
    manifest = {
        'schema': 'izzi-publication-v1', 'id': 'cartofreako-world-atlas' if world else 'starlink-star-light-v3',
        'metadata': {'title': title, 'subtitle': 'Maps, interpretation and sources' if world else 'Natural sky, observer sky, orbital subpoints and ground infrastructure',
                     'running_title': 'CARTOFREAKO / WORLD ATLAS' if world else 'STARLINK STAR LIGHT / v3',
                     'creator': 'Cartofreako', 'language': 'en', 'edition': 'A4 and digital edition / November 2026',
                     'modified': '2026-11-14T12:00:00Z', 'identifier': 'urn:uuid:'+str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/bdekoz/cartofreako/'+stem))},
        'fonts': {'regular': 'font-regular', 'bold': 'font-bold', 'fallback_regular': 'fallback-regular', 'fallback_bold': 'fallback-bold'}, 'cmyk_profile': 'cmyk-profile',
        'assets': assets, 'introduction': intro, 'chapter_order': [c['id'] for c in chapters], 'chapters': chapters,
        'cover_image': chapters[3]['image'] if world else chapters[4]['image'],
        'reading_guide': [
            'Begin with each complete overview, then read its key, interpretation and source notes. An overview shows the relationships across a whole plate; it does not make every label on the large original readable at book size.',
            'Read paired key entries from left to right across each row, then continue with the row below.',
            'Enlarged details come from the original artwork. The ebook supports zooming on images and changing the size of the accompanying text.',
            'Celestial maps describe directions on the sky. Observer maps describe the sky above a named local horizon. Orbital subpoint maps describe positions projected onto Earth. Ground infrastructure maps describe terrestrial facilities. These are distinct coordinate and observation contexts.',
            'Legend swatches preserve the original symbol shapes and their local background. Their text is recomposed for reading. Color may differ between a screen and a printed page.'
        ],
        'colophon': [
            'Every chapter retains its plate-specific source references and dates. Cartofreako provides the geographic content; Izzi provides the publication layout and export.',
            'Atkinson Hyperlegible typography. A4 portrait pages with white margins. Original map artwork is rasterized at approximately 300 pixels per inch at its placed size; legend and explanatory text remains live.',
            'Print artwork is converted from sRGB using the recorded Artifex CMYK SWOP profile, then limited to 240 percent total ink while retaining the black component. This can lighten saturated dark colors. A physical proof is required to judge the printed result.',
            'The digital edition uses RGB overview images with adjustable text, chapter navigation, links and image descriptions. It retains the same content selection as the print edition.',
            'Project sources: https://github.com/bdekoz/cartofreako and https://github.com/bdekoz/izzi.'
        ]
    }
    if layout == 'landscape':
        manifest['print_layout'] = 'facing-spreads-v1'
        manifest['metadata']['edition'] = 'A4 landscape and digital edition / November 2026'
        manifest['metadata']['identifier'] = 'urn:uuid:'+str(uuid.uuid5(
            uuid.NAMESPACE_URL, 'https://github.com/bdekoz/cartofreako/'+stem+'/a4-landscape-20261114'))
        manifest['introduction'][0] = 'This A4 landscape edition pairs each complete cartographic plate with a readable legend on the facing page.'
        manifest['reading_guide'][0] = 'In print, each complete map fills the safe area of an even left page; its title, primary context and complete symbol key are on the facing right page. Longer explanations, sources and enlarged details follow the pair when needed. The ebook keeps each map and its text together in one reflowable chapter.'
        manifest['reading_guide'][1] = 'Read symbol keys across each row and then down. Read explanatory text down the left column and then down the right column. Contents entries point to the map page; the facing legend repeats that reference.'
        manifest['colophon'][1] = 'Atkinson Hyperlegible typography. A4 landscape pages with white safety margins and page-count-dependent binding allowance. Each complete map is proportionally fitted to the entire safe frame, with its primary legend opposite. Original artwork is rasterized at approximately 300 pixels per inch at its placed size; legend and explanatory text remains live.'
    if layout == 'spread':
        manifest['print_layout'] = 'portrait-map-spreads-v1'
        manifest['metadata']['edition'] = 'v4 / A4 portrait spreads and digital edition / November 2026'
        manifest['metadata']['identifier'] = 'urn:uuid:'+str(uuid.uuid5(
            uuid.NAMESPACE_URL, 'https://github.com/bdekoz/cartofreako/'+stem+'/a4-portrait-spread-20261114'))
        manifest['introduction'][0] = 'This v4 edition presents each complete cartographic plate across two facing A4 portrait pages, followed by a two-page legend and source-note spread.'
        manifest['reading_guide'][0] = 'In print, each map spans an even left page and the facing odd right page. The full map is preserved at its largest proportional size across the spread, with its original background extended to the page edges. The next two facing pages contain its title, complete symbol key, interpretation and sources. The ebook keeps each complete map and its text together in one reflowable chapter.'
        manifest['reading_guide'][1] = 'Read keys across each row, then down. Read explanatory text down the left column, then down the right column. Contents entries point to the first map page. The map joins at the centre fold; a physical binding can obscure fine marks there.'
        manifest['reading_guide'][2] = 'The ebook supports zooming on complete maps and changing text size. Selected enlarged details remain in the ebook; the print edition gives each complete map a two-page spread.'
        manifest['colophon'][1] = 'Atkinson Hyperlegible typography. A4 portrait trim, 210 x 297 mm, with 3 mm bleed on every edge. Each complete map is proportionally fitted across the 420 x 297 mm spread; its dominant border background fills the remaining space. A single raster is split into matching halves with shared fold bleed. Print maps exceed 300 pixels per inch at their placed size. Legend and source text remains live within mirrored binding margins.'
        for chapter in chapters:
            chapter.setdefault('ebook_image', dict(chapter['image']))
            chapter['image']['caption'] = 'Complete map across the preceding two-page spread. Fine source labels and individual marks still require enlargement.'
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination/(stem+'.manifest.json')
    serialized = json.dumps(manifest, indent=2, ensure_ascii=False)+'\n'
    if manifest_path.exists() and manifest_path.read_text() != serialized:
        raise ValueError('Frozen manifest differs; choose a new output directory')
    manifest_path.write_text(serialized)
    (destination/(stem+'.content.json')).write_text(json.dumps({'book': title, 'source': assets['source-book'],
        'chapter_count': len(chapters), 'key_count': sum(r['key_count'] for r in extraction), 'chapters': extraction}, indent=2)+'\n')
    return manifest_path, stem


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--book', choices=['both', 'world', 'starlink'], default='both')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--layout', choices=['portrait', 'landscape', 'spread'], default='portrait')
    parser.add_argument('--profile', type=Path, help='Explicit Izzi profile; defaults to the selected layout profile')
    parser.add_argument('--izzi', type=Path, default=ROOT.parent/'izzi')
    parser.add_argument('--epubcheck', type=Path, default=ROOT/'build/pod-tools/epubcheck-5.4.0/epubcheck.jar')
    parser.add_argument('--prepare-only', action='store_true'); parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.output is None:
        args.output = ROOT/{'portrait':'output/atlas-optional-v3', 'landscape':'output/atlas-optional-v3-landscape',
                            'spread':'output/atlas-optional-v4-spread'}[args.layout]
    profile = args.profile or args.izzi.resolve()/'config/publication'/ {
        'portrait':'ingramspark-a4-20261114.json', 'landscape':'a4-landscape-facing-20261114.json',
        'spread':'a4-portrait-spread-20261114.json'}[args.layout]
    for book in ('world', 'starlink') if args.book == 'both' else (args.book,):
        manifest, stem = prepare(book, args.output.resolve()/'sources', args.layout)
        print('Prepared '+str(manifest), flush=True)
        if not args.prepare_only:
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            env['PYTHONPATH'] = str(ROOT/'build/setouchi-h3-python')+os.pathsep+env.get('PYTHONPATH', '')
            command = [sys.executable, str(args.izzi.resolve()/'scripts/build-publication.py'), 'build', str(manifest),
                       '--stem', stem, '--output', str(args.output.resolve()), '--epubcheck', str(args.epubcheck.resolve())]
            command += ['--profile', str(profile.resolve())]
            if args.resume:
                command.append('--resume')
            subprocess.run(command, check=True, env=env)


if __name__ == '__main__':
    main()
