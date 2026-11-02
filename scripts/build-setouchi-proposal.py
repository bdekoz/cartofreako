#!/usr/bin/env python3
"""Build the ST31–ST33 atlas revision, ten-page application and WordPress draft.

Uses the completed ST2 sheets without rerendering their data. Dependencies are
the same bundled fonts, ReportLab, Pillow, lxml and Poppler as the atlas build.
No network request, WordPress write, application or payment is performed.
"""
import argparse
from datetime import date, datetime
from html import escape
import importlib
import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from PIL import Image as PILImage
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.graphics import renderSVG
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from legend_informatics import ROOT, WIDTH, HEIGHT, digest, register_fonts
from setouchi_delivery import STANDARD_FILES

ATLAS = importlib.import_module('build-setouchi-revision-review')
CANONICAL_URL = 'https://benjamin.dekosnik.com/futures/setouchi-2028/'
PREVIEW_URL = 'https://benjamin.dekosnik.com/?page_id=3175&preview=true'
CALL_URL = 'https://setouchi-artfest.jp/en/proposals'
GUIDELINES_URL = 'https://setouchi-artfest.jp/files/uploads/en_ApplicationGuidelines2028.pdf'
TOUR_URL = 'https://setouchi-artfest.jp/files/uploads/en_Report_On-Site_Tour.pdf'
PROPOSAL_NAME = 'cartofreako-x-setouchi-proposal.pdf'
CV_A4_NAME = '20261101-art-cv-2p-a4.pdf'
INK = colors.HexColor('#202b30')
BLUE = colors.HexColor('#176778')
LIGHT = colors.HexColor('#eaf2f3')
GREY = colors.HexColor('#57636b')
CONTENT_WIDTH = A4[0] - 76

# Inclusive planning allowances, in JPY. They are not supplier quotations.
BUDGET = [
    ('Artist: development, preparation and facilitation', 250_000),
    ('Local co-facilitation and host support', 180_000),
    ('Japanese translation and event interpretation', 200_000),
    ('Technical consultations and guest honoraria', 160_000),
    ('Paper, colour and legibility proofs', 80_000),
    ('Twelve wall maps, source labels and spare prints', 200_000),
    ('Reusable supports and reversible mounting', 150_000),
    ('Table hire, study atlases and workshop materials', 80_000),
    ('Artist international return travel', 220_000),
    ('Japan transport, freight and packing', 140_000),
    ('Artist accommodation: 21 nights × JPY 10,000', 210_000),
    ('Venue and utilities allowance', 100_000),
    ('Small AV rental and remote guest connections', 60_000),
    ('Exhibition care, removal and return', 70_000),
]
SUBTOTAL = sum(amount for _, amount in BUDGET)
CONTINGENCY = SUBTOTAL // 10
TOTAL = SUBTOTAL + CONTINGENCY


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def record(path, relative_to=ROOT):
    return {'path': str(path.relative_to(relative_to)), 'sha256': digest(path), 'bytes': path.stat().st_size}


def title(entry):
    return ATLAS.INDEX_TITLES.get(entry['stem'], entry['title'])


def convert_cv(output):
    source = ROOT / 'assets.static/setouchi-triennale/20261101-art-cv-2p.pdf'
    target = output / CV_A4_NAME
    command = ['gs', '-q', '-dSAFER', '-dBATCH', '-dNOPAUSE', '-sDEVICE=pdfwrite',
               '-dCompatibilityLevel=1.7', '-dAutoRotatePages=/None', '-sPAPERSIZE=a4',
               '-dFIXEDMEDIA', '-dPDFFitPage', '-dEmbedAllFonts=true',
               '-sOutputFile=' + str(target), str(source)]
    subprocess.run(command, check=True)
    before = subprocess.check_output(['pdftotext', '-layout', str(source), '-'], text=True)
    after = subprocess.check_output(['pdftotext', '-layout', str(target), '-'], text=True)
    if before.split() != after.split() or ATLAS.page_count(target) != 2:
        raise ValueError('A4 conversion must retain both CV pages and every text token')
    write_json(output / 'sources/cv-a4-conversion.json', {
        'source': record(source), 'output': record(target, output),
        'pages': 2, 'source_paper': 'US Letter', 'output_paper': 'A4',
        'method': 'proportional fit with Ghostscript pdfwrite; no rasterization',
        'text_tokens_unchanged': True, 'command': command,
        'ghostscript_version': subprocess.check_output(['gs', '--version'], text=True).strip(),
    })
    print('Converted complete CV: two A4 pages; all text preserved', flush=True)


def build_atlases(source, output, issued):
    book = json.loads((source / 'plate-source-bibliography.json').read_text())
    entries = [e for e in book['entries'] if e['stem'] not in ATLAS.PDF_EXCLUDED_STEMS]
    if len(entries) != 36:
        raise ValueError('Expected the approved 36-subject atlas selection')
    files = json.loads((source / STANDARD_FILES).read_text())['records']
    lookup = {(r['stem'], r['scope'], r['kind']): r for r in files}
    source_manifest = json.loads((source / 'sources/revision-manifest.json').read_text())
    if source_manifest['pdf_selection']['included_stems'] != [e['stem'] for e in entries]:
        raise ValueError('ST2 selection no longer agrees with its assembly receipt')
    editions = {}
    for scope in ('world', 'japan'):
        cover = output / 'sources' / f'title-page-{scope}.pdf'
        front = output / 'sources' / f'edition-notes-{scope}.pdf'
        cover_settings = ATLAS.title_page(cover, issued, scope)
        ATLAS.introduction(front, entries, issued, scope)
        documents = [cover, front]
        retained = []
        for entry in entries:
            for kind in ('map', 'legend'):
                original = lookup[(entry['stem'], scope, kind)]['files']['pdf']
                path = source / original['path']
                if digest(path) != original['sha256']:
                    raise ValueError('ST2 PDF checksum mismatch: ' + str(path))
                documents.append(path)
                retained.append(dict(record(path), stem=entry['stem'], kind=kind,
                                     atlas_page=len(retained) + 4))
        target = output / f'setouchi-tri-explore-v3-{scope}.pdf'
        temporary = target.with_suffix('.tmp.pdf')
        subprocess.run(['pdfunite', *map(str, documents), str(temporary)], check=True)
        if ATLAS.page_count(temporary) != 75:
            raise ValueError('Atlas must contain 75 pages')
        temporary.replace(target)
        editions[scope] = dict(record(target, output), pages=75, cover=cover_settings,
                              retained_sheets=retained)
        print(f'Built {scope.title()} Atlas: 75 pages', flush=True)
    receipt = {
        'generation_date': issued.isoformat(),
        'source_delivery': str(source.relative_to(ROOT)),
        'source_revision_manifest': record(source / 'sources/revision-manifest.json'),
        'generation_style': record(ROOT / 'generation-style.json'),
        'sheet_cm': [round(WIDTH * 2.54, 2), round(HEIGHT * 2.54, 2)],
        'front_matter_pages': 3, 'subjects': 36, 'editions': editions,
        'index': [{'ordinal': e['ordinal'], 'stem': e['stem'], 'title': title(e)} for e in entries],
        'observation_dates_changed': False,
    }
    write_json(output / 'sources/atlas-revision.json', receipt)
    shutil.copyfile(source / 'plate-source-bibliography.json', output / 'sources/plate-source-bibliography.json')
    return book, entries, lookup


def floorplan():
    """Concept drawing only: six paired wall positions and two workshop tables."""
    d = Drawing(CONTENT_WIDTH, 340)
    x, y, scale = 40, 22, 37.5
    w, h = 6 * scale, 8 * scale
    d.add(Rect(x, y, w, h, fillColor=colors.white, strokeColor=INK, strokeWidth=1.2))
    # Door gap on the south wall; the clear arrival zone leads to the table aisle.
    d.add(Line(x + 72, y, x + 132, y, strokeColor=colors.white, strokeWidth=3))
    d.add(String(x + 72, y - 13, 'ENTRY / 1.6 m opening', fontName='Atkinson-Regular', fontSize=9, fillColor=INK))
    d.add(String(x + w / 2, y + h + 9, '6 m', textAnchor='middle', fontName='Atkinson-Bold', fontSize=10))
    d.add(String(8, y + h / 2, '8 m', fontName='Atkinson-Bold', fontSize=10))
    # Each numbered vertical bar represents one world/Japan pair on the wall.
    for i in range(3):
        for j, wall_x in enumerate((x + 4, x + w - 10)):
            pos_y = y + 66 + i * 76
            d.add(Rect(wall_x, pos_y, 6, 42, fillColor=BLUE, strokeColor=None))
            d.add(String(wall_x + (15 if j == 0 else -13), pos_y + 17,
                         str(i + 1 + 3 * j), fontName='Atkinson-Bold', fontSize=10, fillColor=BLUE))
    for table_y in (y + 112, y + 202):
        d.add(Rect(x + 77, table_y, 1.8 * scale, .8 * scale, fillColor=LIGHT, strokeColor=BLUE))
        d.add(String(x + 111, table_y + 11, 'TABLE', textAnchor='middle', fontName='Atkinson-Bold', fontSize=9, fillColor=BLUE))
    d.add(Line(x + 111, y + 145, x + 111, y + 199, strokeColor=GREY, strokeDashArray=[3, 3]))
    d.add(String(x + 118, y + 170, '1.6 m', fontName='Atkinson-Regular', fontSize=8, fillColor=GREY))
    labels = ['SIX WORLD / JAPAN PAIRS', '1  Water', '2  Fiber', '3  CDN and Cloud',
              '4  Coral threat', '5  Temperature', '6  Rare-earth production',
              '', 'Two 1.8 × 0.8 m tables', 'Seated reading / drawing',
              'Clear routes at least 1.2 m', '', 'A3 source keys alongside maps',
              'Ephemera on a movable board', '', 'Concept layout; site to be agreed']
    for i, label in enumerate(labels):
        d.add(String(292, 311 - i * 18, label, fontName='Atkinson-Bold' if i == 0 else 'Atkinson-Regular',
                     fontSize=9, fillColor=BLUE if i == 0 else INK))
    return d


def paragraph(text, small=False):
    return {'kind': 'small' if small else 'paragraph', 'text': text}


def heading(text):
    return {'kind': 'heading', 'text': text}


def figures(*items):
    # Each tuple: source stem, scope, concise caption. Files are bound below.
    return {'kind': 'figures', 'items': [dict(stem=s, scope=sc, caption=c) for s, sc, c in items]}


def pages(entries):
    """Application text and structure, shared by the PDF and accessible HTML."""
    return [
        {'title': 'Cartofreako × Setouchi', 'subtitle': 'A public atlas studio · Benjamin De Kosnik · Setouchi Triennale 2028', 'nodes': [
            heading('Concept'),
            paragraph('Cartofreako is a tool to approach the world and learn, design, and anticipate possible futures. '
                      'For the 2028 Setouchi Triennale, it becomes an open studio where residents and visitors read maps, exchange knowledge and make new work in public. '
                      'A Japan atlas and a world atlas connect the Seto Inland Sea with communications networks, media circulation, atmosphere, oceans, food, energy and minerals from around the world.'),
            paragraph('Large paired maps establish a shared reference. Around a table, participants trace water patterns, compare map projections, '
                      'question digital infrastructure and propose subjects rooted in island life. Drawing and discussion produce an evolving display of annotated maps, '
                      'paper experiments and questions. The project draws on R. Buckminster Fuller’s Dymaxion Map and World Game as prompts for collective inquiry.'),
            paragraph('Awashima is the preferred setting for autumn 2028. Its maritime history offers a starting point for conversations about routes and exchange. '
                      'Local collaborators will help select questions and adapt the studio to an agreed indoor room. Other festival venues remain possible.'),
            figures(('water', 'world', 'World · Water. Natural Earth physical geography; generalized bathymetry.'),
                    ('water', 'japan', 'Japan · Water. The same sources at a closer geographic scale.')),
            heading('One installation, five ways to take part'),
            paragraph('Five events and workshops are proposed, with two detailed in this proposal: Hamonshu Revisited; Dymaxion and AuthaGraph; Ocean Changes and Climate; Video Common Market Revisited; and an open invitation to propose further sessions.'),
            paragraph('Proposed category: interaction and exchange. Indoor installation with workshops; preferred season: autumn, 29 September–12 November 2028. '
                      'Requested production allowance: <b>JPY {:,}</b>.'.format(TOTAL)),
            paragraph('Project page: <a href="' + CANONICAL_URL + '">' + CANONICAL_URL + '</a>', small=True),
        ]},
        {'title': 'A room for maps and conversation', 'subtitle': 'Installation · materials · dimensions · visitor experience', 'nodes': [
            paragraph('A room of approximately 6 × 8 m holds six world/Japan map pairs, two reading and making tables, and a movable display for work made during the Triennale. '
                      'Visitors can enter for a brief look, read the sources while seated, or stay for a guided session.'),
            {'kind': 'diagram'},
            paragraph('<b>Display:</b> twelve pigment-printed wall maps, each <b>111.76 × 48.39 cm</b>; readable Japanese/English source keys; '
                      'two table reference sets; reusable supports; paper, pencils, tracing sheets and folding templates. Washi is a proposed material for selected editions, subject to print trials.'),
            paragraph('<b>Reading sequence:</b> choose a subject, compare its world and Japan views, consult the dated key, then add a question or make a paper response. '
                      'The initial subjects are Water, Fiber, CDN and Cloud, Coral Threat, Temperature and Rare-earth Production. Other atlas subjects can rotate into the display.'),
            paragraph('<b>Site:</b> an accessible indoor room on Awashima, selected with the festival and a host. The tour report identifies former shops and school buildings as places visited; '
                      'this drawing does not assign a particular property. Supports and circulation will be adjusted after measurement. [2]', small=True),
        ]},
        {'title': 'Two atlases, 36 subjects', 'subtitle': 'Japan and World · the same subject identifiers in both volumes', 'nodes': [
            paragraph('Each 75-page volume opens with a cover, edition notes and an index, followed by 36 maps and their separate legend/source sheets. '
                      'The printed index retains the archive’s subject numbers. Subjects 05 and 06 are outside this selection.'),
            {'kind': 'index', 'entries': [{'number': e['ordinal'], 'title': title(e)} for e in entries]},
            heading('Read the evidence at its own scale'),
            paragraph('The atlas is a dated study edition. A Japan detail can contain nearby countries; national statistics do not measure an individual island. '
                      'Celestial subjects use an observer/context view. Each legend preserves source dates, units and methods. '
                      'The world framing places Antarctica at the lower left as an editorial choice.'),
        ]},
        {'title': 'Hamonshu Revisited', 'subtitle': 'Workshop 1 · water, pattern and print · proposed 90-minute session', 'nodes': [
            paragraph('Begin with the wave and ripple designs in Mori Yūzan’s 1903 <i>Hamonshū</i>, as proposed in the artist’s project description. '
                      'Participants discuss how a line can describe movement, then group and redraw patterns. They apply their own derived patterns to transparent overlays over the Water plate’s colour fields.'),
            figures(('water', 'japan', 'Plate 04 · Japan Water. Source: Natural Earth. Generalized depths provide a drawing surface; they are not a navigation chart.')),
            figures(('water', 'world', 'Plate 04 · World Water. Its published source geometry is retained in this application.')),
            paragraph('<b>Format:</b> up to 16 participants; a short introduction, small-group pattern classification, a drawing/printing exercise and a shared viewing. '
                      'Use tracing sheets, pencils, water-based print materials and study maps. Provide a seated and no-cut version.'),
            paragraph('<b>Result:</b> a small collection of participant-made pattern sheets beside the maps. The overlays are artistic responses, separately labelled from measured geography. '
                      'Participants choose whether to display their work or take it home.', small=True),
        ]},
        {'title': 'Dymaxion and AuthaGraph', 'subtitle': 'Workshop 2 · projection, collective design and AI-assisted cartography', 'nodes': [
            figures(('geometry', 'world', 'Plate 01 · Cartography Geometry. Cartofreako’s native AuthaGraph construction.'),
                    ('graticules', 'world', 'Plate 02 · Cartographic Graticules. A coordinate framework for the same map.')),
            paragraph('Compare ways of unfolding a world and choosing what sits near the centre or edge. The session connects Fuller’s Dymaxion Map and World Game with '
                      'the AuthaGraph formulation and the practical choices of the Cartofreako atlas. Participants trace a route, fold a study map and explain what each representation makes easy or difficult to see.'),
            heading('A proposed conversation with Hajime Narukawa'),
            paragraph('Invite Narukawa to discuss AuthaGraph, cartographic design and the role of AI-assisted tools. His participation and the session format remain to be agreed. '
                      'The artist can lead the paper exercise independently; remote guest participation is included in the planning model.'),
            heading('A resource exercise'),
            figures(('resources-mineral-rare-earth-mine-production-2025', 'world',
                     'Plate 30 · Rare-earth mine production, 2025. Source: USGS as recorded in the atlas. Country values describe production, not mineral reserves.')),
            paragraph('Choose a material used by a familiar device. Compare the resource map with the paths and institutions needed to make, circulate and repair that device. '
                      'Small groups sketch a possible future and list what additional evidence they would need to evaluate it.'),
            paragraph('Proposed 90 minutes, up to 16 participants. Large study sheets, folding templates and written prompts support discussion in Japanese and English.', small=True),
        ]},
        {'title': 'Video Common Market Revisited', 'subtitle': 'Workshop 3 · media circulation and its physical infrastructure', 'nodes': [
            figures(('network-fiber', 'world', 'Plate 09 · World Fiber. TeleGeography snapshots, 2022/2026; ITU public terrestrial routes, retrieved October 2026. Routes are schematic.')),
            paragraph('Begin with a proposed conversation between Lisa Nakamura and Abigail De Kosnik about contemporary media circulation. '
                      'Read the cable, cloud/CDN, Starlink groundstation and orbital maps alongside the distribution of Japan-origin media. '
                      'Ask how a familiar screen experience depends on distant materials, institutions and places.'),
            figures(('network-cdn', 'japan', 'Plate 08 · Japan CDN and Cloud. Cache dated 21 October 2026; typed source records and approximate reference positions.'),
                    ('network-swarm-ge-1080p', 'world', 'Plate 11 · Dan Da Dan, 1080p/4K. Alpha60 observations, 4 September 2025–4 March 2026.')),
            paragraph('<b>Format:</b> a 90-minute public conversation and map-reading workshop, approximately 20 seated participants. '
                      'A local respondent and the audience bring examples of viewing and sharing. The speakers are proposed invitees; remote participation is the budget assumption.'),
            paragraph('<b>Interpretation:</b> CDN marks do not count unique active facilities or measure traffic. Swarm circles represent cumulative downloader observations, '
                      'not unique viewers; the 720p/SD partition is a separate atlas subject. Keep these distinctions on the table while discussing culture and distribution.', small=True),
        ]},
        {'title': 'Ocean Changes and Climate', 'subtitle': 'Workshop 4 · what a map tells us, and what it leaves open', 'nodes': [
            figures(('resources-fauna-coral-reef-threat-2011', 'world', 'Plate 28 · World coral threat. WRI Reefs at Risk Revisited, 2011. Honeycombs retain source-cell threat classes.')),
            paragraph('Invite an ocean or climate specialist and a local respondent to begin from a question chosen with the host: a change noticed, a resource used, '
                      'or a future worth investigating. The atlas supplies comparisons rather than a ready-made account of island conditions. The scientific contributors are to be selected with the host.'),
            figures(('anthropocene-temperature-2026', 'world', 'Plate 16 · World land-temperature records. NOAA CPC data through 28 October 2026.'),
                    ('anthropocene-temperature-2026', 'japan', 'Plate 16 · Japan view. Counts of record days; 2026 is a partial year.')),
            paragraph('<b>Format:</b> 90 minutes, up to 16 participants. Read a source key together, compare the two scales, write questions that the maps cannot answer, '
                      'then propose observations or collaborations that could extend the discussion.'),
            paragraph('<b>Careful comparisons:</b> the reef layer is a historical threat assessment, not current coral cover; symbol area is not reef area. '
                      'The temperature maps describe land, not sea temperature. Differences between the displayed years are not a direct estimate of warming. '
                      'Fresh local knowledge and future source updates will be dated and credited separately.', small=True),
        ]},
        {'title': 'Working in public', 'subtitle': 'Open invitation · collaborators · production and installation schedule', 'nodes': [
            heading('A fifth strand: an open studio'),
            paragraph('Residents, visitors and other interested parties can propose a topic, bring a question or help make a session. '
                      'The host and artist choose feasible additions to the programme. A bilingual facilitator supports conversation and written participation. '
                      'Contributors choose their credit and whether a drawing is displayed, returned or reproduced; public documentation uses separately agreed selections.'),
            heading('Proposed technical consultations'),
            paragraph('The supplied project description names <b>Tomiyoshi Tsukada</b> in Nagano for print production, <b>Hajime Narukawa / AuthaGraph</b> for cartography, '
                      'and <b>Awagami</b> for washi. These are proposed consultations, with availability, roles and fees to be agreed. '
                      'Local collaborators help determine the questions, language and daily welcome.'),
            {'kind': 'table', 'widths': [125, CONTENT_WIDTH - 125], 'rows': [
                ['Period', 'Production and care'],
                ['2027: after selection', 'Agree a host and room; measure access and walls; confirm contributors, quotations, rights and responsibilities.'],
                ['Jan–Jun 2028', 'Co-design local prompts; test papers, scale, colour and mounting; prepare Japanese/English text and workshop templates.'],
                ['Aug–Sep 2028', 'Refresh selected data 6–8 weeks before opening; check sources and captions; make final prints, spares and care instructions.'],
                ['24–28 Sep 2028', 'Proposed installation window: install supports and prints, check circulation and seating, rehearse with the local host.'],
                ['29 Sep–12 Nov 2028', 'Autumn display. Plan 21 artist nights across installation and workshop blocks; schedule the four sessions and open studio with the host. Local care continues between visits.'],
                ['13–15 Nov 2028', 'Remove supports, restore the room, return materials and agree the final participant-work selection and documentation.'],
            ]},
            paragraph('The installation is designed to remain legible and usable throughout the autumn session. Daily checks cover print condition, supports, table supplies and clear routes. '
                      'Keep spare labels and prints on site; agree any closure or repair with the host.', small=True),
        ]},
        {'title': 'Production budget', 'subtitle': 'One integrated proposal · inclusive planning allowances in Japanese yen', 'nodes': [
            {'kind': 'table', 'widths': [CONTENT_WIDTH - 100, 100], 'rows': [
                ['Item', 'JPY'],
                *[[label, f'{amount:,}'] for label, amount in BUDGET],
                ['Subtotal', f'{SUBTOTAL:,}'],
                ['Contingency (10%)', f'{CONTINGENCY:,}'],
                ['Total requested', f'{TOTAL:,}'],
            ]},
            paragraph('This estimate covers the installation, four named workshops and the open-studio strand. It includes travel, accommodation, exhibition care and removal. '
                      'The artist plans 21 nights on site; international guests participate remotely unless a revised budget supports travel.'),
            paragraph('The proposed funding source is the festival production subsidy, subject to selection and the agreed estimate. No sales or ticket income is assumed. '
                      'Amounts include tax allowances where applicable and must be replaced by quotations after the room, paper and programme are agreed.'),
            paragraph('If quotations exceed the allowance, reduce the number of full-size display pairs or use standard paper for most editions while retaining both table atlases, '
                      'readable source keys, interpretation and the core workshops. Record the revised scope with the host before production.'),
        ]},
        {'title': 'Artist and references', 'subtitle': 'Benjamin De Kosnik · selected CV from the supplied 1 November 2026 document', 'nodes': [
            heading('Selected CV'),
            paragraph('<b>Education:</b> MFA, Studio Art, California College of the Arts (2016); BA, Mathematics, University of Texas at Austin (1995). '
                      '<b>Selected exhibitions:</b> <i>Another Light Show</i>, with Kristen Wong, 500 Capp Street, San Francisco (2026); '
                      '<i>Transmarcations: X is not for destination …</i>, Beursschouwburg, Brussels (2017); '
                      'CCA MFA Exhibition (2016); Bay Area Digitalists, Root Division (2015); Hong Kong Open Printshop Graphic Arts Fiesta (2014); '
                      'Tokyo Screen Print Biennial (2011, 2013).'),
            paragraph('<b>Selected talks:</b> <i>Piracy is the Past, Present, and Future of Streaming</i>, HOPE_16, with Abigail De Kosnik (2025); '
                      '<i>War, Weapons, and the Web: Tracing Cyberwar Leaks and 3D-Printed Firearms as Distributed Network Swarms</i>, '
                      'Association of Internet Researchers, Rio, with Abigail De Kosnik and Aaron Zolla (2025); '
                      '<i>Digital Expansionism and Counter-Expansionism as Cyberwarfare: Analyzing Leaks in the Russo-Ukrainian War</i>, '
                      'International Communications Association Post Conference, Sydney, with Abigail De Kosnik (2024); '
                      '<i>UKR-RUS Leak Analysis</i>, HOT FOCI, USENIX (2022); '
                      '<i>Peer Phenomena as Nam June Paik’s Video Common Market</i>, Decentralized Web Summit (2018); '
                      '<i>Alpha-60 Bittorrent Cartography</i>, Venice Research Pavilion, with Abigail De Kosnik (2017); '
                      '<i>Writing Art in Digital Space</i>, International Conference on Artistic Research, The Hague (2016); '
                      '<i>The Machine is Learning Aesthetics</i>, Digital Craftsmanship Workshop, Designing Interactive Systems Conference, '
                      'ACM SIGCHI, Brisbane (2016).'),
            paragraph('<b>Public Collections:</b> Freehome, Berlin, Germany; Hong Kong Open Printshop, Hong Kong; '
                      'New Holland Island, St. Petersburg, Russia; Garage Archive Collection, Moscow, Russia; '
                      'HDK, Gothenburg, Sweden; Printed Matter, NY, NY.'),
            paragraph('<b>Selected distinction:</b> Special Jury Prize, Tokyo Screen Print Biennial (2011). '
                      '<b>Related experience:</b> Data Discovery Program, University of California Berkeley (2025).'),
            paragraph('Contact: studio.dekosnik@gmail.com · benjamin.dekosnik.com', small=True),
            heading('References and visual sources'),
            paragraph('[1] Setouchi Triennale 2028, official call and applicant guidelines, checked 1 November 2026. '
                      '<a href="' + CALL_URL + '">setouchi-artfest.jp/en/proposals</a>.', small=True),
            paragraph('[2] Setouchi Triennale 2028, <i>Report on the On-site Tours</i>, September–October 2026. '
                      'Awashima’s maritime history and candidate building types inform this proposed setting. '
                      '<a href="' + TOUR_URL + '">Official tour report</a>.', small=True),
            paragraph('[3] Benjamin De Kosnik, supplied project description and two-page art CV, 1 November 2026; '
                      'Cartofreako public-work memo, 21 October 2026. The selected CV above is an excerpt. The full supplied CV remains in the local source package.', small=True),
            paragraph('[4] Cartofreako, Japan and World atlases, ST2 map edition, 31 October 2026; front matter revised 1 November 2026. '
                      'Figures in this proposal reproduce those maps. The adjoining atlas legend sheets carry provider URLs, snapshots, units and methods. '
                      'Core sources shown here: AuthaGraph/Narukawa; Natural Earth; USGS; TeleGeography; ITU; cloud_cdn_cache.bkoz; Alpha60; WRI; NOAA CPC.', small=True),
            paragraph('Current atlas files and project material: <a href="' + CANONICAL_URL + '">' + CANONICAL_URL + '</a>. '
                      'The application is self-contained; the two full-size atlas volumes are supplementary reading.', small=True),
        ]},
    ]


def make_styles():
    return {
        'title': ParagraphStyle('Title', fontName='Atkinson-Bold', fontSize=28, leading=31, textColor=INK, spaceAfter=8),
        'subtitle': ParagraphStyle('Subtitle', fontName='Atkinson-Regular', fontSize=10, leading=14, textColor=BLUE, spaceAfter=17),
        'heading': ParagraphStyle('Heading', fontName='Atkinson-Bold', fontSize=13, leading=17, textColor=BLUE, spaceBefore=8, spaceAfter=6),
        'paragraph': ParagraphStyle('Body', fontName='Atkinson-Regular', fontSize=10.5, leading=14.2, textColor=INK, spaceAfter=9),
        'small': ParagraphStyle('Small', fontName='Atkinson-Regular', fontSize=8.5, leading=11.5, textColor=GREY, spaceAfter=8),
        'table': ParagraphStyle('Cell', fontName='Atkinson-Regular', fontSize=9.2, leading=12.2, textColor=INK, alignment=TA_LEFT),
        'index': ParagraphStyle('Index', fontName='Atkinson-Regular', fontSize=9.2, leading=11.5, textColor=INK),
    }


def styled_table(rows, widths, styles):
    cells = [[Paragraph(escape(str(value)), styles['table']) for value in row] for row in rows]
    table = Table(cells, colWidths=widths, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BACKGROUND', (0, 0), (-1, 0), LIGHT),
        ('LINEBELOW', (0, 0), (-1, 0), .6, BLUE),
        ('LINEBELOW', (0, 1), (-1, -1), .3, colors.HexColor('#d7dfe1')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return table


CSS = '''
*{box-sizing:border-box}body{margin:0;background:#f1f4f4;color:#202b30;font:17px/1.6 system-ui,sans-serif}
main{max-width:1050px;margin:auto;background:#fff;padding:clamp(20px,5vw,64px)}h1,h2,h3{line-height:1.15}h1{font-size:clamp(2rem,5vw,3.4rem)}
h2{margin-top:2rem}h3,a{color:#176778}a{overflow-wrap:anywhere}p{max-width:80ch}.subtitle{color:#176778}.note{font-size:.9rem;color:#57636b}
figure{margin:1.2rem 0}img{display:block;width:100%;height:auto}figcaption{font-size:.85rem;line-height:1.45;color:#57636b;margin:.5rem 0 1rem}
.figures{display:grid;gap:20px;grid-template-columns:repeat(2,minmax(0,1fr))}.figures.single{grid-template-columns:1fr}
table{width:100%;border-collapse:collapse;font-size:.93rem}td,th{text-align:left;vertical-align:top;padding:.6rem;border-bottom:1px solid #d7dfe1}th{background:#eaf2f3}
.page{padding-bottom:3rem;margin-bottom:3rem;border-bottom:1px solid #b9cdd0}.index{columns:2;column-gap:32px}.index p{break-inside:avoid;margin:0 0 .6rem;font-size:.9rem}
nav{display:flex;gap:1rem;flex-wrap:wrap;margin:2rem 0}.badge{font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:#57636b}
@media(max-width:650px){.figures{grid-template-columns:1fr}.index{columns:1}main{padding:20px}td,th{padding:.45rem}}
@media print{body{background:white}main{max-width:none;padding:0}.page{page-break-after:always}nav{display:none}}
'''


def html_document(page_title, body):
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(page_title)}</title><style>{CSS}</style></head><body><main>{body}</main></body></html>\n')


def build_proposal(source, output, issued, entries, lookup):
    styles = make_styles()
    figure_records = {}
    content = pages(entries)
    story, html_pages = [], []
    for page_number, page in enumerate(content, 1):
        if story:
            story.append(PageBreak())
        flow = [Paragraph(page['title'], styles['title']), Paragraph(page['subtitle'], styles['subtitle'])]
        html = [f'<section class="page" id="page-{page_number}"><p class="badge">{page_number:02d} / 10</p>',
                f'<h1>{escape(page["title"])}</h1><p class="subtitle">{escape(page["subtitle"])}</p>']
        for node in page['nodes']:
            kind = node['kind']
            if kind in ('paragraph', 'heading', 'small'):
                item = Paragraph(node['text'], styles[kind])
                flow.append(item)
                tag = 'h3' if kind == 'heading' else 'p'
                attr = ' class="note"' if kind == 'small' else ''
                html.append(f'<{tag}{attr}>{node["text"]}</{tag}>')
            elif kind == 'diagram':
                drawing = floorplan()
                flow.append(drawing)
                renderSVG.drawToFile(drawing, str(output / 'media/installation-layout.svg'))
                html.append('<figure><img src="media/installation-layout.svg" alt="Concept plan for a six by eight metre room: six paired wall-map positions, two tables and a clear entrance."><figcaption>Concept layout; dimensions and host room to be agreed.</figcaption></figure>')
            elif kind == 'figures':
                count = len(node['items'])
                width = (CONTENT_WIDTH - (14 if count > 1 else 0)) / count
                cells = []
                html.append(f'<div class="figures{" single" if count == 1 else ""}">')
                for fig in node['items']:
                    key = (fig['stem'], fig['scope'])
                    original = lookup[(fig['stem'], fig['scope'], 'map')]['files']['preview']
                    src = source / original['path']
                    if digest(src) != original['sha256']:
                        raise ValueError('Map preview checksum mismatch: ' + str(src))
                    filename = f'{fig["scope"]}-{fig["stem"]}.png'
                    dest = output / 'media' / filename
                    if key not in figure_records:
                        shutil.copyfile(src, dest)
                        with PILImage.open(dest) as image:
                            size = image.size
                        figure_records[key] = dict(record(dest, output), source=record(src),
                                                   stem=fig['stem'], scope=fig['scope'], pixels=list(size), uses=[])
                    rec = figure_records[key]
                    rec['uses'].append({'page': page_number, 'caption': fig['caption'], 'width_pt': width,
                                        'effective_dpi': round(rec['pixels'][0] / (width / 72), 1)})
                    image_height = width * rec['pixels'][1] / rec['pixels'][0]
                    cells.append([Image(str(dest), width=width, height=image_height), Spacer(1, 5),
                                  Paragraph(fig['caption'], styles['small'])])
                    html.append(f'<figure><img src="media/{filename}" alt="{escape(fig["caption"], quote=True)}">'
                                f'<figcaption>{escape(fig["caption"])}</figcaption></figure>')
                if count == 1:
                    flow.append(KeepTogether(cells[0]))
                else:
                    table = Table([[cells[0], '', cells[1]]], colWidths=[width, 14, width])
                    table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                               ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                               ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
                    flow.append(table)
                html.append('</div>')
            elif kind == 'table':
                flow.append(styled_table(node['rows'], node['widths'], styles))
                flow.append(Spacer(1, 12))
                html.append('<table>')
                for i, row in enumerate(node['rows']):
                    tag = 'th' if i == 0 else 'td'
                    html.append('<tr>' + ''.join(f'<{tag}>{escape(str(v))}</{tag}>' for v in row) + '</tr>')
                html.append('</table>')
            elif kind == 'index':
                halves = [node['entries'][:18], node['entries'][18:]]
                cols = []
                for half in halves:
                    cols.append([Paragraph(f'<b>{e["number"]:02d}</b>  {escape(e["title"])}', styles['index']) for e in half])
                rows = [[cols[0][i], '', cols[1][i]] for i in range(18)]
                width = (CONTENT_WIDTH - 22) / 2
                table = Table(rows, colWidths=[width, 22, width], rowHeights=25)
                table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                           ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                           ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
                flow.append(table)
                html.append('<div class="index">' + ''.join(f'<p><b>{e["number"]:02d}</b> {escape(e["title"])}</p>' for e in node['entries']) + '</div>')
            else:
                raise ValueError(kind)
        story.extend(flow)
        html_pages.append('\n'.join(html) + '</section>')

    def footer(canvas, doc):
        if doc.page > 10:
            raise ValueError('Content overflow: application exceeds ten A4 pages')
        canvas.saveState()
        canvas.setFont('Atkinson-Regular', 8)
        canvas.setFillColor(GREY)
        canvas.drawString(38, A4[1] - 26, 'CARTOFREAKO / SETOUCHI TRIENNALE 2028')
        canvas.drawString(38, 23, 'BENJAMIN DE KOSNIK · ' + issued.isoformat())
        canvas.drawRightString(A4[0] - 38, 23, f'{doc.page:02d} / 10')
        canvas.restoreState()

    path = output / PROPOSAL_NAME
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=38, rightMargin=38,
                            topMargin=47, bottomMargin=42, title='Cartofreako × Setouchi — A public atlas studio',
                            author='Benjamin De Kosnik', pageCompression=1)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    if ATLAS.page_count(path) != 10:
        raise ValueError('Expected ten application pages')
    (output / 'proposal.html').write_text(html_document('Cartofreako × Setouchi — application',
        '<nav><a href="index.html">Delivery index</a><a href="' + PROPOSAL_NAME + '">Download the ten-page PDF</a></nav>' + '\n'.join(html_pages)))
    write_json(output / 'sources/proposal-content.json', content)
    write_json(output / 'sources/figure-provenance.json', list(figure_records.values()))
    write_json(output / 'sources/budget.json', {'currency': 'JPY', 'basis': 'inclusive planning allowances, not quotations',
        'items': [{'item': label, 'amount': value} for label, value in BUDGET],
        'subtotal': SUBTOTAL, 'contingency_rate': .1, 'contingency': CONTINGENCY, 'total': TOTAL})
    print(f'Built application: ten A4 pages; budget JPY {TOTAL:,}', flush=True)


def wordpress_blocks(media_urls=None):
    """Portable core blocks. Relative URLs make the supplied local preview complete.

    Pass a JSON map from package-relative file names to actual Media Library
    URLs to generate a block fragment with production attachment URLs.
    """
    media_urls = media_urls or {}
    def url(path):
        return escape(media_urls.get(path, '../' + path), quote=True)
    def p(text):
        return '<!-- wp:paragraph -->\n<p>' + text + '</p>\n<!-- /wp:paragraph -->'
    def h(text):
        return '<!-- wp:heading -->\n<h2 class="wp-block-heading">' + text + '</h2>\n<!-- /wp:heading -->'
    def fig(path, caption):
        return ('<!-- wp:image {"sizeSlug":"full","linkDestination":"none"} -->\n'
                '<figure class="wp-block-image size-full"><img src="' + url(path) + '" alt="' + escape(caption, quote=True) + '">'
                '<figcaption class="wp-element-caption">' + escape(caption) + '</figcaption></figure>\n<!-- /wp:image -->')
    parts = [
        p('A proposal by Benjamin De Kosnik for Setouchi Triennale 2028.'),
        p('Cartofreako is a tool to approach the world and learn, design, and anticipate possible futures. '
          'Cartofreako × Setouchi proposes a public atlas studio: a place to read maps, exchange knowledge and make new work with residents and visitors.'),
        fig('media/japan-water.png', 'Japan Atlas · Water. Natural Earth physical geography; generalized bathymetry.'),
        h('Two atlases, one shared table'),
        p('The Japan and World atlases each contain 36 subjects, with a separate legend and source sheet after every map. '
          'They connect the Seto Inland Sea with communications networks, media circulation, atmosphere, oceans, food, energy and minerals from around the world. '
          'At the studio table, discussion and drawing turn these references into questions and possible futures.'),
        p('<a href="' + url('setouchi-tri-explore-v3-japan.pdf') + '">Download the Japan Atlas</a> · '
          '<a href="' + url('setouchi-tri-explore-v3-world.pdf') + '">Download the World Atlas</a> · '
          '<a href="' + url(PROPOSAL_NAME) + '">Read the ten-page proposal</a>'),
        p('Atlas edition: 1 November 2026. Each volume has 75 pages. Full-size map sheets are 111.76 × 48.39 cm. '
          'Maps retain their own observation dates; they are not live measurements.'),
        h('A flexible installation'),
        p('Six world/Japan map pairs, reading and making tables, and a growing display of workshop material form the proposed installation. '
          'Awashima is the preferred autumn setting, with the room and local programme to be developed with the festival and a host. '
          'The design can be adapted to other agreed venues.'),
        h('Hamonshu Revisited'),
        p('Discuss and classify the wave and ripple patterns in Mori Yūzan’s 1903 Hamonshū, then make new patterns over study copies of the Water plate. '
          'Drawing, print and washi experiments connect historical visual language with a contemporary atlas.'),
        h('Dymaxion and AuthaGraph'),
        p('A proposed conversation with Hajime Narukawa about AuthaGraph, R. Buckminster Fuller’s legacy and AI-assisted cartography. '
          'Folding and tracing exercises invite participants to explore how a map changes what we notice.'),
        fig('media/world-resources-mineral-rare-earth-mine-production-2025.png',
            'World Atlas · Rare-earth mine production, 2025. Country production values, not mineral reserves. Source: USGS / atlas bibliography.'),
        h('Ocean Changes and Climate'),
        p('Read coral, water and temperature maps with invited specialists and local participants. '
          'Compare the questions people bring with what each source can show, then identify new observations or collaborations to pursue.'),
        fig('media/world-resources-fauna-coral-reef-threat-2011.png',
            'World Atlas · Coral reef integrated local threat. WRI, 2011: a historical assessment, not current coral cover.'),
        h('Video Common Market Revisited'),
        p('A proposed discussion with Lisa Nakamura and Abigail De Kosnik begins with the circulation of Japan-origin media. '
          'Maps of fiber-optic cables, cloud/CDN records, Starlink groundstations, satellites and network swarms reveal subjects for collective inquiry.'),
        fig('media/world-network-fiber.png', 'World Atlas · Fiber. TeleGeography and ITU sources, 2022–2026; schematic routes.'),
        h('An open invitation'),
        p('Residents, visitors and other interested parties can propose topics and help shape additional sessions. '
          'The installation grows through annotated maps, questions and paper experiments, with participants choosing what to share.'),
        p('Proposed production consultations include Tomiyoshi Tsukada in Nagano for printing, Hajime Narukawa / AuthaGraph for cartography, '
          'and Awagami for washi. Collaborator participation, venue and programme are to be agreed.'),
        h('Artist'),
        p('Benjamin De Kosnik holds an MFA in Studio Art from California College of the Arts and a BA in Mathematics from the University of Texas at Austin. '
          'His supplied CV includes exhibitions at 500 Capp Street, Beursschouwburg and Hong Kong Open Printshop, '
          'and the Special Jury Prize at the 2011 Tokyo Screen Print Biennial.'),
        p('Project context: <a href="' + CALL_URL + '">Setouchi Triennale 2028 official call</a>. '
          'Source references and dates accompany the atlas maps and the application PDF.'),
    ]
    return '\n\n'.join(parts) + '\n'


def build_wordpress(output, media_map=None):
    folder = output / 'wordpress'
    folder.mkdir(exist_ok=True)
    mapping = json.loads(media_map.read_text()) if media_map else {}
    local = wordpress_blocks()
    # Only exact file names in this explicit manifest are acceptable substitutions.
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(local, 'html.parser')
    assets = sorted({node.get('src', node.get('href'))[3:] for node in soup.select('[src],[href]')
                     if node.get('src', node.get('href')).startswith('../')})
    if mapping:
        if set(mapping) != set(assets):
            raise ValueError('WordPress media map must provide exactly the paths in media-manifest.json')
        for path, url in mapping.items():
            if urlparse(url).scheme != 'https' or not urlparse(url).netloc:
                raise ValueError('Media URL must be an absolute HTTPS URL: ' + path)
    (folder / 'page-content.html').write_text(wordpress_blocks(mapping))
    (folder / 'preview.html').write_text(html_document('Cartofreako × Setouchi',
        '<p class="badge">WordPress page 3175 · local content preview</p><h1>Cartofreako × Setouchi</h1>' + local))
    write_json(folder / 'media-manifest.json', [record(output / path, output) for path in assets])
    write_json(folder / 'page.json', {'page_id': 3175, 'title': 'Cartofreako × Setouchi',
        'slug': 'setouchi-2028', 'parent_path': '/futures/', 'canonical_url': CANONICAL_URL,
        'preview_url': PREVIEW_URL, 'status': 'draft', 'content_file': 'page-content.html',
        'media_urls_resolved': bool(mapping), 'remote_write_performed': False,
        'excerpt': 'A public atlas studio proposed for Setouchi Triennale 2028: maps, workshops and collective inquiry.'})
    (folder / 'README.txt').write_text(
        'WORDPRESS PAGE 3175 — CARTOFREAKO × SETOUCHI\n\n'
        'Canonical permalink: ' + CANONICAL_URL + '\n'
        'Editor preview: ' + PREVIEW_URL + '\n\n'
        'page-content.html contains core Gutenberg blocks for the existing page.\n'
        'preview.html is the complete local preview, with working image/PDF links.\n'
        'The canonical site and its preview were unavailable to the web reader; no\n'
        'authenticated WordPress tool is connected. This package does not publish.\n\n'
        'To install: upload the seven assets in media-manifest.json to WordPress\n'
        'or the site file host (the World PDF may exceed the Media Library limit).\n'
        'Write a JSON object mapping every manifest path to its final HTTPS URL.\n'
        'Rebuild only the block fragment with:\n'
        '  python3 scripts/build-setouchi-proposal.py --wordpress-only \\\n'
        '    --wordpress-media-map /path/to/media-urls.json\n'
        'Paste page-content.html into page 3175 using the WordPress code editor;\n'
        'use the title and excerpt in page.json. Keep the existing parent and\n'
        'permalink. Preview all image and download links before publishing.\n\n'
        'Relative ../ URLs in an unrebound fragment are for the local preview;\n'
        'use the media map before pasting it into the live WordPress editor.\n')
    print('Built WordPress page 3175 draft and local preview', flush=True)


def source_records(output, source, issued):
    assets = ROOT / 'assets.static/setouchi-triennale'
    names = ['20261101 setouchi proposal.pdf', '20261101-art-cv-2p.pdf',
             '20261021 cartofreako freakout.pdf', 'en_ApplicationGuidelines2028.pdf', 'en_Report_On-Site_Tour.pdf']
    inputs = []
    for name in names:
        src = assets / name
        dest = output / 'sources/input' / name
        dest.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(src, dest)
        inputs.append(record(src))
        subprocess.run(['pdftotext', '-layout', str(src), str(dest.with_suffix('.txt'))], check=True)
    write_json(output / 'sources/input-provenance.json', inputs)
    write_json(output / 'sources/call-requirements.json', {
        'checked_date': '2026-11-01', 'method': 'official web page and linked official PDFs read with web tool',
        'url': CALL_URL, 'guidelines_url': GUIDELINES_URL, 'tour_url': TOUR_URL,
        'deadline_jst': '2026-11-02T10:00:00+09:00', 'deadline_los_angeles': '2026-11-01T17:00:00-08:00',
        'maximum_a4_pages_proposal_and_references': 10, 'maximum_plans': 3, 'maximum_file_bytes': 2_000_000_000,
        'language': ['English', 'Japanese'], 'concept_and_cv_guidance': 'About half an A4 page each in English',
        'required': ['title', 'concept', 'description', 'production process', 'materials', 'size',
                     'production and installation schedule', 'estimated budget', 'visuals', 'CV or previous work', 'payment evidence separately'],
        'fee_jpy_per_plan': 1500, 'production_subsidy_ceiling_approximately_jpy': 2_500_000,
        'application_submission_performed': False, 'payment_performed': False,
        'submitted_plan_count': 0, 'prepared_plan_count': 1,
    })
    write_json(output / 'sources/build.json', {'issued': issued.isoformat(),
        'source_delivery': str(source.relative_to(ROOT)), 'canonical_url': CANONICAL_URL,
        'source_script': record(Path(__file__)),
        'git_head_at_build': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'command': 'make setouchi-v3 SETOUCHI_V3_DATE=' + issued.isoformat(),
        'source_data_refreshed': False})


def index(output, issued):
    body = f'''<p class="badge">CARTOFREAKO / SETOUCHI TRIENNALE 2028 / {issued.isoformat()}</p>
<h1>A public atlas studio</h1><p>Benjamin De Kosnik · ST31–ST33 delivery</p>
<p>One complete application, revised Japan and World atlas volumes, and content for WordPress page 3175.</p>
<nav><a href="{PROPOSAL_NAME}">Application PDF · 10 A4 pages</a><a href="proposal.html">Read the application online</a>
<a href="{CV_A4_NAME}">Complete CV · 2 A4 pages</a>
<a href="setouchi-tri-explore-v3-japan.pdf">Japan Atlas · 75 pages</a><a href="setouchi-tri-explore-v3-world.pdf">World Atlas · 75 pages</a>
<a href="wordpress/preview.html">WordPress page preview</a><a href="wordpress/page-content.html">Gutenberg block content</a></nav>
<figure><img src="media/japan-water.png" alt="Japan Water plate"><figcaption>Japan · Water. Natural Earth sources; generalized bathymetry.</figcaption></figure>
<h2>The application</h2><p>The ten-page A4 PDF includes the concept, room drawing, 36-subject atlas index, four named workshops,
open studio, production schedule, JPY {TOTAL:,} estimate, selected CV and references. The supplied two-page CV was US Letter;
the application uses a compact A4 excerpt. The complete two-page CV is also converted to A4 as a separate download.
Source originals are preserved under <code>sources/input/</code>.</p>
<p>The full atlas volumes are supplementary downloads. Submit only the ten-page application as the proposal/reference packet;
payment evidence is a separate item required by the <a href="{CALL_URL}">official call</a>.</p>
<h2>The revised atlases</h2><p>Covers read CARTOFREAKO, the generation date at half size, and JAPAN or WORLD in matching large type.
Edition notes use centimetres. Index titles are revised. All 144 map and legend pages are assembled from the verified ST2 PDFs.</p>
<h2>WordPress destination</h2><p><a href="{CANONICAL_URL}">{CANONICAL_URL}</a> · existing page ID 3175.
The draft contains the programme, images and three downloads. <a href="wordpress/README.txt">Installation instructions</a>
explain how to replace local media references with uploaded file URLs.</p>
<h2>Delivery records</h2><nav><a href="sources/atlas-revision.json">Atlas assembly receipt</a>
<a href="sources/figure-provenance.json">Figure sources</a><a href="sources/budget.json">Budget</a>
<a href="sources/call-requirements.json">Call requirements</a><a href="sources/validation.json">Validation</a>
<a href="SHA256SUMS">Checksums</a></nav>'''
    (output / 'index.html').write_text(html_document('Cartofreako × Setouchi — delivery', body))


def checksums(output):
    records = [record(path, output) for path in sorted(output.rglob('*'))
               if path.is_file() and path.name not in ('manifest.json', 'SHA256SUMS')]
    write_json(output / 'manifest.json', {'edition': 'Setouchi 2028 v3', 'files': records})
    (output / 'SHA256SUMS').write_text(''.join(f'{r["sha256"]}  {r["path"]}\n' for r in records))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'output/setouchi-triennale-2028-st2')
    parser.add_argument('--output', type=Path, default=ROOT / 'output/setouchi-triennale-2028-v3')
    parser.add_argument('--date', type=date.fromisoformat, default=datetime.now(ZoneInfo('America/Los_Angeles')).date())
    parser.add_argument('--wordpress-media-map', type=Path)
    parser.add_argument('--wordpress-only', action='store_true')
    parser.add_argument('--skip-atlases', action='store_true', help='Reuse already assembled v3 atlases during content layout work')
    args = parser.parse_args()
    output, source = args.output.resolve(), args.source.resolve()
    if output == source or output.is_relative_to(source):
        raise ValueError('The proposal edition must not overwrite the ST2 source delivery')
    for folder in ('sources', 'media'):
        (output / folder).mkdir(parents=True, exist_ok=True)
    if args.wordpress_only:
        build_wordpress(output, args.wordpress_media_map)
        checksums(output)
        return
    register_fonts()
    if args.skip_atlases:
        book = json.loads((source / 'plate-source-bibliography.json').read_text())
        entries = [e for e in book['entries'] if e['stem'] not in ATLAS.PDF_EXCLUDED_STEMS]
        lookup = {(r['stem'], r['scope'], r['kind']): r for r in json.loads((source / STANDARD_FILES).read_text())['records']}
    else:
        book, entries, lookup = build_atlases(source, output, args.date)
    source_records(output, source, args.date)
    convert_cv(output)
    build_proposal(source, output, args.date, entries, lookup)
    build_wordpress(output, args.wordpress_media_map)
    index(output, args.date)
    checksums(output)


if __name__ == '__main__':
    main()
