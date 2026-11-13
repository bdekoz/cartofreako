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
from atlas_presentation import Theme, settings, css, groundstation_settings, groundstation_background, orbital_presentation
from lxml import etree as E
from cartofreako_style import STYLE

builder = importlib.import_module('build-atlas-defaults')
world = importlib.import_module('atlas_world')
exporter = importlib.import_module('export-setouchi-sheets')


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

    def test_submarine_routes_and_landings_use_light_dyad_without_changing_status(self):
        fixture = '''<svg><g id="network-fiber"><path id="route" d="M 0 0 L 1 1"
          style="fill:none;stroke:rgb(0, 0, 0);stroke-width:.02;stroke-dasharray:.09 .055"/></g>
          <g id="network-fiber-landings"><circle id="landing" cx="1" cy="1" r=".1" fill="black"/></g>
          <g id="network-fiber-itu-terrestrial"><path id="land-route" stroke="rgb(76,187,23)"/></g>
          <g id="unrelated"><path id="other" stroke="#000000"/></g></svg>'''
        for pair in ('wine-amber', 'ultramarine-porcelain'):
            profile = copy.deepcopy(STYLE)
            profile['atlas']['presentation']['default_palette'] = pair
            recipe = settings(profile)[1]
            stream = io.StringIO()
            xml.sax.parseString(fixture, Theme(stream, recipe, 'map', subject='network-fiber'))
            after = E.fromstring(stream.getvalue().encode())
            route = after.xpath('//*[@id="route"]')[0]
            self.assertEqual(css(route.attrib)['stroke'], recipe['text'])
            self.assertEqual(css(route.attrib)['stroke-dasharray'], '.09 .055')
            self.assertEqual(css(route.attrib)['stroke-width'], '.02')
            self.assertEqual(route.get('d'), 'M 0 0 L 1 1')
            self.assertEqual(after.xpath('//*[@id="landing"]')[0].get('fill'), recipe['text'])
            self.assertEqual(after.xpath('//*[@id="land-route"]')[0].get('stroke'), 'rgb(76,187,23)')
            self.assertEqual(after.xpath('//*[@id="other"]')[0].get('stroke'), '#000000')

    def test_groundstation_native_ocean_uses_dark_dyad_and_preserves_markers(self):
        root = E.fromstring(b'<svg><g id="network-groundstations-background"><rect id="ocean" style="fill:rgb(242,244,243);fill-opacity:1"/></g><g id="stations"><circle id="site" fill="#fcc553" cx="1" cy="2" r=".1"/></g></svg>')
        site = E.tostring(root.xpath('//*[@id="site"]')[0])
        groundstation_background(root, self.recipe)
        self.assertEqual(css(root.xpath('//*[@id="ocean"]')[0].attrib)['fill'], self.recipe['background'])
        self.assertEqual(E.tostring(root.xpath('//*[@id="site"]')[0]), site)

    def test_setouchi_orbital_context_removes_repeated_inset_and_preserves_data_paint(self):
        fixture=b'''<svg xmlns="http://www.w3.org/2000/svg"><rect id="sheet-paper" fill="#240413"/>
          <defs><g id="source-cartography"><g id="orbital-image-frame" transform="translate(.25 .1) scale(.9886)">
          <g id="terrestrial-background"><rect width="44" height="19.052559" fill="#fcc553"/></g>
          <g id="terrestrial-land"><path id="land" d="M 1 1 L 2 1 L 2 2 Z" fill="#47231d"/></g>
          <circle id="satellite" data-norad-id="123" cx="12" cy="4" r=".02" fill="#ff4a18"/>
          <text x="12" y="4" fill="#fcc553">123</text></g></g></defs>
          <g id="st2-image-frame" transform="translate(.25 .1) scale(.9886)"><use href="#source-cartography"/></g></svg>'''
        for stem,ground in [('orbital-technosphere-global','rgb(242,244,243)'),
                            ('orbital-technosphere-observer','rgb(148,148,148)')]:
            root=E.fromstring(fixture)
            point=E.tostring(root.xpath('//*[@id="satellite"]')[0])
            orbital_presentation(root,stem,cyclic=True)
            self.assertFalse(root.xpath('//*[@id="terrestrial-background"]'))
            self.assertIsNone(root.xpath('//*[@id="orbital-image-frame"]')[0].get('transform'))
            self.assertEqual(root.xpath('//*[@id="orbital-image-paper"]')[0].get('fill'),ground)
            self.assertEqual(css(root.xpath('//*[@id="sheet-paper"]')[0].attrib)['fill'],'#ffffff')
            self.assertEqual(css(root.xpath('//*[@id="land"]')[0].attrib)['fill'],'rgb(216,221,219)')
            self.assertEqual(E.tostring(root.xpath('//*[@id="satellite"]')[0]),point)
            before=E.tostring(root)
            orbital_presentation(root,stem,cyclic=True)
            self.assertEqual(E.tostring(root),before)

    def test_current_resource_panel_uses_page_ink_pair_without_changing_swatches(self):
        current = importlib.import_module('build-current-atlas')
        fixture = ('<svg><g id="source-legend">'
                   '<rect id="resource-legend-panel" style="fill:white;fill-opacity:.96"/>'
                   '<rect id="measured-swatch" data-resource-legend-swatch="true" '
                   'style="fill:#ff1493;fill-opacity:1"/>'
                   '<text>2022 / source period</text></g></svg>')
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory)/'source.svg', Path(directory)/'target.svg'
            source.write_text(fixture)
            for kind in ('map', 'legend'):
                current.current_theme(source, target, self.recipe, kind)
                after = E.parse(str(target))
                panel = css(after.xpath('//*[@id="resource-legend-panel"]')[0].attrib)
                self.assertEqual(panel['fill'], self.recipe['background'])
                self.assertEqual(panel['fill-opacity'], '1')
                self.assertEqual(css(after.xpath('//*[@id="measured-swatch"]')[0].attrib),
                                 {'fill': '#ff1493', 'fill-opacity': '1'})
                self.assertEqual(css(after.xpath('//text')[0].attrib)['fill'], self.recipe['text'])
                self.assertEqual(after.xpath('//text')[0].text, '2022 / source period')

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
                native, evidence = ground.prepare(native, work, self.recipe, profile_path=profile)
            ids=ground.S.read_svg(native).xpath('//*[@id]/@id')
            self.assertEqual(len(ids),len(set(ids)))
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

    def test_world_adapter_preserves_selected_epoch_and_objects_with_a3_keys(self):
        source=E.fromstring(b'''<svg xmlns="http://www.w3.org/2000/svg"><g id="source-cartography">
          <metadata id="orbital-technosphere-metadata" data-timestamp="2099-01-02T03:04:05Z"
             data-visible-records="1" data-skipped-stale="0" data-failed-propagation="0"/>
          <g id="terrestrial-land"><path d="M 1 1 L 2 1 L 2 2 L 1 2 Z"/></g>
          <g data-display-group="objects-debris" data-object-count="1">
          <path d="M 10 5 L 10.1 5.1 M 10 5.1 L 10.1 5" data-object-kind="locpoint"
            data-norad-id="123" data-role="debris" data-marker-shape="x"
            style="fill:none;stroke:#000000;stroke-width:.01"/>
          </g></g></svg>''')
        with tempfile.TemporaryDirectory() as directory:
            work=Path(directory)
            profile=work/'profile.json';profile.write_text('{"catalogs":{"groups":[]}}')
            for stem in ('orbital-technosphere-observer','orbital-technosphere-global'):
                root,key,_=world.compose(stem,source,work,self.recipe,orbital_profile=profile,styled=True)
                points=root.xpath('//*[@data-object-kind="locpoint"]')
                self.assertEqual(len(points),1)
                self.assertEqual(points[0].get('d'),source.xpath('//*[@data-object-kind="locpoint"]')[0].get('d'))
                self.assertEqual(root.get('data-calculation-or-source-date'),'2099-01-02T03:04:05Z')
                self.assertEqual(css(points[0].attrib)['stroke'],'#ffffff')
                self.assertAlmostEqual(float(key.get('width')[:-2])*25.4,420)
                self.assertAlmostEqual(float(key.get('height')[:-2])*25.4,297)
                self.assertEqual(key.xpath('//*[@id="sheet-paper"]')[0].get('fill'),'#fcc553')
                debris_label=next(n for n in key.xpath('//*[local-name()="text"]') if 'debris /' in (n.text or '').lower())
                self.assertEqual(css(debris_label.getprevious()[0].attrib)['stroke'],'#ffffff')
                if stem.endswith('observer'):
                    notes=' '.join(key.xpath('//*[local-name()="text"]/text()'))
                    self.assertIn('Cyclic framing',notes)
                    self.assertIn('zero-degree elevation',notes)

    def test_export_dimensions_follow_physical_page_size(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'sheet.svg'
            for width,height,expected in (('44in','19.052559in',(13200,5716)),
                                           ('420mm','297mm',(4961,3508))):
                path.write_text(f'<svg width="{width}" height="{height}"/>')
                self.assertEqual(exporter.sheet_pixels(path),expected)


if __name__ == '__main__':
    unittest.main()
