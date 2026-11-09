#!/usr/bin/env python3
"""Transaction, integrity, freshness and selection regression tests."""
from datetime import datetime, timezone
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import dataset
from data_http import fetch


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
                if state.get('transient_errors'):
                    self.send_response(state['transient_errors'].pop(0))
                    self.send_header('Retry-After', '7')
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
                if (state.pop('truncate', False)
                        or (state.get('truncate_unbounded') and (not requested or requested.endswith('-')))):
                    payload = payload[:len(payload)//2]
                self.wfile.write(payload)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.server_port}/year.nc"

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
        with patch('data_http.time.sleep'), patch('sys.stderr', new_callable=io.StringIO):
            with self.assertRaises(dataset.DatasetError):
                fetch(self.url, self.root / "second", self.root / "cache")
        self.assertFalse((self.root / "second").exists())
        self.assertEqual(len(self.state['calls']), 7)  # Initial success plus six attempts.

    def test_minimum_interval_respects_provider_policy(self):
        fetch(self.url, self.root / "first", self.root / "cache", minimum_interval=7200)
        second = fetch(self.url, self.root / "second", self.root / "cache", minimum_interval=7200)
        self.assertEqual(len(self.state["calls"]), 1)
        self.assertEqual(second["acquisition"], "policy-cache")

    def test_interrupted_download_resumes_only_matching_remote_identity(self):
        self.state['truncate'] = True
        with self.assertRaises(dataset.DatasetError):
            fetch(self.url, self.root/'first', self.root/'cache')
        self.assertFalse((self.root/'first').exists())
        self.assertEqual(len(list((self.root/'cache/http').glob('*.part'))), 1)
        fetch(self.url, self.root/'second', self.root/'cache')
        self.assertEqual((self.root/'second').read_bytes(), self.state['data'])
        self.assertEqual(self.state['calls'][-1]['If-Range'], '"one"')
        self.assertFalse(list((self.root/'cache/http').glob('*.part')))

    def test_changed_remote_identity_restarts_instead_of_appending(self):
        self.state['truncate'] = True
        with self.assertRaises(dataset.DatasetError):
            fetch(self.url, self.root/'first', self.root/'cache')
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
        with self.assertRaises(dataset.DatasetError):
            fetch(self.url, self.root/'first', self.root/'cache')
        fetch(self.url, self.root/'second', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'second').read_bytes(), self.state['data'])
        self.assertEqual(self.state['calls'][1]['Range'], 'bytes=9-15')
        self.assertFalse(list((self.root/'cache/http').glob('*.part')))

    def test_interrupted_bounded_range_preserves_and_resumes_partial(self):
        self.state['truncate'] = True
        with self.assertRaises(dataset.DatasetError):
            fetch(self.url, self.root/'first', self.root/'cache', range_size=7)
        self.assertFalse((self.root/'first').exists())
        fetch(self.url, self.root/'second', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'second').read_bytes(), self.state['data'])
        self.assertEqual(self.state['calls'][1]['Range'], 'bytes=3-9')

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
        with self.assertRaises(dataset.DatasetError):
            fetch(self.url, self.root/'first', self.root/'cache')
        fetch(self.url, self.root/'second', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'second').read_bytes(), self.state['data'])
        self.assertEqual(self.state['calls'][1]['If-Range'], self.state['last_modified'])

    def test_provider_throttling_retries_same_range_and_respects_delay(self):
        self.state['transient_errors'] = [429, 503]
        with patch('data_http.time.sleep') as sleep, patch('sys.stderr', new_callable=io.StringIO):
            fetch(self.url, self.root/'first', self.root/'cache', range_size=7)
        self.assertEqual((self.root/'first').read_bytes(), self.state['data'])
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [7, 7])
        self.assertEqual([call['Range'] for call in self.state['calls'][:3]], ['bytes=0-6'] * 3)

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


if __name__ == "__main__":
    unittest.main()
