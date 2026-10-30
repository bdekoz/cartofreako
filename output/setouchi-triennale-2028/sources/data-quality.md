# Data periods and interpretation

This is a reproducible study edition prepared on 29 October 2026. A new render
does not make every source contemporary. Keep the observation period beside
each exhibited plate. See `generation-plan.json` for each plate's input command
and its specific note.

| Layer | Evidence and limit |
|---|---|
| Earth, Water, bathymetry | Current checked-out Natural Earth physical vectors; geographic/generalized context, not navigation charts |
| Geometry, graticules | Native mathematical projection; no observational period |
| Atmosphere | JAXA refreshed Oct 29; cloud through Oct 29 18:20 UTC, precipitation Oct 26, aerosols/shortwave Oct 15. Acquisition times differ and coverage masks remain |
| Temperature 2026 | NOAA CPC land analysis through Oct 28; partial year, H3 resolution 3, strict record comparison against 1979–2025 with at least 30 valid history years |
| Temperature 2025 | Complete 2025 field from the pinned repository source snapshot; historical baseline files were retained |
| Particulate 2025/2026 | Japan MOE measured PM2.5 (Nov–Dec 2025 / Jan–Sep 2026), China CNEMC via Quotsoft (2025 / through Oct 28 2026), selected Indian CPCB/AirNow monitors, and a separate AirGradient sensor. Earlier smoke/fire/weather/EPA source cutoffs remain |
| Network CDN | cloud_cdn_cache.bkoz manifest Oct 21: 28,243 typed records; 13,140 source coordinates, 1,405 derived references, 13,698 unplotted. Honeycombs and reference triangles use Alpha60 r8 strategies; records are not a verified active-facility census |
| Fiber | TeleGeography 2022 / Aug 5 2026 plus 37,397 ITU public terrestrial fibre routes retrieved Oct 29; Kelly green land lines, 0.5 pt / 75%; schematic |
| Groundstations | Sep 2 2025 source snapshot; location is not proof of current operation |
| Swarm | Dan Da Dan 210/211/212, Sep 4 2025–Mar 4 2026; native Alpha60 AuthaGraph cache maps, separate 1080p/4K and 720p/SD plates. Circle area follows downloader-observation weight, opacity 5%; counts are not unique people |
| Astronomy | Refreshed selected Gaia/NASA/JPL catalogs; curated entries retained. All-sky means coordinate coverage, not a census of every object |
| Orbital technosphere | Sixteen CelesTrak CSV groups retrieved Oct 29, using native seven-day age/six-hour future-epoch filters. NASA SSC validation reference remains historical because its refresh timed out |
| Resource countries | 1,676 records from refreshed primary inputs; World Bank release Oct 8. Forest observations are 2023–2024; food index 2022–2024. Each country's year is retained |
| Coral reef threat | WRI 2011 baseline; 7,215 source cells in 844 composition-preserving honeycomb groups. Three prototypes are supplied. Symbol footprints are not reef area or present-day condition |
| Petroleum | OPEC WOO 2026 outlook, EIA October 2026 estimates/forecasts, ANP 2016–2025, Statistics Canada monthly series, and UNSD latest accepted 2018–2024 throughput |

Celestial and solar calculations use a fixed **2026-10-29 20:00 UTC** instant.
This is a calculation reference, not a claim that the observation occurred at
that time. The Japan ground-sky and orbital-observer products are calculated
for a conceptual Setouchi reference (34.45 N, 133.99 E). Hubble and all-sky
companions retain sky context because a geographic Japan crop is undefined.

Japan crops use the native AuthaGraph projection and the Natural Earth 1:10m
Japan boundary. The two swarm companions use that same geographic viewport,
including neighbouring countries; their physical circle-area scale matches the
world plates. They are not Japan-only totals. Geographic Japan coastline strokes are 1 pt. Country statistics use 1:110m polygons. No national value is
claimed to resolve an individual island. Resource fills are fully opaque, with distinct named izzi-hue palettes; petroleum
uses browns. Temperature highs use shared 1–5, 6–10, 11–20, 21–40, 41–80,
81+ day classes. Missing data are not zero. The geographic locator is not a confirmed venue.

## Particulate interpretation

Teal rings record available monitor days, orange crosses days when any eligible
monitor daily mean exceeded 35 micrograms per cubic metre. At least 18 valid
hours are required. AirGradient sensor counts remain separate. Dates and
coverage differ; these are not national averages or comparable annual rates.
Sources and country counts: docs/pages/data/anthropocene-particulate.md.
Japan covers 1,076 stations in November–December 2025 and 1,095 in
January–September 2026; China 1,686 / 1,345 stations; India 16 selected
government locations plus one separate AirGradient sensor. These are unequal
observation windows. Numeric Japanese 999x status codes are excluded. Extreme
provider-reported daily means are retained in a separate operator-review ledger;
passing completeness checks does not certify instrument accuracy.

Atmosphere uses foreground land outlines with fill opacity 0 and opaque pink
cloud-fraction classes. Observations remain visible across land and sea. Blue precipitation
excludes observed zeros; those remain in the data. Rose aerosol and gold
shortwave outlines avoid mixed-color fills. The Japan cloud snapshot is nighttime
and has no positive daytime retrievals; this is not evidence of clear skies.

## Petroleum checks

All OPEC workbooks, worksheets, nonempty cells, display formats, merged ranges
and notes are retained in the normalized evidence files. The country index is
a navigation aid, not a replacement for the worksheet's component and scenario
headings. OPEC WOO is not the Annual Statistical Bulletin. All 209 named country
and territory entries are retained, including those with regional coverage
only. Seventeen have separately indexed numeric cells; 14 have a suitable total
liquids series for the 2030 projection plate. Other country values are missing,
not inferred from regional totals.

The EIA import preserves crude production, all-liquids production, capacity,
surplus capacity and unplanned outages as separate measures. The 2025 map uses
annual historical/estimated all-liquids production. It includes 36 countries;
Bahrain uses a point because the 1:110m geometry lacks its polygon. EIA covers
Russia, Brazil, Canada, Venezuela, Mexico and the USA independently of OPEC.
National-source corroboration is additionally available for Brazil, Canada
and the USA. No newer Russian, Venezuelan or Mexican government dataset was
ingested; EIA is the integrated independent source for those countries.

Canada's 2025 crude and equivalent-products totals sum to 310,930,332 cubic
metres, consistent with Statistics Canada's rounded 310.9 million publication.
ANP's basin sum is 1,376,065.401 thousand barrels in 2025 (about 3.770 million
barrels/day); EIA's 4.65 million all-liquids figure includes additional
components. ANP metadata has stale resource-name/year text; units, table title
and actual CSV years were checked and the original metadata retained.

The former UNdata `DownloadHandler.ashx` refinery export returns 404. A moved
handler was not confirmed. The official alternative is:

https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY,/A..GR.086/?startPeriod=2018&format=csv

`GR` with transaction `086` is total refinery throughput, not gross refinery
output. `TN` and multiplier `3` mean thousand metric tonnes. The new repository
normalizer validates these dimensions, rejects duplicate country/year rows,
and resolves names from the official structure. Its 689 rows exactly match the
task-prepared extract; Japan 2024 is 120,404.978 thousand metric tonnes.

## Review before the final exhibition edition

1. Review the implemented PM2.5 source joins and coverage. China uses a 2022
   station-coordinate inventory; Japan needs earlier 2025 backfill; India is a
   selected urban sample. PurpleAir requires an authorized key and pilot budget.
2. Refresh the dated infrastructure inventories and review what constitutes an
   active facility before representing those maps as current in 2028.
3. Refresh source releases and translate final labels 6–8 weeks before opening.
   Have a domain reader check petroleum definitions and national/regional scope.
4. Review OPEC/JAXA/publication attribution and excerpt terms for the intended
   public catalog. No public distribution or upload was performed here.
5. Check print colour, line weights and label size on physical proofs. Screen
   previews and dimension checks do not replace a printer's proof.

The Energy Institute page and Austrian WKO report were investigated but their
automated downloads failed; their numerical content was not added to the maps.
WKO source context is recorded separately. The NASA SSC reference timeout did
not replace the successfully downloaded CelesTrak groups with stale data.
