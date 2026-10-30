#!/usr/bin/env python3
"""Assemble the reviewed index and linked documents into a vector study PDF.

Dependencies: reportlab, beautifulsoup4, markdown, pdfrw, pypdf.
Run from the repository root; optionally supply task-local dependencies with
PYTHONPATH. No source data are downloaded or recalculated.
"""
from __future__ import annotations

import ast
import hashlib
import io
import json
import re
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

import markdown
from bs4 import BeautifulSoup
from pdfrw import PdfReader as FormReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl
from pypdf import PdfReader, PdfWriter
from pypdf._configuration import overwrite_configuration
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle

# The audited native swarm contains a 256 MB compressed vector stream.
overwrite_configuration(maximum_declared_stream_length=512_000_000)

OUT = Path(__file__).resolve().parents[1]
REPO = OUT.parents[1]
DEST = OUT / 'setouchi-tri-explore-v1.pdf'
W, H = A4
MARGIN = 36
WIDTH = W - 2 * MARGIN
INK = colors.HexColor('#17212b')
BLUE = colors.HexColor('#155b91')
MUTED = colors.HexColor('#52616d')
LIGHT = colors.HexColor('#d9e1e7')
FONTDIR = Path('/usr/share/fonts/liberation-sans-fonts')
for name, file in [('Atlas', 'Regular'), ('Atlas-Bold', 'Bold'), ('Atlas-Italic', 'Italic')]:
    pdfmetrics.registerFont(TTFont(name, str(FONTDIR / f'LiberationSans-{file}.ttf')))
pdfmetrics.registerFontFamily('Atlas', normal='Atlas', bold='Atlas-Bold', italic='Atlas-Italic')

BODY = ParagraphStyle('body', fontName='Atlas', fontSize=10, leading=14,
                      textColor=INK, spaceAfter=8, splitLongWords=True)
SMALL = ParagraphStyle('small', parent=BODY, fontSize=9, leading=12, spaceAfter=6)
TITLE = ParagraphStyle('title', parent=BODY, fontName='Atlas-Bold', fontSize=23,
                       leading=28, spaceAfter=16, keepWithNext=True)
HEADING = ParagraphStyle('heading', parent=BODY, fontName='Atlas-Bold', fontSize=14,
                         leading=19, spaceBefore=14, spaceAfter=8, keepWithNext=True)
TABLE = ParagraphStyle('table', parent=SMALL, fontSize=9, leading=12, spaceAfter=0)


def paragraph(c, text, x, top, width=WIDTH, style=BODY):
    p = Paragraph(text, style)
    _, height = p.wrap(width, H)
    p.drawOn(c, x, top - height)
    return top - height


def chrome(c, title):
    c.setFillColor(MUTED)
    c.setFont('Atlas', 8)
    c.drawString(MARGIN, H - 27, 'CARTOFREAKO / SETOUCHI 2028 / ' + title.upper())
    c.setStrokeColor(LIGHT)
    c.line(MARGIN, 35, W - MARGIN, 35)
    c.setFont('Atlas', 8)
    c.drawString(MARGIN, 22, 'Exploration edition v1 / prepared 29 October 2026')


def html_inline(tag):
    html = tag.decode_contents()
    html = re.sub(r'<code>(.*?)</code>', r'<font name="Atlas">\1</font>', html, flags=re.S)
    html = html.replace('<strong>', '<b>').replace('</strong>', '</b>')
    html = html.replace('<em>', '<i>').replace('</em>', '</i>')
    return html


def markdown_pdf(text, path, section):
    soup = BeautifulSoup(markdown.markdown(text, extensions=['tables']), 'html.parser')
    flow = []
    for tag in soup.children:
        if not getattr(tag, 'name', None):
            continue
        if tag.name in ('h1', 'h2', 'h3'):
            flow.append(Paragraph(html_inline(tag), TITLE if tag.name == 'h1' else HEADING))
        elif tag.name == 'p':
            flow.append(Paragraph(html_inline(tag), BODY))
        elif tag.name in ('ol', 'ul'):
            for n, item in enumerate(tag.find_all('li', recursive=False), 1):
                prefix = f'{n}. ' if tag.name == 'ol' else '• '
                flow.append(Paragraph(escape(prefix) + html_inline(item), BODY))
        elif tag.name == 'table':
            rows = [[Paragraph(html_inline(cell), TABLE) for cell in row.find_all(['td', 'th'])]
                    for row in tag.find_all('tr')]
            widths = [130, WIDTH - 130] if len(rows[0]) == 2 else [WIDTH / len(rows[0])] * len(rows[0])
            table = LongTable(rows, colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eaf0f5')),
                ('LINEBELOW', (0, 0), (-1, -1), 0.35, LIGHT),
                ('LEFTPADDING', (0, 0), (-1, -1), 7),
                ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            flow.extend([table, Spacer(1, 12)])
        else:
            raise ValueError(f'Unsupported source element: {tag.name}')
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=MARGIN,
                            rightMargin=MARGIN, topMargin=55, bottomMargin=49,
                            title=section, author='Cartofreako')
    doc.build(flow, onFirstPage=lambda c, d: chrome(c, section),
              onLaterPages=lambda c, d: chrome(c, section))
    return len(PdfReader(path).pages)


def clean_note(note):
    match = re.match(r'Local snapshot: (\{.*?\})\. (.*)', note)
    if not match:
        return note
    meta = ast.literal_eval(match[1])
    parts = [f"Source snapshot: {meta['as_of_utc'][:10]}."]
    if meta.get('data_through'):
        parts.append(f"Data through {meta['data_through']}.")
    parts.append('Partial year.' if meta.get('partial_year') else 'Complete calendar-year field.')
    return ' '.join(parts) + ' ' + match[2]


def main():
    soup = BeautifulSoup((OUT / 'index.html').read_text(), 'html.parser')
    plates = json.loads((OUT / 'sources/generation-plan.json').read_text())['plates']
    companions = {p['stem']: p for p in json.loads((OUT / 'sources/japan-companions.json').read_text())}
    options = {o['id']: o for o in json.loads((OUT / 'proposal/options.json').read_text())}
    articles = soup.select('#plates article')
    plate_count = len(plates)
    if plate_count != 38 or len(plates) != len(articles):
        raise ValueError('The verified index must contain exactly 38 paired plates.')
    catalogs = [(OUT / a['href'], options[Path(a['href']).name[:2]])
                for a in soup.select('.catalogs a')]
    if len(catalogs) != 9:
        raise ValueError('Expected all nine linked catalogs.')
    inputs = [OUT / 'index.html', OUT / 'sources/generation-plan.json',
              OUT / 'sources/japan-companions.json', OUT / 'proposal/options.json',
              OUT / 'sources/data-quality.md',
              REPO / 'docs/pages/data/anthropocene-particulate.md',
              REPO / 'docs/development/20261029_setouchi_triennale_explore.md']
    with tempfile.TemporaryDirectory(prefix='cartofreako-aggregate-') as temporary:
        temp = Path(temporary)
        notes = temp / 'notes.pdf'
        reviews = temp / 'reviews.pdf'
        markdown_pdf((OUT / 'sources/data-quality.md').read_text(), notes, 'Source periods and interpretation')
        plan = inputs[-1].read_text()
        review = plan.split('## Human-gated reviews and next steps\n', 1)[1]
        review = review.split('\nNo application, payment, outreach,', 1)[0]
        markdown_pdf('# Human reviews and next steps\n' + review, reviews, 'Human reviews and next steps')

        sections = []
        page = plate_count + 4
        for path, option in catalogs:
            count = len(PdfReader(path).pages)
            if count != 4:
                raise ValueError(f'Unexpected catalog length: {path}')
            sections.append(dict(title=option['id'] + ' / ' + option['title'],
                                 path=path, page=page, count=count, kind='catalog'))
            page += count
        for title, path, kind in [
            ('Shared Sea Atlas / application draft', OUT / 'proposal/shared-sea-atlas_application-draft.pdf', 'application'),
            ('Atlas contact sheets', OUT / 'proposal/atlas-contact-sheets.pdf', 'contacts'),
            ('Petroleum source annex', OUT / 'proposal/petroleum-source-annex.pdf', 'petroleum'),
            ('Visual revisions, colour key and coral prototypes', OUT / 'proposal/visual-revisions-and-coral-prototypes.pdf', 'visual-revisions'),
            ('Source periods and interpretation', notes, 'notes'),
            ('Human reviews and next steps', reviews, 'reviews'),
        ]:
            count = len(PdfReader(path).pages)
            sections.append(dict(title=title, path=path, page=page, count=count, kind=kind))
            page += count
        total = page - 1

        base = temp / 'overview-and-atlas.pdf'
        c = canvas.Canvas(str(base), pagesize=A4, pageCompression=1)
        forms = {}

        def draw_plate(path, x, y, width):
            if path not in forms:
                # Cairo inserts PDF dictionary comments that pdfrw's older
                # parser misreads as names. Re-serialize dictionaries with
                # pypdf while retaining the original compressed vector streams.
                normalized = io.BytesIO()
                normalizer = PdfWriter()
                normalizer.append(path, import_outline=False)
                normalizer.write(normalized)
                source = FormReader(fdata=normalized.getvalue())
                if len(source.pages) != 1:
                    raise ValueError(f'Expected a one-page plate: {path}')
                forms[path] = pagexobj(source.pages[0])
                inputs.append(path)
            form = forms[path]
            scale = width / float(form.BBox[2] - form.BBox[0])
            c.saveState()
            c.translate(x, y)
            c.scale(scale, scale)
            c.doForm(makerl(c, form))
            c.restoreState()

        chrome(c, 'Complete exploration')
        paragraph(c, 'Cartofreako<br/>Setouchi 2028', MARGIN, 756,
                  style=ParagraphStyle('cover', parent=TITLE, fontSize=39, leading=45))
        paragraph(c, 'An atlas, nine show concepts and an application draft', MARGIN, 642,
                  style=ParagraphStyle('deck', parent=BODY, fontSize=17, leading=23))
        earth = OUT / 'plates/world/pdf/earth-authagraph-44-19.052559.pdf'
        draw_plate(earth, MARGIN, 363, WIDTH)
        paragraph(c, f'<b>{plate_count} world plates · {plate_count} Japan companions · 9 show catalogs</b>', MARGIN, 340)
        paragraph(c, 'Recommended proposal: <b>Shared Sea Atlas</b>, an indoor exhibition '
                  'to develop with an Awashima host for autumn 2028.', MARGIN, 302)
        paragraph(c, 'This volume brings the visual index and its linked presentation documents '
                  'together. Maps retain their vector artwork for zooming. The source and review '
                  'sections preserve the dates, limits and decisions still needed.', MARGIN, 248)
        paragraph(c, 'The application draft is eight A4 pages, leaving space for verified CV and '
                  'prior work within the ten-page application limit. This aggregate is an '
                  'exploration document; select and finalize a separate application packet.', MARGIN, 177)
        paragraph(c, 'Study edition / v1 / 29 October 2026', MARGIN, 103, style=SMALL)
        c.showPage()

        chrome(c, 'Contents')
        paragraph(c, 'Contents', MARGIN, 779, style=TITLE)
        y = paragraph(c, 'Page numbers refer to this volume. PDF bookmarks navigate to every '
                      'map pair, catalog and supporting document.', MARGIN, 732) - 20

        def toc_line(label, first, last=None):
            nonlocal y
            c.setFillColor(INK)
            c.setFont('Atlas', 10.5)
            c.drawString(MARGIN, y, label)
            c.setFillColor(BLUE)
            c.drawRightString(W - MARGIN, y, str(first) + (f'–{last}' if last and last != first else ''))
            y -= 25

        toc_line('Plate index', 3)
        toc_line(f'World / Japan atlas — all {plate_count} pairs', 4, plate_count + 3)
        y -= 10
        for sec in sections:
            toc_line(sec['title'], sec['page'], sec['page'] + sec['count'] - 1)
            if sec['kind'] == 'catalog' and sec['title'].startswith('V3'):
                y -= 10
        paragraph(c, '<b>Reading the maps.</b> Full masters measure 44 × 19.052559 inches. '
                  'These reduced study pages retain vectors; zoom to inspect small legend text. '
                  'Country totals do not resolve individual islands. Missing values are not zero. '
                  'Observation periods vary; OPEC future values are projections.', MARGIN, y - 8, style=SMALL)
        c.showPage()

        chrome(c, 'Plate index')
        paragraph(c, 'World / Japan pairs', MARGIN, 779, style=TITLE)
        paragraph(c, 'Each page pairs a world plate with its Japan companion and source note. '
                  'Celestial companions use sky context or a Setouchi observer reference.', MARGIN, 730)
        col_width = (WIDTH - 26) / 2
        for i, plate in enumerate(plates):
            col, row = divmod(i, 19)
            x, top = MARGIN + col * (col_width + 26), 661 - row * 30
            label = f"<b>{i+1:02}</b> {escape(plate['title'])}"
            paragraph(c, label, x, top, col_width - 27, SMALL)
            c.setFillColor(BLUE)
            c.setFont('Atlas', 9)
            c.drawRightString(x + col_width, top - 10, str(i + 4))
        c.showPage()

        for i, (plate, article) in enumerate(zip(plates, articles), 1):
            if article.h3.get_text() != plate['title']:
                raise ValueError('Index order differs from the render plan.')
            chrome(c, f'Atlas / pair {i:02} of {plate_count}')
            paragraph(c, escape(plate['title']), MARGIN, 777, style=TITLE)
            paths = [OUT / a['href'] for a in article.select('a[href$=".pdf"]')]
            if len(paths) != 2:
                raise ValueError(f'Missing paired PDF links: {plate["title"]}')
            for path, label, y in [(paths[0], 'WORLD', 477), (paths[1], 'JAPAN COMPANION', 221)]:
                c.setFillColor(MUTED)
                c.setFont('Atlas-Bold', 8.5)
                c.drawString(MARGIN, y + WIDTH * 19.052559 / 44 + 11, label)
                draw_plate(path, MARGIN, y, WIDTH)
            note = clean_note(article.find('small').get_text())
            bottom = paragraph(c, '<b>Source and interpretation.</b> ' + escape(note), MARGIN, 198, style=SMALL)
            if bottom < 85:
                raise ValueError(f'Caption exceeds space: {plate["stem"]}')
            context = ('Celestial companion: sky context / Setouchi reference; no geographic Japan crop.'
                       if companions[plate['stem']]['kind'] == 'celestial-context'
                       else 'Japan companion: AuthaGraph viewport; native circle areas match the world plate.'
                       if companions[plate['stem']]['kind'] == 'authagraph-swarm-detail'
                       else 'Japan companion: enlargement in the native projection; national values do not resolve island conditions.')
            paragraph(c, escape(context), MARGIN, 76, style=SMALL)
            c.showPage()
            print(f'Paired {i:02}/{plate_count}: {plate["title"]}', flush=True)
        c.save()

        writer = PdfWriter()
        writer.append(base, import_outline=False)
        if len(writer.pages) != plate_count + 3:
            raise ValueError('Unexpected overview and atlas pagination.')
        for sec in sections:
            if len(writer.pages) + 1 != sec['page']:
                raise ValueError('Section pagination mismatch.')
            writer.append(sec['path'], import_outline=False)
            if sec['path'].is_relative_to(OUT):
                inputs.append(sec['path'])
            print(f'Appended: {sec["title"]}', flush=True)
        if len(writer.pages) != total:
            raise ValueError('Unexpected aggregate page count.')

        overlay_stream = io.BytesIO()
        overlay = canvas.Canvas(overlay_stream, pagesize=A4)
        for n, p in enumerate(writer.pages, 1):
            width, height = float(p.mediabox.width), float(p.mediabox.height)
            overlay.setPageSize((width, height))
            overlay.setFillColor(MUTED)
            overlay.setFont('Atlas', 7.5)
            overlay.drawRightString(width - 36, height - 14, f'v1 / {n} of {total}')
            overlay.showPage()
        overlay.save()
        overlay_stream.seek(0)
        overlay_reader = PdfReader(overlay_stream)
        for p, number in zip(writer.pages, overlay_reader.pages):
            p.merge_page(number)

        writer.add_outline_item('Overview and contents', 0)
        writer.add_outline_item('Plate index', 2)
        atlas = writer.add_outline_item(f'World / Japan atlas — {plate_count} pairs', 3)
        for i, p in enumerate(plates):
            writer.add_outline_item(f'{i+1:02} / {p["title"]}', i+3, parent=atlas)
        catalog_parent = writer.add_outline_item('Nine show catalogs', plate_count + 3)
        for sec in sections:
            writer.add_outline_item(sec['title'], sec['page']-1,
                                    parent=catalog_parent if sec['kind'] == 'catalog' else None)
        writer.add_metadata({
            '/Title': 'Cartofreako / Setouchi Triennale 2028 / Exploration v1',
            '/Author': 'Cartofreako',
            '/Subject': f'{plate_count} world/Japan pairs, nine catalogs, application draft and source reviews',
            '/Creator': 'Cartofreako aggregate builder / ReportLab and pypdf',
            '/Keywords': 'Setouchi, 2028, atlas, AuthaGraph, petroleum, exploration',
        })
        writer.page_mode = '/UseOutlines'
        writer.create_viewer_preferences().display_doctitle = True
        print('Writing aggregate with original vector artwork…', flush=True)
        writer.write(DEST)
        writer.close()
        evidence = {
            'file': DEST.name, 'pages': total, 'world_plates': plate_count, 'japan_companions': plate_count,
            'catalogs': 9, 'vector_maps': True,
            'scope': 'Verified index, all paired plates, nine catalogs, application, contact sheets, petroleum annex, visual revisions and resource colour key, coral prototypes, source notes and human reviews',
            'sections': [{k: v for k, v in s.items() if k != 'path'} for s in sections],
            'inputs': [{'path': str(p.relative_to(REPO)), 'sha256': hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()}
                       for p in sorted(set(inputs))],
            'sha256': hashlib.file_digest(DEST.open('rb'), 'sha256').hexdigest(),
            'bytes': DEST.stat().st_size,
        }
        (OUT / 'sources/aggregate-pdf.json').write_text(json.dumps(evidence, indent=2) + '\n')
        print(f'Created {DEST}: {total} pages, {DEST.stat().st_size/1024**2:.1f} MiB', flush=True)


if __name__ == '__main__':
    main()
