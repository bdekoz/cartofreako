# Cahill-Keyes projection documentation

This repository contains a native C++20 forward implementation of the
Cahill-Keyes projection for the `a60::carto::projection_api`. The implementation
is derived from Mary Jo Graça and Gene Keyes's
[`MegamapMaker-prep9.pl`](assets/cahill-keyes/MegamapMaker-prep9.pl), preserves
the existing Visionscarto map registration, and scales to any finite, positive
2:1 `a60::carto::frame`.

## Read by purpose

- [Geometric context](docs/cahill-keyes-context.md) explains the octahedral
  model, octants and half-octants, the piecewise graticule, and the final
  M-shaped layout.
- [Implementation notes](docs/cahill-keyes-implementation-notes.md) records the
  coordinate pipeline, constants, formulas, C++ API, scaling rules, validation,
  and test strategy.
- [Bibliography](docs/cahill-keyes-bibliography.md) identifies the historical
  papers, primary specifications, source implementation, and related ports and
  map assets.
- [README](README.md) gives the shortest build and usage introduction.

## Quick use

```c++
#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "a60-carto-projection-cahill-keyes.h"

const a60::carto::frame::area dimensions {13200, 6600};
const a60::carto::frame map_frame {dimensions};
const auto projection = a60::carto::make_cahill_keyes_projection(
  map_frame, "visionscarto-cahillkeyes-44x22.300");

// The public API accepts latitude first, then longitude.
const auto [x, y] = projection.meridians_to_point_2d(40.7128, -74.0060);
```

The width must equal twice the height. The returned point is in the frame's
screen coordinate system: the origin is at the upper left, `x` increases to the
right, and `y` increases downward. The optional raster name affects
`image_filename()` only; it is not needed by the projection mathematics.

Run the standalone checks with:

```sh
make check
```

## Source guide

| File | Role |
| --- | --- |
| [`src/a60-carto-projection-cahill-keyes-native.h`](src/a60-carto-projection-cahill-keyes-native.h) | Native, scalable forward construction |
| [`src/a60-carto-projection-cahill-keyes.h`](src/a60-carto-projection-cahill-keyes.h) | `projection_api`, frame validation, and named presets |
| [`src/a60-carto-projection.h`](src/a60-carto-projection.h) | Common projection interface and state |
| [`src/a60-carto-frame.h`](src/a60-carto-frame.h) | Frame and `frame_area` abstraction |
| [`src/a60-carto-projection-cahill-keyes-functions.h`](src/a60-carto-projection-cahill-keyes-functions.h) | Projection-specific path and seam helpers |
| [`tests/test-cahill-keyes-projection.cc`](tests/test-cahill-keyes-projection.cc) | Mathematical reference, scaling, and domain tests |
| [`tests/test-cahill-keyes-projection-api.cc`](tests/test-cahill-keyes-projection-api.cc) | Public API, frame, raster, and integration-anchor tests |
| [`src/a60-svg-carto-geo.h`](src/a60-svg-carto-geo.h) | Geographic integration points exercised by the API test |

## Attribution and licensing

The map design is Gene Keyes's development of B.J.S. Cahill's octahedral map.
The computational construction ported here was written in Perl by Mary Jo
Graça. Its source header permits non-commercial use with attribution to Graça
and Keyes and asks commercial users to contact Gene Keyes. See the
[implementation provenance and licensing note](docs/cahill-keyes-implementation-notes.md#provenance-and-licensing)
and the [bibliography](docs/cahill-keyes-bibliography.md).
