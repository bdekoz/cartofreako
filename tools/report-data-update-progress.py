#!/usr/bin/env python3
"""Local hourly CPC progress reports; no provider requests or acquisition changes."""
import argparse
from datetime import datetime, timezone, timedelta
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
LOCAL = ZoneInfo('America/Los_Angeles')
NAMES = [f'{field}.{year}.nc' for year in range(1979, 2027) for field in ('tmax', 'tmin')]
BEGIN = '# BEGIN cartofreako-hourly-data-update-progress'
END = '# END cartofreako-hourly-data-update-progress'
ORDER = ('natural-earth', 'orbital', 'astronomy', 'anthropocene', 'resources', 'atmosphere',
         'atoll', 'network', 'petroleum', 'ocean', 'ocean-context', 'india')


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.'+path.name)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def held_lock(path):
    if not path.exists():
        return False
    with path.open() as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(stream, fcntl.LOCK_UN)
    return False


def writer_running(root):
    return held_lock(root/'update.lock')


def pacing_seconds(requests, interval, successes, minimum=2):
    total = 0
    for _ in range(requests):
        total += interval
        successes += 1
        if successes >= 10:
            interval, successes = max(minimum, interval*.9), 0
    return total


def snapshot(root, now, minimum=2):
    states = list((root/'runs').glob('*/state.json'))
    if not states:
        raise ValueError('No data-update run found under '+str(root))
    state = read(max(states, key=lambda p:p.stat().st_mtime))
    ident = state['dataset_id']
    raw = root/'editions'/ident/'inputs/anthropocene/.raw/cpc'
    cache = root/'cache/http'
    cached = {}
    for path in cache.glob('*.json'):
        if path.name.endswith('.partial.json'):
            continue
        item = read(path)
        url = item.get('url', '')
        name = url.rsplit('/', 1)[-1]
        if '/cpc_global_temp/' in url and name in NAMES and item.get('bytes', 0)>0:
            if (root/'cache/sha256'/item['sha256']).is_file():
                cached[name] = item
    pinned = {}
    archive = read(root/'cache/cpc-archive/manifest.json', {})
    for name, item in archive.get('files', {}).items():
        if name in NAMES and int(name.split('.')[1]) <= 2025:
            obj = root/'cache/sha256'/item['sha256']
            if obj.is_file() and obj.stat().st_size == item['bytes']:
                pinned[name] = item
                cached[name] = item
    current_year = {}
    for variable in ('tmax', 'tmin'):
        name = f'{variable}.2026.nc'
        item = read(root/'cache/cpc-current'/f'{variable}.2026.json', {})
        if not item:
            continue
        obj = root/'cache/sha256'/item['sha256']
        if not obj.is_file() or obj.stat().st_size != item['bytes']:
            continue
        cached[name] = item
        start, end = item.get('pending_start'), item.get('pending_through')
        needed = ((datetime.fromisoformat(end)-datetime.fromisoformat(start)).days+1) if start and end else 0
        saved = [path.stem for path in (root/'cache/cpc-current/parts'/f'{variable}.2026').glob('*.nc')
                 if start and end and start <= path.stem <= end and path.with_name(path.name+'.receipt.json').exists()]
        checked = item.get('inventory_checked_at')
        check_due = not checked or datetime.fromisoformat(checked).astimezone(timezone.utc).date() != datetime.fromtimestamp(now, timezone.utc).date()
        current_year[name] = {'variable':variable, 'through':item['data_through'],
                             'needed_days':needed, 'cached_days':len(saved),
                             'remaining_requests':max(0, needed-len(saved))+int(check_due),
                             'latest_saved_day':max(saved) if saved else None,
                             'running':held_lock(root/'cache/cpc-current'/f'{variable}.2026.lock')}
    complete = {name: (raw/name).stat().st_size for name in NAMES if (raw/name).is_file()}
    typical = sum(r['bytes'] for r in cached.values())/len(cached) if cached else 88_000_000
    partials = {}
    bases = ('https://psl.noaa.gov/thredds/fileServer/Datasets/cpc_global_temp',
             'https://downloads.psl.noaa.gov/Datasets/cpc_global_temp')
    for name in set(NAMES)-set(complete)-set(pinned)-set(current_year):
        for base in bases:
            key = hashlib.sha256((base+'/'+name+'{}').encode()).hexdigest()
            part = cache/(key+'.part')
            meta = read(cache/(key+'.partial.json'))
            if part.is_file() and meta:
                item = {'name': name, 'bytes': part.stat().st_size,
                        'total': meta.get('bytes') or typical, 'mtime': part.stat().st_mtime}
                if item['mtime']>partials.get(name, {}).get('mtime', 0):
                    partials[name] = item
    requests = 0
    for name in set(NAMES)-set(complete):
        if name in pinned:
            continue
        if name in current_year:
            requests += current_year[name]['remaining_requests']
            continue
        if name in partials:
            item = partials[name]
            requests += max(0, math.ceil((item['total']-item['bytes'])/2097152))
        elif name in cached:
            # Same-day cache copies need no provider traffic. Otherwise one
            # conditional request is the expected unchanged-object path.
            checked = datetime.fromisoformat(cached[name]['checked_at']).astimezone(timezone.utc)
            requests += int(checked.date()!=datetime.fromtimestamp(now, timezone.utc).date()
                            and cached[name].get('checked_run')!=ident)
        else:
            requests += math.ceil(typical/2097152)
    key = hashlib.sha256(b'noaa-psl').hexdigest()
    provider = read(cache/'providers'/(key+'.json'), {})
    interval = max(minimum, provider.get('interval', minimum))
    delay = max(0, provider.get('next_at', 0)-now)
    model = delay+pacing_seconds(requests, interval, provider.get('successes', 0), minimum)
    sources = [r['id'] for r in state.get('sources', [])]
    return {'at': now, 'run_id': ident, 'status': state['status'], 'error': state.get('error'),
            'writer_running': writer_running(root), 'completed_sources': sources,
            'phase': state.get('current_source') or next((s for s in ORDER if s not in sources), 'validation/activation'),
            'source_issues': state.get('issues', {}),
            'complete': len(complete), 'cached': len(cached), 'pinned_archives': len(pinned), 'total_files': len(NAMES),
            'current_year':current_year,
            'cpc_workers':[s['variable'] for s in current_year.values() if s['running']],
            'downloaded_bytes': sum(complete.values())+sum(p['bytes'] for p in partials.values()),
            'expected_bytes': typical*len(NAMES), 'remaining_requests': requests,
            'partial': max(partials.values(), key=lambda p:p['mtime']) if partials else None,
            'pacing_interval': interval, 'pacing_model_seconds': model,
            'minimum_interval': minimum, 'free_gib': shutil.disk_usage(root).free/1024**3}


def report(current, previous):
    at = datetime.fromtimestamp(current['at'], LOCAL)
    lines = [at.strftime('%Y-%m-%d %H:%M:%S %Z')+' — data-update progress',
             f'Run: {current["run_id"]}; journal: {current["status"]}; '
             f'writer: {"running" if current["writer_running"] else "not running"}',
             f'Sources: {len(current["completed_sources"])}/{len(ORDER)} complete; phase: {current["phase"]}',
             f'CPC: {current["complete"]}/96 files downloaded; {current["cached"]}/96 cached; '
             f'{current["downloaded_bytes"]/1024**3:.2f}/{current["expected_bytes"]/1024**3:.2f} GiB in this edition.']
    for name, issue in current.get('source_issues', {}).items():
        lines.append(f'Source {name}: {issue["status"]}; {issue["reason"]}')
    if current.get('pinned_archives'):
        lines.append(f'Pinned CPC archives: {current["pinned_archives"]} files need no provider request.')
    for item in current.get('current_year', {}).values():
        text=f'CPC 2026 {item["variable"].upper()}: retained through {item["through"]}'
        if item['needed_days']:
            text+=f'; {item["cached_days"]}/{item["needed_days"]} missing days cached'
            if item['latest_saved_day']:
                text+='; latest saved '+item['latest_saved_day']
        text+='; worker '+('running' if item['running'] else 'not running')
        lines.append(text+'.')
    partial = current['partial']
    if partial:
        lines.append(f'Current file: {partial["name"]} — {100*partial["bytes"]/partial["total"]:.1f}% '
                     f'({partial["bytes"]:,}/{int(partial["total"]):,} bytes); '
                     f'last progress {datetime.fromtimestamp(partial["mtime"], LOCAL):%H:%M:%S %Z}.')
    lines.append(f'Adaptive spacing: {current["pacing_interval"]:.1f}s between requests.')
    if (previous and previous['run_id']==current['run_id']
            and previous.get('pinned_archives', 0)==current.get('pinned_archives', 0)):
        delta = current['downloaded_bytes']-previous['downloaded_bytes']
        elapsed = current['at']-previous['at']
        if elapsed>0:
            lines.append(f'Since last report: {current["complete"]-previous["complete"]:+d} files, '
                         f'{delta/1024**2:+.1f} MiB over {elapsed/60:.0f} min.')
            if delta>0 and current['writer_running'] and previous['writer_running']:
                rate = delta/elapsed
                current['observed_eta_seconds'] = max(0, current['expected_bytes']-current['downloaded_bytes'])/rate
                lines.append(f'Observed-rate ETA: about {current["observed_eta_seconds"]/3600:.1f}h if that rate persists; '
                             'recently recovering pacing can make this conservative.')
    if current['complete']==96 and not current.get('cpc_workers'):
        lines.append('CPC downloads complete. Remaining source preparation/validation has no reliable ETA yet.')
    elif (current['status']=='failed' or not current['writer_running']) and not current.get('cpc_workers'):
        lines.append('Completion ETA unavailable while the update is stopped; saved bytes remain available.')
    else:
        seconds = current['pacing_model_seconds']
        finish = at+timedelta(seconds=seconds)
        lines.append(f'CPC pacing-model ETA: about {seconds/3600:.1f}h remaining; {finish:%Y-%m-%d %H:%M %Z}.')
        lines.append(f'Assumes continued recovery toward {current["minimum_interval"]:g}s and no renewed 429s. '
                     'Network/processing delays may extend this; this ETA covers CPC only.')
    if current['error']:
        lines.append('Run error: '+current['error'])
    lines.append(f'Free disk: {current["free_gib"]:.1f} GiB.')
    return '\n'.join(lines)


def cron_contents(existing, command=None):
    cleaned = re.sub(r'(?ms)^'+re.escape(BEGIN)+r'\n.*?^'+re.escape(END)+r'\n?', '', existing)
    if command is None:
        return cleaned
    return cleaned.rstrip('\n')+'\n\n'+BEGIN+'\n0 * * * * '+command.replace('%', r'\%')+'\n'+END+'\n'


def configure_hourly(root, notify=False, remove=False, minimum=2):
    result = subprocess.run(['crontab', '-l'], text=True, capture_output=True)
    if result.returncode and 'no crontab' not in result.stderr.lower():
        raise RuntimeError(result.stderr.strip())
    command = [sys.executable, str(Path(__file__).resolve()), '--root', str(root),
               '--minimum-interval', str(minimum), '--scheduled']
    if notify:
        command.append('--notify')
    shell = shlex.join(command)+' >> '+shlex.quote(str(REPO/'data-update-progress.log'))+' 2>&1'
    updated = cron_contents(result.stdout, None if remove else shell)
    if not remove:
        (REPO/'data-update-progress.log').touch(exist_ok=True)
    subprocess.run(['crontab', '-'], input=updated, text=True, check=True)
    check = subprocess.run(['crontab', '-l'], text=True, capture_output=True)
    if check.returncode or (BEGIN in check.stdout)==remove:
        raise RuntimeError('Could not verify the hourly reporting schedule')
    print('Removed hourly progress schedule.' if remove else 'Installed: 0 * * * * (every hour at :00).')


def notify_user(text):
    command = shutil.which('notify-send')
    if not command:
        return
    bus = Path(f'/run/user/{os.getuid()}/bus')
    if not bus.exists():
        return
    env = {**os.environ, 'DBUS_SESSION_BUS_ADDRESS': 'unix:path='+str(bus)}
    # This is a desktop notification to the same local user, not an external
    # message. Full details remain in the durable progress log.
    subprocess.run([command, '--app-name=Cartofreako', 'CPC / data-update progress', text],
                   env=env, timeout=10, check=False, stdout=subprocess.DEVNULL)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=REPO/'.cartofreako/data')
    parser.add_argument('--minimum-interval', type=float, default=2)
    parser.add_argument('--notify', action='store_true')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--install-hourly', action='store_true')
    mode.add_argument('--uninstall-hourly', action='store_true')
    mode.add_argument('--scheduled', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    if not math.isfinite(args.minimum_interval) or args.minimum_interval<=0:
        parser.error('--minimum-interval must be positive')
    if args.install_hourly or args.uninstall_hourly:
        configure_hourly(root, args.notify, args.uninstall_hourly, args.minimum_interval)
        return 0
    # Leave the hourly schedule dormant between acquisition runs. Independent
    # CPC workers remain visible in manual reports but do not enable this job.
    if args.scheduled and not writer_running(root):
        return 0
    folder = root/'reports'
    folder.mkdir(parents=True, exist_ok=True)
    with (folder/'progress-report.lock').open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        current = snapshot(root, time.time(), args.minimum_interval)
        history = read(folder/'progress-history.json', [])
        previous = history[-1] if history else None
        text = report(current, previous)
        history.append(current)
        atomic_json(folder/'progress-history.json', history[-168:])
        atomic_json(folder/'progress-latest.json', {**current, 'report': text})
        print(text+'\n', flush=True)
        if args.notify:
            try:
                notice = [line for line in text.splitlines() if line.startswith(
                    ('CPC:', 'Current file:', 'CPC pacing-model ETA:', 'Completion ETA unavailable',
                     'CPC downloads complete.', 'Run error:'))]
                notice.append('ETA assumes no renewed throttling. Details: '+str(REPO/'data-update-progress.log'))
                notify_user('\n'.join(notice))
            except (OSError, subprocess.TimeoutExpired) as error:
                print('Desktop notification unavailable: '+str(error), file=sys.stderr)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print('data-update progress: '+str(error), file=sys.stderr)
        sys.exit(1)
