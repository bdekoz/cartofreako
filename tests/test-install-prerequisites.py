#!/usr/bin/env python3
"""Exercise dependency installation without touching the host or network."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
import json, os, pathlib, subprocess, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['INSTALL_TEST_LOG'], 'a') as log:
    log.write(json.dumps([name, *args]) + '\n')
missing = os.environ.get('MISSING_PACKAGES', '').split()
if name == 'uname': print(os.environ.get('TEST_KERNEL', 'Linux'))
elif name == 'id': print(os.environ.get('TEST_UID', '1000'))
elif name == 'rpm': sys.exit(int(args[-1] in missing))
elif name == 'dpkg-query':
    if args[-1] in missing: sys.exit(1)
    print('install ok installed', end='')
elif name == 'sudo': sys.exit(subprocess.run(args).returncode)
elif name in ('dnf', 'apt-get'):
    sys.exit(int(os.environ.get('INSTALL_TEST_STATUS', '0')))
elif name == 'brew':
    if args[0] == 'list': sys.exit(int(args[-1] in missing))
    elif args[0] == '--prefix': print(os.environ['INSTALL_TEST_PREFIX'])
    elif args[0] == 'install': sys.exit(int(os.environ.get('INSTALL_TEST_STATUS', '0')))
elif name == 'fc-match': print(os.environ.get('TEST_FONT', 'Atkinson Hyperlegible'), end='')
elif name == 'fc-scan': print(os.environ.get('TEST_SCAN_FONT', 'Atkinson Hyperlegible'), end='')
elif name == 'curl': pathlib.Path(args[args.index('--output') + 1]).write_text('fixture')
elif name == 'git' and args[0] == 'clone': pathlib.Path(args[-1]).mkdir(parents=True)
elif name == 'check-prerequisites.sh': sys.exit(int(os.environ.get('CHECK_TEST_STATUS', '0')))
'''


class Installer(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        scripts = self.folder / 'repo/scripts'
        scripts.mkdir(parents=True)
        self.installer = scripts / 'install-prerequisites.sh'
        shutil.copy(ROOT / 'scripts/install-prerequisites.sh', self.installer)
        self.bin = self.folder / 'bin'
        self.bin.mkdir()
        for name in ('uname', 'id', 'rpm', 'dpkg-query', 'sudo', 'dnf', 'apt-get',
                     'brew', 'xcode-select', 'fc-match', 'fc-scan', 'fc-cache', 'curl', 'git'):
            self.write_mock(self.bin / name)
        self.write_mock(scripts / 'check-prerequisites.sh')
        self.log = self.folder / 'calls.jsonl'
        self.os_release = self.folder / 'os-release'
        self.os_release.write_text('ID=fedora\n')
        self.env = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'],
                    'PREREQUISITE_OS_RELEASE': str(self.os_release),
                    'INSTALL_TEST_LOG': str(self.log), 'INSTALL_TEST_PREFIX': str(self.folder),
                    'XDG_DATA_HOME': str(self.folder / 'data'),
                    'LABEL_FONT': 'atkinson_hyperlegible', 'MISSING_PACKAGES': '',
                    'TEST_KERNEL': 'Linux', 'TEST_UID': '1000',
                    'TEST_FONT': 'Atkinson Hyperlegible', 'TEST_SCAN_FONT': 'Atkinson Hyperlegible',
                    'INSTALL_TEST_STATUS': '0', 'CHECK_TEST_STATUS': '0',
                    'ALPHA60_SRC': str(self.folder / 'alpha60/src'),
                    'IZZI_SRC': str(self.folder / 'izzi/src'),
                    'NETWORK_INFRASTRUCTURE_CLOUD_SOURCE': str(self.folder / 'cloud'),
                    'SUBMARINE_CABLE_SOURCE': str(self.folder / 'cables')}
        for name in ('alpha60', 'izzi', 'cloud', 'cables'):
            directory = self.folder / name
            directory.mkdir()
            (directory / 'keep').write_text('existing checkout')

    def write_mock(self, path):
        path.write_text('#!' + sys.executable + '\n' + MOCK)
        path.chmod(0o755)

    def run_installer(self, *args, **env):
        return subprocess.run(['sh', str(self.installer), *args],
                              env={**self.env, **env}, text=True, capture_output=True)

    def calls(self, *names):
        rows = [json.loads(line) for line in self.log.read_text().splitlines()]
        return [row for row in rows if row[0] in names]

    def test_fedora_installs_only_missing_packages_then_checks(self):
        result = self.run_installer(MISSING_PACKAGES='ripgrep h3-devel')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('sudo'), [['sudo', 'dnf', 'install', '-y', 'ripgrep', 'h3-devel']])
        self.assertEqual(self.calls('dnf'), [['dnf', 'install', '-y', 'ripgrep', 'h3-devel']])
        self.assertEqual(len(self.calls('check-prerequisites.sh')), 1)
        self.assertEqual(self.calls('git', 'curl'), [])

    def test_no_missing_packages_does_not_require_sudo(self):
        (self.bin / 'sudo').unlink()
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('dnf', 'apt-get', 'brew', 'git', 'curl'), [])
        self.assertEqual(len(self.calls('check-prerequisites.sh')), 1)

    def test_debian_checks_installation_status_and_runs_as_root(self):
        self.os_release.write_text('ID=ubuntu\nID_LIKE=debian\n')
        result = self.run_installer(MISSING_PACKAGES='ripgrep rapidjson-dev', TEST_UID='0')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls('apt-get'), [
            ['apt-get', 'update'], ['apt-get', 'install', '-y', 'ripgrep', 'rapidjson-dev']])
        self.assertEqual(self.calls('sudo'), [])

    def test_installation_failure_stops_before_checking_or_cloning(self):
        result = self.run_installer(MISSING_PACKAGES='ripgrep', INSTALL_TEST_STATUS='23')
        self.assertEqual(result.returncode, 23)
        self.assertEqual(self.calls('git', 'curl', 'check-prerequisites.sh'), [])

    def test_dry_run_performs_no_installation_or_check(self):
        shutil.rmtree(self.folder / 'alpha60')
        result = self.run_installer('--dry-run', MISSING_PACKAGES='ripgrep', TEST_FONT='fallback')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('sudo dnf install -y ripgrep', result.stdout)
        self.assertIn('git clone', result.stdout)
        self.assertIn('Atkinson Hyperlegible fonts', result.stdout)
        self.assertEqual(self.calls('sudo', 'dnf', 'git', 'curl', 'check-prerequisites.sh'), [])
        self.assertFalse((self.folder / 'alpha60').exists())
        self.assertFalse((self.folder / 'data').exists())

    def test_macos_installs_missing_formulae_and_casks_without_sudo(self):
        result = self.run_installer(TEST_KERNEL='Darwin', MISSING_PACKAGES='ripgrep inkscape')
        self.assertEqual(result.returncode, 0, result.stderr)
        installs = [row for row in self.calls('brew') if row[1] == 'install']
        self.assertEqual(installs, [['brew', 'install', 'ripgrep'], ['brew', 'install', '--cask', 'inkscape']])
        self.assertEqual(self.calls('sudo'), [])

    def test_only_missing_repositories_are_cloned_and_cloud_is_pinned(self):
        shutil.rmtree(self.folder / 'cloud')
        shutil.rmtree(self.folder / 'izzi')
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls('git')
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0], ['git', 'clone', 'https://github.com/bdekoz/izzi.git', str(self.folder / 'izzi')])
        self.assertEqual(calls[-1], ['git', '-C', str(self.folder / 'cloud'), 'checkout',
                                   '1be1eb04e73320e0337a74a99686cd532f09ad9b'])
        self.assertEqual((self.folder / 'alpha60/keep').read_text(), 'existing checkout')

    def test_missing_original_font_is_installed_with_license(self):
        result = self.run_installer(TEST_FONT='fallback')
        self.assertEqual(result.returncode, 0, result.stderr)
        fonts = self.folder / 'data/fonts/AtkinsonHyperlegible'
        self.assertEqual(len(list(fonts.glob('*.ttf'))), 4)
        self.assertTrue((fonts / 'OFL.txt').exists())
        self.assertEqual(len(self.calls('fc-cache')), 1)

    def test_invalid_font_does_not_install_or_report_success(self):
        result = self.run_installer(TEST_FONT='fallback', TEST_SCAN_FONT='Wrong font')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.folder / 'data').exists())
        self.assertEqual(self.calls('check-prerequisites.sh'), [])

    def test_checker_failure_is_returned(self):
        result = self.run_installer(CHECK_TEST_STATUS='9')
        self.assertEqual(result.returncode, 9)

    def test_unsupported_distribution_does_not_mutate_anything(self):
        self.os_release.write_text('ID=unsupported\n')
        result = self.run_installer()
        self.assertEqual(result.returncode, 2)
        self.assertIn('Unsupported distribution', result.stderr)
        self.assertEqual(self.calls('sudo', 'dnf', 'git', 'curl'), [])

    def test_only_plural_make_targets_are_available(self):
        result = subprocess.run(['make', '--no-print-directory', '-s', 'list-targets'],
                                cwd=ROOT, text=True, capture_output=True, check=True)
        names = result.stdout.splitlines()
        self.assertIn('check-prerequisites', names)
        self.assertIn('install-prerequisites', names)
        for name in ('check-prerequisite', 'install-prerequisite'):
            self.assertNotIn(name, names)
            result = subprocess.run(['make', '--no-print-directory', '-n', name],
                                    cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('No rule to make target', result.stderr)


if __name__ == '__main__':
    unittest.main()
