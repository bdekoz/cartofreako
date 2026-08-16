# Anthropocene generation implementation notes

[Documentation index](../../../../index.md) ·
[Generation guide](../../getting-started/generation.md) ·
[Generate-pass decisions](../../getting-started/generation-methods.md) ·
[Stage 12 implementation](../../../development/stage-12.md) ·
[Stage 8b enrichment plan](enrichment-plan.md) ·
[Stage 13 source expansion review](source-expansion-stage-13.md) ·
[Snapshot assets](../../../../assets.static/anthropocene/README.md)

## Current pass status

The four standard Anthropocene pass IDs are current **accepted experimental**
products. Maturity and lifecycle are separate: each remains a **standard**,
default-generated, release-eligible pass across all six projections.

| Pass ID | Current role | Lifecycle | Maturity |
| --- | --- | --- | --- |
| `anthropocene-particulate-2025` | Complete-year source-separated observation atlas | Standard; default-generated | Accepted experimental |
| `anthropocene-particulate-2026` | Explicitly partial-year source-separated observation atlas | Standard; default-generated | Accepted experimental |
| `anthropocene-temperature-2025` | Complete-year CPC temperature field | Standard; default-generated | Accepted experimental |
| `anthropocene-temperature-2026` | Explicitly partial-year CPC temperature field | Standard; default-generated | Accepted experimental |

The former unqualified `anthropocene` pass was removed. Compatibility Make
aliases build the year-bearing particulate pair; they do not recreate an
ambiguous unqualified artifact.

Two additional families are implemented as **exploration only** and remain
outside default generation and release: the synthetic, default-visible
PurpleAir interface review and the bounded water-debris depth-station
experiment. They are available through their explicit targets and
`make all-experiments`.

The [pass-status manifest](../../../../contracts/pass-status-v1.json) records
this classification and its claim boundaries. Acceptance applies to the
current visual/research implementation, source metadata, title hierarchy, and
field treatment. It does not turn observations into causal attribution,
remove either 2026 partial-year qualifier, authorize unreviewed source
refreshes, or promote Stage 15 atoll, PurpleAir, or water-debris research
products.

## Outcome and claim boundary

Stage 8 is feasible as a source-separated observation atlas. It is not
feasible as a defensible map that attributes each individual fire, flood,
record, smoke plume, or air-quality episode to anthropogenic climate change.
Event attribution needs event-specific counterfactual analysis; the IPCC
assesses changes in the frequency and intensity of classes of extremes rather
than assigning a universal causal fraction to every mapped observation. See
[IPCC AR6 WGI Chapter 11](https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-11/).

The implemented pass therefore maps human-relevant climate and weather
indicators under the requested **Anthropocene** title while retaining their
distinct observational meanings. It computes no composite severity or
attribution score. The SVG footer and embedded metadata state that boundary.

The implementation consists of:

- [`generate-anthropocene-particulate.cc`](../../../../src.generate/generate-anthropocene-particulate.cc),
  the particulate generator entry point;
- [`anthropocene-particulate-data.h`](../../../../src.generate/anthropocene-particulate-data.h), strict profile
  and normalized GeoJSON validation;
- [`anthropocene-particulate-generation.h`](../../../../src.generate/anthropocene-particulate-generation.h),
  projection, semantic SVG layers, legends, metadata, and verification;
- [`prepare-anthropocene-particulate.cc`](../../../../src.generate/prepare-anthropocene-particulate.cc), the
  deterministic source normalizer;
- [`prepare-anthropocene-temperature.cc`](../../../../src.generate/prepare-anthropocene-temperature.cc),
  the CPC daily-grid to global-H3 field normalizer;
- [`generate-anthropocene-temperature.cc`](../../../../src.generate/generate-anthropocene-temperature.cc),
  the complete-2025/partial-2026 Stage 8b field renderer;
- explicit [fetch](../../../../scripts/fetch-anthropocene-particulate-data.sh) and
  [prepare](../../../../scripts/prepare-anthropocene-particulate-data.sh) scripts plus a
  profile-aware [checksum verifier](../../../../scripts/verify-anthropocene-particulate-data.sh);
  and
- checked [2025](../../../../assets.static/anthropocene/anthropocene-particulate-2025-profile.json)
  and [2026](../../../../assets.static/anthropocene/anthropocene-particulate-2026-profile.json)
  profiles with checksum-pinned normalized snapshots.

## Duration and snapshot authority

The two profiles contain literal years and snapshot boundaries. Neither
generator nor preparer reads the host clock:

```json
{
  "2025": { "data_through": "2025-12-31", "partial_year": false },
  "2026": { "as_of_utc": "2026-08-05T00:00:00Z", "partial_year": true }
}
```

Changing `duration.year` is an intentional profile edit, not an automatic New
Year rollover. The normalized GeoJSON must have the same year, snapshot time,
partial-year flag, and H3 resolution or loading fails. Each source also has an
`available_through` value because publication latency differs substantially
in the partial edition:
EPA AirData in this capture ends May 31, Storm Events ends April 30, HMS ends
August 3, and the captured GSN and CWFIS inputs extend through August 4.

Counts use the source's reporting day. EPA uses `Date Local`; HMS uses its UTC
ordinal date; station records use the station daily record; Storm Events uses
reported begin/end calendar dates; and fire feeds use their acquisition or
report date. Every parser excludes a reporting date on or after the profile's
UTC snapshot boundary, including when a refreshed annual archive contains
newer rows. The atlas does not imply that unlike source days are synchronized
to the same instant.

## Classification and implemented layers

The normalizer aggregates positive observations into resolution-4 H3 cells.
Each property is a count of unique source-reporting days in that cell. Multiple
monitors, detections, polygons, or reports on the same day do not inflate the
cell-day count.

| Classification | Metric ID | Definition | Default source |
| --- | --- | --- | --- |
| Climate records | `climate-records:temperature-record-high-days` | GSN station day whose TMAX strictly exceeds every prior valid value for that calendar day | NOAA GHCN/GSN |
| Climate records | `climate-records:temperature-record-low-days` | GSN station day whose TMIN strictly falls below every prior valid value for that calendar day | NOAA GHCN/GSN |
| Hydrology | `hydrology:precipitation-record-days` | GSN station day whose precipitation strictly exceeds every prior valid value for that calendar day | NOAA GHCN/GSN |
| Hydrology | `hydrology:heavy-precipitation-days` | At least 10 mm and above that station/month's 1991–2020 wet-day 95th percentile | NOAA GHCN/GSN |
| Fire | `fire:active-fire-days` | Day with one or more satellite hotspot detections in the cell | Checked v1: CWFIS; new global refresh: NASA FIRMS required, CWFIS regional QA |
| Atmosphere | `atmosphere:observed-smoke-days` | Day an HMS analyst polygon covers the cell center, with a centroid fallback for sub-cell polygons | NOAA HMS |
| Hydrology | `hydrology:flood-event-days` | Located Storm Events day classified as flood, heavy rain, or excessive rainfall | NOAA Storm Events |
| Severe weather | `severe-weather:extreme-event-days` | Located day represented in the NOAA Storm Events database | NOAA Storm Events |
| Air-quality exposure | `air-quality-exposure:pm25-exceedance-days` | Unique regulatory monitor day with PM2.5 AQI strictly greater than 100 | **EPA AirData** |

The profile controls enablement, scales, colors, and shapes. PM2.5 exposure is
enabled by default but remains visually and semantically distinct from smoke:
it is a cross-square in the `air-quality-exposure` group, while HMS smoke is a
ring in `atmosphere`. An elevated PM2.5 measurement does not by itself identify
smoke, and an overhead smoke polygon does not assert ground-level PM2.5
exposure.

PurpleAir is consequently not the default PM2.5 source. Its low-cost sensor
network can be useful for exploratory local analysis, but PM readings are not
smoke attribution, API/licensing terms require separate review, and the user
confirmed [EPA AirData](https://aqs.epa.gov/aqsweb/airdata/download_files.html)
for the regulatory exposure layer. The Stage 15 PurpleAir interface experiment
is exploration-only and uses 12 synthetic rendering anchors, no sensor IDs or
measurements. Its layer is visible by default at 60% opacity so the proposed
style can be reviewed. A future observed-data adapter needs a read key from
[PurpleAir Develop](https://develop.purpleair.com/), a reviewed source-use
receipt, and explicit correction/sensor metadata. The key belongs only in the
acquisition environment. PurpleAir remains excluded from the standard
particulate data and is never relabeled as observed smoke.

## Record and precipitation eligibility

The source normalizer reads the fixed-width
[GHCN-Daily GSN archive](https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily).
It rejects `-9999` and any value with a nonblank GHCN quality flag. A station
element qualifies only when at least 30 prior years contain at least 183 valid
days. This follows the completeness intent of NCEI's
[Daily Weather Records](https://www.ncei.noaa.gov/news/daily-weather-records-data-tool)
while keeping the calculation reproducible from the bounded GSN files.

For each qualifying station and month/day, current values are compared with
all prior valid station history. Comparisons are strict, so ties are not new
records. TMAX defines the high layer and TMIN defines the low layer. The pass
does not merge warm-night records into highs or cold-day records into lows.

Heavy precipitation uses positive 1991–2020 PRCP values as the station/month
wet-day sample, the nearest-rank 95th percentile, and a separate 10 mm minimum.
That metric and a new all-history daily precipitation record may overlap; they
remain independently toggleable rather than being deduplicated into a score.

## Fire-source evaluation: Canada and northern Russia

CAL FIRE is useful for named California incidents but is geographically too
narrow for the global pass. It remains `supplemental-not-default`.

The selected fire-source roles are:

| Source | Role | Evaluation |
| --- | --- | --- |
| [Canadian Wildland Fire Information System daily hotspots](https://cwfis.cfs.nrcan.gc.ca/downloads/hotspots/) | **Included default** | Public daily CSVs, no credential, useful Canada and North America coverage; the checked snapshot includes 167 available reporting files through August 4 |
| [NASA FIRMS area API](https://firms.modaps.eosdis.nasa.gov/api/area/) | **Required for a new global refresh** | Global VIIRS point detections cover every world region; requires a free `FIRMS_MAP_KEY`; the fetcher joins advertised standard-processing availability to the NRT tail |
| [Copernicus Sentinel-3 FRP](https://cds.climate.copernicus.eu/datasets/satellite-fire-radiative-power) | **Validation-only / future alternative** | Global fire-radiative-power points and grids add valuable high-latitude cross-checking, but CDS acquisition and a second sensor/product harmonization contract are outside the bounded default |
| [Rosleskhoz operational reports](https://rosleshoz.gov.ru/activity/forest-security-and-protection/fires/operative-information/) | **Administrative validation** | Confirms regions, counts, and affected area in Russia; no stable documented point-vector API was found, so prose reports are not scraped into H3 cells |
| [GWIS](https://gwis.jrc.ec.europa.eu/applications) | **Map-level QA** | Useful global visual comparison, but its active-fire layer substantially derives from FIRMS and is not treated as an independent default observation feed |

The checked snapshot has zero FIRMS input rows, which means **unknown global
FIRMS coverage**, not zero Russian fires. This is explicit in GeoJSON source
statistics and profile source status. A new global refresh now fails without
`FIRMS_MAP_KEY`, without at least 95% of expected FIRMS reporting dates, or
without rows in each audited world region. The explicit
`ANTHROPOCENE_REGIONAL_DEVELOPMENT_ONLY=1` override is for local pipeline
debugging, not promotion. Active-fire detections are thermal anomalies, not
automatically wildfire incidents, burned area, cause, or impact.

## Smoke, flood, severe weather, and EPA methods

The [NOAA Hazard Mapping System](https://www.ospo.noaa.gov/products/land/hms-smoke/)
annual shapefile supplies analyst-drawn smoke polygons. H3 center containment
is used for ordinary polygons. Polygons smaller than a resolution-4 cell can
produce an empty fill; those are assigned to their centroid cell so a valid
small plume is not erased. Density labels remain source metadata but are not
converted into ground exposure.

The [NOAA Storm Events Database](https://www.ncei.noaa.gov/stormevents/)
details and locations files are joined by event ID. Location-table points and
valid begin/end coordinates are both accepted; set semantics remove duplicates.
Every calendar day from begin through end is counted. Events without usable
coordinates are excluded, so the layer maps located reports rather than the
database's full administrative total.

The EPA normalizer reads parameter `88101` daily data, keeps rows with numeric
AQI greater than the profile's exclusive threshold of 100, deduplicates
state/county/site/date, then deduplicates again as H3 cell-days.

## Snapshot audit

The complete-2025 and partial-2026 normalized files have SHA-256 values
`ecd4b11bab4faa9895522dbfe75436ef66820f53620bf0c5f6fc7404e9f5426b`
and
`a3b2fcb3a809710d278ce88aef52ea938fa67e8b900313cf2e5c2ed9c6ddde42`.
Their embedded H3 cell-day totals are:

| Metric | 2025 complete | 2026 partial |
| --- | ---: | ---: |
| Temperature record highs | 4,129 | 1,567 |
| Temperature record lows | 714 | 434 |
| Precipitation records | 1,757 | 424 |
| Heavy precipitation | 1,491 | 426 |
| Active fire | 127,392 | 35,940 |
| Observed smoke | 1,794,158 | 1,088,261 |
| Flood/heavy-rain events | 7,135 | 1,000 |
| Severe-weather events | 21,694 | 4,195 |
| EPA PM2.5 exceedance | 1,240 | 129 |

Both source audits record zero FIRMS rows. These totals validate the bounded
pipeline; they are not normalized by population, station density, satellite
opportunity, reporting practice, area, or unequal time coverage. Raw complete
and partial counts are not a direct year-to-year rate comparison.

## Additional resource types evaluated

The original list is useful but not exhaustive. The following classifications
preserve scientifically meaningful additions without silently expanding this
phase:

| Candidate | Suggested classification | Stage 8 decision |
| --- | --- | --- |
| EPA PM2.5 exceedance days | `air-quality-exposure` | **Implemented and enabled by default**, distinct from smoke |
| Weekly drought severity/exposure | `hydrology:drought-exposure-weeks` | Valuable future layer using the [U.S. Drought Monitor](https://droughtmonitor.unl.edu/Data.aspx) or a global drought product; weekly polygon/raster semantics do not match a daily point count without another contract |
| Tropical-cyclone exposure days | `severe-weather:tropical-cyclone-exposure-days` | Valuable future subtype using [IBTrACS](https://www.ncei.noaa.gov/products/international-best-track-archive); requires track buffering, wind-radius choices, and duplicate handling with Storm Events |
| Warm-night and cold-day records | `climate-records` subtypes | Straightforward future profile metrics, deliberately not merged into the requested high/low meanings |
| Heatwave/cold-spell duration | `climate-extremes` | Better derived from a gridded baseline with consecutive-day logic; separate raster phase |
| Tide-gauge or sea-level anomalies | `ocean-heat-and-level` | Scientifically useful measurement series but not an extreme-event day layer |
| Coral bleaching stress days | `ocean-heat:coral-bleaching-stress-days` | **Confirmed separate phase**; see below |

### Coral bleaching is a separate phase

NOAA Coral Reef Watch's gridded products are scientifically appropriate for
bleaching heat stress, but a sound implementation needs reef masks, marine
raster sampling, time-series accumulation, product/version selection,
coverage-quality flags, and a visual grammar that does not imply conditions in
open-ocean cells. The profile records the requested metric as `separate-phase`.
It is absent from normalized features and SVG metric groups, and verification
fails if a Stage 8 coral layer appears. A future phase should begin with
[NOAA Coral Reef Watch](https://coralreefwatch.noaa.gov/product/5km/index_5km_bse-365d.php)
and a reef-only validation fixture.

## Rendering and SVG contract

The generator projects H3 centers with the same six production projection
implementations and places colored, shape-distinct glyphs in physical page
space. Broad smoke rings render first; fire, hydrology, severe weather,
air-quality exposure, and climate records render above them. Counts affect
opacity logarithmically up to each profile `scale_days` value. This is a
visibility scale, not a scientific transformation.

Stage 13 doubles the observation-atlas plate heading from `0.21` to `0.42`
page units. Its existing per-count marker opacity remains source-specific;
this compatibility atlas is not silently restyled as the non-sparse field.

The layer hierarchy is:

```text
anthropocene-particulate-background
terrestrial-land
atmosphere / observed-smoke-days
fire / active-fire-days
hydrology / precipitation-record-days, heavy-precipitation-days,
            flood-event-days
severe-weather / extreme-weather-event-days
air-quality-exposure / pm25-exceedance-days
climate-records / temperature-record-high-days,
                  temperature-record-low-days
legend-and-provenance
coverage-note
```

Every marker carries its H3 index, metric ID, family, shape, and raw day count.
Root metadata records the profile, year, snapshot, H3 resolution, normalized
SHA-256, layer totals, explicit PM2.5/smoke separation, and deferred coral
phase. SVG generation reopens the output and verifies its view box, complete
layers, marker count, provenance, finite numbers, label font, PM2.5/smoke
shape distinction, and absence of a coral group.

## Acquisition and refresh

The particulate observation family is offline and explicit:

```sh
make generate-anthropocene-particulate
make generate-anthropocene-particulate-artifacts
```

The unqualified `generate-anthropocene` and
`generate-anthropocene-artifacts` targets build both year-bearing particulate
and CPC temperature families. The former `*-atlas` names are compatibility
aliases for the particulate pair.

A deliberate refresh is two-stage:

```sh
make fetch-anthropocene-particulate-data
make prepare-anthropocene-particulate-data
# equivalent authorized wrapper for the complete two-step refresh
read -rsp 'NASA FIRMS MAP_KEY: ' FIRMS_MAP_KEY; printf '\n'
export FIRMS_MAP_KEY
make generate-authorized-external EXTERNAL_PASSES=nasa-firms
unset FIRMS_MAP_KEY
```

The fetch target validates TAR/ZIP/GZIP containers, discovers the latest
year-specific Storm Events files, records all raw SHA-256 values, tolerates
documented missing CWFIS days, and requires NASA FIRMS for a global refresh.
It reads the FIRMS availability endpoint before requesting five-day chunks and
does not print the map key. The prepare target verifies that raw manifest,
extracts into a temporary directory, audits FIRMS dates and regions, and writes
only an ignored candidate. It never overwrites checked data. After
review, update the checked GeoJSON, its `SHA256SUMS`, profile checksum and
coverage dates, test fixtures, and this audit together.

The wrapper intentionally does not invoke an Anthropocene artifact target.
Rendering a prepared candidate before profile/hash/source review would bypass
its promotion gate. Request the free key from the official
[NASA FIRMS MAP_KEY page](https://firms.modaps.eosdis.nasa.gov/api/map_key/);
the complete handling procedure is in the
[Stage 15 plan](../../../development/stage-15.md#getting-and-using-a-nasa-firms-map_key).

Supply another already-normalized, matching dataset with Make variables:

```sh
make ANTHROPOCENE_PARTICULATE_PROFILE_2026=/absolute/path/profile.json \
     ANTHROPOCENE_PARTICULATE_GEOJSON_2026=/absolute/path/observations.geojson \
     generate-anthropocene-particulate-2026
```

The generation rule verifies that the selected profile names the selected
GeoJSON and that its declared SHA-256 matches before invoking the generator.

## Tests and limitations

`tests/test-anthropocene-particulate-generation.cc` validates profile classifications,
EPA/smoke separation, fire-source roles, coral deferral, exact snapshot audit
values, H3 centers and resolution, metric sums, and sample projection bounds
on all six projections. `make check` also verifies the normalized SHA-256.

Important remaining limitations are:

- the snapshot is partial-year and source publication dates differ;
- GSN is a sparse reference network, not all global stations;
- monitoring and event-report density are geographically uneven;
- HMS smoke aloft and EPA surface PM2.5 describe different phenomena;
- CWFIS and FIRMS hotspots can include non-wildfire thermal anomalies;
- Storm Events is U.S.-focused and only located reports are mapped;
- H3 cell-day aggregation loses sub-cell extent, duration, density, and
  within-day timing;
- no population exposure, damages, emissions, burned area, return period, or
  trend normalization is inferred; and
- none of the layers alone establishes anthropogenic causation.

## Stage 8b coverage work

The current snapshot audit explains the North American visual bias: FIRMS
contributed zero rows, CWFIS and HMS are regional, EPA AirData is
United-States-only, and the temperature layer uses the intentionally sparse
GSN subset. This is a source-coverage limitation rather than a projection
failure.

The first [Stage 8b enrichment](enrichment-plan.md) increment is implemented
alongside, rather than blended into, the year-qualified particulate atlas.
NOAA CPC daily TMAX/TMIN fields are normalized onto every resolution-3 global
H3 cell with valid-day denominators and distinct covered-zero/missing
semantics. The complete-2025 field compares strict daily records with
1979–2024; the partial-2026 field runs through August 4 and compares with
1979–2025. Both serialize 41,162 global cells and cover the same 11,945-cell
land-analysis domain. The checked totals are 178,896 high and 59,806 low
record cell-days in 2025, and 105,041 high and 40,943 low record cell-days in
2026. Region gates confirm coverage in Europe, Siberia, China/Japan,
Australia/Oceania, Africa, and South America as well as North America.
H3 rings are split explicitly at the antimeridian before projection. In the
Cahill-Keyes render, 21 of 11,945 covered cells would otherwise close across
an outer topology cut; those cells use a small centered hexagon and the SVG
records the fallback count on each affected path. The other five projections
need no fallback cells.

All data-bearing high and low field paths are multiplied by the profile's
`display.data_graphic_opacity = 0.60`; covered-zero context and legend
swatches retain their own opaque reference styling. The plate heading is
twice its prior size (`0.34` rather than `0.17` page units). Root metadata
records `data-graphic-opacity="0.6"` and `data-title-scale="2"`, and the
generator self-check requires both.

Generate both years by default, or either explicit year, across all six
projections with:

```sh
make generate-anthropocene
make generate-anthropocene-2025
make generate-anthropocene-2026
make generate-anthropocene-years
```

The global FIRMS gate is also implemented, but neither checked particulate
snapshot is retroactively relabelled: both have zero FIRMS rows. A new global
fire snapshot cannot be promoted until credentialed raw acquisition passes its
audits. The
[Stage 13 source review](source-expansion-stage-13.md)
prioritizes full GHCN-Daily and OpenAQ, keeps CAMS/MAIAC in separately labeled
modeled or satellite-aerosol products. Stage 15 now supplies a synthetic,
default-visible PurpleAir interface experiment without claiming sensor data;
a real supplemental snapshot still requires a bounded scope or
provider-arranged bulk extract. Its bounded water-debris experiment likewise
renders only five reviewed 2018 depth stations and remains exploration-only.
OISST/Coral Reef Watch ocean themes remain planned.
