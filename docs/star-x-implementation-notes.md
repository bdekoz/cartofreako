# Star-X C++20 implementation notes

[Documentation index](../index.md) ·
[Geometric context](star-x-context.md) ·
[Bibliography](star-x-bibliography.md)

## Scope and result

`a60::carto::starxproj` is a direct C++20 forward Star-X projection for the
common `a60::carto::projection_api`. It accepts `(latitude, longitude)` and
returns one `(x, y)` point in a portrait map frame. It does not render four
temporary Cahill-Keyes images, crop raster tiles, or depend on an external
projection process.

The implementation deliberately separates two operations:

1. `ck_native::forward_projection` supplies the established Cahill-Keyes
   half-octant construction and standard M-layout coordinates.
2. `star_x_detail::assemble_native_point()` applies only the Star-X net
   rearrangement: keep the left four spatial face slots below, rotate the
   right four slots by 180 degrees, and place them above.

This makes Star-X a real point projection while keeping its local geometry
numerically identical to the tested Cahill-Keyes implementation.

## Code organization

| Component | Responsibility |
| --- | --- |
| [`cart0freak0-star-x.h`](../src/cart0freak0-star-x.h) | Frame contract, two-group assembly, public API adapter, input validation, and factory |
| [`cart0freak0-cahill-keyes.h`](../src/cart0freak0-cahill-keyes.h) | Shared native half-octant formulas, M-layout assembly, and raster-registration longitude adjustment |
| [`a60-carto-projection.h`](../src/a60-carto-projection.h) | Shared interface, projection state, and `star_x` mode |
| [`a60-carto-frame.h`](../src/a60-carto-frame.h) | `frame` and `frame.frame_area` dimensions |
| [`a60-carto.h`](../src/a60-carto.h) | Umbrella include and `starxwestate` whole-earth state |
| [`test-star-x-projection-api.cc`](../tests/test-star-x-projection-api.cc) | Reference anchors, assembly identity, global domain, scaling, validation, and API tests |

The repository renamed projection-specific headers from the former
`a60-carto-projection-*` prefix to `cart0freak0-*`. The implementation is
therefore in `src/cart0freak0-star-x.h`, consistent with every other current
projection header.

## Coordinate conventions

| Layer | Call or result | Axes |
| --- | --- | --- |
| Public API | `(latitude, longitude)` in degrees | geographic |
| Cahill-Keyes native core | `(longitude, latitude)` in degrees | centered Cartesian, `x` right and `y` up |
| Normalized Star-X carrier | `(u, v)` in `[0,1]` frame fractions | `u` right and `v` down |
| Public result | `(x, y)` in `frame.frame_area` | screen coordinates, origin at upper left |

The public method accepts finite latitude in `[-90, 90]` and finite
longitude in `[-180, 180]`. Values outside those closed intervals throw
`std::invalid_argument` with a Star-X-specific message.

## Shared Cahill-Keyes calculation

Star-X changes the net, not the map within a face. The native core still:

- normalizes a location into one of eight geographic octants and sixteen
  mirrored half-octants;
- evaluates the same A–L piecewise graticule construction;
- uses the same line, circle, interpolation, and supple-zone formulas; and
- applies the same per-octant rotations and reflections that create the
  Cahill-Keyes M layout.

Those formulas and their constants are documented in the
[Cahill-Keyes implementation notes](cahill-keyes-implementation-notes.md).
Keeping that implementation as the numerical authority avoids a second
copy of a long, piecewise algorithm and guarantees that future corrections
to the local construction reach both projections.

The one-degree Visionscarto registration is also shared through:

```text
lambda_r = lambda + 1 degree
if lambda_r > 180 degrees:
    lambda_r -= 360 degrees
```

This adjustment is project registration, not part of the historical
Cahill-Keyes specification. Sharing one function prevents the two public
projections from drifting at their longitude seams.

## Face-group terminology

The standard M layout interleaves official geographic octant numbers:

```text
source left half                 source right half
[ octants 1 and 6 ][ 2 and 7 ] [ 3 and 8 ][ 4 and 5 ]
  spatial slots 1–2   3–4         5–6        7–8
```

Consequently, Star-X “group 1, slots 1–4” means the four faces on the
source M map's left side, not official geographic octants 1, 2, 3, and 4.
Group 2 contains spatial slots 5–8 on the right side. This interpretation
matches both the requested left/right split and the historical four-plate
layout. See the [geometric context](star-x-context.md#face-numbers-and-spatial-slots)
for the complete mapping.

In centered native coordinates the split is exact and scale-independent:

```text
group 1: ck_x < 0
group 2: ck_x >= 0
```

The boundary belongs to group 2. With the shared registration adjustment,
group 2 covers public longitudes from -21 degrees inclusive to 159 degrees
exclusive. Group 1 covers the complementary interval across the
antimeridian.

## Frame-derived scale and aspect ratio

The historical arrangement used four 17-by-22-inch portrait plates in a
two-by-two composition, producing a 34-by-44 carrier. Reducing that ratio
gives the variable-frame contract:

```text
W > 0
H > 0
W / H = 17 / 22
W and H are finite
```

Let one carrier unit be `s = H/22`. Then:

```text
carrier width W = 17s
carrier height H = 22s
group square side G = 11s = H/2
side margin M = 3s = (W-G)/2
Cahill-Keyes source viewport = 2G by G
Cahill-Keyes scaffold MG = G/2 = H/4
```

The two source groups are therefore congruent `G`-by-`G` squares. They are
stacked without stretching, and the remaining six carrier units become
three-unit margins on the left and right. Every source length is multiplied
by the same scale, so varying the frame cannot alter angles or local
Cahill-Keyes proportions.

`is_star_x_frame()` compares `W` with `(17/22)H` using:

```text
tolerance = 16 * epsilon(double) * max(W, expected_W)
```

The tolerance accepts floating-point roundoff only. A conventional 2:1
Cahill-Keyes frame, an approximate 17:22 frame, zero, negative, NaN, and
infinite dimensions are rejected.

## The Star-X assembly formulas

Let `(cx, cy)` be the centered Cartesian result from the Cahill-Keyes
projector configured with scaffold altitude `H/4`. Thus `cx` spans the two
source groups, `cy` is positive upward, `G=H/2`, and `M=(W-G)/2`.

Group 1 is converted to screen axes and translated into the lower half:

```text
X1 = M + G + cx
Y1 = 3G/2 - cy
```

For group 2, the signs of both local coordinates are reversed—the 2D
rotation matrix for 180 degrees—and the result is translated into the upper
half:

```text
X2 = M + G - cx
Y2 = G/2 + cy
```

Equivalently, start with source-screen coordinates `(sx, sy)` in a `2G` by
`G` Cahill-Keyes map:

```text
sx = G + cx
sy = G/2 - cy

group 1: (X,Y) = (M + sx,       G + sy)
group 2: (X,Y) = (M + 2G - sx,  G - sy)
```

The second line makes the rigid 180-degree rotation particularly visible.
No latitude, longitude, or projected length is interpolated during net
assembly.

The implementation evaluates these formulas once in a unit-height carrier:
`G=1/2`, `M=3/22`, and native scaffold altitude `1/4`. It divides `X` by
`17/22` to obtain normalized `u`, then multiplies `(u,v)` by the requested
frame dimensions. This normalized implementation is algebraically
equivalent to constructing a separate native scaffold at every output size.

## Pole placement and the X

The northern polar vertices of group 1 approach the frame's center from
below. After the 180-degree rotation, group 2's northern vertices approach
it from above. Their interrupted octahedral edges outline the central X.
The standard M net duplicates polar vertices at cuts, so the center is a
small polar locus rather than one artificially collapsed pixel. Historical
Star-X compositions place an eight-point star over that locus.

The southern polar copies remain near the two outer ends: group 2's South
Pole is near the top and group 1's is near the bottom. This is a consequence
of rotating an entire four-face group, not a special latitude case.

## Public C++ API

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

const auto [x, y]
  = projection.meridians_to_point_2d(40.7128, -74.0060);
```

The factory retains only `map_frame.frame_area`; input placement offsets are
discarded because placement in a larger drawing belongs to `cartography`.
The optional name is metadata returned by `image_filename()` and does not
affect projection mathematics.

`starxproj` also accepts a validated `projection_base`, preserving the
construction shape used by existing projections. `make_star_x_projection()`
sets `longitude_zero_x` and `latitude_zero_y` to the projected location of
geographic `(0,0)`.

## Cuts and projected paths

Star-X inherits every cut between Cahill-Keyes octants and introduces the
major group cut at the two M-layout half boundaries. A point is always
defined, including on a deterministic boundary side, but a renderer must not
join two projected samples across a cut with a straight SVG segment.

The existing `cart0freak0-cahill-keyes-functions.h` helper is specific to a
2:1 M-layout rectangle and must not be applied to a 17:22 Star-X frame. A
future Star-X coastline or graticule generator should split geographic paths
by octant and group before projection, or provide a Star-X-specific edge
folding helper. The point projection and `augment_carto_geo_specific` anchors
do not require path interpolation.

## Numeric safeguards

The Star-X layer adds no trigonometric approximation. Its only arithmetic
after the Cahill-Keyes result is addition, subtraction, division by the
constant aspect ratio, and output scaling. Validation occurs before the
native call, so invalid geographic values receive public Star-X diagnostics.
The native projector remains immutable after its one-time function-local
static initialization and is safe for concurrent read-only calls.

## Verification

`tests/test-star-x-projection-api.cc` verifies:

- inheritance from `projection_api` and the `star_x` mode;
- every pole, seam, supple-zone, and city location used by
  `augment_carto_geo_specific`;
- the defining group transform against ordinary Cahill-Keyes coordinates on
  a 5-degree global grid;
- northern polar placement around the center and southern polar placement
  at the outer ends;
- finite, in-frame output for every integer latitude and longitude;
- exact uniform scaling across `17x22`, `34x44`, `1632x2112`, `5100x6600`,
  and fractional frames;
- use of `frame.frame_area` rather than input placement offsets;
- strict aspect-ratio and geographic-domain rejection; and
- raster-name behavior with and without a runtime data prefix.

The expected 1632-by-2112 anchors were calculated by applying the documented
rigid transforms to the independently Perl-derived 2112-by-1056
Cahill-Keyes fixture. This gives the test a numeric oracle without making a
historical raster the implementation.

## Provenance and limitations

The local face projection is derived from Mary Jo Graça and Gene Keyes's
`MegamapMaker-prep9.pl`; its attribution and non-commercial-use terms remain
applicable. The two-group arrangement follows Benjamin De Kosnik's published
Star-X description and historical plate diagram. Full references and source
roles are in the [bibliography](star-x-bibliography.md).

This is a forward spherical projection. It does not provide an inverse,
ellipsoidal correction, polygon clipping, or a raster reconstruction. The
17:22 frame preserves the historical carrier; the projected net itself uses
only the central 11:22 strip, leaving intentional three-unit side margins.

---

[Documentation index](../index.md) ·
[Geometric context](star-x-context.md) ·
[Bibliography](star-x-bibliography.md)
