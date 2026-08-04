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
public default deliberately fixes one depth-5 configuration reconstructed and
registered for the checked-in source raster. Its spanning tree is embedded as
compact generated data. The generation layer can also select five immutable
exploratory trees without making the public projection dependent on runtime
configuration files. Every choice remains deterministic and suitable for a
header-oriented library API.

The work has four parts:

1. **Forward projection:** reproduce the upstream icosahedron face order,
   depth-5 subdivision, fixed land-aware cut tree, planar unfolding, and
   per-face affine transform in C++20.
2. **Perspective exploration:** preserve complete reference metadata and five
   additional cut trees with independently selected planar registrations.
3. **Variable frames and slices:** uniformly normalize a selected net to a
   `16:9` carrier, then derive exact, unscaled terminal-face subsets.
4. **Documentation and tests:** record the geometry, formulas, provenance,
   API contract, limitations, and fixed reference coordinates.

## Code organization

| Component | Responsibility |
| --- | --- |
| [`cart0freak0-myriahedral.h`](../src.projections/cart0freak0-myriahedral.h) | Mesh generation, unfolding, forward transform, frame validation, API adapter, and source-raster preset |
| [`cart0freak0-myriahedral-tree.inc`](../src.projections/cart0freak0-myriahedral-tree.inc) | Compact parent indices for the fixed 5120-face spanning tree |
| [`myriahedral-perspective-generation.h`](../src.generate/myriahedral-perspective-generation.h) | Reference and exploratory configuration metadata, immutable cut trees, and lazy layouts |
| [`perspective-configurations.json`](../assets.static/myriahedral/perspective-configurations.json) | Machine-readable preprocessing, registration, digest, and artifact metadata |
| [`cart0freak0-myriahedral-slicing.h`](../src.projections/cart0freak0-myriahedral-slicing.h) | Exact two-group terminal-face partition, clip geometry, and SVG verification |
| [`generate-myriahedral-slices.cc`](../src.generate/generate-myriahedral-slices.cc) | Ad-hoc water-slice wrapper generator |
| [`a60-carto-projection.h`](../src.projections/a60-carto-projection.h) | Shared `projection_api`, `projection_base`, and `myriahedral` projection mode |
| [`a60-carto-frame.h`](../src.projections/a60-carto-frame.h) | `frame` and `frame.frame_area` geometry |
| [`a60-carto.h`](../src.projections/a60-carto.h) | Umbrella include that exports the projection |
| [`test-myriahedral-projection-api.cc`](../tests/test-myriahedral-projection-api.cc) | Fixed anchors, upstream-layout checks, variable frames, full-degree sweep, domain validation, and API integration |
| [`test-myriahedral-slicing.cc`](../tests/test-myriahedral-slicing.cc) | Hinge membership, complementary face counts, registered bounds, frame offsets, and invalid-carrier rejection |
| [`projection-generation-common.h`](../src.generate/projection-generation-common.h) | Native-cell classification, repeated transition bisection, and seam-safe line generation |
| [`test-projection-generation-common.cc`](../tests/test-projection-generation-common.cc) | Antimeridian and multi-face source-edge regression coverage |
| [`a60-svg-carto-geo.h`](../src.projections/a60-svg-carto-geo.h) | Geographic integration anchors exercised by the projection test |

Most numeric helpers live in `a60::carto::myriahedral_detail`. They are
header-local `inline` functions so the implementation follows the rest of the
cartography library's integration model.

## Reference map configuration

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

## Perspective configuration metadata

A Myriahedral “perspective” is not just a center longitude and a rotation.
Those values do not determine where the mesh is cut. An accurate description
needs enough metadata to reproduce both the topology and its presentation:

| Layer | Required metadata | Why it matters |
| --- | --- | --- |
| Identity | Stable id, schema or algorithm revision, generator argument, output tag | Prevents a changed algorithm from masquerading as the same map |
| Mesh | Icosahedron constants and face order, depth, subdivision order, terminal face count | Every tree index depends on the exact face numbering |
| Land model | Source geometry or exact-fraction digest, smoothing kernel, `sigma`, cutoff, epsilon, and special-country multipliers | Changes the edge costs from which the tree is selected |
| Tree selection | Cost formula, geographic weights and center, root face, spanning-tree algorithm, parent array, and tree digest | Completely determines retained hinges and cuts |
| Flattening | `alpha` and the planar unfolding convention | Distinguishes partial folding from the fully open net used here |
| Registration | Planar rotation, raw bounds, axis direction, and tie-breaking rule | Places the same topology in a recognizable reading orientation |
| Canvas | Normalization formula, aspect ratio, physical carrier, crop or whitespace policy | Determines final output coordinates and apparent scale |
| Verification | Reference-image digest and dimensions, or another fixed set of geographic anchors | Detects a plausible-looking but incorrectly registered result |

The complete machine-readable record is
[`perspective-configurations.json`](../assets.static/myriahedral/perspective-configurations.json).
The corresponding compile-time records and parent arrays are in
[`myriahedral-perspective-generation.h`](../src.generate/myriahedral-perspective-generation.h).
The JSON records full raw bounds and SHA-256 digests; the embedded tree is the
authoritative runtime topology.

### Historical option-name trap

The preserved preprocessing program's option names are transposed relative to
their mathematical use. Reproduction must retain this behavior rather than
silently “correcting” it:

```text
longitude_distance = abs(face_longitude - clat) / 180
latitude_distance  = abs(face_latitude  - clon) / 90

geographic_norm = wlat * longitude_distance^2
                + wlon * latitude_distance^2
```

Thus legacy `wlat` is the **longitude** coefficient, `wlon` is the
**latitude** coefficient, `clat` is the effective center **longitude**, and
`clon` is the effective center **latitude**. Longitude distance is the
historical direct absolute subtraction, not a newly wrapped great-circle
difference. For the reference configuration, the effective center is
therefore `(longitude=-60, latitude=-65)`.

The shared land model uses the exact 5120-face fractions in
[`exact-fractions.txt`](../assets.static/myriahedral/exact-fractions.txt),
Gaussian smoothing with `sigma=0.7` and cutoff `0.001`, and an epsilon of
`0.000001`. Indonesia, Australia, Greenland, Argentina, and Chile receive a
factor of two after smoothing; New Zealand receives a factor of five. The
area-weighted adjacent land value `f` then contributes the edge cost:

```text
edge_weight = exp((1 - f)^2 * geographic_norm)
```

Boost.Graph's Prim implementation starts at face `103`. Its 5119 selected
edges are serialized as one parent per face. Preserving the parent data avoids
depending on library-specific ordering when costs tie.

### Five perspectives worth investigating

All exploratory configurations retain depth `5`, `sigma=0.7`, `alpha=1`,
root face `103`, the same exact land input, and a centered `44 × 24.75`
carrier. The parameters below change the tree before unfolding. The legacy
weights and centers are shown using their original flag spellings; “center”
uses their effective geographic meaning.

| Perspective | Effective center `(lon, lat)` | Legacy `wlat`, `wlon` | Rotation | Investigation |
| --- | ---: | ---: | ---: | --- |
| Reference | `(-60, -65)` | `0.5, 0.1` | `335°` | Compatibility with `black-white-downsampled.png` |
| Americas | `(-100, 25)` | `0.5, 0.1` | `22°` | North–South American continuity and its links to the polar branches |
| Atlantic | `(-25, 15)` | `0.5, 0.1` | `24°` | Relationships among the Americas, Europe, and Africa around the Atlantic |
| Afro Eur Asia | `(35, 20)` | `0.5, 0.1` | `290°` | Africa–Europe–Asia continuity |
| Pacific | `(160, 0)` | `0.5, 0.1` | `326°` | Trans-Pacific and Pacific-rim continuity, including Oceania |
| Antarctic | `(0, -75)` | `0.3, 0.7` | `285°` | Southern Ocean continuity with deliberately stronger latitude weighting |

The reference rotation came from geographic landmark registration against the
source PNG. The exploratory rotations came from a deterministic integer-degree
search: retain local north-up and east-right orientation near `(0°,0°)`, then
maximize occupied scale inside the centered `16:9` carrier. This is a
presentation policy, not part of Prim's tree selection; another publication
may rotate or crop the same topology differently.

The generated full-resolution ocean artifacts are:

| Perspective | Ocean artifacts |
| --- | --- |
| Americas | [PNG](../assets.generated/png/water-myriahedral-americas-44-24.75.png) · [SVG](../assets.generated/svg/water-myriahedral-americas-44-24.75.svg) · [PDF](../assets.generated/pdf/water-myriahedral-americas-44-24.75.pdf) |
| Atlantic | [PNG](../assets.generated/png/water-myriahedral-atlantic-44-24.75.png) · [SVG](../assets.generated/svg/water-myriahedral-atlantic-44-24.75.svg) · [PDF](../assets.generated/pdf/water-myriahedral-atlantic-44-24.75.pdf) |
| Afro Eur Asia | [PNG](../assets.generated/png/water-myriahedral-afro-eur-asia-44-24.75.png) · [SVG](../assets.generated/svg/water-myriahedral-afro-eur-asia-44-24.75.svg) · [PDF](../assets.generated/pdf/water-myriahedral-afro-eur-asia-44-24.75.pdf) |
| Pacific | [PNG](../assets.generated/png/water-myriahedral-pacific-44-24.75.png) · [SVG](../assets.generated/svg/water-myriahedral-pacific-44-24.75.svg) · [PDF](../assets.generated/pdf/water-myriahedral-pacific-44-24.75.pdf) |
| Antarctic | [PNG](../assets.generated/png/water-myriahedral-antarctic-44-24.75.png) · [SVG](../assets.generated/svg/water-myriahedral-antarctic-44-24.75.svg) · [PDF](../assets.generated/pdf/water-myriahedral-antarctic-44-24.75.pdf) |

Generate the five layered SVGs with:

```sh
make generate-water-myriahedral-perspectives
```

`make all` also exports their PDF and 3840-by-2160 PNG derivatives.

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
source asset. The five exploratory layouts deliberately reuse `16:9` as a
comparison carrier; that is a generation policy, not a geometric discovery.

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
  map_frame, "assets.static/myriahedral/black-white-downsampled.png");

const auto [x, y]
  = projection.meridians_to_point_2d(40.7128, -74.0060);
```

The optional filename is returned by `image_filename()` after prefixing the
runtime data-resource path. It does not influence projection mathematics.
`myriahedral_source` is the named `4480 x 2520` preset for the checked-in PNG.

Generation code may pass an explicit immutable `projection_layout` to the
factory overload. The projection retains a pointer to that layout, so its
lifetime must exceed the projection's; rvalue layouts are rejected. The six
configured generation layouts are function-local statics and satisfy that
contract. The ordinary public factory continues to select the reference
layout.

## Initialization and complexity

The reference spherical and planar face arrays are initialized once in a
function-local static object. Each exploratory layout has its own lazy static
and is unfolded only if selected. The one-time work per selected perspective
subdivides and unfolds 5120 triangles. A forward query then uses the
hierarchical face search and a constant-size affine solve. The data footprint
is dominated by each initialized spherical and planar triangle array; every
compressed parent tree is about 20 KiB of hexadecimal text.

Function-local static initialization is thread-safe under C++11 and later.

## Generator boundary handling

The projection API maps individual points. Producing a path also requires a
topological decision: two geographically adjacent points can land on
different planar copies when the unfolded net cuts their shared spherical
edge. The shared generator assigns each input point to a depth-5 face and
bisects a face transition 48 times. Let `p_left` be the last limiting point in
the old face and `p_right` the first in the new face. If

```text
distance(project(p_left), project(p_right)) > max(frame width, frame height) * 1e-5
```

the transition is a cut and begins a new SVG subpath. Otherwise it is a
retained tree hinge and the two limiting points remain connected.

Densification normally leaves one transition in a source edge, but that is
not a safe invariant. An edge passing close to a mesh vertex can cross several
small faces. After each bisection the generator therefore advances to the
first point in the new face and searches again until it reaches the endpoint
face. A 64-transition guard detects non-progress or unexpectedly unsuitable
input instead of silently emitting a distant chord.

Exact longitude `+180` is canonicalized to `-180` by `geographic_vector()`.
This makes native-face classification use the same representative as the
forward point transform. Before the shared rule, an exact antimeridian
endpoint could be classified on the east copy but projected on the west copy.

These two cases were visible in the water artifact because coastlines and
rivers are open line paths. The Earth base is composed from filled areas,
which already use exact face-local triangle clipping and therefore did not
emit the same false chords.

## Myriahedral slicing

Cahill-Keyes has four repeated columns and eight named octants, so quarto and
octo slicing follow large construction faces. A Myriahedral net has no
equivalent canonical four- or eight-page partition: its useful topology is the
retained hinge tree over 5120 terminal faces. Four slicing families merit
further use:

1. **Hinge-component slices.** Cut one or a few retained hinges and publish
   the resulting connected tree components. These have the cleanest
   topological interpretation and preserve every uncut face relationship.
2. **Semantic terminal-face groups.** Seed faces from named regions, optimize
   a small set of hinge cuts, and serialize the resulting unions of exact
   triangles. This is the method implemented below.
3. **Base-icosahedron families.** Group terminal faces by their 20 original
   icosahedron ancestors, then combine those ancestors into polar, five-part,
   ten-part, or publication-specific sets. These are repeatable, though they
   need not follow the unfolded tree's visually obvious branches.
4. **Geographic masks or carrier viewports.** Select faces by hemisphere,
   pole, ocean basin, centroid region, or simply crop rectangular strips.
   These are useful presentation views, but a rectangle is not a pure
   topological slice and may include pieces from unrelated branches.

### Implemented two-group partition

The requested ad-hoc partition is:

- **Group 1:** North America, South America, Antarctica, Greenland, and
  Iceland.
- **Group 2:** every remaining land and ocean face.

The exploration seeded a terminal face only when its exact land fraction was
at least `0.05`. Group 1 seeds were selected by an Americas longitude/latitude
window, an Antarctica latitude threshold, the exact Greenland country bit,
and an Iceland centroid window. All other seeded land faces requested group
2. A two-state dynamic program on the reference tree minimized the number of
changed branches while penalizing cuts through land:

```text
hinge_cut_cost(a,b) = 1 + 1000 * max(raw_land_fraction[a],
                                     raw_land_fraction[b])
```

That search found five retained hinges. Four have zero land fraction on both
sides; the high-Arctic `51--273` separator is the one unavoidable
land-adjacent transition for this exact semantic grouping:

```text
51--273
3929--3924
2026--2025
3601--3602
264--259
```

The production implementation no longer repeats the exploratory geographic
heuristics. It stores those five exact edges in
[`cart0freak0-myriahedral-slicing.h`](../src.projections/cart0freak0-myriahedral-slicing.h).
Traversal starts at root face `103` in group 2 and toggles the current label
whenever it crosses one of the five edges. Every face is consequently assigned
once, with no overlap and no omitted carrier face:

| Group | Terminal faces | Raw rotated bounds `(min x, min y) ... (max x, max y)` |
| --- | ---: | --- |
| 1 | 2722 | `(-3.794926045716, -2.925593176288) ... (0.333633177675, 1.609508207795)` |
| 2 | 2398 | `(-3.145317798691, -2.245606055383) ... (2.570969787434, 0.706070797167)` |

### Carrier-preserving output

Both slices reuse
[`water-myriahedral-44-24.75.svg`](../assets.generated/svg/water-myriahedral-44-24.75.svg)
on its canonical `44 × 24.75` carrier. Each terminal face is normalized once
with the reference layout, and its three exact planar vertices become one SVG
clip-path subpath. The wrapper takes the tight rectangular bounds of that face
union. It applies no `scale()` transform and does not call the geographic
projection again.

This is the direct Myriahedral analogue of the face-clipped Cahill-Keyes
octants: projection belongs to the complete carrier; slicing belongs to the
resulting planar geometry. The lightweight SVG wrappers use an external
`<use>` reference and must remain beside the master SVG. Their PDF and PNG
exports are self-contained.

| Group | Carrier `viewBox` | Raster size | Ocean artifacts |
| --- | --- | ---: | --- |
| 1 | `4.62928339117 0 22.5313244677 24.75` | `3496 × 3840` | [PNG](../assets.generated/png/water-myriahedral-adhoc-slice-1.png) · [SVG](../assets.generated/svg/water-myriahedral-adhoc-slice-1.svg) · [PDF](../assets.generated/pdf/water-myriahedral-adhoc-slice-1.pdf) |
| 2 | `8.17447516357 4.93044675727 31.1962414453 16.1085708816` | `3840 × 1983` | [PNG](../assets.generated/png/water-myriahedral-adhoc-slice-2.png) · [SVG](../assets.generated/svg/water-myriahedral-adhoc-slice-2.svg) · [PDF](../assets.generated/pdf/water-myriahedral-adhoc-slice-2.pdf) |

Generate both slice SVGs with:

```sh
make generate-myriahedral-slices
```

They are also members of `make all`, which exports both PDF and PNG forms.
The mask follows depth-5 mesh faces rather than legal or political borders;
small coastal and high-Arctic differences are therefore a deliberate
resolution property, not a claim about exact regional boundaries.

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

`tests/test-projection-generation-common.cc` adds path-level regressions for:

- an exact `+180` endpoint, including agreement between point projection and
  native-face classification; and
- a short Natural Earth river edge that crosses faces `377 -> 369 -> 355`,
  verifying that the retained hinge and following cut become two local
  subpaths instead of one page-spanning chord; and
- all five exploratory metadata records, selected immutable layouts, frame
  bounds, and distinct registered coordinates.

`tests/test-myriahedral-slicing.cc` verifies:

- all five configured cut pairs are real retained hinges;
- the groups contain exactly 2722 and 2398 faces and together cover all 5120;
- the two tight viewports and inverse output-frame offsets;
- every clip triangle lies inside its declared viewport; and
- rejection of a non-`16:9` complete carrier.

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
- The public default remains one fixed raster-compatible configuration. The
  generation layer adds five compile-time exploratory layouts; accepting an
  arbitrary untrusted run-time tree would still require a separate validated
  serialization interface.

## Provenance

The mesh ordering, subdivision scheme, land-aware spanning-tree method,
flattening approach, configuration search space, and source raster derive from
[`temporaer/myriaworld`](https://github.com/temporaer/myriaworld). The method
originates in Jarke J. van Wijk's 2008 paper, *Unfolding the Earth:
Myriahedral Projections*. Natural Earth supplied the historical country
geometry used while reconstructing the fixed tree.

The local raster
[`black-white-downsampled.png`](../assets.static/myriahedral/black-white-downsampled.png)
is byte-for-byte identical to the upstream sample at the time of
implementation. Its SHA-256 is:

```text
1228cae3fdcbdcb867952135e9eeaec7d894c092eb8dae828d0dd61ad8658fd7
```

See the [bibliography](myriahedral-bibliography.md) for stable primary links,
the configuration evidence, data sources, and licensing notes.
The exact reconstruction inputs, generators, selected tree, planar baseline,
and scoring output are preserved in the
[`assets.static/myriahedral`](../assets.static/myriahedral/README.md) artifact
manifest.
