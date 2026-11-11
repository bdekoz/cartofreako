#!/usr/bin/env python3
"""Check NASA's Exoplanet TAP service hourly until a valid one-row CSV query succeeds."""
import argparse
import csv
from datetime import datetime, timezone
from http.client import HTTPException
import io
import json
import math
import os
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from data_http_policy import retry_after, timestamp
from dataset import DatasetError, ROOT, atomic_json, data_root, lock, redact

URL = 'https://exoplanetarchive.ipac.caltech.edu/TAP/sync?' + urlencode(
    {'query': 'SELECT TOP 1 pl_name FROM pscomppars', 'format': 'csv'})
MAX_RESPONSE_BYTES = 65536


def local_timestamp(when):
    local = datetime.fromtimestamp(when, timezone.utc).astimezone()
    return local.isoformat(timespec='seconds') + ' ' + local.tzname()


def availability(success):
    return '\033[32myes\033[0m' if success else '\033[31mno\033[0m'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def probe(url, timeout):
    """One bounded GET, without redirects or internal retries; HTTP 200 alone is insufficient."""
    request = Request(url, headers={'Accept': 'text/csv', 'Accept-Encoding': 'identity',
                                    'User-Agent': 'cartofreako-data-update/1.0'})
    try:
        with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            status, headers = response.status, dict(response.headers)
            if status != 200:
                return status, headers, False, 'expected HTTP 200 CSV response'
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                return status, headers, False, 'response exceeds one-row probe size limit'
            content_type = next((v for k, v in headers.items() if k.lower() == 'content-type'), '')
            if 'html' in content_type.lower():
                return status, headers, False, 'HTML response instead of catalog CSV'
            try:
                rows = list(csv.reader(io.StringIO(body.decode('utf-8-sig')), strict=True))
            except (UnicodeError, csv.Error) as error:
                return status, headers, False, 'invalid CSV: ' + str(error)
            success = (len(rows) == 2 and rows[0] == ['pl_name'] and
                       len(rows[1]) == 1 and bool(rows[1][0].strip()))
            return status, headers, success, ('valid pl_name CSV with one planet' if success else
                                              'invalid or empty one-row catalog CSV')
    except HTTPError as error:
        status, headers = error.code, dict(error.headers)
        error.close()
        return status, headers, False, 'Too Many Requests' if status == 429 else 'HTTP error'
    except (URLError, OSError, HTTPException) as error:
        return None, {}, False, redact(error)


def wait_until(when):
    while (remaining := when - time.time()) > 0:
        time.sleep(min(remaining, 30))


def monitor(url, status_log, cache, *, interval=3600, timeout=20, once=False):
    status_log, cache = Path(status_log), Path(cache)
    folder = cache / 'http/monitors'
    journal = folder / 'nasa-exoplanet-ping.json'
    with lock(folder, 'nasa-exoplanet-ping'):
        print(f'Monitoring {redact(url)}; success log {status_log}', flush=True)
        while True:
            state = json.loads(journal.read_text()) if journal.exists() else {}
            now = time.time()
            due = state.get('next_probe_at', 0)
            if due > now:
                print(f'{local_timestamp(now)} {availability(False)} Next probe no earlier than '
                      f'{local_timestamp(due)} (cooldown; no new check)', flush=True)
                if once:
                    return 2
                wait_until(due)
                continue
            # Reserve before I/O, so restarting cannot bypass the hourly slot.
            state.update(url=redact(url), last_attempt_at=timestamp(now, utc=True), next_probe_at=now + interval)
            atomic_json(journal, state)
            status, headers, success, note = probe(url, timeout)
            received = time.time()
            value = next((v for k, v in headers.items() if k.lower() == 'retry-after'), '')
            delay = retry_after(value, now=received)
            state.update(last_status=status, last_note=note,
                         next_probe_at=max(now + interval, received + delay))
            atomic_json(journal, state)
            print(f'{local_timestamp(received)} {availability(success)} HTTP '
                  f'{status if status is not None else "unavailable"}: {note}', flush=True)
            if success:
                status_log.parent.mkdir(parents=True, exist_ok=True)
                with status_log.open('a') as stream:
                    stream.write(f'{local_timestamp(received)} HTTP {status} first successful NASA Exoplanet '
                                 f'Archive ping; valid pl_name CSV; {redact(url)}\n')
                    stream.flush()
                    os.fsync(stream.fileno())
                print(f'First successful ping recorded in {status_log}; monitor finished. '
                      'Retry with: make data-update', flush=True)
                return 0
            if value:
                print(f'Retry-After: {delay:g}s (until {local_timestamp(received + delay)})', flush=True)
            print(f'Next probe no earlier than {local_timestamp(state["next_probe_at"])}', flush=True)
            if once:
                return 1


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('must be a finite positive number')
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default=URL, help='one-row CSV query URL (default: NASA Exoplanet TAP)')
    parser.add_argument('--log', type=Path, default=ROOT / 'nasa-exoplanet-ping-status.log')
    parser.add_argument('--cache', type=Path, default=Path(os.environ.get('DATA_HTTP_CACHE', data_root() / 'cache')))
    parser.add_argument('--interval', type=positive, default=3600, help='seconds between probes (default: 3600)')
    parser.add_argument('--timeout', type=positive, default=20, help='network timeout in seconds (default: 20)')
    parser.add_argument('--once', action='store_true', help='one eligible probe; exit 2 if a saved cooldown prevents it')
    args = parser.parse_args()
    if urlsplit(args.url).scheme not in ('http', 'https') or not urlsplit(args.url).hostname:
        parser.error('--url must be an HTTP(S) CSV query URL')
    try:
        return monitor(args.url, args.log.expanduser().resolve(), args.cache.expanduser().resolve(),
                       interval=args.interval, timeout=args.timeout, once=args.once)
    except KeyboardInterrupt:
        print('NASA Exoplanet monitor stopped; saved probe schedule retained.', file=sys.stderr)
        return 130
    except (DatasetError, OSError, ValueError) as error:
        print('ping-nasa-exoplanet-archive: ' + redact(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
