# Particulate data enrichment: Japan and Asia-28

Research and implementation date: 29 October 2026. The investigation below
led to implemented Japan, China and selected Indian PM2.5 layers in both years
of the Setouchi atlas. Original EPA AQI, smoke and other metrics are preserved.
The maintained [source and methodology page](../pages/data/anthropocene-particulate.md)
records the actual coverage, exclusions, commercial-source findings and limits.

## Finding and recommendation

**Japan has useful official particulate monitoring. The weak Japan coverage in
the original plates was primarily an input-selection problem. Start with Japanese
government measurements; use PurpleAir as a tested supplement.** The existing
`anthropocene-particulate` profiles combine several distinct environmental
indicators. Their US EPA PM2.5 and North American smoke layers do not describe
Japan, and fire detections are not surface PM2.5 concentrations. A blank Japan
cell is not evidence of clean air or absence of monitoring.

Recommended order:

1. NIES finalized station measurements for historical Japanese comparisons.
2. Ministry of the Environment's Sora-mame provisional hourly PM2.5 for recent
   dates, including 2026; preserve its provisional status.
3. OpenAQ plus selected national sources for Asia-28, with explicit country and
   station coverage audits and upstream deduplication.
4. PurpleAir outdoor sensors where a coverage inventory demonstrates added
   information and local comparisons support their calibration.
5. CAMS modeled fields for a separate regional context plate. Never silently
   replace missing ground measurements with model values.

## A successful Setouchi-area retrieval

One bounded request to the official Sora-mame API retrieved **Kagawa prefecture,
September 2026, PM2.5**. This is a working route, not a proposed endpoint:

```text
https://soramame.env.go.jp/soramame/api/data_search?Start_YM=202609&End_YM=202609&TDFKN_CD=37&REQUEST_DATA=PM2_5
```

The response was HTTP 200, `application/json;charset=SJIS`, 956,149 bytes, and
12,960 station-hour slots. It contains 18 station codes, but only **12 stations
with numeric PM2.5 readings**: 8,627 numeric rows, 4,320 empty strings, and 13
`-` tokens. Six all-empty station series must not be reported as PM2.5 coverage.
Numeric values include negatives (range -7 to 43); retain them with quality
flags and consult official handling rules before aggregation. Neither missing
strings nor suspect values should be silently converted to zero.

The local retrieval receipt,
`output/setouchi-triennale-2028/sources/research/particulate/kagawa-api-probe.json`,
records the request, digest and per-station counts. The adjacent raw response is
preserved for inspection. This sample establishes usable nearby observations;
it does not establish complete Setouchi island or national coverage.

The [official API manual](https://soramame.env.go.jp/data/apiManual/3.html)
documents `Start_YM`, optional `End_YM`, required prefecture code `TDFKN_CD`,
optional station codes `SKT_CD`, and `REQUEST_DATA=PM2_5` in µg/m³. It states
that API access does not require personal information. Keep station codes as
strings. Observed rows have `SKT_CD`, `SKT_DATE`, `SKT_TIME` and `PM2_5`;
hours run 01–24. Normalize Japan time and hour-ending intervals explicitly.

## Source comparison

| Source | Useful evidence | Access and time coverage | Role in these maps |
|---|---|---|---|
| NIES Environmental Observatory | Finalized government station observations and station metadata | Downloadable hourly archives from FY2009 onward; older hourly data by request. Latest posted release is FY2024, published 20 October 2026 | Preferred historical Japan backbone |
| MOE Sora-mame | Recent provisional station PM2.5, with pollutant-specific missingness | Public JSON API; all 47 prefectures ingested for Nov–Dec 2025 and Jan–Sep 2026 | Implemented Japan observations, distinctly labeled provisional |
| PurpleAir | Community optical sensor observations | Account/read key and points budget; history is sensor-specific | Optional neighborhood supplementation after inventory and calibration |
| OpenAQ | Harmonized measurements from contributing providers | API v3 needs a key; the public AWS bulk archive does not | Implemented selected Indian CPCB/AirNow monitors and a separate AirGradient sensor; broader Asia-28 inventory remains |
| EANET | Regional background and deposition-monitoring evidence | Public summary downloads; finer time series require registration; restrictive republication terms | Background corroboration, conditional on variables and permission |
| CAMS EAC4 | Global modeled/assimilated particulate mass | 0.75-degree grid, 2003–2025 currently listed; monthly product and underlying 3-hourly fields | Separate modeled regional context |

NIES provides monthly/annual, hourly and station files, including coordinates.
The site explicitly allows reuse with attribution and publishes correction
notices. Download only the required prefecture/year files first. Japanese fiscal
years cross calendar years: FY2024 covers April 2024–March 2025. It cannot alone
supply a complete calendar-2025 plate; FY2025 was not listed as released at this
check. Record revisions as well as acquisition dates. [NIES downloads and release log](https://tenbou.nies.go.jp/download/)

For Sora-mame, a public API is not itself a blanket redistribution license for
every prefectural station. Check station-owner reuse conditions and the current
download guidance before packaging a public dataset. Use NIES finalized files
when they become available, retaining the original provisional receipt and a
revision comparison. [Sora-mame downloads](https://soramame.env.go.jp/download)

## Would PurpleAir be better?

**Potentially for an uncovered locality; not established as a better Japan-wide
baseline.** No authenticated Japan/Setouchi PurpleAir inventory was obtained in
this pass, so there is no verified count of active outdoor sensors or usable
2025/2026 station-days. A crowded map screenshot cannot establish those counts.

PurpleAir's official documentation describes a points-based API, one million
initial points for new accounts, single-sensor historical requests and
averaging-dependent request limits. History across the network begins in 2016,
but an individual sensor may have a much shorter record. Map AQI conversions
are not automatically included in raw API responses. No account was created,
no paid calls were made, and no private sensors were queried. [PurpleAir API overview](https://community.purpleair.com/t/about-the-purpleair-api/7145)

Proposed pilot: inventory public outdoor sensors in Japan and the Setouchi
bounding box; count freshness, valid hours, downtime and year coverage before
downloading full histories. Retain sensor model, A/B channels, humidity, field
definition and calibration version. Compare with nearby official monitors
across seasons, holding out stations or dates from calibration evaluation.
Keep raw and corrected results separately. The published US-wide PurpleAir
correction is useful methodology, but its transfer to Japanese aerosol mixtures
needs evaluation. [Barkjohn et al., 2021](https://amt.copernicus.org/articles/14/4617/2021/)

## Asia-28 means the project's existing region

Use `region-rankings-20260925-v1`, not a newly invented geographic definition.
The checked local file is
`/home/bkoz/src/alpha60-results/data/region-ranking-definitions.json`; its
embedded definition digest is
`876acd82b3b47ae56c4b1deeca41fb39d88c64ba100f1edf8f0047962d90810a`.
The 28 ISO3 entries are:

```text
AFG BGD BRN BTN CHN HKG IDN IND IRN JPN KHM KOR LAO LKA
MAC MDV MMR MNG MYS NPL PAK PHL PRK SGP THA TLS TWN VNM
```

Hong Kong, Macao and Taiwan remain distinct project entries. Russia is outside
this particular definition. Preserve the original ISO3 membership and an ISO2
API crosswalk rather than allowing a provider's country labels to redefine it.
[Published definition location](https://alpha60-devops.github.io/alpha60-results/data/region-ranking-definitions.json)

| Region members | First route to test | Verification status in this pass |
|---|---|---|
| JPN | NIES + Sora-mame | Documentation verified; one month of Kagawa API data retrieved |
| SGP | NEA through data.gov.sg | Official PM2.5 dataset verified; API and historical products offered |
| KOR | AirKorea / Korean public-data portal; OpenAQ for compatible history | Official monitoring and API documentation found; account-based download not tested |
| HKG | EPD hourly pollutant concentrations and archives | Official PM2.5 reporting verified; bulk historical join still to test |
| TWN | Ministry of Environment open-data portal | Official API documentation found; dataset selection, key and retention still to test |
| AFG, BGD, BRN, BTN, CHN, IDN, IND, IRN, KHM, LAO, LKA, MAC, MDV, MMR, MNG, MYS, NPL, PAK, PHL, PRK, THA, TLS, VNM | OpenAQ country/provider inventory, then national-agency adapters where needed | Candidate integration route only; current coverage and usable periods not verified |

Singapore's official listing offers PM2.5 data from February 2016 to October
2026 and states an open-data license allowing personal/commercial reuse. Its
regional reporting locations must not be represented as individual station
addresses. [NEA dataset](https://data.gov.sg/datasets/d_e1058d6974c877257e32048ab128ad83/view)

For the other verified leads, use the agencies' actual PM concentrations, not a
combined AQI interpreted as PM2.5: [AirKorea](https://www.airkorea.or.kr/index.do),
[AirKorea API manual](https://apiweb.airkorea.or.kr/common/upload.pdf),
[Hong Kong EPD](https://www.aqhi.gov.hk/en/), and
[Taiwan MOENV API guide](https://data.moenv.gov.tw/manual_file/48ea920a856be600.pdf).

OpenAQ is a practical common adapter, not a guarantee of all 28 countries or
all years. Query countries, locations, sensors, parameter and provider metadata
first; then bounded hourly/daily measurement intervals. API v3 authenticates
with `X-API-Key`. Preserve upstream license and station identity so direct
national data and their OpenAQ copies are not counted twice.
[OpenAQ coverage model](https://docs.openaq.org/about/about),
[API key documentation](https://docs.openaq.org/using-the-api/api-key),
[country catalog](https://docs.openaq.org/resources/countries)

EANET offers monthly/annual summaries without registration and finer data after
registration. Its published terms require written permission for republication
and restrict third-party supply. Check the actual PM2.5/PM10 variables and
station-year availability before treating it as particulate coverage; deposition
chemistry is a different measurement. [EANET data and terms](https://monitoring.eanet.asia/document/public/index)

CAMS EAC4 supplies modeled/assimilated regional continuity at 0.75 degrees.
The listed monthly release spans 2003–2025, with twice-yearly updates delayed
4–6 months. Surface PM2.5/PM10 units are kg/m³; multiply by 1,000,000,000 for
µg/m³. Its spatial support is much coarser than an island or neighborhood.
Use the model's own grid and a separate legend; resampling cannot create
observed detail. [CAMS EAC4 monthly metadata](https://ads.atmosphere.copernicus.eu/datasets/cams-global-reanalysis-eac4-monthly?tab=overview)

## Proposed integration and visual improvements

These are project design decisions, not claims that every provider implements
the same quality rules.

1. Add separate `pm25_concentration` and `pm10_concentration` products with
   provider, original station ID, coordinate provenance, UTC interval, local
   date, original unit/value, normalized µg/m³, quality flag and provisional /
   finalized state. Keep Japanese SPM distinct from PM2.5 and PM10. Preserve
   the source record and retrieval digest alongside normalized rows.
2. Start a Setouchi pilot with Kagawa, Okayama, Hiroshima, Ehime, Hyogo,
   Tokushima, Yamaguchi and Osaka. Join official station metadata, including
   relocation histories; do not infer coordinates from station-code prefixes.
   Publish a station/year coverage matrix before claiming a regional field.
3. Calculate station-day summaries before spatial grouping. An initial research
   completeness rule can require 18 valid hourly intervals per day, explicitly
   labeled as our rule and checked against the source's official conventions.
   Do not sum concentrations or count monitors as pollution intensity.
4. Show station circles at Japan scale, concentration as colour, and completeness
   in a companion panel. For annual comparisons, show observed mean plus valid
   days and comparable seasonal coverage. A separate episode-day map may use
   an explicitly named concentration threshold and valid-day denominator.
5. Keep 2025 full-year and 2026 year-to-date clearly different. For change maps,
   compare the same calendar window and station cohort. Do not interpret
   changing network membership as an atmospheric trend.
6. At world/Asia scale, use H3 only as an aggregation display, with station counts
   and support retained. Avoid Voronoi or interpolation fills that imply measured
   coverage across unmonitored ocean, mountain terrain or countries. Grey means
   unavailable. Model estimates and community sensors need separate encodings.
7. Test duplicate station-hours, leading-zero IDs, time-zone/day-boundary
   handling, missing tokens, negative values, station relocation, unit conversion,
   source revisions, and official/OpenAQ duplication. Verify conservation of
   observations through each aggregation stage.

## Next steps and human reviews

- The Japanese station join and all-prefecture adapter are implemented. Next,
  backfill earlier 2025 months from finalized NIES releases as available.
- Before public reuse, resolve Sora-mame station-owner terms and seek EANET
  permission if its data are selected. No permission request was sent.
- The public OpenAQ AWS archive was ingested without a key. A key would help
  build an exhaustive Asia-28 provider inventory. A PurpleAir key and agreed point budget are needed only if the
  optional coverage pilot is selected; do not buy data before checking value.
- Have a Japanese air-monitoring reader review negative readings, aggregation
  conventions, provisional/final reconciliation and any episode threshold.
- For the exhibition edition, refresh dates and translations, document coverage
  gaps, and review concentration and completeness legends on a physical proof.

Implementation outcome: official Japanese observations, CNEMC measurements via
Quotsoft and selected Indian OpenAQ history now feed the native particulate
renderer. The public [AWS archive documentation](https://docs.openaq.org/aws/about)
resolved the apparent OpenAQ key blocker. PurpleAir remains a conditional
supplement; broader Asia-28 coverage still requires a provider-by-country and
station-year inventory. AirGradient supplies the implemented commercial-sensor
example, explicitly separate from government monitors.
