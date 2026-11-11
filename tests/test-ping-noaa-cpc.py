#!/usr/bin/env python3
"""Hourly CPC monitoring, Retry-After and first-success log regressions."""
from datetime import datetime, timezone
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import io
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from dataset import DatasetError, lock

spec = importlib.util.spec_from_file_location('cpc_ping', ROOT/'scripts/ping-noaa-cpc.py')
ping = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ping)


class Monitor(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.log = self.root/'noaa-cpc-ping-status.log'
        self.cache = self.root/'cache'
        self.url = 'https://psl.noaa.gov/thredds/fileServer/Datasets/cpc_global_temp/tmin.1981.nc'
        self.clock = SimpleNamespace(now=1794247200.0, sleeps=[])
        self.clock.time = lambda: self.clock.now
        self.clock.monotonic = lambda: self.clock.now
        def sleep(delay):
            self.clock.sleeps.append(delay)
            self.clock.now += delay
        self.clock.sleep = sleep
        self.addCleanup(patch.stopall)
        patch.object(ping, 'time', self.clock).start()
        patch('data_http_policy.time', self.clock).start()
        self.output = patch('sys.stdout', new_callable=io.StringIO).start()

    def run_monitor(self, **kwargs):
        return ping.monitor(self.url, self.log, self.cache, **kwargs)

    def test_first_success_is_logged_once_then_monitor_stops(self):
        start = self.clock.now
        partial = self.cache/'http/example.part'
        partial.parent.mkdir(parents=True)
        partial.write_bytes(b'preserve the downloaded data')
        with patch.object(ping, 'probe', side_effect=[(429, {}, False, 'Too Many Requests'),
                                                    (206, {}, True, 'data probe succeeded')]) as probe:
            self.assertEqual(self.run_monitor(), 0)
        self.assertEqual(probe.call_count, 2)
        self.assertEqual(self.clock.now, start+3600)
        journal = json.loads((self.cache/'http/monitors/noaa-cpc-ping.json').read_text())
        self.assertEqual(journal['last_attempt_at'], ping.timestamp(start+3600, utc=True))
        lines = self.log.read_text().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith(ping.timestamp(start+3600)+' HTTP 206'))
        self.assertEqual(partial.read_bytes(), b'preserve the downloaded data')

    def test_retry_after_seconds_extends_hourly_interval(self):
        start = self.clock.now
        with patch.object(ping, 'probe', side_effect=[(429, {'Retry-After': '7200'}, False, 'Too Many Requests'),
                                                    (206, {}, True, 'data probe succeeded')]):
            self.assertEqual(self.run_monitor(), 0)
        self.assertEqual(self.clock.now, start+7200)
        self.assertIn('Retry-After: 7200', self.output.getvalue())

    def test_retry_after_http_date_extends_hourly_interval(self):
        start = self.clock.now
        when = format_datetime(datetime.fromtimestamp(start+10800, timezone.utc), usegmt=True)
        with patch.object(ping, 'probe', side_effect=[(503, {'retry-after': when}, False, 'HTTP error'),
                                                    (206, {}, True, 'data probe succeeded')]):
            self.assertEqual(self.run_monitor(), 0)
        self.assertEqual(self.clock.now, start+10800)

    def test_restart_does_not_probe_before_saved_hourly_slot(self):
        with patch.object(ping, 'probe', return_value=(429, {}, False, 'Too Many Requests')) as probe:
            self.assertEqual(self.run_monitor(once=True), 1)
            self.assertEqual(self.run_monitor(once=True), 2)
            self.assertEqual(probe.call_count, 1)
        self.assertFalse(self.log.exists())

    def test_failures_and_timeouts_never_record_success(self):
        for status in (429, 404, 503, None):
            with self.subTest(status=status):
                with patch.object(ping, 'probe', return_value=(status, {}, False, 'failed')):
                    self.assertEqual(self.run_monitor(once=True), 1)
                self.assertFalse(self.log.exists())
                self.clock.now += 3600

    def test_history_is_preserved_and_success_is_appended(self):
        self.log.write_text('earlier recovery\n')
        with patch.object(ping, 'probe', return_value=(200, {}, True, 'data probe succeeded')) as probe:
            self.assertEqual(self.run_monitor(), 0)
        self.assertEqual(probe.call_count, 1)
        self.assertTrue(self.log.read_text().startswith('earlier recovery\n'))
        self.assertEqual(len(self.log.read_text().splitlines()), 2)

    def test_provider_cooldown_is_respected_before_first_probe(self):
        pacer = ping.Pacer(self.url, self.cache)
        pacer.defer(7200, throttled=True)
        with patch.object(ping, 'probe', return_value=(206, {}, True, 'data probe succeeded')) as probe:
            self.assertEqual(self.run_monitor(once=True), 2)
        probe.assert_not_called()
        self.assertFalse(self.log.exists())

    def test_duplicate_monitors_are_excluded(self):
        with lock(self.cache/'http/monitors', 'noaa-cpc-ping'), patch.object(ping, 'probe') as probe:
            with self.assertRaisesRegex(DatasetError, 'already running'):
                self.run_monitor()
        probe.assert_not_called()

    def test_probe_reads_only_one_byte_when_range_is_ignored(self):
        response = MagicMock(status=200, headers={})
        response.read.return_value = b'C'
        response.__enter__.return_value = response
        with patch.object(ping, 'build_opener') as opener:
            opener.return_value.open.return_value = response
            status, _, success, _ = ping.probe(self.url, 20)
        self.assertEqual(status, 200)
        self.assertTrue(success)
        response.read.assert_called_once_with(1)
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.get_header('Range'), 'bytes=0-0')
        self.assertIsInstance(opener.call_args.args[0], ping.NoRedirect)

    def test_bad_partial_response_is_not_success(self):
        response = MagicMock(status=206, headers={'Content-Range': 'bytes 5-5/100'})
        response.__enter__.return_value = response
        with patch.object(ping, 'build_opener') as opener:
            opener.return_value.open.return_value = response
            self.assertFalse(ping.probe(self.url, 20)[2])
        response.read.assert_not_called()

    def test_http_error_has_no_internal_retries_and_preserves_retry_after(self):
        error = HTTPError(self.url, 429, 'Too Many Requests', {'Retry-After': '7200'}, None)
        with patch.object(ping, 'build_opener') as opener:
            opener.return_value.open.side_effect = error
            status, headers, success, _ = ping.probe(self.url, 20)
        self.assertEqual(status, 429)
        self.assertEqual(headers['Retry-After'], '7200')
        self.assertFalse(success)
        self.assertEqual(opener.return_value.open.call_count, 1)

    def test_network_error_is_not_success(self):
        with patch.object(ping, 'build_opener') as opener:
            opener.return_value.open.side_effect = URLError('timed out')
            status, _, success, note = ping.probe(self.url, 20)
        self.assertIsNone(status)
        self.assertFalse(success)
        self.assertIn('timed out', note)

    def test_default_success_log_is_in_repository_root(self):
        with patch.object(sys, 'argv', ['ping-noaa-cpc.py', '--once']), patch.object(ping, 'monitor', return_value=0) as monitor:
            self.assertEqual(ping.main(), 0)
        self.assertEqual(monitor.call_args.args[1], ROOT/'noaa-cpc-ping-status.log')

    def test_cli_writes_real_local_http_success_to_selected_log(self):
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                calls.append(self.headers.get('Range'))
                self.send_response(206)
                self.send_header('Content-Range', 'bytes 0-0/100')
                self.send_header('Content-Length', '1')
                self.end_headers()
                self.wfile.write(b'C')
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        result = subprocess.run([sys.executable, str(ROOT/'scripts/ping-noaa-cpc.py'), '--once',
                                 '--url', f'http://127.0.0.1:{server.server_port}/tmin.1981.nc',
                                 '--cache', str(self.cache), '--log', str(self.log)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ['bytes=0-0'])
        self.assertRegex(self.log.read_text(), r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} P[SD]T HTTP 206 ')


if __name__ == '__main__':
    unittest.main()
