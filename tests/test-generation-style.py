#!/usr/bin/env python3
"""Guard style contracts, physical Japan scaling and lossless swarm export layers."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.sax
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


compiler = module('compile-generation-style')
detail = module('generate-japan-detail')
exporter = module('export-native-swarm')
world_frame = module('setouchi_world_framing')


class WorldFraming(unittest.TestCase):
    def test_antarc_country_fill_keeps_style_and_all_vertices(self):
        from lxml import etree
        from shapely.geometry import box
        from antarctica_inset import subpaths
        root = etree.fromstring(b'''<g xmlns="http://www.w3.org/2000/svg" id="terrestrial-land"><g id="countries" fill="#ffee00">
          <path id="mixed" data-iso3="ATA" fill-rule="evenodd"
            d="M 39 12 L 40 12 L 40 14 L 39 14 Z M 10 2 L 11 2 L 11 3 Z"/>
          </g></g>''')
        before = subpaths(root[0][0].get('d'))
        changes = []
        inset = world_frame.partition(root, box(35, 9, 44, 18), changes)
        after = subpaths(root[0][0].get('d')) + subpaths(inset[0][0].get('d'))
        self.assertCountEqual(before, after)
        self.assertEqual(inset[0].get('fill'), '#ffee00')
        self.assertEqual(inset[0][0].get('data-iso3'), 'ATA')
        self.assertEqual(inset[0][0].get('fill-rule'), 'evenodd')
        self.assertEqual(changes[0]['vertices'], 4)


class Styles(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads((ROOT / 'generation-style.json').read_text())

    def test_generated_header_is_current(self):
        self.assertEqual(compiler.compile_style(self.profile), (ROOT / 'src.generate/generation-style.h').read_text())

    def test_rejects_misleading_keys_and_unrenderable_classes(self):
        for family, field, value in (
            ('temperature', 'high_upper_days', [5, 10, 10, 40, 80]),
            ('temperature', 'high_upper_days', [5, 10, 20.5, 40, 80]),
            ('resources', 'solar_upper_mw', [100, 1000]),
            ('coral', 'display_cell_cap', 3),
            ('fiber', 'opacity', 75),
            ('water', 'river_width_pt', 0),
        ):
            profile = copy.deepcopy(self.profile)
            profile[family][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                compiler.compile_style(profile)
        self.profile['resources']['solar_colors'][0] = self.profile['coral']['colors'][0]
        with self.assertRaisesRegex(ValueError, 'reuse'):
            compiler.compile_style(self.profile)

    def test_japan_preserves_physical_route_strokes(self):
        source = '''<svg><g id="coastline"><path style="stroke-width:0.1"/></g>
          <g id="rivers"><path style="stroke-width:0.1;stroke-opacity:1"/></g>
          <path data-itu-fiber-route="true" style="stroke:#4cbb17;stroke-width:0.1"/>
          <circle data-fiber-landing="true" r="0.02" style="stroke-width:0.1"/>
          <path id="outline-only-land" style="fill-opacity:0"/></svg>'''
        target = io.StringIO()
        scale = 4.5
        xml.sax.parseString(source, detail.Detail(target, scale, (0, 0, 10, 10)))
        root = ET.fromstring('<svg>' + target.getvalue() + '</svg>')
        for node, expected in ((root[0][0], 1), (root[1][0], 1.5), (root[2], .5), (root[3], .5)):
            style = dict(item.split(':', 1) for item in node.get('style').split(';'))
            self.assertAlmostEqual(float(style['stroke-width']) * scale * 72, expected)
        self.assertEqual(root[2].get('style').split(';')[0], 'stroke:#4cbb17')
        self.assertEqual(float(root[3].get('r')), .01)
        self.assertIn('fill-opacity:0', root[4].get('style'))

    def test_japan_swarm_area_and_viewport(self):
        target = io.StringIO()
        source = '''<svg data-resolution-partition="ge-1080p"><g transform="scale(0.0104166666666667)">
          <circle cx="96" cy="96" r="12"/><circle cx="900" cy="900" r="12"/>
          </g><style>circle{fill-opacity:0.05}</style></svg>'''
        handler = detail.Detail(target, 4, (0, 0, 2, 2))
        xml.sax.parseString(source, handler)
        root = ET.fromstring('<svg>' + target.getvalue() + '</svg>')
        self.assertEqual((handler.total, handler.shown), (2, 1))
        self.assertAlmostEqual(float(root[0][0].get('r')) * 4, 12)


class Export(unittest.TestCase):
    source = '''<svg xmlns="http://www.w3.org/2000/svg" width="1in" height="1in" viewBox="0 0 96 96">
      <defs><clipPath id="clip"><rect x="5" y="5" width="70" height="70"/></clipPath></defs>
      <rect width="96" height="96" fill="white"/>
      <g transform="translate(4 3)" clip-path="url(#clip)">
      <circle class="c" cx="25" cy="25" r="15"/><circle class="c" cx="25" cy="25" r="12"/>
      <circle class="c" cx="25" cy="25" r="10"/><circle class="c" cx="35" cy="30" r="9"/>
      <circle class="c" cx="35" cy="30" r="8"/></g><path d="M 0 90 L 90 90" stroke="black"/>
      <style>.c{fill:#b24bc5;fill-opacity:0.05}</style></svg>'''

    def test_partitioned_render_matches_unsplit(self):
        import cairo
        import gi
        gi.require_version('Rsvg', '2.0')
        from gi.repository import Rsvg
        definitions = exporter.Definitions()
        xml.sax.parseString(self.source, definitions)
        parts = []
        handler = exporter.Layers(''.join(definitions.common), parts.append, limit=2)
        xml.sax.parseString(self.source, handler)
        self.assertEqual((handler.total, handler.layer_count), (5, 3))

        def render(documents):
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 96, 96)
            for document in documents:
                handle = Rsvg.Handle.new_from_data(document)
                viewport = Rsvg.Rectangle()
                viewport.x = viewport.y = 0
                viewport.width = viewport.height = 96
                self.assertTrue(handle.render_document(cairo.Context(surface), viewport))
            surface.flush()
            return bytes(surface.get_data())

        self.assertEqual(render(parts), render([self.source.encode()]))

    def test_rejects_group_compositing_across_boundaries(self):
        with self.assertRaisesRegex(ValueError, 'compositing'):
            xml.sax.parseString('<svg><g opacity="0.5"><circle r="1"/></g></svg>', exporter.Layers('', lambda content: None))

    def test_cyclic_swarm_render_matches_svg_uses_at_seam(self):
        import cairo
        import gi
        gi.require_version('Rsvg', '2.0')
        from gi.repository import Rsvg
        source = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
            width="1in" height="1in" viewBox="0 0 96 96" data-cyclic-shift-in="10">
          <rect id="st2-sheet-paper" width="96" height="96" fill="white"/>
          <defs><g id="source-cartography"><style>.c{fill:#b24bc5;fill-opacity:0.15}</style>
            <path d="M 0 0 L 96 0 L 96 30 L 0 30 Z" fill="#dddddd"/>
            <circle class="c" cx="1" cy="40" r="12"/><circle class="c" cx="95" cy="40" r="12"/>
            <circle class="c" cx="3" cy="40" r="10"/><circle class="c" cx="93" cy="40" r="10"/>
            <circle class="c" cx="50" cy="60" r="10"/></g>
            <clipPath id="clip"><rect width="96" height="96"/></clipPath></defs>
          <g id="st2-image-frame" transform="translate(2 2) scale(0.95)">
            <rect id="st2-image-background" width="96" height="96" fill="#fafafa"/>
            <g id="st2-image-window" clip-path="url(#clip)">
              <use xlink:href="#source-cartography" transform="translate(-86 0)"/>
              <use xlink:href="#source-cartography" transform="translate(10 0)"/>
              <use xlink:href="#source-cartography" transform="translate(106 0)"/>
            </g><g id="antarctica-consolidated-inset" transform="translate(1 1)">
              <path d="M 5 80 L 15 80 L 15 90 Z" fill="#99aaaa"/>
            </g></g></svg>'''
        parts = []
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.svg'
            path.write_text(source)
            total, _ = exporter.cyclic_layers(path, parts.append, limit=2)
        self.assertEqual(total, 5)

        def pixels(documents):
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 192, 192)
            for content in documents:
                handle = Rsvg.Handle.new_from_data(content)
                viewport = Rsvg.Rectangle()
                viewport.x = viewport.y = 0
                viewport.width = viewport.height = 192
                self.assertTrue(handle.render_document(cairo.Context(surface), viewport))
            surface.flush()
            return bytes(surface.get_data())
        self.assertEqual(pixels(parts), pixels([source.encode()]))


if __name__ == '__main__':
    unittest.main()
