# Anthropocene snapshot assets

This directory contains the small authoritative profile and the normalized,
checked Stage 8 snapshot used by ordinary offline generation:

- `anthropocene-profile.json` fixes the calendar year, partial-snapshot date,
  thresholds, H3 aggregation, source roles, metric styles, and deferred work;
- `anthropocene-2026.geojson` contains one point at the center of each
  resolution-4 H3 cell with one or more positive unique-day counts; and
- `SHA256SUMS` pins the normalized GeoJSON bytes used by `make check`; normal
  generation also verifies the same digest through the selected profile.

The snapshot is partial through source-specific dates recorded in the profile.
Its 43,895 cells are observations, not complete global coverage. An omitted
property means unavailable or unobserved and must not be interpreted as zero.
The profile's literal `duration.year` is the sole year authority; the generator
does not read the host clock.

## Checked normalization

The 2026 snapshot was normalized on 2026-08-05 from:

| Raw input | Captured SHA-256 or set digest |
| --- | --- |
| NOAA GHCN GSN archive | `3cb70cbd4af615154bbd3513c3b258f9913082b91a32cf4c58d9b7328b053954` |
| NOAA GHCN station inventory | `91e4bd9b4c991c3ea9c19062eae73bca118cad0f4a436e33149ff345bffc8f9c` |
| EPA AirData daily PM2.5 archive | `c6900edda13ee5d451abb393f961ae427e76506bb87931967db54150143c91d5` |
| NOAA HMS annual smoke archive | `42f89a34af1a3a6f4fcaf08c0e87b51b0741a220ecec271e9f7856ba3a9350c5` |
| NOAA Storm Events details | `2afe1359fe06a94bc0fcd099f186f0e7f8aba8243cc37665ab8d2c87e4b42f19` |
| NOAA Storm Events locations | `36960089c2ce0a491ac5010eeea51fd7a9747e876cc128eaf14eb92087b785f3` |
| 167 CWFIS daily CSVs, filename-sorted SHA-256 manifest | `0d9e1656a3778e5c166db8cf520dfdf50a9445305c6d38d40e67a0770ae1432a` |

The raw archives are intentionally not checked in. They are mutable annual
feeds and total hundreds of megabytes. `make fetch-anthropocene-data` stages a
new set under ignored `.raw/YEAR/`; `make prepare-anthropocene-data` produces a
candidate under ignored `.prepared/` without replacing this checked snapshot.
Promotion is deliberately manual because every refresh changes source
coverage and must update profile dates, statistics, and the normalized digest
together.

NASA FIRMS global data is optional and requires `FIRMS_MAP_KEY`. When present,
the fetcher obtains five-day global chunks and the preparer accepts each CSV.
The checked snapshot has no FIRMS rows and therefore does not claim Russian
fire coverage. CWFIS supplies the default public Canada/North America layer.

See the [Anthropocene implementation notes](../../docs/anthropocene-implementation-notes.md)
for source roles, formulas, coverage boundaries, refresh commands, and
interpretation limits.
