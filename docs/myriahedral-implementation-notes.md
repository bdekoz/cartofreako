# Myriahedral C++20 implementation notes

[Documentation index](../index.md) ·
[Geometric context](myriahedral-context.md) ·
[Bibliography](myriahedral-bibliography.md)

## Scope and result

`a60::carto::myriaproj` is a native C++20 forward Myriahedral projection for
the common `a60::carto::projection_api`. It transforms `(latitude, longitude)`
directly into `(x, y)` in a map frame. It does not invoke the historical
`myriaworld` executable, inspect the source raster, or depend at runtime on
Boost.Graph, GDAL, Natural Earth, or Google's S2 geometry library.

Myriahedral projection is a method for creating many possible maps, not one
closed-form map. A fine spherical mesh is given a cut tree, and that tree
determines the shape and seams of the resulting planar net. This
implementation deliberately fixes one depth-5 configuration reconstructed and
registered for the checked-in source raster. Its spanning tree is embedded as
compact generated data. That makes the forward transform deterministic and
suitable for a header-oriented library API.

The work has three parts:

1. **Forward projection:** reproduce the upstream icosahedron face order,
   depth-5 subdivision, fixed land-aware cut tree, planar unfolding, and
   per-face affine transform in C++20.
2. **Variable frames:** normalize that fixed net and uniformly scale it to
   any finite, positive `frame.frame_area` with the checked-in source
   raster's `16:9` ratio.
3. **Documentation and tests:** record the geometry, formulas, provenance,
   API contract, limitations, and fixed reference coordinates.

## Code organization

| Component | Responsibility |
| --- | --- |
| [`cart0freak0-myriahedral.h`](../src/cart0freak0-myriahedral.h) | Mesh generation, unfolding, forward transform, frame validation, API adapter, and source-raster preset |
| [`cart0freak0-myriahedral-tree.inc`](../src/cart0freak0-myriahedral-tree.inc) | Compact parent indices for the fixed 5120-face spanning tree |
| [`a60-carto-projection.h`](../src/a60-carto-projection.h) | Shared `projection_api`, `projection_base`, and `myriahedral` projection mode |
| [`a60-carto-frame.h`](../src/a60-carto-frame.h) | `frame` and `frame.frame_area` geometry |
| [`a60-carto.h`](../src/a60-carto.h) | Umbrella include that exports the projection |
| [`test-myriahedral-projection-api.cc`](../tests/test-myriahedral-projection-api.cc) | Fixed anchors, upstream-layout checks, variable frames, full-degree sweep, domain validation, and API integration |
| [`a60-svg-carto-geo.h`](../src/a60-svg-carto-geo.h) | Geographic integration anchors exercised by the projection test |

Most numeric helpers live in `a60::carto::myriahedral_detail`. They are
header-local `inline` functions so the implementation follows the rest of the
cartography library's integration model.

## Fixed map configuration

The upstream repository does not preserve the exact command that generated
`black-white-downsampled.png`; its README command produces a different tree.
Treating that command as the raster configuration places known cities on the
wrong planar branches. The gap is also recorded in upstream issue #2.

The source-compatible tree used here was reconstructed by running the exact
upstream depth-5 pipeline with historical Natural Earth country geometry,
then comparing candidate trees and rotations against recognizable geographic
anchors in the requested raster. The adopted preprocessing parameters are:

```text
depth       = 5
sigma       = 0.7
wlat        = 0.5
wlon        = 0.1
clat        = -60
clon        = -65
alpha       = 1
net rotation = 335 degrees
```

These values define the implementation's reproducible compatibility
configuration. They are not presented as a recovered historical command line;
the upstream evidence is insufficient for that claim.

The original program computes land overlap against Natural Earth country
geometry, smooths it, weights the dual graph, and applies Prim's
minimum-spanning-tree algorithm. Repeating that historical preprocessing
produced one parent index for every face. The root is face `103`, and the tree
has `5119` hinge edges. Four hexadecimal digits encode each parent in the
checked-in `.inc` file.

Only this derived tree is required by the runtime projection. Changing the
mesh depth, land data, smoothing, graticule weights, center, or tree algorithm
would define a different Myriahedral map and require new topology and
registration data.

The final net is rotated `335` degrees in the mathematical plane to register
the reconstructed net with the source raster's geographic orientation.

## Coordinate conventions

| Layer | Arguments or result | Convention |
| --- | --- | --- |
| `projection_api::meridians_to_point_2d` | `(latitude, longitude)` | degrees |
| Geographic vector | `(gx, gy, gz)` | Cartesian unit sphere |
| Spherical mesh | 5120 chord triangles | upstream face order |
| Unfolded net | `(qx, qy)` | Cartesian, `y` upward |
| Normalized canvas | `(u, v)` | `16:9`, `v` downward |
| Public result | `(x, y)` | frame coordinates, origin at upper left |

The public method accepts finite latitude in `[-90, 90]` and longitude in
`[-180, 180]`. Invalid values throw `std::invalid_argument`. Longitude `+180`
is canonicalized to `-180` before face selection so the two spellings of the
same meridian return the same point.

## Forward transform

### 1. Geographic vector

For longitude `lambda` and latitude `phi`, both in radians:

```text
g = (cos(phi) cos(lambda),
     cos(phi) sin(lambda),
     sin(phi))
```

Exact poles are represented as `(0,0,+1)` and `(0,0,-1)` so their result does
not inherit a tiny longitude-dependent component from floating-point
`cos(pi/2)`.

### 2. Icosahedron and depth-5 subdivision

The initial regular icosahedron has 20 faces. Its twelve vertices use the
upstream constants:

```text
tau = 0.8506508084
one = 0.5257311121
```

The initial face order is preserved because every embedded tree index refers
to that order. For a face `(p0,p1,p2)`, one subdivision computes normalized
spherical edge midpoints:

```text
a = normalize((p0 + p2) / 2)
b = normalize((p0 + p1) / 2)
c = normalize((p1 + p2) / 2)
```

and emits children in this exact order:

```text
(p0,b,a), (b,p1,c), (a,b,c), (a,c,p2)
```

Four subdivision rounds after the initial icosahedron produce:

```text
20 * 4^4 = 5120 faces
```

This is `myriaworld --depth 5`: the base icosahedron is level one.

### 3. How the land-aware tree was formed

This preprocessing is documented for provenance; it is not rerun by the C++
forward transform. For face `i`, let `f_i` be its land fraction, `A_i` its
spherical area, and `d(i,j)` the angular distance between centroids. The
upstream Gaussian smoothing has the form:

```text
w(i,j) = exp(-d(i,j)^2 / sigma^2)

F_i = max(0,
          sum_j w(i,j) A_j f_j
          / (sum_j w(i,j) A_j + 0.000001))
```

Terms below the upstream cutoff are omitted. Country-specific multipliers
help keep vulnerable land groups connected. Each neighboring face pair gets
a cost derived from their area-weighted smoothed land fraction and the
configured geographic weighting. A minimum spanning tree retains exactly
`5119` dual-graph edges as hinges. Every other shared edge becomes a map cut.

The fixed tree matters more to forward coordinates than the preprocessing
formula: it completely specifies which neighboring triangles remain attached.

### 4. Flatten the first face

Let:

```text
d0 = p1 - p0
d1 = p2 - p0
l0 = |d0|
l1 = |d1|
c  = abs((d0 dot d1) / (l0 l1))
```

The first chord triangle is placed in the plane as:

```text
q0 = (0, 0)
q1 = (l0, 0)
q2 = (c l0, sqrt(1-c^2) l1)
```

The absolute value and vertex order intentionally match the upstream
implementation.

### 5. Unfold every tree neighbor

Suppose a positioned parent and an unpositioned child share planar edge
`a--b`. Let `r_a` and `r_b` be the child's 3D chord distances from its third
vertex to the two shared vertices, and let `L = |b-a|`. The location of the
third vertex along the shared edge is:

```text
t = (r_a^2 - r_b^2 + L^2) / (2L)
h = sqrt(max(0, r_a^2 - t^2))
```

With edge unit vector `e` and perpendicular `n = (-e_y,e_x)`, the two circle
intersections are:

```text
c0 = a + t e + h n
c1 = a + t e - h n
```

The intersection on the opposite side of `a--b` from the parent's third
vertex is selected. Traversing all tree edges this way lays out every triangle
without closing the non-tree cuts.

After the `335` degree rotation, the canonical raw bounds are:

```text
minimum = (-3.794926045715898, -2.925593176288270)
maximum = ( 2.570969787433996,  1.609508207794985)
```

These bounds and representative face vertices are checked against an
independent reconstruction in the test.

### 6. Locate the spherical face

A point lies on the interior side of each great-circle edge. For edge
`a--b`, with opposite vertex `c`, the signed containment quantity is:

```text
s = sign((a cross b) dot c) * ((a cross b) dot g)
```

The selected triangle maximizes its minimum `s` across all three edges. The
search first considers 20 base faces and then only four children at each of
four levels. It therefore evaluates 36 small triangle tests rather than
scanning all 5120 faces. Exact edge ties resolve by stable face order.

### 7. Map within one triangle

Let the selected spherical chord face be `(p0,p1,p2)` and the corresponding
planar face be `(q0,q1,q2)`. Define:

```text
d0 = p1 - p0
d1 = p2 - p0
r  = g - p0

A = d0 dot d0
B = d0 dot d1
C = d1 dot d1
R0 = r dot d0
R1 = r dot d1
D = A C - B^2

alpha = (R0 C - R1 B) / D
beta  = (R1 A - R0 B) / D
```

The point in the unfolded net is:

```text
q = q0 + alpha (q1-q0) + beta (q2-q0)
```

This is the affine/chord mapping used by the previous implementation. The
component normal to the chord face is discarded when solving for `alpha` and
`beta`.

### 8. Normalize and scale the net

Let the raw bounds have extent `(E_x,E_y)`. In a normalized canvas of width
`R = 16/9` and height `1`, use one uniform scale:

```text
s = min(R / E_x, 1 / E_y)
left   = (R - s E_x) / 2
bottom = (1 - s E_y) / 2

u = (left + s(q_x - minimum_x)) / R
v = 1 - (bottom + s(q_y - minimum_y))
```

The subtraction from one converts mathematical `y`-up coordinates to screen
`y`-down coordinates. For frame dimensions `(W,H)`:

```text
X = u W
Y = v H
```

Uniform scaling preserves the net geometry at every supported size.

## Aspect-ratio contract

The checked-in raster is `4480 x 2520`, exactly `16:9`. This implementation
uses that complete image canvas—including its intentional whitespace—as its
registration contract. Consequently a map-only frame is valid when:

```text
width / height = 16 / 9
```

This ratio is **not an inherent property of the general Myriahedral method**.
A different cut tree or a tightly cropped rendering could require a different
canvas. It is required here so coordinates remain proportional to the chosen
source asset.

Validation requires finite, positive dimensions and compares the calculated
width using a small machine-epsilon tolerance. Approximate ratios are rejected.
Only `frame.frame_area` is retained; input `moriginx` and `moriginy` offsets are
discarded because placement in a larger composition belongs to `cartography`.

## Public API and use

```c++
#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-myriahedral.h"

const double height = 900;
const a60::carto::frame::area size {
  a60::carto::myriahedral_width_to_height_ratio * height,
  height
};
const a60::carto::frame map_frame {size};
const auto projection = a60::carto::make_myriahedral_projection(
  map_frame, "assets/myriahedral/black-white-downsampled.png");

const auto [x, y]
  = projection.meridians_to_point_2d(40.7128, -74.0060);
```

The optional filename is returned by `image_filename()` after prefixing the
runtime data-resource path. It does not influence projection mathematics.
`myriahedral_source` is the named `4480 x 2520` preset for the checked-in PNG.

## Initialization and complexity

The spherical and planar face arrays are initialized once in a function-local
static object. The one-time work subdivides and unfolds 5120 triangles. A
forward query then uses the hierarchical face search and a constant-size
affine solve. The data footprint is dominated by the spherical and planar
triangle arrays; the compressed tree itself is about 20 KiB of hexadecimal
text.

Function-local static initialization is thread-safe under C++11 and later.

## Tests

`tests/test-myriahedral-projection-api.cc` verifies:

- the `projection_api` relationship and `myriahedral` mode;
- source dimensions, raster name, and runtime resource prefix;
- all 27 positions used by `augment_carto_geo_specific`;
- independently reconstructed raw net bounds;
- variable `frame.frame_area` sizes and proportional coordinates;
- rejection of wrong ratios, non-positive sizes, infinity, and NaN;
- rejection of out-of-range or non-finite geographic coordinates;
- a complete whole-degree latitude/longitude sweep;
- exact equivalence of longitude `-180` and `+180`.

Run it with every standalone projection check:

```sh
make check
```

## Limits and interpretation

- The method and this map are spherical, not ellipsoidal.
- Coordinates are continuous within each face and across retained tree hinges.
  Non-tree edges are intentional discontinuities.
- A point exactly on a cut has more than one geometrically valid planar image.
  Stable face order chooses one representation.
- The affine mapping of finite chord triangles is not a globally exact
  equal-area or conformal formula. Distortion becomes small as mesh faces get
  finer, but exact preservation should not be claimed.
- Coastlines in the PNG are a rendered reference. The raster is not sampled
  during projection, and antialiasing or historical source-data differences
  can produce small visual registration differences at coast edges.
- This header exposes one fixed Myriahedral configuration. Supporting arbitrary
  run-time cut trees would be a separate generator and serialization feature.

## Provenance

The mesh ordering, subdivision scheme, land-aware spanning-tree method,
flattening approach, configuration search space, and source raster derive from
[`temporaer/myriaworld`](https://github.com/temporaer/myriaworld). The method
originates in Jarke J. van Wijk's 2008 paper, *Unfolding the Earth:
Myriahedral Projections*. Natural Earth supplied the historical country
geometry used while reconstructing the fixed tree.

The local raster
[`black-white-downsampled.png`](../assets/myriahedral/black-white-downsampled.png)
is byte-for-byte identical to the upstream sample at the time of
implementation. Its SHA-256 is:

```text
1228cae3fdcbdcb867952135e9eeaec7d894c092eb8dae828d0dd61ad8658fd7
```

See the [bibliography](myriahedral-bibliography.md) for stable primary links,
the configuration evidence, data sources, and licensing notes.
The exact reconstruction inputs, generators, selected tree, planar baseline,
and scoring output are preserved in the
[`assets/myriahedral`](../assets/myriahedral/README.md) artifact
manifest.
