# Cahill-Keyes C++20 implementation notes

[Documentation index](../index.md) ·
[Geometric context](cahill-keyes-context.md) ·
[Bibliography](cahill-keyes-bibliography.md)

## Scope and result

The implementation replaces the former per-point Node.js subprocess, shared
temporary file, and fixed-height caches with an in-process C++20 forward
projection. It ports the coordinate-conversion core of Mary Jo Graça and Gene
Keyes's `MegamapMaker-prep9.pl`, including:

- longitude/latitude normalization into eight octants and sixteen mirrored
  half-octants;
- the complete A–L piecewise graticule construction;
- the supple-zone line/circle intersection;
- all eight rotations and reflections in the standard M-layout; and
- uniform scaling from the canonical 10,000-unit scaffold to an arbitrary
  positive, finite 2:1 map frame.

The public class remains `a60::carto::ckproj` and continues to implement
`a60::carto::projection_api`. Its existing `projection_base` constructor and
named presets remain available. New code can construct it directly from an
`a60::carto::frame`.

The work was delivered in three stages:

1. **Native projection:** translate the forward construction to C++20 and
   verify it against the Perl results and `augment_carto_geo_specific` anchors.
2. **Variable frames:** derive every length and origin from
   `frame.frame_area`, enforce the projection's 2:1 aspect ratio, and retain
   the named compatibility presets.
3. **Documentation:** record the geometry, formulas, implementation choices,
   usage, verification method, provenance, and bibliography in this
   documentation set.

## Code organization

| Component | Responsibility |
| --- | --- |
| [`a60-carto-projection-cahill-keyes.h`](../src/a60-carto-projection-cahill-keyes.h) | Numeric forward projection, frame validation, `projection_api` adapter, screen-coordinate conversion, raster naming, and compatibility presets |
| [`a60-carto-projection-cahill-keyes-functions.h`](../src/a60-carto-projection-cahill-keyes-functions.h) | Scale- and offset-aware splitting of projected paths at wrapped frame edges |
| [`test-cahill-keyes-projection.cc`](../tests/test-cahill-keyes-projection.cc) | Native reference points, scale invariance, domain sweep, and invalid geographic input |
| [`test-cahill-keyes-projection-api.cc`](../tests/test-cahill-keyes-projection-api.cc) | Public API anchors, variable frames, invalid frames, raster paths, and compatibility construction |
| [`test-cahill-keyes-path-functions.cc`](../tests/test-cahill-keyes-path-functions.cc) | Horizontal, vertical, corner, two-edge, variable-frame, stateful, and invalid path cases |

`ck_native::forward_projection` owns all scale-dependent construction values.
Its constructor calculates the fixed scaffold geometry once. Calls to
`operator()` are then stateless and require no cache or external process.

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

The scaffold altitude and scale factor are:

```text
MG = H / 2 = W / 4
q  = MG / 10000 = H / 20000 = W / 40000
```

The original M-layout spans 40,000 units when `MG = 10,000`, so these formulas
fit it exactly to the frame width. Every construction length is multiplied by
`q`; angles and geographic zone boundaries remain unchanged. Important scaled
constants are:

| Quantity | Value |
| --- | ---: |
| `MA` | `940q` |
| ordinary latitude spacing | `100q` per degree |
| polar latitude spacing | `104q` per degree |
| `AP75` | `1560q` |
| `AP73` | `1760q` |

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

The port uses `double`, `std::numbers::pi_v<double>`, `std::hypot`, and four
small geometry operations.

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

For two lines through `P1`, `P2` at angles `θ1`, `θ2`, let
`a1 = tan(θ1)` and `a2 = tan(θ2)`. Their intersection is:

```text
x = (a1*P1x - a2*P2x - P1y + P2y) / (a1 - a2)
y = a1 * (x - P1x) + P1y
```

For a circle with center `C`, radius `r`, and a segment from `P0` to `P1`, set
`d = P1 - P0` and solve `|P0 + td - C|² = r²`:

```text
A = d·d
B = 2 d·(P0 - C)
Cq = (P0 - C)·(P0 - C) - r²
t = (-B ± sqrt(B² - 4 A Cq)) / (2A)
```

Only roots in `[0,1]` are segment intersections. A negative discriminant, a
zero-length segment, or roots outside the segment report no intersection.

## Reference half-octant construction

### Preliminary scaffold

Let `S = MG`. The primary points are:

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
Cy = (|V|² - |D|²)
     / (2 * (√3(Vx - Dx) + (Vy - Dy)))
Cx = √3 Cy
R  = distance(C, D)
```

All these values are computed once in the native projection constructor.

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

The conditions are evaluated in the following order, which resolves boundary
overlap exactly as the Perl implementation does:

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

For `m > 29°`, the 15° path length is found by intersecting the supple circle
with segment `Jt→Jf`. If that segment does not contain the intersection, the
algorithm tries `Q→Jt` and subtracts the distance back from `Jt`. Failure to
intersect either segment is a construction error and throws
`std::domain_error`.

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
#include "a60-carto-projection-cahill-keyes-functions.h"

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

## Translation method and compatibility decisions

The C++ implementation ports the original mathematical subroutines, not the
Perl program's interactive “Blocks,” file conversion, coastline generation, or
alternative area-code layouts. Corresponding design choices are:

- `calculate_preliminaries()` performs the source `Preliminary` work once per
  projection scale.
- `longitude_latitude_to_meridian()` implements the source `LLtoMP` mapping.
- `meridian_parallel_to_xy()` implements the A–L portion of `MPtoXY`.
- `half_octant_to_megamap()` implements the eight standard `MJtoMM` placements.
- Intermediate named points and signed path lengths are retained so formulas
  can be compared to the source rather than algebraically collapsed.
- Double-precision operations replace Perl numeric scalars, with explicit
  finite/range validation and standard-library trigonometry.
- The public one-degree longitude adjustment is retained solely for existing
  raster and `augment_carto_geo_specific` registration.
- The projection enum spelling is consistently `cahill_keyes`.

There is no subprocess, shell command, JavaScript runtime, temporary output
file, or global coordinate cache in the forward path.

## Verification

Run all standalone tests under strict C++20 warnings:

```sh
make check
```

The checks cover:

- Perl-derived numeric reference coordinates at a 528-unit scaffold,
  including nontrivial piecewise cases and all eight octants;
- exact proportional results at 1056-, 1320-, and 2112-unit scaffolds;
- a half-degree sweep of the complete geographic domain: 361 latitudes by 721
  longitudes, or 260,281 projected points, including integer zone and octant
  boundaries and every A–L dispatch region;
- finite, in-frame output for all 27 locations used by
  `augment_carto_geo_specific`;
- expected `projection_api` coordinates for those 27 integration anchors;
- 320×160, 44×22, 4224×2112, 13200×6600, and 1234.5×617.25 frames;
- rejection of 16:9, approximate 2:1, portrait, zero, negative, and infinite
  frames;
- preservation of an explicitly offset legacy `projection_base`;
- the checked-in inverse-raster filename convention;
- a real projected seam crossing between 158° E and 162° E;
- horizontal and vertical path folds in both directions;
- simultaneous corner crossings and ordered two-edge crossings;
- preservation of unrecognized jumps and of the incremental remainder;
- agreement between the non-mutating and stateful path APIs;
- scale and nonzero-origin path behavior; and
- rejection of invalid path sizes, aspect ratios, origins, and points.

The path-function executable was also run with AddressSanitizer and
UndefinedBehaviorSanitizer. Leak detection was disabled because it is not
supported under the execution environment's `ptrace`; address and undefined
behavior checks passed. The projection, frame, and path headers were also
compiled together against the neighboring real `a60` and `izzi` definitions.
The tests otherwise contain small compatible fixtures so the implementation
can be built without the rest of the application dependency graph.

## Invariants and limitations

- Only the standard M-layout forward transform is implemented. The alternative
  Butterfly and arbitrary Perl area-code arrangements are outside this class.
- There is no inverse `(x,y)` to `(latitude,longitude)` solver.
- Equality branches at 0°, 15°, 29°, 30°, 45°, 73°, and 75° intentionally
  reproduce source boundary decisions.
- A point API cannot preserve both copies of a geographic position lying on a
  cut. Paths and polygons must be split at projection seams before drawing.
- The fixed one-degree public offset is project registration behavior and must
  be reconsidered if raster assets are re-registered.
- The required frame aspect ratio is 2:1. Letterboxing or cropping a different
  display area belongs outside the projection.

## Provenance and licensing

The native implementation is derived from
[`assets/cahill-keyes/MegamapMaker-prep9.pl`](../assets/cahill-keyes/MegamapMaker-prep9.pl),
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
[Bibliography](cahill-keyes-bibliography.md)
