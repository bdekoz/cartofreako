# AuthaGraph C++20 implementation notes

[Documentation index](../index.md) ·
[Geometric context](authagraph-context.md) ·
[Bibliography](authagraph-bibliography.md)

## Scope and result

`a60::carto::agproj` is a native C++20 forward AuthaGraph projection for the
common `a60::carto::projection_api`. It transforms `(latitude, longitude)`
directly into `(x, y)` in a map frame. It does not invoke an external program,
sample a raster, or use the source PDF as a lookup table.

The numeric core follows Hajime Narukawa's 2022 analytic formulation. That
paper replaces the earlier modeling construction's curved intermediate
tetrahedron with four congruent cones so that the projection can be expressed
as formulas. The result closely approximates, but is not numerically identical
to, the earlier 96-region graphical construction. This distinction matters:
the implementation is the published analytic formulation, not a reverse
engineering of every point in the checked-in drawing sheet.

The work was delivered in three stages:

1. **Forward projection:** implement the spherical-to-planar formulas, orient
   the published tetrahedron on Earth, assemble its 24 symmetric regions, and
   expose the result through `projection_api`.
2. **Variable frames:** normalize the rectangular net and scale it to any
   finite, positive `frame.frame_area` with the required `4:sqrt(3)` ratio.
3. **Documentation:** record the geometric model, equations, source-plate
   calibration, API, validation, limitations, and bibliography.

## Code organization

| Component | Responsibility |
| --- | --- |
| [`a60-carto-projection-authagraph.h`](../src/a60-carto-projection-authagraph.h) | Numeric forward transform, net assembly, frame validation, API adapter, and A3 compatibility preset |
| [`a60-carto-projection.h`](../src/a60-carto-projection.h) | Shared `projection_api`, `projection_base`, and projection mode |
| [`a60-carto-frame.h`](../src/a60-carto-frame.h) | `frame` and `frame.frame_area` geometry |
| [`a60-carto.h`](../src/a60-carto.h) | Umbrella include that exports the projection |
| [`test-authagraph-projection-api.cc`](../tests/test-authagraph-projection-api.cc) | Reference coordinates, full-degree domain sweep, variable frames, validation, and API integration |
| [`a60-svg-carto-geo.h`](../src/a60-svg-carto-geo.h) | Geographic integration anchors exercised by the projection test |

Most implementation helpers live in `a60::carto::authagraph_detail`. They are
header-local `inline` functions so the projection retains the library's
header-oriented integration model.

## Coordinate conventions

The public and internal layers intentionally use different units and axes:

| Layer | Arguments or result | Convention |
| --- | --- | --- |
| `projection_api::meridians_to_point_2d` | `(latitude, longitude)` | degrees |
| Internal geographic vector | `(longitude, latitude)` | radians on a unit sphere |
| Unfolded tetrahedron | `(qx, qy)` | Cartesian, `y` upward |
| Normalized map | `(u, v)` | unit rectangle, `v` downward |
| Public result | `(x, y)` | frame coordinates, origin at upper left |

The public method accepts finite latitude in `[-90, 90]` and longitude in
`[-180, 180]`. Invalid values throw `std::invalid_argument`.

## Forward transform

### 1. Geographic vector

For longitude `lambda` and latitude `phi`, both in radians, form a unit vector:

```text
g = (cos(phi) cos(lambda),
     cos(phi) sin(lambda),
     sin(phi))
```

The implementation treats Earth as a sphere, matching the simplifying model
used in the 2022 paper. It does not apply ellipsoidal flattening.

### 2. AuthaGraph tetrahedron orientation

The four published vertices are stored in this implementation order:

| `i` | Latitude | Longitude |
| ---: | --- | --- |
| 0 | 76° 52′ 51.82608″ N | 149° 27′ 03.56868″ E |
| 1 | 27° 57′ 09.99792″ S | 97° 21′ 25.2126″ E |
| 2 | 22° 55′ 41.65104″ S | 133° 16′ 57.93168″ W |
| 3 | 6° 38′ 13.37028″ S | 18° 51′ 08.037″ W |

After conversion to unit vectors `p[i]`, every distinct pair has dot product
approximately `-1/3`, and the four vectors sum approximately to zero. Those
are useful checks that the coordinates form a regular tetrahedron centered on
the sphere.

The closest tetrahedral vertex supplies the local pole:

```text
i = arg max dot(g, p[i])
```

An exact boundary tie is resolved by the lower array index. The adjacent
vertex `p[(i + 1) mod 4]` defines the reference meridian in that local system.

### 3. Local longitude and latitude

Let `p = p[i]`, `r = p[(i + 1) mod 4]`, and project `r` into the tangent plane
at `p`:

```text
t = normalize(r - p * dot(p, r))
h = t cross g

lambda_l = atan2(dot(p, h), dot(t, g))
phi_l    = asin(clamp(dot(p, g), -1, 1))
```

`lambda_l` is local longitude around the selected vertex and `phi_l` is local
latitude measured toward it. The cross-product order is part of the adopted
orientation; reversing it mirrors the assembled map.

### 4. Select one of six symmetric sectors

Each nearest-vertex region is divided into six 60-degree sectors. With
`alpha = pi/3`:

```text
s = floor((lambda_l + alpha) / alpha) mod 6
lambda_hat = positive_mod(lambda_l + alpha, 2 alpha) - alpha
```

Thus `lambda_hat` lies in `[-pi/3, pi/3)`. A global sector number
`n = 6i + s` identifies one of 24 congruent spherical regions. The 2022 paper
uses tetrahedral symmetry to reduce the analytic derivation to one such
1/24-region. The earlier graphical method additionally split those regions
into four, producing 96 control regions.

### 5. Project the canonical 1/24-region

The code evaluates the following form of Narukawa's equations 2.22 and 2.23:

```text
c = ((2 + cos(lambda_hat)) cos(phi_l))
    / (sqrt(2) cos(phi_l) + sin(phi_l))

x_t = (2/pi) c
      (lambda_hat - asin(sin(lambda_hat) / sqrt(3)))

y_t = (sqrt(2) - c) / sqrt(3)
```

The argument of `asin` is clamped to `[-1, 1]` to contain floating-point
roundoff at boundaries. In the canonical triangle, the selected tetrahedron
vertex is at `(0, sqrt(2/3))`, the opposite edge midpoint is at `(0, 0)`, and
the two outer edge endpoints are at `(±sqrt(2)/3, 0)`.

The formula preserves the intended area relationship for meridionally divided
subregions. It does not make the complete map locally equal-area at every
point; Narukawa's distortion analysis explicitly reports remaining local area,
angular, and distance distortion.

### 6. Assemble the periodic tetrahedral net

Let:

```text
l0 = sqrt(2/3)
v0 = (1, 0)
v1 = (1/2, sqrt(3)/2)
O  = l0 (a v0 + b v1)
```

For every global sector `n`, a table supplies the integer origin coefficients
`(a, b)` and a rotation `r` measured in sixths of `pi`:

| Vertex `i` | `s=0` | `s=1` | `s=2` | `s=3` | `s=4` | `s=5` |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `(1,1; -1)` | `(1,1; -1)` | `(2,1; +1)` | `(2,1; +1)` | `(2,2; +3)` | `(0,2; -3)` |
| 1 | `(0,0; -3)` | `(2,0; +3)` | `(1,1; +5)` | `(1,1; +5)` | `(0,1; -5)` | `(0,1; -5)` |
| 2 | `(3,1; +5)` | `(3,1; +5)` | `(2,1; -5)` | `(2,1; -5)` | `(2,0; -3)` | `(4,0; +3)` |
| 3 | `(0,2; +3)` | `(2,2; -3)` | `(3,1; -1)` | `(3,1; -1)` | `(0,1; +1)` | `(0,1; +1)` |

Each cell is `(a,b;r)`. With the usual 2D rotation matrix `R`, the unfolded
point is:

```text
q = R(r pi/6) (x_t, y_t) + O
```

The table is deliberately explicit. It makes the chosen cuts, orientation,
and periodic edge pairing inspectable, and avoids a fragile chain of special
cases. See the [geometric context](authagraph-context.md#the-24-sector-net) for
an annotated net.

### 7. Normalize and register the rectangle

The raw net has dimensions:

```text
W0 = 4 sqrt(2/3)
H0 = sqrt(2)
W0 / H0 = 4 / sqrt(3)
```

The normalized coordinates are:

```text
u = positive_mod(qx / W0 + delta, 1)
v = 1 - clamp(qy / H0, 0, 1)
```

where `delta = -0.08797138953590078`. This is a cyclic horizontal shift of the
periodic net. It places the cuts and tetrahedron vertices in the same map
registration as the checked-in A3 source plate; it does not change local
projection geometry.

### 8. Scale into `frame.frame_area`

For a map viewport with origin `(ox, oy)`, width `W`, and height `H`:

```text
X = ox + u W
Y = oy + v H
```

The generic factory creates a map-only viewport at `(0, 0)` and uses only the
passed frame's `frame_area`. Placement offsets on that input frame are ignored;
layout within a larger canvas belongs to the surrounding cartography code.
The A3 compatibility preset is the exception: it keeps the full PDF page as
`pframe` and its measured map rectangle as `map_frame`.

## Variable-size frame contract

A valid AuthaGraph map frame must satisfy:

```text
W and H are finite
W > 0 and H > 0
W = (4 / sqrt(3)) H
```

`is_authagraph_frame()` compares `W` to `(4/sqrt(3))H` with this tolerance:

```text
16 * epsilon(double) * max(W, expected_W)
```

The tolerance admits ordinary floating-point rounding, not an approximate
aspect ratio. `1920x1080`, `2x1`, zero, negative, NaN, infinity, and
overflowing dimensions are rejected.

## Public API and usage

Construct a map-only projection from any valid `frame::area`:

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

// The API accepts latitude first, then longitude.
const auto [x, y]
  = projection.meridians_to_point_2d(40.7128, -74.0060);
```

The raster name is optional and affects `image_filename()` only. The generic
projection does not inspect an image or infer its dimensions. If a raster is
supplied, it must already use the same projection, crop, cyclic registration,
and aspect ratio.

The checked-in A3 drawing-sheet preset remains available:

```c++
const a60::carto::projection_api& projection = a60::carto::ag_a3;
const auto [x, y] = projection.meridians_to_point_2d(0, 0);
```

`ag_a3` returns page coordinates because the map is embedded within the PDF
page. Use `make_authagraph_projection()` when the desired coordinate system is
the map rectangle itself.

## A3 source-plate calibration

The compatibility preset is registered to
[`15-SP-TESD-03-AG.pdf`](../assets/authagraph/15-SP-TESD-03-AG.pdf).

| Measurement | Value in PDF points |
| --- | ---: |
| Full page width | 1190.55 |
| Full page height | 841.89 |
| Map left | 107.101118 |
| Map top | 199.632551 |
| Map width | 976.1626648661487 |
| Map height | 422.690833 |
| Projected `(0°, 0°)` x | 120.05917135268346 |
| Projected `(0°, 0°)` y | 267.89452133439636 |

The asset is a one-page A3 PDF created by Adobe Illustrator. Its SHA-256 is:

```text
65c053590f2693038d8d4db3fbc2c6858d7c79705072f195adf2bf2f386f4805
```

The analytic and earlier graphical constructions are close rather than
identical, so the calibration establishes a compatible viewport and cyclic
registration. It should not be read as a promise of pixel-perfect coastline
agreement everywhere on the plate.

## Numeric safeguards

- Geographic inputs and frame dimensions must be finite.
- Latitude and longitude use closed, explicitly checked degree domains.
- Dot products passed to `asin` are clamped to `[-1, 1]`.
- The sector operation uses positive modular arithmetic, including at the
  antimeridian.
- Longitude `-180` and `+180` map to equivalent periodic positions.
- The normalized vertical coordinate is clamped for boundary roundoff.
- Frame-ratio multiplication is checked for finite output before comparison.
- The A3 embedded viewport must be finite, positive, ratio-correct, and wholly
  contained by its page frame.

## Verification

`tests/test-authagraph-projection-api.cc` exercises:

- all 27 positions used by `augment_carto_geo_specific`, against independently
  calculated expected coordinates;
- the four published singular vertices against locations measured in the PDF;
- every integer latitude/longitude pair in a `181 x 361` global grid;
- antimeridian equivalence and finite, in-bounds results;
- invalid geographic arguments;
- six projection sizes, from unit scale through a 6,600-unit height, including
  direct `frame::area` construction and fractional dimensions;
- rejection of wrong ratios and non-finite, non-positive, or overflowing
  dimensions;
- generic map-only placement and A3 embedded-viewport behavior; and
- runtime resource paths and the public `projection_api` interface.

Run all standalone projection checks with:

```sh
make check
```

## Limits and extension points

- Only the forward transform is implemented; there is no `(x, y)` to
  longitude/latitude inverse.
- The geographic model is spherical, not ellipsoidal.
- The projection has intentional cuts. Lines that cross a periodic seam must
  be split by rendering code rather than connected across the page.
- The analytic 2022 formulation approximates the original graphical
  construction and retains local distortion. It should be described as an
  AuthaGraph or equal-area-type projection, not as a rigorously equal-area
  implementation at every point.
- The assembly and horizontal shift encode one useful world-map aspect.
  Alternative periodic aspects can be produced by changing the net cut and
  registration, but doing so should be accompanied by new reference tests.
- A future inverse should define behavior on duplicated seam coordinates and
  singular tetrahedron vertices explicitly.

## Provenance

The formulas, tetrahedron orientation, and distinction between the earlier
96-region method and the analytic approximation are sourced in Narukawa's
primary publications. The checked-in PDF supplies the compatibility viewport,
not the projection equations. Full citations and links are in the
[AuthaGraph bibliography](authagraph-bibliography.md).

---

[Documentation index](../index.md) ·
[Geometric context](authagraph-context.md) ·
[Bibliography](authagraph-bibliography.md)
