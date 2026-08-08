# Bathymetry Hamonshū generation implementation notes

[Documentation index](../index.md) ·
[Generation guide](generation.md) ·
[Generation methods](generation-methods.md) ·
[Bathymetry Roulette](bathymetry-roulette-implementation-notes.md) ·
[Natural Earth data](natural-earth-10m-physical-vectors.md)

## Outcome

`bathymetry-hamonshu` is a separate standard art-generation pass. It does not
replace or alias `bathymetry-roulette`. Both use the same twelve nested Natural
Earth depth thresholds, explicit overlapping projected-page cells, 24
jittered Voronoi regions, original bathymetry blue ramp, 30% graphic opacity,
shallow-to-deep paint order, and six production projections. The form engine
is different: this pass calls Izzi's `a60-svg-curves-hamonshu.h` instead of
`a60-svg-curves-roulette.h`.

Izzi supplies a source-indexed 153-entry procedural catalogue derived from
Mori Yūzan's 1903 *Hamonshū*, volume 2. Cartofreako owns the depth mapping,
field layout, geographic clipping, color, metadata, layer assembly, and
artifacts. The Smithsonian Libraries digitization is CC0; Natural Earth is
public domain. Izzi's descriptive English motif names identify visual forms
and are not translations of historical captions.

## Depth encoding

Hamonshū paths are line constructions, so this pass does not invent a roulette
`d/r` equivalent or fill open polylines into arbitrary polygons. Instead,
depth strictly increases two native Izzi parameters: line/constituent density
and curvature. Independently of those art experiments, the pass restores the
same shallow-to-deep blue-hue variation as the original Natural Earth
bathymetry scheme. Color is therefore a redundant third cue. Every line uses
its depth band's blue at 30% opacity.

| Natural Earth depth | Density | Curvature | Blue RGB |
| ---: | ---: | ---: | --- |
| 0 m | 0.55 | 0.30 | `190,219,235` |
| -200 m | 0.65 | 0.42 | `169,207,229` |
| -1,000 m | 0.75 | 0.56 | `146,194,221` |
| -2,000 m | 0.88 | 0.72 | `122,178,211` |
| -3,000 m | 1.02 | 0.90 | `99,161,201` |
| -4,000 m | 1.18 | 1.10 | `76,142,190` |
| -5,000 m | 1.35 | 1.35 | `58,124,176` |
| -6,000 m | 1.55 | 1.62 | `45,107,160` |
| -7,000 m | 1.78 | 1.95 | `35,91,143` |
| -8,000 m | 2.05 | 2.30 | `27,76,125` |
| -9,000 m | 2.35 | 2.75 | `20,62,107` |
| -10,000 m | 2.70 | 3.25 | `15,49,88` |

All values stay inside Izzi's validated density range 0.25–4.0 and curvature
range 0.20–4.0. Each constituent curve uses 24 relative samples. The values
are categorical rendering parameters attached to Natural Earth thresholds;
they are not physical models of wave energy, pressure, or current speed.

## Source motifs and variation

Twelve entries from Izzi's curated explorer provide the spatial vocabulary:

| Illustrated page / motif | Descriptive source ID |
| --- | --- |
| 001/01 | `nested-current-scrolls` |
| 002/01 | `braided-ribbon-currents` |
| 003/01 | `sparse-crest-silhouettes` |
| 003/02 | `interlaced-ripple-crests` |
| 006/02 | `sweeping-trough` |
| 009/01 | `layered-shoal-contours` |
| 017/03 | `fan-tailed-current` |
| 020/04 | `curling-current-and-droplets` |
| 023/02 | `ornamental-scroll-current` |
| 039/02 | `spray-tailed-curl` |
| 040/01 | `layered-eddy-channels` |
| 046–047/02 | `continuous-looping-current` |

The decorative page-51 endpaper in Izzi's thirteen-row curated explorer is
intentionally excluded. Every retained entry directly describes water,
current, crest, ripple, trough, channel, or spray.

The layout uses the same 1.10-unit cells and 2.15-unit base diameter as the
revised roulette pass. Motif boxes vary from 0.74 to 1.36 of that diameter;
phase spans one turn, small rotations stay within ±1/24 turn, alternating
motifs reflect, centers shift by at most 0.22 cells, and alternating rows
stagger by half a cell. Even the smallest box overlaps adjacent cells.
Linework is serialized explicitly rather than emitted through an SVG
`<pattern>` or `<use>` reference.

## Voronoi grouping, clipping, and layers

Twenty-four deterministic sites form a jittered 6-by-4 grid in projected page
space. Each field-cell center selects its nearest site. Site-to-motif mapping
rotates by depth; at every depth each of the twelve motifs owns exactly two
Voronoi regions. This creates broad neighborhoods of related line form while
retaining local phase, reflection, and overlap.

The generated motif paths are not hard-clipped at the planar Voronoi boundary.
They may overlap neighboring regions, which softens the group transition and
permits intentional interference and moiré. Each path is clipped only by its
Natural Earth depth polygon. The generator paints nested thresholds shallow to
deep; before drawing each field it paints the common opaque pale ground through
that threshold. Deeper thresholds therefore replace shallower artwork and
produce exclusive visible bands without polygon differences.

```text
bathymetry-hamonshu-metadata
defs
  12 bathymetry-hamonshu-clip-* clip paths
bathymetry-hamonshu
  bathymetry-0m
    bathymetry-0m-hamonshu-ground
    12 bathymetry-0m-hamonshu-variation-* groups
  bathymetry-200m
  ...
  bathymetry-10000m
bathymetry-hamonshu-key
```

Each variation path records the Izzi source ID, depth density and curvature,
box factor, phase, rotation, reflection, offsets, two Voronoi site numbers,
instance count, stroke paint, and opacity. Root metadata records source,
projection, field geometry, nearest-site policy, absence of hard Voronoi
clipping, blue-ramp contract, accepted moiré, and exact cell counts.
Cahill–Keyes contains 1,269 cells per depth and 15,228 motif instances.

## Commands and standard-pass behavior

Generate the six layered SVGs or all SVG/PDF/PNG artifacts with:

```sh
make generate-bathymetry-hamonshu
make generate-bathymetry-hamonshu-artifacts
```

One projection uses
`make generate-bathymetry-hamonshu-PROJECTION`; for example:

```sh
make generate-bathymetry-hamonshu-cahill-keyes
```

The pass is included in `make all`, `assets-single`, `assets-resilient`, the
Cahill–Keyes snapshot input set, and generation-profile `"all"`. Profile
selectors accept the canonical `bathymetry-hamonshu` and the convenience
aliases `hamonshu` and `art-agua-hamonshu`.

The Stage 13 focused review artifacts are generated locally at
`assets.generated/cahill-keyes/svg/bathymetry-hamonshu-ck-44-22.svg` and
`assets.generated/cahill-keyes/png/bathymetry-hamonshu-ck-44-22.png`. They are deliberately
not linked from GitHub Pages until a completed static-asset release publishes
them to the immutable S3 tree.

## Verification and limits

Focused tests validate the twelve monotonic depth parameter pairs, Izzi API
bounds, twelve unique source IDs and path results, 24-site/equal-two-region
distribution, overlap, identifiers, and exact 30% opacity. Each generator
reopens its SVG and verifies the projection view box, metadata and counts,
twelve geographic clips, 144 variation groups, depth paint order, source IDs,
ground/clip references, hole preservation, finite path data, configured font,
absence of SVG pattern definitions, and presence of all twelve Natural Earth
blues.

The fields encode categorical depth thresholds, not continuous bathymetry.
Hamonshū motif, density, curl, line direction, and moiré do not encode ocean
current, swell, hazard, geology, uncertainty, or measured bottom roughness.
Because every motif instance is serialized, large SVG/PDF files and substantial
Inkscape export memory are accepted characteristics of this art pass.
