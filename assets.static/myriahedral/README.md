# Myriahedral reconstruction artifacts

These files preserve the temporary inputs, generators, selected topology, and
verification outputs used to implement
`src.projections/cart0freak0-myriahedral.h`. They were copied byte-for-byte from
`/tmp/myriaworld.gjlN58` on 2026-08-01.

## Repository location

The reconstruction package was staged in a temporary ad-hoc area during
development and now lives permanently in `assets.static/myriahedral`.
Documentation, tooling, and future provenance references should use the
permanent path. The production base raster remains
`assets.static/myriahedral/black-white-downsampled.png`, alongside these
supporting artifacts.

## Selected configuration

Grid entry `37` in `boost-grid-configs.txt` records:

```text
wlat = 0.5
wlon = 0.1
clat = -60
clon = -65
```

These are legacy option names, not semantic latitude/longitude labels. In
`boost_tree.cc`, `wlat` weights longitude distance, `wlon` weights latitude
distance, `clat` is the effective center longitude, and `clon` is the
effective center latitude. The selected effective center is consequently
`(-60, -65)` in `(longitude, latitude)` order.

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
| `reconstruct.py` | Historical independent reconstruction of the legacy mesh, affine/chord projection, and rendering lineage |
| `render_grid.py` | Converts generated tree files into independent planar `.npz` layouts |
| `boost-grid-37.npz` | Selected unrotated legacy planar baseline used during tree and registration reconstruction |
| `landmark_scores.py` | Geographic-anchor registration scorer |
| `landmark-output.txt` | Scoring output; grid 37 selects the 335-degree orientation |
| `grid37-land.png` | Final low-resolution diagnostic rendering of the selected layout |
| `perspective-configurations.json` | Machine-readable reference and five-perspective preprocessing, registration, digest, and artifact metadata |
| `SHA256SUMS` | Digests for every preserved artifact except this manifest |

The scripts intentionally retain the absolute `/tmp/myriaworld.gjlN58` paths
with which they were run. Adjust those paths before rerunning them elsewhere.
Large dependency trees, compiler outputs, the cloned upstream repository,
historical Natural Earth source files, and rejected candidate layouts are not
duplicated here. Their derived data needed by the final implementation is
captured by `exact-fractions.txt`, the selected tree, and the legacy planar
baseline.

The five exploratory trees are embedded under `src.generate/` and selected by
`myriahedral-perspective-generation.h`. They reuse the exact fractions and
historical weighting program recorded here; their complete parameters, raw
bounds, rotations, parent-data paths, and source-tree digests are recorded in
`perspective-configurations.json`.

## Numerical lineage and production divergence

The preserved scripts and `boost-grid-37.npz` reproduce the historical
`myriaworld` numerical lineage. They remain authoritative for preprocessing,
terminal-face numbering, the selected spanning tree, and landmark
registration. They are not the numerical oracle for the current C++ forward
projection.

A 2026-08-04 audit found that the legacy face-local transform was an
orthogonal chord-plane approximation rather than van Wijk's central gnomonic
mapping. It introduced a small false discontinuity across retained hinges.
The inherited seed-triangle formula also mixed two edge lengths, and its base
icosahedron constants were truncated. The production implementation now:

- derives and normalizes the regular-icosahedron vertices from the golden
  ratio while retaining face order;
- embeds the layout seed with a signed, length-preserving dot-product
  construction;
- maps points with widened central gnomonic barycentric coordinates; and
- uses containment-first widened predicates plus roundoff-bounded validation.

Consequently, current raw bounds and fixed geographic anchors intentionally
differ slightly from `boost-grid-37.npz` and the reference raster's generating
algorithm. Schema v2 of `perspective-configurations.json` records the current
bounds, distinguishes Prim root face `103` from layout seed face `0`, and names
the gnomonic method. The raster remains a subpixel registration and visual
reference, not proof of the forward formula.
