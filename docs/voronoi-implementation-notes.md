# Icosahedral Voronoi C++20 implementation notes

[Documentation index](../index.md) ·
[Geometric context](voronoi-context.md) ·
[Bibliography](voronoi-bibliography.md)

## Scope and result

`a60::carto::voronoiproj` is a native C++20 forward implementation of the
default `geoIcosahedral()` map from `d3-geo-polygon` 1.12.1. It transforms a
finite `(latitude, longitude)` pair directly into `(x, y)` in an
`a60::carto::frame`. It does not start a JavaScript process, call D3 at run
time, sample a raster, or construct a general-purpose Voronoi diagram.

The name describes how the fixed polyhedral map chooses a face. Twenty
spherical sites lie at the centers of a regular icosahedron's faces. A point
belongs to the site with the smallest great-circle distance, equivalently the
largest unit-vector dot product. Each resulting spherical Voronoi cell is one
icosahedral triangle. The selected cell is projected gnomonically and moved
into a planar net through a fixed shared-edge tree.

The work has three parts:

1. **Native forward projection:** reproduce D3's twelve vertices, twenty
   faces, face-centroid sites, nearest-site choice, local gnomonic projection,
   parent tree, shared-edge transforms, and registered orientation.
2. **Variable frames:** express D3's default `960 x 500` registration in
   normalized coordinates and scale it to any finite, positive
   `frame.frame_area` with the same `48:25` ratio.
3. **Verification and documentation:** preserve D3-derived numeric anchors,
   exercise the full geographic domain, and record formulas, topology,
   boundaries, limitations, provenance, and licensing.

This is a fixed compatibility projection, not a configurable wrapper around
all of `geoPolyhedralVoronoi()`. Changing the sites, face order, parent tree,
rotation, center, or scale would define a different planar map.

## Code organization

| Component | Responsibility |
| --- | --- |
| [`cart0freak0-voronoi.h`](../src/cart0freak0-voronoi.h) | Icosahedral geometry, face sites, gnomonic formulas, affine unfolding, D3 registration, frame validation, API adapter, and source-canvas preset |
| [`a60-carto-projection.h`](../src/a60-carto-projection.h) | Shared `projection_api`, `projection_base`, and `voronoi` projection mode |
| [`a60-carto-frame.h`](../src/a60-carto-frame.h) | `frame` and `frame.frame_area` geometry |
| [`a60-carto.h`](../src/a60-carto.h) | Umbrella include that exports the projection |
| [`test-voronoi-projection-api.cc`](../tests/test-voronoi-projection-api.cc) | D3 reference points, topology, transforms, variable frames, domain sweep, seam equivalence, validation, and API integration |

Numeric helpers are in `a60::carto::voronoi_detail`. They are header-local
`inline` functions so the implementation follows the library's
header-oriented integration model.

## Fixed D3 compatibility configuration

The controlling upstream configuration is the default returned by
`geoIcosahedral()` in `d3-geo-polygon` 1.12.1:

| D3 setting | Value | C++ representation |
| --- | ---: | --- |
| Planar angle | `0°` | no final planar rotation |
| Spherical rotation | `[108°, 0°]` | add `108°` to input longitude and wrap |
| Projection scale | `131.777` | `source_scale` |
| Geographic center | `[162°, 0°]` | raw-net registration reference |
| Translation | `[480, 250]` | center of the registered source canvas |
| Registered canvas | `960 x 500` | `voronoi_source_width` and `voronoi_source_height` |
| Canvas ratio | `48:25` | `voronoi_width_to_height_ratio` |

The first four values are explicit in the pinned `icosahedral.js`. The
translation is D3's projection default, documented as the center of a
`960 x 500` area. There is no required source raster: “source canvas” means a
coordinate registration against those D3 defaults.

The `48:25` ratio is therefore a compatibility property of this registered
view. It is not an intrinsic aspect ratio of a regular icosahedron or of every
possible icosahedral net.

## Coordinate conventions

| Layer | Arguments or result | Convention |
| --- | --- | --- |
| `projection_api::meridians_to_point_2d` | `(latitude, longitude)` | degrees in the public geographic domain |
| Rotated geographic vector | `(gx, gy, gz)` | Cartesian unit sphere |
| Face-local gnomonic point | `(px, py)` | unit-scale tangent plane; local `py` is south-positive |
| Unfolded raw net | `(qx, qy)` | D3 raw-projection orientation |
| Normalized canvas | `(u, v)` | unit square fractions; `v` is screen-down |
| Public result | `(X, Y)` | frame coordinates, origin at the upper left |

The public method accepts latitude in `[-90, 90]` and longitude in
`[-180, 180]`. Both values must be finite. Invalid input throws
`std::invalid_argument`.

## Forward transform

### 1. Apply the registered spherical rotation

Let public longitude be `lambda` in degrees. The default D3 yaw is reproduced
before face selection:

```text
lambda_r = lambda + 108 degrees

if lambda_r > 180 degrees:  lambda_r -= 360 degrees
if lambda_r < -180 degrees: lambda_r += 360 degrees
```

The comparisons are strict. A result of exactly `+180°` remains `+180°`
rather than being canonicalized to `-180°`; this preserves the same stable
face-boundary choice as D3. Public `-180°` and `+180°` both become `-72°`, so
the two spellings of the antimeridian project identically.

### 2. Convert to a unit geographic vector

Define a unit-sphere conversion for latitude `phi` and longitude `lambda`,
both in radians:

```text
unit(phi,lambda) = (cos(phi) cos(lambda),
                    cos(phi) sin(lambda),
                    sin(phi))

g = unit(phi,lambda_r)
```

The exact poles are represented as `(0,0,+1)` and `(0,0,-1)`. This removes
the tiny, longitude-dependent horizontal residue that would otherwise result
from floating-point evaluation of `cos(pi/2)`.

### 3. Construct the regular icosahedron

The north and south vertices are:

```text
v[0] = unit(+90 degrees, 0 degrees)
v[1] = unit(-90 degrees, 0 degrees)
```

The other ten alternate between two five-vertex rings. For `k = 0..9`:

```text
theta    = atan(0.5) = 26.56505117707799... degrees
lambda_k = ((36 k + 180) mod 360) - 180 degrees
phi_k    = -theta when k is even, +theta when k is odd

v[k+2] = unit(phi_k, lambda_k)
```

The alternating `36°` phases put each ring's own vertices `72°` apart and
offset the northern ring halfway between the southern ring's longitudes.

The twenty oriented faces use this fixed order:

```text
north:
  0:(0,3,11)   1:(0,5,3)    2:(0,7,5)
  3:(0,9,7)    4:(0,11,9)

equatorial belt:
  5:(2,11,3)   6:(3,4,2)    7:(4,3,5)    8:(5,6,4)
  9:(6,5,7)   10:(7,8,6)   11:(8,7,9)   12:(9,10,8)
 13:(10,9,11) 14:(11,2,10)

south:
 15:(1,2,4)   16:(1,4,6)   17:(1,6,8)
 18:(1,8,10)  19:(1,10,2)
```

The indices and ordering matter. They determine tie resolution, the face
adjacency used by the parent tree, and the final net.

### 4. Derive each face site and tangent basis

For a face with ordered unit vertices `(va,vb,vc)`, its spherical site is:

```text
s = normalize(va + vb + vc)
```

For these regular faces this is the spherical face centroid used by D3. A
right-handed tangent basis at the site is then:

```text
east  = normalize((-s_y, s_x, 0))
north = s cross east
```

Every site is away from the geographic poles, so the east vector is
non-degenerate. The twenty sites are also the twenty vertices of the
icosahedron's dual dodecahedron.

### 5. Select the nearest spherical site

For unit vectors, angular distance to site `s[i]` is:

```text
d_i = acos(g dot s[i])
```

Because `acos` is decreasing on `[-1,1]`, minimizing distance is equivalent
to maximizing the dot product:

```text
face = arg max over i=0..19 of (g dot s[i])
```

The C++ loop uses the strict comparison `candidate > closest`, avoiding all
twenty `acos` calls and preserving the lowest face index on an exact tie. The
north and south poles are explicit five-way ties; they select faces `0` and
`15`, respectively.

### 6. Project gnomonically on the selected face

Let `s`, `east`, and `north` be the selected face basis. Define:

```text
denominator = g dot s

px =  (g dot east)  / denominator
py = -(g dot north) / denominator
```

Since `g dot s` is the cosine of angular distance from the face site, this is
the unit-scale gnomonic projection onto the plane tangent at `s`. The minus
sign gives the local plane D3's screen-oriented vertical convention. The face
site itself maps to `(0,0)`, and great-circle arcs within the face map to
straight lines.

Every point selected for one of these triangular cells is on the visible
hemisphere of its site, so the denominator is positive. A non-positive value
indicates an internally inconsistent layout and throws `std::logic_error`.

### 7. Align child faces across shared edges

The root face `0` keeps the identity transform. Every other face is attached
to one adjacent parent along their two shared vertices. Project those two
vertices into the child face to obtain source edge `(S0,S1)` and into the
parent face to obtain target edge `(T0,T1)`. Let:

```text
v = S1 - S0
u = T1 - T0

scale = length(u) / length(v)
angle = atan2(u_x v_y - u_y v_x, u dot v)

R = [ cos(angle)   sin(angle) ]
    [-sin(angle)   cos(angle) ]
```

The edge similarity transform is:

```text
E(p) = T0 + scale R (p - S0)
```

In six-coefficient affine form:

```text
E = [a b c]
    [d e f]
    [0 0 1]

a = scale cos(angle)       b = scale sin(angle)
d = -scale sin(angle)      e = scale cos(angle)
c = T0_x - a S0_x - b S0_y
f = T0_y - d S0_x - e S0_y
```

If `M[parent]` already places the parent in the root plane, composition gives:

```text
M[child] = M[parent] E
```

Affine multiplication applies the right operand first. The parent array is:

```text
face:     0   1  2   3  4   5  6  7  8  9  10 11 12 13 14 15 16 17 18 19
parent:   -   7  9  11 13   0  5  6  7  8   9 10 11 12 13  6  8 10 12 14
```

It is a tree with twenty nodes and nineteen retained hinge edges. A regular
icosahedron has thirty face-adjacency edges, so the other eleven adjacencies
become cuts in the planar net. The parent array is not in topological order;
initialization repeatedly advances faces whose parents are ready and rejects
an invalid, disconnected, or cyclic tree.

After applying the selected face transform, the raw net point is:

```text
q = (M[face](px,py))
q_y = -q_y
```

The final vertical negation reproduces the raw-output convention of D3's
polyhedral projection.

### 8. Reproduce D3 center, scale, and translation

Write `F(phi,lambda)` for the unfolded raw-net operation above, without the
public `108°` rotation. The registered center reference is initialized once:

```text
q_center = F(0 degrees, 162 degrees)
```

For a public coordinate, first compute:

```text
q = F(phi, rotate(lambda, +108 degrees))
```

Then reproduce D3's scale `k=131.777` and translation `(480,250)` while
normalizing by the source canvas:

```text
u = (480 + 131.777 (q_x - q_center_x)) / 960
v = (250 - 131.777 (q_y - q_center_y)) / 500
```

The minus sign in `v` converts the raw mathematical vertical direction to
upper-left-origin screen coordinates. With the configured rotation, public
`(latitude=0°, longitude=54°)` reaches the center reference and maps to
`(480,250)` on the source canvas. Public `(0°,0°)` instead maps to:

```text
(349.2275614546223, 250.0)
```

That latter coordinate initializes `projection_base::longitude_zero_x` and
`latitude_zero_y`; the fields name the public zero meridians, not the canvas
center.

### 9. Scale into `frame.frame_area`

For a valid requested frame of width `W` and height `H`:

```text
X = u W
Y = v H
```

Because `W/H = 960/500`, this is equivalent to uniformly multiplying every
source-canvas coordinate by one factor:

```text
factor = H / 500 = W / 960
X = factor X_source
Y = factor Y_source
```

The geometry, registered whitespace, and all reference coordinates therefore
remain proportional at every supported size.

## Variable-size frame contract

A valid Voronoi map frame satisfies:

```text
W and H are finite
W > 0 and H > 0
W = (48/25) H
```

`is_voronoi_frame()` computes `expected_W=(48/25)H`, rejects an overflowed
result, and compares with:

```text
tolerance = 16 * epsilon(double) * max(W, expected_W)
valid = abs(W - expected_W) <= tolerance
```

The tolerance admits floating-point roundoff only. A conventional `2:1`
frame, an approximate ratio such as `960 x 500.001`, non-positive dimensions,
NaN, infinity, and overflowing dimensions are rejected.

Only the input frame's `frame_area` is retained. `moriginx` and `moriginy` are
discarded because placement of a map in a larger composition belongs to the
surrounding cartography.

## Public API and use

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
const auto [x, y]
  = projection.meridians_to_point_2d(40.7128, -74.0060);
```

The optional filename is returned by `image_filename()` after prefixing the
runtime data-resource path. It is metadata only and does not influence the
numeric transform.

Two named source-registration values are available:

```c++
const a60::carto::frame& source_frame = a60::carto::pvoronoi_source;
const a60::carto::projection_api& source_projection
  = a60::carto::voronoi_source;
```

Both use `960 x 500`; `voronoi_source` has no prescribed raster name.

## Initialization and complexity

The twelve vertices, twenty sites and tangent bases, and nineteen composed
face transforms are built once in a function-local static `layout_data`.
Function-local static initialization is thread-safe under C++11 and later.

Each forward query then performs a fixed twenty-site dot-product scan, one
gnomonic projection, one affine transform, and one canvas transform. Its cost
is constant for this fixed layout—`O(20)`, conventionally written `O(1)`—and
there is no per-point allocation, external process, or coordinate cache.

## Numeric safeguards and boundary behavior

- Geographic arguments and frame dimensions must be finite and within their
  closed domains.
- Exact pole vectors remove longitude-dependent `cos(pi/2)` residue.
- Strict nearest-site comparison gives deterministic lowest-index ties;
  explicit pole handling gives the same face choices as that stable order.
- `-180°` and `+180°` public longitude produce identical rotated input.
- Gnomonic projection rejects a non-positive tangent-plane denominator.
- Shared-edge construction requires exactly two common vertices and
  non-degenerate projected edges.
- Tree construction validates parent indices, a single reachable root, and
  progress to all twenty faces.
- Frame validation checks ratio multiplication for overflow before comparing.
- Output is calculated from the registered transform rather than clamped to
  the frame; the valid fixed geometry places the tested global domain within
  the canvas.

At an ordinary Voronoi boundary, two sites are equally near. On a retained
hinge their two planar coordinates agree along the aligned edge. On a cut they
are two valid but separated images; stable face order chooses one. At an
icosahedron vertex five cells meet and the same rule applies.

## Verification

[`tests/test-voronoi-projection-api.cc`](../tests/test-voronoi-projection-api.cc)
verifies:

- the `projection_api` relationship, `voronoi` mode, source dimensions, and
  `48:25` compile-time ratio;
- all twenty sites selecting their own faces;
- the fixed parent tree and representative composed transforms for faces `1`
  and `19`;
- seventeen coordinates generated by `d3-geo-polygon` 1.12.1 at its default
  `960 x 500` registration, including both poles, both antimeridian spellings,
  all geographic sign quadrants, major cities, the Pacific, and Antarctica;
- seven variable frames ranging from height `1` through `4000`, including
  direct `frame::area` and fractional construction;
- proportional coordinates and finite in-frame results at every size;
- deliberate removal of input frame placement offsets;
- raster naming and runtime resource-path prefixing;
- rejection of wrong ratios, approximate ratios, non-positive dimensions,
  NaN, infinity, and overflow;
- every integer pair in a `181 x 361` whole-world grid, or 65,341 geographic
  inputs, covering poles, face boundaries, all quadrants, and cuts;
- exact `-180°`/`+180°` equivalence at five-degree latitude intervals; and
- rejection of non-finite or out-of-range latitude and longitude.

Run it with all standalone projection checks:

```sh
make check
```

## Limits and extension points

- Only the forward point transform is implemented. There is no inverse
  `(x,y)` to `(latitude,longitude)` operation.
- The geographic model is a sphere, not an ellipsoid.
- Gnomonic projection maps great circles to straight lines within a face, but
  it is not equal-area, conformal, or equidistant. Distortion grows away from
  each face site.
- Position is continuous across retained tree hinges, but derivatives need
  not agree across face boundaries. Non-tree edges are intentional map
  discontinuities.
- The point API does not reproduce D3's streaming polygon clipping, adaptive
  resampling, or inverse traversal. A renderer must split paths at net cuts
  rather than drawing a spurious segment across the canvas.
- The fixed sites, face order, parent tree, rotation, center, scale, and canvas
  define one D3-compatible map. Configurable Voronoi sites or alternate nets
  would require an additional topology and registration API.
- The raster filename is metadata. Any supplied image must already use the
  same projection, cuts, registration, crop, and aspect ratio.

## Provenance and licensing

The geometry, face ordering, parent tree, gnomonic-face choice, shared-edge
unfolding method, and registration values derive from the ISC-licensed
[`d3-geo-polygon` 1.12.1](https://github.com/d3/d3-geo-polygon/tree/v1.12.1),
commit `7f1e0ae42b6b3bb474f792f2c4b53bf4ff50f4ab`. Its `icosahedral.js` credits
the Icosahedral map implementation to Jason Davies (2013), Enrico Spinielli
(2017), and Philippe Rivière (2017–2018). The package and license identify
Mike Bostock as author and copyright holder.

The required 2017 Mike Bostock ISC notice is retained verbatim in
[`cart0freak0-voronoi.h`](../src/cart0freak0-voronoi.h). The C++ code has no
runtime D3 dependency, but removing the dependency does not remove the source
attribution or notice requirement.

See the [bibliography](voronoi-bibliography.md) for pinned file-level links,
D3's projection semantics, standard gnomonic background, related polyhedral
work, and the local verification record.

---

[Documentation index](../index.md) ·
[Geometric context](voronoi-context.md) ·
[Bibliography](voronoi-bibliography.md)
