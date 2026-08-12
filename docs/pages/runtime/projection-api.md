# Forward and reverse projection API

**Implementation dates:** 2026-08-09; all-family reverse completed 2026-08-10
**Status:** runtime API 3 implemented; geometry command-buffer ABI 1 retained

[Documentation index](../../../index.md) ·
[WebAssembly quick start](webassembly-quick-start.md) ·
[Runtime reference](../../../src.wasm/README.md) ·
[Stage 10 architecture](webassembly-architecture.md)

## Outcome

Cartofreako now has one projection-neutral, headless point API in native C++,
WebAssembly, the JavaScript wrapper, and the module-worker protocol. Forward
results always expose the projected point, native topology cell, and component.
Reverse results never use a sentinel coordinate: they return an explicit status
and zero or more face-qualified candidates with a forward residual.

The geometry command-buffer ABI remains version 1. The independently versioned
point API is version 3. API 3 completes reverse support for all six projection
families, adds an optional inverse component selector, and makes the current
two-component Star-X composition authoritative for structured point calls.
Existing geometry consumers do not need to change their command buffers.

| Projection family | Forward | Reverse mode | Current boundary |
| --- | --- | --- | --- |
| Cahill–Keyes | Implemented | `face-qualified` | Octant-qualified bounded numerical inverse over the authoritative piecewise forward construction. |
| AuthaGraph | Implemented | `face-qualified` | Analytic 24-sector inverse with periodic-copy enumeration and explicit tetrahedron-vertex ambiguity. |
| Dymaxion | Implemented | `face-qualified` | Exact Gray-transform inverse over all 23 registered faces/subfaces. |
| Myriahedral, all six layouts | Implemented | `face-qualified` | Analytic inverse over the complete 5,120-face mesh. |
| Star-X | Implemented | `candidates` | Component 0 reverses the ordinary carrier; component 1 reverses the fixed-`60°S` unified Antarctic cap. |
| Voronoi | Implemented | `face-qualified` | Analytic inverse over all 20 registered icosahedral faces. |

Every family in the current registry is reversible. The `unsupported` status
remains part of the stable result vocabulary for a future registered layout
that has forward but not reverse support; it never means “guess with another
projection.”

Stage 16J also implements Equal Earth forward/reverse equations through a
[standalone experimental API](../projections/equal-earth/implementation.md).
Equal Earth is intentionally absent from runtime API 3, the six-family enum,
the standard artifact catalog, and release generation. Its separate neutral
fixtures and page wrapper let it serve as a checked comparison method without
silently changing this API's family registry.

## Native C++ surface

[`cart0freak0-projection-runtime.h`](../../../src.projections/cart0freak0-projection-runtime.h)
defines the contract:

```cpp
using projection_handle = projection_context;

struct geographic_coordinate {
  double longitude_degrees;
  double latitude_degrees;
};

struct projected_coordinate { double x; double y; };

struct forward_result {
  projected_coordinate point;
  std::uint32_t native_cell;
  std::uint32_t component;
};

enum class inverse_status {
  unique, ambiguous, outside, cut, unsupported
};

struct inverse_candidate {
  geographic_coordinate point;
  std::uint32_t native_cell;
  std::uint32_t component;
  double forward_residual;
  bool boundary;
};

forward_result forward(projection_handle const&, geographic_coordinate);
inverse_result inverse(projection_handle const&, projected_coordinate,
                       inverse_options = {});
```

`forward_many` and `inverse_many` take C++20 spans and retain one structured
result per input. Longitude precedes latitude in this API. The older internal
`geographic_point` remains latitude/longitude so existing generation code does
not change order silently.

`inverse_options` accepts:

- `tolerance_pixels`, a finite positive residual and boundary tolerance;
- optional `native_cell`, which restricts the solve to one known face; and
- optional `component`, which is `0` for ordinary single-component layouts
  and selects Star-X carrier `0` or unified Antarctic cap `1`; and
- `maximum_candidates`, which bounds ambiguous output.

An invalid non-finite input, unsafe tolerance, zero candidate limit, or
out-of-range face/component is a contract error. A finite point outside the
carrier is an ordinary `outside` result.

## JavaScript and WebAssembly surface

The high-level wrapper follows array/GeoJSON order:

```js
import createCartofreako from './cartofreako-web.mjs';

const engine = await createCartofreako();
const projection = engine.projection({
  name: 'myriahedral-pacific',
  frame: [1920, 1080]
});

const forward = projection.forward([171.2, 7.1]);
const reverse = projection.inverse([forward.x, forward.y]);
const qualified = projection.inverse([forward.x, forward.y], {
  nativeCell: forward.nativeCell,
  component: forward.component
});

console.log(engine.apiVersion);       // 3
console.log(engine.abiVersion);       // 1
console.log(projection.metadata().inverseMode);
console.log(reverse.status, reverse.candidates);
```

`metadata()` and `listProjections()` expose the input order and degree domain,
pixel units, top-left page origin, right/down axes, exact native aspect,
carrier cut topology, native-cell and component counts, and reverse capability. The wrapper
deep-freezes this manifest so a consumer cannot mutate the registry used to
construct later projection instances.

`forwardMany(Float64Array)` consumes packed longitude/latitude pairs and
returns packed `coordinates`, `nativeCells`, and `componentIds`.
`inverseMany(Float64Array)` consumes packed x/y pairs and returns:

```text
statuses             Uint8Array    one status per input point
candidateOffsets     Uint32Array   candidate ranges, input count + 1
coordinates          Float64Array  packed longitude/latitude candidates
nativeCells          Uint32Array   one per candidate
componentIds         Uint32Array   one per candidate
forwardResiduals     Float64Array  pixels, one per candidate
boundaries           Uint8Array   one boundary flag per candidate
truncated            Uint8Array   one truncation flag per input point
```

[`cartofreako-web.d.ts`](../../../src.wasm/cartofreako-web.d.ts) supplies the API 3
TypeScript contract. The worker client exposes the same four point operations.
The D3 adapter provides `invertCandidates(point)` and a conservative
`invert(point)`: the latter returns `[longitude, latitude]` only for a `unique`
result and returns `null` for cuts, ambiguity, outside points, or unsupported
families.

For Star-X, an unqualified inverse can legitimately return carrier and cap
candidates from the same page coordinate. A consumer that is reversing its
own forward result should pass both `nativeCell` and `component`. The structured
Star-X forward routes latitudes north of `60°S` to carrier component `0` and
latitudes at or south of `60°S` to cap component `1`. The lower-level C++
`starxproj` forward remains the ordinary carrier transform for diagnostics and
generator composition.

## Status semantics

| Status | Meaning |
| --- | --- |
| `unique` | Exactly one interior face-qualified candidate passed its residual check. |
| `ambiguous` | Several faces or overlapping carrier regions produced valid candidates, or the configured candidate limit was reached. |
| `outside` | The point is outside the finite carrier or inside no registered face. |
| `cut` | Exactly one retained candidate lies on a registered face, periodic, component, cutoff, or singular boundary. A qualifier or the net registration may place adjacent topology elsewhere. |
| `unsupported` | The selected projection advertises no reverse implementation. |

Callers must preserve all `ambiguous` candidates or explicitly select a
`nativeCell`. Choosing the first candidate without recording that decision
defeats the purpose of a face-qualified inverse.

## Implemented inverse mathematics

### Cahill–Keyes

The reverse first converts screen coordinates back to the centered native
Megamap scaffold. For each requested or enumerated native cell it maps the
runtime cell to the official Cahill–Keyes assembly octant, then exactly undoes
that octant's translation, `-60°` or `-120°` rotation, and southern reflection.
The sign of the recovered half-octant y coordinate selects the corresponding
side of the octant meridian.

The remaining canonical solve is bounded to meridian magnitude `[0°, 45°]`
and absolute parallel `[0°, 90°]`. The Cahill–Keyes forward construction is
piecewise at the 29°/30° meridian transition and the 15°, 73°, and 75°
parallels, so the reverse does not assume one differentiable formula. It
selects a basin from a five-degree lattice augmented with the 29° and 73°
joints, then runs a bounded two-dimensional pattern search against the native
forward transform. Only candidates whose forced-octant forward residual fits
the caller's pixel tolerance are retained.

The solver then reconstructs the registered sector longitude, reverses the
project's one-degree raster registration, and marks the Equator, outer
octant meridians, and poles as boundaries. All meridians converge at a pole;
there the API returns the selected octant's center longitude as a stable
representative, marks it as a boundary, and makes no claim that polar
longitude is unique. This implementation derives from Cartofreako's checked
native forward construction; it does not copy D3's inverse.

### AuthaGraph

The inverse converts the screen point back to the unnormalized periodic
tetrahedron net and enumerates the 24 registered cells plus the finite set of
horizontal periodic copies that can meet the rectangle. For each cell it
subtracts the published lattice origin and applies the inverse of that cell's
multiple-of-30-degree rotation. This recovers the canonical analytic triangle
coordinate `(x,y)`.

The published forward equations can then be inverted directly. With reduced
sector longitude `r`, the runtime reconstructs

```text
c = sqrt(2) - sqrt(3)y
A = pi x / (2c)
A = r - asin(sin(r) / sqrt(3))
tan(local_latitude) = (2 + cos(r)) / c - sqrt(2)
```

The `A(r)` function is monotone on `[-pi/3,pi/3]`, so a bounded scalar solve
has one result. Sector parity chooses the correct 60-degree interval and
restores the complete pole-local longitude. The runtime reconstructs the
global unit vector from the selected tetrahedron vertex, its prime-meridian
tangent, and their cross product. It rejects candidates that do not retain the
selected nearest vertex/sector and accepts only a complete periodic forward
residual within tolerance. At `c=0` all six sectors meet at a tetrahedron
vertex; those copies are reported as boundary candidates instead of assigning
an invented longitude.

### Dymaxion

The reverse first undoes screen normalization and enumerates every registered
planar triangle containing the point. This includes the separate Australia
and Japan subfaces, so their established 23-piece Airocean layout and tie rule
are preserved. Planar barycentric weights transfer the point through the
face's affine registration into the canonical equilateral triangle used by
the exact Fuller transform.

Gray's forward equations express canonical `x,y` as symmetric combinations of
the three spherical edge distances `a1,a2,a3`. The inverse separates those
distances into one unknown mean plus three offsets fixed by `x,y`. It solves
the monotone scalar constraint that the three corresponding gnomonic edge
coordinates sum to the icosahedron chord length, reconstructs face-local
gnomonic `x,y,z`, normalizes the direction, and applies the stored orthonormal
face basis. A forced transform through the selected face/subface supplies the
final pixel residual. No approximate planar barycentric direction is
substituted for the exact Fuller calculation.

### Myriahedral

The inverse undoes the registered 16:9 canvas normalization, enumerates every
planar triangle containing the point, and recovers its widened barycentric
weights. The same weights combine the corresponding spherical chord-face
vertices; normalizing that vector returns the geographic direction. The
candidate is forced forward through the same face and accepted only when its
pixel residual is within tolerance. This applies unchanged to the reference,
Americas, Atlantic, Afro–Eur–Asia, Pacific, and Antarctic layouts.

### Voronoi

The inverse undoes the 960×500 source-canvas registration and 108-degree input
rotation. It enumerates the 20 transformed face triangles, recovers planar
barycentrics, reconstructs and normalizes the spherical direction, reverses
the longitude rotation, and verifies the candidate through that registered
face. Periodic/cut boundaries therefore remain candidates rather than being
collapsed into an invented globally unique coordinate.

### Star-X

Star-X has two useful page components and API 3 keeps them distinct.

For carrier component `0`, the inverse removes the uniform page-centered
enlargement, undoes the selected square group's translation, reverses the
upper group's 180-degree rotation when applicable, and recovers centered
Cahill–Keyes M-layout coordinates. It then invokes the checked native
Cahill–Keyes inverse for the corresponding assembly octant and verifies the
ordinary Star-X forward residual. In the composed API, this component owns
latitudes strictly north of `60°S`.

For cap component `1`, the inverse subtracts the projection-only registered
South Pole and recovers geographic bearing with `atan2(dx,-dy)`. It solves
latitude monotonically in `[-90°,-60°]` against the authoritative
`antarctic_source_radius()` function, projects the result through the unified
cap again, and retains it only within pixel tolerance. Exact registered
quadrant meridians are snapped back to their deterministic native-cell tie
rule. The `60°S` circumference and quadrant seams are cuts. At the South Pole,
longitude is undefined, so a component-1 inverse without `nativeCell` returns
four stable quadrant-center representatives in southern cells 4–7; a
native-cell qualifier selects one. Page overlap between the top-painted cap and ordinary
carrier remains explicit as multiple component-qualified candidates.

## Headless and consent boundary

API 3 performs no network access, opens no UI, displays no authorization
prompt, and persists no state. It is safe to call from Node, a module worker,
headless Chrome, a build agent, or a game toolchain. Source-license acceptance,
dataset consent, local-governance restrictions, and publication authorization
belong to the calling workflow. An agent should pass and log those decisions
alongside the projection ID, layout, frame, native-cell choice, source artifact
ID, and checksum; the numerical API does not fabricate consent on the caller's
behalf.

## Verification

Run the focused native and headless browser checks:

```sh
make check-forward-reverse-projection-api
make check-wasm-projections
make check-wasm-projections-browser
```

The native check covers outside/error states, batch structure, 1,560
Cahill–Keyes interior samples spanning every octant and piecewise zone, 16
registered outer-meridian probes, eight qualified pole probes, four carrier
scales, all 24 AuthaGraph sectors plus a global coordinate lattice, all 23
Dymaxion faces/subfaces plus the same lattice, all 5,120 face centers in each
of the six Myriahedral layouts, every Voronoi face center, and Star-X carrier,
cap, cutoff, quadrant-seam, overlap, and South-Pole behavior. Node checks all
six advertised modes, typed arrays, component-qualified Star-X and D3
inversion. The Chrome check repeats main-thread and module-worker reverse calls
through the real Emscripten module, including the Star-X cap.

## Deliberate boundaries

- Reverse coordinates describe the same spherical WGS 84 longitude/latitude
  domain used by the forward implementations; they are not ellipsoidal geodesic
  solutions.
- `projectGeometry()` retains geometry command-buffer ABI 1 and its existing
  topology-safe ordinary Star-X carrier. The generated Star-X atlas compositor
  still performs layer-aware clipping and topmost cap painting. API 3's
  structured point forward/reverse is the component-aware interface.
- A D3-style `invert()` cannot express multiple faces or components. It
  therefore returns `null` unless the result is `unique`; use
  `invertCandidates()` for editing, seams, and Star-X.
- Numerical reverse is necessarily more expensive for the piecewise
  Cahill–Keyes construction and Star-X carrier than for the analytic
  polyhedral families. Use `nativeCell`, `component`, and packed batches when
  those identities are already known.

---

[Documentation index](../../../index.md) ·
[WebAssembly quick start](webassembly-quick-start.md) ·
[Runtime reference](../../../src.wasm/README.md)
