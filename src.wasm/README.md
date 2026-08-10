# WebAssembly projection runtime

[Documentation index](../index.md) ·
[Web-developer quick start](../docs/pages/webassembly-quick-start.md) ·
[Forward/reverse API](../docs/forward-reverse-projection-api.md) ·
[Stage 10 implementation notes](../docs/pages/stage-10-webassembly.md) ·
[Slice examples](examples/README.md)

The production browser runtime exposes all six Cartofreako projection models
through one ES-module API. It transforms points, lines, polygon rings,
multi-geometries, finite carrier faces, and slices into a shared typed-array
command buffer. The same buffer feeds the supplied SVG, Canvas, and D3 stream
adapters, either on the main thread or in a Web Worker. Runtime API 3 also
provides structured forward results and candidate-aware reverse projection for
all six families without changing geometry command-buffer ABI 1. Star-X keeps
its ordinary carrier and unified Antarctic cap as explicit components.

The older Cahill-Keyes and land/ocean-only Myriahedral modules remain available
as compatibility builds. New applications should start with
[`cartofreako-web.mjs`](cartofreako-web.mjs).

## Build and test

From the repository root:

```sh
make wasm-projections
make check-forward-reverse-projection-api
make check-wasm-projections
make check-wasm-projections-browser
```

`check-wasm-projections` exercises all six models, all checked Myriahedral
layouts, points, lines, holes, multipolygons, carrier geometry, all four slice
kinds, SVG, Canvas, D3 replay, and the common Cahill-Keyes/Myriahedral Natural
Earth base maps under Node. It also checks forward/reverse result structure,
face/component qualification, batches, singular/cut statuses, and conservative D3
inverse behavior. The browser check serves the files with the proper MIME
types and runs the module, reverse API, Canvas adapter, slices, and worker in
headless Chrome/Chromium.

Build and check every new and compatibility module with:

```sh
make wasm
make check-wasm
```

The generated files are intentionally untracked build artifacts.

## Runtime paths

Deploy these files at the same relative paths, or provide Emscripten's
`locateFile` option when the binary lives elsewhere:

| Path | Role |
| --- | --- |
| `src.wasm/cartofreako-projections.mjs` | Generated Emscripten ES-module loader |
| `src.wasm/cartofreako-projections.wasm` | Generated all-projection binary |
| `src.wasm/cartofreako-web.mjs` | Stable high-level API and GeoJSON flattener |
| `src.wasm/cartofreako-web.d.ts` | TypeScript declarations for runtime API 3 |
| `src.wasm/cartofreako-svg.mjs` | SVG path/document and base-map renderer |
| `src.wasm/cartofreako-canvas.mjs` | Canvas and OffscreenCanvas command replay |
| `src.wasm/cartofreako-d3.mjs` | D3-compatible synchronous stream adapter |
| `src.wasm/cartofreako-projections-worker.mjs` | ES-module worker hosting one WASM runtime |
| `src.wasm/cartofreako-worker-client.mjs` | Promise-based main-thread worker client |

Source and verification paths are:

| Path | Role |
| --- | --- |
| `src.wasm/cartofreako-projections-web.cc` | Thin Embind boundary for the shared C++ runtime |
| `src.projections/cart0freak0-projection-runtime.h` | Projection/layout registry, frame validation, native cells, and seam routing |
| `src.projections/cart0freak0-projection-geometry.h` | Flat geometry protocol, sampling, clipping, and command buffers |
| `src.projections/cart0freak0-projection-slicing.h` | Generic slice descriptors and built-in catalogs |
| `tests/test-projection-runtime.cc` | Native all-model geometry and slice checks |
| `tests/test-forward-reverse-projection-api.cc` | Native exhaustive face-qualified reverse and batch checks |
| `src.wasm/cartofreako-projections-smoke.mjs` | Node integration smoke test |
| `src.wasm/cartofreako-browser-smoke.html` | Real-browser main-thread/worker smoke page |
| `scripts/run-wasm-browser-smoke.py` | Ephemeral local server and Chrome DevTools runner |

Serve `.mjs` as JavaScript and `.wasm` as `application/wasm`. Do not open the
examples through `file://`; module and WASM loading require HTTP(S).

## Minimal API

```js
import createCartofreako from './cartofreako-web.mjs';

const runtime = await createCartofreako();
const projection = runtime.projection({
  name: 'myriahedral',
  frame: [1920, 1080]
});

const tokyo = projection.project(139.6917, 35.6895); // longitude, latitude
const marshall = projection.forward([171.2, 7.1]);
const reverse = projection.inverse([marshall.x, marshall.y]);
const faceQualified = projection.inverse([marshall.x, marshall.y], {
  nativeCell: marshall.nativeCell,
  component: marshall.component
});
const geometry = projection.projectGeometry(geojson, {
  tolerancePx: 0.35,
  slice: null
});

console.log(runtime.apiVersion, runtime.abiVersion);
console.log(projection.metadata(), reverse, faceQualified);
projection.dispose();
```

Omit `height` to derive it from the selected projection's exact native frame
ratio. If both dimensions are supplied, the C++ constructor rejects an
incorrect ratio. Unlike the two compatibility adapters, the high-level
`project(longitude, latitude)` method follows GeoJSON coordinate order.
The structured API uses two-coordinate arrays:
`forward([longitude, latitude])` and `inverse([x, y], options)`.

Available reference identifiers are:

```text
cahill-keyes  authagraph  dymaxion  myriahedral  star-x  voronoi
```

The checked alternate layouts are `myriahedral-americas`,
`myriahedral-atlantic`, `myriahedral-afro-eur-asia`,
`myriahedral-pacific`, and `myriahedral-antarctic`.

## Runtime API 3 and command-buffer ABI 1

The point API and geometry protocol are versioned separately. Runtime API 3
provides `forward`, `forwardMany`, `inverse`, and `inverseMany`; geometry
buffers remain ABI 1. Cahill–Keyes, AuthaGraph, Dymaxion, Myriahedral (all six
layouts), and Voronoi advertise `inverseMode: "face-qualified"`. Star-X
advertises `inverseMode: "candidates"`: carrier component `0` owns latitudes
north of `60°S`, and unified-cap component `1` owns the cutoff and everything
south. `inverse` accepts both `nativeCell` and `component` qualifiers.

See the [forward/reverse implementation notes](../docs/forward-reverse-projection-api.md)
for status semantics, batch fields, native C++ types, algorithms, and
verification.

### Command-buffer ABI 1

`projectGeometry()` accepts GeoJSON or the already flattened form emitted by
`flattenGeoJSON()`. Its output owns normal JavaScript typed arrays; no view
points into growable WASM memory.

| Field | Type | Meaning |
| --- | --- | --- |
| `coordinates` | `Float64Array` | Interleaved local output `x,y` pairs |
| `partOffsets` | `Uint32Array` | Point offsets; length is part count plus one |
| `partTypes` | `Uint8Array` | `0` point, `1` line, `2` ring |
| `featureIds` | `Uint32Array` | Original flattened GeoJSON feature index |
| `nativeCells` | `Uint32Array` | Canonical topology cell for each output part |
| `componentIds` | `Uint32Array` | Disconnected projected component identifier |
| `ringRoles` | `Uint8Array` | `0` none, `1` exterior, `2` hole |
| `closed` | `Uint8Array` | Whether a renderer closes the part |
| `frame` | object | Source origin plus local output width and height |
| `diagnostics` | object | Sampling, transition, cut, wrap, clip, and drop counts |

GeoJSON is flattened in JavaScript before one batched call into WASM. Filled
Cahill-Keyes/Star-X rings are clipped to their geographic octants;
Dymaxion/Myriahedral/Voronoi rings are transformed face-locally and clipped to
exact registered planar triangles; AuthaGraph rings are clipped in its
periodic finite carrier. Exterior and hole pieces retain their roles and are
rendered with the even-odd rule.

## Slices

A slice is always applied to a valid complete carrier. The slice output is
translated into local coordinates by subtracting `sourceView.x/y`; it is never
passed back as a new, wrong-ratio projection frame.

The four kinds are:

| Kind | Stage | Meaning |
| --- | --- | --- |
| `carrier-viewport` | after projection | Rectangular view of the finite carrier |
| `native-cell-mask` | topology/face stage | Exact retained octants, sectors, or faces |
| `geographic-preclip` | before projection | WGS 84 source subset |
| `planar-tile` | after projection | Non-wrapping finite-carrier delivery tile |

Named catalogs reproduce the four Cahill-Keyes strips, eight exact octants,
and two Myriahedral reference-layout face groups:

```js
const slices = projection.listSlices();
const result = projection.projectGeometry(geojson, {slice: 'ck-octant-7'});

const geographic = projection.projectGeometry(geojson, {
  slice: {kind: 'geographic-preclip', bounds: [100, 0, 150, 50]}
});

const tile = projection.projectGeometry(geojson, {
  slice: {kind: 'planar-tile', view: [300, 100, 400, 300]}
});
```

See the [runnable slice examples](examples/README.md) and the
[quick start](../docs/pages/webassembly-quick-start.md#use-a-slice) for exact
carrier/ocean plus feature usage.

## Compatibility modules

These Stage 4.3 targets and APIs remain unchanged:

| Adapter | Generated paths | JavaScript class | Layers |
| --- | --- | --- | --- |
| `cahill-keyes-web.cc` | `cartofreako-cahill-keyes.mjs/.wasm` | `CahillKeyesProjection` | ocean faces, graticules, land |
| `cahill-myriahedral.cc` | `cartofreako-cahill-myriahedral.mjs/.wasm` | `MyriahedralProjection` | exactly ocean and land |

The shared all-projection runtime can reproduce both ocean/land base maps with
`carrierGeometry()` plus `projectGeometry()` and `renderBaseMapSvg()`. Keep the
compatibility modules only for older callers that require
`generateBaseMapSvg(landGeoJson)` or its established serialized styling.

The checked-in
[`cartofreako-cahill-keyes-land-110m.geojson`](cartofreako-cahill-keyes-land-110m.geojson)
derives from Natural Earth's public-domain `ne_110m_land` release. Its five
`ck_band` pieces remain a complete WGS 84 land union; the all-projection
runtime ignores that compatibility property.

## Boundaries and licenses

Runtime API 3 has no globally unique inverse contract: an interrupted cut,
periodic seam, singular vertex, or overlapping Star-X component may return
multiple candidates. Use `nativeCell` and `component` when known; retain
feature IDs and a planar index for feature picking regardless. There is no built-in WebGL
triangulator or XYZ geographic tile scheme; finite-carrier planar tiles are
the supported delivery unit. Input polygon edges should follow RFC 7946's
antimeridian-cut guidance.

The runtime manifest publishes the repository's GPL-3.0-or-later license and
the additional Cahill-Keyes/Star-X notice. The Cahill-Keyes forward
construction derives from work by Mary Jo Graça and Gene Keyes, distributed
for non-commercial use with attribution; commercial users should contact Gene
Keyes. Natural Earth is public domain and applies only when that optional data
asset is deployed.

---

[Documentation index](../index.md) ·
[Web-developer quick start](../docs/pages/webassembly-quick-start.md) ·
[Forward/reverse API](../docs/forward-reverse-projection-api.md) ·
[Stage 10 implementation notes](../docs/pages/stage-10-webassembly.md) ·
[Slice examples](examples/README.md)
