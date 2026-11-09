#!/usr/bin/env python3
"""Exercise the real fetch wrapper with small offline provider responses."""
from datetime import date
import gzip
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class Fetch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'data'
        raw = self.data / '.raw/2026/firms'
        raw.mkdir(parents=True)
        (raw / 'stale-VIIRS_SNPP_SP.csv').write_text('old sensor selection\n')
        (raw.parent / 'SHA256SUMS').write_text('previous manifest\n')
        profile = json.loads((ROOT / 'assets.static/anthropocene/anthropocene-particulate-2026-profile.json').read_text())
        profile['snapshot'].update(as_of_utc='2026-01-11T00:00:00Z', data_through='2026-01-10')
        self.profile = self.root / 'profile.json'
        self.profile.write_text(json.dumps(profile, indent=2)+'\n')
        fixtures = self.root / 'fixtures'
        fixtures.mkdir()
        with tarfile.open(fixtures / 'ghcn.tar.gz', 'w:gz') as archive:
            item = tarfile.TarInfo('station.dly')
            item.size = 1
            archive.addfile(item, io.BytesIO(b'\n'))
        for name in ('epa.zip', 'hms.zip'):
            with zipfile.ZipFile(fixtures/name, 'w') as archive:
                archive.writestr('fixture.csv', 'fixture\n')
        (fixtures/'storm.csv.gz').write_bytes(gzip.compress(b'fixture\n'))
        fake = self.root/'curl'
        fake.write_text('#!'+sys.executable+'\n'+r'''
import datetime,json,os,pathlib,shutil,sys
args=sys.argv[1:];url=next(a for a in args if a.startswith('https://'))
output=pathlib.Path(args[args.index('-o')+1]);fixtures=pathlib.Path(os.environ['FIRMS_TEST_FIXTURES'])
if '/api/area/' in url:
    parts=url.split('/');source,days,start=parts[-4],int(parts[-2]),datetime.date.fromisoformat(parts[-1])
    with open(os.environ['FIRMS_TEST_REQUESTS'],'a') as log:log.write(source+' '+str(start)+' '+str(days)+'\n')
    if os.environ.get('FIRMS_TEST_FAIL')=='1':
        print('fixture provider HTTP 503',file=sys.stderr);sys.exit(22)
    output.write_text('latitude,longitude,acq_date\n'+''.join('40,-100,'+str(start+datetime.timedelta(days=i))+'\n' for i in range(days)))
elif '/api/data_availability/' in url:
    output.write_text('data_id,min_date,max_date\n'+''.join(source+',2026-01-01,2026-01-05\n'+source.replace('_SP','_NRT')+',2026-01-04,2026-01-10\n' for source in ('VIIRS_NOAA20_SP','VIIRS_SNPP_SP')))
elif url.endswith('ghcnd_gsn.tar.gz'):shutil.copyfile(fixtures/'ghcn.tar.gz',output)
elif url.endswith('ghcnd-stations.txt'):output.write_text('fixture inventory\n')
elif '/daily_88101_' in url:shutil.copyfile(fixtures/'epa.zip',output)
elif '/hms_smoke' in url:shutil.copyfile(fixtures/'hms.zip',output)
elif url.endswith('/csvfiles/'):
    output.write_text('StormEvents_details-ftp_v1.0_d2026_c20260111.csv.gz\nStormEvents_locations-ftp_v1.0_d2026_c20260111.csv.gz\n')
elif 'StormEvents_' in url:shutil.copyfile(fixtures/'storm.csv.gz',output)
elif '/hotspots/' in url:
    output.write_text('lat,lon,rep_date,source\n40,-100,2026-01-01,fixture\n');print('200',end='')
else:raise RuntimeError('Unexpected fixture URL')
''')
        fake.chmod(0o755)
        self.log = self.root/'requests'
        self.env = {**os.environ, 'PATH':str(self.root)+os.pathsep+os.environ['PATH'],
                    'FIRMS_MAP_KEY':'fixture-key-never-log',
                    'ANTHROPOCENE_FIRMS_DELAY_SECONDS':'0',
                    'FIRMS_TEST_FIXTURES':str(fixtures), 'FIRMS_TEST_REQUESTS':str(self.log),
                    'FIRMS_TEST_FAIL':'0'}
        for name in ('DATA_HTTP_CACHE', 'ANTHROPOCENE_FIRMS_SOURCES', 'CWFIS_ARCHIVE_CACHE'):
            self.env.pop(name, None)

    def run_fetch(self, **env):
        return subprocess.run(['bash',str(ROOT/'scripts/fetch-anthropocene-particulate-data.sh'),str(self.data),str(self.profile)],
                              cwd=ROOT,env={**self.env,**env},text=True,capture_output=True,timeout=30)

    def test_supported_default_replaces_old_sensor_and_names_chunks_by_date(self):
        result = self.run_fetch()
        self.assertEqual(result.returncode,0,result.stderr)
        requests = self.log.read_text().splitlines()
        self.assertEqual(requests, ['VIIRS_NOAA20_SP 2026-01-01 5',
                                    'VIIRS_NOAA20_NRT 2026-01-04 5',
                                    'VIIRS_NOAA20_NRT 2026-01-09 2'])
        names = {p.name for p in (self.data/'.raw/2026/firms').glob('*.csv')}
        self.assertEqual(names, {'000-VIIRS_NOAA20_SP-2026-01-01.csv',
                                '000-VIIRS_NOAA20_NRT-2026-01-04.csv',
                                '001-VIIRS_NOAA20_NRT-2026-01-09.csv'})
        self.assertNotIn(self.env['FIRMS_MAP_KEY'],result.stdout+result.stderr)
        subprocess.run(['sha256sum','--check',str(self.data/'.raw/2026/SHA256SUMS')],check=True,stdout=subprocess.DEVNULL)

    def test_explicit_historical_sensor_override_is_preserved(self):
        result = self.run_fetch(ANTHROPOCENE_FIRMS_SOURCES='VIIRS_SNPP_SP VIIRS_SNPP_NRT')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(all(row.startswith('VIIRS_SNPP_') for row in self.log.read_text().splitlines()))
        self.assertFalse((self.data/'.raw/2026/firms/stale-VIIRS_SNPP_SP.csv').exists())

    def test_failed_acquisition_preserves_previous_staging(self):
        result = self.run_fetch(FIRMS_TEST_FAIL='1')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((self.data/'.raw/2026/firms/stale-VIIRS_SNPP_SP.csv').read_text(),'old sensor selection\n')
        self.assertEqual((self.data/'.raw/2026/SHA256SUMS').read_text(),'previous manifest\n')
        self.assertNotIn(self.env['FIRMS_MAP_KEY'],result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main()
