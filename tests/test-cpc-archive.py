#!/usr/bin/env python3
"""Historical CPC imports avoid downloads without inventing provider freshness."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from dataset import DatasetError, atomic_json, digest
spec = importlib.util.spec_from_file_location('cpc_archive', ROOT / 'scripts/import-cpc-archive.py')
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class Archive(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'old'
        self.cache = self.root / 'cache'
        self.source.mkdir()
        self.year = 2025
        for variable in ('tmax', 'tmin'):
            (self.source / f'{variable}.{self.year}.nc').write_bytes(b'archive ' + variable.encode())
        (self.source / 'SHA256SUMS').write_text(''.join(
            digest(path) + '  ./' + path.name + '\n' for path in sorted(self.source.glob('*.nc'))))
        self.addCleanup(patch.stopall)
        patch.object(archive, 'validate_netcdf').start()

    def import_files(self):
        return archive.import_archive(self.source, self.cache, self.year, self.year)

    def test_local_import_checks_hashes_and_retains_unknown_provider_times(self):
        report = self.import_files()
        self.assertEqual(report['imported_local'], 2)
        raw = self.root / 'new-edition/.raw/cpc'
        self.assertEqual(len(archive.stage_archive(raw, self.cache, self.year, self.year)), 2)
        for variable in ('tmax', 'tmin'):
            name = f'{variable}.{self.year}.nc'
            self.assertEqual((raw / name).read_bytes(), (self.source / name).read_bytes())
            receipt = json.loads((raw / (name + '.receipt.json')).read_text())
            self.assertEqual(receipt['cache_policy'], 'pinned-cpc-archive')
            self.assertIsNone(receipt['provider_checked_at'])
            self.assertIsNone(receipt['retrieved_at'])
            self.assertNotIn('checked_at', receipt)
            self.assertTrue((self.source / name).stat().st_mode & 0o200)
        self.assertEqual(self.import_files()['existing_archive'], 2)

    def test_already_refreshed_archive_is_preferred_over_legacy_bytes(self):
        name = f'tmax.{self.year}.nc'
        body = b'fresh newer archived year'
        sha = hashlib.sha256(body).hexdigest()
        (self.cache / 'sha256').mkdir(parents=True)
        (self.cache / 'sha256' / sha).write_bytes(body)
        url = archive.BASES[0] + '/' + name
        key = hashlib.sha256((url + '{}').encode()).hexdigest()
        atomic_json(self.cache / 'http' / (key + '.json'), {
            'url': url, 'sha256': sha, 'bytes': len(body), 'checked_at': '2026-11-09T23:00:00Z',
            'retrieved_at': '2026-11-09T22:00:00Z'})
        report = self.import_files()
        self.assertEqual(report['adopted_http'], 1)
        self.assertEqual(report['imported_local'], 1)
        manifest = archive.read_manifest(self.cache)
        record = manifest['files'][name]
        self.assertEqual(record['sha256'], sha)
        self.assertEqual(record['provider_checked_at'], '2026-11-09T23:00:00Z')
        self.assertEqual(archive.stage_archive(self.source, self.cache, self.year, self.year, missing_only=True), [])
        self.assertEqual((self.source / name).read_bytes(), b'archive tmax')

    def test_bad_local_checksum_never_creates_a_pinned_record(self):
        (self.source / f'tmax.{self.year}.nc').write_bytes(b'changed')
        with self.assertRaisesRegex(DatasetError, 'changed local CPC archive'):
            self.import_files()
        self.assertFalse((self.cache / 'cpc-archive/manifest.json').exists())

    def test_corrupt_imported_object_fails_instead_of_requesting_replacement(self):
        self.import_files()
        record = archive.read_manifest(self.cache)['files'][f'tmax.{self.year}.nc']
        obj = self.cache / 'sha256' / record['sha256']
        obj.unlink()
        obj.write_bytes(b'changed')
        with self.assertRaisesRegex(DatasetError, 'Corrupted CPC archive object'):
            archive.stage_archive(self.root / 'new', self.cache, self.year, self.year)

    def test_product_years_cannot_be_imported_as_archives(self):
        with self.assertRaisesRegex(DatasetError, '2026 requires incremental'):
            archive.import_archive(self.source, self.cache, 2025, 2026)
        self.import_files()
        self.assertEqual(archive.stage_archive(self.root / 'new', self.cache, 2026, 2026), [])

    def test_real_fetch_script_skips_archives_and_requests_product_year_files(self):
        self.import_files()
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_GET(self):
                calls.append(self.path)
                body = b'fresh product-year file'
                self.send_response(200)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('ETag', '"fresh-2026"')
                self.end_headers()
                self.wfile.write(body)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.addCleanup(server.server_close)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        validator = self.root / 'gdalinfo-fixture'
        validator.write_text('#!' + sys.executable + '\nimport sys\nfrom pathlib import Path\n'
                             'assert Path(sys.argv[1].split(":",1)[1].rsplit(":",1)[0]).is_file()\n')
        validator.chmod(0o755)
        output = self.root / 'fetched'
        env = {**os.environ, 'DATA_HTTP_CACHE': str(self.cache), 'CPC_ARCHIVE_CACHE': '1', 'CPC_INCREMENTAL': '0',
               'CPC_BASE_URL': f'http://127.0.0.1:{server.server_port}', 'GDALINFO': str(validator),
               'DATA_UPDATE_RUN_ID': 'archive-fixture'}
        result = subprocess.run(['bash', str(ROOT / 'scripts/fetch-anthropocene-cpc-data.sh'),
                                 str(output), '2025', '2026'], env=env, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ['/tmax.2026.nc', '/tmin.2026.nc'])
        self.assertEqual(result.stdout.count('using pinned CPC archive'), 2)
        raw = output / '.raw/cpc'
        self.assertEqual(len((raw / 'SHA256SUMS').read_text().splitlines()), 4)
        self.assertEqual((raw / 'tmax.2025.nc').read_bytes(), b'archive tmax')
        self.assertEqual((raw / 'tmax.2026.nc').read_bytes(), b'fresh product-year file')
        forced = subprocess.run(['bash', str(ROOT / 'scripts/fetch-anthropocene-cpc-data.sh'),
                                 str(self.root / 'forced'), '2025', '2025'],
                                env={**env, 'CPC_ARCHIVE_CACHE': '0'}, text=True, capture_output=True, timeout=20)
        self.assertEqual(forced.returncode, 0, forced.stderr)
        self.assertEqual(calls[-2:], ['/tmax.2025.nc', '/tmin.2025.nc'])
        self.assertNotIn('using pinned CPC archive', forced.stdout)


if __name__ == '__main__':
    unittest.main()
