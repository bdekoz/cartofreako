---
layout: default
title: Anthropocene particulate sources
---

# Anthropocene particulate sources

[Documentation index](../README.md) · [Source data](README.md) ·
[Implementation](../passes/anthropocene/implementation.md) ·
[Japan / Asia enrichment investigation](../../development/20261029_particulate_data_enrichement_explore.md)

The Setouchi study uses measured PM2.5 concentrations from Japan, China and a
selected set of Indian cities. Government monitors, a community sensor, US EPA
AQI, satellite fire detections and analyst-drawn smoke are separate layers.
None is a measure of how much an individual event was caused by climate change.

These additions are local study outputs in
`output/setouchi-triennale-2028/`; they do not imply that the public gallery or
the immutable v14 release has been republished.

## What the new PM2.5 marks mean

| Mark | Quantity | Missing and zero |
| --- | --- | --- |
| Teal ring | Number of local days with an eligible government/reference monitor in an H3 resolution 4 cell | No ring means no eligible measurements in the ingested sources. |
| Orange cross-square | Number of those days when at least one monitor's daily mean was greater than **35 µg/m³** | A covered cell with zero exceedance days is explicitly zero for its available records. |
| Magenta diamond | Valid days from the separately identified AirGradient sensor | This does not increase government-monitor coverage. |
| Purple circle | AirGradient days with a daily mean greater than 35 µg/m³ | Sensor estimates are not substituted for reference measurements. |
| Existing brown cross-square | US EPA PM2.5 **AQI >100** days | This is a different measure from the concentration threshold. |

The 35 µg/m³ threshold is an analytical display threshold, not a universal
health standard or a conversion of national AQIs. Counts use the **union of
local cell-days**, so ten monitors reporting on one day do not create ten days.
A threshold day means at least one eligible monitor exceeded it; it is not the
mean concentration of the cell. Rings retain evidence of monitoring where
exceedance counts are zero.

An eligible station-day has at least **18 distinct valid hours**. Missing,
negative, nonfinite and conflicting duplicate readings are excluded. Missing
dates are not filled with zeros. The detailed counts and date ranges below
must accompany any comparison: these are available-day counts, not annual
exceedance rates or national population exposure estimates.

Eligibility is a completeness and parsing check, not independent certification
of an instrument. Daily means above 250 µg/m³ are retained but listed in
`pm25-extreme-value-review.json` for operator review. This is a review trigger,
not a health standard or an automatic clipping limit. Some Indian records have
long runs of repeated high values, and some Japanese provisional values remain
unusually high after status-code removal; those require source-level review.

<!-- BEGIN generated-pm25-coverage -->
| Country / instrument | Year | Stations | H3 cells | Available date range | Eligible station-days |
| --- | --- | ---: | ---: | --- | ---: |
| China / government | 2025 | 1,686 | 562 | 2025-01-01–2025-12-31 | 547,441 |
| India / selected government | 2025 | 16 | 15 | 2025-01-01–2025-12-31 | 4,006 |
| India / AirGradient sensor | 2025 | 1 | 1 | 2025-09-10–2025-12-31 | 100 |
| Japan / government | 2025 | 1,076 | 223 | 2025-11-01–2025-12-31 | 62,014 |
| China / government | 2026 | 1,345 | 511 | 2026-01-01–2026-10-28 | 391,529 |
| India / selected government | 2026 | 16 | 15 | 2026-01-01–2026-10-26 | 3,471 |
| India / AirGradient sensor | 2026 | 1 | 1 | 2026-01-01–2026-10-02 | 245 |
| Japan / government | 2026 | 1,095 | 226 | 2026-01-01–2026-09-30 | 283,898 |
<!-- END generated-pm25-coverage -->

## Japan: Ministry of the Environment / Soramame

The [Soramame service](https://soramame.env.go.jp/) supplies provisional hourly
government observations. Its [API manual](https://soramame.env.go.jp/data/apiManual/3.html)
documents `REQUEST_DATA=PM2_5` in µg/m³ and prefecture codes `01`–`47`.
The public API requires no account. Live error responses establish a rolling
one-year history and a maximum three-month request window; requesting a whole
year in one call fails.

The ingestion requests all 47 prefectures for November–December 2025 and
January–September 2026 in separate windows. Station IDs are strings, preserving
leading zeros. Coordinates come from the service's published station CSV,
dated 30 October 2026 at 01:00 JST (29 October UTC). Historical station IDs that
cannot be joined to that inventory are excluded and listed in the quality
receipt; a current coordinate join is not proof that a station never moved.

Hours `01`–`24` belong to the supplied JST observation date. The daily mean
uses valid nonnegative hourly PM2.5 values. **SPM is not substituted for PM2.5**:
it is a different field with different units. Provisional readings can be
corrected later. Attribution and the service's national/local-agency reuse
conditions should be checked before exhibition or redistribution.

Numeric `999x` status codes are excluded before counting hours or calculating
means. The [MOE monitoring manual](https://www.env.go.jp/content/900402531.pdf),
table 6-4-1, identifies `9999`, `9998` and `9997` as missing/unmeasured/error
codes; [prefectural documentation](https://taiki-kanshi.wakayama.jp/wp-content/uploads/2024/10/hosoku.pdf)
also lists instrument-status codes in that range. Raw-data inspection found
`9999` among otherwise low concentrations, which would have produced false
exceedances if treated as a measurement.

[NIES finalized monitoring downloads](https://tenbou.nies.go.jp/download/)
remain the preferred historical backfill. The accessible release is fiscal
2024, which runs April 2024–March 2025; it is not calendar 2025. This study does
not label that older release as 2026 measurements. Earlier 2025 Japanese months
remain a documented gap pending a finalized, date-filtered backfill.

## China: CNEMC via the Quotsoft public archive

[Wang Xiaolei's Quotsoft archive](https://quotsoft.net/air/) identifies the
[China National Environmental Monitoring Centre](https://air.cnemc.cn:18007/)
as the source of its daily files. Its documented URL is
`https://quotsoft.net/air/data/china_sites_YYYYMMDD.csv`. The direct CNEMC portal
timed out during this acquisition; the successfully downloaded files are
explicitly attributed to the public archive rather than claimed as direct
CNEMC API responses.

The ingestion downloads every date from 1 January 2025 through 28 October
2026. Only `type=PM2.5` hourly means in µg/m³ are used. `PM2.5_24h`, AQI and
other pollutant rows are excluded to prevent duplicate or incompatible
measurements. Hours `00`–`23` use China local time.

Station-code coordinates use the **13 February 2022 inventory**, preserved in
[this pinned public copy](https://github.com/bryt888/hfaw/blob/3cd38dc7a3feb285ef143301455fb03748b572f5/AQI/data/stations_20220213.csv).
This is a historical coordinate crosswalk, not a newly surveyed 2026 station
inventory. Invalid coordinates and unmatched/new station codes are excluded;
their identities are retained in the acquisition receipts. Potential station
relocations and a newer authoritative inventory remain review items. The H3
display does not resolve individual neighbourhoods or interpolate between
stations.

## India: CPCB and AirNow through OpenAQ's public archive

The [OpenAQ bulk archive](https://docs.openaq.org/aws/about) is public on AWS
and can be read **without an API key**. This differs from OpenAQ's v3 API and
authenticated Explorer downloads. The implementation uses location/year
listings and daily compressed CSVs, following the
[documented archive structure](https://docs.openaq.org/aws/year-guide).

The selected sample has 16 reference-monitor locations in 14 Indian cities:
New Delhi, Mumbai, Chennai, Kolkata, Bengaluru, Ahmedabad, Lucknow, Hyderabad,
Srinagar, Indore, Thiruvananthapuram, Patna, Jaipur and Chandigarh. Fourteen
locations are supplied by CPCB and two by AirNow. This is an explicitly
selected urban sample, **not all of India's monitors**. The exact location IDs,
provider names, primary Explorer pages and cached metadata hashes are in
`assets.static/anthropocene/asia-pm25/openaq-locations.json`.

Public location pages establish the provider, reference-monitor classification,
PM2.5 parameter and Indian country code. The parser accepts PM2.5 mass
concentrations only, checks coordinates and the local UTC+05:30 offset, and
aggregates the actual available files for 2025 and 2026. A station's listing in
the archive does not imply complete reporting. The AWS archive also has a
publication delay; observed dates, not download dates, control the map.

Multiple within-hour measurements are averaged. If a station-day has more
than one PM2.5 sensor, the sensor with the most valid hours is selected, with a
stable sensor-ID tie break. Overlapping instruments are never counted as
additional days. A daily record with changing coordinates is excluded.
Provider-specific licences remain attached to the source metadata; the
AirNow locations declare US Public Domain. OpenAQ is the distributor, not the
original instrument operator.

## Commercial and community sensor sources

| Source | What is usable | Current treatment |
| --- | --- | --- |
| [AirGradient / OpenAQ](https://explore.openaq.org/locations/5728639) | Public historical PM2.5 from the outdoor Bemina, Srinagar sensor; the page declares CC BY 4.0 | Ingested as a separate sensor layer. Provider-reported concentrations; local calibration has not been independently validated. |
| [PurpleAir API](https://community.purpleair.com/t/about-the-purpleair-api/7145) | Sensor metadata, PM2.5 channels and historical observations; hourly requests can cover 180 days, daily requests two years | No authorized API key/points were available. No PurpleAir observations are claimed as integrated. A bounded outdoor-sensor and calibration pilot is the next step. |
| [IQAir AirVisual](https://api-docs.iqair.com/) | Concentrations depend on the subscription; the [published plans](https://www.iqair.com/air-quality-monitors/api) put pollutant concentrations above the free Community tier and list 48-hour history in Enterprise | The free AQI feed is not a substitute for annual concentration records. Historical access and reuse terms need a concrete account/export before integration. |
| [WAQI / AQICN](https://aqicn.org/api/) | Useful station discovery and pollutant AQI feeds | AQI sub-indices are not raw µg/m³. Published restrictions on cached redistribution make this a poor default archive for the atlas. |

PurpleAir can add local detail, but that does not establish better national
coverage or more accurate reference measurements. Its low-cost optical
observations need outdoor classification, channel agreement, humidity checks
and a correction appropriate to the local aerosol mix. A US correction should
not be silently assumed valid for Japan, China or India. The
[PurpleAir historical API guidance](https://community.purpleair.com/t/loop-api-calls-for-historical-data/4623)
also requires sorting timestamps and respecting half-open request windows.
No account registration, point purchase or commercial subscription was made.

## Existing global and North American layers

| Original provider | Observation represented | Scope / limitation |
| --- | --- | --- |
| [NOAA GHCN Daily](https://www.ncei.noaa.gov/pub/data/ghcn/daily/) | Station daily temperature/precipitation records and heavy precipitation | Global GSN station sample; record-history and baseline filters remain in each profile. |
| [US EPA AirData](https://aqs.epa.gov/aqsweb/airdata/download_files.html) | PM2.5 AQI exceedance days | US regulatory records; preserved separately from the new Asian concentration counts. |
| [NOAA HMS](https://www.ospo.noaa.gov/products/land/hms.html) | Analyst-observed smoke plume days | Primarily North America; plume occurrence is not ground-level PM2.5 concentration. |
| [NOAA Storm Events](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/) | Reported flood/heavy rain and severe-weather days | US event reporting; no inference of absence elsewhere. |
| [Canadian Wildland Fire Information System](https://cwfis.cfs.nrcan.gc.ca/downloads/hotspots/) | Available satellite hotspot reporting days | Source coverage and available files vary; detections are not area burned. |
| [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/api/) | Optional global active-fire observations | Configured optional source; no new FIRMS acquisition is claimed in this enrichment. |

Original feature values and metric totals are preserved exactly. Their existing
source-specific cutoffs remain recorded in the profiles; the new acquisition
date does not make the older smoke, fire, weather or EPA records current.

## Reproduce and audit

The acquisition and preparation scripts are:

- [`fetch-soramame-pm25.py`](../../../scripts/fetch-soramame-pm25.py)
- [`fetch-cnemc-pm25.py`](../../../scripts/fetch-cnemc-pm25.py)
- [`fetch-openaq-pm25.py`](../../../scripts/fetch-openaq-pm25.py)
- [`prepare-asia-pm25.py`](../../../scripts/prepare-asia-pm25.py)

Raw downloads, URL/hash receipts, station metadata and daily normalized tables
are retained under `assets.static/anthropocene/asia-pm25/`. The three
`*-quality.json` files report exclusions and failures. The prepared profiles,
GeoJSON, unique cell-day ledger and country coverage report live in
`output/setouchi-triennale-2028/sources/data/anthropocene/`.

The preparation checks unique station-day keys, valid-hour thresholds, finite
nonnegative concentrations, H3 cell centres, threshold-days as a subset of
measured-days, preserved legacy values/totals and output hashes. Rendering
uses the existing native particulate generator. No interpolated field or
countrywide average is fabricated to fill gaps.

The separate [Setouchi development plan](../../development/20261029_setouchi_triennale_explore.md)
records human reviews and next steps: authoritative Chinese station updates,
earlier Japanese 2025 backfill, an exhaustive Indian location inventory,
source reuse checks before public exhibition, and any funded PurpleAir pilot.
