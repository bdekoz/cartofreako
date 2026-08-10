# Cahill-Keyes C++20 implementation notes

[Documentation index](../index.md) ·
[Geometric context](cahill-keyes-context.md) ·
[Forward/reverse API](forward-reverse-projection-api.md) ·
[Bibliography](cahill-keyes-bibliography.md)

## Scope and result

The implementation replaces the former per-point Node.js subprocess, shared
temporary file, and fixed-height caches with an in-process C++20 forward
projection and an octant-qualified reverse solver. Its geometric construction
is derived from the
coordinate-conversion core of Mary Jo Graça and Gene Keyes's
`MegamapMaker-prep9.pl`, including:

- longitude/latitude normalization into eight octants and sixteen mirrored
  half-octants;
- the complete A–L piecewise graticule construction;
- the supple-zone line/circle intersection;
- all eight rotations and reflections in the standard M-layout; and
- dimensionless construction followed by uniform scaling to an arbitrary
  positive, finite 2:1 map frame.

The C++ implementation is not required to reproduce the Perl program's
floating-point behavior. In particular, its line and circle intersections,
intermediate precision, scale handling, and segment traversal intentionally
diverge where the older techniques are ill-conditioned. The Perl output is a
useful provenance and coarse-compatibility corpus, not a correctness oracle.

The public class remains `a60::carto::ckproj` and continues to implement
`a60::carto::projection_api`. Its existing `projection_base` constructor and
named presets remain available. New code can construct it directly from an
`a60::carto::frame`.

The work was delivered in five stages:

1. **Native projection:** translate the forward construction to C++20 and
   verify it against the Perl results and `augment_carto_geo_specific` anchors.
2. **Variable frames:** derive every length and origin from
   `frame.frame_area`, enforce the projection's 2:1 aspect ratio, and retain
   the named compatibility presets.
3. **Numerical hardening:** normalize the internal scaffold, replace the
   unstable intersection formulae, test representable boundary neighborhoods,
   and remove generator coordinate perturbations.
4. **Documentation:** record the geometry, formulas, implementation choices,
   usage, verification method, provenance, and bibliography in this
   documentation set.
5. **Reverse projection:** undo the selected M-layout octant, solve the
   canonical piecewise construction with a bounded forward-residual search,
   and expose candidates through runtime API 2.

## Code organization

| Component | Responsibility |
| --- | --- |
| [`cart0freak0-cahill-keyes.h`](../src.projections/cart0freak0-cahill-keyes.h) | Numeric forward projection, octant-qualified reverse solver, frame validation, `projection_api` adapter, screen-coordinate conversion, raster naming, and compatibility presets |
| [`cart0freak0-cahill-keyes-functions.h`](../src.projections/cart0freak0-cahill-keyes-functions.h) | Scale- and offset-aware splitting of projected paths at wrapped frame edges |
| [`cart0freak0-cahill-keyes-slicing.h`](../src.projections/cart0freak0-cahill-keyes-slicing.h) | Carrier-frame viewport descriptors, exact-octant clipping, SVG slice wrappers, and verification |
| [`test-cahill-keyes-projection.cc`](../tests/test-cahill-keyes-projection.cc) | Compatibility points, representable boundary neighborhoods, scale invariance, continuity, domain sweep, and invalid input |
| [`test-cahill-keyes-projection-api.cc`](../tests/test-cahill-keyes-projection-api.cc) | Public API anchors, variable frames, invalid frames, raster paths, and compatibility construction |
| [`test-cahill-keyes-path-functions.cc`](../tests/test-cahill-keyes-path-functions.cc) | Horizontal, vertical, corner, two-edge, variable-frame, stateful, and invalid path cases |
| [`test-cahill-keyes-slicing.cc`](../tests/test-cahill-keyes-slicing.cc) | Four-strip and exact-octant geometry, metadata, source references, physical units, and invalid carriers |
| [`test-forward-reverse-projection-api.cc`](../tests/test-forward-reverse-projection-api.cc) | Runtime round trips, 1,560 zone samples, registered seams, qualified poles, batches, outside points, and capability status |

`ck_native::forward_projection` builds a dimensionless, `long double`
scaffold with `MG = 1` and stores the requested output altitude separately.
Calls to `operator()` are stateless: they evaluate the canonical construction,
assemble the octant, and apply the output scale only once at the end. Reverse
calls are also stateless and evaluate the same forward construction during
their residual search. No cache or external process is required.

## Coordinate conventions

The two public layers deliberately use different argument and coordinate
conventions:

| Layer | Call | Axes |
| --- | --- | --- |
| `ck_native::forward_projection` | `(longitude, latitude)` | centered Cartesian; `x` right, `y` up |
| `projection_api::meridians_to_point_2d` | `(latitude, longitude)` | map frame; `x` right, `y` down |

Both geographic arguments are degrees. The native class accepts finite
latitudes in `[-90, 90]` and finite longitudes in `[-180, 180]`; values outside
those closed intervals throw `std::invalid_argument`.

## Frame-derived scale

Let a requested frame have width `W` and height `H`. A valid Cahill-Keyes frame
must satisfy:

```text
W > 0
H > 0
W = 2H
W and H are finite
```

`is_cahill_keyes_frame()` compares `W` with `2H` using only a roundoff-sized
tolerance:

```text
tolerance = 16 * epsilon(double) * max(W, 2H)
valid = abs(W - 2H) <= tolerance
```

This admits arithmetic noise, not approximate 2:1 aspect ratios. For example,
`2000.001 × 1000` is rejected.

The geometric scale represented by a requested frame is:

```text
MGout = H / 2 = W / 4
qout  = MGout / 10000 = H / 20000 = W / 40000
```

The original M-layout spans 40,000 units when `MG = 10,000`, so these formulas
fit it exactly to the frame width. The implementation does not repeatedly
multiply each construction value by `qout`. It instead evaluates an equivalent
canonical scaffold with `MG = 1` and these dimensionless constants:

| Quantity | Value |
| --- | ---: |
| `MA` | `0.094` |
| ordinary latitude spacing | `0.01` per degree |
| polar latitude spacing | `0.0104` per degree |
| `AP75` | `0.156` |
| `AP73` | `0.176` |

After octant assembly, the canonical coordinate is multiplied by `MGout`.
This makes the geometric decisions independent of page or raster size and
eliminates the former scale-dependent intersection classification.

The standard frame constructor centers the map at `(W/2, H/2)`. After native
projection returns `(x, y)`, the API result is:

```text
X = W / 2 + x
Y = H / 2 - y
```

The legacy `projection_base` constructor preserves explicitly supplied origins,
so its general form is `X = longitude_zero_x + x` and
`Y = latitude_zero_y - y`.

## Geographic normalization

### Raster registration adjustment

`ckproj` first adds one degree to longitude and wraps values greater than
180°:

```text
λ' = λ + 1°
if λ' > 180°, λ' = λ' - 360°
```

This is a **cartofreako/Visionscarto raster registration adjustment**, not part
of the Cahill-Keyes construction. It preserves the behavior of the raster
assets and the geographic anchors already used by the project. The native
class itself implements the canonical longitude boundaries without this
offset.

### Octant and half-octant coordinates

For native longitude `λ'` and latitude `φ`, `LLtoMP` from the Perl source is
represented by:

```text
o0 = floor((λ' + 200) / 90) + 1
u  = λ' + 200 - 90(o0 - 1) - 45
s  = -1 when u < 0, otherwise +1
m  = abs(u)
p  = abs(φ)
```

The quotient is non-negative over the validated longitude domain, so the C++
integer conversion has the same result as `floor`. If `o0` is 5 it wraps to
octant 1. Southern latitudes remap the four northern sectors as follows:

```text
1 -> 6
2 -> 7
3 -> 8
4 -> 5
```

The result has `0 ≤ m ≤ 45`, `0 ≤ p ≤ 90`, a side sign `s`, and an
octant number 1–8. In the native formula, the longitude sectors are:

| Octant sector | Half-open native longitude interval |
| --- | --- |
| 1 / 6 | `[-180, -110)` and `[160, 180]` |
| 2 / 7 | `[-110, -20)` |
| 3 / 8 | `[-20, 70)` |
| 4 / 5 | `[70, 160)` |

Because the public API applies the one-degree registration adjustment, its
visible seam longitudes are -111°, -21°, 69°, and 159°.

## Numeric geometry primitives

Geographic inputs and public outputs remain `double`, but the complete
dimensionless construction uses `long double`,
`std::numbers::pi_v<long double>`, the `long double` trigonometric overloads,
and `std::fma` where it reduces cancellation. Only the final assembled
coordinate is scaled and rounded to `double`.

`long double` supplies the widest standard floating-point type available on
the target; the algorithm does not rely on extra precision alone. Canonical
scaling and the stable geometric formulations are required even on targets
where `long double` and `double` have the same representation.

For points `P=(Px,Py)` and `Q=(Qx,Qy)`, distance is:

```text
d(P,Q) = hypot(Px - Qx, Py - Qy)
```

Interpolation a distance `l` along a segment of total construction length `L`
is:

```text
interpolate(l, L, P, Q) = P + (Q - P) * l/L
```

Some calls intentionally use a signed `L`; this preserves the source
construction's direction near the 73° transition at the outer edge. A zero
total length is rejected with `std::domain_error`.

For two lines through `P1`, `P2` at angles `θ1`, `θ2`, use unit direction
vectors `r = (cos θ1, sin θ1)` and `s = (cos θ2, sin θ2)`. With the
two-dimensional scalar cross product `×`, their intersection is:

```text
t = (P2 - P1) × s / (r × s)
intersection = P1 + tr
```

This avoids tangent slopes, their vertical-line singularity, and division by a
difference of two rounded tangents. The construction rejects only exactly
parallel direction vectors; the `m = 0` meridian has its explicit analytic
limit.

For a circle with center `C`, radius `r`, and a segment from `P0` to `P1`, set
`d = P1 - P0` and project the center onto the segment's supporting line:

```text
a  = d·d
t0 = (C - P0)·d / a
e  = P0 + t0*d - C
h² = r² - e·e
dt = sqrt(h² / a)
t  = t0 ± dt
```

Only factors in `[0,1]` are segment intersections. Roundoff tolerances are
derived from `long double` epsilon and the magnitudes of the radial terms and
segment factors. A negative `h²` or an endpoint factor is clamped only when it
falls inside that error bound. Accepted roots are ordered along the segment.

This deliberately replaces the Perl routine's expanded quadratic coefficient,
naïve quadratic roots, exact discriminant sign test, and exact endpoint tests.
Those choices were responsible for reachable false “no intersection” results
near the 45° half-octant boundary.

## Reference half-octant construction

### Preliminary scaffold

Let the canonical scaffold use `S = MG = 1` and `q = 1/10000`. The primary
points are:

```text
M = (0, 0)
G = (S, 0)
A = (940q, 0)
N = (S, S tan 30°)
```

The remaining fixed points follow from intersections and scaled distances:

```text
B = line(M, 30°) ∩ line(A, 45°)
D = N + (M - N) * MB/MN
F = (S, Ny - MB)
E = (Nx - MA sin 30°, Ny - MA cos 30°)
Δm = (GF + AB) / 45

U = A + AP73 * (cos 30°, sin 30°)
T = line(U, -60°) ∩ line(B, 30°)
```

`Δm` is the distance advanced along the piecewise equator for each degree of
half-octant meridian.

The supple-zone circle is constrained to have center
`C = (√3 Cy, Cy)` and to pass through `D` and a constructed point `V` at
`m = 29°, p = 15°`. Equating the two squared radii gives:

```text
Cy = ((V - D)·(V + D))
     / (2 * (√3(Vx - Dx) + (Vy - Dy)))
Cx = √3 Cy
R  = distance(C, D)
```

The dot-product difference-of-squares form avoids subtracting two independently
rounded squared norms. All these values are computed once in the native
projection constructor.

### Meridian framework

For half-meridian `m`, the equatorial point `Q(m)` advances by
`l = Δm * m` along `G→F→E`: first vertically from `G` to `F`, then by
interpolation from `F` to `E`.

Two joints divide the constructed meridian into torrid, middle, and frigid
portions:

```text
Jt(m) = line(M, 2m/3) ∩ line(Q(m), m/3)
Jf(m) = line(A, m) ∩ line(M, 2m/3)
```

At `m = 0`, `Jf` uses the limiting center-line point `(Ax + AB, 0)`. The
segment lengths used for latitude equisection are:

```text
Lt = distance(Q, Jt)
Lm = distance(Jt, Jf)
Lf = signed distance(Jf, P73)
```

For `m ≤ 30°`, `P73` lies on the circle centered at `A` with radius
`1760q`. For `m > 30°`, it is the intersection of the -60° line through `T`
and the `m`-degree line through `Jf`. Near 45° the source construction can put
the transition in the middle segment; the implementation preserves that case
with a negative `Lf`. `P75` lies on the circle centered at `A` with radius
`1560q`.

### A–L zone dispatch

The conditions are evaluated in the following order. This defines which
geometric formula owns an exact boundary; it is not a promise to reproduce the
source program's floating-point branch classification:

| Zone | Ordered condition | Construction |
| --- | --- | --- |
| A | `m = 0`, `p ≥ 75` | Center line, `104q` units per degree from the pole |
| B | `m = 0`, `p < 75` | Center line, `100q` units per degree from `G` |
| C | `m != 0`, `p ≥ 75` | Polar circle centered at `A`, radius `104q(90-p)` |
| D | `p = 0` | Equatorial point `Q(m)` |
| E | `p ≥ 73`, `m ≤ 30` | Circle centered at `A`, radius `AP75 + 100q(75-p)` |
| F | `m = 45`, `p ≤ 15` | Linear interpolation `E→D` |
| G | `m = 45`, `15 < p ≤ 73` | Linear interpolation `D→T` |
| H | `m = 45`, `73 < p < 75` | Equisection through `P75→B→P73` |
| I | `m ≤ 29` | Equisection over `Q→Jt→Jf→P73` |
| J | `m > 29`, `p ≥ 73` | Frigid supple interpolation through `P75`, `Jf`, and `P73` |
| K | `m > 29`, `p ≤ 15` | Torrid supple interpolation to the computed 15° path length |
| L | `m > 29`, `15 < p < 73` | Middle supple interpolation from the 15° path length to `P73` |

Zones I, K, and L walk a cumulative length across the constructed segments,
then interpolate within whichever segment contains that length. Zone I, for
example, uses:

```text
l = p * (Lt + Lm + Lf) / 73
```

For `m > 29°`, the 15° path length is found by traversing the meridian in
geographic order, `Q→Jt→Jf`. The implementation first intersects the circle
with `Q→Jt`, then with `Jt→Jf`, and converts the accepted segment factor
directly to cumulative meridian length. A joint hit has the same cumulative
length from either segment. This ordering intentionally differs from the Perl
routine's middle-segment-first search and states the desired geometry directly:
parallel 15 is the first circle crossing encountered poleward from the
equator. Failure to intersect either segment is a construction error and
throws `std::domain_error`.

## Octant assembly

After zone construction, the half-octant sign is applied as `(x,y) = (x,sy)`.
The two supported rotations are implemented directly:

```text
rotate -60°:
  x' =  x cos60° + y sin60°
  y' = -x sin60° + y cos60°

rotate -120°:
  x' = -x cos60° + y sin60°
  y' = -x sin60° - y cos60°
```

North octants use those rotations directly. South octants first reflect
`x = 2MG - x`. The M-layout transform table is:

| Octant | Reflection | Rotation | Translate `x` |
| ---: | --- | ---: | ---: |
| 1 | none | -120° | `-MG` |
| 2 | none | -60° | `-MG` |
| 3 | none | -120° | `+MG` |
| 4 | none | -60° | `+MG` |
| 5 | `x = 2MG - x` | -60° | `+MG` |
| 6 | `x = 2MG - x` | -120° | `-MG` |
| 7 | `x = 2MG - x` | -60° | `-MG` |
| 8 | `x = 2MG - x` | -120° | `+MG` |

Finally, every octant is translated vertically by `MG sin60°`.

## Octant-qualified reverse

The reverse contract is deliberately not a single unqualified
`(x,y) -> (longitude,latitude)` function. The interrupted M-layout can place a
boundary on more than one planar copy, so the native method accepts one
official assembly octant and the projection-neutral runtime either honors a
caller's `nativeCell` or enumerates all eight cells.

For a selected octant, `inverse()` divides out `MGout`, removes the common
vertical translation, reverses the octant's `-60°` or `-120°` rotation, and
undoes the southern `x = 2MG - x` reflection when present. The result is a
signed canonical half-octant coordinate. Its y sign chooses the west/east
half; the remaining magnitude must be explained by one pair:

```text
0 <= m <= 45
0 <= p <= 90
```

The forward is continuous but piecewise at the A–L zone boundaries. Rather
than differentiate across those joints, the reverse evaluates a five-degree
`m,p` lattice augmented by `m=29` and `p=73`, chooses the smallest-residual
basin, and applies a bounded two-dimensional pattern search. A result is
accepted only when the selected octant's authoritative forward transform
returns to the requested point within `tolerance_pixels`. This makes the
forward residual, rather than a copied external inverse, the numerical oracle.

The geographic sector is reconstructed from the assembly-octant table, and
the public runtime subtracts the one-degree raster registration before
returning longitude. Runtime cells `0..3` represent the four northern sectors;
cells `4..7` are their southern counterparts. Equator points, outer
45° meridians, and poles carry `boundary=true`. Every meridian converges at a
pole, so a cell-qualified polar result uses that octant's center longitude as
a stable representative; only its latitude and residual are geographically
meaningful there.

This capability remains runtime API 2 and advertises
`inverseMode: "face-qualified"`; geometry command buffers remain ABI 1. See
the [projection-neutral forward/reverse contract](forward-reverse-projection-api.md)
for statuses, batches, WebAssembly, workers, D3, and TypeScript behavior.

### Reverse implementation plan and completion record

The Stage 14 implementation followed this bounded plan:

1. **Preserve the public contract.** Keep runtime API 2 and geometry ABI 1,
   add no sentinel coordinates, and promote capability metadata only after a
   checked candidate path exists. **Complete.**
2. **Invert assembly before geography.** Convert screen coordinates to the
   centered scaffold and exactly reverse the selected octant's translation,
   rotation, and southern reflection. **Complete.**
3. **Solve the authoritative construction.** Reuse
   `meridian_parallel_to_xy()` as the oracle over bounded `(m,p)` rather than
   maintaining a second set of inverse A–L formulas. **Complete.**
4. **Restore registration and topology.** Reconstruct the registered sector
   longitude, undo the public one-degree offset, retain runtime-cell identity,
   and explicitly classify cuts and poles. **Complete.**
5. **Verify native numerics.** Cover compatibility anchors, every assembly
   octant, both half-octants and hemispheres, all piecewise transitions,
   unqualified enumeration, exact public seams, poles, batches, invalid input,
   and forward residuals. **Complete.**
6. **Verify consumer parity.** Rebuild the all-projection and compatibility
   WebAssembly modules, then exercise Node, typed arrays, D3, main-thread
   browser calls, and module-worker calls. **Complete.**
7. **Defer composition semantics.** Use this checked solver as the future
   carrier inverse for Star-X, but do not claim Star-X support until its four
   transformed components and unified Antarctic cap have an explicit result
   model. **Open Stage 14 follow-on.**

### Issues found during implementation

- **Runtime cells are not official assembly-octant numbers.** Runtime cells
  are northern `0..3` followed by southern `4..7`; the forward assembly order
  is `1,2,3,4,6,7,8,5`. Treating `cell + 1` as the octant put every southern
  candidate into the wrong transform. The reverse now uses the explicit table
  `{1,2,3,4,6,7,8,5}`.
- **The public longitude sectors include a wrapped first sector.** The visible
  sector is `159°..249°`, while native registered longitude is canonicalized
  around the antimeridian. Reversing with four ordinary closed `[-180,180]`
  intervals misclassified this sector. Reconstruction now happens around the
  registered sector center and canonicalizes only after subtracting the
  one-degree raster offset.
- **The construction is continuous but not globally differentiable.** A
  single Newton solve can cross the 29°/30° or 15°/73°/75° ownership branches,
  use the wrong local derivative, and converge to a residual minimum outside
  the selected octant. The adopted lattice includes the non-five-degree
  joints and the refinement is bounded, derivative-free, and checked through
  the forward transform.
- **Screen and native axes differ.** Runtime points are top-left, y-down frame
  coordinates; the native scaffold is centered and y-up. Attempting assembly
  inversion before removing the projection origin and y reflection produces
  plausible-looking but geographically wrong solutions. The runtime performs
  that conversion explicitly before calling the native reverse.
- **Half-octant sign degenerates on the center line and at poles.** Away from
  those loci, the unassembled y sign identifies the side of the octant. At
  `m=0` both sides are the same meridian, and at `p=90` every meridian is the
  same geographic point. The center line therefore has one natural result;
  the pole uses a documented per-octant representative longitude and is always
  marked as a boundary.
- **A cut cannot be made globally unique by numerical precision.** Equator
  and outer-meridian points can legitimately validate in more than one native
  cell or have only one separated planar copy. Candidate enumeration preserves
  `ambiguous` versus `cut`; `nativeCell` is the only supported way to demand a
  particular copy.
- **Unqualified reverse is intentionally more expensive.** It tests all eight
  octants; a known `nativeCell` tests one. Agentic, editing, and game workflows
  should retain the cell returned by `forward()` and pass it back whenever
  their interaction already identifies the projected component.
- **An inline seed cache was not safe in the closed WebAssembly variant.** An
  attempted 220-point lattice member passed native tests but reproducibly made
  the rebuilt all-projection WASM module trap with an out-of-bounds access on
  an unrelated Myriahedral forward call. Removing the member restored the
  module. The evidence points to the enlarged `std::variant`/WASM stack
  footprint, although the exact Emscripten failure mechanism was not proven.
  The released solver therefore remains stateless; any future cache must be
  out-of-line or shared and must pass the real browser/worker checks before it
  is retained.
- **The compatibility WebAssembly rebuild exposed stale Izzi includes.** The
  old compatibility sources and two embedded-code documentation examples
  still included the removed `a60-svg.h` shim. They now use canonical
  `izzi-svg.h`; both compatibility WebAssembly smoke tests pass again.
- **The focused runtime target did not track projection headers transitively.**
  `PROJECTION_RUNTIME_HEADERS` named the runtime shell but omitted the
  Cahill–Keyes and other concrete projection headers it includes. A solver-only
  header edit could therefore leave a stale native test or all-projection WASM
  binary. The Makefile dependency set now names every concrete runtime
  projection header, so these focused targets rebuild when their mathematics
  changes.

## Public construction and usage

The preferred factory takes the `frame` that owns the requested
`frame.frame_area`:

```c++
const a60::carto::frame::area dimensions {4224, 2112};
const a60::carto::frame map_frame {dimensions};

const auto projection = a60::carto::make_cahill_keyes_projection(
  map_frame, "visionscarto-cahillkeyes-44x22.300");

const auto [x, y] = projection.meridians_to_point_2d(
  48.8575, 2.3514); // latitude, longitude: Paris
```

The equivalent direct construction is:

```c++
const a60::carto::ckproj projection {map_frame, "optional-raster-name"};
```

The raster name is carried in `projection_base::name` and used by
`image_filename()`. It does not load a file and does not affect numeric output.
Existing named objects such as `ck_1xengc`, `ck_2xengc`, and `ck_44x22` are
compatibility presets built on the same variable-frame constructor.

Invalid frame dimensions throw `std::invalid_argument` during construction.
Geographic range errors throw the same exception during projection. Internal
degenerate geometry uses `std::domain_error`.

## Projected path seam handling

The forward API maps one geographic point at a time. Connecting its results
without considering the octahedral cuts can draw a long false line across the
map. The separate path utilities consume **already projected screen points**
and split those paths at discontinuities:

```c++
#include "a60-carto.h"
#include "cart0freak0-cahill-keyes-functions.h"

a60::vrange geographic {
  {21.3, -157.8}, // latitude, longitude
  {-18.1, 178.4},
};

a60::vrange projected;
for (const auto& location : geographic)
  projected.push_back(a60::carto::ckwecarto_44x22.to_point_2d(location));

const a60::vvranges segments = a60::carto::fold_path_edges(
  a60::carto::ckwecarto_44x22, projected);
// Render every element of segments as a separate SVG path.
```

`fold_path_edges()` is the preferred interface. It does not modify its input,
returns no segments for an empty input, and otherwise returns only nonempty
segments. Original points stay ordered. Each split adds an exit point on one
frame edge and a corresponding entry point on the opposite edge.

`minimize_path_distance()` remains as a compatibility interface for callers
that render one segment per iteration. It returns the next continuous segment
and mutates its `vrange&` argument. After a split, that argument contains the
unprocessed suffix beginning at the opposite-edge entry point. When no split
remains, the function returns the final segment and clears the argument:

```c++
while (!projected.empty())
  {
    const a60::vrange segment = a60::carto::minimize_path_distance(
      a60::carto::ckwecarto_44x22, projected);
    // Render segment.
  }
```

Repeated calls produce exactly the same segmentation as
`fold_path_edges()`.

The shared generation path applies this fold automatically for Cahill-Keyes.
It tests each original adjacent projected-point pair before generic native-cell
splitting, because splitting first would discard the relationship needed to
extend an exit and entry to opposite carrier edges. A detected outer-frame
wrap is rendered through `fold_path_edges()`; all other pairs retain the
shared native-cell transition logic used by the other projections. This is
the path used by astronomy reference curves, graticules, Natural Earth
geometry, orbital tracks, atmosphere contours, and network paths.

Native-cell classification uses the same operations as the forward
projection: the public one-degree longitude registration is performed in
`double`, then the registered value is promoted to `long double` before the
native octant formula is evaluated. This ordering matters immediately beside
the visible seams at -111°, -21°, 69°, and 159°. A former add-360/subtract-360
normalization could round a one-ULP neighbor onto the seam for classification
while the forward projection still selected the opposite planar copy.

### Detection and edge-intersection formulas

Let the projection frame have width `W`, height `H`, and drawing origin
`(ox, oy)`. Its screen-space edges are:

```text
L = ox       R = ox + W
T = oy       B = oy + H
```

An adjacent pair is a horizontal wrap candidate when its points occupy the
opposite outer quarters and `abs(xc - xp) >= W/2`. It is a vertical candidate
when its points occupy opposite halves and `abs(yc - yp) >= H/3`. These
thresholds retain the historical Cahill-Keyes M-layout classification while
deriving all lengths from the current variable frame.

For a left-to-right wrap, the current point is temporarily unwrapped as
`xc' = xc - W` and the exit edge is `L`; the reverse direction uses
`xc' = xc + W` and `R`. Top/bottom wrapping applies the same construction with
`H`. For one coordinate `s`, its unwrapped endpoint `e`, and the selected edge
`b`, the segment parameter is:

```text
t = (b - s) / (e - s)
```

The other coordinate is linearly interpolated at `t`. The result is clamped
only to absorb floating-point roundoff at the frame boundary. If both axes
wrap, both endpoint coordinates are unwrapped and the earlier intersection is
emitted first. Equal intersection parameters pass through paired opposite
corners in one split; unequal parameters create the necessary middle segment
between two different frame edges.

The frame origin may be positive or negative, and dimensions may be any valid
2:1 size. The helper independently checks the aspect ratio so an incompatible
cartography fails before path processing. Invalid dimensions/origins and
non-finite projected points throw `std::invalid_argument`. Large jumps that do
not match an opposite-edge classification are preserved unchanged rather than
losing a point.

## Carrier slicing and enlargement

The full Cahill-Keyes projection and a published enlargement have different
frame rules. The complete world is first projected on a finite, positive 2:1
**carrier**. A slice is then a viewport into those projected coordinates; it
is not another projection and is not required to be 2:1.

For a carrier-space view `(x0, y0, w, h)`, the slice descriptor records an
output frame of `w × h` with origin offsets `(-x0, -y0)`. Its local transform
is only:

```text
Xslice = Xcarrier - x0
Yslice = Ycarrier - y0
```

This preserves scale and geographic registration. Enlargement happens because
the smaller viewport receives its own physical page or raster resolution, not
because its coordinates are stretched. Passing an 11×22 strip to `ckproj`
would be an architectural error: the projection correctly rejects that frame,
whereas the slice writer correctly accepts it as a viewport.

Two descriptor families are generated:

1. `make_four_slices()` divides the carrier into four equal-width,
   full-height rectangles. A 44×22 world therefore produces four 11×22 pages
   containing official octant pairs `(1,6)`, `(2,7)`, `(3,8)`, and `(4,5)`.
2. `make_eight_slices()` projects a sampled outline for each official octant,
   computes its natural axis-aligned bounds, and uses the outline as an SVG
   clip path. These eight pages have varying ratios and are semantic faces,
   not cells of a rectangular 4×2 grid.

The four ordered latitude ranges retained in descriptor metadata are
presentation context only. Geographic filtering belongs before projection;
changing a projected viewport cannot turn its irregular face content into a
latitude band.

The SVG wrapper keeps `viewBox` values in unitless carrier coordinates and
expresses output `width` and `height` in inches. It references the complete
Earth SVG through `<use>`, avoiding twelve duplicated copies of a large vector
document. The sibling master SVG is therefore required by an SVG slice, while
the exported PDF and PNG are self-contained. The complete generation,
historical printing context, targets, and raster behavior are documented in
the [generation guide](generation.md#cahill-keyes-enlargement-slices).

## Provenance, compatibility, and intentional divergence

The C++ implementation ports the original mathematical subroutines, not the
Perl program's interactive “Blocks,” file conversion, coastline generation, or
alternative area-code layouts. Corresponding design choices are:

- `calculate_preliminaries()` performs the source `Preliminary` geometry once
  on the canonical `MG = 1` scaffold.
- `longitude_latitude_to_meridian()` implements the source `LLtoMP` mapping.
- `meridian_parallel_to_xy()` implements the A–L portion of `MPtoXY`.
- `half_octant_to_megamap()` implements the eight standard `MJtoMM` placements.
- Intermediate named points and signed path lengths are retained because they
  express the published construction clearly.
- Canonical geometry uses `long double`; output scaling and conversion to
  `double` happen only after octant assembly.
- Direction-vector line intersections replace tangent-slope algebra.
- Closest-approach circle/segment intersections replace the expanded
  quadratic and naive roots.
- Parallel 15 is located by traversing `Q→Jt→Jf`, rather than by preferring the
  middle segment.
- Roundoff-sized, magnitude-aware tolerances are used only to classify a
  circle tangency or segment endpoint that is numerically indistinguishable
  from the boundary.
- The public one-degree longitude adjustment is retained solely for existing
  raster and `augment_carto_geo_specific` registration.
- The projection enum spelling is consistently `cahill_keyes`.

These are intentional numerical divergences from
`MegamapMaker-prep9.pl`. Coordinate agreement with the Perl samples is kept as
a coarse regression signal, but exact last-bit agreement, exception behavior,
root preference, and scale-dependent branch behavior are explicitly not
compatibility requirements.

### Resolved near-cut numerical defect

The former direct port could throw
`Cahill-Keyes parallel 15 misses its meridian` for valid coordinates a few
representable values inside a 45° half-octant boundary. One reproduced case
was public longitude approximately `68.9999999999998°`, latitude `20°`: an
11-unit scaffold threw while 528-, 1056-, and 3300-unit scaffolds succeeded.
The exact 69° cut also succeeded because it selected a separate equality
branch. A geographic construction cannot legitimately change intersection
existence with output size, so this was classified as a forward-projection
defect rather than a source-compatibility requirement.

The source of the defect was a combination of scale-dependent intermediate
coordinates, cancellation in the expanded circle quadratic, and exact tests
of the discriminant and segment endpoints. Generator path bisection reaches
these neighborhoods routinely even though a half-degree coordinate sweep does
not.

Before the numerical correction, Orbital Technosphere generation worked
around the defect by retrying failed points with latitude and longitude
offsets. That workaround could move a coordinate across the very cut being
resolved, concealed unrelated projection exceptions, and made output depend
on retry order. It has been removed: orbital markers, observer sites, labels,
and reference paths now use the same exact-coordinate projection path as every
other generator.

Ocean banding and the Star-X lower-left equatorial notch were different
failures: they came from SVG ring closure, polygon clipping, and paint order,
not the point transform. Their fixes remain documented under
[Natural Earth geometry processing](generation.md#geometry-processing).

There is no subprocess, shell command, JavaScript runtime, temporary output
file, or global coordinate cache in the forward path.

## Verification

Run all standalone tests under strict C++20 warnings:

```sh
make check
```

During Stage 14 development, the reverse-specific unattended checks are:

```sh
make check-forward-reverse-projection-api
make check-wasm-projections
make check-wasm-projections-browser
```

The checks cover:

- Perl-derived compatibility coordinates at a 528-unit scaffold, including
  nontrivial piecewise cases and all eight octants; these are not treated as
  the numerical oracle;
- proportional results at 11-, 528-, 1056-, 1320-, 2112-, and 3300-unit
  scaffolds;
- finite, scale-invariant results in representable-value neighborhoods around
  every native octant cut and the 0°, 15°, 29°, 30°, 45°, 73°, and 75°
  construction transitions, on both coordinate axes and hemispheres;
- one-sided continuity at unfolded cuts and two-sided continuity where a
  construction transition remains within one map face;
- a half-degree sweep of the complete geographic domain: 361 latitudes by 721
  longitudes, or 260,281 projected points, including integer zone and octant
  boundaries and every A–L dispatch region;
- finite, in-frame output for all 27 locations used by
  `augment_carto_geo_specific`;
- expected `projection_api` coordinates for those 27 integration anchors;
- direct reverse recovery for the native compatibility anchors;
- 1,560 qualified reverse samples across all eight runtime cells, both
  half-octants, both hemispheres, and every 15°/29°/30°/73°/75° zone branch;
- qualified and unqualified reverse at 44-, 440-, 3,840-, and 13,200-pixel
  carrier widths;
- all four public registered seams at four latitudes, all eight qualified
  polar copies, equator ambiguity, unqualified candidate enumeration, and
  forced-forward residual acceptance;
- 320×160, 44×22, 4224×2112, 13200×6600, and 1234.5×617.25 frames;
- rejection of 16:9, approximate 2:1, portrait, zero, negative, and infinite
  frames, plus invalid or overflow-prone direct scaffold altitudes;
- preservation of an explicitly offset legacy `projection_base`;
- the checked-in inverse-raster filename convention;
- a real projected seam crossing between 158° E and 162° E;
- forward-consistent native-cell ownership on both sides of all four visible
  seams, including immediately adjacent floating-point values;
- horizontal and vertical path folds in both directions;
- simultaneous corner crossings and ordered two-edge crossings;
- preservation of unrecognized jumps and of the incremental remainder;
- agreement between the non-mutating and stateful path APIs;
- shared-generation edge routing for a sampled celestial equator, ecliptic,
  and galactic equator without almost-full-width interior chords;
- scale and nonzero-origin path behavior; and
- rejection of invalid path sizes, aspect ratios, origins, and points;
- exact four-strip carrier partitioning and official octant-pair metadata;
- bounded, face-clipped outlines for all eight semantic octants;
- inch-sized SVG roots with unscaled carrier-coordinate view boxes; and
- rejection of non-2:1 projection carriers without imposing that ratio on
  slice output frames.

The path-function executable was also run with AddressSanitizer and
UndefinedBehaviorSanitizer. Leak detection was disabled because it is not
supported under the execution environment's `ptrace`; address and undefined
behavior checks passed. The projection, frame, and path headers were also
compiled together against the neighboring real `a60` and `izzi` definitions.
The tests otherwise contain small compatible fixtures so the implementation
can be built without the rest of the application dependency graph.

## Invariants and limitations

- Only the standard M-layout forward/reverse transform is implemented. The alternative
  Butterfly and arbitrary Perl area-code arrangements are outside this class.
- Reverse results are octant-qualified candidates, not a false globally unique
  coordinate. Polar longitude is a documented per-octant representative.
- Equality branches at 0°, 15°, 29°, 30°, 45°, 73°, and 75° define ownership
  of exact geometric boundaries. Adjacent representable values are tested for
  totality and the appropriate one- or two-sided continuity; matching the
  source program's last-bit branch behavior is not an invariant.
- A point API cannot preserve both copies of a geographic position lying on a
  cut. Paths and polygons must be split at projection seams before drawing.
- The fixed one-degree public offset is project registration behavior and must
  be reconsidered if raster assets are re-registered.
- The required frame aspect ratio is 2:1. Letterboxing or cropping a different
  display area belongs outside the projection.
- Direct native construction rejects scaffold altitudes greater than half of
  `double`'s maximum so the complete centered layout remains representable.

## Provenance and licensing

The native implementation is derived from
[`assets.static/cahill-keyes/MegamapMaker-prep9.pl`](../assets.static/cahill-keyes/MegamapMaker-prep9.pl),
dated 2012-03-15 and attributed in its header to Mary Jo Graça, with Gene Keyes
credited for the projection design and calculations. That header permits
modification, reproduction, and redistribution for non-commercial use with
attribution to both Graça and Keyes, and directs commercial users to Gene
Keyes. It does not name a particular Creative Commons license variant.

That upstream notice should be reviewed alongside this repository's license
before redistribution; do not assume that the repository license erases the
source-specific attribution, non-commercial-use, or contact language. The
[bibliography](cahill-keyes-bibliography.md) records the source and design
history.

[Documentation index](../index.md) ·
[Geometric context](cahill-keyes-context.md) ·
[Forward/reverse API](forward-reverse-projection-api.md) ·
[Bibliography](cahill-keyes-bibliography.md)
