#!/usr/bin/env python3
"""Check observed-value opacity, unchanged cell geometry, and archive guards."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from setouchi_radiation import LAYER, SVG, apply_opacity, band_for


class RadiationTests(unittest.TestCase):
    def setUp(self):
        self.settings = {'bands': 100, 'scale_min': 0, 'scale_max': 400}
        root = etree.Element('{' + SVG + '}svg')
        etree.SubElement(root, '{' + SVG + '}metadata', {
            'id': 'cloud-atmosphere-metadata', 'data-feature-count': '12', 'data-h3-resolution': '3',
            'data-observation-jaxa-jasmes-swr-end': '2026-10-15T23:59:00Z'})
        group = etree.SubElement(root, '{' + SVG + '}g', id=LAYER)
        self.data = {'observation_end_utc': '2026-10-15T23:59:00Z', 'feature_count': 12,
                     'h3_resolution': 3, 'missing_semantics': 'unobserved-not-zero', 'cells': []}
        for source_bin in range(1, 7):
            paths = []
            for offset in range(2):
                x = source_bin * 10 + offset
                path = f'M {x} 0 L {x + 1} 0 L {x} 1 Z '
                value = (source_bin - 1) * 400 / 6 + (10 if offset == 0 else 40)
                self.data['cells'].append({'h3': f'fixture-{x}', 'value': value, 'valid_fraction': 0.8,
                                          'source_bin': source_bin, 'path': path})
                paths.append(path)
            etree.SubElement(group, '{' + SVG + '}path', {
                'id': f'{LAYER}-bin-{source_bin}', 'data-bin': str(source_bin), 'data-cell-count': '2',
                'd': ''.join(paths), 'style': f'fill:none;stroke:#f0bd45;stroke-opacity:0.24;stroke-width:0.0{source_bin}'})
        self.tree = etree.ElementTree(root)

    def test_full_scale_has_one_hundred_distinct_monotone_levels(self):
        values = [400 * i / 99 for i in range(100)]
        self.assertEqual([band_for(v, self.settings) for v in values], list(range(100)))
        self.assertEqual(band_for(-1, self.settings), 0)
        self.assertEqual(band_for(401, self.settings), 99)
        self.assertGreater(band_for(240, self.settings), band_for(200, self.settings))
        for v in (float('nan'), float('inf')):
            with self.assertRaises(ValueError): band_for(v, self.settings)

    def test_each_observation_controls_its_opacity_without_changing_geometry_or_width(self):
        result = apply_opacity(self.tree, self.data, self.settings)
        paths = self.tree.xpath('//*[@data-opacity-band]')
        self.assertEqual(result['bands'], 100)
        self.assertEqual(result['observed_cells'], 12)
        self.assertEqual(sum(result['band_cell_counts']), 12)
        self.assertEqual(len(paths), 12)  # The two cells in each former band now differ.
        self.assertCountEqual([p.get('d') for p in paths], [c['path'] for c in self.data['cells']])
        by_geometry = {c['path']: c for c in self.data['cells']}
        for path in paths:
            cell = by_geometry[path.get('d')]
            style = dict(part.split(':', 1) for part in path.get('style').split(';'))
            self.assertEqual(style['stroke-width'], f'0.0{cell["source_bin"]}')
            self.assertEqual(style['stroke'], '#f0bd45')
            self.assertAlmostEqual(float(style['stroke-opacity']), band_for(cell['value'], self.settings) / 99, places=8)

    def test_date_mismatch_stops_before_mutation(self):
        before = etree.tostring(self.tree)
        self.data['observation_end_utc'] = '2026-07-31T23:59:00Z'
        with self.assertRaisesRegex(ValueError, 'provenance'):
            apply_opacity(self.tree, self.data, self.settings)
        self.assertEqual(etree.tostring(self.tree), before)

    def test_changed_geometry_stops_before_mutation(self):
        before = etree.tostring(self.tree)
        self.data['cells'][0]['path'] = 'M 999 999 L 1000 999 L 999 1000 Z '
        with self.assertRaisesRegex(ValueError, 'geometry'):
            apply_opacity(self.tree, self.data, self.settings)
        self.assertEqual(etree.tostring(self.tree), before)

    def test_duplicate_and_insufficient_quality_cells_are_rejected(self):
        for key, value in [('h3', self.data['cells'][1]['h3']), ('valid_fraction', 0.1)]:
            data = deepcopy(self.data)
            data['cells'][0][key] = value
            with self.assertRaisesRegex(ValueError, 'quality'):
                apply_opacity(self.tree, data, self.settings)

    def test_missing_observations_are_not_fabricated(self):
        data = deepcopy(self.data)
        data['cells'].pop()
        with self.assertRaisesRegex(ValueError, 'geometry'):
            apply_opacity(self.tree, data, self.settings)
        data = deepcopy(self.data)
        data['missing_semantics'] = 'missing-is-zero'
        with self.assertRaisesRegex(ValueError, 'provenance'):
            apply_opacity(self.tree, data, self.settings)


if __name__ == '__main__':
    unittest.main()
