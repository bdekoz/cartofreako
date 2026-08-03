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

The implementation deliberately separates three transformation stages:

1. `ck_native::forward_projection` supplies the established Cahill-Keyes
   half-octant construction and standard M-layout coordinates.
2. `star_x_detail::assemble_native_point()` applies the Star-X net
   rearrangement: keep the left four spatial face slots below, rotate the
   right four slots by 180 degrees, place them above, apply the configured
   symmetric inter-group spacing, and uniformly enlarge the assembled X
   about the page center. The default enlargement is 120 percent.
3. SVG composition helpers add the North-pole star and gather Natural Earth
   geometry south of 60 degrees south into one correctly scaled polar
   representation at the bottom of the page. This layer-aware step stays out
   of the one-point API so it does not also gather ocean and bathymetry.

This makes Star-X a real point projection while keeping its local geometry
numerically identical to the tested Cahill-Keyes implementation.

## Code organization

| Component | Responsibility |
| --- | --- |
| [`cart0freak0-star-x.h`](../src.projections/cart0freak0-star-x.h) | Frame contract, configurable group spacing and enlargement, polar-composition geometry, public API adapter, validation, and factory |
| [`cart0freak0-cahill-keyes.h`](../src.projections/cart0freak0-cahill-keyes.h) | Shared native half-octant formulas, M-layout assembly, and raster-registration longitude adjustment |
| [`a60-carto-projection.h`](../src.projections/a60-carto-projection.h) | Shared interface, projection state, and `star_x` mode |
| [`a60-carto-frame.h`](../src.projections/a60-carto-frame.h) | `frame` and `frame.frame_area` dimensions |
| [`a60-carto.h`](../src.projections/a60-carto.h) | Umbrella include and `starxwestate` whole-earth state |
| [`test-star-x-projection-api.cc`](../tests/test-star-x-projection-api.cc) | Reference anchors, assembly identity, global domain, scaling, validation, and API tests |
| [`generate-geometry.cc`](../src.generate/generate-geometry.cc) | Layered Star-X face geometry and the central North-pole star |
| [`natural-earth-generation.h`](../src.generate/natural-earth-generation.h) | Layer-aware land, ice, and coastline split plus unified Antarctica placement |

The repository renamed projection-specific headers from the former
`a60-carto-projection-*` prefix to `cart0freak0-*`. The implementation is
therefore in `src.projections/cart0freak0-star-x.h`, consistent with every other current
projection header.

## Coordinate conventions

| Layer | Call or result | Axes |
| --- | --- | --- |
| Public API | `(latitude, longitude)` in degrees | geographic |
| Cahill-Keyes native core | `(longitude, latitude)` in degrees | centered Cartesian, `x` right and `y` up |
| Normalized Star-X carrier | `(u, v)` in page fractions | `u` right and `v` down |
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
default signed carrier gap D = -(9/88)H
default inward shift per group T = -D/2 = (9/176)H
default page-centered enlargement E = 6/5
```

The two source groups are therefore congruent `G`-by-`G` squares. Their
local geometry is never stretched: group placement is rigid and the later
enlargement is uniform in both axes.
The remaining six carrier units become three-unit margins on the left and
right. Every source length and the default translation are multiplied by the
same scale, so varying the frame cannot alter angles or local Cahill-Keyes
proportions.

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
Let `R` be the configured signed carrier-gap ratio and `D=RH` its distance
in output-frame units. `R=0` reproduces the original edge-to-edge carrier
placement. Negative values overlap the invisible square carriers and pull
the visible octants toward the center. Let `E` be the configured positive
page-enlargement factor.

Group 1 is converted to screen axes and translated into the lower half:

```text
X1 = M + G + cx
Y1 = 3G/2 - cy + D/2
```

For group 2, the signs of both local coordinates are reversed—the 2D
rotation matrix for 180 degrees—and the result is translated into the upper
half:

```text
X2 = M + G - cx
Y2 = G/2 + cy - D/2
```

Equivalently, start with source-screen coordinates `(sx, sy)` in a `2G` by
`G` Cahill-Keyes map:

```text
sx = G + cx
sy = G/2 - cy

group 1: (X,Y) = (M + sx,       G + sy + D/2)
group 2: (X,Y) = (M + 2G - sx,  G - sy - D/2)
```

The second line makes the rigid 180-degree rotation particularly visible.
No latitude, longitude, or projected length is interpolated during net
assembly.

After either group formula, Stage 5 uniformly scales the assembled point
about the exact page center:

```text
X' = W/2 + E(X - W/2)
Y' = H/2 + E(Y - H/2)
```

Because both axes use the same `E`, this step changes neither angles nor the
local Cahill-Keyes scale ratio. For the 34-by-44 generator frame and default
`E=1.2`, the formula is the SVG-equivalent affine transform:

```text
matrix(1.2, 0, 0, 1.2, -3.4, -4.4)
```

The implementation evaluates these formulas once in a unit-height carrier:
`G=1/2`, `M=3/22`, `D=R`, and native scaffold altitude `1/4`. It divides
`X` by `17/22` to obtain normalized `u`, applies the centered enlargement in
normalized page coordinates, then multiplies `(u,v)` by the requested frame
dimensions. This is algebraically equivalent to constructing a separate
native scaffold at every output size.

### Stage 4: configurable group gap

`star_x_layout::group_gap_ratio` accepts a finite value in `[-1/2, 0]`.
Zero restores the former layout. The lower endpoint lets the two carrier
centers coincide; intermediate negative values reduce the visible space
without scaling, rotating, or otherwise changing an octant.

The default is:

```text
Rdefault = -9/88
Tdefault = -Rdefault H/2 = 9H/176
```

For the generator's 34-by-44 frame this is `D=-4.5`: group 2 moves down
`2.25` units and group 1 moves up `2.25` units. Their inward tips converge
at the 22-unit centerline instead of leaving the former broad central gap.

### Stage 5: configurable page enlargement

`star_x_layout::enlargement_factor` accepts any finite positive value. The
default is `1.2`, matching the requested 120-percent enlargement. A value of
`1` disables only this stage; it does not disable the configured group gap.
Values larger than the default are permitted for intentional crop and poster
layouts, so callers—not the point API—own any clipping decision.

The order is significant: the algorithm first rotates and places each group,
including the signed gap, and then scales the complete assembled result about
the page center. Scaling the two groups independently would also scale their
gap around two different centers and would not reproduce the reference
geometry.

### Stage 6: polar composition

Stage 6 adds two presentation elements after the point transform.

The North-pole mark is a regular eight-point star centered at `(W/2,H/2)`.
It alternates an outer radius of `(1.25/44)H` with an inner radius equal to
`0.4` of the outer radius. `make_north_pole_star()` returns its sixteen
vertices, beginning at the upper tip, so Izzi can emit a native SVG path.

Antarctica cannot be unified by the ordinary one-point API without also
redirecting every ocean, bathymetry, and graticule sample south of the cutoff.
The Natural Earth generator therefore clips land, minor islands, glaciated
areas, ice shelves, and coastline at `phi_c = -60 degrees`. Geometry north of
the cutoff follows the ordinary enlarged X. Southern geometry uses a local
South-polar azimuthal representation:

```text
r = (phi + 90 degrees) H E / 400
theta = lambda pi / 180
xp = r sin(theta)
yp = -r cos(theta)
```

The South Pole is the local origin and the prime meridian points upward. The
`H/400` scale follows the Cahill-Keyes canonical construction: one degree is
100 of 10,000 octant units and the Star-X scaffold altitude is `H/4`. The
same `E` as Stage 5 is applied, so the continent retains the map's geographic
scale instead of inheriting the deliberately oversized silhouette in the
reference artwork.

Placement is data-derived. If the projected Antarctic outline has local
bounds `[xmin,xmax] x [ymin,ymax]`, its translation is:

```text
dx = W/2 - (xmin + xmax)/2
dy = Ybottom - ymax
```

`Ybottom` is the lowest point of the enlarged Star-X octant geometry,
sampled over the integer-degree globe. Thus the continent is visually
centered on the page axis and its lower edge aligns with the lowest octant.
Ocean and bathymetry remain in the unfolded X; this preserves the global net
while the land, ice, and coastline layers present Antarctica once. The
checked-in
[`geometry-star-x-34-44.with-poles.svg`](../assets.static/adhoc/geometry-star-x-34-44.with-poles.svg)
establishes this visual intent only—none of its Antarctic path coordinates or
scale are copied.

## Pole placement and the X

The northern polar vertices of group 1 approach the frame's center from
below. After the 180-degree rotation, group 2's northern vertices approach
it from above. Their interrupted octahedral edges outline the central X.
The standard M net duplicates polar vertices at cuts, so the center is a
small polar locus rather than one artificially collapsed pixel. Historical
Star-X compositions place an eight-point star over that locus.

The southern polar copies remain near the two outer ends in the ordinary
point transform: group 2's South Pole is near the top and group 1's is near
the bottom. This is a consequence of rotating an entire four-face group, not
a special latitude case. The Stage 6 Natural Earth composition replaces the
fragmented Antarctic *land presentation* with one polar inset; it does not
silently change those public point coordinates.

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

To reproduce the former edge-to-edge carrier placement, pass an explicit
layout:

```c++
const a60::carto::star_x_layout original_layout {
  .group_gap_ratio = 0,
  .enlargement_factor = 1
};
const auto old_projection = a60::carto::make_star_x_projection(
  map_frame, "star-x-original-layout.svg", original_layout);
```

To keep the gap-closing adjustment but choose a different enlargement:

```c++
const a60::carto::star_x_layout layout {
  .enlargement_factor = 1.1
};
```

The factory retains only `map_frame.frame_area`; input placement offsets are
discarded because placement in a larger drawing belongs to `cartography`.
The optional name is metadata returned by `image_filename()` and does not
affect projection mathematics. `group_gap_ratio()` and
`enlargement_factor()` report the validated settings retained by the
projection.

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
2:1 M-layout rectangle and must not be applied to a 17:22 Star-X frame. The
shared generators instead split geographic paths by registered octant and
group before projection. The Stage 6 Antarctic branch clips source geometry
geographically before applying its continuous polar transform.

## Numeric safeguards

The normal Star-X point layer adds only addition, subtraction, division by
the constant aspect ratio, and uniform output scaling. The gap ratio must be
finite and within `[-1/2, 0]`; the enlargement must be finite and positive.
Validation occurs before the native call, so invalid layout and geographic
values receive public Star-X diagnostics. The optional Antarctic compositor
uses one sine and cosine per densified source point; its radius is linear in
co-latitude and becomes exactly zero at the South Pole.
The native projector remains immutable after its one-time function-local
static initialization and is safe for concurrent read-only calls.

## Verification

`tests/test-star-x-projection-api.cc` verifies:

- inheritance from `projection_api` and the `star_x` mode;
- every pole, seam, supple-zone, and city location used by
  `augment_carto_geo_specific`;
- the defining group transform against ordinary Cahill-Keyes coordinates on
  a 5-degree global grid;
- the default 2.25-unit inward translation and 120-percent page-centered
  enlargement on a 34-by-44 frame, plus exact recovery of the former
  coordinates when the gap is zero and enlargement is one;
- northern polar placement around the center and southern polar placement
  at the outer ends;
- finite, in-frame output for every integer latitude and longitude;
- exact uniform scaling across `17x22`, `34x44`, `1632x2112`, `5100x6600`,
  and fractional frames;
- use of `frame.frame_area` rather than input placement offsets;
- alternating radii and central symmetry of the eight-point polar star;
- the Antarctic polar origin, radius, orientation, and enlargement scale;
- strict aspect-ratio, gap-ratio, enlargement, and geographic-domain
  rejection; and
- raster-name behavior with and without a runtime data prefix.

The expected 1632-by-2112 anchors were calculated by applying the documented
rigid and centered-scale transforms to the independently Perl-derived 2112-by-1056
Cahill-Keyes fixture. This gives the test a numeric oracle without making a
historical raster the implementation.

The geometry generator additionally asserts one `north-pole-star` path. The
Natural Earth generators assert the unified land, ice-shelf, and coastline
paths while retaining exactly two Earth layer groups and 22 water-overlay
groups.

## Provenance and limitations

The local face projection is derived from Mary Jo Graça and Gene Keyes's
`MegamapMaker-prep9.pl`; its attribution and non-commercial-use terms remain
applicable. The two-group arrangement follows Benjamin De Kosnik's published
Star-X description and historical plate diagram. Full references and source
roles are in the [bibliography](star-x-bibliography.md).

This is a forward spherical projection. It does not provide an inverse,
ellipsoidal correction, or raster reconstruction. The point API does not
automatically replace Antarctic points with the composed inset: callers that
render geographic layers must opt into the supplied layer-aware helpers, as
the Natural Earth generators do. The 17:22 frame preserves the historical
carrier; the default centered enlargement reduces its former margins while
remaining inside the 34-by-44 page for the tested Star-X geometry.

---

[Documentation index](../index.md) ·
[Geometric context](star-x-context.md) ·
[Bibliography](star-x-bibliography.md)
