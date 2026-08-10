# Stage 12 development implementation notes

[Documentation index](../../../index.md) ·
[Generation guide](../getting-started/generation.md) ·
[Projection snapshots](../../../index.md#generated-artifact-previews) ·
[Resources details](../passes/resources/implementation.md) ·
[Resource metric catalog](../passes/resources/metric-catalog.md) ·
[Prerequisites and hardware](../getting-started/prerequisites.md)

## Release scope

Stage 12 expands the offline, reproducible release graph without merging
unlike measurements into synthetic scores:

- resources now comprise six families and 14 released metric products;
- energy adds wind, nuclear, and petroleum-refinery-throughput products beside
  solar;
- `resources-fauna` adds fisheries production and an actual coral-reef threat
  field;
- `resources-human` releases five independently labeled passes: under 30,
  over 60, upper-secondary attainment, bachelor’s attainment, and resident
  patent applications per million person-years;
- the default Anthropocene target produces both 2025 and 2026 temperature
  fields; the earlier source-separated observation atlas remains available
  through `generate-anthropocene-atlas*` targets;
- `make authorize-external` validates local authorization for optional
  P-Tree, NASA FIRMS, and licensed network-topology workflows;
- `make generate-authorized-external` authorizes every selected workflow
  before running its bounded acquisition and artifact pipeline; and
- `make generate-snapshot-ck` creates the 28-thumbnail Cahill–Keyes contact
  sheet documented in [`generated-snapshot-ck.md`](../gallery/cahill-keyes.md);
- the thumbnail targets retain their 480-pixel width when invoked through
  `assets-single` or `assets-resilient`, even though those recursive release
  targets forward the 3840-pixel full-size export setting; and
- Star-X Natural Earth compositing now paints every transformed Antarctic
  fragment after the ordinary quadrant paths in the same thematic layer, so
  the unified polar projection remains on top instead of being clipped by a
  later feature or longitude band.

The standard graph contains 187 layered SVG products, 187 PDF exports, 187
full-size PNG exports, 84 deterministic resource `.svg.gz` files, and 28
additional low-resolution Cahill–Keyes thumbnails. The thumbnails are derived
artifacts, not additional projection passes.

## Resource release definitions

Every country metric retains its own units and dates. Production/capacity
metrics pass when represented observations account for at least 90% of the
source world total. Broad country statistics pass when they cover at least
80% of mapped countries and 90% of mapped population. Missing remains
unknown, never an inferred zero. A rate derived from count activity may use
the output gate against a compatible world numerator; the patent row reports
both that share and its smaller country domain explicitly.

| Family | Released product | Reference | Records/domain |
| --- | --- | --- | ---: |
| Energy | Installed solar capacity | IRENA, 2025 | 169 countries; 99.832% of source world output |
| Energy | Installed wind capacity | IRENA, 2025 | 124 countries; 100% after a bounded rounding clamp |
| Energy | Operating nuclear net electrical capacity | IAEA RDS-2/45, 31 Dec 2024 | 32 countries; 100% of 377,014 MW(e) |
| Energy | Petroleum refinery throughput | UN Energy Statistics, latest observation from 2018–2024 | 106 countries; 98.629% of source output |
| Food | Food production index | FAO via WDI, 2022 | 168 countries |
| Fauna | Total fisheries production | FAO via WDI, 2024 | 169 countries |
| Fauna | Integrated local coral-reef threat | WRI *Reefs at Risk Revisited*, 2011 | 7,215 quarter-degree reef cells |
| Flora | Forest area | FAO via WDI, 2023 | 169 countries |
| Mineral | Rare-earth mine production | USGS, 2025 estimate | 12 producer countries; 99%+ of source output |
| Human | Population under 30 | UN/WDI, 2024 | 169 countries |
| Human | Population 60 and older | UN/WDI, 2024 | 169 countries |
| Human | Completed ISCED 3 or higher, age 25+ | WDI/UIS, latest 2018–2025 | 150 countries |
| Human | Completed ISCED 6 or higher, age 25+ | WDI/UIS, latest 2018–2024 | 149 countries |
| Human | Resident patent applications per million person-years | WDI, 2019–2021 matched mean | 93 countries; 95.814% of applications |

The public `petrochemical` target deliberately selects petroleum refinery
throughput. It does not claim nameplate capacity, crude extraction, chemical
plant capacity, or total petrochemical output. Observations older than 2018
are excluded from the rendered map while remaining in the denominator, so
the recency filter cannot make its output-share gate easier to pass.

Stage 12 tried two additional human candidates but did not release them.
Adult literacy covers 144 mapped countries and 89.432% of mapped population,
just below the population gate. Advanced-degree attainment covers 126 mapped
countries and 90.335% of population, below the country gate. Both remain
explicitly planned instead of being filled or relabeled.

## Reef derivation and rendering

The reef product starts from WRI's licensed 500 m KML/KMZ geometry rather
than a country proxy. The preparer audits 24 regional threat-class source
features containing 63,383 polygons. Each polygon contributes its interior
point to a 0.25° cell; when several polygons occupy one cell, the highest
integrated local-threat rank wins. The checked GeoJSON contains 7,215 polygon
cells split among Low, Medium, High, and Very High classes.

This is a resolution-reduced presence/threat field, not reef area. It avoids
suggesting that every square kilometre of a filled cell is coral. Spatial
metrics carry a separate schema branch with source counts, mapped feature
count, resolution, class field, source digest, and gate result. Their SVGs
draw subdued Natural Earth land beneath `resource-spatial-coverage`; country
metrics retain the existing country/missing/value layers.

## Generation targets

Family targets now build every released metric in that family for all six
projections:

```sh
make generate-resources-energy
make generate-resources-fauna
make generate-resources-human
make generate-resources-stage12
```

Metric and metric/projection targets remain independently addressable:

```sh
make generate-resources-energy-wind
make generate-resources-energy-nuclear-cahill-keyes
make generate-resources-energy-petrochemical-star-x
make generate-resources-fauna-fisheries
make generate-resources-fauna-reefs-cahill-keyes
make generate-resources-human-over-60
make generate-resources-human-patents-voronoi
```

`generate-resources-stage6b` remains a compatibility alias for the current
complete resource graph; it does not reproduce the smaller historical
matrix.

The Anthropocene defaults are now:

```sh
make generate-anthropocene                 # 2025 and 2026, all projections
make generate-anthropocene-cahill-keyes    # 2025 and 2026, Cahill–Keyes
make generate-anthropocene-atlas           # explicit legacy observation atlas
```

## Optional external authorization

Provider account creation and acceptance of external terms are necessarily
manual. Once those steps are complete, this rule verifies the local boundary
without fetching a production snapshot or generating an artifact:

```sh
NETWORK_TOPOLOGY_LICENSE_ACCEPTED=CC-BY-NC-SA-3.0 \
FIRMS_MAP_KEY='…' \
make authorize-external
```

The rule:

1. requires a P-Tree `ftp.ptree.jaxa.jp` entry in `PTREE_NETRC` (default
   `~/.netrc`), rejects group/other-readable permissions, loads the verified
   per-user SECOM root installed by `make install-jaxa-certificate` (or an
   explicit absolute `PTREE_CACERT`), and performs a read-only implicit-FTPS
   listing; the mutating workflow then selects the latest advertised H09 CLP
   observation not after process start and records its exact source date even
   when P-Tree publication lags;
2. requires `FIRMS_MAP_KEY`, keeps it out of printed commands and output, and
   validates the live NASA FIRMS availability CSV header; and
3. requires the exact topology license acknowledgement and runs the existing
   commit/digest checks over the external cloud, submarine-cable, and
   Internet-exchange roots.

Validate only selected integrations with, for example:

```sh
make EXTERNAL_PASSES='jaxa-ptree nasa-firms' authorize-external
make EXTERNAL_PASSES=network-topology \
  NETWORK_TOPOLOGY_LICENSE_ACCEPTED=CC-BY-NC-SA-3.0 authorize-external
```

Secrets are never copied into the repository or generated metadata. This
rule confirms working access and an operator-provided license assertion; it
does not register accounts, accept terms on anyone's behalf, grant a
commercial TeleGeography license, or make legal advice.

The explicit mutating companion uses the same selection:

```sh
make EXTERNAL_PASSES=jaxa-ptree generate-authorized-external
make EXTERNAL_PASSES=network-topology \
  NETWORK_TOPOLOGY_LICENSE_ACCEPTED=CC-BY-NC-SA-3.0 \
  generate-authorized-external
FIRMS_MAP_KEY='…' make EXTERNAL_PASSES=nasa-firms \
  generate-authorized-external
```

`generate-authorized-external` first performs the same checks as
`authorize-external` for the whole selected set. With no `EXTERNAL_PASSES`
override, local discovery
selects P-Tree from its netrc machine entry, FIRMS from a nonempty map key,
and topology from the exact license acknowledgement; unconfigured providers
are reported and skipped. A selected P-Tree account automatically installs
the pinned, fingerprint-verified per-user trust anchor when it is absent.
Supplying `EXTERNAL_PASSES` makes every named pass mandatory. After setup and
authorization, the target runs, in canonical order:

1. P-Tree fetch, preparation, verification, and all six SVG/PDF/PNG exports;
2. the global Anthropocene fetch and preparation with NASA FIRMS; and
3. all six licensed network-topology SVG/PDF/PNG exports.

The FIRMS workflow intentionally ends at
`assets.static/anthropocene/.prepared/anthropocene-<year>.geojson`. The
candidate must be audited and deliberately promoted with its digest, profile,
coverage dates, tests, and documentation before the observation-atlas release
artifacts are regenerated. Rendering it automatically would bypass the
existing data-review gate. Explicitly requested but unavailable passes fail,
configured passes that fail live authorization fail, and a later failure does
not undo earlier completed downloads or artifacts.

Stage 13 adds persistence after that transaction. Only after all selected
workflows finish does the driver atomically merge canonical pass names into
the ignored `.cartofreako/authorized-external-passes` file with mode `0600`.
It stores no credentials. Future `make all` graphs include Cloud-atmosphere
when `jaxa-ptree` is recorded and licensed topology when
`network-topology` is recorded. FIRMS remains a recorded acquisition/review
authorization without a promoted render graph. A failure writes no new state;
`EXTERNAL_AUTHORIZATION_STATE` can select another file, and
`AUTHORIZED_EXTERNAL_PASSES=` temporarily suppresses all persisted additions.

## Hardware requirements

The release-qualified reference machine remains the Framework Desktop used
for the prior static-asset render:

| Component | Validated configuration |
| --- | --- |
| Processor/APU | AMD Ryzen AI Max+ 395 with Radeon 8060S |
| CPU topology | 16 physical cores, 32 hardware threads |
| CPU identity | AMD family 26, model 112, stepping 0; microcode `0xb700037` |
| Memory | 131,150,248 kB kernel-visible (about 125.1 GiB; 128 GB installed class) |
| Swap | 8,388,604 kB (8 GiB) |
| Render defaults | `ASSET_JOBS=2`, `PNG_LONG_SIDE=3840` |

The Radeon GPU and the CPU's AVX2/AVX-512 features are recorded provenance,
not requirements. The build does not use `-march=native` and does not require
GPU acceleration. A 64-bit platform with the documented C++20,
GDAL/GEOS/H3, and Inkscape stack is the software boundary. No smaller RAM
minimum has been release-qualified; use the 128 GB-class reference envelope
for release parity, or reduce concurrency with `make assets-single` or
`make ASSET_JOBS=1 assets-resilient` and document the measured host.

The previous generated tree occupies about 2.153 GB and its XZ bundle about
0.846 GB. Stage 12 adds 54 resource maps and 28 thumbnails, so reserve
substantial headroom beyond the source/static-data checkouts for complete
SVG/PDF/PNG output and atomic Inkscape temporaries. The exact Stage 12 archive
sizes belong in its release manifest after the full render, not in this
development note.

## Source and schema boundary

The checked resource contracts are now
`cartofreako-resources-profile-v3` and
`cartofreako-resources-values-v3`. The refresh workflow downloads and pins
primary-source inputs from [IRENA](https://www.irena.org/Publications/2026/Mar/Renewable-capacity-statistics-2026),
[IAEA](https://www-pub.iaea.org/MTCD/publications/PDF/RDS-2-45_web.pdf),
[UNdata](https://data.un.org/Data.aspx?d=EDATA&f=cmID%3AGR%3BtrID%3A086),
[World Bank WDI](https://data.worldbank.org/indicator/ER.FSH.PROD.MT),
[WRI](https://www.wri.org/data/reefs-risk-revisited), USGS, and Natural
Earth. Ordinary generation remains offline and verifies the checked
`SHA256SUMS` set.
