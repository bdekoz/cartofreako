# Anthropocene Stage 13 source expansion review

[Documentation index](../index.md) ·
[Anthropocene implementation](anthropocene-implementation-notes.md) ·
[Enrichment plan](anthropocene-enrichment-plan.md) ·
[Generation methods](generation-methods.md)

## Decision

The legacy observation atlas remains scientifically useful, including its
large polar smoke geometry, but its uneven source coverage should be improved
without combining measurements, analyses, forecasts, and attribution into one
score. Stage 13 re-evaluated five practical source families.

The recommended order is:

1. expand climate-record stations from the GSN subset to full GHCN-Daily;
2. add an independently labeled global surface-PM field from OpenAQ's public
   archive after provider/unit/coverage QA;
3. prototype CAMS or MAIAC as a separate global aerosol analysis/remote-sensing
   product, never as `observed-smoke-days`; and
4. use PurpleAir only as a supplemental, explicitly authorized source when a
   bounded sensor set or provider-arranged bulk extract is available.

No Stage 13 source is silently merged into the checked 2026 atlas. Its current
counts and digest remain reproducible, and each new family must pass a
source-specific preparation and promotion review first.

## Source findings

| Source | What it can add | Access and scale | Stage 13 classification |
| --- | --- | --- | --- |
| [NOAA GHCN-Daily](https://www.ncei.noaa.gov/pub/data/ghcn/daily/) | Many more global TMAX, TMIN, and precipitation stations than the current GSN subset | Public station/year files; the complete archive is several GB compressed and requires the existing 30-year/183-day eligibility calculation over much more history | **First implementation candidate** for climate-record coverage |
| [OpenAQ Open Data on AWS](https://docs.openaq.org/aws/about) | Global provider-reported surface PM2.5 and other pollutants, partitioned by location/year/month/day | Anonymous gzip CSV archive; measurements remain provider-specific and need units, averaging, location, instrument, and duplicate QA | **First implementation candidate** for a separate `air-quality-exposure` field |
| [CAMS global EAC4 reanalysis](https://ads.atmosphere.copernicus.eu/datasets/cams-global-reanalysis-eac4?tab=overview) | Globally complete PM2.5, black/organic carbon, and aerosol optical-depth estimates | 0.75° gridded analysis, every three hours, 2003 onward; data assimilation combines observations with an atmospheric model | **Separate modeled/reanalysis pass**, not an observation count |
| [NASA MODIS MAIAC MCD19](https://www.earthdata.nasa.gov/s3fs-public/2025-04/MCD19_User_Guide_V6.pdf) | Global aerosol optical depth and aerosol-type context, including biomass-burning classification | High-volume gridded remote sensing with cloud/retrieval QA and Earthdata acquisition requirements | **Separate satellite aerosol pass** after a bounded tile/time design |
| [PurpleAir API](https://community.purpleair.com/t/api-use-guidelines/1589) | Dense low-cost PM2.5 observations where sensors exist | API key required; historical queries are one sensor at a time, and PurpleAir asks large historical users to arrange a bulk request rather than crawl thousands of sensors | **Optional supplemental source**, not the default global acquisition path |

CAMS [GFAS fire emissions](https://ads.atmosphere.copernicus.eu/datasets/cams-global-fire-emissions-gfas?tab=overview)
is also valuable for global biomass-burning flux and estimated species
emissions. It is derived from satellite fire radiative power, however, so it
belongs beside FIRMS as a fire/emissions product rather than being relabeled
as an analyst-observed smoke plume.

## Why OpenAQ precedes PurpleAir

OpenAQ publishes day files for all sensors at a location in an anonymous
public object archive. That structure is compatible with bounded, resumable
year/location acquisition and makes a global coverage inventory possible
before downloading the complete measurement body. A preparer can retain
source provider, sensor, unit, averaging period, coordinates, and observation
time before deriving any daily threshold.

PurpleAir is still useful, especially where regulatory and OpenAQ monitors are
sparse. It is not a good unattended global-history default: official guidance
says the historical endpoint handles one sensor per request, API consumption
uses account keys/points, and large historical requests should be coordinated
with PurpleAir. A production integration therefore needs all of:

- an explicit `PURPLEAIR_API_READ_KEY` authorization boundary;
- a pinned sensor manifest or provider-supplied bulk extract;
- attribution and use-term review;
- channel agreement, uptime, humidity/correction, indoor/outdoor, and location
  QA; and
- an independent metric such as `purpleair-pm25-exceedance-days`, never an
  assertion of smoke attribution.

Until those are available, PurpleAir remains exploration-only rather than
being simulated with partial or rate-limit-hostile acquisition.

## Promotion gates

### Full GHCN-Daily

- pin archive/version, station inventory, and complete SHA-256 manifest;
- rerun the existing quality-flag rejection and 30 prior years × 183 valid
  days eligibility rules;
- report eligible stations and H3 cells by world region against the GSN
  baseline;
- retain strict record comparisons and 1991–2020 wet-day p95 semantics; and
- establish a workstation disk/time budget before making it standard.

### OpenAQ surface PM

- inventory public locations and PM2.5 sensors before selecting files;
- accept only convertible mass-concentration units and record every rejected
  unit/provider combination;
- normalize timestamps to the source's explicit UTC/local semantics without
  inventing missing time zones;
- deduplicate sensor/provider/location/day while preserving raw provenance;
- publish geographic and reporting-day coverage gates; and
- label the product surface air-quality exposure, not smoke.

### CAMS or MAIAC aerosol

- keep analysis/model and satellite-retrieval layers separate;
- select one variable, level, temporal aggregation, version, and QA contract;
- expose missing/cloud/retrieval failure instead of treating it as zero;
- validate multiple world regions and high latitudes; and
- use a new output stem so the legacy HMS smoke layer remains identifiable.

## Implementation boundary

This review adds no hidden downloader, credential, or generated metric. The
next bounded implementation should begin with an OpenAQ inventory fixture or
a full-GHCN development slice, then add a deterministic preparer and coverage
report before any default artifact is changed. PurpleAir should be implemented
only after an operator supplies a valid key plus a bounded acquisition scope
or bulk-data arrangement.
