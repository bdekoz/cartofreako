# Local hourly data-update progress reports

The operational reporter reads local journals, HTTP receipts and partial-file
sizes. It makes no network requests and does not alter acquisition state or
cached downloads. It lives under `tools/` so adding it does not change the
scientific implementation fingerprint of an active acquisition. Commits change
the fingerprint's revision. While acquisition is running, commit and push from
a separate worktree and leave the acquisition checkout's HEAD and scripts
unchanged. The fingerprint also records whether tracked files are modified,
so documentation edits can change a previously clean checkout's fingerprint.
Keep those edits in a separate worktree during acquisition. Updating that
checkout before acquisition finishes invalidates its method provenance checks.

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
Scheduled reports run at `:00` only while `make data-update` or
`make data-update-resilient` holds the acquisition lock. Otherwise the scheduled
check exits silently, without writing reports or sending notifications. The
schedule stays installed so reporting resumes automatically during a later
update. Manual reports remain available at any time. Report timestamps and
estimated completion use America/Los_Angeles.
Cron runs while the local computer is awake, including after the chat closes.
Desktop notifications require the user's desktop session bus; the file report
is still written when that session is unavailable. These are local reports,
not scheduled messages delivered into the chat.

Each report shows downloaded/cached CPC files out of 96, partial bytes and
percentage, last progress, the source phase and completed-source count, disk
space, adaptive request spacing, and a CPC completion estimate. Reports
count imported 1979–2025 archives as cached and exclude them from future
provider requests. Old partials for those pinned years are retained on disk
and excluded from active-file progress. Reports include the retained 2026
TMAX/TMIN endpoints, missing-day subset counts, and independently running
backfill workers in manual reports even when the main update is stopped.
Independent backfill workers do not enable scheduled reports. A cached year file can
still need new daily observations; the endpoint and backfill lines show this.
The pacing model
assumes ten successful requests per 10% recovery step down to the configured
minimum interval, without new 429s. Network/processing delays can extend it.
Later reports also show the observed throughput since the preceding sample;
that extrapolation can be conservative during recovery. When neither the main
update nor a CPC worker is running, no active completion estimate is shown.
Completing CPC does not mean the full acquisition
and scientific preparation have completed.
The completion estimate covers CPC only, not a remaining FIRMS backfill,
particulate preparation, OISST transfer or full plate rendering. Completed
particulate-period reuse is visible in the acquisition log; see
[cache controls](../pages/getting-started/generation.md#particulate-acquisition-options).

For `make data-update-resilient`, reports show the current source being worked
on and list failed, deferred, blocked and invalidated sources from the journal.
This keeps an intentionally deferred astronomy source from hiding progress in
other groups. An incomplete acquisition is resumable and does not select a
partial edition; see the [resilient workflow](../pages/getting-started/generation.md#resilient-data-updates).

The default minimum interval is two seconds. Pass `--minimum-interval SECONDS`
when installing if the current acquisition uses a different
`NOAA_HTTP_MIN_INTERVAL`. `--root` selects another data store.

When the update exits, scheduled reports become silent again. To remove the
schedule entirely:

```sh
python3 tools/report-data-update-progress.py --uninstall-hourly
```

Verify report calculations and cron preservation with:

```sh
python3 tests/test-data-update-progress.py
```
