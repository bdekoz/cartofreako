# cartofreako

This repository contains native C++20 forward implementations of the
AuthaGraph, Cahill-Keyes, Myriahedral, and icosahedral Voronoi projections for
the shared `a60::carto::projection_api`.

The authoritative project documentation is [`index.md`](index.md). It contains
the projection comparison, aspect-ratio requirements, public APIs, usage
examples, implementation guides, geometric context, bibliographies,
attribution, and source/test index.

## Build and test

Run the standalone algorithm and API compatibility checks with:

```sh
make check
```

The checks build in `tests/` with C++20 and strict compiler warnings. See
[`index.md`](index.md#choose-a-projection) to select and use a projection.
