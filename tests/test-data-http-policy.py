#!/usr/bin/env python3
"""Provider pacing, cross-process cooldown and retry-budget regressions."""
from datetime import datetime, timezone
from email.utils import format_datetime
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.request import Request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from dataset import DatasetError
from data_http_policy import Pacer, Progress, open_response, retry_after, setting


class Policy(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.url = 'https://psl.noaa.gov/thredds/fileServer/Datasets/cpc_global_temp/tmax.1981.nc'
        self.env = {'NOAA_HTTP_MIN_INTERVAL': '2', 'NOAA_HTTP_MAX_INTERVAL': '60',
                    'DATA_HTTP_RETRY_BUDGET': '120', 'DATA_HTTP_PROGRESS_INTERVAL': '30'}
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, self.env).start()
        self.clock = SimpleNamespace(now=0.0, sleeps=[])
        self.clock.monotonic = lambda: self.clock.now
        self.clock.time = lambda: 1794240000 + self.clock.now
        def sleep(delay):
            self.clock.sleeps.append(delay)
            self.clock.now += delay
        self.clock.sleep = sleep
        patch('data_http_policy.time', self.clock).start()
        patch('data_http_policy.random.uniform', return_value=1).start()
        self.log = patch('sys.stderr', new_callable=io.StringIO).start()
        self.progress = Progress(self.url)

    def test_request_spacing_is_shared_between_files_and_provider_hosts(self):
        first = Pacer(self.url, self.root)
        second = Pacer('https://downloads.psl.noaa.gov/Datasets/cpc_global_temp/tmin.1981.nc', self.root)
        first.wait(120, self.progress)
        second.wait(120, self.progress)
        self.assertEqual(self.clock.sleeps, [2])
        self.assertEqual(first.path, second.path)

    def test_cooldown_survives_another_downloader_instance(self):
        first = Pacer(self.url, self.root)
        first.defer(90, throttled=True)
        second = Pacer(self.url, self.root)
        second.wait(120, self.progress)
        self.assertEqual(self.clock.now, 90)
        state = json.loads(first.path.read_text())
        self.assertEqual(state['interval'], 4)
        self.assertIn('shared NOAA cooldown', self.log.getvalue())

    def test_success_gradually_recovers_instead_of_resetting_pacing(self):
        pacer = Pacer(self.url, self.root)
        pacer.defer(30, throttled=True)
        pacer.success()
        self.assertEqual(json.loads(pacer.path.read_text())['interval'], 4)
        for _ in range(9):
            pacer.success()
        self.assertEqual(json.loads(pacer.path.read_text())['interval'], 3.6)

    def test_retry_after_supports_seconds_and_http_dates(self):
        self.assertEqual(retry_after('125'), 125)
        date = format_datetime(datetime.fromtimestamp(self.clock.time()+180, timezone.utc), usegmt=True)
        self.assertEqual(retry_after(date), 180)
        self.assertEqual(retry_after('invalid'), 0)

    def test_more_than_five_throttled_retries_fit_configured_time_budget(self):
        with patch.dict(os.environ, {'DATA_HTTP_RETRY_BUDGET': '1800'}):
            pacer = Pacer(self.url, self.root)
            errors = [HTTPError(self.url, 429, 'Too Many Requests', {}, None) for _ in range(6)]
            response = Mock()
            with patch('data_http_policy.urlopen', side_effect=[*errors, response]) as open_url:
                result = open_response(Request(self.url), pacer, self.progress)
        self.assertIs(result, response)
        self.assertEqual(open_url.call_count, 7)
        self.assertEqual(self.clock.now, 1050)
        self.assertIn('retry 6', self.log.getvalue())
        self.assertIn('next retry', self.log.getvalue())

    def test_exhausted_budget_preserves_cooldown_without_extra_request(self):
        with patch.dict(os.environ, {'DATA_HTTP_RETRY_BUDGET': '60'}):
            pacer = Pacer(self.url, self.root)
            def throttled(*args, **kwargs):
                raise HTTPError(self.url, 429, 'Too Many Requests', {}, None)
            with patch('data_http_policy.urlopen', side_effect=throttled) as open_url:
                with self.assertRaisesRegex(DatasetError, 'budget exhausted or insufficient'):
                    open_response(Request(self.url), pacer, self.progress)
        self.assertEqual(open_url.call_count, 2)
        self.assertEqual(self.clock.now, 30)
        self.assertGreater(json.loads(pacer.path.read_text())['next_at'], self.clock.time())

    def test_retry_after_beyond_budget_is_not_shortened(self):
        pacer = Pacer(self.url, self.root)
        error = HTTPError(self.url, 429, 'Too Many Requests', {'Retry-After': '600'}, None)
        with patch('data_http_policy.urlopen', side_effect=error) as open_url:
            with self.assertRaisesRegex(DatasetError, 'budget exhausted or insufficient') as failure:
                open_response(Request(self.url), pacer, self.progress)
        self.assertEqual(open_url.call_count, 1)
        self.assertEqual(json.loads(pacer.path.read_text())['next_at'], self.clock.time()+600)
        self.assertIn('Try again no earlier than', str(failure.exception))
        self.assertIn('make data-update', str(failure.exception))
        self.assertIn('provider Retry-After', self.log.getvalue())

    def test_existing_cooldown_cannot_exceed_request_budget(self):
        pacer = Pacer(self.url, self.root)
        pacer.defer(600, throttled=True)
        with patch('data_http_policy.urlopen') as open_url:
            with self.assertRaisesRegex(DatasetError, 'cooldown exceeds remaining'):
                open_response(Request(self.url), pacer, self.progress)
        open_url.assert_not_called()

    def test_nontransient_error_is_not_retried(self):
        error = HTTPError(self.url, 404, 'Not Found', {}, None)
        with patch('data_http_policy.urlopen', side_effect=error) as open_url:
            with self.assertRaises(HTTPError):
                open_response(Request(self.url), Pacer(self.url, self.root), self.progress)
        self.assertEqual(open_url.call_count, 1)
        error.close()

    def test_invalid_configuration_fails_before_acquisition(self):
        for value in ('nan', 'inf', '-1', 'words', '0'):
            with self.subTest(value=value), patch.dict(os.environ, {'DATA_HTTP_RETRY_BUDGET': value}):
                with self.assertRaises(DatasetError):
                    setting('DATA_HTTP_RETRY_BUDGET', 1800, positive=True)
        with patch.dict(os.environ, {'NOAA_HTTP_MAX_INTERVAL': '1'}):
            with self.assertRaisesRegex(DatasetError, 'must be at least'):
                Pacer(self.url, self.root)

    def test_progress_reports_filename_bytes_elapsed_and_retry_time(self):
        self.progress.offset, self.progress.total = 60817408, 87362645
        self.progress.report('resuming', force=True)
        message = self.log.getvalue()
        self.assertIn('tmax.1981.nc', message)
        self.assertIn('60,817,408/87,362,645 bytes', message)
        self.assertIn('elapsed 0s', message)

    def test_warning_distinguishes_unknown_reset_and_local_retry_time(self):
        error = HTTPError(self.url, 429, 'Too Many Requests', {}, None)
        with patch.dict(os.environ, {'DATA_HTTP_RETRY_BUDGET': '1', 'DATA_UPDATE_RUN_ID': 'fixture-run'}), \
             patch('data_http_policy.urlopen', side_effect=error):
            with self.assertRaises(DatasetError) as failure:
                open_response(Request(self.url), Pacer(self.url, self.root), self.progress)
        self.assertIn('WARNING: HTTP 429 Too Many Requests', self.log.getvalue())
        self.assertIn('provider reset time unknown', self.log.getvalue())
        self.assertIn('next eligible retry', self.log.getvalue())
        self.assertIn('scripts/noaa-cpc-ping.py', self.log.getvalue())
        self.assertIn('noaa-cpc-ping-status.log', self.log.getvalue())
        self.assertIn("make data-update DATA_UPDATE_ARGS='--resume fixture-run'", str(failure.exception))

    def test_throttling_raises_zero_baseline_interval(self):
        with patch.dict(os.environ, {'NOAA_HTTP_MIN_INTERVAL': '0'}):
            pacer = Pacer(self.url, self.root)
            pacer.defer(30, throttled=True)
        self.assertEqual(json.loads(pacer.path.read_text())['interval'], 1)

    def test_independent_processes_share_request_spacing(self):
        # Actual independent interpreters exercise flock and persisted state;
        # virtual time is used only for the long retry tests above.
        code = '''import sys, time
sys.path.insert(0, sys.argv[1])
from data_http_policy import Pacer, Progress
url = 'https://psl.noaa.gov/test'
Pacer(url, sys.argv[2]).wait(time.monotonic()+10, Progress(url))
print(time.time())
'''
        env = {**os.environ, 'NOAA_HTTP_MIN_INTERVAL': '0.1', 'NOAA_HTTP_MAX_INTERVAL': '1'}
        children = [subprocess.Popen([sys.executable, '-c', code, str(ROOT/'scripts'), str(self.root)],
                                     env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    for _ in range(2)]
        times = []
        for child in children:
            stdout, stderr = child.communicate(timeout=15)
            self.assertEqual(child.returncode, 0, stderr)
            times.append(float(stdout.strip()))
        self.assertGreaterEqual(max(times)-min(times), 0.08)

    def test_make_exports_overrides_through_recursive_acquisition(self):
        report = self.root/'http-vars.mk'
        names = ['DATA_HTTP_RETRY_BUDGET', 'NOAA_HTTP_MIN_INTERVAL', 'NOAA_HTTP_MAX_INTERVAL',
                 'DATA_HTTP_PROGRESS_INTERVAL', 'CPC_HTTP_RANGE_SIZE', 'CPC_HTTP_DAILY_CACHE', 'CPC_BASE_URL']
        child = self.root/'report.py'
        child.write_text('import json, os\nprint(json.dumps({k:os.environ[k] for k in '+repr(names)+'}))\n')
        report.write_text('dump-http-vars:\n\t+@$(MAKE) --no-print-directory -s -f '+str(report)
                          +' child-http-vars\nchild-http-vars:\n\t@'+sys.executable+' '+str(child)+'\n')
        result = subprocess.run(['make', '--no-print-directory', '-s', '-f', 'Makefile', '-f', str(report),
                                 'dump-http-vars', 'NOAA_HTTP_MIN_INTERVAL=7', 'DATA_HTTP_RETRY_BUDGET=321',
                                 'CPC_BASE_URL=http://localhost/custom'], cwd=ROOT,
                                env={**os.environ, 'MAKEFLAGS': '', 'MFLAGS': '', 'MAKEOVERRIDES': ''},
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertEqual(values['NOAA_HTTP_MIN_INTERVAL'], '7')
        self.assertEqual(values['DATA_HTTP_RETRY_BUDGET'], '321')
        self.assertEqual(values['CPC_BASE_URL'], 'http://localhost/custom')
        self.assertEqual(values['CPC_HTTP_RANGE_SIZE'], '2097152')
        self.assertEqual(values['CPC_HTTP_DAILY_CACHE'], '1')


if __name__ == '__main__':
    unittest.main()
