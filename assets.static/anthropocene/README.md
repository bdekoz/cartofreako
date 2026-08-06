# Anthropocene snapshot assets

This directory contains the authoritative profiles and normalized snapshots
used by ordinary offline Stage 8 and Stage 8b generation:

- `anthropocene-profile.json` fixes the calendar year, partial-snapshot date,
  thresholds, H3 aggregation, source roles, metric styles, and deferred work;
- `anthropocene-2026.geojson` contains one point at the center of each
  resolution-4 H3 cell with one or more positive unique-day counts; and
- `anthropocene-temperature-2025-profile.json` and
  `anthropocene-temperature-2026-profile.json` independently fix complete-2025
  and partial-2026 NOAA CPC field contracts;
- their year-bearing GeoJSON files contain every resolution-3 H3 cell so
  covered-zero and missing cells remain distinguishable; and
- `SHA256SUMS` pins all normalized GeoJSON bytes used by `make check`; normal
  generation also verifies each digest through its selected profile.

The snapshot is partial through source-specific dates recorded in the profile.
Its 43,895 cells are observations, not complete global coverage. An omitted
property means unavailable or unobserved and must not be interpreted as zero.
The profile's literal `duration.year` is the sole year authority; the generator
does not read the host clock.

The [Stage 8b enrichment plan](../../docs/anthropocene-enrichment-plan.md)
records the CPC temperature/FIRMS-gate increment implemented here and the
remaining CAMS, PurpleAir, and ocean work.

## Stage 8b temperature fields

The temperature profiles use NOAA CPC Global Unified Temperature V1.0 daily
TMAX/TMIN on its 0.5-degree global grid. The preparer maps valid source-grid
centers to resolution-3 H3, averages multiple grid centers in one cell for each
06Z-to-06Z reporting day, and counts strict daily records against all available
same-calendar-day values since 1979 once at least 30 history years exist.
Every one of the 41,162 global H3 cells is serialized. Positive `valid_days`
means an analyzed cell even when both record counts are zero; zero valid days
means missing or outside CPC's land domain.

The 2025 product is complete through December 31 and compares with 1979–2024.
The 2026 product is partial through August 4 (216 source days) and compares
with 1979–2025. The checked normalization audit is:

| Year | Status | Covered H3 cells | Record-high days | Record-low days | TMAX valid cell-days | TMIN valid cell-days |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2025 | complete | 11,945 | 178,896 | 59,806 | 4,359,841 | 4,359,925 |
| 2026 | partial through August 4 | 11,945 | 105,041 | 40,943 | 2,579,998 | 2,580,120 |

The shared covered domain includes 2,069 North American, 1,553 South American,
936 European, 2,836 African, 1,580 Siberian, 1,132 China/Japan, and 951
Oceania bounding-box audit cells. These boxes overlap and are coverage gates,
not additive regional statistics. The display saturates record-high counts at
32 days and record-low counts at 16 days, approximately the complete-2025
95th-percentile values; the raw counts remain embedded and unchanged.
Antimeridian H3 rings are split before projection. Cahill-Keyes uses an
SVG-audited centered-hex fallback for 21 covered cells at its outer topology
cuts; the other five projections use no fallback cells.

The 96-file CPC source manifest has SHA-256
`9e8507f1ad63332b3af55b5a5ab76e26209baabd97f6f644df55b5cd2faa0bee`.
The normalized 2025 and 2026 GeoJSON SHA-256 values are respectively
`7dbb1858e357ff87b8fd4b7ee9874d0a9978a55ccfe7943e16ec7563e9a520c6`
and
`5953eba7ed3e73ecc0d77961a17759336f1833118d7850a5891a316369c9bde2`.

Generate their SVG families or all exported artifacts with:

```sh
make generate-anthropocene-2025
make generate-anthropocene-2026
make generate-anthropocene-year-artifacts
```

The ignored raw archive is staged and candidates are prepared explicitly:

```sh
make fetch-anthropocene-cpc-data
make prepare-anthropocene-temperature-data
```

The raw `.raw/cpc/SHA256SUMS` file is itself pinned by both profiles. Candidate
preparation verifies every yearly TMAX/TMIN file and never overwrites the
checked GeoJSON.

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

NASA FIRMS requires the free `FIRMS_MAP_KEY`. A new global refresh fails when
the key or staged FIRMS rows are absent unless the explicit
`ANTHROPOCENE_REGIONAL_DEVELOPMENT_ONLY=1` debugging override is set. The
fetcher reads FIRMS' advertised date ranges, joins standard S-NPP processing to
its NRT tail in five-day chunks, and avoids logging the key. Preparation audits
at least 95% of expected dates and nonzero rows in North America, South
America, Europe, Africa, northern Asia, East Asia, and Oceania. The original
checked Stage 8 snapshot still has no FIRMS rows and therefore makes no global
fire claim; CWFIS is regional QA/fallback only.

See the [Anthropocene implementation notes](../../docs/anthropocene-implementation-notes.md)
for current source roles, formulas, coverage boundaries, refresh commands, and
interpretation limits, and the
[Stage 8b enrichment plan](../../docs/anthropocene-enrichment-plan.md) for the
full global-coverage design and its remaining phases.
