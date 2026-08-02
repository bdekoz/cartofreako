# Cartographic projection documentation

This repository contains native C++20 forward implementations of the
AuthaGraph, Cahill-Keyes, Star-X, Myriahedral, and icosahedral Voronoi
projections for `a60::carto::projection_api`. All five accept variable-size
`a60::carto::frame` values while enforcing the aspect ratio required by the
selected geometry or source-canvas registration.

## Choose a projection

| Projection | Geometric model | Required map ratio | Public class | Factory |
| --- | --- | ---: | --- | --- |
| AuthaGraph | Oblique tetrahedron, 24 symmetric sectors, periodic rectangle | `4:sqrt(3)` | `agproj` | `make_authagraph_projection()` |
| Cahill-Keyes | Octahedron, 8 octants, M-shaped rectangular layout | `2:1` | `ckproj` | `make_cahill_keyes_projection()` |
| Star-X | Cahill-Keyes octants, two stacked four-face groups, polar-centered X | `17:22` | `starxproj` | `make_star_x_projection()` |
| Myriahedral | Depth-5 icosahedral mesh, land-aware spanning-tree net | `16:9` source canvas | `myriaproj` | `make_myriahedral_projection()` |
| Voronoi | Regular icosahedron, 20 nearest-site gnomonic faces | `48:25` source canvas | `voronoiproj` | `make_voronoi_projection()` |

Run all standalone projection checks with:

```sh
make check
```

Generate geometry, labeled graticules, the layered Natural Earth physical
map, and the 153-layer Hamonshū ocean for AuthaGraph, Myriahedral, Star-X,
and Voronoi with:

```sh
make generate-projections
```

Every frame preserves the projection's required ratio and has a largest
dimension of exactly 44 units:

| Projection | Generated frame | Per-projection target |
| --- | ---: | --- |
| AuthaGraph | `44 × 19.052559` (`44 × 11√3`) | `make generate-authagraph` |
| Myriahedral | `44 × 24.75` | `make generate-myriahedral` |
| Star-X | `34 × 44` | `make generate-star-x` |
| Voronoi | `44 × 22.916667` (`44 × 275/12`) | `make generate-voronoi` |

Artifact-family targets are also available as
`generate-geometry-projections`, `generate-graticules-projections`,
`generate-earth-projections`, and `generate-ocean-projections`. Each generic
generator accepts a projection name on its command line and reopens its SVG
to validate the view box, required layers, path structure, and finite numeric
output.

| Projection | Geometry | Graticules | Earth | Ocean |
| --- | --- | --- | --- | --- |
| AuthaGraph | [`geometry-authagraph-44-19.052559.svg`](geometry-authagraph-44-19.052559.svg) | [`graticules-authagraph-44-19.052559.svg`](graticules-authagraph-44-19.052559.svg) | [`earth-authagraph-44-19.052559.svg`](earth-authagraph-44-19.052559.svg) | [`ocean-authagraph-44-19.052559.svg`](ocean-authagraph-44-19.052559.svg) |
| Myriahedral | [`geometry-myriahedral-44-24.75.svg`](geometry-myriahedral-44-24.75.svg) | [`graticules-myriahedral-44-24.75.svg`](graticules-myriahedral-44-24.75.svg) | [`earth-myriahedral-44-24.75.svg`](earth-myriahedral-44-24.75.svg) | [`ocean-myriahedral-44-24.75.svg`](ocean-myriahedral-44-24.75.svg) |
| Star-X | [`geometry-star-x-34-44.svg`](geometry-star-x-34-44.svg) | [`graticules-star-x-34-44.svg`](graticules-star-x-34-44.svg) | [`earth-star-x-34-44.svg`](earth-star-x-34-44.svg) | [`ocean-star-x-34-44.svg`](ocean-star-x-34-44.svg) |
| Voronoi | [`geometry-voronoi-44-22.916667.svg`](geometry-voronoi-44-22.916667.svg) | [`graticules-voronoi-44-22.916667.svg`](graticules-voronoi-44-22.916667.svg) | [`earth-voronoi-44-22.916667.svg`](earth-voronoi-44-22.916667.svg) | [`ocean-voronoi-44-22.916667.svg`](ocean-voronoi-44-22.916667.svg) |

The [SVG generation pipeline](docs/generation.md) explains the generator
sources and Make targets, Natural Earth acquisition, seam handling, sampling,
polygon clipping, projected-path folding, layer construction, self-checks,
and perceptual tradeoffs.

Generate the layered 44×22 Cahill-Keyes face geometry with the real Alpha60
and Izzi headers from the neighboring repositories:

```sh
make generate-geometry
```

Generate the separately grouped and degree-labeled 10° Cahill-Keyes latitude
and longitude graticules with:

```sh
make generate-graticules-ck
```

Generate the layered 44×22 Cahill-Keyes physical map from Natural Earth's
1:10m coastline, land, minor-island, reef, ocean, river, lake/reservoir,
playa, ice, and twelve-depth bathymetry datasets with:

```sh
make generate-earth-ck
```

This target requires GDAL development headers plus `curl` and `unzip`. On its
first run it downloads and SHA-256-verifies Natural Earth's official 5.1.1
physical-vector bundle; the downloaded build input remains ignored by Git.
See the [data note](assets/natural-earth-10m-physical-vectors.md) for source,
checksum, licensing, and the standalone fetch target.

Generate just the Natural Earth ocean, filled with 153 independently layered
vector interpretations of the wave studies in Mori Yūzan's 1903 *Hamonshū*,
volume 2, with:

```sh
make generate-ocean-ck
```

The output uses the same 44×22 Cahill-Keyes frame. Each English motif name is
descriptive because the source has no printed pattern captions; every layer
title records both its illustrated-page number and PDF scan number. See the
[wave-pattern catalogue and rendering notes](docs/hamonshu-wave-patterns.md)
for the page convention, naming scheme, vector method, and provenance.

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
#include "cart0freak0-authagraph.h"

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
#include "cart0freak0-cahill-keyes.h"

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

## Star-X

Star-X reuses the native Cahill-Keyes geometry, splits the ordinary M layout
into left and right groups of four spatial face slots, rotates the right
group by 180 degrees, and stacks it above the left group. This produces the
portrait X arrangement around the northern polar locus without raster tiles
or temporary maps.

### Read by purpose

- [Geometric context](docs/star-x-context.md) explains the octahedral model,
  official octant numbers versus spatial slots, group rotation, final page
  quadrants, polar center, cuts, and aspect ratio.
- [Implementation notes](docs/star-x-implementation-notes.md) records the
  shared Cahill-Keyes calculation, exact assembly formulas, frame contract,
  public API, validation, test strategy, provenance, and limitations.
- [Bibliography](docs/star-x-bibliography.md) identifies the original Star-X
  description and plate diagram, inherited Cahill-Keyes sources, historical
  context, assets, and verification material.
- [README](README.md) gives the shortest repository introduction.

### Quick use

```c++
#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-star-x.h"

const double height = 2200;
const a60::carto::frame::area dimensions {
  a60::carto::star_x_width_to_height_ratio * height,
  height
};
const a60::carto::frame map_frame {dimensions};
const auto projection = a60::carto::make_star_x_projection(
  map_frame, "star-x.svg");

// The public API accepts latitude first, then longitude.
const auto [x, y] = projection.meridians_to_point_2d(40.7128, -74.0060);
```

The width must equal `(17/22) * height`. This retains the historical
34-by-44 four-panel carrier at every scale; `17x22`, `34x44`, `1632x2112`,
and `5100x6600` are all valid examples. The returned point uses an
upper-left screen origin. The optional raster name is metadata only.

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
#include "cart0freak0-myriahedral.h"

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

## Icosahedral Voronoi

The Voronoi implementation reproduces the default `geoIcosahedral()` layout
from `d3-geo-polygon` without a JavaScript dependency. Twelve spherical
vertices define twenty regular triangular faces. Each triangle centroid is a
Voronoi site; the forward transform selects the nearest site by maximizing its
dot product with the geographic unit vector, projects onto that face's
gnomonic tangent plane, and carries the result through the fixed shared-edge
unfolding tree.

This is distinct from the Myriahedral projection above: both begin with an
icosahedron, but this projection retains 20 regular faces and a conventional
fixed net, while Myriahedral subdivides to 5120 faces and uses a land-aware
tree.

### Read by purpose

- [Geometric context](docs/voronoi-context.md) explains the regular
  icosahedron, spherical Voronoi cells, face-centered gnomonic projection,
  unfolding tree, cuts, geographic quadrants, screen axes, and registered
  canvas.
- [Implementation notes](docs/voronoi-implementation-notes.md) records the
  vertex and face construction, nearest-site and gnomonic formulas,
  shared-edge transforms, fixed D3 registration, frame contract, API,
  numeric safeguards, tests, and limitations.
- [Bibliography](docs/voronoi-bibliography.md) identifies the pinned
  `d3-geo-polygon` sources, D3 projection semantics, cartographic background,
  attribution, licensing, and repository verification sources.
- [README](README.md) gives the shortest repository introduction.

### Quick use

```c++
#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-voronoi.h"

const double height = 500;
const a60::carto::frame::area dimensions {
  a60::carto::voronoi_width_to_height_ratio * height,
  height
};
const a60::carto::frame map_frame {dimensions};
const auto projection = a60::carto::make_voronoi_projection(
  map_frame, "icosahedral-voronoi.png");

// The public API accepts latitude first, then longitude.
const auto [x, y] = projection.meridians_to_point_2d(40.7128, -74.0060);
```

The required width is `(48/25) * height`, preserving the original `960 x 500`
source-canvas registration. Screen coordinates use an upper-left origin. The
optional raster name is metadata for `image_filename()` and does not
participate in the numeric transform. The `voronoi_source` preset selects the
native source-canvas dimensions but does not prescribe a raster.

## Source guide

| File | Role |
| --- | --- |
| [`src/cart0freak0-authagraph.h`](src/cart0freak0-authagraph.h) | AuthaGraph analytic forward transform, frame validation, API, and A3 preset |
| [`tests/test-authagraph-projection-api.cc`](tests/test-authagraph-projection-api.cc) | AuthaGraph formula, source-plate, variable-frame, domain, and API tests |
| [`src/cart0freak0-cahill-keyes.h`](src/cart0freak0-cahill-keyes.h) | Native scalable forward construction, `projection_api`, frame validation, and named presets |
| [`src/cart0freak0-cahill-keyes-functions.h`](src/cart0freak0-cahill-keyes-functions.h) | Scale- and offset-aware Cahill-Keyes projected-path seam splitting |
| [`tests/test-cahill-keyes-projection.cc`](tests/test-cahill-keyes-projection.cc) | Cahill-Keyes mathematical reference, scaling, and domain tests |
| [`tests/test-cahill-keyes-projection-api.cc`](tests/test-cahill-keyes-projection-api.cc) | Cahill-Keyes public API, frame, raster, and integration-anchor tests |
| [`tests/test-cahill-keyes-path-functions.cc`](tests/test-cahill-keyes-path-functions.cc) | Cahill-Keyes path seam, scaling, offset, state, and validation tests |
| [`docs/generation.md`](docs/generation.md) | End-to-end SVG generation, seam and folding techniques, data preparation, structural checks, and perceptual considerations |
| [`src/cart0freak0-star-x.h`](src/cart0freak0-star-x.h) | Direct Star-X group assembly, frame validation, public API, and factory |
| [`tests/test-star-x-projection-api.cc`](tests/test-star-x-projection-api.cc) | Star-X anchors, rigid assembly, global domain, polar placement, variable-frame, validation, and API tests |
| [`docs/star-x-context.md`](docs/star-x-context.md) | Star-X octahedral context, face-slot mapping, group rotation, quadrants, polar locus, and cuts |
| [`docs/star-x-implementation-notes.md`](docs/star-x-implementation-notes.md) | Star-X formulas, scaling proof, API, safeguards, verification, and provenance |
| [`docs/star-x-bibliography.md`](docs/star-x-bibliography.md) | Star-X arrangement, Cahill-Keyes geometry, historical, asset, and test sources |
| [`tests/projection-generation-common.h`](tests/projection-generation-common.h) | Exact 44-unit frame configurations, projection dispatch, native-cell lookup, cut bisection, and shared seam-safe path projection |
| [`tests/projection-area-generation.h`](tests/projection-area-generation.h) | Face-local Myriahedral and Voronoi area transforms plus exact planar-triangle clipping for filled paths |
| [`tests/generate-geometry.cc`](tests/generate-geometry.cc) | Izzi SVG generator and structural test for native AuthaGraph, Cahill-Keyes/Star-X, Myriahedral, and Voronoi faces plus four map quadrants |
| [`geometry-ck-44-22.svg`](geometry-ck-44-22.svg) | Generated layered Cahill-Keyes face geometry in a 44×22 frame |
| [`tests/generate-graticules.cc`](tests/generate-graticules.cc) | Izzi SVG generator and structural test for grouped, degree-labeled, discontinuity-split 10° latitude and longitude lines |
| [`graticules-ck-44-22.svg`](graticules-ck-44-22.svg) | Generated 44×22 Cahill-Keyes graticule with 17 latitude groups and 36 longitude groups |
| [`tests/generate-earth.cc`](tests/generate-earth.cc) | GDAL/Izzi SVG generator and structural test for clipped and native-cut-split Natural Earth 1:10m physical-vector layers |
| [`earth-ck-44-22.svg`](earth-ck-44-22.svg) | Generated layered 44×22 Cahill-Keyes physical map |
| [`tests/generate-ocean.cc`](tests/generate-ocean.cc) | GDAL/Izzi generator and structural test for the seam-safe Natural Earth ocean and 153 source-indexed Hamonshū vector-pattern layers |
| [`tests/hamonshu-v2-patterns.inc`](tests/hamonshu-v2-patterns.inc) | Complete illustrated-page, motif-number, and descriptive-name catalogue for *Hamonshū*, volume 2 |
| [`ocean-ck-44-22.svg`](ocean-ck-44-22.svg) | Generated 44×22 Cahill-Keyes ocean with independently selectable wave-pattern layers |
| [`docs/hamonshu-wave-patterns.md`](docs/hamonshu-wave-patterns.md) | PDF page mapping, motif naming, vector interpretation, ocean-clipping method, and source provenance |
| [`scripts/fetch-natural-earth-10m.sh`](scripts/fetch-natural-earth-10m.sh) | Pinned, checksum-verifying acquisition of the required Natural Earth shapefiles |
| [`assets/natural-earth-10m-physical-vectors.md`](assets/natural-earth-10m-physical-vectors.md) | Natural Earth source, checksum, extracted-dataset, and licensing note |
| [`src/cart0freak0-myriahedral.h`](src/cart0freak0-myriahedral.h) | Myriahedral mesh, unfolding, forward transform, frame validation, API, and source-raster preset |
| [`src/cart0freak0-myriahedral-tree.inc`](src/cart0freak0-myriahedral-tree.inc) | Compact fixed parent tree for the 5120-face net |
| [`tests/test-myriahedral-projection-api.cc`](tests/test-myriahedral-projection-api.cc) | Myriahedral topology, reference-coordinate, variable-frame, domain, and API tests |
| [`src/cart0freak0-voronoi.h`](src/cart0freak0-voronoi.h) | Icosahedral Voronoi geometry, gnomonic face projection, affine unfolding, frame validation, API, and source-canvas preset |
| [`tests/test-voronoi-projection-api.cc`](tests/test-voronoi-projection-api.cc) | Voronoi topology, independent D3 reference coordinates, variable-frame, global-domain, seam, and API tests |
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

Star-X retains that Cahill-Keyes construction and its terms, then applies
Benjamin De Kosnik's two-group arrangement. See the
[Star-X implementation provenance](docs/star-x-implementation-notes.md#provenance-and-limitations)
and [bibliography](docs/star-x-bibliography.md).

The Myriahedral method was published by Jarke J. van Wijk. The fixed mesh,
tree-building method, source command, and raster derive from Hannes Schulz's
`temporaer/myriaworld` implementation; historical land geometry came from
Natural Earth. See the
[Myriahedral implementation provenance](docs/myriahedral-implementation-notes.md#provenance)
and [bibliography](docs/myriahedral-bibliography.md).

The icosahedral Voronoi geometry, parent tree, and registration derive from
the ISC-licensed [`d3-geo-polygon`](https://github.com/d3/d3-geo-polygon)
implementation by Mike Bostock, with the Icosahedral map implemented by Jason
Davies, Enrico Spinielli, and Philippe Rivière. The required ISC notice is
retained in `src/cart0freak0-voronoi.h`. See the
[Voronoi implementation provenance](docs/voronoi-implementation-notes.md#provenance-and-licensing)
and [bibliography](docs/voronoi-bibliography.md).
