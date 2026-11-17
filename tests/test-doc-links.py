#!/usr/bin/env python3
"""Check GitHub anchors and the boundary between templates and public pages."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("doc_links", ROOT / "scripts/check-doc-links.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class DocumentationLinks(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="cartofreako-doc-links-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def run_check(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["check-doc-links.py", *map(str, args)]):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = checker.main()
        return status, stdout.getvalue(), stderr.getvalue()

    def test_github_heading_punctuation_preserves_separate_spaces(self):
        path = self.write("record.md", "# Saved settings — today\n\n# Saved settings — today\n")
        self.write("README.md", "[First](record.md#saved-settings--today)\n"
                   "[Second](record.md#saved-settings--today-1)\n")
        self.assertEqual(checker.document_anchors(path),
                         {"saved-settings--today", "saved-settings--today-1"})
        self.assertEqual(self.run_check("--root", self.root)[0], 0)

    def test_generator_templates_are_not_checked_as_finished_pages(self):
        self.write("scripts/templates/manual.html", '<a href="@@PAGE_URL@@">Page</a>')
        self.write("scripts/observer-hourly-viewer.html", '<script src="frames.js"></script>')
        self.write("README.md", "# Sources\n")
        self.assertEqual(checker.repository_files(self.root), [Path("README.md")])
        self.assertEqual(self.run_check("--root", self.root)[0], 0)

    def test_missing_documentation_and_assets_still_fail(self):
        self.write("README.md", "[Missing guide](docs/missing.md)\n![Missing preview](preview.png)\n")
        status, _, errors = self.run_check("--root", self.root)
        self.assertEqual(status, 1)
        self.assertIn("missing local target: docs/missing.md", errors)
        self.assertIn("missing local target: preview.png", errors)

    def test_public_page_cannot_link_to_an_unpublished_template(self):
        self.write("README.md", "[Template](scripts/templates/manual.html)\n")
        self.write("scripts/templates/manual.html", "<h1>Template</h1>")
        status, _, errors = self.run_check("--root", self.root)
        self.assertEqual(status, 1)
        self.assertIn("not published", errors)

    def test_rendered_site_still_checks_generated_asset_links(self):
        self.write("site/index.html", '<a href="output/book.pdf">Book</a>')
        status, _, errors = self.run_check("--walk", self.root / "site")
        self.assertEqual(status, 1)
        self.assertIn("missing local target: output/book.pdf", errors)
        self.write("site/output/book.pdf", "fixture")
        self.assertEqual(self.run_check("--walk", self.root / "site")[0], 0)

    def test_template_exclusions_match_jekyll_configuration(self):
        config = (ROOT / "_config.yml").read_text()
        for path in checker.TEMPLATE_PATHS:
            with self.subTest(path=str(path)):
                self.assertIn("  - " + str(path) + "\n", config)


if __name__ == "__main__":
    unittest.main()
