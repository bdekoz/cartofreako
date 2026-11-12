#!/usr/bin/env python3
"""Read dense local H3 SVGs without changing their paint or Japan viewport."""
from pathlib import Path
import importlib
import sys
import tempfile
import unittest
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from setouchi_h3_trials import settings_for
compositor = importlib.import_module('build-current-atlas')


class AtlasSettings(unittest.TestCase):
    def test_amber_cloud_page_uses_dark_captions_without_changing_data(self):
        tree = etree.ElementTree(etree.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<text fill="#fcc553" style="fill:#fcc553;fill-opacity:.94">Caption'
            '<tspan style="fill:#fcc553">source period</tspan></text>'
            '<path id="observation" fill="#e72b88" d="M0,0 L1,1"/>'
            '<image href="layers/cloud.png" width="44" height="19.052559"/>'
            '</svg>'))
        data = [etree.tostring(n) for n in list(tree.getroot())[1:]]
        compositor.cloud_annotation_contrast(tree)
        for node in tree.xpath('//*[local-name()="text" or local-name()="tspan"]'):
            self.assertEqual(compositor.css(node.attrib)['fill'], '#240413')
        self.assertEqual(tree.getroot()[0].get('fill'), '#240413')
        self.assertEqual(compositor.css(tree.getroot()[0].attrib)['fill-opacity'], '.94')
        self.assertEqual([etree.tostring(n) for n in list(tree.getroot())[1:]], data)

    def test_large_world_and_japan_paths_retain_style_and_viewport(self):
        with tempfile.TemporaryDirectory() as directory:
            atlas = Path(directory)
            # Both files exceed libxml2's default limit for one attribute.
            dense_path = 'M0,0 ' + 'L1,1 ' * 2_100_000
            style = ('fill:rgb(41,127,184);fill-opacity:0.7;'
                     'stroke:rgb(41,127,184);stroke-opacity:0.7;stroke-width:0.0025')
            world = (f'<svg xmlns="http://www.w3.org/2000/svg">'
                     f'<g id="precipitation-rate"><path data-bin="1" style="{style}" '
                     f'd="{dense_path}"/></g></svg>')
            japan = ('<svg xmlns="http://www.w3.org/2000/svg" '
                     'xmlns:xlink="http://www.w3.org/1999/xlink">'
                     '<defs><clipPath id="viewport"><rect x="1" y="2" width="12" height="6"/>'
                     '</clipPath></defs><g clip-path="url(#viewport)">'
                     '<g transform="translate(-3 -4) scale(2)">'
                     '<use xlink:href="#source-content"/></g></g>'
                     f'<g id="source-content"><path d="{dense_path}"/></g></svg>')
            for scope, content in [('world', world), ('japan', japan)]:
                target = atlas/'maps'/scope/'svg/cloud-atmosphere.svg'
                target.parent.mkdir(parents=True)
                target.write_text(content)
            result = settings_for(atlas, 'cloud-atmosphere', 300)
            self.assertEqual(result['styles']['precipitation-rate']['1'], {
                'fill': [41/255, 127/255, 184/255, .7],
                'stroke': [41/255, 127/255, 184/255, .7], 'width': .0025})
            self.assertEqual(result['styles']['precipitation-rate']['6'],
                             result['styles']['precipitation-rate']['1'])
            self.assertEqual(result['views'][0]['bounds'], [0, 0, 44, 19.052559])
            self.assertEqual(result['views'][1]['bounds'], [1.94, 2.94, 6.12, 3.12])
            self.assertEqual(result['views'][1]['pixels_per_unit'], 600)


if __name__ == '__main__':
    unittest.main()
