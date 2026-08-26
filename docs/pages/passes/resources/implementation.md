# Resources Stage 12 implementation notes

[Documentation index](../../../../index.md) ·
[Stage 12 overview](../../../development/20260815_stage-12.md) ·
[Projection snapshots](../../getting-started/build.md#generated-artifact-previews) ·
[Generation guide](../../getting-started/generation.md) ·
[Metric catalog](metric-catalog.md) ·
[Enrichment plan](enrichment-plan.md)

## Implemented scope

Resources are six independent families: `resources-energy`,
`resources-food`, `resources-fauna`, `resources-flora`,
`resources-mineral`, and `resources-human`. The aggregate profile selectors
`resources`, `resource`, and `resouces` expand to all six. `fisheries` and
`reefs` select fauna; `ressources-flora` remains a spelling alias for flora.
There is no combined resource score.

The [resource metric catalog](metric-catalog.md) is the visible
lifecycle index for all 59 definitions. It separates the 14 standard passes
below from optional-pass infrastructure and 45 exploration-only entries.
`Supplemental` catalog status does not mean an implemented optional pass.

The checked snapshot releases 14 separate metric products:

| Family | Metric | Artifact stem |
| --- | --- | --- |
| Energy | Installed solar capacity, 2025 | `resources-energy-solar-capacity-2025` |
| Energy | Installed wind capacity, 2025 | `resources-energy-wind-capacity-2025` |
| Energy | Operating nuclear net capacity, 2024 | `resources-energy-nuclear-operating-capacity-2024` |
| Energy | Petroleum refinery throughput, latest 2018–2024 | `resources-energy-petrochemical-refinery-throughput-latest-2024` |
| Food | Food production index, 2022 | `resources-food-food-production-index-2022` |
| Fauna | Total fisheries production, 2024 | `resources-fauna-fisheries-production-latest-2024` |
| Fauna | Coral-reef integrated local threat, 2011 | `resources-fauna-coral-reef-threat-2011` |
| Flora | Forest area, 2023 | `resources-flora-forest-area-percent-2023` |
| Mineral | Rare-earth mine production, 2025 estimate | `resources-mineral-rare-earth-mine-production-2025` |
| Human | Population under 30, 2024 | `resources-human-population-under-30-2024` |
| Human | Population 60+, 2024 | `resources-human-population-over-60-2024` |
| Human | Upper-secondary attainment, latest 2018–2025 | `resources-human-upper-secondary-attainment-latest-2025` |
| Human | Bachelor’s attainment, latest 2018–2024 | `resources-human-bachelors-attainment-latest-2024` |
| Human | Resident patent applications per million, 2019–2021 | `resources-human-resident-patent-applications-per-million-2019-2021` |

The public term `petrochemical` is only a convenient Make-target alias for the
precisely labeled refinery-throughput metric. The map is not nameplate
capacity, extraction, chemical-plant capacity, or all petrochemical output.
All fourteen products—including fisheries and the spatial reef product—are
standard, offline passes in `make all`; reef generation is not
authorization-gated.

## Data contract and gates

[`resources-profile.json`](../../../../assets.static/resources/resources-profile.json)
uses `cartofreako-resources-profile-v3`. It defines the source register,
country geometry and values digests, six families, palettes, metrics, one
default per family, and either a country coverage definition or a spatial
definition for every released product. Its `display.data_graphic_opacity`
field is fixed at `0.60` for the Stage 14 render contract. Immutable Stage 13
artifacts retain their original `0.30` value.

[`resources-values.json`](../../../../assets.static/resources/resources-values.json)
uses `cartofreako-resources-values-v3`. Its 1,679 records contain family,
metric, ISO3 key, observation year, finite nonnegative value, and value state.
[`coral-reefs-025deg.geojson`](../../../../assets.static/resources/coral-reefs-025deg.geojson)
is the separately digested spatial input.

The loader rejects unknown/duplicate JSON members, wrong schemas, unknown
sources or metrics, invalid IDs/digests/colors, values attached to unreleased
metrics, country and spatial release metadata on the same metric, failed
gates, missing files, duplicate country keys, and declared/actual count drift.

- Broad country statistics require at least 80% of mapped countries and 90%
  of mapped population.
- Production and capacity statistics require at least 90% of the source world
  total. Country/population coverage remains visible so a producer metric
  cannot be mistaken for a household statistic.
- A rate derived from a count-based activity may use the same output-share
  gate when the source publishes a compatible world numerator. The patent
  map therefore gates on 95.814% of resident applications while disclosing
  that its rate denominator covers 93 countries and 81.743% of mapped
  population; missing countries remain unknown, not zero.
- A released spatial field must declare a nonempty, checked domain and pass
  its source-specific gate. The reef gate requires at least 7,000 mapped
  quarter-degree cells.
- A source zero is rendered as zero. An absent record or cell is unknown and
  is never imputed.

Exact release counts and percentages live in the profile and are repeated in
SVG metadata and legends. The Stage 12 summary records the
[complete table and rejected human candidates](../../../development/20260815_stage-12.md#resource-release-definitions).

## Human derivations

The 2024 age metrics use matched World Bank/UN sex and age bands:

```text
under30 = population(0–14)
        + female_population × female%(15–29) / 100
        + male_population   × male%(15–29) / 100

over60 = population(65+)
       + female_population × female%(60–64) / 100
       + male_population   × male%(60–64) / 100
```

Each becomes a percentage of matched total population. The patent product is
the sum of resident applications in 2019–2021 divided by matched total
person-years and multiplied by one million. It measures applications, not
grants, invention quality, or 2026 activity.

The attainment metrics use the latest accepted observation from 2018 onward.
ISCED 3+ means completed upper secondary or higher; ISCED 6+ means completed
bachelor’s or equivalent, excluding short-cycle ISCED 5. Adult literacy and
advanced degrees were tested but remain planned because they miss the current
non-sparse gate.

## Reef derivation

The WRI KMZ contains six regional layers, each with four integrated
local-threat features. Preparation checks all 24 source features and 63,383
polygons. An interior point assigns each polygon to a 0.25° grid cell;
overlaps retain the highest threat rank. The checked result has 7,215 cells:
1,493 Low, 1,967 Medium, 1,433 High, and 2,322 Very High.

The reduction is intentionally coarse enough for the six projection products
and thumbnail review. A filled cell means at least one source reef polygon
was assigned there; it does not claim full-cell coral area.

## Rendering contract

Country products join the `RESOURCE_A3` field in compact Natural Earth 1:110m
geometry and contain:

1. `resources-background`;
2. `terrestrial-land`;
3. `resource-country-coverage`;
4. `resource-missing-data`;
5. `resource-country-values`; and
6. `resource-legend`.

The reef product replaces the three country sublayers with
`resource-spatial-coverage` above subdued 1:10m land. It uses categorical
Low/Medium/High/Very High colors and a no-mapped-reef swatch. Both branches
clip across all projection seams and use native-face area clipping where
required.

Every observed country fill and every observed reef cell uses its metric hue
at 60% opacity. Missing-data context stays opaque: transparency cannot make an
unknown country look like a low observed value. Legends also stay opaque so
their reference colors remain readable. Main plate headings are twice the
pre-Stage-13 size (`0.36` rather than `0.18` page units); metadata records
both `data-graphic-opacity="0.6"` and `data-title-scale="2"`. Stage 14 raises
the observed field from Stage 13's 30% setting to 60% while retaining the
same title scale and evidence metadata.

Every SVG embeds the complete source and metric catalogues, selected metric,
units, period, profile/value/geometry digests, gate statistics, Stage 12
workflow version, and `missing-is-zero=false`. Country paths expose ISO3,
value, year, and state; reef paths expose threat rank and label. The generator
reopens and checks the viewBox, branch-specific layers, catalogue counts,
spatial path count, metadata, finite output, and configured label font.

## Generate and inspect

Family/projection targets build every released metric in that family. Metric
aliases address one product:

```sh
make generate-resources-energy-cahill-keyes  # four maps
make generate-resources-fauna                # fisheries + reefs, six projections
make generate-resources-human                # five maps, six projections
make generate-resources-energy-wind
make generate-resources-fauna-reefs-star-x
make generate-resources-human-over-60-cahill-keyes
make generate-resources-stage12              # all 84 maps
```

`make generate-resources-artifacts` adds PDFs and PNGs. Released SVGs are
stored as deterministic `gzip -n -9` files; their plain SVGs are ignored
generation/export intermediates. `generate-resources-stage6b` remains a
compatibility alias for the current full resource graph.

Ordinary generation is offline. Refresh and review are explicit:

```sh
make refresh-resources-data
make check
git diff -- assets.static/resources
```

The fetcher stages upstream files in a temporary directory. The Python
preparer validates source anchors/totals, names, time windows, age/rate
formulas, reef geometry/counts, and gates before atomically installing the v3
documents and `SHA256SUMS`.
