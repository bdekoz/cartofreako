# Anthropocene generation implementation notes

[Documentation index](../index.md) ·
[Generation guide](generation.md) ·
[Generate-pass decisions](generation-methods.md) ·
[Stage 8b enrichment plan](anthropocene-enrichment-plan.md) ·
[Snapshot assets](../assets.static/anthropocene/README.md)

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

- [`generate-anthropocene.cc`](../src.generate/generate-anthropocene.cc), the
  requested generator entry point;
- [`anthropocene-data.h`](../src.generate/anthropocene-data.h), strict profile
  and normalized GeoJSON validation;
- [`anthropocene-generation.h`](../src.generate/anthropocene-generation.h),
  projection, semantic SVG layers, legends, metadata, and verification;
- [`prepare-anthropocene.cc`](../src.generate/prepare-anthropocene.cc), the
  deterministic source normalizer;
- explicit [fetch](../scripts/fetch-anthropocene-data.sh) and
  [prepare](../scripts/prepare-anthropocene-data.sh) scripts plus a
  profile-aware [checksum verifier](../scripts/verify-anthropocene-data.sh);
  and
- a checked [2026 profile](../assets.static/anthropocene/anthropocene-profile.json)
  and checksum-pinned normalized snapshot.

## Duration and snapshot authority

The profile contains the literal default year `2026`, matching the calendar
year when Stage 8 was implemented. Neither generator nor preparer reads the
host clock:

```json
"duration": { "type": "calendar-year", "year": 2026 },
"snapshot": {
  "as_of_utc": "2026-08-05T00:00:00Z",
  "partial_year": true
}
```

Changing `duration.year` is an intentional profile edit, not an automatic New
Year rollover. The normalized GeoJSON must have the same year, snapshot time,
partial-year flag, and H3 resolution or loading fails. Each source also has an
`available_through` value because publication latency differs substantially:
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
| Fire | `fire:active-fire-days` | Day with one or more satellite hotspot detections in the cell | CWFIS by default; NASA FIRMS optional |
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
for the regulatory exposure layer. PurpleAir stays classified as
`excluded-from-default`, not as observed smoke.

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
| [NASA FIRMS area API](https://firms.modaps.eosdis.nasa.gov/api/area/) | **Configured optional global source** | Global MODIS/VIIRS point detections cover Canada and northern Russia; requires a free `FIRMS_MAP_KEY`; standard-processing sources are preferred for analysis when available |
| [Copernicus Sentinel-3 FRP](https://cds.climate.copernicus.eu/datasets/satellite-fire-radiative-power) | **Validation-only / future alternative** | Global fire-radiative-power points and grids add valuable high-latitude cross-checking, but CDS acquisition and a second sensor/product harmonization contract are outside the bounded default |
| [Rosleskhoz operational reports](https://rosleshoz.gov.ru/activity/forest-security-and-protection/fires/operative-information/) | **Administrative validation** | Confirms regions, counts, and affected area in Russia; no stable documented point-vector API was found, so prose reports are not scraped into H3 cells |
| [GWIS](https://gwis.jrc.ec.europa.eu/applications) | **Map-level QA** | Useful global visual comparison, but its active-fire layer substantially derives from FIRMS and is not treated as an independent default observation feed |

The checked snapshot has zero FIRMS input rows, which means **unknown global
FIRMS coverage**, not zero Russian fires. This is explicit in GeoJSON source
statistics and profile source status. Set `FIRMS_MAP_KEY` before a refresh to
obtain global five-day chunks. Active-fire detections are thermal anomalies,
not automatically wildfire incidents, burned area, cause, or impact.

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
state/county/site/date, then deduplicates again as H3 cell-days. In the checked
snapshot, 164 monitor site-days become 129 H3 cell-days across 67 cells.

## Snapshot audit

The checked normalized file has SHA-256
`a3b2fcb3a809710d278ce88aef52ea938fa67e8b900313cf2e5c2ed9c6ddde42`.
Its embedded audit values are:

| Metric | H3 cell-days | H3 cells |
| --- | ---: | ---: |
| Temperature record highs | 1,567 | 255 |
| Temperature record lows | 434 | 136 |
| Precipitation records | 424 | 159 |
| Heavy precipitation | 426 | 147 |
| Active fire | 35,940 | 4,937 |
| Observed smoke | 1,088,261 | 43,690 |
| Flood/heavy-rain events | 1,000 | 359 |
| Severe-weather events | 4,195 | 1,813 |
| EPA PM2.5 exceedance | 129 | 67 |

The source audit records 996 GSN files, 768 temperature-eligible stations,
652 precipitation-eligible stations, 177,365 EPA rows, 29,813 HMS polygons,
23,255 Storm Events details, 8,944 located events, 167 CWFIS files, and 755,252
CWFIS rows. These totals validate the pipeline; they are not normalized by
population, station density, satellite opportunity, reporting practice, or
area.

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

The layer hierarchy is:

```text
anthropocene-background
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

Ordinary generation is offline:

```sh
make generate-anthropocene
make generate-anthropocene-artifacts
```

A deliberate refresh is two-stage:

```sh
make fetch-anthropocene-data
make prepare-anthropocene-data
```

The fetch target validates TAR/ZIP/GZIP containers, discovers the latest
year-specific Storm Events files, records all raw SHA-256 values, tolerates
documented missing CWFIS days, and optionally requests NASA FIRMS. The prepare
target verifies that raw manifest, extracts into a temporary directory, and
writes only an ignored candidate. It never overwrites checked data. After
review, update the checked GeoJSON, its `SHA256SUMS`, profile checksum and
coverage dates, test fixtures, and this audit together.

Supply another already-normalized, matching dataset with Make variables:

```sh
make ANTHROPOCENE_PROFILE=/absolute/path/profile.json \
     ANTHROPOCENE_GEOJSON=/absolute/path/observations.geojson \
     generate-anthropocene-cahill-keyes
```

The generation rule verifies that the selected profile names the selected
GeoJSON and that its declared SHA-256 matches before invoking the generator.

## Tests and limitations

`tests/test-anthropocene-generation.cc` validates profile classifications,
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

The proposed [Stage 8b enrichment plan](anthropocene-enrichment-plan.md)
specifies separate complete-2025 and partial-2026 products, a non-sparse global
field option, required global fire coverage, broader temperature and PM2.5
sources, a permission-gated PurpleAir product, and ocean heat-stress themes.
Those profiles, sources, targets, and artifacts are proposed work; they are not
part of the implemented Stage 8 contract described above.
