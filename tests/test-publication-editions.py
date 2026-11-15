#!/usr/bin/env python3
"""Content integration checks for the two frozen Cartofreako publications."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as E
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('book_adapter', ROOT/'scripts/build-publication-editions.py')
adapter = importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)


def normalize(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text))


def check_source_chapter(data, chapter):
    source_lines = 0
    svg_path = Path(data['assets'][chapter['id']+'-legend-svg']['path'])
    source_title, source_subtitle, source_sections, _ = adapter.legend_content(svg_path, chapter['id']+'-legend')
    assert source_sections == chapter['sections'], ('Source legend changed or text extraction differs', chapter['id'])
    # Every visible source-text line, except sheet furniture and the
    # separately recorded source title/subtitle, must survive extraction.
    svg = adapter.E.parse(str(svg_path)).getroot()
    frame_h = float(svg.get('viewBox').split()[3])
    source_texts = svg.xpath('.//*[local-name()="text"]')
    recovered = normalize(source_title+' '+source_subtitle+' '+' '.join(
        s['title']+' '+' '.join(s.get('paragraphs', []))+' '+' '.join(k['label'] for k in s.get('keys', []))
        for s in source_sections))
    for node in source_texts:
        value = adapter.value(node)
        if (float(node.get('y', '0')) > frame_h-.6 or value in ('Legend', 'How to read this plate (continued)')
                or node.get('data-type-role') == 'footer'):
            continue
        # A3 repeats the section heading before every note. The book
        # places that same heading once above its complete paragraphs.
        for section in source_sections:
            if value.startswith(section['title']+': '):
                value = value[len(section['title'])+2:]
                break
        # Wrapped source lines are fragments of reconstructed prose.
        assert normalize(value) in recovered, ('Unrepresented SVG text', chapter['id'], value)
        source_lines += 1
    return source_lines


def check_book(directory, stem, count):
    manifest_path = directory/'sources'/(stem+'.manifest.json')
    data = json.loads(manifest_path.read_text())
    receipt = json.loads((directory/'validation'/(stem+'.json')).read_text())
    assert len(data['chapters']) == count
    assert data['chapter_order'] == receipt['chapter_order']
    assert adapter.digest(manifest_path) == receipt['identity']['manifest_sha256']
    assert len(set(data['chapter_order'])) == count
    for item in receipt['outputs'].values():
        assert adapter.digest(directory/item['path']) == item['sha256'], item['path']
    for item in data['assets'].values():
        assert adapter.digest(Path(item['path'])) == item['sha256'], item['path']
    pages = receipt['layout']['chapter_pages']
    placements = receipt['layout']['placements']
    for item in placements:
        assert min(item['ppi']) >= 299, item
        x, y, w, h = item['box_points']
        left = (20 if item['page'] % 2 else 15)*72/25.4
        assert x >= left-.02 and x+w <= left+175*72/25.4+.02
        assert y >= 20*72/25.4-.02 and y+h <= 277*72/25.4+.02
    checked_paragraphs, checked_keys, source_lines = 0, 0, 0
    with zipfile.ZipFile(directory/receipt['outputs']['epub']['path']) as epub:
        chapter_names = [n for n in epub.namelist() if n.startswith('EPUB/chapter-')]
        assert len(chapter_names) == count
        for number, chapter in enumerate(data['chapters']):
            start = pages[chapter['id']]
            end = pages[data['chapters'][number+1]['id']]-1 if number+1<count else receipt['layout']['pages']
            text = subprocess.check_output(['pdftotext', '-f', str(start), '-l', str(end),
                                             str(directory/receipt['outputs']['print']['path']), '-'], text=True)
            lines = [line for line in text.splitlines() if line.strip() != data['metadata']['running_title'] and not re.fullmatch(r'\d+', line.strip())]
            pdf_text = normalize(' '.join(lines))
            document = E.fromstring(epub.read('EPUB/chapter-'+chapter['id']+'.xhtml'))
            ebook_text = normalize(' '.join(document.itertext()))
            assert normalize(chapter['title']) in pdf_text and normalize(chapter['title']) in ebook_text
            paragraphs = [p for section in chapter['sections'] for p in section.get('paragraphs', [])]
            keys = [k['label'] for section in chapter['sections'] for k in section.get('keys', [])]
            for text in paragraphs+keys:
                assert normalize(text) in pdf_text, ('Missing print text', chapter['id'], text)
                assert normalize(text) in ebook_text, ('Missing EPUB text', chapter['id'], text)
            checked_paragraphs += len(paragraphs); checked_keys += len(keys)
            source_lines += check_source_chapter(data, chapter)
    return {'book': stem, 'chapters': count, 'paragraphs': checked_paragraphs, 'keys': checked_keys,
            'source_svg_text_lines': source_lines, 'placed_image_ppi_and_margins': 'pass',
            'print_and_epub_text_coverage': 'pass', 'source_hashes': 'pass'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'output/atlas-optional-v3')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--sources-only', action='store_true')
    args = parser.parse_args()
    inventory = [('atlas-world.20261112.v3', 39), ('starlink-star-light.v3', 8)]
    if args.sources_only:
        results = []
        for stem, count in inventory:
            data = json.loads((args.output/'sources'/(stem+'.manifest.json')).read_text())
            assert len(data['chapters']) == count
            results.append({'book': stem, 'chapters': count, 'source_svg_text_lines': sum(check_source_chapter(data, c) for c in data['chapters'])})
    else:
        results = [check_book(args.output.resolve(), stem, count) for stem, count in inventory]
    text = json.dumps({'schema': 'cartofreako-publication-validation-v1', 'books': results}, indent=2)+'\n'
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True); args.report.write_text(text)


if __name__ == '__main__':
    main()
