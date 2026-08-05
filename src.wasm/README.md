# WebAssembly renderers

[Documentation index](../index.md) ·
[Myriahedral implementation notes](../docs/myriahedral-implementation-notes.md#webassembly-land-and-ocean-option) ·
[Illustrative Myriahedral overlay](../docs/web-workflow.md)

This directory contains production Emscripten/Embind adapters for the C++20
Cahill-Keyes and Myriahedral projections. Both expose a variable-size forward
projection and `generateBaseMapSvg(landGeoJson)` to JavaScript.

| Adapter | Frame | Generated SVG layers | Build target |
| --- | --- | --- | --- |
| [`cahill-keyes-web.cc`](cahill-keyes-web.cc) | `2:1` | ocean faces, graticules, land | `make check-wasm-cahill-keyes` |
| [`cahill-myriahedral.cc`](cahill-myriahedral.cc) | `16:9` | **ocean and land only** | `make check-wasm-cahill-myriahedral` |

The Myriahedral choice is intentionally a base-map option. It does not
compute or serialize graticules, bathymetry, rivers, lakes, ice, minor
islands, reefs, playas, or coastlines as separate layers. Its SVG has exactly
these two groups, in paint order:

```xml
<g id="ocean">...</g>
<g id="land">...</g>
```

## Build and test

From the repository root:

```sh
make wasm-cahill-keyes
make check-wasm-cahill-keyes
make wasm-cahill-myriahedral
make check-wasm-cahill-myriahedral
```

The targets write ES-module loaders and their companion binaries beside the
sources:

```text
cartofreako-cahill-keyes.mjs
cartofreako-cahill-keyes.wasm
cartofreako-cahill-myriahedral.mjs
cartofreako-cahill-myriahedral.wasm
```

The Node smoke tests check reference coordinates, frame scaling, invalid
input, finite SVG output, and seam safety. The Myriahedral test additionally
requires all 5,120 terminal ocean faces, exactly two SVG groups, no optional
physical layers, and land segments short enough to rule out cut-spanning
closing chords.

## Myriahedral JavaScript API

```js
import createModule from './cartofreako-cahill-myriahedral.mjs';

const module = await createModule();
const response = await fetch('./cartofreako-cahill-keyes-land-110m.geojson');
const land = await response.json();

const projection = new module.MyriahedralProjection(1920, 1080);
const newYork = projection.project(40.7128, -74.0060);
const svg = projection.generateBaseMapSvg(land);

projection.delete();
```

Any finite, positive `16:9` frame is valid. The SVG root records
`data-layers="ocean land"` and remains transparent outside the unfolded net.
The ocean path is assembled directly from the registered planar triangles in
the selected fixed layout.

### Filled-land cuts

The shared geographic input was originally clipped into five non-wrapping
Cahill-Keyes longitude bands. Those pieces still form the complete land
union, and the Myriahedral adapter ignores their `ck_band` metadata.

Closing those polygons after projecting their vertices directly would draw
false fills across thousands of Myriahedral cuts. The WASM adapter instead
uses the same strategy as the native filled-area generator:

1. clip each geographic ring to a five-degree longitude/latitude cell;
2. segment cell edges at no more than half-degree intervals;
3. collect every terminal face sampled by that cell;
4. map the cell geometry through each face's affine transform; and
5. clip the result to that face's exact planar triangle.

The output pieces share an `evenodd` land path. A same-color hairline stroke
covers antialiasing cracks between retained neighboring pieces without
connecting geometric cuts. This processing is implemented in C++ and needs
no GDAL, GEOS, S2, Boost, or virtual filesystem in the browser.

## Cahill-Keyes geographic source

[`cartofreako-cahill-keyes-land-110m.geojson`](cartofreako-cahill-keyes-land-110m.geojson)
derives from Natural Earth's public-domain `ne_110m_land` physical-vector
release. The downloaded source archive used here has SHA-256:

```text
1926c621afd6ac67c3f36639bb1236134a48d82226dc675d3e3df53d02d2a3de
```

Source URL:

```text
https://naciscdn.org/naturalearth/110m/physical/ne_110m_land.zip
```

Before export, GDAL clipped the geographic polygons at Cahill-Keyes cut
meridians `-111`, `-21`, `69`, and `159` degrees. Coordinates remain WGS 84
longitude/latitude. Each polygon feature carries a zero-based `ck_band`
property; the Cahill-Keyes adapter uses it to bias an exact eastern-cut vertex
west by `1e-7` degrees and prevent a false Antarctica chord.

The native Cahill-Keyes forward construction derives from
`MegamapMaker-prep9.pl` by Mary Jo Graça and Gene Keyes. Its non-commercial
attribution terms are recorded in
[`cart0freak0-cahill-keyes.h`](../src.projections/cart0freak0-cahill-keyes.h);
commercial users should contact Gene Keyes.

The [illustrative Myriahedral workflow](../docs/web-workflow.md) remains useful
when a page needs a raster-backed graticule and city-anchor overlay. It is a
separate example, not the land-and-ocean production base-map adapter above.

---

[Documentation index](../index.md) ·
[Myriahedral implementation notes](../docs/myriahedral-implementation-notes.md#webassembly-land-and-ocean-option) ·
[Illustrative Myriahedral overlay](../docs/web-workflow.md)
