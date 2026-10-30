#!/usr/bin/env python3
"""Guard style contracts, physical Japan scaling and lossless swarm export layers."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
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


if __name__ == '__main__':
    unittest.main()
