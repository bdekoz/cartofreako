#!/usr/bin/env python3
"""Limit remote ocean refreshes and preserve verified local baseline inputs."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from dataset import DatasetError, digest

spec = importlib.util.spec_from_file_location('ocean_fetch', ROOT / 'scripts/fetch-ocean-temperature.py')
ocean = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocean)


class OceanFetch(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.history, self.output = self.root / 'history', self.root / 'edition'
        self.history.mkdir()
        self.names = ['lsmask.oisst.nc', 'sst.day.mean.2023.nc', 'icec.day.mean.2023.nc']
        for name in self.names:
            path = self.history / name
            path.write_bytes(('verified archive: ' + name).encode())
            (self.history / (name + '.json')).write_text(json.dumps({
                'url': ocean.BASE + name, 'sha256': digest(path), 'bytes': path.stat().st_size,
                'shape': [1 if name.startswith('lsmask') else 365, 720, 1440],
                'retrieved_at': '2026-11-08T20:00:00Z',
            }))
        nc = MagicMock()
        nc.__enter__.return_value.shape.side_effect = lambda name: (1 if name == 'lsmask' else 365, 720, 1440)
        self.netcdf = patch.object(ocean, 'NetCDF', return_value=nc)
        self.netcdf.start()
        self.addCleanup(self.netcdf.stop)

    def stage(self):
        return ocean.stage_history(self.history, self.output, start_year=2023, end_year=2023)

    def test_history_is_verified_and_staged_without_network_or_new_freshness_claim(self):
        with patch.object(ocean.requests, 'get') as request:
            records = self.stage()
        request.assert_not_called()
        self.assertEqual(len(records), 3)
        for name, record in zip(self.names, records):
            self.assertEqual((self.output / name).read_bytes(), (self.history / name).read_bytes())
            self.assertEqual(record['cache_policy'], 'pinned-oisst-history')
            self.assertEqual(record['retrieved_at'], '2026-11-08T20:00:00Z')
            self.assertNotIn('checked_at', record)
            self.assertEqual(json.loads((self.output / (name + '.json')).read_text()), record)

    def test_missing_archive_inventory_fails_before_staging(self):
        (self.history / self.names[-1]).unlink()
        with self.assertRaisesRegex(DatasetError, 'Missing local OISST history'):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_corrupted_history_does_not_replace_existing_edition_bytes(self):
        name = self.names[1]
        original = (self.history / name).read_bytes()
        (self.history / name).write_bytes(b'x' * len(original))
        self.output.mkdir()
        (self.output / name).write_bytes(b'previous verified edition')
        with self.assertRaisesRegex(DatasetError, 'Changed local OISST history'):
            self.stage()
        self.assertEqual((self.output / name).read_bytes(), b'previous verified edition')
        self.assertFalse(list(self.output.glob('.*-*')))

    def test_mismatched_receipt_source_is_rejected(self):
        receipt = self.history / (self.names[0] + '.json')
        record = json.loads(receipt.read_text())
        record['url'] = ocean.BASE + 'another-dataset.nc'
        receipt.write_text(json.dumps(record))
        with self.assertRaisesRegex(DatasetError, 'Invalid local OISST history receipt'):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_wrong_native_grid_is_rejected(self):
        with patch.object(ocean, 'NetCDF') as nc:
            nc.return_value.__enter__.return_value.shape.return_value = (1, 360, 720)
            with self.assertRaisesRegex(DatasetError, 'Unexpected local OISST history grid'):
                self.stage()
        self.assertFalse((self.output / self.names[0]).exists())

    def test_default_remote_refresh_is_limited_to_2025_and_2026(self):
        with patch.object(sys, 'argv', ['fetch-ocean-temperature.py', '--output', str(self.output)]), \
             patch.object(ocean, 'fetch', side_effect=lambda name, directory: {'url': ocean.BASE + name}) as fetch:
            ocean.main()
        self.assertEqual({c.args[0] for c in fetch.call_args_list},
                         {'lsmask.oisst.nc', *[f'{v}.day.mean.{y}.nc' for y in (2025, 2026) for v in ('sst', 'icec')]})

    def test_history_mode_only_requests_the_four_target_year_files(self):
        history = [{'url': ocean.BASE + name} for name in self.names]
        with patch.object(sys, 'argv', ['fetch-ocean-temperature.py', '--output', str(self.output),
                                       '--history-dir', str(self.history)]), \
             patch.object(ocean, 'stage_history', return_value=history), \
             patch.object(ocean, 'fetch', side_effect=lambda name, directory: {'url': ocean.BASE + name}) as fetch:
            ocean.main()
        self.assertEqual({c.args[0] for c in fetch.call_args_list},
                         {f'{v}.day.mean.{y}.nc' for y in (2025, 2026) for v in ('sst', 'icec')})
        manifest = json.loads((self.output / 'manifest.json').read_text())
        self.assertEqual(len(manifest['files']), 7)
        self.assertEqual(manifest['failures'], [])

    def test_missing_history_never_falls_back_to_remote_history_downloads(self):
        with patch.object(sys, 'argv', ['fetch-ocean-temperature.py', '--output', str(self.output),
                                       '--history-dir', str(self.root / 'missing')]), \
             patch.object(ocean, 'fetch') as fetch:
            with self.assertRaisesRegex(DatasetError, 'Historical years are never fetched automatically'):
                ocean.main()
        fetch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
