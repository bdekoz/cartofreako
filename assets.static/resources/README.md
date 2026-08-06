# Resources Stage 6b snapshot

This directory contains the checked, offline inputs for the five-family
resources generate pass:

- `resources-profile.json` — strict `cartofreako-resources-profile-v2`
  catalogue, source register, palettes, default metrics, and declared coverage;
- `resources-values.json` — normalized ISO3 country observations using
  `cartofreako-resources-values-v2`;
- `countries-110m.geojson` — Natural Earth 5.1.1 Admin-0 geometry with the
  normalized `RESOURCE_A3` join key; and
- `SHA256SUMS` — digests for all three checked inputs.

Ordinary generation does not use the network. `make check` validates both
JSON contracts, source/metric references, five family defaults, record counts,
coverage declarations, geometry joins, and these digests.

## Released family defaults

The first Stage 6b increment releases one non-sparse country metric per family.
It also catalogues the requested follow-on metrics without pretending that
unreleased data are present.

| Family | Default artifact metric | Source period | Checked country records | Release gate |
| --- | --- | ---: | ---: | --- |
| `resources-energy` | Installed solar capacity | IRENA 2025 | 169 | 99.832% of the IRENA world total represented |
| `resources-food` | Food production index | FAO via WDI, 2022 observations | 168 | 95%+ mapped countries and 99%+ mapped population |
| `resources-flora` | Forest area as percentage of land | FAO via WDI, 2023 observations | 169 | 95%+ mapped countries and effectively all mapped population |
| `resources-mineral` | Rare-earth mine production | USGS 2025 estimate | 12 producer countries | 99%+ of the rounded USGS world total represented |
| `resources-human` | Population under age 30 | UN/WDI 2024 inputs | 169 | 95%+ mapped countries and effectively all mapped population |

`resources-human` also carries a normalized, available age-60-and-older
series. It is not mixed into the under-30 static artifact.

Missing means unknown, never zero. Every country path stores the metric,
observation year, value state, and source-facing unit in SVG metadata or data
attributes. Reported, estimated, derived, remotely sensed, facility, and legal
evidence classes remain separate.

## Source boundary

The checked snapshot is a normalized factual extract, not a redistribution of
the upstream reports. The profile records each source URL, release, retrieval
date, license note, and, where a source file was inspected directly, its
SHA-256 digest. The WDI entry is one deterministic digest over the exact
ZIP/JSON input selected for every indicator code.

- Natural Earth 5.1.1 Admin-0 geometry is public domain.
- IRENA *Renewable Capacity Statistics 2026* supplies 2025 solar capacity.
- USGS *Mineral Commodity Summaries 2026* supplies estimated 2025 rare-earth
  mine production in metric tonnes of rare-earth-oxide equivalent.
- World Development Indicators, refreshed 2026-07-13 under CC BY 4.0, supplies
  the FAO forest/food series and UN population age inputs.

## Explicit refresh workflow

Refresh is a maintainer action and can change source observations, geometry,
coverage, output names, and visual diffs:

```sh
make refresh-resources-data
make check
git diff -- assets.static/resources
```

`scripts/fetch-resources-data.sh` downloads the pinned Natural Earth, IRENA,
USGS, and World Bank inputs into a temporary directory. It then invokes
`scripts/prepare-resources-data.py`, which performs the deterministic joins,
derivations, coverage calculations, schema emission, and checksums. The
preparer itself never downloads data and can be run against an audited local
source set.

Before accepting a refresh, review:

1. upstream release names, URLs, licenses, and file digests;
2. every IRENA country-name join and the solar world-total check;
3. the USGS rare-earth table transcription and rounded world total;
4. the fixed 2024 inputs and formula for under-30 and over-60 percentages;
5. every default metric's non-sparse gate; and
6. generated SVG/PNG visual diffs for all six projections.

The USGS transcription lives visibly in the preparer because PDF footnote
layout is not a stable machine-readable table. A new MCS release requires a
reviewed code/data change; silently scraping shifted PDF columns is rejected.
