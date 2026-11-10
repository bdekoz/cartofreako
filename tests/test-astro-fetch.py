#!/usr/bin/env python3
"""Astronomy provider outages must fail over, retain good outputs and reuse downloads."""
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('astro_fetch', ROOT / 'scripts/fetch-astro-data.py')
astro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(astro)


def catalog(columns, count):
    names = columns.split(',')
    rows = [columns]
    for index in range(count):
        row = {name: '1' for name in names}
        row.update(source_id=str(index + 1), pl_name=f'Planet {index}', hostname=f'Host {index}',
                   ra='120', dec='-20', phot_g_mean_mag='4.5', discoverymethod='Transit')
        rows.append(','.join(row[name] for name in names))
    return ('\n'.join(rows) + '\n').encode()


class AstronomyFetch(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.calls = Counter()
        self.primary = '503'
        self.broken_body = None
        self.fail_body = None
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                parts = urlsplit(self.path)
                query = parse_qs(parts.query)
                key = parts.path if parts.path != '/sbdb' else query['sstr'][0]
                owner.calls[key] += 1
                code = 200
                if parts.path in ('/primary', '/mirror'):
                    if parts.path == '/primary' and (owner.primary == '503' or
                            owner.primary == 'transient' and owner.calls[key] == 1):
                        code, body = 503, b'Service Unavailable'
                    elif parts.path == '/primary' and owner.primary == 'invalid':
                        body = b'<VOTABLE>service returned XML instead of CSV</VOTABLE>'
                    else:
                        body = catalog(astro.GAIA_COLUMNS, 500)
                elif parts.path == '/planets':
                    body = catalog(astro.PLANET_COLUMNS, 250)
                else:
                    search = query['sstr'][0]
                    des = next(des for _, name, des in astro.SMALL_BODIES if name == search)
                    if owner.fail_body == search:
                        code, body = 503, b'Service Unavailable'
                    else:
                        body = json.dumps({'object': {'des': 'wrong' if owner.broken_body == search else des,
                                                      'fullname': search, 'kind': 'an'},
                                           'orbit': {'epoch': '2460000.5', 'elements': [
                                               {'name': name, 'value': '1'} for name in
                                               ('e', 'a', 'i', 'om', 'w', 'ma', 'n')]}}).encode()
                self.send_response(code)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('ETag', '"fixture-v1"')
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.addCleanup(server.server_close)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(worker.join)
        self.addCleanup(server.shutdown)
        self.base = f'http://127.0.0.1:{server.server_port}'
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {'DATA_HTTP_RETRY_BUDGET': '0.2', 'DATA_UPDATE_RUN_ID': '',
                                'NOAA_HTTP_MIN_INTERVAL': '0', 'NOAA_HTTP_MAX_INTERVAL': '60'}).start()
        self.log = patch('sys.stderr', new_callable=io.StringIO).start()
        patch('sys.stdout', new_callable=io.StringIO).start()

    def refresh(self, **kwargs):
        astro.refresh(self.root / 'output', self.root / 'cache',
                      gaia_taps=(self.base + '/primary', self.base + '/mirror'),
                      planet_tap=self.base + '/planets', sbdb_api=self.base + '/sbdb', **kwargs)

    def test_persistent_503_uses_partner_and_records_real_url(self):
        self.refresh()
        output = self.root / 'output'
        self.assertEqual(self.calls['/primary'], 1)
        self.assertEqual(self.calls['/mirror'], 1)
        self.assertIn('HTTP 503', self.log.getvalue())
        receipt = json.loads((output / 'gaia-dr3-bright.csv.receipt.json').read_text())
        self.assertTrue(receipt['url'].startswith(self.base + '/mirror?'))
        self.assertEqual(parse_qs(urlsplit(receipt['url']).query)['QUERY'], [astro.GAIA_QUERY])
        sums = (output / 'SHA256SUMS').read_text().splitlines()
        self.assertEqual(len(sums), 9)
        for line in sums:
            sha, name = line.split('  ')
            self.assertEqual(astro.digest(output / name), sha)

    def test_transient_503_is_retried_without_using_partner(self):
        self.primary = 'transient'
        with patch.dict(os.environ, {'DATA_HTTP_RETRY_BUDGET': '10'}), \
                patch('data_http_policy.Progress.sleep'):
            self.refresh()
        self.assertEqual(self.calls['/primary'], 2)
        self.assertEqual(self.calls['/mirror'], 0)
        self.assertIn('HTTP 503; retry 1', self.log.getvalue())

    def test_http_200_with_wrong_format_is_rejected_before_partner_fallback(self):
        self.primary = 'invalid'
        self.refresh()
        self.assertEqual(self.calls['/mirror'], 1)
        self.assertIn('missing required CSV columns', self.log.getvalue())

    def test_late_failure_keeps_outputs_and_retry_reuses_good_downloads(self):
        self.primary = 'good'
        output = self.root / 'output'
        output.mkdir()
        old = output / 'gaia-dr3-bright.csv'
        old.write_bytes(b'previous validated catalog')
        self.fail_body = '67P'
        with self.assertRaises(astro.DatasetError):
            self.refresh()
        self.assertEqual(old.read_bytes(), b'previous validated catalog')
        self.assertFalse((output / 'SHA256SUMS').exists())
        previous_calls = self.calls.copy()
        self.fail_body = None
        self.refresh()
        for name in ('/primary', '/planets', '1 Ceres', '4 Vesta', '433 Eros', '1P', '2P'):
            self.assertEqual(self.calls[name], previous_calls[name])
        self.assertEqual(self.calls['67P'], previous_calls['67P'] + 1)
        self.assertNotEqual(old.read_bytes(), b'previous validated catalog')
        self.assertIn('using validated cache (same-utc-day)', self.log.getvalue())

    def test_jpl_wrong_object_identity_never_replaces_existing_outputs(self):
        output = self.root / 'output'
        output.mkdir()
        (output / 'SHA256SUMS').write_text('previous manifest')
        self.broken_body = '1 Ceres'
        with self.assertRaisesRegex(astro.DatasetError, 'unexpected JPL object identity'):
            self.refresh()
        self.assertEqual((output / 'SHA256SUMS').read_text(), 'previous manifest')
        self.assertFalse((output / 'sbdb-ceres.json').exists())

    def test_truncated_catalog_cannot_be_published(self):
        path = self.root / 'gaia.csv'
        path.write_bytes(catalog(astro.GAIA_COLUMNS, 499))
        with self.assertRaisesRegex(astro.DatasetError, 'expected 500 rows, received 499'):
            astro.validate_catalog(path, astro.GAIA_COLUMNS, 500, 'source_id')


if __name__ == '__main__':
    unittest.main()
