#!/usr/bin/env python3
"""Exercise India archive preservation across independent update editions."""
import csv
import gzip
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
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('india_openaq', ROOT / 'scripts/fetch-india-openaq-pm25.py')
openaq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(openaq)


def archive(day='2025-01-01', value=20):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(['location_id', 'sensors_id', 'datetime', 'lat', 'lon', 'parameter', 'units', 'value'])
    for hour in range(18):
        writer.writerow([235, 1, f'{day}T{hour:02}:00:00+05:30', 28.6, 77.3, 'pm25', 'ug/m3', value])
    return gzip.compress(stream.getvalue().encode(), mtime=0)


class IndiaCache(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cache = self.root / 'cache'
        self.name = 'location-235-20250101.csv.gz'
        self.body = archive()

    def test_import_and_reuse_across_editions_without_requesting_daily_bytes(self):
        earlier = self.root / 'earlier/raw'
        earlier.mkdir(parents=True)
        (earlier / self.name).write_bytes(self.body)
        (earlier.parent / 'openaq-download-receipts.json').write_text(json.dumps([
            {'key': self.name, 'sha256': hashlib.sha256(self.body).hexdigest()}]))
        with patch.object(openaq, 'PROJECT', self.root):
            first = openaq.ArchiveCache(self.cache, self.root / 'one', [earlier])
            second = openaq.ArchiveCache(self.cache, self.root / 'two')
        def no_network():
            self.fail('A downloaded daily file was requested again')
        first_path, receipt = first.get(self.name, 'fixture-url', no_network)
        self.assertEqual(receipt['acquisition'], 'cache-imported')
        self.assertIsNone(receipt['retrieved_at_utc'])
        second_path, receipt = second.get(self.name, 'fixture-url', no_network)
        self.assertEqual(receipt['acquisition'], 'cache-reused')
        self.assertEqual(first_path.read_bytes(), second_path.read_bytes())
        self.assertEqual((earlier / self.name).read_bytes(), self.body)

    def test_explicit_refresh_preserves_bytes_in_previous_edition(self):
        cache = openaq.ArchiveCache(self.cache, self.root / 'one')
        old_path, _ = cache.get(self.name, 'fixture-url', lambda: self.body)
        new_body = archive(value=30)
        later = openaq.ArchiveCache(self.cache, self.root / 'two')
        new_path, receipt = later.get(self.name, 'fixture-url', lambda: new_body, refresh=True)
        self.assertEqual(receipt['acquisition'], 'downloaded')
        self.assertEqual(new_path.read_bytes(), new_body)
        self.assertEqual(old_path.read_bytes(), self.body)

    def test_checked_source_cache_is_discovered_without_an_explicit_path(self):
        earlier = self.root / 'assets.static/anthropocene/asia-pm25/raw'
        earlier.mkdir(parents=True)
        (earlier / self.name).write_bytes(self.body)
        with patch.object(openaq, 'PROJECT', self.root):
            cache = openaq.ArchiveCache(self.cache, self.root / 'one')
        _, receipt = cache.get(self.name, 'fixture-url', lambda: self.fail('Unexpected request'))
        self.assertEqual(receipt['acquisition'], 'cache-imported')

    def test_corrupt_cache_is_rejected_without_network_replacement(self):
        cache = openaq.ArchiveCache(self.cache, self.root / 'one')
        cache.get(self.name, 'fixture-url', lambda: self.body)
        path = self.cache / 'raw' / self.name
        path.unlink()
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'checksum changed'):
            cache.get(self.name, 'fixture-url', lambda: self.fail('Unexpected request'))

    def test_bad_import_receipt_is_rejected(self):
        earlier = self.root / 'earlier/raw'
        earlier.mkdir(parents=True)
        (earlier / self.name).write_bytes(self.body)
        (earlier.parent / 'openaq-download-receipts.json').write_text(json.dumps([
            {'key': self.name, 'sha256': '0' * 64}]))
        cache = openaq.ArchiveCache(self.cache, self.root / 'one', [earlier])
        with self.assertRaisesRegex(ValueError, 'checksum changed'):
            cache.get(self.name, 'fixture-url', lambda: self.fail('Unexpected request'))

    def test_new_run_discovers_new_days_and_downloads_only_new_daily_archives(self):
        inventory = self.root / 'locations.json'
        inventory.write_text(json.dumps({'coverage': 'Test selected India station', 'locations': [
            {'id': 235, 'country': 'IND', 'name': 'Delhi', 'provider': 'CPCB', 'kind': 'reference'}]}))
        calls = []
        keys = ['records/csv.gz/locationid=235/year=2025/' + self.name]
        def get(url, params=None):
            calls.append((url, params))
            if 'explore.openaq.org' in url:
                body = b'<div>CPCB PM2.5 Reference grade</div><script>code:"IN"</script>'
            elif params:
                body = ('<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
                        '<IsTruncated>false</IsTruncated>' + ''.join(
                            '<Contents><Key>' + key + '</Key></Contents>' for key in keys) +
                        '</ListBucketResult>').encode()
            else:
                body = archive('2025-01-02' if '20250102' in url else '2025-01-01')
            return type('Response', (), {'content': body})()
        for run in ('one', 'two'):
            args = ['fetch-india-openaq-pm25.py', '--output', str(self.root / run),
                    '--cache-dir', str(self.cache), '--locations-json', str(inventory),
                    '--start', '2025-01-01', '--end', '2025-01-02', '--refresh-index']
            with patch.object(sys, 'argv', args), patch.object(openaq, 'get', get), patch('sys.stdout', io.StringIO()):
                openaq.main()
            keys.append('records/csv.gz/locationid=235/year=2025/location-235-20250102.csv.gz')
        downloads = [url for url, params in calls if url.endswith('.csv.gz') and params is None]
        self.assertEqual(len(downloads), 2)
        self.assertEqual(sum('20250101' in url for url in downloads), 1)
        self.assertEqual(sum(params is not None for _, params in calls), 2)
        report = json.loads((self.root / 'two/openaq-quality.json').read_text())
        self.assertEqual(report['raw_acquisition_counts'], {'cache-reused': 1, 'downloaded': 1})
        self.assertEqual(report['eligible_station_days'], 2)
        self.assertEqual(report['failures'], [])
        with gzip.open(self.root / 'two/openaq-station-days.csv.gz', 'rt') as stream:
            self.assertEqual([r['mean_ug_m3'] for r in csv.DictReader(stream)], ['20.0', '20.0'])

    def test_source_adapter_uses_shared_cache_without_forced_daily_refresh(self):
        from data_sources import Sources
        source = Sources(self.root / 'edition', '2026-11-09T00:00:00+00:00', self.cache)
        with patch.object(source, 'run', side_effect=RuntimeError('captured')) as run:
            with self.assertRaisesRegex(RuntimeError, 'captured'):
                source.india()
        args = list(map(str, run.call_args.args))
        self.assertEqual(Path(args[1]).name, 'fetch-india-openaq-pm25.py')
        self.assertEqual(args[args.index('--cache-dir') + 1], str(self.cache / 'india-openaq'))
        self.assertIn('--refresh-index', args)
        self.assertNotIn('--refresh-since', args)
        self.assertFalse((ROOT / 'scripts/fetch-openaq-pm25.py').exists())


if __name__ == '__main__':
    unittest.main()
