"""Shared physical typography and SVG helpers for the Setouchi legend revision."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
from xml.sax.saxutils import escape

from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / 'assets/fonts/atkinson-hyperlegible'
NS = 'http://www.w3.org/2000/svg'
XL = 'http://www.w3.org/1999/xlink'
WIDTH, HEIGHT = 44.0, 19.052559
SUFFIX = '-authagraph-44-19.052559'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def font_environment():
    receipt = json.loads((FONT_DIR / 'provenance.json').read_text())
    for record in receipt['files']:
        if digest(FONT_DIR / record['file']) != record['sha256']:
            raise ValueError('Font source checksum mismatch: ' + record['file'])
    cache = ROOT / 'build/legend-informatics'
    cache.mkdir(parents=True, exist_ok=True)
    config = cache / 'fonts.conf'
    config.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd">'
                      '<fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include>'
                      f'<dir>{escape(str(FONT_DIR))}</dir>'
                      f'<cachedir>{escape(str(cache / "font-cache"))}</cachedir></fontconfig>')
    env = dict(os.environ, FONTCONFIG_FILE=str(config), XDG_CACHE_HOME=str(cache / 'cache'))
    match = subprocess.check_output(['fc-match', '-f', '%{file}', 'Atkinson Hyperlegible'],
                                    env=env, text=True).strip()
    if not Path(match).is_relative_to(FONT_DIR):
        raise RuntimeError('Atkinson Hyperlegible is being substituted: ' + match)
    return env


def register_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    for role in ('Regular', 'Bold', 'Italic', 'BoldItalic'):
        name = 'Atkinson-' + role
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / ('AtkinsonHyperlegible-' + role + '.ttf'))))
    pdfmetrics.registerFontFamily('Atkinson', normal='Atkinson-Regular', bold='Atkinson-Bold',
                                 italic='Atkinson-Italic', boldItalic='Atkinson-BoldItalic')


def el(tag, parent=None, **attributes):
    node = E.Element('{'+NS+'}'+tag, nsmap={None: NS}) if parent is None else E.SubElement(parent, '{'+NS+'}'+tag)
    for key, value in attributes.items():
        node.set(key.replace('_', '-'), str(value))
    return node


def text(parent, x, y, value, size=0.25, **attributes):
    node = el('text', parent, x=x, y=y, font_family='Atkinson Hyperlegible',
              font_size=size, fill='#2a2824', **attributes)
    node.text = str(value)
    return node


def save(root, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    E.ElementTree(root).write(str(path), encoding='UTF-8', xml_declaration=True)


def legend_group(identifier):
    return 'legend' in identifier or identifier.endswith('-key')
