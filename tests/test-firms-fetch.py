#!/usr/bin/env python3
"""Exercise the real fetch wrapper with small offline provider responses."""
from datetime import date, timedelta
import gzip
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import threading
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

    def cached_provider(self, year=2026):
        self.provider_calls = []
        self.nrt_end = 10
        fixtures = self.root/'fixtures'
        annual = self.root/'annual.zip'
        with zipfile.ZipFile(annual, 'w') as archive:
            archive.writestr(f'{year}_hotspots.csv', 'lat,lon,rep_date,source\n40,-100,2025-01-01,fixture\n')
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_GET(self):
                owner.provider_calls.append(self.path)
                if '/api/area/' in self.path:
                    parts=self.path.split('/')
                    start=date.fromisoformat(parts[-1]);days=int(parts[-2])
                    body=('latitude,longitude,acq_date\n'+''.join(
                        '40,-100,'+str(start+timedelta(days=n))+'\n' for n in range(days))).encode()
                elif '/api/data_availability/' in self.path:
                    body=(f'data_id,min_date,max_date\nVIIRS_NOAA20_SP,{year}-01-01,{year}-01-05\n'
                          f'VIIRS_NOAA20_NRT,{year}-01-04,{year}-01-{owner.nrt_end:02d}\n').encode()
                elif self.path.endswith('ghcnd_gsn.tar.gz'):body=(fixtures/'ghcn.tar.gz').read_bytes()
                elif self.path.endswith('ghcnd-stations.txt'):body=b'fixture inventory\n'
                elif '/daily_88101_' in self.path:body=(fixtures/'epa.zip').read_bytes()
                elif '/hms_smoke' in self.path:body=(fixtures/'hms.zip').read_bytes()
                elif self.path.endswith('/csvfiles/'):
                    body=(f'StormEvents_details-ftp_v1.0_d{year}_c20260111.csv.gz\n'
                          f'StormEvents_locations-ftp_v1.0_d{year}_c20260111.csv.gz\n').encode()
                elif 'StormEvents_' in self.path:body=(fixtures/'storm.csv.gz').read_bytes()
                elif '/hotspots/archive/' in self.path:body=annual.read_bytes()
                elif '/hotspots/' in self.path:body=b'lat,lon,rep_date,source\n40,-100,2026-01-01,fixture\n'
                else:
                    self.send_error(500);return
                etag='"'+hashlib.sha256(body).hexdigest()+'"'
                self.send_response(304 if self.headers.get('If-None-Match')==etag else 200)
                self.send_header('ETag',etag)
                self.send_header('Content-Length',str(len(body)))
                self.end_headers()
                if self.headers.get('If-None-Match')!=etag:self.wfile.write(body)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.addCleanup(server.server_close)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        self.addCleanup(server.shutdown)
        hook=self.root/'http-fixture'
        hook.mkdir()
        (hook/'sitecustomize.py').write_text('''import urllib.request,urllib.parse,os
original=urllib.request.urlopen
def local(request,*args,**kwargs):
    parsed=urllib.parse.urlsplit(request.full_url)
    request=urllib.request.Request(os.environ['PARTICULATE_HTTP_FIXTURE']+parsed.path,
        data=request.data,headers=dict(request.header_items()),method=request.get_method())
    return original(request,*args,**kwargs)
urllib.request.urlopen=local
''')
        return {'DATA_HTTP_CACHE':str(self.root/'cache'), 'PARTICULATE_REUSE_FROM':str(self.root/'no-prior-inputs'),
                'PARTICULATE_HTTP_FIXTURE':f'http://127.0.0.1:{server.server_port}', 'PYTHONPATH':str(hook),
                'DATA_UPDATE_RUN_ID':'first-run','PARTICULATE_REFRESH':'0'}

    def age_receipts(self):
        for path in (self.root/'cache/http').glob('*.json'):
            value=json.loads(path.read_text())
            value['checked_at']='2026-01-01T00:00:00Z'
            path.write_text(json.dumps(value))

    def test_cached_full_fetch_only_requests_missing_new_days_after_short_tail(self):
        env=self.cached_provider()
        first=self.run_fetch(**env)
        self.assertEqual(first.returncode,0,first.stderr)
        self.age_receipts()
        self.provider_calls.clear()
        self.nrt_end=12
        profile=json.loads(self.profile.read_text())
        profile['snapshot'].update(as_of_utc='2026-01-13T00:00:00Z',data_through='2026-01-12')
        self.profile.write_text(json.dumps(profile,indent=2))
        second=self.run_fetch(**{**env,'DATA_UPDATE_RUN_ID':'second-run'})
        self.assertEqual(second.returncode,0,second.stderr)
        firms=[p for p in self.provider_calls if '/api/area/' in p]
        self.assertEqual(len(firms),1,firms)
        self.assertTrue(firms[0].endswith('/VIIRS_NOAA20_NRT/world/2/2026-01-11'),firms)
        cwfis=[p for p in self.provider_calls if '/hotspots/' in p]
        self.assertEqual(cwfis,['/downloads/hotspots/20260111.csv','/downloads/hotspots/20260112.csv'])
        self.assertNotIn(self.env['FIRMS_MAP_KEY'],second.stdout+second.stderr)
        names={p.name for p in (self.data/'.raw/2026/firms').glob('*.csv')}
        self.assertIn('001-VIIRS_NOAA20_NRT-2026-01-09.csv',names)
        self.assertIn('002-VIIRS_NOAA20_NRT-2026-01-11.csv',names)
        self.assertIn('completed-period',second.stderr)

    def test_closed_year_never_repeats_archives_or_firms_in_a_new_run(self):
        env=self.cached_provider(2025)
        profile=json.loads(self.profile.read_text())
        profile['duration']['year']=2025
        profile['snapshot'].update(as_of_utc='2026-01-11T00:00:00Z',data_through='2025-01-10')
        self.profile.write_text(json.dumps(profile,indent=2))
        first=self.run_fetch(**env)
        self.assertEqual(first.returncode,0,first.stderr)
        self.age_receipts()
        self.provider_calls.clear()
        second=self.run_fetch(**{**env,'DATA_UPDATE_RUN_ID':'second-run'})
        self.assertEqual(second.returncode,0,second.stderr)
        self.assertFalse(any('/api/area/' in p or '/hotspots/' in p or '2025.zip' in p
                             or 'StormEvents_' in p for p in self.provider_calls),self.provider_calls)
        self.provider_calls.clear()
        forced=self.run_fetch(**{**env,'DATA_UPDATE_RUN_ID':'third-run','PARTICULATE_REFRESH':'1'})
        self.assertEqual(forced.returncode,0,forced.stderr)
        self.assertTrue(any('/api/area/' in p for p in self.provider_calls))

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
