#!/usr/bin/env python3
"""Check aggregate ordering and failure propagation without fetching data."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [
    'fetch-natural-earth-10m', 'install-jaxa-certificate',
    'fetch-astro-data', 'fetch-orbiting-data',
    'fetch-atoll-evidence-data', 'prepare-atoll-evidence-data',
    'fetch-cloud-atmosphere-data', 'prepare-cloud-atmosphere-data',
    'fetch-anthropocene-data', 'prepare-anthropocene-data',
    'fetch-anthropocene-cpc-data', 'prepare-anthropocene-temperature-data',
    'refresh-resources-data', 'refresh-network-fiber', 'prepare-network-swarm-data',
    'fetch-ocean-stage-2', 'verify-cloud-atmosphere-data',
]


class DataUpdate(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.log = self.folder / 'steps'
        self.record = self.folder / 'record.py'
        self.record.write_text('''import os, pathlib, sys, time
with pathlib.Path(os.environ['DATA_UPDATE_TEST_LOG']).open('a') as log:
    log.write(sys.argv[1] + "\\n")
time.sleep(0.02)
sys.exit(23 if sys.argv[1] == os.environ.get('DATA_UPDATE_TEST_FAIL') else 0)
''')
        fixture = self.folder / 'sources.mk'
        fixture.write_text('.PHONY: ' + ' '.join(EXPECTED) + '\n' + '\n'.join(
            f'{target}:\n\t@"{sys.executable}" "{self.record}" $@' for target in EXPECTED
        ) + '''
prepare-atoll-evidence-data: fetch-atoll-evidence-data
prepare-cloud-atmosphere-data: fetch-cloud-atmosphere-data
verify-cloud-atmosphere-data: prepare-cloud-atmosphere-data
''')
        # The real top-level Makefile calls this wrapper as its submake.
        # Only the child source recipes are replaced; its flags and target
        # selection come directly from the real data-update recipe.
        self.wrapper = self.folder / 'make-sources'
        self.wrapper.write_text('#!' + sys.executable + '\n' + '''import os, sys
os.execvp('make', ['make', '-f', os.environ['DATA_UPDATE_TEST_MAKEFILE'], *sys.argv[1:]])
''')
        self.wrapper.chmod(0o755)
        self.env = {**os.environ, 'DATA_UPDATE_TEST_LOG': str(self.log),
                    'DATA_UPDATE_TEST_MAKEFILE': str(fixture), 'DATA_UPDATE_TEST_FAIL': '',
                    'MAKEFLAGS': '', 'MFLAGS': '', 'MAKEOVERRIDES': ''}

    def run_update(self, *flags, failure=''):
        return subprocess.run(['make', '--no-print-directory', *flags,
                               f'MAKE={self.wrapper}', 'data-update'], cwd=ROOT,
                              env={**self.env, 'DATA_UPDATE_TEST_FAIL': failure},
                              text=True, capture_output=True, timeout=30)

    def test_all_source_steps_run_once_in_order_under_parallel_make(self):
        result = self.run_update('-j8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), EXPECTED)
        self.assertIn('Completed every configured data refresh', result.stdout)

    def test_fetch_failure_stops_preparation_and_reports_failure_under_keep_going(self):
        failed = 'fetch-anthropocene-cpc-data'
        result = self.run_update('-j8', '-k', failure=failed)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.log.read_text().splitlines(), EXPECTED[:EXPECTED.index(failed) + 1])
        self.assertNotIn('Completed every configured data refresh', result.stdout)

    def test_shared_experiment_sources_remain_in_the_existing_aggregate(self):
        # Appending a reporting target reads the real Make variable and keeps
        # this test independent of line wrapping and recipe formatting.
        report = self.folder / 'report.mk'
        report.write_text('report-data-update:\n\t@printf "%s\\n" $(EXPERIMENT_DATA_FETCH_TARGETS)\n')
        result = subprocess.run(['make', '--no-print-directory', '-s', '-f', 'Makefile',
                                 '-f', str(report), 'report-data-update'], cwd=ROOT,
                                env=self.env, text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout.splitlines(), EXPECTED[:8])
        database = subprocess.run(['make', '--no-print-directory', '-np', '-f', 'Makefile',
                                   '-f', str(report), 'report-data-update'], cwd=ROOT,
                                  env=self.env, text=True, capture_output=True, check=True)
        rule = re.search(r'^all-experiments-fetch: (.*)$', database.stdout, re.MULTILINE)
        self.assertIsNotNone(rule)
        self.assertEqual(rule.group(1).split(), ['clean', *EXPECTED[:8]])

    def test_public_target_registry_contains_data_update(self):
        result = subprocess.run(['make', '--no-print-directory', '-s', 'list-targets'],
                                cwd=ROOT, env=self.env, text=True, capture_output=True, check=True)
        self.assertIn('data-update', result.stdout.splitlines())


if __name__ == '__main__':
    unittest.main()
