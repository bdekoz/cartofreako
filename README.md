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
SVG, PDF, and PNG suite. The self-contained `make check` target needs only GNU
Make and a C++20 compiler.

List every supported top-level Make target with:

```sh
make list-targets
```

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

Generate 24 production whole-earth maps, five exploratory Myriahedral ocean
perspectives, 12 Cahill-Keyes enlargement slices, and two Myriahedral
face-group slices as layered SVG, PDF, and opaque-white,
3840-pixel-long-side PNG artifacts with:

```sh
make all
```

Outputs are organized under `assets.generated/svg/`, `assets.generated/pdf/`, and
`assets.generated/png/`.
