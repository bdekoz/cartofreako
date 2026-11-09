#!/usr/bin/env python3
"""Exercise acquisition failure isolation, cache reuse and CSV identity checks."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("refresh", ROOT / "scripts/refresh-orbiting-snapshot.py")
refresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(refresh)
DATA = ROOT / "assets.static/orbital-technosphere/20261103"


class Refresh(unittest.TestCase):
    def test_duplicate_catalog_ids_rejected(self):
        lines = (DATA / "celestrak-iridium-next.csv").read_bytes().splitlines(keepends=True)
        with self.assertRaisesRegex(ValueError, "duplicate ID"):
            refresh.validate_csv(lines[0] + lines[1] + lines[1], "duplicate")

    def test_fresh_download_is_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(refresh, "urlopen", return_value=io.BytesIO(b"data")) as download:
                first = refresh.fetch("https://example.invalid/catalog.csv", Path(directory))
                second = refresh.fetch("https://example.invalid/catalog.csv", Path(directory))
                self.assertEqual(first, second)
                download.assert_called_once()

    def test_mid_capture_failure_installs_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            template = directory / "template.json"
            profile = json.loads((DATA / "orbital-technosphere-profile.json").read_text())
            template.write_text(json.dumps(profile))
            output = directory / "snapshot"
            argv = ["refresh", "--template", str(template), "--output", str(output),
                    "--cache", str(directory / "cache")]
            active = (DATA / "celestrak-active.csv").read_bytes()
            with patch.object(sys, "argv", argv), patch.object(refresh, "fetch", side_effect=[
                    (active, {"url": "fixture"}), OSError("HTTP 403; stop")]) as download, \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(refresh.main(), 1)
                self.assertEqual(download.call_count, 2)
            self.assertFalse(output.exists())
            self.assertEqual(json.loads(template.read_text()), profile)

    def test_existing_snapshot_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sys, "argv", ["refresh", "--template", "unused.json",
                    "--output", directory, "--cache", directory]), \
                    patch.object(refresh, "fetch") as download, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(refresh.main(), 1)
                download.assert_not_called()

    def capture_nasa_reference(self, nasa_result, historical=True):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            template = directory / "template.json"
            profile = json.loads((DATA / "orbital-technosphere-profile.json").read_text())
            profile["catalogs"]["groups"] = []
            template.write_text(json.dumps(profile))
            output = directory / "snapshot"
            argv = ["refresh", "--template", str(template), "--output", str(output),
                    "--cache", str(directory / "cache")]
            if historical:
                argv += ["--historical-reference-profile", str(
                    ROOT / "assets.static/orbital-technosphere/orbital-technosphere-profile.json")]
            active = (DATA / "celestrak-active.csv").read_bytes()
            messages = io.StringIO()
            with patch.object(sys, "argv", argv), patch.object(refresh, "fetch", side_effect=[
                    (active, {"url": "fixture"}), nasa_result]), \
                    contextlib.redirect_stdout(messages), contextlib.redirect_stderr(messages):
                status = refresh.main()
            files = {p.name: p.read_bytes() for p in output.iterdir()} if output.exists() else {}
            self.assertEqual(json.loads(template.read_text()), profile)
            return status, files, messages.getvalue()

    def test_nasa_network_failure_is_nonfatal_with_historical_reference(self):
        status, files, messages = self.capture_nasa_reference(OSError("Network is unreachable"))
        self.assertEqual(status, 0)
        self.assertIn("WARNING (nonfatal)", messages)
        self.assertIn("Network is unreachable", messages)
        self.assertIn("2026-08-13T15:36:00Z", messages)
        self.assertIn("Created", messages)
        nasa = json.loads(files["orbital-technosphere-profile.json"])["catalogs"]["nasa_ssc_reference"]
        self.assertEqual(nasa["reference_status"], "historical-validation-only")
        self.assertEqual(nasa["refresh_error"], "Network is unreachable")
        self.assertEqual(files["nasa-ssc-reference.json"],
                         (ROOT / "assets.static/orbital-technosphere/nasa-ssc-reference.json").read_bytes())
        self.assertEqual(files["celestrak-active.csv"], (DATA / "celestrak-active.csv").read_bytes())
        receipt = json.loads(files["acquisition.json"])["sources"][-1]
        self.assertEqual(receipt["reference_timestamp"], nasa["reference_timestamp"])
        self.assertEqual(receipt["sha256"], refresh.digest(files["nasa-ssc-reference.json"]))

    def test_nasa_failure_without_historical_reference_installs_nothing(self):
        status, files, messages = self.capture_nasa_reference(OSError("Network is unreachable"), historical=False)
        self.assertEqual(status, 1)
        self.assertEqual(files, {})
        self.assertIn("no snapshot installed", messages)

    def test_nasa_success_clears_previous_refresh_error(self):
        data = (DATA / "nasa-ssc-reference.json").read_bytes()
        status, files, messages = self.capture_nasa_reference((data, {"url": "fixture"}))
        self.assertEqual(status, 0)
        nasa = json.loads(files["orbital-technosphere-profile.json"])["catalogs"]["nasa_ssc_reference"]
        self.assertEqual(nasa["reference_timestamp"], "2026-11-03T17:10:00Z")
        self.assertTrue(nasa["reference_status"].startswith("current-query"))
        self.assertNotIn("refresh_error", nasa)
        self.assertNotIn("WARNING", messages)


if __name__ == "__main__":
    unittest.main()
