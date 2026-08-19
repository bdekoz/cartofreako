# Bathymetry Roulette generation implementation notes

[Documentation index](../../../../index.md) ·
[Generation guide](../../getting-started/generation.md) ·
[Generation methods](../../getting-started/generation-methods.md) ·
[Natural Earth data](../../data/natural-earth.md)

## Outcome and feasibility

Stage 4.5 is implemented as the projection-aware `bathymetry-roulette` pass.
It combines the original twelve-color Natural Earth blue ramp with a second,
independent form encoding: a progressively more complex Izzi roulette family
for each depth threshold. Every roulette is an even-odd-filled form at 30%
opacity. Each family expands into an explicit overlapping field whose nearby
cells share a deterministic projected-page Voronoi assignment rather than
displaying one canonical symbol on a uniform grid. The pass writes one
layered SVG for every production projection and can export the corresponding
PDF and PNG review artifacts.

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
before the path closes. The 0 m form starts exactly at `d/r = 1`, the cycloid
boundary; no form is below it. Depth alone raises `d/r` strictly to 5.00.
Every level uses even-odd fill and the matching color from Natural Earth's
ordinary bathymetry scheme.

| Natural Earth depth | Roulette | `R:r` | `d/r` | Blue RGB | Closure turns |
| ---: | --- | ---: | ---: | --- | ---: |
| 0 m | Epitrochoid | 1:1 | 1.00 | `190,219,235` | 1 |
| -200 m | Epitrochoid | 1:1 | 1.12 | `169,207,229` | 1 |
| -1,000 m | Epitrochoid | 1:1 | 1.25 | `146,194,221` | 1 |
| -2,000 m | Epitrochoid | 2:1 | 1.40 | `122,178,211` | 1 |
| -3,000 m | Epitrochoid | 2:1 | 1.60 | `99,161,201` | 1 |
| -4,000 m | Epitrochoid | 3:1 | 1.85 | `76,142,190` | 1 |
| -5,000 m | Epitrochoid | 3:1 | 2.15 | `58,124,176` | 1 |
| -6,000 m | Hypotrochoid | 4:1 | 2.50 | `45,107,160` | 1 |
| -7,000 m | Epitrochoid | 5:2 | 2.90 | `35,91,143` | 2 |
| -8,000 m | Hypotrochoid | 5:2 | 3.40 | `27,76,125` | 2 |
| -9,000 m | Hypotrochoid | 11:7 | 4.10 | `20,62,107` | 7 |
| -10,000 m | Epitrochoid | 11:7 | 5.00 | `15,49,88` | 7 |

Every turn has 128 line samples. The table describes the representative base
curve shown in the key; it is not a single symbol stamped unchanged across the
map. Each base curve expands into twelve deterministic layout variations:

- diameter factors range from 0.74 to 1.36 around a 2.15-unit base diameter;
- phases step from 0 through 11/12 of a turn;
- centers move by up to 0.22 cells in both axes; and
- alternating rows are offset by half a cell.

Point distance is deliberately not a layout variation: all cells at one depth
retain that depth's exact `d/r`. Cell spacing is 1.10 page units. Even the
smallest 1.591-unit curve is wider than that spacing, so neighboring roulettes
overlap and their clipped forms read as a continuous field instead of a
regular icon grid. Fill and stroke both use the depth blue at exactly 30%
opacity; stroke width begins at 0.014 units and varies slightly between layout
families. The common opaque ground is `rgb(239,245,243)`. Thus shape, density
from overlap, and the restored blue ramp all communicate depth without making
any one cue carry the interpretation alone.

## Layering and clipping model

The generator turns each already projected Natural Earth depth geometry into
an SVG `clipPath`. For each depth it then paints an opaque full-frame ground
through that clip and generates an explicit staggered page-space mosaic.
Twenty-four deterministically jittered sites form a 6-by-4 projected-page
Voronoi partition. Every field-cell center is assigned to its nearest site;
each site selects one of twelve layout variations, so each variation owns
exactly two regions at every depth. Neighboring cells consequently share
diameter, phase, and offset behavior over broad areas. The roulette curves are
not hard-clipped to the planar Voronoi boundaries: their overlapping edges can
cross a region boundary and produce softer transitions and moiré. Natural
Earth depth geometry remains the only geographic clip. All coordinates are
written into the SVG and collected into twelve semantic variation groups.
There is no SVG `<pattern>` element or reused canonical curve in the field.

This follows the compositional model of the historical `ocean` pass: establish
a clipped geographic region, distribute related motif variations through a
mosaic, paint the region ground, and draw the varied motif linework above it.
Unlike that pass's geographic 5°/10° cells, the roulette mosaic is registered
in projected page space. Curves therefore keep a consistent physical scale
across projections while their offsets, sizes, phases, and Voronoi
neighborhoods break the old symbol grid. The depth's `d/r` does not vary
spatially.

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
subpaths and records its instance count, diameter factor, exact depth `d/r`,
phase, two center offsets, and its two Voronoi site numbers. The root metadata
records the 6-by-4 nearest-site assignment, absence of hard Voronoi clipping,
page-space cell size, base diameter, row stagger, variation count, 30% opacity,
minimum `d/r`, accepted-moiré policy, per-depth cell count, and total
curve-instance count. For example, Cahill-Keyes contains 1,269 cells per depth
and 15,228 explicit curve instances overall. The visible four-column key shows
the representative base curve and blue for every depth with its abbreviated
kind, radius ratio, and `d/r` value.

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

The links below are immutable v14 release references. They show the blue,
filled, Voronoi-grouped implementation documented above; the older v12
references retained the pre-Stage-13 monochrome algorithm. Local focused
review uses `assets.generated/cahill-keyes/png/bathymetry-roulette-ck-44-22.png`.

| Projection | Preview |
| --- | --- |
| Cahill-Keyes | [`bathymetry-roulette-ck-44-22.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/cahill-keyes/full/bathymetry-roulette-ck-44-22.png) |
| AuthaGraph | [`bathymetry-roulette-authagraph-44-19.052559.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/authagraph/full/bathymetry-roulette-authagraph-44-19.052559.png) |
| Dymaxion | [`bathymetry-roulette-dymaxion-44-20.78461.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/dymaxion/full/bathymetry-roulette-dymaxion-44-20.78461.png) |
| Myriahedral | [`bathymetry-roulette-myriahedral-44-24.75.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/myriahedral/full/bathymetry-roulette-myriahedral-44-24.75.png) |
| Star-X | [`bathymetry-roulette-star-x-34-44.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/star-x/full/bathymetry-roulette-star-x-34-44.png) |
| Voronoi | [`bathymetry-roulette-voronoi-44-22.916667.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/voronoi/full/bathymetry-roulette-voronoi-44-22.916667.png) |

The pass is also selectable through `generation-profile.json` as
`bathymetry-roulette` or either compatibility alias.

## Verification and interpretation limits

`make check` validates the twelve-entry depth catalogue and twelve-entry field
variation catalogue, `d/r >= 1`, strict depth growth, all-filled paint rule,
unique closed base and varied paths, equal 24-site distribution, unique IDs,
sample counts, exact 30% opacity, and one-, two-, and seven-turn closure
periods. Each generator then reopens its SVG and checks the projection view
box, Voronoi-field metadata and counts, twelve clip paths, 144 variation
groups, depth paint order, ground/clip references, hole-preserving clip rules,
sufficient projected geometry, finite output, absence of SVG pattern
definitions, and presence of every original Natural Earth bathymetry blue.

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
