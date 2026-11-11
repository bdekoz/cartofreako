#!/usr/bin/env python3
"""Probe CPC hourly until a data request succeeds, then log its Pacific time."""
import argparse
from http.client import HTTPException
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from data_http_policy import Pacer, retry_after, timestamp
from dataset import DatasetError, ROOT, atomic_json, data_root, lock, redact


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def probe(url, timeout):
    """Exactly one GET; never fetch a whole file or follow a redirect."""
    request = Request(url, headers={'Range': 'bytes=0-0', 'Accept-Encoding': 'identity',
                                    'User-Agent': 'cartofreako-data-update/1.0'})
    try:
        with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            status = response.status
            headers = dict(response.headers)
            if status == 206 and not re.fullmatch(r'bytes 0-0/[1-9][0-9]*', response.headers.get('Content-Range', '')):
                return status, headers, False, 'invalid one-byte Content-Range'
            # Even if the provider ignores Range and sends HTTP 200, only
            # one byte is read before closing. Nothing enters the data cache.
            success = status in (200, 206) and bool(response.read(1))
            return status, headers, success, 'data probe succeeded' if success else 'no successful data response'
    except HTTPError as error:
        status, headers = error.code, dict(error.headers)
        error.close()
        return status, headers, False, 'Too Many Requests' if status == 429 else 'HTTP error'
    except (URLError, OSError, HTTPException) as error:
        return None, {}, False, redact(error)


def wait_until(when):
    # Short sleeps allow prompt Ctrl-C/SIGTERM handling while detached.
    while (remaining := when - time.time()) > 0:
        time.sleep(min(remaining, 30))


def record_success(path, when, status, url):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        stream.write(f'{timestamp(when)} HTTP {status} first successful CPC ping {redact(url)}\n')
        stream.flush()
        os.fsync(stream.fileno())


def monitor(url, status_log, cache, *, interval=3600, timeout=20, once=False):
    status_log, cache = Path(status_log), Path(cache)
    folder = cache / 'http/monitors'
    journal = folder / 'noaa-cpc-ping.json'
    pacer = Pacer(url, cache)
    with lock(folder, 'noaa-cpc-ping'):
        print(f'{timestamp(time.time())} Monitoring {redact(url)}; success log {status_log}', flush=True)
        while True:
            state = json.loads(journal.read_text()) if journal.exists() else {}
            now = time.time()
            due = state.get('next_probe_at', 0)
            if pacer.enabled:
                with pacer.state() as provider:
                    due = max(due, provider.get('next_at', 0))
                    if due <= now:
                        provider['next_at'] = now + provider['interval']
            if due > now:
                print(f'{timestamp(now)} Next probe no earlier than {timestamp(due)}', flush=True)
                if once:
                    return 2
                wait_until(due)
                continue
            # Reserve the next hourly slot before I/O so restarting the
            # monitor cannot accidentally cause a burst of extra requests.
            state.update(url=redact(url), last_attempt_at=timestamp(now, utc=True), next_probe_at=now+interval)
            atomic_json(journal, state)
            status, headers, success, note = probe(url, timeout)
            received = time.time()
            value = next((v for k, v in headers.items() if k.lower() == 'retry-after'), '')
            provider_delay = retry_after(value, now=received)
            state.update(last_status=status, next_probe_at=max(now+interval, received+provider_delay))
            atomic_json(journal, state)
            print(f'{timestamp(received)} HTTP {status if status is not None else "unavailable"}: {note}', flush=True)
            if success:
                record_success(status_log, received, status, url)
                print(f'First successful ping recorded in {status_log}; monitor finished.', flush=True)
                return 0
            if status == 429 or provider_delay:
                pacer.defer(max(provider_delay, 30 if status == 429 else 0), throttled=status == 429)
            if value:
                print(f'Retry-After: {value}; next probe no earlier than {timestamp(state["next_probe_at"])}', flush=True)
            if once:
                return 1


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('must be a finite positive number')
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    base = os.environ.get('CPC_BASE_URL', 'https://psl.noaa.gov/thredds/fileServer/Datasets/cpc_global_temp')
    parser.add_argument('--url', default=base.rstrip('/')+'/tmin.1981.nc', help='CPC file that returned 429')
    parser.add_argument('--log', type=Path, default=ROOT/'noaa-cpc-ping-status.log')
    parser.add_argument('--cache', type=Path, default=Path(os.environ.get('DATA_HTTP_CACHE', data_root()/'cache')))
    parser.add_argument('--interval', type=positive, default=3600, help='seconds between probes (default: 3600)')
    parser.add_argument('--timeout', type=positive, default=20, help='network timeout in seconds (default: 20)')
    parser.add_argument('--once', action='store_true', help='one eligible probe; exit 2 if an existing cooldown prevents it')
    args = parser.parse_args()
    if urlsplit(args.url).scheme not in ('http', 'https') or not urlsplit(args.url).hostname:
        parser.error('--url must be an HTTP(S) data URL')
    try:
        return monitor(args.url, args.log.expanduser().resolve(), args.cache.expanduser().resolve(),
                       interval=args.interval, timeout=args.timeout, once=args.once)
    except KeyboardInterrupt:
        print('CPC monitor stopped; saved probe schedule retained.', file=sys.stderr)
        return 130
    except (DatasetError, OSError, ValueError) as error:
        print('ping-noaa-cpc: '+redact(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
