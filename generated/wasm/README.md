# Cahill-Keyes WebAssembly renderer

This directory contains the production browser adapter and checked-in
WebAssembly build for cartofreako's C++20 Cahill-Keyes projection.
`cahill-keyes-web.cc` exports a variable-size 2:1 projection through Embind.
The browser can project individual geographic coordinates and ask the same
C++ object to generate a complete SVG base map.

The generated SVG contains eight ocean faces, seam-safe ten-degree
graticules, and projected Natural Earth land. It is returned as a string and
loaded through a browser Blob URL; no pre-projected SVG or raster is used.

Build and test it from the repository root:

```sh
make wasm-cahill-keyes
make check-wasm-cahill-keyes
```

The build writes these artifacts in place to `generated/wasm/`:

```text
cartofreako-cahill-keyes.mjs
cartofreako-cahill-keyes.wasm
```

They remain beside the inputs and test harness:

```text
cahill-keyes-web.cc
cartofreako-cahill-keyes-land-110m.geojson
cahill-keyes-smoke.mjs
```

The generated `.mjs` loader and `.wasm` binary are stored in the repository
alongside their adapter, smoke test, and seam-prepared geographic input. Run
the build target again after changing the adapter or projection headers.

## Geographic source and projection seams

`cartofreako-cahill-keyes-land-110m.geojson` derives from Natural Earth's
public-domain `ne_110m_land` physical-vector release. The downloaded source
archive used here has SHA-256:

```text
1926c621afd6ac67c3f36639bb1236134a48d82226dc675d3e3df53d02d2a3de
```

Source URL:

```text
https://naciscdn.org/naturalearth/110m/physical/ne_110m_land.zip
```

Before export, GDAL clips the geographic polygons at the Cahill-Keyes cut
meridians `-111`, `-21`, `69`, and `159` degrees. That preprocessing is not a
projection: coordinates remain WGS 84 longitude/latitude. It prevents an SVG
fill from closing across an interrupted-octant seam. All planar coordinates
in the displayed map are still computed at runtime by
`ckproj::meridians_to_point_2d()` inside WASM.

Each clipped feature carries a zero-based `ck_band` property. GDAL can emit a
vertex exactly on a band's eastern cut, while the public point projection
assigns that exact longitude to the next face. Before projecting land, the
WASM adapter uses `ck_band` to bias such an eastern vertex west by `1e-7`
degrees. This preserves the feature's intended face and prevents a false
closing chord through Antarctica. The smoke test also measures consecutive
projected land segments and rejects any segment at least one quarter of the
map width.

The native forward construction derives from `MegamapMaker-prep9.pl` by Mary
Jo Graça and Gene Keyes. Its non-commercial attribution terms are recorded in
`src/cart0freak0-cahill-keyes.h`; commercial users should contact Gene Keyes.
