#!/usr/bin/env python3
"""Keep frozen atlas identities while selecting the actual released metric period."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
atlas = importlib.import_module('build-current-atlas')
from dataset import DatasetError


class SourceSelection(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.profile_path = Path(temporary.name)/'resources-profile.json'
        self.profile = {'families': [
            {'id': 'resources-food', 'metrics': [
                {'id': 'food-production-index', 'output_tag': 'food-production-index-2022',
                 'reference_period': '2022', 'status': 'default'}]},
            {'id': 'resources-flora', 'metrics': [
                {'id': 'forest-area-percent', 'output_tag': 'forest-area-percent-2023',
                 'reference_period': '2023', 'status': 'default'}]},
            {'id': 'resources-fauna', 'metrics': [
                {'id': 'coral-reef-threat', 'output_tag': 'coral-reef-threat-2011',
                 'reference_period': 'Reefs at Risk Revisited 2011', 'status': 'released'}]}]}

    def resolve(self, stem, ident=None):
        self.profile_path.write_text(json.dumps(self.profile))
        original = {'id': ident or stem, 'source_stem': stem, 'title': 'Fixture'}
        frozen = deepcopy(original)
        result = atlas.resolve_catalog_sources([original], self.profile_path)[0]
        self.assertEqual(original, frozen)
        self.assertEqual(result['id'], original['id'])
        return result

    def test_dated_food_and_forest_names_use_selected_reference_period(self):
        for old, new, period in [
            ('resources-food-food-production-index-latest-2024', 'resources-food-food-production-index-2022', '2022'),
            ('resources-flora-forest-area-percent-2024', 'resources-flora-forest-area-percent-2023', '2023')]:
            with self.subTest(stem=old):
                result = self.resolve(old)
                self.assertEqual(result['source_stem'], new)
                self.assertEqual(result['source_reference_period'], period)
                self.assertEqual(result['catalog_source_stem'], old)

    def test_later_snapshot_changes_the_source_without_a_hardcoded_year(self):
        metric = self.profile['families'][0]['metrics'][0]
        metric.update(output_tag='food-production-index-2023', reference_period='2023')
        result = self.resolve('resources-food-food-production-index-latest-2024')
        self.assertEqual(result['source_stem'], 'resources-food-food-production-index-2023')
        self.assertEqual(result['source_reference_period'], '2023')

    def test_reef_source_uses_native_anthropocene_namespace(self):
        result = self.resolve('resources-fauna-coral-reef-threat-2011', 'anthropocene-coral-reef-threat-2011')
        self.assertEqual(result['source_stem'], result['id'])
        self.assertEqual(result['source_reference_period'], 'Reefs at Risk Revisited 2011')

    def test_unreleased_or_missing_metrics_are_rejected(self):
        self.profile['families'][0]['metrics'][0]['status'] = 'supplemental'
        with self.assertRaisesRegex(DatasetError, 'missing or ambiguous'):
            self.resolve('resources-food-food-production-index-latest-2024')
        with self.assertRaisesRegex(DatasetError, 'missing or ambiguous'):
            self.resolve('resources-food-invented-measure-2024')

    def test_ambiguous_compatible_metrics_are_rejected(self):
        metric = deepcopy(self.profile['families'][0]['metrics'][0])
        metric['output_tag'] = 'food-production-index-2023'
        self.profile['families'][0]['metrics'].append(metric)
        with self.assertRaisesRegex(DatasetError, 'missing or ambiguous'):
            self.resolve('resources-food-food-production-index-latest-2024')

    def test_exact_released_tag_takes_precedence(self):
        metric = deepcopy(self.profile['families'][0]['metrics'][0])
        metric['output_tag'] = 'food-production-index-2023'
        self.profile['families'][0]['metrics'].append(metric)
        result = self.resolve('resources-food-food-production-index-2022')
        self.assertEqual(result['source_stem'], 'resources-food-food-production-index-2022')


if __name__ == '__main__':
    unittest.main()
