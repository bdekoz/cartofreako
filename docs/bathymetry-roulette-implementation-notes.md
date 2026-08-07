# Bathymetry Roulette generation implementation notes

[Documentation index](../index.md) ·
[Generation guide](generation.md) ·
[Generation methods](generation-methods.md) ·
[Natural Earth data](natural-earth-10m-physical-vectors.md)

## Outcome and feasibility

Stage 4.5 is implemented as the projection-aware `bathymetry-roulette` pass.
It replaces the ordinary twelve-color bathymetry ramp with one pale ground
and one dark ink, assigning a progressively more variable and complex Izzi
roulette family to each Natural Earth depth threshold. Each family is expanded
into an explicit, overlapping field of varied curves rather than displaying
one canonical roulette as a repeated symbol. The pass writes one layered SVG
for every production projection and can export the corresponding PDF and PNG
review artifacts.

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

Each row is the representative base style for one depth family. `R:r` is the
fixed-to-rolling radius ratio, `d/r` is point distance divided by rolling
radius, and the closure period is the number of rolling-circle turns sampled
before the path closes. The base point-distance ratio increases strictly with
depth; the final four levels change from outline to even-odd fill.

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

Every turn has 128 line samples. The table describes the representative base
curve shown in the key; it is not a single symbol stamped unchanged across the
map. Each base curve expands into twelve deterministic field variations:

- diameter factors range from 0.74 to 1.36 around a 2.15-unit base diameter;
- point-distance factors range from 0.960 to 1.040, preserving the strict
  shallow-to-deep ordering of the base families;
- phases step from 0 through 11/12 of a turn;
- centers move by up to 0.22 cells in both axes; and
- alternating rows are offset by half a cell.

Cell spacing is 1.10 page units. Even the smallest 1.591-unit curve is wider
than that spacing, so neighboring roulettes overlap and their clipped arcs
read as a continuous pattern field instead of a regular icon grid. Stroke
width begins at 0.014 units and varies slightly between field families. The
final four depth levels retain low-opacity even-odd fills as well as their
outlines. The common ground is `rgb(239,245,243)` and the common ink is
`rgb(23,63,72)`; no ordinary depth-ramp color appears in the output.

## Layering and clipping model

The generator turns each already projected Natural Earth depth geometry into
an SVG `clipPath`. For each depth it then paints an opaque full-frame ground
through that clip and generates an explicit staggered page-space mosaic. A
stable two-dimensional mix assigns every cell to one of the twelve variations;
all curve coordinates are written into the SVG and collected into twelve
semantic variation groups. There is no SVG `<pattern>` element or reused
canonical curve in the map field.

This follows the compositional model of the historical `ocean` pass: establish
a clipped geographic region, distribute related motif variations through a
mosaic, paint the region ground, and draw the varied motif linework above it.
Unlike that pass's geographic 5°/10° cells, the roulette mosaic is registered
in projected page space. Curves therefore keep a consistent physical scale
across projections while their offsets, sizes, phases, and point distances
break the old symbol grid.

The twelve depth groups paint shallow to deep, matching the source nesting
order. Because each depth paints the same opaque ground before its linework, a
deeper threshold replaces the shallower field beneath it and the visible result
is a set of exclusive bands without an expensive polygon-difference pass.
Projection-safe geographic clipping still comes from the shared Natural Earth
pipeline, including even-odd polygon and hole behavior. Star-X retains the same
unfolded-ocean topology used by the water pass.

The SVG layer contract is:

```text
bathymetry-roulette-metadata
defs
  12 bathymetry-roulette-clip-* clip paths
bathymetry-roulette
  bathymetry-0m
    bathymetry-0m-roulette-ground
    12 bathymetry-0m-roulette-variation-* groups
  bathymetry-200m
  ...
  bathymetry-10000m
bathymetry-roulette-key
```

Every variation group contains one explicit path with all assigned cell
subpaths and records its instance count, diameter factor, point-distance
factor, phase, and two center offsets. The root metadata records field mode,
page-space cell size, base diameter, row stagger, variation count, per-depth
cell count, and total curve-instance count. For example, Cahill-Keyes contains
1,269 cells per depth and 15,228 explicit curve instances overall. The visible
four-column key shows the representative base curve for every depth with its
abbreviated kind, radius ratio, and `d/r` value.

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
| Cahill-Keyes | [`bathymetry-roulette-ck-44-22.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/png/bathymetry-roulette-ck-44-22.png) |
| AuthaGraph | [`bathymetry-roulette-authagraph-44-19.052559.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/png/bathymetry-roulette-authagraph-44-19.052559.png) |
| Dymaxion | [`bathymetry-roulette-dymaxion-44-20.78461.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/png/bathymetry-roulette-dymaxion-44-20.78461.png) |
| Myriahedral | [`bathymetry-roulette-myriahedral-44-24.75.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/png/bathymetry-roulette-myriahedral-44-24.75.png) |
| Star-X | [`bathymetry-roulette-star-x-34-44.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/png/bathymetry-roulette-star-x-34-44.png) |
| Voronoi | [`bathymetry-roulette-voronoi-44-22.916667.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/png/bathymetry-roulette-voronoi-44-22.916667.png) |

The pass is also selectable through `generation-profile.json` as
`bathymetry-roulette` or either compatibility alias.

## Verification and interpretation limits

`make check` validates the twelve-entry depth catalogue and twelve-entry field
variation catalogue, ordering, strict growth in base point variation,
outline-to-fill transition, unique closed base and varied paths, unique IDs,
sample counts, and one-, two-, and seven-turn closure periods. Each generator
then reopens its SVG and checks the projection view box, explicit-mosaic
metadata and counts, twelve clip paths, 144 variation groups, depth paint
order, ground/clip references, hole-preserving clip rules, sufficient projected
geometry, finite output, absence of SVG pattern definitions, and absence of
the ordinary bathymetry palette.

The explicit variation paths are intentionally large XML nodes. External
libxml2 validation should therefore use `xmllint --huge --noout`; ordinary
mode may stop at its node-size guard even though the document is well formed.

The fields encode categorical Natural Earth thresholds, not continuous
seafloor elevation or uncertainty. Roulette shape does not imply current,
direction, geology, or measured roughness. Curves are intentionally clipped
into partial, overlapping arcs at coastlines and depth boundaries. Dense fills,
interference between adjacent curves, and moiré at some display or export
scales are intentional properties of the confirmed artwork; they should not be
read as additional bathymetric data. Every field instance is serialized rather
than referenced, so SVG/PDF size and rendering cost are deliberately not
bounded as part of this generative pass.
