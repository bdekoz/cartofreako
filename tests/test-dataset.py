#!/usr/bin/env python3
"""Transaction, integrity, freshness and selection regression tests."""
from datetime import datetime, timezone
from http.client import IncompleteRead
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import io
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import dataset
from data_http import fetch


def virtual_clock():
    clock = SimpleNamespace(now=0.0, sleeps=[])
    clock.monotonic = lambda: clock.now
    clock.time = lambda: 1794240000 + clock.now
    def sleep(delay):
        clock.sleeps.append(delay)
        clock.now += delay
    clock.sleep = sleep
    return clock


def fixture(root, ident="fixture"):
    root.mkdir(parents=True, exist_ok=True)
    registry = json.loads((ROOT / "config/data-products.json").read_text())
    source_ids = {s for g in registry["groups"].values() for s in g["sources"]}
    names = {b for g in registry["groups"].values() for b in g["bindings"]}
    sources, records = [], []
    for name in sorted(source_ids):
        path = root / (name + ".json")
        path.write_text(json.dumps({"fixture": name}))
        records.append(dataset.file_record(root, path))
        sources.append({"id": name, "status": "validated", "acquisition": "pinned-local",
                        "coverage": {"reason": "test fixture"}, "files": [path.name]})
    # Bindings need not all name distinct files; fixture content is not a
    # scientific source adapter. Activation invariants are tested separately.
    manifest = {"schema": dataset.SCHEMA, "dataset_id": ident, "state": "validated",
                "requested_as_of": "2026-11-08T00:00:00Z", "resolved_at": "2026-11-08T01:00:00Z",
                "product_groups": list(dataset.GROUPS), "sources": sources, "files": records,
                "registry": registry,
                "products": json.loads((ROOT/'config/atlas-plates.json').read_text()),
                "bindings": {name: records[0]["path"] for name in names},
                "implementation": {"revision": "fixture", "dirty": False, "files": {}},
                "validation": {"status": "passed", "checks": ["fixture-integrity"]}}
    manifest = dataset.seal(manifest)
    path = root / "dataset.json"
    dataset.atomic_json(path, manifest)
    return path, manifest


class Dataset(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_validated_edition_activation_and_immutable_selection(self):
        path, manifest = fixture(self.root / "editions/first", "first")
        dataset.activate(self.root, path)
        selected, loaded = dataset.load(self.root / "current.json")
        self.assertEqual(selected, path)
        second, _ = fixture(self.root / "editions/second", "second")
        dataset.activate(self.root, second)
        self.assertEqual(loaded["dataset_id"], "first")
        self.assertEqual(dataset.load(selected)[1], manifest)
        self.assertEqual(dataset.load(self.root / "current.json")[1]["dataset_id"], "second")

    def test_corrupt_or_incomplete_candidate_keeps_previous_pointer(self):
        path, _ = fixture(self.root / "editions/first", "first")
        dataset.activate(self.root, path)
        before = (self.root / "current.json").read_bytes()
        candidate, manifest = fixture(self.root / "editions/candidate", "candidate")
        for mutation in ("missing-source", "bad-bytes", "incomplete"):
            changed = json.loads(json.dumps(manifest))
            if mutation == "missing-source":
                changed["sources"] = changed["sources"][:-1]
            elif mutation == "bad-bytes":
                changed["files"][0]["sha256"] = "0" * 64
            else:
                changed["state"] = "preparing"
            dataset.atomic_json(candidate, dataset.seal(changed))
            with self.assertRaises(dataset.DatasetError):
                dataset.activate(self.root, candidate)
            self.assertEqual((self.root / "current.json").read_bytes(), before)

    def test_paths_cannot_escape_edition(self):
        for path in ("../private", "/etc/passwd", ""):
            with self.assertRaises(dataset.DatasetError):
                dataset.safe_path(self.root, path)
        (self.root / "escape").symlink_to(self.root.parent)
        with self.assertRaises(dataset.DatasetError):
            dataset.safe_path(self.root, "escape/other")

    def test_manifest_and_pointer_tampering_are_rejected(self):
        path, manifest = fixture(self.root / "editions/one")
        dataset.activate(self.root, path)
        manifest["resolved_at"] = "2026-11-09T01:00:00Z"
        dataset.atomic_json(path, manifest)
        with self.assertRaises(dataset.DatasetError):
            dataset.load(path)
        with self.assertRaises(dataset.DatasetError):
            dataset.load(self.root / "current.json")

    def test_update_lock_excludes_concurrent_writer(self):
        with dataset.lock(self.root):
            with self.assertRaisesRegex(dataset.DatasetError, "already running"):
                with dataset.lock(self.root):
                    self.fail("acquired a second lock")

    def test_secret_values_are_redacted(self):
        with patch.dict(os.environ, {"FIRMS_MAP_KEY": "private-fixture"}):
            message = dataset.redact("failure https://example/private-fixture user private-fixture")
        self.assertNotIn("private-fixture", message)
        self.assertIn("REDACTED", message)


class Freshness(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        state = self.state = {"data": b"first readable data", "etag": '"one"', "calls": [], "fail": False}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                state["calls"].append(dict(self.headers))
                error = state.get('errors_on_call', {}).get(len(state['calls']))
                if state.get('transient_errors'):
                    error = state['transient_errors'].pop(0)
                if error:
                    self.send_response(error)
                    self.send_header('Retry-After', state.get('retry_after', '7'))
                    self.end_headers()
                    return
                if state["fail"]:
                    self.send_error(503)
                    return
                if len(state['calls']) == state.get('change_on_call'):
                    state.update(data=b'a completely different revision', etag='"two"')
                if ((state['etag'] and self.headers.get("If-None-Match") == state["etag"])
                        or (state.get('last_modified') and self.headers.get('If-Modified-Since') == state['last_modified'])):
                    self.send_response(304)
                    self.end_headers()
                    return
                offset, end, ranged = 0, len(state['data']) - 1, False
                requested = self.headers.get('Range')
                validator = state['etag']
                if not validator or validator.startswith('W/'):
                    validator = state.get('last_modified')
                if (requested and not state.get('ignore_ranges')
                        and self.headers.get('If-Range') in (None, validator)):
                    start, stop = requested.split('=')[1].split('-')
                    offset = int(start)
                    end = min(int(stop), end) if stop else end
                    ranged = True
                self.send_response(206 if ranged else 200)
                if not state.get('no_validator'):
                    if state['etag']:
                        self.send_header("ETag", state["etag"])
                    if state.get('last_modified'):
                        self.send_header('Last-Modified', state['last_modified'])
                if ranged:
                    reported_start = offset + 1 if state.get('bad_range') else offset
                    self.send_header('Content-Range', f'bytes {reported_start}-{end}/{len(state["data"])}')
                self.send_header("Content-Length", str(end-offset+1))
                self.end_headers()
                payload = state['data'][offset:end+1]
                if (state.pop('truncate', False) or state.get('truncate_always')
                        or (state.get('truncate_unbounded') and (not requested or requested.endswith('-')))):
                    payload = payload[:len(payload)//2]
                self.wfile.write(payload)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.server_port}/year.nc"

    def retain_interrupted_partial(self, destination, **kwargs):
        # Force an exhausted budget to exercise recovery on a later invocation.
        with patch.dict(os.environ, {'DATA_HTTP_RETRY_BUDGET': '1'}):
            with self.assertRaisesRegex(dataset.DatasetError, 'retry budget'):
                fetch(self.url, destination, self.root/'cache', **kwargs)

    def test_unchanged_data_uses_conditional_http_and_keeps_retrieval_time(self):
        first = fetch(self.url, self.root / "first", self.root / "cache")
        second = fetch(self.url, self.root / "second", self.root / "cache")
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertEqual(first["retrieved_at"], second["retrieved_at"])
        self.assertEqual(self.state["calls"][-1]["If-None-Match"], '"one"')

    def test_changed_readable_data_creates_new_object_and_preserves_old(self):
        first = fetch(self.url, self.root / "first", self.root / "cache")
        self.state.update(data=b"second readable data", etag='"two"')
        second = fetch(self.url, self.root / "second", self.root / "cache")
        self.assertNotEqual(first["sha256"], second["sha256"])
        self.assertEqual((self.root / "first").read_bytes(), b"first readable data")

    def test_failed_revalidation_does_not_claim_old_cache_is_current(self):
        fetch(self.url, self.root / "first", self.root / "cache")
        self.state["fail"] = True
        with patch('data_http_policy.time', virtual_clock()), \
             patch('data_http_policy.random.uniform', return_value=1), \
             patch.dict(os.environ, {'DATA_HTTP_RETRY_BUDGET': '3'}), \
             patch('sys.stderr', new_callable=io.StringIO):
            with self.assertRaises(dataset.DatasetError):
                fetch(self.url, self.root / "second", self.root / "cache")
        self.assertFalse((self.root / "second").exists())
        self.assertEqual(len(self.state['calls']), 3)  # Initial success plus two attempts within budget.

    def test_minimum_interval_respects_provider_policy(self):
        fetch(self.url, self.root / "first", self.root / "cache", minimum_interval=7200)
        second = fetch(self.url, self.root / "second", self.root / "cache", minimum_interval=7200)
        self.assertEqual(len(self.state["calls"]), 1)
        self.assertEqual(second["acquisition"], "policy-cache")

    def test_interrupted_download_resumes_only_matching_remote_identity(self):
        self.state['truncate'] = True
        self.retain_interrupted_partial(self.root/'first')
        self.assertFalse((self.root/'first').exists())
        self.assertEqual(len(list((self.root/'cache/http').glob('*.part'))), 1)
        fetch(self.url, self.root/'second', self.root/'cache')
        self.assertEqual((self.root/'second').read_bytes(), self.state['data'])
        self.assertEqual(self.state['calls'][-1]['If-Range'], '"one"')
        self.assertFalse(list((self.root/'cache/http').glob('*.part')))

    def test_changed_remote_identity_restarts_instead_of_appending(self):
        self.state['truncate'] = True
        self.retain_interrupted_partial(self.root/'first')
        self.state.update(data=b'a completely different revision', etag='"two"')
        fetch(self.url, self.root/'second', self.root/'cache')
        self.assertEqual((self.root/'second').read_bytes(), self.state['data'])

    def test_bounded_ranges_avoid_proxy_truncation_and_revalidate(self):
        self.state['truncate_unbounded'] = True
        first = fetch(self.url, self.root/'first', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'first').read_bytes(), self.state['data'])
        self.assertEqual([call['Range'] for call in self.state['calls']],
                         ['bytes=0-6', 'bytes=7-13', 'bytes=14-18'])
        self.assertEqual(self.state['calls'][1]['If-Range'], '"one"')
        second = fetch(self.url, self.root/'second', self.root/'cache', range_size=7)
        self.assertEqual(first['sha256'], second['sha256'])
        self.assertEqual(self.state['calls'][-1]['If-None-Match'], '"one"')

    def test_bounded_ranges_resume_existing_open_ended_partial(self):
        self.state['truncate_unbounded'] = True
        self.retain_interrupted_partial(self.root/'first')
        fetch(self.url, self.root/'second', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'second').read_bytes(), self.state['data'])
        self.assertEqual(self.state['calls'][1]['Range'], 'bytes=9-15')
        self.assertFalse(list((self.root/'cache/http').glob('*.part')))

    def test_interrupted_bounded_range_preserves_and_resumes_partial(self):
        self.state['truncate'] = True
        self.retain_interrupted_partial(self.root/'first', range_size=7)
        self.assertFalse((self.root/'first').exists())
        fetch(self.url, self.root/'second', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'second').read_bytes(), self.state['data'])
        self.assertEqual(self.state['calls'][1]['Range'], 'bytes=3-9')

    def test_ocean_cached_path_uses_ranges_and_recovers_truncation_in_one_call(self):
        spec = importlib.util.spec_from_file_location('ocean_fetch', ROOT/'scripts/fetch-ocean-temperature.py')
        ocean = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ocean)
        self.state.update(truncate=True, truncate_unbounded=True, etag=None,
                          last_modified='Mon, 13 Apr 2020 21:00:04 GMT')
        clock = virtual_clock()
        with patch.object(ocean, 'BASE', self.url.rsplit('/', 1)[0] + '/'), \
             patch.object(ocean, 'NetCDF') as netcdf, \
             patch.dict(os.environ, {'DATA_HTTP_CACHE': str(self.root/'cache')}), \
             patch('data_http_policy.time', clock):
            netcdf.return_value.__enter__.return_value.shape.return_value = (1, 720, 1440)
            record = ocean.fetch('sst.day.mean.2025.nc', self.root/'ocean')
        self.assertEqual((self.root/'ocean/sst.day.mean.2025.nc').read_bytes(), self.state['data'])
        self.assertEqual(record['bytes'], len(self.state['data']))
        self.assertEqual([call['Range'] for call in self.state['calls']], ['bytes=0-8388607', 'bytes=9-18'])
        self.assertEqual(self.state['calls'][1]['If-Range'], self.state['last_modified'])
        self.assertEqual(clock.sleeps, [2])

    def test_body_interruptions_recover_saved_bytes(self):
        from data_http_policy import open_response
        for error in (TimeoutError('read timed out'), ConnectionResetError('connection reset'),
                      IncompleteRead(b't', 3)):
            with self.subTest(error=type(error).__name__):
                cache = self.root/type(error).__name__
                calls = 0
                class InterruptedResponse(io.BytesIO):
                    status = 206
                    headers = {'ETag': '"one"', 'Content-Length': '7', 'Content-Range': 'bytes 0-6/19'}
                    def read(self, size):
                        if self.tell() == 0:
                            return super().read(4)
                        raise error
                def interrupted_response(*args, **kwargs):
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        return InterruptedResponse(self.state['data'])
                    return open_response(*args, **kwargs)
                before = len(self.state['calls'])
                with patch('data_http.open_response', side_effect=interrupted_response), \
                     patch('data_http_policy.time', virtual_clock()):
                    fetch(self.url, cache/'output', cache, range_size=7)
                offset = 5 if isinstance(error, IncompleteRead) else 4
                self.assertEqual(self.state['calls'][before]['Range'], f'bytes={offset}-{offset+6}')
                self.assertEqual(self.state['calls'][before]['If-Range'], '"one"')
                self.assertEqual((cache/'output').read_bytes(), self.state['data'])

    def test_repeated_truncation_exhausts_budget_without_publishing_or_counting_success(self):
        self.state['truncate_always'] = True
        clock = virtual_clock()
        with patch('data_http_policy.time', clock), \
             patch.dict(os.environ, {'DATA_HTTP_RETRY_BUDGET': '5'}), \
             patch('data_http_policy.Pacer.success') as success:
            with self.assertRaisesRegex(dataset.DatasetError, 'HTTP response retry budget'):
                fetch(self.url, self.root/'output', self.root/'cache', range_size=7)
        success.assert_not_called()
        self.assertEqual(len(self.state['calls']), 2)
        self.assertEqual(clock.sleeps, [2])
        self.assertEqual(next((self.root/'cache/http').glob('*.part')).read_bytes(), self.state['data'][:6])
        self.assertFalse((self.root/'output').exists())
        self.assertFalse((self.root/'cache/sha256').exists())

    def test_body_retry_does_not_reset_http_status_retry_budget(self):
        self.state.update(truncate=True, errors_on_call={2: 503, 3: 503}, retry_after='1')
        clock = virtual_clock()
        with patch('data_http_policy.time', clock), \
             patch('data_http_policy.random.uniform', return_value=1), \
             patch.dict(os.environ, {'DATA_HTTP_RETRY_BUDGET': '3'}):
            with self.assertRaisesRegex(dataset.DatasetError, 'HTTP 503; retry budget'):
                fetch(self.url, self.root/'output', self.root/'cache', range_size=7)
        self.assertEqual(len(self.state['calls']), 2)
        self.assertEqual(clock.sleeps, [2])
        self.assertEqual(next((self.root/'cache/http').glob('*.part')).read_bytes(), self.state['data'][:3])
        self.assertFalse((self.root/'output').exists())

    def test_revision_changed_between_ranges_replaces_partial(self):
        self.state['change_on_call'] = 2
        fetch(self.url, self.root/'first', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'first').read_bytes(), self.state['data'])

    def test_server_ignoring_bounded_ranges_downloads_full_object(self):
        self.state['ignore_ranges'] = True
        fetch(self.url, self.root/'first', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'first').read_bytes(), self.state['data'])
        self.assertEqual(len(self.state['calls']), 1)

    def test_inconsistent_range_cannot_publish_an_object(self):
        self.state['bad_range'] = True
        with self.assertRaisesRegex(dataset.DatasetError, 'inconsistent partial response'):
            fetch(self.url, self.root/'first', self.root/'cache', range_size=7)
        self.assertFalse((self.root/'first').exists())

    def test_multiple_ranges_require_identity_validator(self):
        self.state['no_validator'] = True
        with self.assertRaisesRegex(dataset.DatasetError, 'without an identity validator'):
            fetch(self.url, self.root/'first', self.root/'cache', range_size=7)
        self.assertFalse((self.root/'first').exists())

    def test_bounded_resume_with_last_modified_like_noaa(self):
        self.state.update(etag=None, last_modified='Mon, 13 Apr 2020 21:00:04 GMT', truncate=True)
        self.retain_interrupted_partial(self.root/'first')
        fetch(self.url, self.root/'second', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'second').read_bytes(), self.state['data'])
        self.assertEqual(self.state['calls'][1]['If-Range'], self.state['last_modified'])

    def test_provider_throttling_retries_same_range_and_respects_delay(self):
        self.state['transient_errors'] = [429, 503]
        clock = virtual_clock()
        with patch('data_http_policy.time', clock), \
             patch('data_http_policy.random.uniform', return_value=1), \
             patch('sys.stderr', new_callable=io.StringIO):
            fetch(self.url, self.root/'first', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'first').read_bytes(), self.state['data'])
        self.assertEqual(clock.sleeps, [30, 7])
        self.assertEqual([call['Range'] for call in self.state['calls'][:3]], ['bytes=0-6'] * 3)

    def test_retry_budget_failure_retains_partial_for_next_run(self):
        self.state['truncate'] = True
        self.retain_interrupted_partial(self.root/'first')
        partial = next((self.root/'cache/http').glob('*.part'))
        before = partial.read_bytes()
        self.state['transient_errors'] = [429] * 10
        with patch('data_http_policy.time', virtual_clock()), \
             patch('data_http_policy.random.uniform', return_value=1), \
             patch.dict(os.environ, {'DATA_HTTP_RETRY_BUDGET': '60'}), \
             patch('sys.stderr', new_callable=io.StringIO):
            with self.assertRaisesRegex(dataset.DatasetError, 'year.nc; 9 partial bytes retained'):
                fetch(self.url, self.root/'failed', self.root/'cache', range_size=7)
        self.assertEqual(partial.read_bytes(), before)
        self.assertFalse((self.root/'failed').exists())
        self.state['transient_errors'] = []
        fetch(self.url, self.root/'recovered', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'recovered').read_bytes(), self.state['data'])

    def test_endpoint_switch_keeps_separate_partial_identity(self):
        self.state['truncate'] = True
        self.retain_interrupted_partial(self.root/'old')
        partial = next((self.root/'cache/http').glob('*.part'))
        before = partial.read_bytes()
        fetch(self.url+'?endpoint=bulk', self.root/'new', self.root/'cache', range_size=7)
        self.assertEqual(partial.read_bytes(), before)
        fetch(self.url, self.root/'resumed', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'resumed').read_bytes(), self.state['data'])

    def test_cpc_script_uses_configured_endpoint_ranges_cache_and_manifest(self):
        validator = self.root/'gdalinfo-fixture'
        validator.write_text('#!' + sys.executable + '\n' + '''import pathlib, sys
path = sys.argv[1].split(':', 1)[1].rsplit(':', 1)[0]
assert pathlib.Path(path).read_bytes() == b'first readable data'
''')
        validator.chmod(0o755)
        env = {**os.environ, 'CPC_BASE_URL': self.url.rsplit('/', 1)[0],
               'CPC_HTTP_RANGE_SIZE': '7', 'DATA_HTTP_CACHE': str(self.root/'cache'),
               'GDALINFO': str(validator), 'DATA_UPDATE_RUN_ID': 'script-fixture'}
        command = ['bash', str(ROOT/'scripts/fetch-anthropocene-cpc-data.sh'),
                   str(self.root/'cpc'), '1981', '1981']
        result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        raw = self.root/'cpc/.raw/cpc'
        self.assertEqual((raw/'tmax.1981.nc').read_bytes(), self.state['data'])
        self.assertEqual((raw/'tmin.1981.nc').read_bytes(), self.state['data'])
        self.assertEqual(len(self.state['calls']), 6)
        self.assertEqual(self.state['calls'][0]['Range'], 'bytes=0-6')
        self.assertEqual(len((raw/'SHA256SUMS').read_text().splitlines()), 2)
        calls = len(self.state['calls'])
        env['DATA_UPDATE_RUN_ID'] = 'another-script-run'
        result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.state['calls']), calls)
        self.assertIn('same-utc-day', result.stderr)
        # Direct legacy fetches retain readable local-file reuse, even though
        # missing-file transfers now use the same shared Python downloader.
        env.pop('DATA_HTTP_CACHE')
        result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.state['calls']), calls)

    def test_shared_source_is_acquired_once_in_a_run_then_revalidated_next_run(self):
        with patch.dict(os.environ,{'DATA_UPDATE_RUN_ID':'first-run'}):
            first=fetch(self.url,self.root/'first',self.root/'cache')
            self.state.update(data=b'provider revision',etag='"two"')
            shared=fetch(self.url,self.root/'shared',self.root/'cache')
        self.assertEqual(first['sha256'],shared['sha256'])
        self.assertEqual(len(self.state['calls']),1)
        with patch.dict(os.environ,{'DATA_UPDATE_RUN_ID':'second-run'}):
            revised=fetch(self.url,self.root/'revised',self.root/'cache')
        self.assertNotEqual(first['sha256'],revised['sha256'])
        self.assertEqual(len(self.state['calls']),2)

    def test_same_utc_day_reuses_verified_bytes_across_runs_then_revalidates(self):
        current = [datetime(2026, 11, 9, 23, 50, tzinfo=timezone.utc)]
        with patch('data_http.datetime') as clock, \
             patch('data_http.utcnow', side_effect=lambda: current[0].isoformat()):
            clock.now.side_effect = lambda zone: current[0]
            clock.fromisoformat.side_effect = datetime.fromisoformat
            with patch.dict(os.environ, {'DATA_UPDATE_RUN_ID': 'daily-first'}):
                first = fetch(self.url, self.root/'first', self.root/'cache', same_day_cache=True)
            current[0] = datetime(2026, 11, 9, 23, 59, tzinfo=timezone.utc)
            with patch.dict(os.environ, {'DATA_UPDATE_RUN_ID': 'daily-second'}):
                second = fetch(self.url, self.root/'second', self.root/'cache', same_day_cache=True)
            self.assertEqual(len(self.state['calls']), 1)
            self.assertEqual(second['checked_at'], first['checked_at'])
            self.assertEqual(second['cache_policy'], 'same-utc-day')
            current[0] = datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc)
            with patch.dict(os.environ, {'DATA_UPDATE_RUN_ID': 'next-day'}):
                next_day = fetch(self.url, self.root/'next-day', self.root/'cache', same_day_cache=True)
        self.assertEqual(len(self.state['calls']), 2)
        self.assertEqual(self.state['calls'][-1]['If-None-Match'], '"one"')
        self.assertEqual(next_day['sha256'], first['sha256'])

    def test_same_day_cache_still_rejects_corrupt_immutable_objects(self):
        record = fetch(self.url, self.root/'first', self.root/'cache', same_day_cache=True)
        obj = self.root/'cache/sha256'/record['sha256']
        obj.chmod(0o644)
        obj.write_bytes(b'corrupt')
        with self.assertRaisesRegex(dataset.DatasetError, 'Corrupted HTTP cache object'):
            fetch(self.url, self.root/'second', self.root/'cache', same_day_cache=True)
        self.assertFalse((self.root/'second').exists())


if __name__ == "__main__":
    unittest.main()
