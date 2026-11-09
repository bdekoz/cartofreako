#!/usr/bin/env python3
"""Astronomy presentation must retain scientific geometry and source epochs."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import re

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('astro_setouchi', ROOT/'scripts/build-astro-setouchi-plates.py')
plates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plates)
from atlas_presentation import css


class Presentation(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.config, self.recipe = plates.settings(plates.STYLE)
        self.profile = {'timestamp': '2026-11-09T17:31:33Z',
                        'observer': {'kind': 'terrestrial', 'name': 'San Francisco, California, USA',
                                     'latitude_deg': 37.7749, 'longitude_deg_east': -122.4194},
                        'instrumentation': {'name': 'Generic ground multi-band reference', 'bands': ['optical']},
                        'dynamic_events': {'lookback_days': 7}}

    def fixture(self, width=44, height=19.052559):
        root = plates.el('svg', width=f'{width}in', height=f'{height}in', viewBox=f'0 0 {width} {height}')
        plates.el('metadata', root, id='astro-metadata', data_timestamp=self.profile['timestamp'],
                  data_sun_altitude_deg=26, data_profile='astro-profile.json', data_observer_kind='terrestrial')
        bg = plates.el('g', root, id='astronomy-background')
        plates.el('rect', bg, width=width, height=height, fill='#000000')
        for key in plates.LAYERS:
            group = plates.el('g', root, id=key)
            if key == 'stars':
                plates.el('circle', group, id='star-fixture', cx=7, cy=8, r=.05,
                          style='fill:rgb(255,165,0);fill-opacity:.92', data_kind='star',
                          data_ra_deg=83, data_dec_deg=20, data_source='https://gea.esac.esa.int/archive/')
        labels = plates.el('g', root, id='labels')
        plates.el('text', labels, x=7.1, y=8, font_size='.17pt').text = 'Source star label'
        source = self.root/'native.svg'
        plates.save(root, source)
        return source

    def test_scientific_layers_colors_and_label_coordinates_survive_theme(self):
        source = self.fixture()
        output = self.root/'maps/map.svg'
        original = plates.make_map(source, output, self.root/'legends/legend.svg', self.recipe, 12)
        actual = plates.parse(output)
        self.assertEqual(plates.scientific_layers(original), plates.scientific_layers(actual))
        self.assertEqual(actual.xpath('//*[@id="star-fixture"]/@data-ra-deg'), ['83'])
        label = actual.xpath('//*[@id="labels"]/*')[0]
        self.assertEqual((label.get('x'), label.get('y'), label.text), ('7.1', '8', 'Source star label'))
        self.assertEqual(css(label.attrib)['fill'], '#fcc553')
        scale = float(actual.get('data-image-scale'))
        self.assertAlmostEqual(scale*float(label.get('font-size'))*72, 12)
        self.assertAlmostEqual(scale*44, 43.5)

    def test_portrait_projection_is_retained_without_cropping_or_stretching(self):
        source = self.fixture(34, 44)
        output = self.root/'map.svg'
        plates.make_map(source, output, self.root/'legend.svg', self.recipe, 12)
        root = plates.parse(output)
        self.assertEqual(plates.dimensions(root), (34, 44))
        self.assertAlmostEqual(float(root.get('data-image-scale'))*44, 43.5)

    def test_legend_uses_actual_counts_observer_date_and_source_glyph(self):
        source = plates.parse(self.fixture())
        output = self.root/'legend.svg'
        counts = plates.make_legend(source, output, self.root/'maps/map.svg', 'Astronomy / fixture',
                                    self.profile, self.recipe, 'a'*64)
        self.assertEqual(counts, {'star': 1})
        legend = plates.parse(output)
        words = ' '.join(legend.xpath('//*[local-name()="text"]/text()'))
        self.assertIn('2026-11-09T17:31:33Z', words)
        self.assertIn('San Francisco', words)
        self.assertIn('Star / 1', words)
        glyph = legend.xpath('//*[@data-legend-kind="star"]/*')[0]
        self.assertEqual(glyph.get('style'), source.xpath('//*[@data-kind="star"]')[0].get('style'))
        self.assertEqual(legend.get('data-input-manifest-sha256'), 'a'*64)
        self.assertEqual(legend.xpath('//*[@id="astro-metadata"]/@data-timestamp'), [self.profile['timestamp']])

    def test_ray_keys_fit_inside_their_legend_rows(self):
        source = plates.parse(self.fixture())
        group = source.xpath('//*[@id="stars"]')[0]
        rays = plates.el('g', group, id='stationary-rays-star-fixture')
        plates.el('line', rays, x1=7, y1=8, x2=7.15, y2=8, stroke='white')
        output = self.root/'legend.svg'
        plates.make_legend(source, output, self.root/'map.svg', 'Astronomy / fixture',
                           self.profile, self.recipe, 'a'*64)
        glyph = plates.parse(output).xpath('//*[@data-legend-kind="star"]')[0]
        scale = float(re.search(r'scale\(([^)]+)', glyph.get('transform'))[1])
        self.assertLessEqual(scale*.15, .21+1e-10)


if __name__ == '__main__':
    unittest.main()
