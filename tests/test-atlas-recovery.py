#!/usr/bin/env python3
"""Exercise native recovery, retained failures and stable publication receipts."""
from contextlib import redirect_stdout
import importlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import dataset
atlas = importlib.import_module('atlas-optional')


class Recovery(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.builds = self.root/'builds'
        self.old = self.builds/'old'
        self.new = self.builds/'new'
        self.input = self.root/'dataset.json'
        self.input.write_text('{"dataset_id":"fixture"}\n')
        self.producer = self.root/'src.generate/generate-earth.cc'
        self.producer.parent.mkdir(parents=True)
        self.producer.write_text('unchanged native producer')
        (self.root/'Makefile').write_text('unchanged native graph')
        self.identity = {'revision': 'a'*40, 'dirty': False,
                         'files': {name: dataset.digest(self.root/name)
                                   for name in ['Makefile', 'src.generate/generate-earth.cc']}}
        self.state = {'build_id': 'old', 'dataset_id': 'fixture', 'status': 'failed',
                      'manifest_sha256': dataset.digest(self.input), 'implementation': self.identity}
        dataset.atomic_json(self.old/'validation/build-state.json', self.state)
        self.native = self.old/'native/authagraph/pdf/earth.pdf'
        self.native.parent.mkdir(parents=True)
        self.native.write_bytes(b'completed native PDF fixture')
        self.root_patch = patch.object(atlas, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def recover(self):
        with redirect_stdout(io.StringIO()):
            return atlas.reuse_native('old', self.new, self.input, {'dataset_id': 'fixture'}, self.identity)

    def test_recovery_preserves_failed_evidence_and_copies_independent_bytes(self):
        before = (self.old/'validation/build-state.json').read_bytes()
        receipt = self.recover()
        target = self.new/'native/authagraph/pdf/earth.pdf'
        self.assertEqual(target.read_bytes(), self.native.read_bytes())
        self.assertNotEqual(target.stat().st_ino, self.native.stat().st_ino)
        self.assertEqual((self.old/'validation/build-state.json').read_bytes(), before)
        saved = json.loads((self.new/receipt['receipt']).read_text())
        self.assertEqual(saved['source_build_id'], 'old')
        self.assertEqual(saved['files'][0]['sha256'], dataset.digest(target))
        self.assertEqual(dataset.digest(self.new/receipt['receipt']), receipt['sha256'])
        target.write_bytes(b'new run can change its copy')
        self.assertEqual(self.native.read_bytes(), b'completed native PDF fixture')

    def test_changed_dataset_is_rejected(self):
        self.input.write_text('different data selection')
        with self.assertRaisesRegex(dataset.DatasetError, 'exact selected dataset'):
            self.recover()

    def test_changed_native_producer_is_rejected(self):
        self.identity = {**self.identity, 'files': {**self.identity['files'], 'src.generate/generate-earth.cc': '0'*64}}
        with self.assertRaisesRegex(dataset.DatasetError, 'unchanged producer bytes'):
            self.recover()

    def test_post_native_coordinator_change_is_explicitly_recorded(self):
        updated = {**self.identity, 'files': {**self.identity['files'], 'scripts/atlas-optional.py': 'b'*64}}
        result = atlas.native_reuse_methods(self.identity, updated)
        self.assertEqual(result['allowed_post_native_or_independent_changes'], ['scripts/atlas-optional.py'])
        self.assertEqual(result['verified_producer_files'], self.identity['files'])

    def test_post_native_h3_presentation_change_is_explicitly_recorded(self):
        for name in ('scripts/setouchi_h3_trials.py', 'scripts/export-setouchi-sheets.py',
                     'scripts/build-current-atlas.py', 'scripts/prepare-marine-heatwaves.py',
                     'scripts/build-ocean-temperature-plates.py', 'scripts/build-ocean-stage-2-plates.py',
                     'scripts/optional_map_annotations.py', 'scripts/validate-ocean-products.py',
                     'scripts/validate-ocean-stage-2.py'):
            with self.subTest(name=name):
                updated = {**self.identity, 'files': {**self.identity['files'], name: 'b'*64}}
                result = atlas.native_reuse_methods(self.identity, updated)
                self.assertEqual(result['allowed_post_native_or_independent_changes'], [name])
                self.assertEqual(result['verified_producer_files'], self.identity['files'])

    def test_unrecorded_method_cannot_be_assumed_compatible(self):
        updated = {**self.identity, 'files': {**self.identity['files'], 'scripts/new-renderer.mjs': 'b'*64}}
        with patch.object(atlas.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, b'', b'')):
            with self.assertRaisesRegex(dataset.DatasetError, 'cannot be verified'):
                atlas.native_reuse_methods(self.identity, updated)

    def test_symlinked_outputs_are_rejected(self):
        (self.native.parent/'outside.pdf').symlink_to(self.input)
        with self.assertRaisesRegex(dataset.DatasetError, 'symlinked outputs'):
            self.recover()

    def test_mutation_during_copy_is_rejected(self):
        original_copy = shutil.copy2
        def mutate(source, target):
            original_copy(source, target)
            Path(source).write_bytes(b'changed during recovery')
        with patch.object(atlas.shutil, 'copy2', side_effect=mutate):
            with self.assertRaisesRegex(dataset.DatasetError, 'changed while recovering'):
                self.recover()

    def test_recovery_never_reuses_screen_outputs(self):
        screen = self.old/'native/authagraph/screen-1080p/earth.png'
        screen.parent.mkdir(parents=True)
        screen.write_bytes(b'outdated screen presentation')
        self.recover()
        self.assertFalse((self.new/'native/authagraph/screen-1080p/earth.png').exists())

    def test_final_receipt_excludes_mutable_state_and_itself(self):
        for name in ['validation/build-state.json', 'validation/full-build.json', 'validation/reused-native.json',
                     'native/earth.svg.gz', 'native/earth.webp', 'logs/001-make.log']:
            path = self.new/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture')
        actual = {str(p.relative_to(self.new)) for p in atlas.build_artifacts(self.new)}
        self.assertEqual(actual, {'validation/reused-native.json', 'native/earth.svg.gz', 'native/earth.webp'})

    def test_failing_child_keeps_redacted_log_and_exit_status(self):
        state = {'status': 'building', 'commands': []}
        path = self.new/'validation/build-state.json'
        with patch.object(atlas, 'ACTIVE_STATE', state), patch.object(atlas, 'ACTIVE_STATE_PATH', path), \
             patch.dict(os.environ, {'FIRMS_MAP_KEY': 'fixture-private-value'}), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(dataset.DatasetError, 'exit status 7'):
                atlas.run([sys.executable, '-c', 'print("fixture-private-value"); raise SystemExit(7)'])
        saved = json.loads(path.read_text())
        command = saved['commands'][0]
        self.assertEqual(command['returncode'], 7)
        self.assertEqual(command['status'], 'failed')
        log = (self.new/command['log']).read_text()
        self.assertIn('[REDACTED]', log)
        self.assertNotIn('fixture-private-value', log)


if __name__ == '__main__':
    unittest.main()
