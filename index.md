# Cartographic projection documentation

This repository contains native C++20 forward implementations of the
AuthaGraph, Cahill-Keyes, and Myriahedral projections for
`a60::carto::projection_api`. All three accept variable-size
`a60::carto::frame` values while enforcing the aspect ratio required by the
selected geometry or source-canvas registration.

## Choose a projection

| Projection | Geometric model | Required map ratio | Public class | Factory |
| --- | --- | ---: | --- | --- |
| AuthaGraph | Oblique tetrahedron, 24 symmetric sectors, periodic rectangle | `4:sqrt(3)` | `agproj` | `make_authagraph_projection()` |
| Cahill-Keyes | Octahedron, 8 octants, M-shaped rectangular layout | `2:1` | `ckproj` | `make_cahill_keyes_projection()` |
| Myriahedral | Depth-5 icosahedral mesh, land-aware spanning-tree net | `16:9` source canvas | `myriaproj` | `make_myriahedral_projection()` |

Run all standalone projection checks with:

```sh
make check
```

## AuthaGraph

The AuthaGraph implementation follows Hajime Narukawa's 2022 analytic
formulation, orients the tetrahedron with the four published geographic
vertices, and scales the unfolded periodic net to any valid map frame. A named
A3 preset aligns projected coordinates with the checked-in AuthaGraph drawing
sheet.

### Read by purpose

- [Geometric context](docs/authagraph-context.md) explains the oblique
  tetrahedron, nearest-vertex regions, 60-degree sectors, 24-sector periodic
  net, cuts, and aspect ratio.
- [Implementation notes](docs/authagraph-implementation-notes.md) records the
  coordinate pipeline, formulas, assembly table, C++ API, variable-frame
  contract, A3 registration, numeric safeguards, tests, and limitations.
- [Bibliography](docs/authagraph-bibliography.md) identifies the 2022 analytic
  paper, the 2017 original method, official project material, the local source
  plate, and repository verification sources.
- [README](README.md) gives the shortest build and usage introduction.

### Quick use

```c++
#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "a60-carto-projection-authagraph.h"

const double height = 900;
const a60::carto::frame::area dimensions {
  a60::carto::authagraph_width_to_height_ratio * height,
  height
};
const a60::carto::frame map_frame {dimensions};
const auto projection = a60::carto::make_authagraph_projection(
  map_frame, "authagraph-world.svg");

// The public API accepts latitude first, then longitude.
const auto [x, y] = projection.meridians_to_point_2d(40.7128, -74.0060);
```

The width must equal `(4/sqrt(3)) * height`, approximately
`2.309401076758503 * height`. A conventional `2:1` frame is not valid. The
returned point is in the frame's screen coordinate system: the origin is at
the upper left, `x` increases to the right, and `y` increases downward.

The optional raster name affects `image_filename()` only. It is not an input
to the projection mathematics. A named compatibility preset, `ag_a3`, uses
full-page coordinates for
[`assets/authagraph/15-SP-TESD-03-AG.pdf`](assets/authagraph/15-SP-TESD-03-AG.pdf).

## Cahill-Keyes

The Cahill-Keyes implementation is derived from Mary Jo Graça and Gene
Keyes's [`MegamapMaker-prep9.pl`](assets/cahill-keyes/MegamapMaker-prep9.pl),
preserves the existing Visionscarto map registration, and scales to any finite,
positive 2:1 `a60::carto::frame`.

### Read by purpose

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

### Quick use

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

The width must equal twice the height. As with AuthaGraph, the returned point
uses upper-left-origin screen coordinates, and the optional raster name does
not participate in the projection calculation.

## Myriahedral

The Myriahedral implementation reproduces the depth-5 icosahedral mesh of
`temporaer/myriaworld` and uses a fixed tree reconstructed and registered for
the checked-in source raster. A compact embedded minimum-spanning tree
specifies which of the 5120 small faces stay attached.
The projection locates a spherical face, transfers the point affinely into its
unfolded planar copy, and scales the complete net to a variable frame. It has
no runtime dependency on the historical generator, Boost.Graph, S2, GDAL, or
Natural Earth.

### Read by purpose

- [Geometric context](docs/myriahedral-context.md) explains the icosahedral
  mesh, primal and dual graphs, land-aware cut tree, hinges, geographic
  quadrants, screen axes, and `16:9` canvas.
- [Implementation notes](docs/myriahedral-implementation-notes.md) records the
  exact subdivision and affine formulas, fixed-tree provenance, unfolding,
  hierarchical face search, frame contract, API, tests, and limitations.
- [Bibliography](docs/myriahedral-bibliography.md) identifies van Wijk's 2008
  paper, the previous implementation, available configuration evidence,
  Natural Earth data, source-raster digest, and licensing evidence.
- [README](README.md) gives the shortest repository introduction.

### Quick use

```c++
#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "a60-carto-projection-myriahedral.h"

const double height = 900;
const a60::carto::frame::area dimensions {
  a60::carto::myriahedral_width_to_height_ratio * height,
  height
};
const a60::carto::frame map_frame {dimensions};
const auto projection = a60::carto::make_myriahedral_projection(
  map_frame, "assets/myriahedral/black-white-downsampled.png");

// The public API accepts latitude first, then longitude.
const auto [x, y] = projection.meridians_to_point_2d(40.7128, -74.0060);
```

The width must equal `(16/9) * height`. That ratio preserves registration with
the complete `4480 x 2520` source raster; it is not an inherent ratio of every
possible Myriahedral net. The returned point uses upper-left-origin screen
coordinates. The optional raster name is metadata for `image_filename()` and
does not participate in the numeric transform. The named
`myriahedral_source` preset selects the checked-in raster at its native size.

## Source guide

| File | Role |
| --- | --- |
| [`src/a60-carto-projection-authagraph.h`](src/a60-carto-projection-authagraph.h) | AuthaGraph analytic forward transform, frame validation, API, and A3 preset |
| [`tests/test-authagraph-projection-api.cc`](tests/test-authagraph-projection-api.cc) | AuthaGraph formula, source-plate, variable-frame, domain, and API tests |
| [`src/a60-carto-projection-cahill-keyes.h`](src/a60-carto-projection-cahill-keyes.h) | Native scalable forward construction, `projection_api`, frame validation, and named presets |
| [`src/a60-carto-projection-cahill-keyes-functions.h`](src/a60-carto-projection-cahill-keyes-functions.h) | Cahill-Keyes path and seam helpers |
| [`tests/test-cahill-keyes-projection.cc`](tests/test-cahill-keyes-projection.cc) | Cahill-Keyes mathematical reference, scaling, and domain tests |
| [`tests/test-cahill-keyes-projection-api.cc`](tests/test-cahill-keyes-projection-api.cc) | Cahill-Keyes public API, frame, raster, and integration-anchor tests |
| [`src/a60-carto-projection-myriahedral.h`](src/a60-carto-projection-myriahedral.h) | Myriahedral mesh, unfolding, forward transform, frame validation, API, and source-raster preset |
| [`src/a60-carto-projection-myriahedral-tree.inc`](src/a60-carto-projection-myriahedral-tree.inc) | Compact fixed parent tree for the 5120-face net |
| [`tests/test-myriahedral-projection-api.cc`](tests/test-myriahedral-projection-api.cc) | Myriahedral topology, reference-coordinate, variable-frame, domain, and API tests |
| [`src/a60-carto-projection.h`](src/a60-carto-projection.h) | Common projection interface and state |
| [`src/a60-carto-frame.h`](src/a60-carto-frame.h) | Shared frame and `frame_area` abstraction |
| [`src/a60-svg-carto-geo.h`](src/a60-svg-carto-geo.h) | Geographic integration points exercised by API tests |

## Attribution and licensing

AuthaGraph was invented and developed by Hajime Narukawa. The implementation
uses his published 2022 analytic formulation and an official Narukawa Lab
drawing sheet. See the
[AuthaGraph implementation provenance](docs/authagraph-implementation-notes.md#provenance)
and [bibliography](docs/authagraph-bibliography.md).

The Cahill-Keyes map design is Gene Keyes's development of B.J.S. Cahill's
octahedral map. The computational construction ported here was written in Perl
by Mary Jo Graça. Its source header permits non-commercial use with attribution
to Graça and Keyes and asks commercial users to contact Gene Keyes. See the
[Cahill-Keyes provenance and licensing note](docs/cahill-keyes-implementation-notes.md#provenance-and-licensing)
and [bibliography](docs/cahill-keyes-bibliography.md).

The Myriahedral method was published by Jarke J. van Wijk. The fixed mesh,
tree-building method, source command, and raster derive from Hannes Schulz's
`temporaer/myriaworld` implementation; historical land geometry came from
Natural Earth. See the
[Myriahedral implementation provenance](docs/myriahedral-implementation-notes.md#provenance)
and [bibliography](docs/myriahedral-bibliography.md).
