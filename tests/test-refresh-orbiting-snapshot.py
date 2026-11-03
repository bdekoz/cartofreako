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


if __name__ == "__main__":
    unittest.main()
