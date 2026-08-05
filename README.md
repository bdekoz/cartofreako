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
C++20 compiler, RapidJSON headers, and the checked-in astronomy and Orbital
Technosphere snapshots.

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
targets, full-suite generation, and the Stage 7 design choices.

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
timestamped Orbital Technosphere maps, five
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
