# Cartofreako WebAssembly quick start

[Documentation index](../../index.md) ·
[Runtime reference](../../src.wasm/README.md) ·
[Runnable examples](../../src.wasm/examples/README.md) ·
[Stage 10 notes](stage-10-webassembly.md)

This is the short path for a web developer who wants an interrupted world map
without learning the native SVG generation system. The API accepts ordinary
GeoJSON, supports all six projections, and returns one typed-array geometry
format for SVG, Canvas, D3, workers, and custom renderers.

## 1. Build

From the repository root:

```sh
make wasm-projections
make check-wasm-projections
```

For the real-browser and worker check:

```sh
make check-wasm-projections-browser
```

The build creates these two untracked artifacts beside the checked-in browser
helpers:

```text
src.wasm/cartofreako-projections.mjs
src.wasm/cartofreako-projections.wasm
```

## 2. Deploy

The smallest normal deployment keeps these three files together:

```text
cartofreako-web.mjs
cartofreako-projections.mjs
cartofreako-projections.wasm
```

Add whichever output adapters you use:

```text
cartofreako-canvas.mjs
cartofreako-svg.mjs
cartofreako-d3.mjs
cartofreako-projections-worker.mjs
cartofreako-worker-client.mjs
```

Serve `.wasm` as `application/wasm` and `.mjs` as JavaScript. Use HTTP(S), not
`file://`. For a local trial from the repository root:

```sh
python3 -m http.server 8000
```

Then open
`http://localhost:8000/src.wasm/examples/slices.html`.

## 3. Project GeoJSON to Canvas

```html
<canvas id="map" width="1200" height="600"></canvas>
<script type="module">
  import createCartofreako from './cartofreako-web.mjs';
  import {drawBaseMap} from './cartofreako-canvas.mjs';

  const runtime = await createCartofreako();
  const projection = runtime.createProjection({
    id: 'cahill-keyes',
    width: 1200
  });

  const land = await fetch('./land.geojson').then(r => r.json());
  const ocean = projection.carrierGeometry();
  const features = projection.projectGeometry(land, {
    tolerancePx: 0.35
  });

  const canvas = document.querySelector('#map');
  canvas.width = features.frame.width;
  canvas.height = features.frame.height;
  drawBaseMap(canvas.getContext('2d'), ocean, features);

  projection.dispose();
</script>
```

Only `width` is needed; the runtime derives the exact native height. If you
provide both dimensions, an incorrect ratio is rejected. The high-level API
uses GeoJSON order: `projection.project(longitude, latitude)`.

Switch projection models by changing `id`:

```text
cahill-keyes  authagraph  dymaxion  myriahedral  star-x  voronoi
```

## Return SVG instead

```js
import {renderBaseMapSvg} from './cartofreako-svg.mjs';

const svg = renderBaseMapSvg(
  projection.carrierGeometry(),
  projection.projectGeometry(land),
  {title: 'Myriahedral world map'}
);
document.querySelector('#map').innerHTML = svg;
```

`renderBaseMapSvg()` emits separate `ocean` and `land` groups. For arbitrary
marks or lines, use `renderSvg(projectedBuffer)`.

## Use a slice

Create the projection on its complete ratio-correct carrier, then pass a slice
to both the carrier and feature calls:

```js
const projection = runtime.createProjection({
  id: 'cahill-keyes',
  width: 1200
});

const options = {slice: 'ck-octant-7'};
const ocean = projection.carrierGeometry(options);
const features = projection.projectGeometry(land, options);

console.log(features.frame);
// Local arbitrary-ratio frame. Coordinates already have source x/y removed.
```

Discover named slices:

```js
for (const slice of projection.listSlices()) {
  console.log(slice.id, slice.kind, slice.sourceView);
}
```

Built-in IDs are `ck-strip-1` through `ck-strip-4`, `ck-octant-1`
through `ck-octant-8`, and `myria-group-1`/`myria-group-2` on the reference
Myriahedral layout.

Use a source-region preclip when the desired region is geographic:

```js
const eastAsia = projection.projectGeometry(land, {
  slice: {
    kind: 'geographic-preclip',
    bounds: [100, 0, 150, 50] // west, south, east, north
  }
});
```

Use a finite-carrier tile or viewport for pan/zoom delivery:

```js
const tile = projection.projectGeometry(land, {
  slice: {
    id: 'z2-x1-y0',
    kind: 'planar-tile',
    view: [300, 0, 300, 300] // carrier x, y, width, height
  }
});
```

An advanced custom face mask names native cells explicitly:

```js
const faces = projection.projectGeometry(land, {
  slice: {
    kind: 'native-cell-mask',
    selectedCells: [4, 5, 6, 18, 19]
  }
});
```

The key rule is that none of these output dimensions reconstructs the
projection. A slice filters or views the complete carrier and then translates
retained coordinates locally.

Run the checked examples from Node:

```sh
node src.wasm/examples/slice-node.mjs ck-octant-7
node src.wasm/examples/slice-node.mjs myria-group-1
```

## Keep projection work off the main thread

```js
import CartofreakoWorkerClient from './cartofreako-worker-client.mjs';
import {drawCommandBuffer} from './cartofreako-canvas.mjs';

const worker = new CartofreakoWorkerClient();
const projected = await worker.projectGeometry(
  {id: 'voronoi', width: 1200},
  geojson,
  {slice: null, tolerancePx: 0.35}
);

drawCommandBuffer(context, projected);
worker.terminate();
```

The worker parses GeoJSON, owns its WASM instance, and transfers output array
buffers back to the page. It uses an ordinary module worker and does not
require shared memory or cross-origin isolation.

## Use with D3

Load `d3-geo` however your application normally does, then use the supplied
stream adapter as the projection passed to `geoPath`:

```js
import {geoPath} from 'd3-geo';
import {cartofreakoD3Projection} from './cartofreako-d3.mjs';

const adapter = cartofreakoD3Projection(projection, {
  slice: 'ck-strip-2',
  tolerancePx: 0.35
});
const path = geoPath(adapter);
svgPath.setAttribute('d', path(geojson));
```

The adapter buffers each source line or polygon, calls WASM in a batch, then
replays topology-safe events to D3's sink. It does not call into WASM once per
vertex.

## Leaflet and OpenLayers

Treat the result as a finite planar carrier:

- Leaflet: use `L.CRS.Simple`, disable wrapping, and place the generated SVG,
  Canvas, or image in bounds matching `buffer.frame`.
- OpenLayers: use a finite custom projection extent and add already projected
  vector or raster layers.

Do not register the forward transform as if it had one continuous global
inverse. Interrupted cuts can map one planar boundary to multiple geographic
candidates. For clicks and hover, retain `featureIds` and index the projected
parts in planar space.

## Typed-array input for high-volume data

Skip GeoJSON parsing when data is already flat:

```js
const projected = projection.projectGeometry({
  coordinates: new Float64Array([lon0, lat0, lon1, lat1]),
  partOffsets: new Uint32Array([0, 2]),
  partTypes: new Uint8Array([1]),       // line
  featureIds: new Uint32Array([42]),
  ringRoles: new Uint8Array([0])
});
```

The returned arrays are owned JavaScript copies, so later WASM memory growth
does not invalidate them.

## Common mistakes

| Symptom | Fix |
| --- | --- |
| WASM fetch or CORS error | Serve through HTTP(S), keep loader and binary together, and send `application/wasm` |
| Frame-ratio exception | Supply only `width`, or use the exact ratio from `runtime.manifest` |
| Lines jump across the page | Do not project raw vertices yourself; pass complete lines/rings to `projectGeometry()` |
| A slice is distorted | Keep the full carrier; use `{slice: ...}` rather than constructing a projection from slice dimensions |
| Main thread stalls on a large file | Use `CartofreakoWorkerClient` |
| Click cannot produce longitude/latitude | ABI 1 has no global inverse; use feature IDs and planar hit testing |

Inspect `runtime.manifest` and `runtime.licenses` before publishing. The
Cahill-Keyes and Star-X implementations carry an additional attribution and
commercial-use notice beyond the repository's GPL license.

---

[Documentation index](../../index.md) ·
[Runtime reference](../../src.wasm/README.md) ·
[Runnable examples](../../src.wasm/examples/README.md) ·
[Stage 10 notes](stage-10-webassembly.md)
