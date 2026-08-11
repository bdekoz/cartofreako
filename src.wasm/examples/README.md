# Browser examples

Serve `src.wasm` after running `make wasm-projections`; ES modules and WASM
cannot be tested reliably through `file://` URLs.

The interactive example is [`slices.html`](slices.html). It projects the same
Natural Earth geometry through the complete carrier and then applies a named
Cahill-Keyes or Myriahedral slice.

[`screen-1080p.html`](screen-1080p.html) is the six-projection consumer
canary. It draws an interrupted map into an exact 1920 × 1080 contain-fit
Canvas, treats its light-gray letterbox/pillarbox region as non-map space, and
passes pointer coordinates through the catalog-compatible affine transform to
the candidate-aware reverse API. Its dependency-free texture-plane record can
be copied into Three.js or raw WebGL without pretending the plate is an
equirectangular globe texture.

[`screen-1080p-three.html`](screen-1080p-three.html) loads the checked catalog
and lossless WebP onto a real Three.js r185 `PlaneGeometry`, converts raycast
UVs back to screen/projected coordinates, and preserves candidate-aware
geographic picks. Serve the repository root (not only `src.wasm`) after
`make generate-screen-1080p wasm-projections`, then open
`/src.wasm/examples/screen-1080p-three.html`. The exact Three.js browser module
is vendored under its MIT license so the example and smoke test remain offline.

The Node example is directly runnable from the repository root:

```sh
make wasm-projections
node src.wasm/examples/slice-node.mjs ck-octant-7
node src.wasm/examples/slice-node.mjs myria-group-1
```

Both examples use `carrierGeometry({slice})` for ocean faces and
`projectGeometry(geojson, {slice})` for land. This is the same command-buffer
path consumed by SVG, Canvas, and the D3 stream adapter.
