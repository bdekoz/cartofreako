# cartofreako

This repository contains native C++20 forward implementations of the
AuthaGraph, Cahill-Keyes, Dymaxion, Star-X, Myriahedral, and icosahedral
Voronoi projections for the shared `a60::carto::projection_api`.

The authoritative project documentation is [`index.md`](index.md). It contains
the projection comparison, aspect-ratio requirements, public APIs, usage
entry points, implementation guides, geometric context, bibliographies,
attribution, and source/test index.

The top-level directories separate implementation, generation, verification,
and artifacts:

| Directory | Contents |
| --- | --- |
| `src.projections/` | Native C++20 projection API and implementations |
| `src.generate/` | SVG generator entry points and generation support headers |
| `src.wasm/` | WebAssembly adapters, geographic input, smoke tests, and generated builds |
| `tests/` | Standalone algorithm and API tests only |
| `assets.static/` | Historical, reference, and downloaded source assets |
| `assets.generated/` | Locally generated or release-extracted SVG, PDF, and PNG renderings |

## Build and test

Install the components listed in
[`docs/prerequisites.md`](docs/prerequisites.md) before building the complete
SVG, PDF, and PNG suite. The offline `make check` target needs GNU Make, a
C++20 compiler, RapidJSON and H3 development files, sibling Alpha60/Izzi
headers, and the checked-in astronomy, Cloud-atmosphere fixture, Orbital
Technosphere, Anthropocene, resources, and network-swarm snapshots.

List every supported top-level Make target with:

```sh
make list-targets
```

A bare `make` uses [`generation-profile.json`](generation-profile.json) to
build only the configured projection/pass SVG matrix. Inspect its normalized
selection first with:

```sh
make generation-plan
make
```

The checked-in development profile selects Cahill-Keyes plus the Earth and
water passes (`ocean` is accepted as the legacy alias for `water`). See the
[generation methods](docs/generation-methods.md) for custom profiles, explicit
targets, full-suite generation, the central `generate-*` evaluation ledger,
and the Stage 7 design choices.

Run the standalone algorithm and API compatibility checks with:

```sh
make check
```

The checks build in `tests/` with C++20 and strict compiler warnings. See
[`index.md`](index.md#choose-a-projection) to select and use a projection.

The production browser build exposes all six projections, topology-safe
GeoJSON, slices, workers, and SVG/Canvas/D3 adapters. The original
Cahill-Keyes and ocean/land-only Myriahedral builds remain compatibility
targets:

```sh
make check-wasm-projections
make check-wasm-projections-browser
make check-wasm-cahill-keyes
make check-wasm-cahill-myriahedral
```

See the [web-developer quick start](docs/pages/webassembly-quick-start.md) and
[`src.wasm` README](src.wasm/README.md) for API, deployment paths, slices,
compatibility contracts, and build requirements.

Generate 24 production whole-earth maps, 12 timestamped astronomy maps, 12
timestamped Orbital Technosphere maps, 84 Stage 12 resources maps, six
cumulative network-swarm maps, six monochrome Bathymetry Roulette maps, 18
source-separated Anthropocene observation and temperature maps, six cloud/CDN network-infrastructure site maps, five
exploratory Myriahedral ocean perspectives, 12 Cahill-Keyes enlargement
slices, and two Myriahedral face-group slices as layered SVG, PDF, and opaque-white,
3840-pixel-long-side PNG artifacts. The same graph also makes 28
480-pixel-wide Cahill-Keyes thumbnails with:

```sh
make all
```

For a release build, run the same graph with bounded concurrency, keep-going
failure isolation, and an automatic serial completion pass:

```sh
make assets-resilient
```

On a memory-constrained machine, run the same complete artifact graph with
only one recipe at a time. This remains serial even when an outer Make was
started with `-j`:

```sh
make assets-single
```

Outputs are organized under `assets.generated/svg/`, `assets.generated/pdf/`, and
`assets.generated/png/`; contact-sheet thumbnails are under
`assets.generated/thumbnail/cahill-keyes/`. Review all Cahill-Keyes passes in
the [generated snapshot](docs/generated-snapshot-ck.md). The
[`v20260807` generated-assets release notes](docs/releases/v20260807.md)
record the static-bundle manifest, render host, hardware sizing, verification,
and source commit. Maintainers publish source tags and large generated bundles
with the [release runbook](docs/releases/README.md).

Astronomy generation is offline by default and uses a checked-in JSON profile
as the authority for both the calculation timestamp and point of reference.
Generate both all-sky and observer-filtered maps, or deliberately refresh the
bounded external snapshots, with:

```sh
make generate-astro
make fetch-astro-data
```

See the
[`astronomy implementation notes`](docs/astro-implementation-notes.md) for the
San Francisco profile, data sources, formulas, instrumentation model, and
outputs.

Cloud-atmosphere generation is a source-timed opt-in outside `make all`.
P-Tree supplies physical Himawari clouds with regional/daytime coverage;
public JAXA Earth COGs supply AOD, precipitation, and shortwave radiation.
Refresh requires the existing P-Tree `.netrc` entry, then preparation converts
all observed layers to a common H3 snapshot:

```sh
make fetch-cloud-atmosphere-data
make prepare-cloud-atmosphere-data
make verify-cloud-atmosphere-data
make generate-cloud-atmosphere
```

See the
[credentialed P-Tree production-download quick start](docs/ptree-production-download.md)
for account registration, secure `.netrc` setup, a login smoke test,
reproducible commands, expected files, and troubleshooting.

Solar illumination is calculated once at generator process start. AOD remains
distinct from smoke and PM2.5, precipitation is not an event count, and
missing data means unobserved. See the
[Cloud-atmosphere implementation notes](docs/cloud-atmosphere-implementation-notes.md)
for the astronomy boundary, source and QA contracts, terms, layers, and
limitations.

Orbital Technosphere generation is also offline by default. Its JSON profile
fixes the SGP4 calculation instant and San Francisco reference point, while
checked-in OMM CSV and NASA SSCWeb snapshots preserve the input state:

```sh
make generate-orbiting
make fetch-orbiting-data
```

See the [Orbital Technosphere implementation notes](docs/orbital-technosphere-implementation-notes.md)
for source feasibility, naming, propagation, detiling layers, and accuracy
limits.

Anthropocene generation defaults to the separately pinned, broad-coverage
NOAA CPC temperature fields for the complete 2025 calendar year and partial
2026 through August 4:

```sh
make generate-anthropocene
make generate-anthropocene-artifacts
make generate-anthropocene-cahill-keyes
```

The original profile-fixed, partial-2026 observation atlas remains available
as an explicit legacy product. It preserves station temperature records,
rainfall, fire, smoke, flood, severe weather, and EPA PM2.5 exposure as
independent layers:

```sh
make generate-anthropocene-atlas
make generate-anthropocene-atlas-artifacts
```

The explicit `generate-anthropocene-2025`, `generate-anthropocene-2026`, and
`generate-anthropocene-year-artifacts` aliases remain available. A release
refresh of the observation atlas requires
`FIRMS_MAP_KEY` and audits NASA FIRMS acquisition dates plus world regions;
`ANTHROPOCENE_REGIONAL_DEVELOPMENT_ONLY=1` is an explicit local-pipeline
override, not a global release path. EPA AirData remains distinct from NOAA HMS
smoke, and CWFIS remains Canadian QA rather than global fire coverage. See the
[Anthropocene implementation notes](docs/anthropocene-implementation-notes.md)
for classifications, formulas, source research, refresh workflow, and limits.
[Stage 8b enrichment plan](docs/anthropocene-enrichment-plan.md) evaluates the
current North American bias, records the implemented CPC/FIRMS-gate increment,
and specifies the remaining CAMS, permission-gated PurpleAir, and ocean work.

Resources Stage 12 implements six current-source families: energy, food,
fauna, flora, mineral, and human. Fourteen independently defined products run
across all six projections: solar, wind, nuclear, petroleum-refinery
throughput, food production, fisheries, actual reef-threat geometry, forest
area, rare-earth production, and five human measures. Unlike units are never
combined into a synthetic score:

```sh
make generate-resources-energy-wind-cahill-keyes
make generate-resources-fauna
make generate-resources-human
make generate-resources
```

The [Stage 12 implementation notes](docs/stage-12-implementation-notes.md),
[resources implementation notes](docs/resources-implementation-notes.md),
and [enrichment plan](docs/resources-enrichment-plan.md) define source roles,
the v3 country/spatial contracts, offline snapshot preparation, reef
normalization, coverage QA, and rejected human candidates.

Stage 12 resource SVG deliverables are deterministic `*.svg.gz` archives. To decompress
every SVG archive in place while keeping each
`.svg.gz` file:

```sh
find assets.generated -type f -name '*.svg.gz' \
  -exec gzip --decompress --keep -- {} +
```

Optional P-Tree, NASA FIRMS, and licensed network-topology passes require
provider-side registration or terms acceptance. After completing that step,
validate the local credentials and authorization without fetching generation
data or printing secrets:

```sh
make authorize-external
```

See [Prerequisites](docs/prerequisites.md#optional-external-authorization) for
the per-provider variables and selective checks.

Network-swarm generation is offline and reproducible from a checked-in
cumulative GeoJSON archive. Prepare the bounded source and generate the six H3/Izzi
honeycomb maps with:

```sh
make prepare-network-swarm-data
make generate-network-swarm
```

See the [network-swarm implementation notes](docs/network-swarm-implementation-notes.md)
for source validation, independent downloader layers, clustering, projection
cuts, profile overrides, and output previews.

Network-infrastructure generation reads a commit- and digest-pinned external
`cloud_cdn_cache` checkout and produces six projection variants of the located
site atlas. The default root is `../cloud_cdn_cache`; override
`NETWORK_INFRASTRUCTURE_CLOUD_SOURCE` when needed:

```sh
make check-network-infrastructure-sources
make generate-network-infrastructure
make generate-network-infrastructure-artifacts
```

`make check-prerequisite` verifies that both `../cloud_cdn_cache/` and
`../www.submarinecablemap.com/` exist before a complete build. The stricter
source checks above additionally enforce the pinned commits and digests.

TeleGeography submarine cable and Internet-exchange topology is a separate
CC BY-NC-SA 3.0 opt-in and is never part of `make all` or generation-profile
`"all"`:

```sh
make check-network-infrastructure-topology-sources
make generate-network-infrastructure-topology
make generate-network-infrastructure-topology-artifacts
```

See the
[network-infrastructure implementation notes](docs/network-infrastructure-implementation-notes.md)
for source pins, checkout overrides, physical-versus-logical edge semantics,
clustering, licensing, and previews.

Bathymetry Roulette generation is offline from the same pinned Natural Earth
input as the Earth and water maps. Generate the six projection variants, or
their complete SVG/PDF/PNG artifact family, with:

```sh
make generate-bathymetry-roulette
make generate-bathymetry-roulette-artifacts
```

See the [Bathymetry Roulette implementation notes](docs/bathymetry-roulette-implementation-notes.md)
for the confirmed depth-to-curve catalogue, explicit overlapping line-field
variations, monochrome clipping model, accepted moiré, layer contract, and
previews.
