#!/usr/bin/env python3
"""Reject missing raster layers even when Inkscape reports exit status zero."""
import importlib
from contextlib import redirect_stderr
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
exporter = importlib.import_module('export-setouchi-sheets')


class ExportResult(unittest.TestCase):
    def run_result(self, output, code=0):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'export.log'
            result = subprocess.CompletedProcess(['inkscape'], code, output)
            with patch.object(exporter.subprocess, 'run', return_value=result), path.open('w') as log:
                exporter.run_export_command(['inkscape'], os.environ, log)
            return path.read_text()

    def test_decoder_errors_fail_even_with_zero_exit(self):
        for message in ('Pixbuf::create_from_file: failed to decode layer.png',
                        'D-Bus error: I/O error: Operation not permitted'):
            with self.subTest(message=message), self.assertRaisesRegex(RuntimeError, 'linked image layers'):
                self.run_result(message)

    def test_unrelated_warnings_are_retained_without_rejecting_export(self):
        output = 'WARNING: Failed to wrap object of type PangoFT2FontMap\n'
        self.assertEqual(self.run_result(output), output)

    def test_nonzero_exit_still_fails(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_result('render failed', 2)

    def test_private_values_are_redacted_from_export_log(self):
        with patch.dict(os.environ, {'FIRMS_MAP_KEY': 'fixture-private-value'}):
            self.assertEqual(self.run_result('fixture-private-value'), '[REDACTED]')


class SheetMargins(unittest.TestCase):
    def boxes(self, declaration=''):
        with tempfile.TemporaryDirectory() as directory:
            svg=Path(directory)/'sheet.svg'
            svg.write_text('<svg width="44in" height="19.052559in" '+declaration+'/>')
            return exporter.margin_boxes(svg,(13200,5716))

    def test_legacy_margin_bands_are_preserved(self):
        self.assertEqual(self.boxes(),[(0,0,74,5716),(13126,0,13200,5716),
                                      (0,0,13200,31),(0,5685,13200,5716)])

    def test_declared_all_sky_margin_excludes_valid_frame_glyphs(self):
        boxes=self.boxes('data-frame-side-margin-inches="0.1515254408298148"')
        image=Image.new('RGB',(13200,5716),'white')
        ImageDraw.Draw(image).rectangle((45,535,80,609),fill='black')
        self.assertEqual(boxes[0],(0,0,44,5716))
        for box in boxes:
            self.assertEqual(image.crop(box).getextrema(),((255,255),)*3)
        image.putpixel((43,550),(0,0,0))
        self.assertNotEqual(image.crop(boxes[0]).getextrema(),((255,255),)*3)

    def test_invalid_declared_margins_fail(self):
        for value in ('nan','inf','-1','0','0.001','22','not-a-number'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.boxes('data-frame-side-margin-inches="'+value+'"')


class ExportQueue(unittest.TestCase):
    def records(self):
        return [{'kind':'map','scope':'world','stem':str(i)} for i in range(10)]

    def test_failure_reports_sheet_and_does_not_start_remaining_queue(self):
        started=[]
        def fail(record):
            started.append(record['stem'])
            raise RuntimeError('fixture export failure')
        log=io.StringIO()
        with redirect_stderr(log), self.assertRaisesRegex(RuntimeError,'fixture export failure'):
            exporter.export_records(self.records(),fail,1)
        self.assertEqual(started,['0'])
        self.assertIn('Export failed: map-world-0',log.getvalue())

    def test_success_returns_every_sheet(self):
        records=self.records()
        result=exporter.export_records(records,lambda record:record,2)
        self.assertEqual(sorted(r['stem'] for r in result),sorted(r['stem'] for r in records))


if __name__ == '__main__':
    unittest.main()
