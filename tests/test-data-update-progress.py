#!/usr/bin/env python3
"""Operational reports preserve schedules and separate pacing estimates from failures."""
import hashlib
import importlib.util
import io
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
    def test_scheduled_report_is_silent_without_main_update_even_with_cpc_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(sys, 'argv', ['report', '--root', folder, '--scheduled', '--notify']), \
                    patch.object(progress, 'writer_running', return_value=False), \
                    patch.object(progress, 'held_lock', return_value=True), \
                    patch.object(progress, 'snapshot') as snapshot, \
                    patch.object(progress, 'notify_user') as notify, \
                    patch.object(progress, 'configure_hourly') as configure, \
                    patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(progress.main(), 0)
            self.assertEqual(output.getvalue(), '')
            self.assertFalse((root/'reports').exists())
            snapshot.assert_not_called()
            notify.assert_not_called()
            configure.assert_not_called()

    def test_scheduled_report_runs_during_update_and_preserves_schedule(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            state = self.fixture(root)
            state['status'] = 'active'
            progress.atomic_json(root/'runs/run-fixture/state.json', state)
            with patch.object(sys, 'argv', ['report', '--root', folder, '--scheduled', '--notify']), \
                    patch.object(progress, 'writer_running', return_value=True), \
                    patch.object(progress, 'notify_user') as notify, \
                    patch.object(progress, 'configure_hourly') as configure, \
                    patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(progress.main(), 0)
            self.assertTrue(output.getvalue().strip())
            self.assertTrue((root/'reports/progress-latest.json').is_file())
            notify.assert_called_once()
            configure.assert_not_called()

    def test_manual_report_remains_available_without_main_update(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            with patch.object(sys, 'argv', ['report', '--root', folder]), \
                    patch.object(progress, 'writer_running', return_value=False), \
                    patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(progress.main(), 0)
            self.assertIn('ETA unavailable while the update is stopped', output.getvalue())
            self.assertTrue((root/'reports/progress-latest.json').is_file())

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

    def test_resilient_report_shows_running_source_and_deferred_work(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            state=self.fixture(root)
            state.update(current_source='resources',issues={
                'astronomy':{'status':'deferred','reason':'explicitly deferred for this invocation'}})
            state['sources']=[r for r in state['sources'] if r['id']!='astronomy']
            progress.atomic_json(root/'runs/run-fixture/state.json',state)
            with patch.object(progress,'writer_running',return_value=True):
                value=progress.snapshot(root,1794265200)
            text=progress.report(value,None)
        self.assertEqual(value['phase'],'resources')
        self.assertIn('Source astronomy: deferred',text)

    def test_stopped_run_does_not_receive_active_completion_estimate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            with patch.object(progress, 'writer_running', return_value=False):
                value = progress.snapshot(root, 1794265200)
            text = progress.report(value, None)
        self.assertIn('ETA unavailable while the update is stopped', text)
        self.assertNotIn('CPC pacing-model ETA:', text)

    def test_pinned_archive_counts_as_cached_and_needs_no_provider_request(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            with patch.object(progress, 'writer_running', return_value=True):
                before = progress.snapshot(root, 1794265200)
                obj = root/'cache/sha256'/('a'*64)
                obj.parent.mkdir(parents=True)
                obj.write_bytes(b'archive')
                progress.atomic_json(root/'cache/cpc-archive/manifest.json', {
                    'files': {'tmin.1979.nc': {'sha256': 'a'*64, 'bytes': 7}}})
                after = progress.snapshot(root, 1794265200)
        self.assertEqual(after['cached'], 1)
        self.assertEqual(after['pinned_archives'], 1)
        self.assertIsNone(after['partial'])
        self.assertLess(after['remaining_requests'], before['remaining_requests'])

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

    def test_daily_backfill_progress_is_visible_while_main_update_is_stopped(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.fixture(root)
            obj=root/'cache/sha256'/('b'*64)
            obj.parent.mkdir(parents=True)
            obj.write_bytes(b'current')
            progress.atomic_json(root/'cache/cpc-current/tmin.2026.json', {
                'sha256':'b'*64,'bytes':7,'data_through':'2026-08-04',
                'pending_start':'2026-08-05','pending_through':'2026-08-06',
                'inventory_checked_at':'2026-11-09T00:00:00Z'})
            part=root/'cache/cpc-current/parts/tmin.2026/2026-08-05.nc'
            part.parent.mkdir(parents=True)
            part.write_bytes(b'new day')
            progress.atomic_json(part.with_name(part.name+'.receipt.json'),{})
            with patch.object(progress,'writer_running',return_value=False), patch.object(progress,'held_lock',return_value=True):
                value=progress.snapshot(root,1794265200)
            text=progress.report(value,None)
        self.assertEqual(value['cpc_workers'],['tmin'])
        self.assertEqual(value['current_year']['tmin.2026.nc']['cached_days'],1)
        self.assertIn('1/2 missing days cached',text)
        self.assertIn('CPC pacing-model ETA:',text)

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
