#!/usr/bin/env python3
"""Operational reports preserve schedules and separate pacing estimates from failures."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('progress', ROOT/'tools/report-data-update-progress.py')
progress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(progress)


class Reports(unittest.TestCase):
    def test_install_is_idempotent_and_preserves_other_cron_entries(self):
        original = 'MAILTO=local\n0 4 * * * /usr/bin/echo existing\n15 * * * * /usr/bin/true\n'
        installed = progress.cron_contents(original, '/usr/bin/python3 /project/report --scheduled')
        again = progress.cron_contents(installed, '/usr/bin/python3 /project/report --scheduled')
        self.assertEqual(installed, again)
        self.assertTrue(installed.startswith(original))
        self.assertEqual(installed.count(progress.BEGIN), 1)
        self.assertIn('0 * * * * /usr/bin/python3', installed)
        removed = progress.cron_contents(installed)
        self.assertEqual(removed.strip(), original.strip())

    def test_pacing_model_accounts_for_recovery_and_floor(self):
        self.assertEqual(progress.pacing_seconds(20, 60, 0), 1140)
        self.assertEqual(progress.pacing_seconds(10, 2, 0), 20)
        self.assertEqual(progress.pacing_seconds(0, 60, 0), 0)
        self.assertLess(progress.pacing_seconds(100, 60, 9), 6000)

    def fixture(self, root):
        state = {'dataset_id': 'run-fixture', 'status': 'preparing',
                 'sources': [{'id': name} for name in ('natural-earth', 'orbital', 'astronomy')]}
        journal = root/'runs/run-fixture/state.json'
        progress.atomic_json(journal, state)
        raw = root/'editions/run-fixture/inputs/anthropocene/.raw/cpc'
        raw.mkdir(parents=True)
        (raw/'tmax.1979.nc').write_bytes(b'complete')
        url = 'https://psl.noaa.gov/thredds/fileServer/Datasets/cpc_global_temp/tmin.1979.nc'
        key = hashlib.sha256((url+'{}').encode()).hexdigest()
        cache = root/'cache/http'
        progress.atomic_json(cache/(key+'.partial.json'), {'bytes': 88_000_000})
        (cache/(key+'.part')).write_bytes(b'partial')
        return state

    def test_snapshot_counts_partial_bytes_and_source_phase_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            with patch.object(progress, 'writer_running', return_value=True):
                value = progress.snapshot(root, 1794265200)
        self.assertEqual(value['complete'], 1)
        self.assertEqual(value['downloaded_bytes'], 15)
        self.assertEqual(value['partial']['name'], 'tmin.1979.nc')
        self.assertEqual(value['phase'], 'anthropocene')
        self.assertEqual(len(value['completed_sources']), 3)

    def test_stopped_run_does_not_receive_active_completion_estimate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            with patch.object(progress, 'writer_running', return_value=False):
                value = progress.snapshot(root, 1794265200)
            text = progress.report(value, None)
        self.assertIn('ETA unavailable while the update is stopped', text)
        self.assertNotIn('CPC pacing-model ETA:', text)

    def test_report_names_eta_assumptions_and_local_timezone(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            with patch.object(progress, 'writer_running', return_value=True):
                value = progress.snapshot(root, 1794265200)
            text = progress.report(value, None)
        self.assertIn('PST', text)
        self.assertIn('no renewed 429s', text)
        self.assertIn('ETA covers CPC only', text)

    def test_cpc_completion_does_not_claim_entire_update_is_finished(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            with patch.object(progress, 'writer_running', return_value=True):
                value = progress.snapshot(root, 1794265200)
            value['complete'] = 96
            text = progress.report(value, None)
        self.assertIn('CPC downloads complete', text)
        self.assertIn('Remaining source preparation/validation', text)


if __name__ == '__main__':
    unittest.main()
