"""Persistent provider pacing and bounded HTTP retries for dataset acquisition."""
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shlex
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import urlopen

from dataset import DatasetError, ROOT, atomic_json, redact


def setting(name, default, *, positive=False):
    try:
        value = float(os.environ.get(name, default))
        if not math.isfinite(value) or value < 0 or (positive and value == 0):
            raise ValueError()
        return value
    except ValueError:
        raise DatasetError(f"{name} must be a finite {'positive' if positive else 'nonnegative'} number") from None


class Progress:
    def __init__(self, url):
        self.name = redact(Path(urlsplit(url).path).name or urlsplit(url).hostname)
        self.started = time.monotonic()
        self.last = None
        self.offset, self.total = 0, None
        self.interval = setting('DATA_HTTP_PROGRESS_INTERVAL', 30, positive=True)

    def report(self, message='downloading', *, force=False):
        now = time.monotonic()
        if force or self.last is None or now - self.last >= self.interval:
            size = f'{self.offset:,}' + (f'/{self.total:,}' if self.total is not None else '')
            print(f'data-http-fetch: {self.name}: {size} bytes; elapsed {now-self.started:.0f}s; '
                  + message, file=sys.stderr, flush=True)
            self.last = now

    def sleep(self, delay):
        end = time.monotonic() + delay
        while (remaining := end - time.monotonic()) > 0:
            time.sleep(min(remaining, self.interval, 30))
            self.report('waiting for provider cooldown')


class Pacer:
    def __init__(self, url, cache):
        host = (urlsplit(url).hostname or '').lower()
        # Both NOAA access points serve the same provider. A host switch must
        # not bypass a cooldown, and different files/processes share the state.
        self.enabled = host == 'psl.noaa.gov' or host.endswith('.psl.noaa.gov')
        self.minimum = setting('NOAA_HTTP_MIN_INTERVAL', 2)
        self.maximum = setting('NOAA_HTTP_MAX_INTERVAL', 60)
        if self.maximum < self.minimum:
            raise DatasetError('NOAA_HTTP_MAX_INTERVAL must be at least NOAA_HTTP_MIN_INTERVAL')
        key = hashlib.sha256(b'noaa-psl').hexdigest()
        self.path = Path(cache) / 'http/providers' / (key + '.json')

    @contextmanager
    def state(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_suffix('.lock').open('a') as stream:
            # Only short state transactions hold this lock; all sleeps and
            # network transfers happen outside it.
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                value = json.loads(self.path.read_text()) if self.path.exists() else {}
                value['interval'] = min(self.maximum, max(self.minimum, value.get('interval', self.minimum)))
                yield value
                atomic_json(self.path, value)
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def wait(self, deadline, progress):
        if not self.enabled:
            return
        announced = False
        while True:
            with self.state() as state:
                now = time.time()
                delay = max(0, state.get('next_at', 0) - now)
                if not delay:
                    state['next_at'] = now + state['interval']
                    return
            remaining = deadline - time.monotonic()
            if delay > remaining:
                raise DatasetError(f'Provider cooldown exceeds remaining HTTP retry budget ({remaining:.0f}s); '
                                   'shared cooldown and partial bytes retained. '
                                   + retry_hint(time.time()+delay))
            if not announced and delay >= 5:
                progress.report(f'shared NOAA cooldown; next request no earlier than {timestamp(time.time()+delay)}', force=True)
                announced = True
            progress.sleep(min(delay, 30))

    def defer(self, delay, *, throttled):
        if self.enabled:
            with self.state() as state:
                if throttled:
                    state['interval'] = min(self.maximum, max(1, self.minimum, state['interval'] * 2))
                    state['successes'] = 0
                state['next_at'] = max(state.get('next_at', 0), time.time() + delay, time.time() + state['interval'])
                next_at = state['next_at']
            return next_at
        return time.time() + delay

    def success(self):
        if self.enabled:
            with self.state() as state:
                state['successes'] = state.get('successes', 0) + 1
                # A single successful range must not reset throttled pacing.
                if state['successes'] >= 10:
                    state['interval'] = max(self.minimum, state['interval'] * 0.9)
                    state['successes'] = 0


def timestamp(when):
    return datetime.fromtimestamp(when, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def retry_hint(when):
    run_id = os.environ.get('DATA_UPDATE_RUN_ID')
    command = (f"make data-update DATA_UPDATE_ARGS='--resume {redact(run_id)}'"
               if run_id else 'make data-update')
    return f'Try again no earlier than {timestamp(when)} with: {command}'


def retry_after(value, *, now=None):
    try:
        return max(0, float(value)) if value.isdigit() else max(0, parsedate_to_datetime(value).timestamp() - (time.time() if now is None else now))
    except (TypeError, ValueError, OverflowError):
        return 0


def cpc_ping_hint(url):
    parts = urlsplit(url)
    if ((parts.hostname == 'psl.noaa.gov' or (parts.hostname or '').endswith('.psl.noaa.gov'))
            and '/cpc_global_temp/' in parts.path):
        command = shlex.join(['nohup', 'python3', str(ROOT/'scripts/noaa-cpc-ping.py'), '--url', url])
        return ('Pause data-update; first success timestamp will be in '
                + str(ROOT/'noaa-cpc-ping-status.log') + '. Launch an hourly CPC monitor: ' + command
                + ' > ' + shlex.quote(str(ROOT/'noaa-cpc-ping-monitor.log')) + ' 2>&1 < /dev/null &'
                )
    return None


def open_response(request, pacer, progress):
    budget = setting('DATA_HTTP_RETRY_BUDGET', 1800, positive=True)
    started = time.monotonic()
    deadline = started + budget
    attempt = 0
    while True:
        if time.monotonic() >= deadline:
            raise DatasetError(f'HTTP retry budget exhausted after {budget:g}s')
        pacer.wait(deadline, progress)
        if time.monotonic() >= deadline:
            raise DatasetError(f'HTTP retry budget exhausted after {budget:g}s')
        try:
            response = urlopen(request, timeout=min(180, max(0.001, deadline - time.monotonic())))
        except HTTPError as error:
            if error.code not in (408, 429, 500, 502, 503, 504):
                if error.code == 304:
                    pacer.success()
                raise
            attempt += 1
            code = error.code
            base = 30 if code == 429 else 2
            supplied_retry_after = error.headers.get('Retry-After', '')
            provider_delay = retry_after(supplied_retry_after)
            delay = max(min(300, base * 2 ** min(attempt - 1, 8)) * random.uniform(1, 1.25),
                        provider_delay)
            error.close()
            next_at = pacer.defer(delay, throttled=code == 429)
            if code == 429:
                provider_note = (f'provider Retry-After {timestamp(time.time()+provider_delay)}'
                                 if supplied_retry_after and provider_delay > 0 else
                                 'provider reset time unknown (no usable Retry-After)')
                progress.report(f'WARNING: HTTP 429 Too Many Requests; {provider_note}; '
                                f'next eligible retry {timestamp(next_at)}', force=True)
                if not getattr(progress, 'cpc_ping_hint_shown', False):
                    hint = cpc_ping_hint(request.full_url)
                    if hint:
                        progress.report(hint, force=True)
                        progress.cpc_ping_hint_shown = True
            remaining = deadline - time.monotonic()
            if delay >= remaining:
                raise DatasetError(f'HTTP {code}; retry budget exhausted or insufficient for next cooldown '
                                   f'after {time.monotonic()-started:.0f}s (budget {budget:g}s); '
                                   'partial bytes retained. ' + retry_hint(next_at)) from None
            progress.report(f'HTTP {code}; retry {attempt} in at least {delay:.1f}s; '
                            f'next retry {timestamp(time.time()+delay)}; '
                            f'retry budget remaining {remaining:.0f}s', force=True)
            # A shared provider cooldown is rechecked before every request.
            # Other providers still receive the same bounded retry policy.
            if not pacer.enabled:
                progress.sleep(delay)
        else:
            pacer.success()
            return response
