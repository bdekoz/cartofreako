# Dymaxion C++20 implementation notes

[Documentation index](../index.md) ·
[Geometric context](dymaxion-context.md) ·
[Bibliography](dymaxion-bibliography.md)

## Scope and result

`a60::carto::dymaxionproj` is a native C++20 forward implementation of the
icosahedral Fuller projection commonly called the Dymaxion or Airocean map.
It accepts `(latitude, longitude)` through the shared
`a60::carto::projection_api` and returns upper-left-origin coordinates in a
variable-size `a60::carto::frame`.
The projection-neutral runtime adds the matching exact face-qualified reverse.

The implementation combines two independently documented parts:

- Robert W. Gray's exact Fuller face transform, which preserves uniform scale
  along every icosahedron edge; and
- the Fuller-oriented interrupted net used by PROJ's Airocean projection,
  including separate Australia and Japan subfaces that keep land interruption
  low.

This is not a gnomonic approximation. The geographic face orientation and net
are also not sufficient by themselves to define the projection: the exact
edge-distance equations are the third essential part. “Exact” describes the
analytic sphere-to-face equations, not a claim that the map is conformal,
equal-area, or free of distortion.

The work is integrated in four stages:

1. **Projection:** select an oriented icosahedron face, evaluate Gray's exact
   equations, place the result in Fuller's interrupted net, and expose the
   common cartographic API.
2. **Variable frame:** normalize the net once and scale both coordinates from
   `frame.frame_area`, accepting any finite, positive frame with the required
   aspect ratio.
3. **Generation and documentation:** add geometry, graticule, Earth, and water
   targets; clip filled data per native face; record formulas, context,
   provenance, tests, and limitations.
4. **Reverse projection:** invert Gray's canonical edge-distance equations for
   all registered faces/subfaces and forward-check every candidate.

## Code and artifact organization

| Component | Responsibility |
| --- | --- |
| [`a60-carto-projection-dymaxion.h`](../src.projections/a60-carto-projection-dymaxion.h) | Icosahedron and net tables, exact face transform, frame validation, API adapter, factory, and native-size preset |
| [`cart0freak0-projection-runtime.h`](../src.projections/cart0freak0-projection-runtime.h) | API 3 exact Gray reverse, face/subface candidates, and residual checks |
| [`a60-carto-projection.h`](../src.projections/a60-carto-projection.h) | Shared `projection_api`, `projection_base`, and `dymaxion` mode |
| [`a60-carto-frame.h`](../src.projections/a60-carto-frame.h) | `frame` and its `frame.frame_area` dimensions |
| [`a60-carto.h`](../src.projections/a60-carto.h) | Umbrella include exporting the Dymaxion header |
| [`projection-generation-common.h`](../src.generate/projection-generation-common.h) | `dymaxion` command argument, exact 44-inch frame, variant dispatch, face classification, and seam bisection |
| [`projection-area-generation.h`](../src.generate/projection-area-generation.h) | Face-local transform and exact planar-triangle clipping for filled paths |
| [`test-dymaxion-projection-api.cc`](../tests/test-dymaxion-projection-api.cc) | Exact reference coordinates, edge scale, topology, variable frames, domain sweep, validation, and API checks |

The production previews are:

| Geometry | Graticules | Earth | Water |
| --- | --- | --- | --- |
| [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/dymaxion/png/geometry-dymaxion-44-20.78461.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/dymaxion/png/graticules-dymaxion-44-20.78461.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/dymaxion/png/earth-dymaxion-44-20.78461.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/dymaxion/png/water-dymaxion-44-20.78461.png) |

Each also has a layered SVG under `assets.generated/dymaxion/svg/` and a
print-size PDF under `assets.generated/dymaxion/pdf/` with the same basename.

## Coordinate conventions

| Layer | Units and axes |
| --- | --- |
| Public input | `(latitude, longitude)` in degrees |
| Geographic vector | Unit sphere, right-handed Cartesian coordinates |
| Canonical Fuller triangle | Unit-edge equilateral triangle centered at its origin, `y` upward |
| Native horizontal net | `5.78304223331047 × 2.7317789919300877`, `y` upward |
| Normalized map | Unit rectangle, `y` downward |
| Public output | `frame.frame_area` coordinates, origin at upper left |

The public domain is finite latitude `[-90, 90]` and longitude
`[-180, 180]`. Exact `+180` is canonicalized to `-180` before trigonometry so
both names for the antimeridian have identical face ties and output bits.
Out-of-domain or non-finite input throws `std::invalid_argument`.

## Icosahedron and drawable faces

### Fuller orientation

The twelve unit vertices are the Fuller orientation published by Gray. Six
are listed explicitly and the remaining six are their antipodes. For example,
the first three are:

```text
v1 = (0.420152426708710,  0.078145249402783,  0.904082550615019)
v2 = (0.995009439436242, -0.091347795276428,  0.040147175877167)
v3 = (0.518836730327364,  0.835420380378236,  0.181331837557262)
```

Twenty regular spherical triangles cover the globe. The planar presentation
uses 23 drawable triangles because two parent faces are subdivided:

```text
18 unchanged complete faces
 2 pieces replacing the Australia parent face
 3 pieces replacing the Japan parent face
-----------------------------------------------
23 drawable faces or subfaces
```

Subdivision changes only the cut and placement. Each piece retains the local
basis and exact transform of its complete parent icosahedron face.

### Deterministic face selection

For an oriented spherical triangle `(p1,p2,p3)` and geographic direction `p`,
the point is inside when these scalar triple products are non-positive within
roundoff:

```text
det(p,  p2, p3) <= 0
det(p1, p,  p3) <= 0
det(p1, p2, p ) <= 0

det(a,b,c) = a dot (b cross c)
```

Faces are examined in table order. A location exactly on an edge or vertex
therefore uses the lowest matching face index. The same classifier is used by
the point API, graticule/path splitting, and face-local polygon clipping.

## Exact Fuller face transform

### 1. Geographic direction

For latitude `phi` and longitude `lambda` in radians:

```text
p = (cos(phi) cos(lambda),
     cos(phi) sin(lambda),
     sin(phi))
```

Both poles are constructed as exact `(0,0,+/-1)` vectors so an irrelevant
longitude residual cannot change a face tie.

### 2. Face-local basis

For complete parent vertices `(q0,q1,q2)`, define:

```text
z = normalize(q0 + q1 + q2)
y = normalize(q0 - z (q0 dot z))
x = y cross z

u = p dot x
v = p dot y
w = p dot z
```

`z` passes through the spherical face center, `y` points toward the first
vertex, and `x` completes a right-handed basis. Every selected point has
`w > 0`.

### 3. Icosahedron constants

Let:

```text
r5 = sqrt(5)
A  = 2 asin(sqrt(5-r5) / sqrt(10))
   = 1.1071487177940904 rad
   = 63.43494882292201 degrees

t  = A / 2
e  = sqrt(8) / sqrt(5+r5)       = 1.0514622242382672
d  = sqrt(3+r5) / sqrt(5+r5)    = 0.8506508083520398
```

`A` is the spherical arc of an icosahedron edge, `e` is its unit-sphere chord
length, and `d` is Gray's vertex-to-edge-plane constant.

### 4. Edge-distance coordinates

First scale the local tangent components by the selected face depth:

```text
s  = sqrt(5 + 2sqrt(5)) / (w sqrt(15))
u' = u s
v' = v s
```

Then form three symmetric intermediate distances:

```text
b1 =  2v'/sqrt(3)             + e/3
b2 =   u' - v'/sqrt(3)        + e/3
b3 = - u' - v'/sqrt(3)        + e/3

a_i = t + atan((b_i - e/2) / d),  i in {1,2,3}
```

The `a_i` values are spherical arc distances associated with the three face
edges. Their symmetric planar combination is:

```text
X = (a2 - a3) / (2A)
Y = (2a1 - a2 - a3) / (2sqrt(3)A)
```

This produces the centered, unit-edge canonical equilateral triangle. In
particular, a point one quarter of the way along a spherical icosahedron edge
maps one quarter of the way along its planar edge. The API test checks the
quarter, midpoint, and three-quarter positions; this property distinguishes
the Fuller transform from a central gnomonic projection.

### 5. Register a face or subface in the net

The exact canonical coordinates of a drawable triangle's three spherical
vertices are cached once. For canonical point `r`, solve:

```text
r = c0 + alpha(c1-c0) + beta(c2-c0)
```

and transfer the same two affine coordinates to its three stored net
vertices `(n0,n1,n2)`:

```text
n = n0 + alpha(n1-n0) + beta(n2-n0)
```

For a complete face this is a rotation, translation, and common scale. For a
split face it also registers the exact parent-face result in the selected
piece of the interrupted map.

## Net dimensions and screen normalization

The horizontal net spans five and one-half triangle edges horizontally and
three equilateral altitudes vertically:

```text
W0 = (11/2)e          = 5.78304223331047
H0 = (3sqrt(3)/2)e    = 2.7317789919300877

W0/H0 = 11/(3sqrt(3))
      = 2.116950987028628...
```

The native net uses a lower-left origin. Public screen coordinates use:

```text
nx = clamp(net_x / W0, 0, 1)
ny = clamp(1 - net_y / H0, 0, 1)

x = nx * frame.width()
y = ny * frame.height()
```

Clamping contains only boundary roundoff. Face selection and transform tests
ensure ordinary locations already lie in the native bounds.

## Exact face-qualified reverse

Runtime API 3 reverses the same Gray transform rather than approximating it
with a planar triangle. It first undoes frame normalization and enumerates the
registered planar triangles containing the point. Planar barycentric weights
transfer the point through the affine net registration to the cached canonical
Fuller triangle, including the Australia and Japan subfaces.

The canonical coordinates determine three offsets from the otherwise unknown
mean of Gray's spherical edge distances:

```text
vertical   = sqrt(3) E y
horizontal = E x

offsets = (2 vertical / 3,
           -vertical / 3 + horizontal,
           -vertical / 3 - horizontal)
```

Here `E` is the spherical icosahedron edge arc. For `ai = mean + offset_i`,
the inverse of Gray's arctangent relation yields the three gnomonic edge
coordinates. Their required sum is the chord length, giving one monotone
bounded scalar equation for `mean`. The solved coordinates reconstruct the
face-local gnomonic direction; normalizing it and applying the stored
orthonormal basis returns the global unit vector.

The runtime retains the candidate only when the selected face/subface's exact
forward transform returns to the requested screen coordinate within the pixel
tolerance. Edges and split boundaries remain multiple/cut candidates, and an
optional `nativeCell` avoids enumerating faces when the caller already knows
the topology.

## Variable-size frame contract

`is_dymaxion_frame()` accepts a frame only when:

```text
width and height are finite
width > 0 and height > 0
width = dymaxion_width_to_height_ratio * height
```

The comparison tolerance is:

```text
16 * epsilon(double) * max(width, expected_width)
```

This allows floating-point evaluation of the exact ratio but rejects an
approximately similar carrier such as `2:1`. Frame placement offsets are
discarded by the projection factory: only `map_frame.frame_area` is retained.
Positioning inside a larger page remains the surrounding `cartography`
object's job.

The standard generated frame fixes the long dimension at 44 inches:

```text
width  = 44
height = 44 / dymaxion_width_to_height_ratio
       = 20.7846096908265...
```

Serialized filenames use `44-20.78461`; in-memory calculations retain the
full double expression.

## Public API and use

Include the frame, shared projection state, and requested header:

```c++
#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "a60-carto-projection-dymaxion.h"

const double width = 1920;
const a60::carto::frame map_frame {
  width,
  width / a60::carto::dymaxion_width_to_height_ratio
};

const auto projection
  = a60::carto::make_dymaxion_projection(map_frame);
const auto [x, y]
  = projection.meridians_to_point_2d(40.7128, -74.0060);
```

An optional raster name uses the same runtime-resource resolution as the
other projection classes:

```c++
const auto projection = a60::carto::make_dymaxion_projection(
  map_frame, "dymaxion-background.png");
const std::string path
  = projection.image_filename(a60::carto::projection_base::filled);
```

`pdymaxion_source` and `dymaxion_source` expose the unscaled native net
dimensions. They have no prescribed backing raster.

## Generation and seam-safe filled geometry

Run all four Dymaxion artifact families with:

```sh
make generate-dymaxion
```

Or generate one SVG family:

```sh
make generate-geometry-dymaxion
make generate-graticules-dymaxion
make generate-earth-dymaxion
make generate-water-dymaxion
```

Open lines are densified geographically. Whenever neighboring samples select
different native faces, the generator bisects the transition for 48
iterations. Coincident planar limits stay joined at a retained hinge; distant
limits start separate SVG subpaths at a cut.

Filled polygons cannot rely on SVG closure across an interrupted net. Natural
Earth areas are therefore gridded, transformed separately in each candidate
Dymaxion face, and intersected with that face's exact planar triangle before
normalization. This prevents false ocean or land chords between unrelated net
edges. The method is shared with Myriahedral and Voronoi, but uses the exact
Fuller face transform rather than either projection's face formula.

## Verification

`make check` covers:

- the `projection_api` base relationship and `dymaxion` mode;
- all 23 face/subface centroids and planar bounds;
- uniform quarter-arc scale along an icosahedron edge;
- 17 city, pole, and seam coordinates independently evaluated by Gray's
  exact reference implementation, converted only for units and screen axes;
- multiple `frame.frame_area` sizes from unit height to 4,000 units;
- discarded placement offsets and runtime raster path resolution;
- rejection of wrong ratios, zero, negative, NaN, infinity, and overflow;
- every integer latitude/longitude pair over the complete public domain; and
- exact equality of the `-180` and `+180` antimeridian forms.

`tests/test-forward-reverse-projection-api.cc` additionally checks an interior
point in every one of the 23 faces/subfaces, a global coordinate lattice,
native-cell qualification, batches, boundary status, exact forward residuals,
and invalid options. Node and browser tests repeat the advertised reverse
through WebAssembly and workers.

Each generator also reopens its SVG and checks the exact view box, layer and
face counts, path presence, and absence of non-finite coordinates. The checked
in PNGs provide the complementary visual regression surface.

## Provenance and licensing

The projection and its terminology originate with R. Buckminster Fuller. The
exact face equations are independently expressed from Robert W. Gray's
published mathematical work. Gray's separately distributed C reference
program has additional non-commercial conditions; no source from that program
is incorporated here, and its output is used only as numeric test data.

The 23 spherical subface definitions and horizontal net placements derive
from PROJ 9.6.2's `airocean.cpp`. Those tables are permissively licensed, and
the required MIT-style permission and warranty notice is retained at the top
of `a60-carto-projection-dymaxion.h`. New cartofreako source remains under the
repository's GPLv3-or-later terms. The
[bibliography](dymaxion-bibliography.md) identifies the formula, history,
source revisions, license, and BFI trademark statement precisely.

## Limitations and claim boundary

- The transform models a sphere. It does not apply ellipsoidal latitude or
  datum corrections.
- It is neither conformal nor equal-area. Shape, area, direction, angle, and
  distance are generally distorted, although the 20 small facets keep global
  distortion comparatively low.
- Scale is exact along facet edges, not everywhere inside a facet.
- The output is intentionally interrupted. It is suited to a complete world
  view, not a seamless local navigation map.
- The flat aspect is one specific Fuller/Airocean unfolding. Other valid
  arrangements of the same icosahedron are possible.
- `Dymaxion`, `Spaceship Earth`, and `Fuller Projection Map` are identified by
  the Buckminster Fuller Institute as BFI trademarks. This implementation is
  technical interoperability work and does not imply BFI endorsement.

See the [bibliography](dymaxion-bibliography.md) for the formula, historical,
net-layout, API-reference, licensing, and trademark sources.

---

[Documentation index](../index.md) ·
[Geometric context](dymaxion-context.md) ·
[Bibliography](dymaxion-bibliography.md)
