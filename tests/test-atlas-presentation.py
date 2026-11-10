#!/usr/bin/env python3
"""Guard atlas palette selection, data paint, source positions and physical type."""
import copy
import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.sax

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from atlas_presentation import Theme, settings, css, groundstation_settings
from lxml import etree as E
from cartofreako_style import STYLE

builder = importlib.import_module('build-atlas-defaults')


class AtlasPresentation(unittest.TestCase):
    def setUp(self):
        self.config, self.recipe = settings(STYLE)

    def test_approved_default_and_optional_palettes(self):
        self.assertEqual(self.recipe['background'], '#240413')
        self.assertEqual(self.recipe['text'], '#fcc553')
        self.assertEqual(self.config['astronomy_label_font_size_pt'], 12)
        for pair in ('wine-amber', 'ultramarine-porcelain', 'plum-ice', 'midnight-champagne'):
            profile = copy.deepcopy(STYLE)
            profile['atlas']['presentation']['default_palette'] = pair
            self.assertEqual(settings(profile)[1]['randoma11y_pair'], pair)
        profile['atlas']['presentation']['default_palette'] = 'missing'
        with self.assertRaises(ValueError):
            settings(profile)

    def test_page_theme_preserves_measured_and_categorical_paint(self):
        fixture = '''<svg><rect id="st2-sheet-paper" width="44" height="19.052559" fill="white"/>
          <g id="land"><path id="base" d="M 0 0 L 1 1" style="fill:#cccccc;fill-opacity:0"/>
          <g id="country-values"><path id="metric" data-value="47" d="M 2 2 L 3 3" fill="#0088ff"/></g></g>
          <g id="native-swarm" fill="#00aabb" fill-opacity=".05"><circle id="member" cx="10" cy="20" r="3"/></g>
          <g id="labels"><text x="2" y="3" font-size=".3" fill="black">A &amp; B</text></g>
          <g id="locator-land"><path id="locator" d="M 4 4 L 5 5" fill="green"/></g></svg>'''
        stream = io.StringIO()
        xml.sax.parseString(fixture, Theme(stream, self.recipe, 'map'))
        after = E.fromstring(stream.getvalue().encode())
        self.assertEqual(after.xpath('//*[@id="metric"]')[0].get('fill'), '#0088ff')
        self.assertEqual(after.xpath('//*[@id="native-swarm"]')[0].get('fill'), '#00aabb')
        self.assertEqual(after.xpath('//*[@id="native-swarm"]')[0].get('fill-opacity'), '.05')
        self.assertEqual(css(after.xpath('//*[@id="base"]')[0].attrib)['fill-opacity'], '0')
        self.assertEqual(css(after[0].attrib)['fill'], '#240413')
        self.assertEqual(css(after.xpath('//text')[0].attrib)['fill'], '#fcc553')
        self.assertEqual(after.xpath('//text')[0].text, 'A & B')
        self.assertEqual(css(after.xpath('//*[@id="locator"]')[0].attrib)['fill'], '#47231d')
        self.assertEqual(dict(after.xpath('//*[@id="member"]')[0].attrib),
                         {'id': 'member', 'cx': '10', 'cy': '20', 'r': '3'})

    def test_groundstation_default_uses_selected_source_and_replaces_both_viewports(self):
        ground = builder.GROUNDSTATIONS
        config = groundstation_settings(STYLE)
        self.assertEqual(config['radius_spread_multiplier'], 2)
        self.assertEqual(len(set(config['capability_markers'].values())), 9)
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            def feature(identifier, folder, fields, geometry):
                return {'id':identifier, 'properties':{'Name':identifier, 'folder_path':[folder],
                        'extended_data':[{'name':k,'value':v} for k,v in fields]}, 'geometry':geometry}
            document = {'features':[
                feature('known', 'North America', [('Freq','Ka'),('Ka Antenna Size','1.85'),('Ka Antenna Count','40')],
                        {'type':'Point','coordinates':[10,5]}),
                feature('unknown', 'North America', [], {'type':'Point','coordinates':[20,5]}),
                feature('pop', 'PoPs & Backbone', [], {'type':'Point','coordinates':[30,5]}),
                feature('link', 'PoPs & Backbone', [], {'type':'LineString','coordinates':[[10,5],[30,5]]})]}
            data = work/'selected.geojson'; data.write_text(json.dumps(document))
            profile = work/'profile.json'
            profile.write_text(json.dumps({'source':{'geojson':data.name, 'gateways_sha256':builder.digest(data),
                                                     'datestamp':'20990101'}}))
            source = work/'native.svg'
            source.write_text('''<svg xmlns="http://www.w3.org/2000/svg">
                <g id="terrestrial-land"><path d="M 0 0 L 1 1"/></g>
                <g id="starlink-gateways-old"><polygon data-groundstation="true" points="0,0 1,1 2,0"/></g>
                <g id="starlink-gateway-links"><path data-gateway-link="true" d="M 10 5 L 30 5"/></g></svg>''')
            with patch.object(ground, 'Projection') as projection:
                projection.return_value.project.side_effect = lambda points: points
                native, evidence = ground.prepare(source, work, self.recipe, profile_path=profile)
            self.assertEqual(evidence['source_date'], '20990101')
            self.assertEqual(evidence['summary']['source_records'], 4)
            self.assertEqual(evidence['source_sha256'], builder.digest(data))
            for bank in ('source-cartography', 'source-content'):
                root = E.fromstring(f'''<svg xmlns="http://www.w3.org/2000/svg">
                    <defs><g id="{bank}"/></defs><g id="antarctica-consolidated-inset"/>
                    <g id="viewport" transform="scale(3)"/></svg>'''.encode())
                ground.replace_source(root, native)
                self.assertFalse(root.xpath('//*[@id="terrestrial-land" or @id="antarctica-consolidated-inset" or @id="starlink-gateways-old"]'))
                sites = root.xpath('//*[@data-groundstation="true"]')
                self.assertEqual({n.get('data-record-id') for n in sites}, {'known','unknown'})
                self.assertEqual(len(root.xpath('//*[@data-kind="pop"]')), 1)
                self.assertEqual(root.xpath('//*[@data-gateway-link="true"]')[0].get('d'), 'M 10 5 L 30 5')
                self.assertEqual(root.xpath('//*[@id="viewport"]')[0].get('transform'), 'scale(3)')

    def test_japan_type_is_physical_not_enlarged(self):
        base = E.fromstring(b'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
          <defs><g id="source-content"/></defs><g transform="scale(3)"><use xlink:href="#source-content"/></g></svg>''')
        approved = E.fromstring(b'''<svg xmlns="http://www.w3.org/2000/svg"><defs><g id="source-cartography">
          <g id="starlink-id"><text x="2" y="3" font-size=".1">12345</text></g></g></defs></svg>''')
        builder.japan_source(base, approved, 'orbital-technosphere-global', self.config, self.recipe)
        label = base.xpath('//*[local-name()="text"]')[0]
        self.assertAlmostEqual(float(label.get('font-size'))*72*3, 6)
        self.assertEqual((label.get('x'), label.get('y'), label.text), ('2', '3', '12345'))

    def test_setouchi_observer_retains_points_and_separates_names(self):
        root = E.fromstring(b'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
          <defs><g id="source-content"><g id="objects-active">
          <circle cx="10" cy="4" r=".02" data-norad-id="100" data-name="STARLINK-1" data-groups="active,starlink" data-role="megaconstellation" style="fill:rgb(1,2,3);fill-opacity:.88"/>
          <circle cx="20" cy="8" r=".02" data-norad-id="200" data-name="INTELSAT-1" data-groups="intelsat" data-role="communications" style="fill:rgb(1,2,3)"/>
          <circle cx="21" cy="9" r=".02" data-norad-id="300" data-name="SENSOR" data-groups="active" data-role="earth-observation" style="fill:rgb(4,5,6)"/>
          <circle cx="22" cy="9" r=".02" data-norad-id="400" data-name="DEBRIS" data-groups="debris" data-role="debris" style="fill:rgb(4,5,6)"/>
          </g><g id="labels"><text>Old capped labels</text></g></g></defs>
          <g transform="scale(.5)"><use xlink:href="#source-content"/></g></svg>''')
        groups = builder.observer_groups(root, self.recipe)
        shapes = {n.get('data-norad-id'): n.get('data-marker-shape') for n in root.xpath('//*[@data-marker-shape]')}
        self.assertEqual(shapes, {'100': 'sunburst', '200': 'square', '300': 'triangle', '400': 'x'})
        self.assertEqual(groups['starlink'][1].get('style'), 'display:inline')
        self.assertEqual(groups['intelsat'][1].get('style'), 'display:none')
        self.assertAlmostEqual(float(groups['starlink'][1][0].get('font-size'))*72*.5, 6)
        self.assertEqual(groups['starlink'][2][0].get('data-source-center'), '10.0 4.0')
        self.assertEqual(groups['starlink'][2][0].get('data-marker-linear-scale'), '1.5')
        debris = root.xpath('//*[@data-norad-id="400" and @data-marker-shape]')[0]
        self.assertEqual(css(debris.attrib)['stroke'], '#000000')
        self.assertEqual(css(debris.attrib)['stroke-opacity'], '1')
        self.assertEqual(len(root.xpath('//*[@data-source-center]')), 4)
        self.assertNotEqual(css(groups['starlink'][2][0].attrib)['fill'], css(groups['intelsat'][2][0].attrib)['fill'])


if __name__ == '__main__':
    unittest.main()
