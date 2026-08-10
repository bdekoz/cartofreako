# Star-X C++20 implementation notes

[Documentation index](../../../../index.md) ·
[Geometric context](context.md) ·
[Bibliography](bibliography.md)

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
3. SVG composition helpers add the North-pole star and apply the current
   Antarctic cap. Every source geometry at or south of the fixed `60°S`
   parallel is reassembled at the bottom of the page. The transform preserves
   each point's ordinary Star-X distance from its source South-Pole tip, and
   the projected boundary is registered with proportional bottom clearance.
   Cut membership and placement use only projection geometry; Natural Earth
   or another thematic dataset supplies content, never transform parameters.

This makes Star-X a real point projection while keeping its local geometry
numerically identical to the tested Cahill-Keyes implementation.

## Current normative constants

| Concern | Current value | Meaning |
| --- | ---: | --- |
| Carrier aspect | `17:22` | Scalable portrait frame inherited from the 34-by-44 composition |
| Signed group gap | `-9/88 H` | Pulls each group inward by `9/176 H` |
| Page enlargement | `1.2` | Uniform scale about `(W/2,H/2)` after group assembly |
| Antarctic cutoff | `-60°` | `phi <= -60°` belongs to the composed cap |
| Cap bearing offset | `0°` | Longitude is used as geographic bearing around the shared pole |
| Boundary sampling | `0.25°` | 1,440 intervals around the complete parallel |
| Cap center x | `W/2` | Shared South Pole lies on the page axis |
| Boundary clearance | `H(0.25/44)` | Bottommost cap boundary remains inside the frame |
| Antarctic paint order | last within each thematic layer | Unified cap is above every ordinary quadrant |

These values define the current generated composition. The ordinary public
point transform remains separately available for carrier diagnostics and
backward compatibility.

## Code organization

| Component | Responsibility |
| --- | --- |
| [`cart0freak0-star-x.h`](../../../../src.projections/cart0freak0-star-x.h) | Frame contract, configurable group spacing and enlargement, polar-composition geometry, public API adapter, validation, and factory |
| [`cart0freak0-star-x-functions.h`](../../../../src.projections/cart0freak0-star-x-functions.h) | Eight-cell seam topology, retained-hinge detection, and paired boundary routing for projected paths |
| [`cart0freak0-projection-runtime.h`](../../../../src.projections/cart0freak0-projection-runtime.h) | API 3 component-aware structured forward, carrier/cap reverse solvers, candidate enumeration, and residual checks |
| [`cart0freak0-cahill-keyes.h`](../../../../src.projections/cart0freak0-cahill-keyes.h) | Shared native half-octant formulas, M-layout assembly, and raster-registration longitude adjustment |
| [`a60-carto-projection.h`](../../../../src.projections/a60-carto-projection.h) | Shared interface, projection state, and `star_x` mode |
| [`a60-carto-frame.h`](../../../../src.projections/a60-carto-frame.h) | `frame` and `frame.frame_area` dimensions |
| [`a60-carto.h`](../../../../src.projections/a60-carto.h) | Umbrella include and `starxwestate` whole-earth state |
| [`test-star-x-projection-api.cc`](../../../../tests/test-star-x-projection-api.cc) | Reference anchors, assembly identity, global domain, scaling, validation, and API tests |
| [`generate-geometry.cc`](../../../../src.generate/generate-geometry.cc) | Layered Star-X face geometry and the central North-pole star |
| [`natural-earth-generation.h`](../../../../src.generate/natural-earth-generation.h) | Dataset clipping against the projection-defined `60°S` cap, radius-preserving all-layer reassembly, and topmost Antarctic paint order |
| [`generate-graticules.cc`](../../../../src.generate/generate-graticules.cc) | Cap-aware latitude/longitude splitting and visible current source/destination boundaries |

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
[Cahill-Keyes implementation notes](../cahill-keyes/implementation.md).
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
layout. See the [geometric context](context.md#face-numbers-and-spatial-slots)
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

### Stages 6, 13, and 14: polar composition

Stage 6 adds two presentation elements after the point transform.

The North-pole mark is a regular eight-point star centered at `(W/2,H/2)`.
It alternates an outer radius of `(1.25/44)H` with an inner radius equal to
`0.4` of the outer radius. `make_north_pole_star()` returns its sixteen
vertices, beginning at the upper tip, so Izzi can emit a native SVG path.

Stage 13 simplified Stage 7's data-derived boundary to a fixed geographic
cut; Stage 14 made its placement projection-only and retained a visible lower
clearance. A point belongs to the cap exactly when:

```text
phi <= -60 degrees
```

The decision no longer depends on maximum land distance, a varying boundary
latitude, or a bisection. Let `Q(lambda)` select the practical Star-X quadrant
using the registered cuts at `-111`, `-21`, `69`, and `159` degrees. Let
`S_q` be that quadrant's South-Pole tip and let `P(phi,lambda)` be the ordinary
Stage 5 Star-X point. The transform still preserves the source radius:

```text
rho(phi,lambda) = length(P(phi,lambda) - S_Q(lambda))
```

GDAL intersects each practical source quadrant with the constant-latitude
polygon from the South Pole through `60°S`. Geometry north of that line stays
in the ordinary X; geometry on or south of it moves to the unified cap. The
diagnostic `radius` is only the maximum projected source radius sampled along
the `60°S` boundary. It validates frame fit and labels the graticule guide; it
does not decide cap membership or rescale geometry.

A single rigid rotation per quadrant is insufficient. Cahill-Keyes boundary
meridians bend below its small near-pole construction zone, so a rotation
that joins one latitude opens a gap at another. The compositor instead keeps
each point's exact source radius and normalizes only its geographic bearing:

```text
theta = lambda pi / 180
xcap = Cx + rho sin(theta)
ycap = Cy - rho cos(theta)
```

This is a pointwise rotation around the quadrant tip, not a rescaled polar
substitute. Adjacent cut meridians coincide at every latitude, the four land
pieces form one mass, and every radius remains exactly the ordinary Star-X
radius. Zero bearing offset gives the reassembled continent a stable
geographic orientation.

The unified South Pole has `Cx = W/2`. Its vertical coordinate is derived
from the complete projected `60°S` boundary, not from a continent, coastline,
or land mask. Let `Ly` be a boundary point's local cap y coordinate and let
`B=max(Ly)` across quarter-degree longitude samples. Then:

```text
bottom_clearance = H * (0.25 / 44)
Cy = H - bottom_clearance - B
```

Consequently the bottommost cap-boundary point is at
`H-bottom_clearance`. It is `0.25` units above the lower view-box edge on the
canonical `34 × 44` plate and scales with every valid 17:22 frame. This moves
the reconstructed Antarctic component upward only far enough to keep the
blue boundary stroke visible. Registration is deterministic before any
source dataset is opened, and `make generate-graticules-star-x` no longer has
a Natural Earth prerequisite.

The same cap operation applies to ocean, land, all twelve bathymetry levels,
minor islands, ice, lakes, playas, rivers, reefs, and coastline, so neither
source geometry nor a polar ocean is duplicated. The graticule generator applies
the identical membership test and mapping; its `antarctic-cap-boundaries`
layer draws the four projected `60°S` source segments and the unified
destination boundary. The layer compositor queues ordinary quadrant paths
separately from cap paths and serializes every transformed Antarctic fragment
last within its thematic layer. Because SVG uses document paint order, this
makes the unified
cap visibly topmost instead of allowing a later source feature or longitude
band to clip it. Layers that contain only Antarctic geometry satisfy the same
contract vacuously.
The
checked-in
[`geometry-star-x-34-44.with-poles.svg`](../../../../assets.static/adhoc/geometry-star-x-34-44.with-poles.svg)
establishes this visual intent only—none of its Antarctic path coordinates or
scale are copied.

## Pole placement and the X

The northern polar vertices of group 1 approach the frame's center from
below. After the 180-degree rotation, group 2's northern vertices approach
it from above. Their interrupted octahedral edges outline the central X.
The standard M net duplicates polar vertices at cuts, so the center is a
small polar locus rather than one artificially collapsed pixel. Historical
Star-X compositions place an eight-point star over that locus.

The four southern polar copies remain at the outer tips in the ordinary point
transform. This is a consequence of rotating an entire four-face group, not
a special latitude case. The composed cap leaves those public point
coordinates unchanged; cap-aware generators explicitly cut the four source
quadrants at `60°S` and route their southern contents to the shared South Pole.

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
Star-X router in `cart0freak0-star-x-functions.h` operates in geographic
space instead. Its eight cells are the four registered longitude sectors and
their southern partners. For each original source edge it locates the first
cell transition, bisects to the two one-sided geographic limits, projects
both, and classifies their relationship in the assembled net:

- transitions at `-21 degrees` and `159 degrees` cross between the lower
  group and the 180-degree-rotated upper group and are inter-group folds;
- separated copies at `-111 degrees`, `69 degrees`, or the equator are
  intra-group folds; and
- coincident copies are retained hinges and stay in one SVG subpath.

A fold ends the current path at the first boundary copy and resumes it at the
paired copy. Those points lie on the actual face edges of the assembled X;
they are not extended to the rectangular page boundary. The shared generator
repeats this operation until the source endpoint is reached, so one coarse
edge may cross several folds. It interprets a `+180/-180` change as the short
continuous antimeridian arc; an intentionally long route needs an
intermediate waypoint.

Filled Natural Earth geometry receives an additional equatorial clip:
northern and southern rings are closed separately before projection. This
matters at the cyclic `159 degrees E / 201 degrees W` octant, where one ring
spanning both hemispheres otherwise bridges the lower-left exterior notch
when SVG applies its fill rule. Stable `-north` and `-south` path-ID suffixes
make the split testable. In Stage 13, each longitude band is split at the
fixed `60°S` parallel before the southern portion receives the continuous
radius-preserving cap transform. The cap projection is a separate continuous
mapping and is not passed through ordinary Star-X edge routing.

## Forward and reverse consequence

There are two useful forward components and therefore two corresponding
reverse paths:

1. **Ordinary carrier.** This is the backward-compatible public `starxproj`
   point result for all latitudes. Its implemented reverse exactly undoes page
   enlargement, group placement, and the group-two 180-degree rotation, then
   delegate the recovered M-layout candidate to the checked face-qualified
   Cahill–Keyes inverse.
2. **Unified Antarctic cap.** A composed forward routes `phi <= -60°` through
   `project_antarctic_fragment()` and the projection-only registration above.
   Its implemented reverse first subtracts the registered pole, recovers longitude bearing
   with `atan2(dx,-dy)`, and performs a bounded numerical solve for latitude in
   `[-90°,-60°]` against `antarctic_source_radius()`. Every candidate must be
   passed forward again and accepted only within the public residual tolerance.

The fixed cutoff and data-independent registration remove the former obstacle
to a reproducible cap inverse. They do not make the complete page globally
one-to-one: the ordinary carrier and overpainted cap can overlap, the pole has
no unique longitude, and the `60°S` boundary is a cut. Runtime results must
therefore retain component and native-cell identity and use the existing
`unique`, `ambiguous`, `cut`, and `outside` statuses. Runtime API 3 now exposes
both paths, advertises `inverseMode: "candidates"`, accepts optional
`nativeCell` and `component` qualifiers, and forces every candidate through
the matching forward component before acceptance. Structured forward calls
use carrier component `0` for `phi > -60°` and cap component `1` otherwise.
At the South Pole, a component-1 reverse without a native-cell qualifier
returns four stable quadrant-center longitude representatives because no
single longitude is geographically authoritative there.

## Numeric safeguards

The normal Star-X point layer adds only addition, subtraction, division by
the constant aspect ratio, and uniform output scaling. The gap ratio must be
finite and within `[-1/2, 0]`; the enlargement must be finite and positive.
Validation occurs before the native call, so invalid layout and geographic
values receive public Star-X diagnostics. The optional Antarctic compositor
uses one ordinary Star-X projection, distance, sine, and cosine per densified
source point. Its radius is measured from the selected source tip and becomes
exactly zero at the South Pole. Cap membership is one latitude comparison;
the former 56-iteration boundary bisection is gone. The constant-latitude cap
polygons must pass GEOS validity checks. Projection-only registration samples
the complete boundary at `0.25°`, validates finite radius and local extent,
and places its bottom at `H - H(0.25/44)`; the complete registered cap must fit
inside the output frame.

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
- each South-Pole tip being the farthest sampled point from page center in
  its practical quadrant;
- exact Antarctic source-radius preservation and agreement of all four cap
  seams at several southern latitudes;
- projection-only fixed-cap registration, including the exact `60°S` cutoff,
  zero bearing offset, complete quarter-degree boundary, horizontal centering,
  and proportional `0.25/44` lower clearance;
- forward and reverse paired-edge routing at all four registered seams in
  both hemispheres, including inter-group folds, intra-group folds, retained
  hinges, and equatorial transitions;
- shared-generator segmentation of multi-fold paths, astronomy reference
  curves, and a synthetic submarine-cable group crossing without a center
  chord;
- strict aspect-ratio, gap-ratio, enlargement, and geographic-domain
  rejection; and
- raster-name behavior with and without a runtime data prefix.

`tests/test-forward-reverse-projection-api.cc` additionally verifies all eight
carrier cells, all four cap quadrants, the exact cutoff, registered quadrant
seams, component qualification, batch behavior, cap/ordinary page overlap,
and the four-candidate South-Pole policy. Node and headless-Chrome tests repeat
the cap round trip through Embind, the JavaScript wrapper, D3 candidates, and
the module-worker protocol.

The expected 1632-by-2112 anchors were calculated by applying the documented
rigid and centered-scale transforms to the independently Perl-derived 2112-by-1056
Cahill-Keyes fixture. This gives the test a numeric oracle without making a
historical raster the implementation.

The geometry generator additionally asserts one `north-pole-star` path. The
graticule and Natural Earth generators assert that the cap contains `60°S`,
excludes a point just north of it, and reports `-60` at every sampled
longitude. The placement check uses only the projected boundary and verifies
that its bottommost point retains the configured lower clearance. Natural
Earth output requires every ordinary quadrant path to precede the first
Antarctic fragment in each applicable layer. Earth keeps
two top-level groups; water adds a final `polar-mark` group so its black
North-pole star paints above all physical overlay groups.

## Provenance and limitations

The local face projection is derived from Mary Jo Graça and Gene Keyes's
`MegamapMaker-prep9.pl`; its attribution and non-commercial-use terms remain
applicable. The two-group arrangement follows Benjamin De Kosnik's published
Star-X description and historical plate diagram. Full references and source
roles are in the [bibliography](bibliography.md).

This is a forward/reverse spherical projection and provides no ellipsoidal
correction or raster reconstruction. Runtime API 3 structured point calls
automatically select the composed cap at or south of `60°S`; the lower-level
`starxproj` and geometry command-buffer ABI 1 retain the ordinary carrier so
layer-aware renderers can perform topology-safe clipping and topmost paint
order with the supplied helpers, as the Natural Earth and graticule generators
do. The cap preserves distance
from the South Pole, but its longitude-derived bearing normalization is
deliberately not a global rigid transform; that correction joins the bent
Cahill-Keyes quadrant edges without changing radial scale. The fixed `60°S`
cut is an authored presentation boundary, not a projection discontinuity or
a claim that Antarctica ends at that latitude. The 17:22 frame preserves the
historical carrier; the default centered enlargement reduces its former
margins while remaining inside the 34-by-44 page for the tested Star-X
geometry.

---

[Documentation index](../../../../index.md) ·
[Geometric context](context.md) ·
[Bibliography](bibliography.md)
