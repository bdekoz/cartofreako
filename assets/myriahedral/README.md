# Myriahedral reconstruction artifacts

These files preserve the temporary inputs, generators, selected topology, and
verification outputs used to implement
`src/cart0freak0-myriahedral.h`. They were copied byte-for-byte from
`/tmp/myriaworld.gjlN58` on 2026-08-01.

## Repository location

The reconstruction package was staged during development under
`assets/adhoc/myriahedral` and now lives permanently in
`assets/myriahedral`. Documentation, tooling, and future provenance references
should use the permanent path. The production base raster remains
`assets/myriahedral/black-white-downsampled.png`, alongside these supporting
artifacts.

## Selected configuration

Grid entry `37` in `boost-grid-configs.txt` records:

```text
wlat = 0.5
wlon = 0.1
clat = -60
clon = -65
```

The grid was generated after Gaussian smoothing with `sigma = 0.7`. The
selected planar registration applies a final `335` degree rotation. The
rotation is used by the projection header and landmark scoring; it is not
baked into `boost-grid-37.tree` or the unrotated coordinates in
`boost-grid-37.npz`.

## Files

| File | Role |
| --- | --- |
| `exact-fractions.txt` | Exact land fraction, spherical area, centroid, and special-country bits for each of 5120 faces |
| `exact_fraction.cc` | S2-based program that generated the exact face data |
| `export_countries.py` | Historical Natural Earth polygon exporter used before exact face intersection |
| `boost_tree.cc` | Boost.Graph smoothing, weighting, Prim-tree, and grid generator |
| `boost-grid-configs.txt` | Parameter map for the generated candidate grid |
| `boost-grid-37.tree` | Selected parent tree; direct source of the compact hexadecimal data in the production header |
| `reconstruct.py` | Independent mesh topology, unfolding, projection, and rendering implementation |
| `render_grid.py` | Converts generated tree files into independent planar `.npz` layouts |
| `boost-grid-37.npz` | Selected unrotated planar layout used to verify raw bounds and representative vertices |
| `landmark_scores.py` | Geographic-anchor registration scorer |
| `landmark-output.txt` | Scoring output; grid 37 selects the 335-degree orientation |
| `grid37-land.png` | Final low-resolution diagnostic rendering of the selected layout |
| `SHA256SUMS` | Digests for every preserved artifact except this manifest |

The scripts intentionally retain the absolute `/tmp/myriaworld.gjlN58` paths
with which they were run. Adjust those paths before rerunning them elsewhere.
Large dependency trees, compiler outputs, the cloned upstream repository,
historical Natural Earth source files, and rejected candidate layouts are not
duplicated here. Their derived data needed by the final implementation is
captured by `exact-fractions.txt`, the selected tree, and the planar baseline.
