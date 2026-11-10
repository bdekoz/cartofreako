#!/usr/bin/env python3
"""Retain completed particulate periods without inventing provider freshness."""
from datetime import date, datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from dataset import DatasetError, atomic_json, digest
from data_http import fetch
spec = importlib.util.spec_from_file_location('particulate', ROOT/'scripts/import-anthropocene-particulate.py')
cache_import = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache_import)


class Periods(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.raw = self.root/'old/.raw/2026'
        self.cache = self.root/'cache'
        self.raw.mkdir(parents=True)
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {'FIRMS_MAP_KEY': 'secret-fixture', 'DATA_UPDATE_RUN_ID': 'new-run',
                               'ANTHROPOCENE_FIRMS_SOURCES': 'VIIRS_NOAA20_SP VIIRS_NOAA20_NRT'}).start()

    def file(self, name, body):
        path = self.raw/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
        return path

    def manifest(self):
        manifest = self.raw/'SHA256SUMS'
        manifest.write_text(''.join(digest(p)+'  '+str(p)+'\n' for p in sorted(self.raw.rglob('*'))
                                    if p.is_file() and p != manifest))
        return manifest

    def firms(self, source='VIIRS_NOAA20_SP', days=('2026-01-01', '2026-01-02')):
        return self.file('firms/000-'+source+'-2026-01-01.csv',
                         'latitude,longitude,acq_date\n'+''.join('40,-100,'+d+'\n' for d in days))

    def test_local_import_verifies_hash_and_preserves_unknown_provider_times(self):
        self.firms()
        self.file('cwfis/20260101.csv', 'lat, lon, rep_date\n40,-100,2026-01-01\n')
        self.manifest()
        self.assertEqual(cache_import.import_local(self.cache, [self.raw], 2026), 2)
        url = cache_import.firms_url('VIIRS_NOAA20_SP', '2026-01-01', 2)
        record = json.loads(cache_import.receipt_path(self.cache, url).read_text())
        self.assertIsNone(record['checked_at'])
        self.assertIsNone(record['retrieved_at'])
        self.assertNotIn('secret-fixture', json.dumps(record))
        with patch('data_http.open_response', side_effect=AssertionError('unexpected provider request')):
            result = fetch(url, self.root/'new.csv', self.cache, retain_cache=True)
        self.assertEqual(result['cache_policy'], 'completed-period')
        self.assertIsNone(result['checked_at'])
        self.assertEqual((self.root/'new.csv').read_bytes(), self.firms().read_bytes())

    def test_old_sensor_is_not_adopted_as_noaa20(self):
        self.firms('VIIRS_SNPP_SP')
        self.manifest()
        self.assertEqual(cache_import.import_local(self.cache, [self.raw], 2026), 0)
        self.assertEqual(list((self.cache/'http').glob('*.json')), [])

    def test_existing_short_tail_is_reused_before_requesting_new_days(self):
        self.firms()
        self.manifest()
        cache_import.import_local(self.cache, [self.raw], 2026)
        start = date(2026, 1, 1)
        self.assertEqual(cache_import.chunk_days(self.cache, 'VIIRS_NOAA20_SP', start, 5), 2)
        self.assertEqual(cache_import.chunk_days(self.cache, 'VIIRS_NOAA20_SP', date(2026, 1, 3), 3), 3)
        self.assertEqual(cache_import.chunk_days(self.cache, 'VIIRS_NOAA20_NRT', start, 5), 5)

    def test_sparse_or_wrong_start_cannot_claim_a_completed_period(self):
        path = self.firms(days=('2026-01-01', '2026-01-03'))
        self.assertIsNone(cache_import.firms_period(path, date(2026, 1, 1)))
        self.assertIsNone(cache_import.firms_period(path, date(2025, 12, 31)))

    def test_changed_local_bytes_are_rejected(self):
        path = self.firms()
        self.manifest()
        path.write_text(path.read_text().replace('40,-100', '41,-100'))
        with self.assertRaisesRegex(DatasetError, 'Changed local particulate input'):
            cache_import.import_local(self.cache, [self.raw], 2026)

    def test_closed_annual_inputs_are_imported_but_current_year_bulk_is_mutable(self):
        self.file('daily_88101_2025.zip', 'closed EPA archive')
        self.file('hms_smoke2025.zip', 'closed smoke archive')
        self.file('daily_88101_2026.zip', 'mutable EPA archive')
        self.manifest()
        self.assertEqual(cache_import.import_local(self.cache, [self.raw], 2025), 2)
        self.assertEqual(cache_import.import_local(self.cache, [self.raw], 2026), 0)

    def test_provider_checked_bytes_are_preferred_and_reused_across_dates_and_runs(self):
        path = self.firms()
        self.manifest()
        url = cache_import.firms_url('VIIRS_NOAA20_SP', '2026-01-01', 2)
        body = b'previous verified provider response'
        from hashlib import sha256
        sha = sha256(body).hexdigest()
        obj = self.cache/'sha256'/sha
        obj.parent.mkdir(parents=True)
        obj.write_bytes(body)
        receipt = cache_import.receipt_path(self.cache, url)
        atomic_json(receipt, {'sha256': sha, 'bytes': len(body), 'url': 'redacted',
                             'checked_at': '2026-01-03T00:00:00Z', 'retrieved_at': '2026-01-03T00:00:00Z',
                             'checked_run': 'earlier-run', 'acquisition': 'remote-checked'})
        self.assertEqual(cache_import.import_local(self.cache, [self.raw], 2026), 0)
        with patch('data_http.open_response', side_effect=AssertionError('unexpected provider request')):
            record = fetch(url, self.root/'new.csv', self.cache, retain_cache=True)
        self.assertEqual(record['checked_at'], '2026-01-03T00:00:00Z')
        self.assertEqual((self.root/'new.csv').read_bytes(), body)
        self.assertEqual(path.read_text().splitlines()[0], 'latitude,longitude,acq_date')

    def test_corrupt_retained_cache_is_not_silently_redownloaded(self):
        self.firms()
        self.manifest()
        cache_import.import_local(self.cache, [self.raw], 2026)
        url = cache_import.firms_url('VIIRS_NOAA20_SP', '2026-01-01', 2)
        record = json.loads(cache_import.receipt_path(self.cache, url).read_text())
        obj = self.cache/'sha256'/record['sha256']
        obj.chmod(0o644)
        obj.write_bytes(b'broken')
        with patch('data_http.open_response') as remote:
            with self.assertRaisesRegex(DatasetError, 'Corrupted HTTP cache'):
                fetch(url, self.root/'new.csv', self.cache, retain_cache=True)
        remote.assert_not_called()

    def test_optional_missing_daily_feed_never_publishes_a_file(self):
        error = HTTPError('https://example.invalid/day.csv', 404, 'missing', {}, None)
        with patch('data_http.open_response', side_effect=error):
            self.assertIsNone(fetch(error.url, self.root/'absent.csv', self.cache, allow_missing=True))
        self.assertFalse((self.root/'absent.csv').exists())
        self.assertFalse((self.root/'absent.csv.receipt.json').exists())
        self.assertEqual(list((self.cache/'http').glob('*.json')), [])


if __name__ == '__main__':
    unittest.main()
