# Bathymetry Roulette generation implementation notes

[Documentation index](../index.md) ·
[Generation guide](generation.md) ·
[Generation methods](generation-methods.md) ·
[Natural Earth data](natural-earth-10m-physical-vectors.md)

## Outcome and feasibility

Stage 4.5 is implemented as the projection-aware `bathymetry-roulette` pass.
It replaces the ordinary twelve-color bathymetry ramp with one pale ground
and one dark ink, assigning a progressively more variable and complex Izzi
roulette to each Natural Earth depth threshold. The pass writes one layered
SVG for every production projection and can export the corresponding PDF and
PNG review artifacts.

The design is feasible without another geographic dataset. The existing
Natural Earth renderer already loads the twelve nested 1:10m bathymetry
polygons, repairs and clips them at projection cuts, preserves holes, and
projects them on all six map frames. Izzi's
`a60-svg-curves-roulette.h`, explored by
`izzi/examples/curves-roulette.cc`, supplies deterministic closed
epitrochoid and hypotrochoid paths for the visual vocabulary.

The canonical public name is `bathymetry-roulette`. Generation profiles also
accept the requested `bathymetry-rolette` spelling and the earlier ledger
name `art-agua-roulette` as aliases. Output filenames always use the
canonical spelling.

## Confirmed depth catalogue

Each row is a complete style decision. `R:r` is the fixed-to-rolling radius
ratio, `d/r` is point distance divided by rolling radius, and the closure
period is the number of rolling-circle turns sampled before the path closes.
The point-distance ratio increases strictly with depth; the final four
levels change from outline to even-odd fill.

| Natural Earth depth | Roulette | `R:r` | `d/r` | Paint | Closure turns |
| ---: | --- | ---: | ---: | --- | ---: |
| 0 m | Epitrochoid | 1:1 | 0.25 | Outline | 1 |
| -200 m | Epitrochoid | 1:1 | 0.35 | Outline | 1 |
| -1,000 m | Epitrochoid | 1:1 | 0.50 | Outline | 1 |
| -2,000 m | Epitrochoid | 2:1 | 0.65 | Outline | 1 |
| -3,000 m | Epitrochoid | 2:1 | 0.75 | Outline | 1 |
| -4,000 m | Epitrochoid | 3:1 | 0.90 | Outline | 1 |
| -5,000 m | Epitrochoid | 3:1 | 1.00 | Outline | 1 |
| -6,000 m | Hypotrochoid | 4:1 | 1.10 | Outline | 1 |
| -7,000 m | Epitrochoid | 5:2 | 1.25 | Even-odd fill | 2 |
| -8,000 m | Hypotrochoid | 5:2 | 1.50 | Even-odd fill | 2 |
| -9,000 m | Hypotrochoid | 11:7 | 2.00 | Even-odd fill | 7 |
| -10,000 m | Epitrochoid | 11:7 | 3.00 | Even-odd fill | 7 |

Every turn has 128 line samples. Motifs occupy a 1.20-unit square
`userSpaceOnUse` tile with 0.12 units of padding and a 0.018-unit stroke. The
common ground is `rgb(239,245,243)` and the common ink is
`rgb(23,63,72)`; no ordinary depth-ramp color appears in the output.

## Layering and clipping model

The generator turns each already projected Natural Earth depth geometry into
an SVG `clipPath` and pairs it with one globally registered page-space
pattern. A full-frame pattern rectangle is clipped to that threshold. The
twelve rectangles paint shallow to deep, matching the source nesting order.
Because every pattern tile has the same opaque ground, a deeper threshold
replaces the shallower motif beneath it and the visible result is a set of
exclusive bands without an expensive polygon-difference pass.

Page-space pattern registration is deliberate. Motifs keep a consistent
physical size and alignment across the map instead of stretching with source
geography or individual polygons. Projection-safe geographic clipping still
comes from the shared Natural Earth pipeline, including even-odd polygon and
hole behavior. Star-X retains the same unfolded-ocean topology used by the
water pass.

The SVG layer contract is:

```text
bathymetry-roulette-metadata
defs
  12 bathymetry-roulette-clip-* clip paths
  12 bathymetry-roulette-pattern-* patterns
bathymetry-roulette
  bathymetry-0m
  bathymetry-200m
  ...
  bathymetry-10000m
bathymetry-roulette-key
```

The visible four-column key repeats every curve with its depth, abbreviated
roulette kind, radius ratio, and `d/r` value. Pattern definitions and depth
groups carry the same parameters as machine-readable SVG attributes and
titles.

## Products and commands

Generate all six layered SVGs with:

```sh
make generate-bathymetry-roulette
```

`generate-bathymetry-roulette-projections` is an equivalent family target.
Use `generate-bathymetry-roulette-PROJECTION` for one map, or export every
SVG, PDF, and 3840-pixel-long-side PNG with:

```sh
make generate-bathymetry-roulette-artifacts
```

| Projection | Preview |
| --- | --- |
| Cahill-Keyes | [`bathymetry-roulette-ck-44-22.png`](../assets.generated/png/bathymetry-roulette-ck-44-22.png) |
| AuthaGraph | [`bathymetry-roulette-authagraph-44-19.052559.png`](../assets.generated/png/bathymetry-roulette-authagraph-44-19.052559.png) |
| Dymaxion | [`bathymetry-roulette-dymaxion-44-20.78461.png`](../assets.generated/png/bathymetry-roulette-dymaxion-44-20.78461.png) |
| Myriahedral | [`bathymetry-roulette-myriahedral-44-24.75.png`](../assets.generated/png/bathymetry-roulette-myriahedral-44-24.75.png) |
| Star-X | [`bathymetry-roulette-star-x-34-44.png`](../assets.generated/png/bathymetry-roulette-star-x-34-44.png) |
| Voronoi | [`bathymetry-roulette-voronoi-44-22.916667.png`](../assets.generated/png/bathymetry-roulette-voronoi-44-22.916667.png) |

The pass is also selectable through `generation-profile.json` as
`bathymetry-roulette` or either compatibility alias.

## Verification and interpretation limits

`make check` validates the twelve-entry catalogue, ordering, strict growth in
point variation, outline-to-fill transition, unique closed paths and IDs,
sample counts, and one-, two-, and seven-turn closure periods. Each generator
then reopens its SVG and checks the projection view box, metadata, twelve
patterns and clip paths, depth paint order, references, hole-preserving clip
rules, sufficient projected geometry, finite output, and absence of the
ordinary bathymetry palette.

The patterns encode categorical Natural Earth thresholds, not continuous
seafloor elevation or uncertainty. Roulette shape does not imply current,
direction, geology, or measured roughness. Curves can be clipped into partial
motifs at coastlines and depth boundaries. Dense fills, interference between
adjacent patterns, and moiré at some display or export scales are intentional
properties of the confirmed artwork; they should not be read as additional
bathymetric data. The large SVGs also cost more to parse and render than a
flat color ramp.
