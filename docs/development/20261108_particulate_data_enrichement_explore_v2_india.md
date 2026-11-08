# Particulate data enrichment v2: India

Research and refresh date: **Sunday, 8 November 2026**. Requested observation
cutoff: `2026-11-08`, inclusive, in `Asia/Kolkata` (UTC+05:30).

## Executive summary

**Implemented four bounded enrichments after plan approval:** an expanded
monitor inventory and national historical backfill; PM10 and hourly episode
detail; separately labeled fire, weather and IITM context; and a historical
LongPMInd grid. The strongest immediate gains came from the first two steps.

The selected 2025/2026 network now contains **24 reference monitors**, up from
16, plus the existing separate AirGradient sensor. Eligible 2026 reference
PM2.5 station-days increased from 3,560 after the initial refresh to **5,396**.
PM10 contributes **5,046 eligible station-days at 22 locations** in 2026.
The 2024 national backfill contains eligible PM2.5 at **534 stations** and PM10
at **525 stations**. These historical stations are not all active in November 2026.

The acquisition is dated **Sunday, 8 November 2026**; source availability still
limits eligible PM2.5 to **4 November**, PM10 to **2 November**, and partial
PM2.5 observations to **5 November**. Missing dates remain unknown. Full national
2025/2026 backfill and ERA5 were unavailable without their respective access
credentials; the fire download covers only a rolling week. Independent validation
of the historical model remains pending.

Current deliverables are under
[`output/india-particulate-20261108/enrichment/`](../../output/india-particulate-20261108/enrichment/),
including [validation and artifact digests](../../output/india-particulate-20261108/enrichment/validation.json),
2025/2026 atlas profiles and local SVG previews, and scientific review figures.
The [versioned-package guide](../../output/india-particulate-20261108/GIT-CONTENTS.md)
identifies the review datasets and receipts included in Git; bulk caches,
hourly exports and full SVG previews remain local.

## What the article changes about the investigation

Ranjani Iyer Mohanty's [Fair Observer article, published 6 November 2026][1],
connects Delhi's recurring late-October–January pollution with particulate
concentrations, crop-residue burning, local emissions and stagnant weather.
This suggests measuring episode timing and both particle fractions, alongside
the existing annual available-day counts. Its phone readings lack the station,
averaging interval and complete provenance needed for ingestion.

Two details need correction before translating the article into map data:

- Its linked vehicle-contribution evidence is a **2021** CSE analysis of IITM
  model results for **24 October–8 November 2021**. The reported majority concerns
  **local sources**, not all Delhi PM2.5 and not a measured November 2026 source
  share. Preserve period, denominator and modeled status. [CSE original analysis][2]
- WHO's **15 µg/m³ PM2.5** and **45 µg/m³ PM10** values have a **24-hour**
  averaging period; its annual values are 5 and 15 µg/m³, respectively. Do not
  compare an unspecified phone reading with an annual or daily benchmark as
  though the intervals were interchangeable. [WHO pollutant guidance][3]

Delhi motivates the episode pilot; it does not represent the pollution mixture,
seasonal cycle or monitoring coverage of every Indian region.

## Initial refresh: the baseline before expansion

The [previous enrichment](20261029_particulate_data_enrichement_explore.md) and
[maintained methodology](../pages/data/anthropocene-particulate.md) describe a
selected urban sample: 14 CPCB locations, two AirNow locations and one AirGradient
sensor. The fetcher previously hard-coded an October cutoff and reused cached
archive indexes. It now accepts an inclusive date interval, refreshed listings
and a recent-file revision window.

Acquisition ran from `2026-11-08T18:07:15.774329+00:00` to
`2026-11-08T18:07:47.200627+00:00`. All 34 location/year listings were refreshed;
cached daily files from 20 October onward were requested again. Earlier cached
files were reused. The original October snapshot remains available for comparison.

| Instrument / period | Stations | Eligible station-days before | After refresh | Latest eligible local date |
| --- | ---: | ---: | ---: | --- |
| Reference monitors, 2025 | 16 | 4,006 | 4,006 | 2025-12-31 |
| Reference monitors, 2026 | 16 | 3,471 | **3,560** | **2026-11-04** |
| AirGradient, 2025 | 1 | 100 | 100 | 2025-12-31 |
| AirGradient, 2026 | 1 | 245 | 245 | 2026-10-02 |

These counts were recomputed from the old and refreshed
`openaq-station-days.csv.gz` files. Eligibility still requires at least 18 distinct
valid hours. The refresh added 139 station-day rows, including incomplete days,
and revised one existing row; no rows disappeared. The revision changed New Delhi
AirNow's 27 October record from one valid hour to 23, making it eligible. The net
increase is **89 eligible reference station-days**.

OpenAQ documents publication **72 hours after a location's day ends**, with later
patches possible. This explains why requesting 8 November does not supply a
complete 8 November archive. That Indian local day was also still in progress
at acquisition. No missing dates were filled or labeled zero. [OpenAQ AWS documentation][4]

The initial refresh is retained within `output/india-particulate-20261108/`:

- `sources/asia-pm25/openaq-station-days.csv.gz`: refreshed Indian normalized data.
- `sources/asia-pm25/openaq-download-receipts.json` and `openaq-quality.json`:
  raw-file digests, acquisition interval, requested cutoff and observed cutoffs.
- `sources/data/anthropocene/`: rebuilt 2025/2026 profiles, GeoJSON, cell-day
  ledger, coverage report and extreme-value review.
- `sources/india-refresh-validation.json`: before/after counts and validation.

The 2026 profile records `requested_data_through: 2026-11-08` separately from
`data_through: 2026-11-04`. Its Japan and China inputs are the prior observations;
their source-specific dates remain visible. The subsequent expanded profiles
and newly rendered local previews are in `enrichment/`. The public gallery and
the immutable release have not been republished.

## Four enrichment steps

| Step | New information | Implemented result | Remaining scope |
| --- | --- | --- | --- |
| 1. Expand the reference-monitor inventory | More places and longer histories | Eight new OpenAQ reference locations; 558-entry archive inventory; all twelve XKDR 2024 partitions | National 2025/2026 backfill needs a full-access key; three station crosswalks remain unresolved |
| 2. Retain PM10 and episode detail | Paired particle fractions, hourly timing and station weather | 1,339,685 instrument-hours; PM10 at 22 locations; paired-day and episode tables; separate PM10 atlas legends | Provider quality review and instrument-method compatibility remain relevant |
| 3. Add fire and dispersion context | Regional detections, measured wind and modeled contributions | NOAA-20/21 public rolling fire feeds; station weather; numeric IITM chart snapshot | No ERA5 or long fire history; IITM issue time unknown and forecast categories fail a closure check |
| 4. Add a separate historical modeled field | Regional context outside monitored cities | LongPMInd v2 monthly archives verified; 2022 annual/November native grids and labeled figures | Historical reconstruction only; held-out validation not established |

### 1. Expand from selected cities to a reconciled reference-monitor inventory

**Use CPCB station identities as the backbone, with OpenAQ and XKDR as delivery
routes.** The new lead is [XKDR's India Air Quality Database][5]. Its live
`/v1/meta` response reports 558 stations and 207 monthly partitions spanning
January 2009–March 2026, exported on 30 September 2026. These are archive-wide
counts, not 558 active PM2.5 stations in November. The provider describes 553 CPCB
stations plus five embassy/consulate stations. [Provider repository][6]

A bounded probe using the provider's published demo key returned HTTP 200 for
metadata, the Anand Vihar inventory and two days of raw particulate observations.
The 1–2 November 2024 sample contains 89 records: 47 PM2.5 and 42 PM10. The station
response identifies `site_301`, with a last-seen timestamp of 1 September 2025.
Thus even the archive's March 2026 endpoint overstates this particular station's
freshness. Receipts and responses are in `sources/research/xkdr-*` within the
dated delivery.

The implemented integration follows these rules:

1. Override the fixed `LOCATIONS` default in
   [`fetch-openaq-pm25.py`](../../scripts/fetch-openaq-pm25.py) with a versioned
   inventory using `--locations-json`. The saved registry retains source IDs,
   coordinates, instrument class and crosswalk status. Historical coordinate
   validity is explicitly unverified. The [CPCB station-list snapshot][7] is a
   useful crosswalk input, not proof of today's complete network.
2. Expand the Delhi/NCR and Punjab–Haryana–western Uttar Pradesh corridor first.
   Retain station/pollutant/month coverage and a national 2024 state/month matrix.
   Empty months have zero observation counts, not zero pollution. Fractions use
   calendar days in the requested window, not verified operational uptime.
3. Accept a unique provider-compatible coordinate/name match only. Preserve
   unmatched and ambiguous identities; do not assign city centroids. The 2024
   backfill is separate from the 2025/2026 OpenAQ records, so overlapping mirror
   values and source precedence have not yet been adjudicated.
4. Use XKDR for verified historical backfill. Its public demo access permits
   complete 2024 bulk files, avoiding the measurements endpoint's row limit;
   the broader archive needs a free individual key. Use CPCB/OpenAQ for recent
   dates according to their actual availability. XKDR declares CC BY 4.0 for its
   compilation with attribution to XKDR and the upstream networks. [Access and terms][5]

**Result:** the [versioned selection](../../scripts/data/india-openaq-locations-20261108.json)
adds Ludhiana (5569), Amritsar (5551), Gurugram (10921), Patiala (5544), Faridabad
(10908 and 10820), and Ghaziabad (5665 and 10919). The
[derived inventory](../../output/india-particulate-20261108/enrichment/inventory.json)
has 21 accepted upstream matches, two unmatched reference locations (Rajbagh and
Vasundhara), one ambiguous match (Sector 11 Faridabad), and the separate sensor.
Unresolved sites retain their OpenAQ identities and are not merged into XKDR.

| Reference observations | Stations | Eligible station-days | Change from refreshed 16-location sample |
| --- | ---: | ---: | ---: |
| Expanded OpenAQ PM2.5, 2025 | 24 | 5,804 | +1,798 |
| Expanded OpenAQ PM2.5, 2026 | 24 | 5,396 | +1,836 |
| XKDR PM2.5, 2024 | 534 | 157,677 | Separate historical period |
| XKDR PM10, 2024 | 525 | 154,964 | Separate historical period |

The selected OpenAQ network remains geographically selective. The national
archive has some 2024 particulate data at 537 distinct stations; 52 of those
lack inventory coordinates. Their nonspatial records are retained, and they are
not mapped using invented coordinates. Adding stations changes coverage and
the chance of an any-monitor threshold exceedance; it is not evidence that
pollution increased. AirGradient's 100 eligible days in 2025 and 245 in 2026
remain separate and unchanged.

### 2. Retain PM10, paired particle fractions and the hourly pollution season

**There is useful information already in the cache.** Inspection of
`sources/asia-pm25/raw/location-235-20261104.csv.gz` found PM10, PM2.5, wind speed,
wind direction, relative humidity and temperature. The corresponding Powai,
Mumbai file also contains PM10. The original parser selected only `parameter=pm25`.
These are verified fields in two files, not a nationwide completeness claim;
file dates must still be checked against each record's local timestamp.

The new normalizer retains **station–instrument–pollutant–interval** records
with original and normalized units, quality flags, retrieval digest and both UTC
and local time. It saves hourly data before deriving daily means and inventories
which locations supply each pollutant or weather variable.

It derives paired PM2.5/PM10 ratios and an indicative `PM10 − PM2.5` coarse fraction
only from colocated, time-aligned, compatible measurements. Retain negative
differences as a quality issue rather than silently clipping them. Neither the
ratio nor the difference identifies a unique emission source.

Build October–January episode views with hourly peaks, daily concentrations,
valid-hour counts and duration above a named threshold. A season crosses calendar
years: compare October 2025–January 2026 as a complete season where available;
label October 2026–January 2027 as incomplete. For a current-year comparison,
use the same observed dates and monitor cohort in both years. Missing days break
an observed episode unless an explicitly separate gap rule is introduced.

| Daily concentration reference | PM2.5, µg/m³ | PM10, µg/m³ | Interpretation |
| --- | ---: | ---: | --- |
| Existing atlas display | >35 | Not implemented | Project visualization threshold |
| WHO 2021 guideline level | 15 | 45 | 24-hour guidance, distinct from annual guidance |
| India NAAQS | 60 | 100 | 24-hour national standard, with its own compliance rules |

Sources: [existing atlas definitions](../pages/data/anthropocene-particulate.md),
[WHO][3] and [Indian Economic Service's reproduction of the CPCB standards][8].
Research counts using the project's 18-hour rule are not automatically regulatory
compliance determinations. Retain available-day denominators and benchmark
versions; do not convert composite AQI into particulate mass.

**Result:** 260,374 colocated paired hours produce 10,369 days with at least
18 paired hours. The 4,001 negative coarse-fraction hours remain flagged; 1,258
zero-PM10 denominators yield a missing ratio. These diagnostic values are not
certification of instrument-method equivalence. Conflicting duplicates are
excluded; valid subhourly observations are averaged within each hour. A
deterministic best-covered instrument is selected per station/pollutant/day.
Wind directions use circular means. Missing dates break episodes and censor
their observed boundaries.

PM10 contributes 5,397 eligible station-days in 2025 and 5,046 in 2026, at
22 reference locations in each year. The atlas adds separate valid-day and
daily-mean-above-100 µg/m³ legends. H3 counts remain unions of local cell-days:
2026 has 4,275 measured PM10 cell-days and 1,453 above-threshold cell-days.
They are research counts, not formal regulatory-compliance determinations.

The matched calendar-date/cohort table contains 3,734 PM2.5 and 3,460 PM10
station-date pairs across 2025 and 2026. It provides a basis for comparisons
without attributing changes in network size to changes in air quality. The
October 2026–January 2027 season is incomplete.

### 3. Join regional fire activity to dispersion conditions and modeled attribution

**Add context for why an episode persists, while keeping measurements and model
outputs distinguishable.** There are three complementary inputs:

- **NASA FIRMS:** satellite active-fire detections, acquisition time, platform,
  confidence and fire radiative power. Its documented API offers VIIRS standard
  and near-real-time products, a free map key and requests of up to five days.
  The [public download catalog][16] also supplies rolling seven-day CSVs without
  a map key; this implementation acquired NOAA-20 and NOAA-21 VIIRS C2 NRT files.
  [NASA API documentation][9]
- **ERA5:** hourly boundary-layer height, wind components and precipitation for
  regional weather context. The atmospheric grid is 0.25 degrees; early-release
  ERA5T normally lags about five days and can later be revised. It cannot supply
  a same-day November 8 analysis merely because its catalog was updated that day.
  [Dataset and access][10], [variable definitions][11]
- **IITM DSS:** modeled contributions from Delhi sectors, surrounding districts
  and biomass burning. Its WRF-Chem system assimilates CPCB PM2.5 and satellite
  aerosol information. The current portal explicitly says its forthcoming
  stubble-burning contribution forecasts use climatological fire counts and
  emissions. [Method][12], [operational portal][13]

Convert timestamped monitor/fire observations through UTC, retaining
`Asia/Kolkata` dates for summaries. IITM daily date labels are joined as published;
their timezone is not independently specified, so they are not an hourly join.
For a longer contextual series, compare monitored
PM episodes with upwind fire activity and low-dispersion conditions, using
declared lag windows and sensitivity checks. Use measured station weather from
step 2 where available; regional reanalysis supplies different spatial support.
A shallow boundary layer is a stagnation indicator, not direct proof of a thermal
inversion; inversion classification needs a vertical temperature profile.

Preserve platform and processing version, reconcile standard/NRT overlaps, and
distinguish fire detections from unique fires, burned area and emissions. Cloud,
overpass timing and short fires affect detection. A crop mask can flag likely
agricultural context but does not establish the burned material. Wind at 10 m
alone cannot establish a plume's transport path or Delhi's crop-burning share.

The fire subset uses the explicit box **72–79°E, 27–33°N**, which crosses national
borders; it is not a Punjab/Haryana polygon or an India-only total. Nominal/high
confidence detections total 5,286 for NOAA-20 and 5,193 for NOAA-21 across
1–8 November IST. A rolling week spans eight local date labels with partial
boundary days. Satellites remain separate: these counts cannot be summed as
unique fires. FRP is instantaneous power in MW, not integrated energy or emissions.

The IITM portal embeds numeric chart arrays. The saved snapshot contains 29
forecast categories for 7–10 November and a daily modeled stubble-burning
history for 35 dates from 3 October to 7 November. Missing 5 October is preserved.
Forecast issue time, lead time and model version are absent from the chart and
remain unknown; the future dates are labeled forecasts. The published forecast
categories sum to **100.807–101.155%** across the four dates. The adapter flags
this inconsistency, preserves the numbers, and does not renormalize or treat
them as a closed source-share composition. There is still no verified stable
bulk-history API contract.

**Result:** a [context figure](../../output/india-particulate-20261108/enrichment/figures/delhi-episode-context.png)
and its PDF/CSV sources combine Anand Vihar PM, measured station wind, regional
fire detections and explicitly modeled IITM estimates. The chart preserves gaps
and identifies forecast status. The join is descriptive; the short overlapping
fire/monitor interval does not support a causal attribution or lag analysis.
ERA5 was not acquired because CDS credentials were absent; measured station
wind is a separately labeled input, not a substitute for boundary-layer height.

### 4. Add LongPMInd as a separate historical modeled baseline

[LongPMInd v2][14] provides daily and monthly PM2.5 and PM10 on a 10 km grid for
India during **1980–2022**, with NetCDF archives and code. The December 2024 v2
record specifically updates PM10, so pin that release and its checksums.
The [research paper][15] describes a machine-learning reconstruction and notes
that observations available for training cover recent years, 2018–2022; earlier
estimates therefore involve temporal extrapolation. High-pollution cases also
need particular scrutiny.

Use it for a clearly dated historical background map and seasonal context across
areas without monitors. This is a new India-specific candidate beyond the earlier
generic CAMS proposal. It **does not fill 2025/2026 measurement gaps** or describe
the November 2026 episode.

**Result:** both monthly archives were downloaded and verified against Zenodo's
published MD5 checksums, with local SHA-256 digests also retained. The bounded
pilot prepares 2022, the latest complete year, into native-grid annual and
November fields, CSV, NPZ, GeoJSON and a
[separate modeled-map figure](../../output/india-particulate-20261108/enrichment/figures/longpmind-2022-model.png).
The grids are 350 × 400, nominally 10 km, with approximately 0.1° spacing.
GeoJSON points locate grid centers; they are not monitor sites.

Annual means weight monthly means by calendar days and require all twelve
months. The PM10 source contains **22 negative cell-months**: these are retained
in an audit table and masked, not clipped to zero. This leaves 27,708 valid
annual PM2.5 cells and 27,692 PM10 cells; the paired CSV/GeoJSON has 27,692 cells.
NetCDF pollutant variables omit units attributes, so µg/m³ is documented from
the paper rather than inferred from the numeric range. The pinned record
declares CC BY 4.0.

The modeled layer contributes **zero** government-monitor coverage days.
Independent held-out validation has not been established because a verified
2022 holdout set and its relationship to training data were not acquired.
Superiority over other modeled products is not established.

## Reproduction and validation

The approved implementation is reproducible with these repository adapters:

```bash
python3 scripts/fetch-openaq-pm25.py \
  --output output/india-particulate-20261108/enrichment/openaq \
  --locations-json scripts/data/india-openaq-locations-20261108.json \
  --start 2025-01-01 --end 2026-11-08

python3 scripts/fetch-india-particulate-context.py \
  --root output/india-particulate-20261108/enrichment

python3 scripts/prepare-india-particulate-enrichment.py \
  --root output/india-particulate-20261108/enrichment

python3 scripts/build-india-particulate-profiles.py \
  --root output/india-particulate-20261108/enrichment

python3 scripts/plot-india-particulate-enrichment.py \
  --root output/india-particulate-20261108/enrichment

python3 tests/test_india_particulate_enrichment.py
python3 scripts/validate-india-particulate-enrichment.py \
  --root output/india-particulate-20261108/enrichment
```

The expanded OpenAQ fetch completed at `2026-11-08T18:27:07.663729+00:00`.
Normalized PM2.5 SHA-256 is
`195a79e1cd98d85fbafe4f88f91c2a7eceba2d6e413245e2fbcd7dabe9c7acdd`.
Saved raw files, manifests and digests define this snapshot; later network
requests may return revisions. Identical task-cache copies share storage, and
fetch writes use atomic replacement to preserve earlier snapshots.

Within `enrichment/`, the principal outputs are:

- `inventory.json`, `acquisition-manifest.json`: identities, provenance and access limits.
- `observations/`: normalized records, instrument-hours, daily PM/weather,
  paired hours/days, episodes, matched cohorts, and station/state/month coverage.
- `context/`: FIRMS detections and per-satellite days, IITM numeric chart data,
  the descriptive Delhi join and its caveats.
- `model/`: the distinct 2022 modeled layer, invalid-value audit and unit/license metadata.
- `profiles/`: expanded 2025/2026 atlas inputs, cell-day ledgers and checksums.
- `atlas-preview/`: locally rendered 2025/2026 AuthaGraph SVGs and a 2026 PNG.
- `figures/`: source-labeled PNG/PDF scientific review figures.
- `validation.json`: validated counts, limitations and artifact digests.

Ten regression tests cover distinct-hour completeness, conflicting duplicates,
deterministic instrument choice, IST/UTC midnight, circular wind averaging,
negative coarse values, episode gaps, ambiguous identities, unmodified IITM
percentages and H3 day unions. Independent PM2.5 adapters agree on all 13,487
station-days' valid hours, eligibility and >35 classifications; their serialized
means differ by at most 0.000043 µg/m³ because of CSV precision. Profile/GeoJSON
hashes and native renderer marker/legend checks pass for both years. Legacy
metric properties and totals are preserved, and model values do not enter
observed-day totals. Review plots were visually inspected.

Scoped documentation links pass. The repository-wide documentation checker
has an existing failure resolving a template link under
`scripts/templates/setouchi-futures-manual.html`; it is not reported as passing.

### Initial refresh commands and audit

The dated working directory was seeded with copies of the existing Indian raw
cache and the existing Japanese/Chinese normalized inputs. The actual refresh
and preparation commands were:

```bash
python3 scripts/fetch-openaq-pm25.py \
  --output output/india-particulate-20261108/sources/asia-pm25 \
  --start 2025-01-01 --end 2026-11-08 \
  --refresh-index --refresh-since 2026-10-20

python3 scripts/prepare-asia-pm25.py \
  --input output/india-particulate-20261108/sources/asia-pm25 \
  --output output/india-particulate-20261108/sources/data/anthropocene \
  --as-of-utc 2026-11-08T18:07:47.200627+00:00 \
  --data-through 2026-11-08
```

The network archive is mutable. Reproduce this acquisition from its saved files
and digests; a later refresh can return revisions. The refreshed normalized
Indian table has SHA-256:

```text
d2b4a4c3251cf0d861e2a1812b2268fc7c6bda64f1311cb08cd730e23508cdb1
```

Checks passed for unique station-days, inclusive local date bounds, finite
nonnegative means, distinct-hour eligibility, unchanged pre-20-October rows,
byte-identical Japan/China inputs, preserved legacy features, profile/GeoJSON
digests and exceedance counts bounded by measured days. A synthetic fixture also
verified discovery through refreshed indexes, replacement of cached recent data
and exclusion of the day after the requested cutoff. Existing extreme-value
review flags remain applicable; these checks do not certify instrument accuracy.

The XKDR probe used `/v1/meta`, `/v1/stations?city=Delhi&q=Anand+Vihar` and
`/v1/measurements` with `station=site_301`, both particulate parameters,
`start=2024-11-01`, `end=2024-11-02`, `agg=raw`, `format=csv`. Exact URLs,
HTTP results and response digests are saved in
`sources/research/xkdr-probe-receipt.json`. No new account or subscription was
created. Subsequent bulk ingestion uses the publisher's permitted 2024 access.
The remaining national 2025/2026 backfill, ERA5 and long fire history require
additional authorized source access; no new account or paid service was created.

[1]: https://www.fairobserver.com/more/environment/the-tunnel-of-doom-air-pollution-season-in-delhi/
[2]: https://www.cseindia.org/vehicles-the-biggest-contributors-to-winter-pollution-in-delhi-cse-11048
[3]: https://www.who.int/teams/environment-climate-change-and-health/air-quality-and-health/health-impacts/types-of-pollutants
[4]: https://docs.openaq.org/aws/about
[5]: https://airquality.xkdr.org/
[6]: https://github.com/xKDR/Air-Quality-Database/blob/main/README.md
[7]: https://app.cpcbccr.com/ccr_docs/caaqms_list_All_India.pdf
[8]: https://ies.gov.in/arthapedia/concept/ambient-air-quality-standards-india
[9]: https://firms.modaps.eosdis.nasa.gov/api/area/
[10]: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview
[11]: https://confluence.ecmwf.int/pages/viewpage.action?pageId=685246447
[12]: https://ews.tropmet.res.in/dss/aboutus.php
[13]: https://ews.tropmet.res.in/dss/
[14]: https://zenodo.org/records/14557027
[15]: https://essd.copernicus.org/articles/16/3565/2024/index.html
[16]: https://firms.modaps.eosdis.nasa.gov/api/active_fire_files/all?format=json
