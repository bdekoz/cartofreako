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
| `assets.generated/` | Checked-in SVG, PDF, and PNG renderings |

## Build and test

Install the components listed in
[`docs/prerequisites.md`](docs/prerequisites.md) before building the complete
SVG, PDF, and PNG suite. The offline `make check` target needs GNU Make, a
C++20 compiler, RapidJSON and H3 development files, sibling Alpha60/Izzi
headers, and the checked-in astronomy, Orbital Technosphere, Anthropocene, and
network-swarm snapshots.

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

The optional browser builds include Cahill-Keyes and a Myriahedral base-map
option restricted to the `ocean` and `land` layers:

```sh
make check-wasm-cahill-keyes
make check-wasm-cahill-myriahedral
```

See the [`src.wasm` README](src.wasm/README.md) for their JavaScript APIs,
layer contracts, and build requirements.

Generate 24 production whole-earth maps, 12 timestamped astronomy maps, 12
timestamped Orbital Technosphere maps, six cumulative network-swarm maps, six
monochrome Bathymetry Roulette maps, six source-separated Anthropocene maps,
six cloud/CDN network-infrastructure site maps, five
exploratory Myriahedral ocean perspectives, 12 Cahill-Keyes enlargement
slices, and two Myriahedral face-group slices as layered SVG, PDF, and opaque-white,
3840-pixel-long-side PNG artifacts with:

```sh
make all
```

Outputs are organized under `assets.generated/svg/`, `assets.generated/pdf/`, and
`assets.generated/png/`.

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

Anthropocene generation is offline from a profile-fixed, partial 2026 H3
snapshot. It preserves temperature records, rainfall, fire, smoke, flood,
severe weather, and EPA PM2.5 exposure as independent layers:

```sh
make generate-anthropocene
make generate-anthropocene-artifacts
```

EPA AirData is the default PM2.5 source and remains distinct from observed
NOAA HMS smoke. CWFIS supplies public Canada/North America hotspots; an
optional `FIRMS_MAP_KEY` adds global NASA FIRMS refresh coverage, including
northern Russia. Coral bleaching stress remains a documented separate
raster/reef phase. See the
[Anthropocene implementation notes](docs/anthropocene-implementation-notes.md)
for classifications, formulas, source research, refresh workflow, and limits.

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
for the confirmed depth-to-curve catalogue, monochrome clipping model,
accepted moiré, layer contract, and previews.
