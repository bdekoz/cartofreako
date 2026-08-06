# Resources Stage 6b implementation notes

[Documentation index](../index.md) ·
[Generation guide](generation.md) ·
[Enrichment and source plan](resources-enrichment-plan.md) ·
[Generation methods](generation-methods.md)

## Implemented scope

The resources pass is now five independent current-source families:

- `resources-energy`;
- `resources-food`;
- `resources-flora`;
- `resources-mineral`; and
- `resources-human`.

`resources-flora` is canonical; `ressources-flora` is accepted only as a
selector/CLI alias. The aggregate generation-profile values `resources`,
`resource`, and `resouces` expand to all five families. Each family has its own
metric catalogue, units, evidence classes, palette, coverage statement, and
default artifact. There is no combined resource score.

The first released increment maps one non-sparse default per family:

| Family | Default | Artifact stem |
| --- | --- | --- |
| Energy | IRENA installed solar capacity, 2025 | `resources-energy-solar-capacity-2025` |
| Food | FAO/WDI food production index, latest accepted snapshot | `resources-food-food-production-index-latest-2026` |
| Flora | FAO/WDI forest area percentage, latest accepted snapshot | `resources-flora-forest-area-percent-latest-2026` |
| Mineral | USGS rare-earth mine production, 2025 estimate | `resources-mineral-rare-earth-mine-production-2025` |
| Human | Derived population under age 30, 2024 | `resources-human-population-under-30-2024` |

The normalized values also include population age 60 and older as an
`available` human metric. Static files still display one metric and unit at a
time; future promotion of that metric gets its own artifact rather than being
overpainted on the under-30 map.

## Data contract

[`resources-profile.json`](../assets.static/resources/resources-profile.json)
uses `cartofreako-resources-profile-v2`. It defines:

- the snapshot date and missing-value semantics;
- the checked country-geometry and values files plus their SHA-256 digests;
- a source register with organization, release, URL, retrieval date, license
  note, and source digest/status (the WDI digest covers the ordered set of
  selected indicator ZIP/JSON inputs);
- exactly five families and one default metric for each;
- metric title, unit, reference period, evidence class, source IDs, lifecycle
  status, transform, artifact tag, notes, and optional coverage; and
- low, high, and missing colors for each family.

[`resources-values.json`](../assets.static/resources/resources-values.json)
uses `cartofreako-resources-values-v2`. Every record contains a family,
metric, ISO3 join key, observation year, finite nonnegative value, and value
state (`reported-or-estimated`, `estimated`, or `derived`). Duplicate
family/metric/country keys are rejected.

The C++ loader rejects unknown or duplicate JSON members, wrong schemas,
unknown source or metric references, invalid identifiers/digests/colors,
duplicate catalog IDs, unreleased metrics carrying values, invalid coverage
arithmetic, default metrics without passing coverage, snapshot-date drift,
missing input files, and declared/actual record-count drift.

## Non-sparse release gates

Defaults are accepted only when the checked profile says the release gate
passes and the loader independently confirms the covered-country count.

- Country human/environment/food statistics require at least 80% of mapped
  countries and 90% of mapped population.
- Production/capacity statistics require at least 90% of the source world
  total. The profile also exposes country and population coverage so a narrow
  producer set cannot be mistaken for a worldwide household statistic.
- Missing country features are always rendered with the explicit missing
  color. A numeric zero is rendered only when the source supplies a covered
  zero record.

The released metrics exceed those thresholds. Exact counts and percentages
are stored beside each default in the profile and repeated in the SVG legend
and root metadata.

## Human age derivation

The 2024 under-30 percentage uses matched World Bank/UN inputs:

```text
under30 = population(0–14)
        + female_population × [female%(15–19)+female%(20–24)+female%(25–29)] / 100
        + male_population   × [male%(15–19)+male%(20–24)+male%(25–29)] / 100

under30_percent = 100 × under30 / total_population
```

The available over-60 series is derived separately:

```text
over60 = population(65+)
       + female_population × female%(60–64) / 100
       + male_population   × male%(60–64) / 100

over60_percent = 100 × over60 / total_population
```

All components are fixed to 2024. The generator labels the result `derived`;
it does not describe it as a direct survey observation.

## Rendering contract

The renderer joins values to Natural Earth 5.1.1 Admin-0 geometry through the
prepared `RESOURCE_A3` field. It uses compact 1:110m country polygons, clips
them across every projection seam, and uses gridded native-face clipping for
the non-Cahill-Keyes/non-Star-X nets. Star-X retains the shared Stage 7
unified-Antarctica construction beneath the country coverage.

Every SVG contains these checked groups:

1. `resources-background`;
2. `terrestrial-land`;
3. `resource-country-coverage`;
4. `resource-missing-data`;
5. `resource-country-values`; and
6. `resource-legend`.

Country paths expose ISO3, family, metric, value, observation year, value
state, and missingness. RDF metadata contains the complete source and metric
catalogues plus one catalogue record per mapped default value. After writing,
the generator reopens the SVG and verifies its viewBox, layers, catalogue
counts, Stage 6b provenance, non-sparse status, missing-is-not-zero semantics,
finite coordinates, and configured font.

## Generate and inspect

Generate one family/projection default, all projections for one family, or the
complete five-family matrix:

```sh
make generate-resources-energy-cahill-keyes
make generate-resources-energy
make generate-resources
```

Aggregate projection targets build all five defaults for that projection:

```sh
make generate-resources-cahill-keyes
make generate-resources-star-x
```

`make generate-resources-artifacts` additionally exports PDF and PNG files.
The checked SVG form is deterministic GNU gzip (`gzip -n -9`); the plain SVG
is an ignored build/export intermediate.

Inspect one archive without changing it:

```sh
gzip -cd \
  assets.generated/svg/resources-energy-solar-capacity-2025-ck-44-22.svg.gz \
  > /tmp/resources-energy-solar-capacity-2025-ck-44-22.svg
```

Decompress every generated SVG archive in place while retaining the archives:

```sh
find assets.generated -type f -name '*.svg.gz' \
  -exec gzip --decompress --keep -- {} +
```

## Refresh and extension boundary

Ordinary builds are offline. A maintainer can deliberately refresh candidates:

```sh
make refresh-resources-data
make check
git diff -- assets.static/resources
```

The fetcher stages upstream files in a temporary directory. The preparer never
downloads; it checks source table anchors/totals, normalizes country joins,
derives ages, calculates coverage, writes both v2 documents, and regenerates
`SHA256SUMS`.

New metrics should be promoted in this order:

1. define one comparable unit and evidence class;
2. pin an auditable release and redistribution boundary;
3. normalize observation years and missing/zero states;
4. calculate a relevant country/population/output/domain gate;
5. add values with `available` status and tests;
6. give a static default its own metric-bearing artifact tag only after the
   gate passes; and
7. generate all six projections and inspect visual/XML diffs.

Facility, deposit, occurrence, and legal-policy data stay supplemental unless
their own coverage supports the precise claim. They never fill absent country
statistics by implication.
