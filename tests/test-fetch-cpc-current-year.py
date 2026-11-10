#!/usr/bin/env python3
"""Append real NetCDF daily arrays without requesting or changing existing observations."""
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ctypes as C
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import numpy as np
from scipy.io import netcdf_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from dataset import DatasetError, atomic_json, digest
from ocean_temperature import NetCDF
from data_sources import netcdf_days
spec = importlib.util.spec_from_file_location('cpc_current', ROOT / 'scripts/fetch-cpc-current-year.py')
cpc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpc)


def ncfile(path, days, *, wrong_grid=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with netcdf_file(path, 'w', version=2) as nc:
        nc.createDimension('time', None)
        nc.createDimension('lat', 360)
        nc.createDimension('lon', 720)
        times = nc.createVariable('time', 'd', ('time',))
        times.units = b'hours since 1900-01-01 00:00:00'
        times[:] = [(d - date(1900, 1, 1)).days * 24 for d in days]
        times.actual_range = np.array([times[0], times[-1]], dtype='float64')
        lat = nc.createVariable('lat', 'f', ('lat',))
        lon = nc.createVariable('lon', 'f', ('lon',))
        lat[:] = np.arange(89.75, -90, -.5)
        lon[:] = np.arange(.25, 360, .5)[::-1] if wrong_grid else np.arange(.25, 360, .5)
        data = nc.createVariable('tmax', 'f', ('time', 'lat', 'lon'))
        data.units, data.max_period = b'degC', b'6z to 6z'
        data.missing_value = np.float32(-9.96921e36)
        data.valid_range = np.array([-90, 50], dtype='float32')
        data.actual_range = np.array([min(d.day for d in days), max(d.day for d in days)], dtype='float32')
        for i, day in enumerate(days):
            data[i] = np.full((360, 720), day.day, dtype='float32')


def xml_inventory(end=date(2026, 1, 4), resolution=24):
    start = (date(2026, 1, 1) - date(1900, 1, 1)).days * 24
    return (f'<gridDataset><axis name="time"><attribute name="units" '
            f'value="hours since 1900-01-01 00:00:00"/><values start="{start}" '
            f'end="{start + (end - date(2026,1,1)).days * 24}" '
            f'npts="{(end-date(2026,1,1)).days+1}" resolution="{resolution}"/>'
            '</axis></gridDataset>').encode()


class Incremental(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.seed = self.root / 'seed.nc'
        ncfile(self.seed, [date(2026, 1, 1), date(2026, 1, 2)])
        self.original = digest(self.seed)
        self.cache, self.output = self.root / 'cache', self.root / 'output.nc'
        self.calls = []
        self.fail_day, self.bad_date, self.bad_grid = None, False, False
        self.end = date(2026, 1, 4)
        self.addCleanup(patch.stopall)
        patch('sys.stdout', new_callable=io.StringIO).start()

    def fetch(self, url, path, cache, **_):
        self.calls.append(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        if url.endswith('/dataset.xml'):
            path.write_bytes(xml_inventory(self.end))
        else:
            day = date.fromisoformat(parse_qs(urlsplit(url).query)['time'][0][:10])
            if day == self.fail_day:
                raise DatasetError('fixture unavailable')
            ncfile(path, [day + timedelta(days=1) if self.bad_date else day], wrong_grid=self.bad_grid)
        receipt = {'url': url, 'sha256': digest(path), 'bytes': path.stat().st_size,
                   'checked_at': '2026-01-05T00:00:00Z', 'retrieved_at': '2026-01-05T00:00:00Z'}
        atomic_json(path.with_name(path.name + '.receipt.json'), receipt)
        return receipt

    def update(self, **kwargs):
        return cpc.update('tmax', 2026, self.cache, self.output, seeds=[self.seed],
                          as_of=datetime(2026, 1, 5, tzinfo=timezone.utc),
                          subset_base='https://fixture.invalid/subset', fetcher=self.fetch, **kwargs)

    def test_only_missing_days_are_requested_and_existing_arrays_are_unchanged(self):
        result = self.update()
        self.assertEqual(result['data_through'], '2026-01-04')
        requested = [parse_qs(urlsplit(url).query)['time'][0][:10] for url in self.calls if '?' in url]
        self.assertEqual(requested, ['2026-01-03', '2026-01-04'])
        with NetCDF(self.output) as nc:
            for i in range(4):
                np.testing.assert_array_equal(nc.read('tmax', start=(i,0,0), count=(1,360,720)), i+1)
            self.assertEqual(nc.attributes('time')['actual_range'][-1],
                             (date(2026,1,4)-date(1900,1,1)).days*24)
        self.assertEqual(digest(self.seed), self.original)
        self.assertEqual(len(netcdf_days(self.output, 'tmax')), 4)
        previous = digest(self.output)
        self.update()
        self.assertEqual(digest(self.output), previous)
        self.assertEqual(len([url for url in self.calls if '?' in url]), 2)

    def test_late_failure_retains_prefix_and_saved_days_are_not_requested_again(self):
        self.fail_day = date(2026, 1, 4)
        with self.assertRaisesRegex(DatasetError, 'fixture unavailable'):
            self.update()
        self.assertFalse(self.output.exists())
        record = json.loads((self.cache / 'cpc-current/tmax.2026.json').read_text())
        self.assertEqual(record['data_through'], '2026-01-02')
        self.fail_day = None
        self.update()
        requested = [parse_qs(urlsplit(url).query).get('time', [''])[0][:10] for url in self.calls]
        self.assertEqual(requested.count('2026-01-03'), 1)
        self.assertEqual(digest(self.seed), self.original)

    def test_wrong_date_or_grid_cannot_replace_prefix(self):
        for field in ('bad_date', 'bad_grid'):
            with self.subTest(field=field):
                setattr(self, field, True)
                cache = self.root / field
                with self.assertRaises(DatasetError):
                    cpc.update('tmax', 2026, cache, seeds=[self.seed],
                               as_of=datetime(2026,1,5,tzinfo=timezone.utc), fetcher=self.fetch)
                record = json.loads((cache / 'cpc-current/tmax.2026.json').read_text())
                self.assertEqual(record['data_through'], '2026-01-02')
                setattr(self, field, False)

    def test_no_new_dates_only_checks_the_small_inventory(self):
        self.end = date(2026, 1, 2)
        result = self.update()
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(self.calls[0].endswith('/dataset.xml'))
        self.assertEqual(result['sha256'], self.original)

    def test_observation_cutoff_does_not_fetch_later_published_days(self):
        self.end = date(2026, 1, 6)
        result = self.update()
        self.assertEqual(result['data_through'], '2026-01-04')
        requested = [parse_qs(urlsplit(url).query)['time'][0][:10] for url in self.calls if '?' in url]
        self.assertEqual(requested, ['2026-01-03', '2026-01-04'])

    def test_corrupt_current_year_cache_fails_before_any_provider_request(self):
        result = self.update(seed_only=True)
        obj = self.cache / 'sha256' / result['sha256']
        obj.unlink()
        obj.write_bytes(b'changed')
        with self.assertRaisesRegex(DatasetError, 'checksum mismatch'):
            self.update()
        self.assertEqual(self.calls, [])

    def test_inventory_rejects_non_daily_spacing(self):
        path = self.root / 'inventory.xml'
        path.write_bytes(xml_inventory(resolution=48))
        with self.assertRaisesRegex(DatasetError, 'contiguous daily'):
            cpc.inventory(path, 2026)

    def test_netcdf4_string_attributes_from_real_subset_format_are_readable(self):
        path = self.root / 'strings.nc'
        handle = C.c_int()
        check = NetCDF.__new__(NetCDF).check
        check(NetCDF.lib.nc_create(str(path).encode(), 4096, C.byref(handle)))
        try:
            values = (C.c_char_p * 1)(b'hours since 1900-01-01 00:00:00')
            check(NetCDF.lib.nc_put_att_string(handle, -1, b'units', C.c_size_t(1), values))
        finally:
            check(NetCDF.lib.nc_close(handle))
        with NetCDF(path) as nc:
            self.assertEqual(nc.attributes()['units'], 'hours since 1900-01-01 00:00:00')

    def test_real_cli_uses_subset_service_and_reuses_all_days_on_retry(self):
        calls = []
        files = {}
        for day in (date(2026,1,3), date(2026,1,4)):
            path = self.root / (str(day) + '.nc')
            ncfile(path, [day])
            files[str(day)] = path.read_bytes()
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_GET(self):
                calls.append(self.path)
                body = (xml_inventory() if self.path.endswith('/dataset.xml') else
                        files[parse_qs(urlsplit(self.path).query)['time'][0][:10]])
                self.send_response(200)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('ETag', '"fixture-daily-v1"')
                self.end_headers()
                self.wfile.write(body)
        server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
        self.addCleanup(server.server_close)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        command = [sys.executable, str(ROOT / 'scripts/fetch-cpc-current-year.py'), '--variable', 'tmax',
                   '--seed', str(self.seed), '--cache', str(self.cache), '--output', str(self.output),
                   '--subset-base', f'http://127.0.0.1:{server.server_port}', '--as-of', '2026-01-05T00:00:00Z']
        for _ in range(2):
            result = subprocess.run(command, text=True, capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 3)
        self.assertEqual(netcdf_days(self.output, 'tmax')[-1], date(2026,1,4))


if __name__ == '__main__':
    unittest.main()
