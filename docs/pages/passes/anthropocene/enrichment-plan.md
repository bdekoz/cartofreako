# Anthropocene Stage 8b enrichment plan

[Documentation index](../../../../index.md) ·
[Implemented Stage 8 notes](implementation.md) ·
[Generation guide](../../getting-started/generation.md) ·
[Snapshot assets](../../../../assets.static/anthropocene/README.md)

## Status and recommendation

Stage 8b is now an **incremental implementation** with two accepted standard
families: complete-2025/partial-2026 particulate observation atlases and
complete-2025/partial-2026 NOAA CPC temperature fields. All four pass IDs are
year-bearing and default-generated. The implementation also provides explicit
global H3 coverage/missing semantics and a hard global-FIRMS refresh gate.
CAMS and ocean products remain planned. PurpleAir now has a credential-free,
synthetic interface experiment; a real community-sensor adapter remains
planned and separately permission-gated.

The completed and planned sequence is:

1. **Implemented:** require global NASA FIRMS fire input instead of silently
   publishing a regional-only refresh; source-date and world-region audits
   prevent promotion without actual global rows. A checked global fire
   snapshot still requires a maintainer-provided free map key.
2. **Implemented:** add NOAA CPC gridded daily maximum and minimum temperature
   as the primary non-sparse temperature field while retaining the
   year-qualified particulate observation atlas as a separate product.
3. **Planned:** add globally complete CAMS analysis fields for modeled PM2.5 and smoke
   context without relabeling either one as a ground observation;
4. **Planned:** add NOAA OISST marine-heatwave and Coral Reef Watch reef-heat-stress
   products as a separate ocean theme; and
5. **Interface implemented; observed data planned:** keep PurpleAir in a
   separately generated, permission-gated community-sensor product. The
   current synthetic overlay tests style and lifecycle only.

The pass should not solve sparse observations by treating missing cells as
zero or by blending station, model, satellite, and community-sensor values into
one score. It should show a globally complete field tier underneath
source-separated observations.

## Why the current map is North-America-heavy

The checked
[`anthropocene-particulate-2026.geojson`](../../../../assets.static/anthropocene/anthropocene-particulate-2026.geojson)
and the rendered
`anthropocene-particulate-2026` plate
are behaving consistently with their inputs. The imbalance is an acquisition
and evidence-class problem, not a projection or marker-layout bug.

| Layer | Checked input | Checked audit | Coverage consequence |
| --- | --- | ---: | --- |
| Observed smoke | NOAA HMS analyst polygons | 1,088,261 cell-days in 43,690 cells | A broad North American layer visually dominates the atlas |
| Active fire | CWFIS plus optional FIRMS | 755,252 CWFIS rows and **zero FIRMS rows** | Fire is regional even though the metric profile calls FIRMS global |
| PM2.5 | EPA AirData | 129 cell-days in 67 cells | Regulatory exposure is United-States-only |
| Temperature | GHCN's GSN reference subset | 768 eligible temperature stations | A deliberately sparse reference network leaves large regional gaps |
| Flood and severe weather | NOAA Storm Events | 8,944 located events | These report layers are United-States-focused |

There is also a time-boundary issue. The image is titled **2026 partial year**.
Fires that occurred in Siberia, Australia, or elsewhere during 2025 cannot
appear in a calendar-2026 product even after geographic coverage is repaired.
The 2025 and 2026 products must therefore be generated separately; prior-year
events must not be inserted into the 2026 snapshot.

## Evidence tiers and products

Stage 8b should make the evidence class visible in the schema, layer IDs,
legend, and filenames:

| Tier | Meaning | Examples | Default treatment |
| --- | --- | --- | --- |
| Observations | Regulatory monitors, weather stations, analyst polygons, or satellite detections | GHCNd, FIRMS, HMS, EEA monitors | Glyphs or event cells above fields |
| Analysis fields | Observation-constrained interpolation, reanalysis, or chemical-transport analysis | CPC gridded temperature, CAMS PM2.5, OISST | Filled cells with explicit valid-day coverage |
| Community sensors | Owner-operated low-cost instruments with non-regulatory QA | PurpleAir | Separate opt-in artifact, never merged into regulatory totals |

A single overloaded PNG cannot legibly encode several full global fields.
Treat one year's Anthropocene pass as a bundle of source-separated themes:

- `anthropocene-particulate-YEAR-PROJECTION` retains and expands the existing
  event/station atlas;
- `anthropocene-temperature-YEAR-PROJECTION` combines the non-sparse
  temperature field with station markers;
- `anthropocene-fire-air-YEAR-PROJECTION` combines global fire detections,
  modeled smoke context, modeled PM2.5, and distinct regulatory monitors;
- `anthropocene-ocean-YEAR-PROJECTION` contains marine heatwaves and reef-only
  bleaching heat stress; and
- `anthropocene-purpleair-YEAR-PROJECTION` is an optional community-sensor
  variant of the air-quality theme.

The SVG can retain independently toggleable semantic groups. Each default PNG
should show only the theme named in its filename. This preserves the current
no-composite-score boundary.

## Recommended sources

### Global core

| Indicator | Recommended source and role | Coverage and cadence | Important boundary |
| --- | --- | --- | --- |
| Active fire | [NASA FIRMS area API](https://firms.modaps.eosdis.nasa.gov/api/area/) VIIRS detections; promote from optional to required | Global, 375 m detections, near-real-time and standard-processing products | Thermal anomalies are not necessarily wildfires, burned area, or cause |
| Fire emissions | [CAMS GFAS](https://ads.atmosphere.copernicus.eu/datasets/cams-global-fire-emissions-gfas) as an optional intensity/emissions layer | Global daily 0.1 degree FRP-derived fields | The ADS v1.2 catalogue stops on 3 December 2025; current operational data require the [ECMWF Data Portal](https://forum.ecmwf.int/t/changes-to-cams-global-biomass-burning-emissions-based-on-fire-radiative-power-gfas-data-availability-on-ads-and-ecmwf-data-portal/14325), so this is not the primary 2026 fire feed |
| Temperature observations | Full [GHCN-Daily](https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily), not only GSN | More than 100,000 stations in 180 countries and territories; daily | Coverage and period of record still vary; apply the existing quality and history gates |
| Non-sparse temperature | [NOAA CPC Global Unified Temperature](https://psl.noaa.gov/data/gridded/data.cpc.globaltemp.html) | Global daily 0.5 degree TMAX/TMIN, 1979-present, updated daily, no usage restriction | Observation-interpolated GTS field on a 06Z-to-06Z day; values inside the most recent seven days can change |
| Temperature sensitivity check | [ERA5-Land daily statistics](https://cds.climate.copernicus.eu/datasets/derived-era5-land-daily-statistics) | Global 0.1 degree, 1950-present, daily min/max available | Reanalysis, not a station observation; use for sensitivity testing rather than silently filling CPC |
| Non-sparse PM2.5 | [CAMS global atmospheric-composition analysis](https://ads.atmosphere.copernicus.eu/datasets/cams-global-atmospheric-composition-forecasts) surface PM2.5 | Global 0.4 degree, 2015-present; hourly single-level fields | Observation-constrained model analysis, not a regulatory measurement and not smoke attribution |
| Global smoke context | CAMS organic-matter aerosol optical depth and fire-emission inputs | Global analysis/forecast fields with transported plumes | Label as **modeled organic-aerosol/smoke context**; organic aerosol and CO are indicators, not proof that every affected cell contains wildfire smoke at the surface |
| Satellite aerosol QA | [Sentinel-5P/TROPOMI absorbing-aerosol index](https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel5P.html) | Near-global daily plume observations since 2018 | Detects absorbing aerosols including smoke, dust, and volcanic ash; keep as QA or an explicitly named aerosol layer, never `observed-smoke-days` |
| Regulatory and reference PM2.5 | [OpenAQ API v3](https://docs.openaq.org/about/about) as a discovery/harmonization path, with direct national feeds where practical | Near-real-time and historical global point data | Not complete; filter to approved providers/instruments and honor each [source license](https://docs.openaq.org/resources/licenses) rather than assigning one blanket OpenAQ license |
| Marine heat | [NOAA daily OISST v2.1](https://www.ncei.noaa.gov/products/optimum-interpolation-sst) | Spatially complete global ocean grid, 0.25 degree, September 1981-present, updated daily | Blended/interpolated climate data record; retain its error and ice fields |
| Coral heat stress | [NOAA Coral Reef Watch v3.1](https://coralreefwatch.noaa.gov/product/5km/index.php) | Daily global 5 km, 1985-present, covering about 95% of global reefs | Maps bleaching **heat stress/risk**, not field-observed bleaching or coral mortality |

NASA FIRMS is the direct fix for missing Russian, Australian, African, Asian,
and South American fire detections. Use one canonical FIRMS VIIRS union for the
metric and demote CWFIS to Canadian QA/fallback so the same satellite fire is
not presented as two independent observations. Acquire standard-processed
records when available and near-real-time records only for the unresolved tail;
record sensor, processing class, collection version, acquisition time, and raw
hash. NASA Earth-science data are generally open, with dataset citation strongly
encouraged; see NASA's [data-use and citation guidance](https://www.earthdata.nasa.gov/engage/open-data-services-software/data-use-policy).

No equivalently mature, downloadable global analyst-smoke-polygon feed was
identified. The honest replacement for blank global smoke coverage is a
separate CAMS modeled plume field, with HMS retained as North American analyst
observations. Surface PM2.5, vertically integrated smoke burden, and fire-source
emissions remain three different metrics.

### Regional observation enrichment

The global core prevents blank regions. Regional feeds can then improve the
observation tier without becoming hard dependencies for worldwide coverage.

| Region | Temperature | PM2.5 | Stage 8b role |
| --- | --- | --- | --- |
| Europe | [E-OBS](https://surfobs.climate.copernicus.eu/dataaccess/access_eobs.php) daily 0.1 degree TX/TN and ECA&D station data | [EEA AQ e-Reporting](https://aqportal.discomap.eea.europa.eu/download-data/) current and verified station downloads | E-OBS v33 is complete through 31 December 2025; replaceable provisional monthly 2026 files exist, but its non-commercial research/education terms and mutable running-year products require a separate rights and snapshot gate |
| China | [CMA daily surface climate V3.0](https://m.data.cma.cn/data/detail/dataCode/SURF_CLI_CHN_MUL_DAY_V3.0.html) | Direct CNEMC data where a documented bulk/reuse agreement is obtained; [TAP](https://acp.copernicus.org/articles/22/13229/2022/) 1 km PM2.5 as a modeled regional validation field | Registration, automation, update latency, and redistribution must be verified before promotion; CPC and CAMS provide the no-gap defaults |
| Japan | [JMA AMeDAS](https://www.jma.go.jp/jma/en/Activities/amedas/amedas.html), with about 840 temperature stations and a manual [historical CSV service](https://ds.data.jma.go.jp/gmd/risk/obsdl/) | Ministry of Environment/NIES [air-monitoring portal](https://www.env.go.jp/air/portal.html) and [download archive](https://tenbou.nies.go.jp/download/) | High-value station enrichment; require a stable bulk method and confirmed reuse terms before automated inclusion |
| Australia | GHCNd plus CPC global field | Government monitor providers discovered through OpenAQ, with direct state feeds preferred | FIRMS and CAMS immediately repair fire and PM2.5 context; provider-specific point licenses still need audit |
| Russia/Siberia | GHCNd plus CPC global field | CAMS analysis; licensed national points if later available | FIRMS supplies active fire and CAMS supplies transported-smoke/PM context without depending on a Russian point API |

E-OBS, CMA, and AMeDAS are valuable, but stitching national station networks
together is not the non-sparse solution. Station identifiers, duplicates,
local-day definitions, quality flags, and reuse terms differ. CPC supplies one
globally consistent field while those sources validate or enrich individual
regions.

## Non-sparse global-field option

Use a second normalized dataset rather than injecting modeled values into the
existing positive-observation GeoJSON:

```text
anthropocene-observations-2025.geojson
anthropocene-fields-2025.geojson
anthropocene-observations-2026.geojson
anthropocene-fields-2026.geojson
```

The field dataset should use H3 resolution 3 by default. Its cell scale is a
reasonable match for CPC's 0.5 degree, CAMS's 0.4 degree, and OISST's 0.25
degree grids, gives a nearly uniform-area display, and avoids producing
hundreds of thousands of tiny SVG elements. Resolution remains
profile-configurable.

For every metric/cell, store both the value and its denominator or coverage:

```json
{
  "cpc_temperature_record_high_days": 4,
  "cpc_temperature_valid_days": 365,
  "cams_pm25_high_days": 12,
  "cams_pm25_valid_days": 365
}
```

A zero with positive `valid_days` is an observed/analyzed zero; absence or zero
valid days is unknown. Render covered zero cells in a quiet neutral tone and
missing cells as gaps or a missing-data hatch. This makes coverage genuinely
non-sparse without drawing false events.

Recommended field contracts are:

- sample the CPC TMAX/TMIN field consistently to H3 cells, then count strict
  calendar-day records against all prior valid years from 1979 through the
  preceding year; require at least 30 prior years and keep its 06Z reporting-day
  definition in metadata;
- compute CAMS daily mean surface PM2.5 in physical units, retaining both days
  at or above 15 micrograms per cubic metre (the
  [WHO 2021 24-hour guideline](https://www.who.int/teams/environment-climate-change-and-health/air-quality-and-health/health-impacts/types-of-pollutants))
  and high days at or above 35.5 micrograms per cubic metre (the first
  [U.S. AQI category above 100](https://aqs.epa.gov/aqsweb/documents/codetables/aqi_breakpoints.html));
  make the displayed threshold a profile choice;
- summarize CAMS organic-matter aerosol optical depth as a continuous annual or
  year-to-date burden until a smoke-day threshold is validated against HMS and
  AERONET; do not invent an unvalidated binary smoke count;
- count OISST marine-heatwave days against a fixed 1982–2011 climatology,
  using the documented seasonally varying 90th-percentile threshold and
  [five-consecutive-day event definition](https://doi.org/10.1016/j.pocean.2015.12.014);
  and
- count CRW reef-pixel days at Bleaching Alert Level 1 or higher, preserving
  Degree Heating Week and alert-level metadata.

The normalized schema consequently needs typed measures (`day-count`, `mean`,
`maximum`, `cumulative`, or `category`), floating-point values, `valid_days`,
source/evidence class, grid version, temporal convention, and quality flags.
The existing observation schema can remain v1 while the new field file starts
at v2.

## PurpleAir experiment and optional observed-data pass

Stage 15 implements a 12-plate, default-visible PurpleAir **interface
experiment** for two years and six projections. Its 12 geographic anchors are
synthetic rendering fixtures, not sensors; it contains no PM values,
measurements, or observation claim. The `purpleair-experiment` layer is capped
at 60% opacity, remains exploration-only, and is built only by its explicit
target or `make all-experiments`.

Assuming redistribution and display permission are resolved, a separate
observed-data pass remains worth implementing as an **opt-in community-sensor
artifact**. It adds useful local density in places with participating owners,
but it is not globally uniform and will not by itself repair Siberian,
Chinese, African, or oceanic coverage. Obtain a read key at
[PurpleAir Develop](https://develop.purpleair.com/) and keep it only in the
acquisition environment; the current synthetic experiment neither needs nor
accepts a key.

Acquisition should use a written bulk-data arrangement or a supplied annual
snapshot. PurpleAir's own [API guidance](https://community.purpleair.com/t/api-use-guidelines/1589)
asks clients not to collect several thousand sensors through the per-sensor
historical endpoint. Pin the public outdoor-sensor inventory and historical
measurements separately for 2025 and 2026, including sensor index, coordinates,
location type, channel A/B `cf_1`, humidity, sampling interval, and timestamps.

A defensible first QA contract is:

1. include only public outdoor sensors and preserve relocation/archival
   boundaries as new sensor epochs;
2. reject non-finite/negative readings, relative humidity above 95%, missing
   humidity, either channel above 3,000 micrograms per cubic metre, and samples
   where the A/B absolute difference exceeds 5 micrograms per cubic metre **and**
   relative difference exceeds 70%;
3. require at least 27 of 30 expected two-minute samples for an hourly mean and
   at least 18 valid hours for a local-day mean;
4. apply the U.S. EPA correction to the mean of A and B `cf_1` values,
   `0.524 * PM - 0.0862 * RH + 5.75`, clipping negative corrected values to
   zero; and
5. aggregate valid sensor-day means to the H3 cell median before thresholding,
   so dense neighborhoods do not receive more day-count opportunities merely
   because they contain more sensors.

The EPA correction and cleaning study is documented by
[Barkjohn, Gantt, and Clements](https://amt.copernicus.org/articles/14/4617/2021/)
and the operational equation appears in the EPA
[PM2.5 sensor QAPP](https://www.epa.gov/system/files/documents/2024-06/particulate-matter-pm2.5-sensor-loan-program-qapp-aasb-qapp-004-r1.1.pdf).
It was developed from U.S. collocations. Outside its validation domain, either
require a named regional collocation correction (`strict` mode) or mark the EPA
correction explicitly as an extrapolation (`exploratory` mode). Never merge
PurpleAir counts into EPA, EEA, or other regulatory totals, and never infer
smoke from a PM2.5 exceedance alone.

## Ocean-distress implementation

Coral heat stress is now practical enough to promote from an indefinite future
phase, provided the reef-mask rights are resolved. CRW v3.1 supplies daily 5 km
SST, HotSpot, Degree Heating Week, and Bleaching Alert Area files from 1985 to
the present. Implement
`ocean-heat:coral-bleaching-heat-stress-days` only in reef-containing cells and
describe it as satellite-derived heat stress associated with bleaching risk.
It is not an observation that coral actually bleached.

The production mask should be CRW's reef-containing-pixel mask or another
explicitly licensed global reef extent. The checked Natural Earth reef vectors
are suitable for a small test fixture, not proof of complete global reef
coverage. UNEP-WCMC and Allen Coral Atlas candidates require a separate
redistribution/derived-work review before their mask is checked into this
repository.

Add `ocean-heat:marine-heatwave-days` from OISST in the same phase. Marine
heatwaves provide globally complete ocean context outside coral latitudes and
avoid making reef locations stand in for all ocean distress. Use a fixed
climatology and a published consecutive-day definition, record the OISST error
and ice masks, and keep marine-heatwave and coral-stress layers independently
toggleable because one is global ocean temperature stress and the other is a
reef-specific ecological risk indicator.

A later cryosphere theme can use the
[NOAA/NSIDC Sea Ice Index v4](https://nsidc.org/data/g02135/versions/4) for
Arctic and Antarctic extent/concentration anomalies. Monthly products are more
appropriate for trend context than turning every short-term daily variation
into a local distress event. Ocean acidification, deoxygenation, harmful algal
blooms, and field-observed bleaching remain deferred: their current global
datasets are sparse, lagged, survey-dependent, or do not share a defensible
annual cell-day contract.

## Two-year artifact contract

Each year is an independent reproducibility unit:

| Duration | Required status | Snapshot rule | Comparison warning |
| --- | --- | --- | --- |
| 2025 | `partial_year: false` | Include only source-reporting dates from 1 January through 31 December 2025; pin later retrieval/correction time separately | Complete-year counts are not directly comparable with raw 2026 year-to-date counts |
| 2026 | `partial_year: true` | End each source before its explicit `available_through` date and the profile snapshot boundary | Title every artifact `2026 PARTIAL YEAR` and expose valid-day denominators |

Use year-bearing profiles and filenames; do not let two runs overwrite the same
unqualified path:

```text
assets.static/anthropocene/anthropocene-particulate-2025-profile.json
assets.static/anthropocene/anthropocene-particulate-2025.geojson
assets.static/anthropocene/anthropocene-particulate-2026-profile.json
assets.static/anthropocene/anthropocene-particulate-2026.geojson
assets.static/anthropocene/anthropocene-temperature-2025-profile.json
assets.static/anthropocene/anthropocene-temperature-2025.geojson
assets.static/anthropocene/anthropocene-temperature-2026-profile.json
assets.static/anthropocene/anthropocene-temperature-2026.geojson
assets.generated/cahill-keyes/png/anthropocene-temperature-2025-ck-44-22.png
assets.generated/cahill-keyes/png/anthropocene-temperature-2026-ck-44-22.png
```

Implemented temperature-field targets are:

```sh
make generate-anthropocene-2025
make generate-anthropocene-2026
make generate-anthropocene-years
make generate-anthropocene-year-artifacts
```

The aliases generate both implemented standard themes across all six
projections. The synthetic PurpleAir and bounded water-debris experiments stay
outside these aliases. Future fire/air and ocean themes can join only after an
explicit lifecycle decision. For visual
year-to-year comparisons, a later product should also support a 2025 window
truncated to the same month/day as the 2026 snapshot or render rates per 100
valid days. The canonical 2025 artifact remains complete and the comparison
window must be labelled separately.

## Implementation sequence

### 1. Dual-year and schema plumbing — implemented for particulate and CPC

- Split the single profile path into explicit 2025 and 2026 profiles.
- Add year-bearing normalized and generated filenames plus per-year checksum
  manifests.
- Generalize source statistics instead of hard-coding one field per Stage 8
  source.
- Add evidence class, typed field measures, valid-day denominators, source
  versions, local/UTC reporting-day rules, and partial/complete status.
- Remove the ambiguous unqualified artifact after both year-bearing
  particulate snapshots and compatibility Make aliases are checked.

### 2. Highest-value geographic repairs — CPC implemented; FIRMS gated

- **Implemented:** make a missing/empty FIRMS capture a release error. An
  explicit `regional-development-only` override exists for pipeline debugging
  but cannot pass the global row/date/region audits.
- **Implemented infrastructure:** query FIRMS-advertised availability so
  standard S-NPP data and its NRT tail do not leave a multi-month hole, union
  detections by H3 cell and reporting day, and allow an explicit multi-sensor
  source list. A checked refresh remains pending the required map key.
- Replace GSN-only ingestion with full eligible GHCNd for the observation tier.
- **Implemented:** sample CPC to an explicit resolution-3 global H3 domain,
  retain valid-day denominators, distinguish covered zero from missing, and
  generate complete-2025 and partial-2026 temperature artifacts. Both checked
  products serialize 41,162 cells and contain 11,945 covered land-domain
  cells, with nonzero regional audits outside North America.

### 3. Global atmosphere

- Acquire CAMS analysis PM2.5 and organic-matter aerosol fields for both years,
  never future forecast lead times.
- Add `valid_days`, unit conversion, daily completeness, and source-cycle
  metadata.
- Add approved OpenAQ/EEA/direct-provider regulatory stations with an explicit
  provider and license allowlist.
- Validate modeled PM2.5 against regulatory monitors and modeled smoke context
  against HMS/AERONET without forcing them to agree.

### 4. Optional community sensors

- **Implemented interface only:** synthetic anchors, six-projection style,
  default visibility, 60% opacity, claim boundary, and no credential.
- Implement the real PurpleAir bulk snapshot adapter, observation QA fixture,
  correction modes, local-day aggregation, and separate artifacts.
- Require the permission record and raw manifest before the opt-in target can
  run.

### 5. Ocean fields

- Implement OISST marine-heatwave fixtures and full-year/partial-year
  aggregation.
- Resolve a production reef mask, then add CRW bleaching-heat-stress fixtures
  and reef-only validation.
- Render ocean fields below reef symbols and expose stress source/version in
  SVG metadata.

### 6. Coverage and release QA

Every candidate should emit a machine-readable matrix for North America, South
America, Europe, Africa, northern Asia, East Asia, and Oceania with source rows,
valid days, input records, positive cells, and missing cells. Release checks
should require:

- nonzero global FIRMS rows and expected acquisition-date coverage;
- at least 99% of eligible land H3 field cells with CPC coverage for each
  included day, excluding source-declared missing dates;
- at least 99% of expected CAMS and OISST field cells or an explicit documented
  outage mask;
- nonzero source coverage audits for Siberia, China/Japan, Australia, Europe,
  Africa, and South America without requiring that every region have an event;
- `partial_year: false` for 2025 and `partial_year: true` for 2026;
- separate raw manifests, normalized hashes, source dates, and metric totals for
  each year and theme;
- no observation/model/community-source metric merging;
- explicit zero-versus-missing tests and projection checks on all six maps; and
- a source-rights manifest recording license, attribution, redistribution,
  credentials, and whether only derived H3 values may be checked in.

## Deferred or rejected shortcuts

- Do not use CAL FIRE, CWFIS, HMS, EPA, or NOAA Storm Events as if any were a
  global feed.
- Do not keep FIRMS optional in a product advertised as global.
- Do not label TROPOMI aerosol index, total PM2.5, carbon monoxide, or all CAMS
  organic aerosol as direct observed wildfire smoke.
- Do not use PurpleAir as the default regulatory layer or apply a U.S.-derived
  correction worldwide without an extrapolation flag.
- Do not use E-OBS alone to fill China, Japan, Australia, Russia, or the 2026
  near-real-time gap.
- Do not merge 2025 Siberian fires into the 2026 calendar-year map.
- Do not add coral stress to land H3 cells or describe heat-stress risk as
  field-observed bleaching.
- Do not calculate an Anthropocene severity score from unlike source values.

The first confirmation point is complete: two year-bearing, source-pinned
particulate products and two year-bearing CPC temperature products are
standard, while a global observation refresh cannot silently omit FIRMS.
Promotion of a new global fire snapshot is intentionally still blocked until
a maintainer supplies `FIRMS_MAP_KEY` and the staged rows pass date and region
audits. The synthetic PurpleAir interface is implemented without pretending
that community-sensor observations were acquired. This increment repairs the
year and temperature ambiguity and establishes the field contract needed by
CAMS, a future observed PurpleAir adapter, and ocean products without
prematurely committing to their calibration choices.
