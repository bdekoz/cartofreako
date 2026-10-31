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
from lxml import etree as E


class FramedShell(xml.sax.ContentHandler):
    """Retain the small frame and definitions, not the source geometry bank."""
    def __init__(self):
        self.buffer = io.StringIO()
        self.writer = XMLGenerator(self.buffer, encoding='utf-8')
        self.bank = self.style_depth = 0

    def startElement(self, name, attrs):
        if self.bank:
            self.bank += 1
            if self.style_depth or name in ('style', 'defs'):
                self.style_depth += 1
                self.writer.startElement(name, dict(attrs))
        else:
            self.writer.startElement(name, dict(attrs))
            if attrs.get('id') == 'source-cartography':
                self.bank = 1

    def characters(self, value):
        if not self.bank or self.style_depth:
            self.writer.characters(value)

    def endElement(self, name):
        if self.bank:
            self.bank -= 1
            if self.style_depth:
                self.writer.endElement(name)
                self.style_depth -= 1
            elif not self.bank:
                self.writer.endElement(name)
        else:
            self.writer.endElement(name)


class Bank(xml.sax.ContentHandler):
    def __init__(self, layers):
        self.layers = layers
        self.depth = 0

    def startElement(self, name, attrs):
        if self.depth or attrs.get('id') == 'source-cartography':
            self.depth += 1
            self.layers.startElement(name, attrs)

    def characters(self, value):
        if self.depth:
            self.layers.characters(value)

    def endElement(self, name):
        if self.depth:
            self.layers.endElement(name)
            self.depth -= 1


def cyclic_layers(source, render, limit=50000):
    """Replay each cyclic copy in full paint order, in bounded circle chunks."""
    handler = FramedShell()
    xml.sax.parse(str(source), handler)
    shell = E.fromstring(handler.buffer.getvalue().encode())
    select = lambda identifier: shell.xpath('//*[@id=$id]', id=identifier)[0]
    frame, window = select('st2-image-frame'), select('st2-image-window')
    copies = [dict(n.attrib) for n in window]
    for node in list(window):
        window.remove(node)
    inset = shell.xpath('//*[@id="antarctica-consolidated-inset"]')
    if inset:
        frame.remove(inset[0])
    render(E.tostring(shell))  # Paper and ocean are painted exactly once.
    common = ''.join(E.tostring(n, encoding='unicode') for n in shell if E.QName(n).localname == 'defs')
    root_attrs = dict(shell.attrib)
    root_attrs.update({'xmlns': 'http://www.w3.org/2000/svg', 'xmlns:xlink': 'http://www.w3.org/1999/xlink'})
    counts = []
    layer_count = 1
    for use in copies:
        layers = Layers(common, render, limit=limit)
        layers.startElement('svg', root_attrs)
        layers.startElement('g', dict(frame.attrib))
        layers.startElement('g', dict(window.attrib))
        layers.startElement('g', {'transform': use['transform']})
        xml.sax.parse(str(source), Bank(layers))
        for name in ('g', 'g', 'g', 'svg'):
            layers.endElement(name)
        layers.endDocument()
        counts.append(layers.total)
        layer_count += layers.layer_count
    if len(set(counts)) != 1:
        raise ValueError('Cyclic copies did not retain the same native circles')
    if inset:
        for identifier in ('st2-sheet-paper', 'st2-image-background'):
            node = select(identifier)
            node.getparent().remove(node)
        frame.append(inset[0])
        render(E.tostring(shell))
        layer_count += 1
    return counts[0], layer_count


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

    for _, root in E.iterparse(str(args.source), events=('start',)):
        root_attrs = dict(root.attrib)
        break
    cyclic = 'data-cyclic-shift-in' in root_attrs
    definitions = Definitions()
    if not cyclic:
        xml.sax.parse(str(args.source), definitions)
    width, height = (inches(root_attrs[key]) for key in ('width', 'height'))
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

    if cyclic:
        total, layer_count = cyclic_layers(args.source, render)
    else:
        layers = Layers(''.join(definitions.common), render)
        xml.sax.parse(str(args.source), layers)
        total, layer_count = layers.total, layers.layer_count
    provenance = args.source.with_suffix('.provenance.json')
    if provenance.exists():
        record = json.loads(provenance.read_text())
        expected = record.get('japan_visible_circles', record.get('native_circles'))
        if expected is not None and total != expected:
            raise ValueError(f'Circle conservation failed: {total} != {expected}')
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
                   native_circles_retained=total, ordered_layers=layer_count, cyclic_copies=3 if cyclic else 1,
                   vector_pdf=bool(args.pdf), pdf_points=[width * 72, height * 72] if args.pdf else None,
                   png_pixels=pixels if args.png else None, png_dpi=dpi if args.png else None,
                   partitioning='50,000 circles per layer; original paint order, ancestor transforms, clipping and styles')
    (args.pdf or args.png).with_suffix('.export.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'Exported {total} native circles in {layer_count} ordered layers', flush=True)


if __name__ == '__main__':
    main()
