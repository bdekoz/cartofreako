# Local hourly data-update progress reports

The operational reporter reads local journals, HTTP receipts and partial-file
sizes. It makes no network requests and does not alter acquisition state or
cached downloads. It lives under `tools/` so adding it does not change the
scientific implementation fingerprint of an active acquisition. Commits change
the fingerprint's revision. While acquisition is running, commit and push from
a separate worktree and leave the acquisition checkout's HEAD and scripts
unchanged. Updating that checkout before acquisition finishes invalidates its
method provenance checks.

Print a report immediately:

```sh
python3 tools/report-data-update-progress.py
```

Install the requested local schedule, every hour at minute zero, with desktop
notifications to the same logged-in user:

```sh
python3 tools/report-data-update-progress.py --install-hourly --notify
```

This adds one managed block to the user's crontab and preserves other entries.
Reports append to `data-update-progress.log` in the repository root. Machine
readable latest/history reports live under `.cartofreako/data/reports/`.
The first scheduled report is at the next `:00`, using the local scheduler;
report timestamps and estimated completion use America/Los_Angeles.
Cron runs while the local computer is awake, including after the chat closes.
Desktop notifications require the user's desktop session bus; the file report
is still written when that session is unavailable. These are local reports,
not scheduled messages delivered into the chat.

Each report shows downloaded/cached CPC files out of 96, partial bytes and
percentage, last progress, the source phase and completed-source count, disk
space, adaptive request spacing, and a CPC completion estimate. The pacing model
assumes ten successful requests per 10% recovery step down to the configured
minimum interval, without new 429s. Network/processing delays can extend it.
Later reports also show the observed throughput since the preceding sample;
that extrapolation can be conservative during recovery. Stopped runs have no
active completion estimate. Completing CPC does not mean the full acquisition
and scientific preparation have completed.

The default minimum interval is two seconds. Pass `--minimum-interval SECONDS`
when installing if the current acquisition uses a different
`NOAA_HTTP_MIN_INTERVAL`. `--root` selects another data store.

After a run becomes active or a validated candidate, the reporter sends a
final scheduled report and removes its own cron block. To stop earlier:

```sh
python3 tools/report-data-update-progress.py --uninstall-hourly
```

Verify report calculations and cron preservation with:

```sh
python3 tests/test-data-update-progress.py
```
