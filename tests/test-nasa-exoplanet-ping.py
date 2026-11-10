#!/usr/bin/env python3
"""NASA recovery requires usable CSV; cooldowns survive retries and restarts."""
from datetime import datetime, timezone
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from dataset import DatasetError, lock

spec = importlib.util.spec_from_file_location('nasa_ping', ROOT / 'scripts/ping-nasa-exoplanet-archive.py')
ping = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ping)


class Monitor(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.log = self.root / 'success.log'
        self.cache = self.root / 'cache'
        self.clock = SimpleNamespace(now=1794330000.0)
        self.clock.time = lambda: self.clock.now
        def sleep(seconds):
            self.clock.now += seconds
        self.clock.sleep = sleep
        self.addCleanup(patch.stopall)
        patch.object(ping, 'time', self.clock).start()
        self.output = patch('sys.stdout', new_callable=io.StringIO).start()

    def run_monitor(self, **kwargs):
        return ping.monitor(ping.URL, self.log, self.cache, **kwargs)

    def response(self, body, headers=None):
        response = MagicMock(status=200, headers=headers or {'Content-Type': 'text/csv'})
        response.read.return_value = body
        response.__enter__.return_value = response
        return response

    def test_valid_csv_is_required_and_response_read_is_bounded(self):
        response = self.response(b'pl_name\n"Proxima Cen b"\n')
        with patch.object(ping, 'build_opener') as opener:
            opener.return_value.open.return_value = response
            status, _, success, _ = ping.probe(ping.URL, 20)
        self.assertEqual(status, 200)
        self.assertTrue(success)
        response.read.assert_called_once_with(ping.MAX_RESPONSE_BYTES + 1)
        self.assertEqual(opener.return_value.open.call_count, 1)
        self.assertIsInstance(opener.call_args.args[0], ping.NoRedirect)
        query = parse_qs(urlsplit(opener.return_value.open.call_args.args[0].full_url).query)
        self.assertEqual(query, {'query': ['SELECT TOP 1 pl_name FROM pscomppars'], 'format': ['csv']})

    def test_maintenance_pages_empty_results_and_bad_csv_are_not_recovery(self):
        examples = [(b'<html>maintenance</html>', {'content-type': 'text/html'}),
                    (b'pl_name\n', {}), (b'pl_name\n""\n', {}),
                    (b'wrong_header\nplanet\n', {}), (b'pl_name\na\nb\n', {}),
                    (b'pl_name\n"unterminated', {}), (b'\xff', {}),
                    (b'x' * (ping.MAX_RESPONSE_BYTES + 1), {})]
        for body, headers in examples:
            with self.subTest(body=body[:30]), patch.object(ping, 'build_opener') as opener:
                opener.return_value.open.return_value = self.response(body, headers)
                self.assertFalse(ping.probe(ping.URL, 20)[2])

    def test_http_errors_preserve_retry_after_without_internal_retry(self):
        for code in (429, 503):
            with self.subTest(code=code), patch.object(ping, 'build_opener') as opener:
                opener.return_value.open.side_effect = HTTPError(ping.URL, code, 'unavailable',
                                                               {'Retry-After': '7200'}, None)
                status, headers, success, _ = ping.probe(ping.URL, 20)
                self.assertEqual(status, code)
                self.assertEqual(headers['Retry-After'], '7200')
                self.assertFalse(success)
                self.assertEqual(opener.return_value.open.call_count, 1)

    def test_network_failure_is_not_recovery(self):
        with patch.object(ping, 'build_opener') as opener:
            opener.return_value.open.side_effect = URLError('timed out')
            status, _, success, note = ping.probe(ping.URL, 20)
        self.assertIsNone(status)
        self.assertFalse(success)
        self.assertIn('timed out', note)

    def test_waits_hourly_then_logs_first_success_and_stops(self):
        start = self.clock.now
        preserved = self.cache / 'http/unrelated.part'
        preserved.parent.mkdir(parents=True)
        preserved.write_bytes(b'downloaded bytes')
        with patch.object(ping, 'probe', side_effect=[(503, {}, False, 'maintenance'),
                                                    (200, {}, True, 'valid CSV')]) as probe:
            self.assertEqual(self.run_monitor(), 0)
        self.assertEqual(probe.call_count, 2)
        self.assertEqual(self.clock.now, start + 3600)
        lines = self.log.read_text().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith(ping.timestamp(start + 3600) + ' HTTP 200'))
        self.assertIn('Retry with: make data-update', self.output.getvalue())
        self.assertIn(ping.timestamp(start) + ' \033[31mno\033[0m HTTP 503', self.output.getvalue())
        self.assertIn(ping.timestamp(start + 3600) + ' \033[32myes\033[0m HTTP 200', self.output.getvalue())
        self.assertEqual(preserved.read_bytes(), b'downloaded bytes')

    def test_retry_after_seconds_and_dates_extend_the_hourly_interval(self):
        for kind in ('seconds', 'date'):
            with self.subTest(kind=kind):
                cache = self.root / kind
                start = self.clock.now
                value = '7200' if kind == 'seconds' else format_datetime(
                    datetime.fromtimestamp(start + 7200, timezone.utc), usegmt=True)
                with patch.object(ping, 'probe', side_effect=[
                        (503, {'retry-after': value}, False, 'maintenance'), (200, {}, True, 'CSV')]):
                    self.assertEqual(ping.monitor(ping.URL, self.log, cache), 0)
                self.assertEqual(self.clock.now, start + 7200)

    def test_restart_preserves_cooldown_and_failure_writes_no_success_log(self):
        with patch.object(ping, 'probe', return_value=(503, {}, False, 'maintenance')) as probe:
            self.assertEqual(self.run_monitor(once=True), 1)
            self.assertEqual(self.run_monitor(once=True), 2)
            self.assertEqual(probe.call_count, 1)
        self.assertFalse(self.log.exists())
        self.assertIn(' \033[31mno\033[0m Next probe', self.output.getvalue())

    def test_duplicate_monitors_are_excluded(self):
        with lock(self.cache / 'http/monitors', 'nasa-exoplanet-ping'), patch.object(ping, 'probe') as probe:
            with self.assertRaisesRegex(DatasetError, 'already running'):
                self.run_monitor()
        probe.assert_not_called()

    def test_default_log_is_under_repository_root(self):
        with patch.object(sys, 'argv', ['ping-nasa-exoplanet-archive.py', '--once']), \
                patch.object(ping, 'monitor', return_value=0) as monitor:
            self.assertEqual(ping.main(), 0)
        self.assertEqual(monitor.call_args.args[1], ROOT / 'nasa-exoplanet-ping-status.log')

    def test_real_cli_records_local_csv_success(self):
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_GET(self):
                calls.append(self.path)
                body = b'pl_name\n"Proxima Cen b"\n'
                self.send_response(200)
                self.send_header('Content-Type', 'text/csv')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.addCleanup(server.server_close)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/ping-nasa-exoplanet-archive.py'),
                                 '--once', '--url', f'http://127.0.0.1:{server.server_port}/query',
                                 '--cache', str(self.cache), '--log', str(self.log)],
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ['/query'])
        self.assertRegex(result.stdout, r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z \x1b\[32myes\x1b\[0m HTTP 200')
        self.assertRegex(self.log.read_text(), r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z HTTP 200 ')


if __name__ == '__main__':
    unittest.main()
