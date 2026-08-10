# Forward and reverse projection API

**Implementation date:** 2026-08-09
**Status:** runtime API 2 implemented; geometry command-buffer ABI 1 retained

[Documentation index](../index.md) ·
[WebAssembly quick start](pages/webassembly-quick-start.md) ·
[Runtime reference](../src.wasm/README.md) ·
[Stage 10 architecture](pages/stage-10-webassembly.md)

## Outcome

Cartofreako now has one projection-neutral, headless point API in native C++,
WebAssembly, the JavaScript wrapper, and the module-worker protocol. Forward
results always expose the projected point, native topology cell, and component.
Reverse results never use a sentinel coordinate: they return an explicit status
and zero or more face-qualified candidates with a forward residual.

The geometry command-buffer ABI remains version 1. The independently versioned
point API is version 2, so existing geometry consumers do not need to change
their buffers merely to detect reverse support.

| Projection family | Forward | Reverse mode | Current boundary |
| --- | --- | --- | --- |
| Cahill–Keyes | Implemented | `none` | Zone-qualified numerical/analytic inverse remains future work. |
| AuthaGraph | Implemented | `none` | Periodic sector inverse and singular-vertex policy remain future work. |
| Dymaxion | Implemented | `none` | Gray-formula face inverse remains future work. |
| Myriahedral, all six layouts | Implemented | `face-qualified` | Analytic inverse over the complete 5,120-face mesh. |
| Star-X | Implemented | `none` | The CK carrier and unified Antarctic compositor need separate inverse semantics. |
| Voronoi | Implemented | `face-qualified` | Analytic inverse over all 20 registered icosahedral faces. |

Unsupported families return `unsupported`; they do not guess, return NaN, or
silently use a different projection.

## Native C++ surface

[`cart0freak0-projection-runtime.h`](../src.projections/cart0freak0-projection-runtime.h)
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
- `maximum_candidates`, which bounds ambiguous output.

An invalid non-finite input, unsafe tolerance, zero candidate limit, or
out-of-range face is a contract error. A finite point outside the carrier is
an ordinary `outside` result.

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
  nativeCell: forward.nativeCell
});

console.log(engine.apiVersion);       // 2
console.log(engine.abiVersion);       // 1
console.log(projection.metadata().inverseMode);
console.log(reverse.status, reverse.candidates);
```

`metadata()` and `listProjections()` expose the input order and degree domain,
pixel units, top-left page origin, right/down axes, exact native aspect,
carrier cut topology, native-cell count, and reverse capability. The wrapper
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

[`cartofreako-web.d.ts`](../src.wasm/cartofreako-web.d.ts) supplies the API 2
TypeScript contract. The worker client exposes the same four point operations.
The D3 adapter provides `invertCandidates(point)` and a conservative
`invert(point)`: the latter returns `[longitude, latitude]` only for a `unique`
result and returns `null` for cuts, ambiguity, outside points, or unsupported
families.

## Status semantics

| Status | Meaning |
| --- | --- |
| `unique` | Exactly one interior face-qualified candidate passed its residual check. |
| `ambiguous` | Several faces or overlapping carrier regions produced valid candidates, or the configured candidate limit was reached. |
| `outside` | The point is outside the finite carrier or inside no registered face. |
| `cut` | Exactly one valid candidate lies on a face boundary; the corresponding neighbor is separated elsewhere in the interrupted net. |
| `unsupported` | The selected projection advertises no reverse implementation. |

Callers must preserve all `ambiguous` candidates or explicitly select a
`nativeCell`. Choosing the first candidate without recording that decision
defeats the purpose of a face-qualified inverse.

## Implemented inverse mathematics

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

## Headless and consent boundary

API 2 performs no network access, opens no UI, displays no authorization
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

The native check covers forward/reverse round trips, unsupported/outside/error
states, batch structure, all 5,120 face centers in each of the six Myriahedral
layouts, every Voronoi face center, and a Myriahedral boundary probe. Node
checks typed arrays and D3 behavior. The Chrome check exercises main-thread and
worker reverse calls through the real Emscripten module.

## Next reverse implementations

1. Dymaxion: invert each registered Gray face/subface and retain every seam
   candidate.
2. Cahill–Keyes: undo octant assembly, enumerate zones, solve branches with a
   safeguarded method, and compare—not copy—D3's inverse as an external oracle.
3. AuthaGraph: invert the published sector algebra with explicit periodic and
   singular-vertex behavior.
4. Star-X: reverse the carrier transforms into CK candidates, then specify a
   separate result for the unified Antarctic cap whose compositor supersedes
   four ordinary source copies.

Each promotion requires independent anchors, forward→reverse and
reverse→forward residual campaigns, cut/hinge/pole/antimeridian probes,
multiple frame scales, batch checks, and headless Node/browser parity.

---

[Documentation index](../index.md) ·
[WebAssembly quick start](pages/webassembly-quick-start.md) ·
[Runtime reference](../src.wasm/README.md)
