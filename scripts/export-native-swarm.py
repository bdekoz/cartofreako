#!/usr/bin/env python3
"""Export native swarm SVGs in bounded memory, preserving every circle and paint order."""
import argparse
import io
import json
import os
from pathlib import Path
import re
import xml.sax
from xml.sax.saxutils import XMLGenerator

from cartofreako_style import digest


class Definitions(xml.sax.ContentHandler):
    def __init__(self):
        self.depth = 0
        self.common = []
        self.root = None

    def startElement(self, name, attrs):
        if self.root is None:
            if name != 'svg':
                raise ValueError('Expected an SVG document')
            self.root = dict(attrs)
        if self.depth or name in ('defs', 'style'):
            if not self.depth:
                self.buffer = io.StringIO()
                self.writer = XMLGenerator(self.buffer, encoding='utf-8')
            self.depth += 1
            self.writer.startElement(name, dict(attrs))

    def characters(self, text):
        if self.depth:
            self.writer.characters(text)

    def endElement(self, name):
        if self.depth:
            self.writer.endElement(name)
            self.depth -= 1
            if not self.depth:
                self.common.append(self.buffer.getvalue())


class Layers(xml.sax.ContentHandler):
    """Only ancestor wrappers and definitions repeat between ordered paint layers."""
    def __init__(self, common, render, limit=50000):
        self.common, self.render, self.limit = common, render, limit
        self.stack = []
        self.skip = self.total = self.layer_count = 0
        self.new_layer()

    def new_layer(self):
        self.buffer = io.StringIO()
        self.writer = XMLGenerator(self.buffer, encoding='utf-8')
        for name, attrs in self.stack:
            self.writer.startElement(name, attrs)
            if name == 'svg':
                self.buffer.write(self.common)
        self.count = 0

    def paint(self):
        self.render(self.buffer.getvalue().encode())
        self.layer_count += 1

    def startElement(self, name, attrs):
        if self.skip or name in ('defs', 'style'):
            self.skip += 1
            return
        if name == 'g':
            style = dict(s.strip().split(':', 1) for s in attrs.get('style', '').split(';') if ':' in s)
            if any(key in attrs or key in style for key in ('opacity', 'filter', 'mask', 'mix-blend-mode')):
                raise ValueError('Group compositing cannot be split across swarm export layers')
        if name == 'circle' and self.count >= self.limit:
            for tag, _ in reversed(self.stack):
                self.writer.endElement(tag)
            self.paint()
            self.new_layer()
        self.stack.append((name, dict(attrs)))
        self.writer.startElement(name, dict(attrs))
        if name == 'svg':
            self.buffer.write(self.common)
        if name == 'circle':
            self.count += 1
            self.total += 1

    def characters(self, text):
        if not self.skip:
            self.writer.characters(text)

    def endElement(self, name):
        if self.skip:
            self.skip -= 1
            return
        self.writer.endElement(name)
        self.stack.pop()

    def endDocument(self):
        self.paint()


def inches(value):
    match = re.fullmatch(r'([0-9.]+)in', value)
    if not match or float(match[1]) <= 0:
        raise ValueError('Native swarm sheet dimensions must be positive inches')
    return float(match[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--pdf', type=Path)
    parser.add_argument('--png', type=Path)
    parser.add_argument('--preview', type=Path)
    size = parser.add_mutually_exclusive_group()
    size.add_argument('--long-side', type=int, default=None)
    size.add_argument('--dpi', type=float, default=None)
    args = parser.parse_args()
    if not (args.pdf or args.png):
        parser.error('Specify --pdf and/or --png')
    if args.preview and not args.png:
        parser.error('--preview requires --png')
    if (args.long_side is not None and args.long_side < 1) or (args.dpi is not None and args.dpi <= 0):
        parser.error('Export size must be positive')

    import cairo
    import gi
    from PIL import Image
    gi.require_version('Rsvg', '2.0')
    from gi.repository import Rsvg
    os.environ.setdefault('XDG_CACHE_HOME', '/tmp/cartofreako-render-cache')

    definitions = Definitions()
    xml.sax.parse(str(args.source), definitions)
    width, height = (inches(definitions.root[key]) for key in ('width', 'height'))
    dpi = args.long_side / max(width, height) if args.long_side else args.dpi or 300
    pixels = (round(width * dpi), round(height * dpi))
    targets = []
    for path in (args.pdf, args.png, args.preview):
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
    if args.pdf:
        pdf = cairo.PDFSurface(str(args.pdf) + '.tmp', width * 72, height * 72)
        pdf.set_metadata(cairo.PDF_METADATA_TITLE, args.source.stem)
        targets.append((pdf, width * 72, height * 72))
    if args.png:
        png = cairo.ImageSurface(cairo.FORMAT_ARGB32, *pixels)
        targets.append((png, *pixels))

    def render(content):
        handle = Rsvg.Handle.new_from_data(content)
        handle.set_dpi(96)
        for surface, target_width, target_height in targets:
            viewport = Rsvg.Rectangle()
            viewport.x = viewport.y = 0
            viewport.width, viewport.height = target_width, target_height
            if not handle.render_document(cairo.Context(surface), viewport):
                raise RuntimeError('librsvg could not render a swarm layer')

    layers = Layers(''.join(definitions.common), render)
    xml.sax.parse(str(args.source), layers)
    provenance = args.source.with_suffix('.provenance.json')
    if provenance.exists():
        record = json.loads(provenance.read_text())
        expected = record.get('japan_visible_circles', record.get('native_circles'))
        if expected is not None and layers.total != expected:
            raise ValueError(f'Circle conservation failed: {layers.total} != {expected}')
    if args.pdf:
        pdf.finish()
        Path(str(args.pdf) + '.tmp').replace(args.pdf)
    if args.png:
        temporary = Path(str(args.png) + '.tmp')
        png.write_to_png(str(temporary))
        png.finish()
        with Image.open(temporary) as source:
            image = source.convert('RGB')
            image.save(temporary, format='PNG', dpi=(dpi, dpi))
            if args.preview:
                image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                image.save(args.preview)
        temporary.replace(args.png)
    receipt = dict(source=str(args.source), source_sha256=digest(args.source),
                   renderer=f'librsvg / Cairo {cairo.cairo_version_string()}',
                   native_circles_retained=layers.total, ordered_layers=layers.layer_count,
                   vector_pdf=bool(args.pdf), pdf_points=[width * 72, height * 72] if args.pdf else None,
                   png_pixels=pixels if args.png else None, png_dpi=dpi if args.png else None,
                   partitioning='50,000 circles per layer; original paint order, ancestor transforms, clipping and styles')
    (args.pdf or args.png).with_suffix('.export.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'Exported {layers.total} native circles in {layers.layer_count} ordered layers', flush=True)


if __name__ == '__main__':
    main()
