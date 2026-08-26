---
layout: default
title: Build and generated artifacts
---

# Build and generated artifacts

[Documentation index](../README.md) ·
[Source layout conventions](source_layout_conventions.md) ·
[Visual gallery](../gallery/README.md)

## Since the v13 generated-assets release

The gallery serves the selected image backend. Current source development
adds capabilities without rewriting the sealed v13 UCB AAO/S3 deposit. See
[the release notes](../releases/since-v13.md) for the full change list.

## Project and build

This repository contains native C++20 forward implementations of the
AuthaGraph, Cahill-Keyes, Dymaxion, Star-X, Myriahedral, and icosahedral
Voronoi projections, plus candidate-aware reverse projection for all six
families through runtime API 3. Star-X exposes its ordinary carrier and unified
Antarctic cap as separate components. All six accept variable-size
`a60::carto::frame` values while enforcing the aspect ratio required by the
selected geometry or source-canvas registration.

Before building, see [Prerequisites](prerequisites.md) for the compiler,
GNU Make, Alpha60, Izzi, H3, GDAL/GEOS, Natural Earth, Inkscape, and optional
WebAssembly requirements, or use the
[technical documentation hub](../README.md).

The repository is organized as described in the
[source layout conventions](source_layout_conventions.md). The build graph,
released artifact catalog, and resource metric classes follow below.

## Build

A bare `make` validates [`generation-profile.json`](../../../generation-profile.json)
and builds only its selected projection/pass SVG matrix. Preview the
normalized selection and targets with `make generation-plan`; see the
[generation methods](generation-methods.md) for schema details and the
generation-pass and Stage 7 decision records. The explicit `make all`
workflow below remains the complete release/review build.

Run all standalone projection checks with:

```sh
make check
```

Generate geometry, labeled graticules, both Natural Earth layer families,
all three timestamped astronomy products, both timestamped Orbital Technosphere
products, all 14 Stage 12 resource products, the Anthropocene observation and
temperature atlases for both 2025 and 2026, the cumulative network-swarm,
the network CDN site atlas, the default-rendered Network Fiber
union, Bathymetry Roulette, and
Bathymetry Hamonshū for
all six projections with:

```sh
make all
```

The 24 production whole-earth maps, 18 astronomy maps, 12 Orbital
Technosphere maps, 84 resources maps, 24 Anthropocene maps, six network-swarm
maps, six network CDN site maps, six Network Fiber maps, six
Network Groundstations maps, six
Bathymetry Roulette maps, six Bathymetry Hamonshū maps, five
exploratory Myriahedral water perspectives, 12 Cahill-Keyes enlargement
slices, and two Myriahedral face-group slices total 217 current standard
products. They are
organized first by projection beneath `assets.generated/`, then into `svg/`,
`pdf/`, `png/`, and `thumbnail/` directories. The 84 resource SVGs also
receive deterministic `.svg.gz` release archives. All 217 standard products have an Inkscape
PDF and PNG beside their projection peers. PNGs preserve the source aspect ratio and
have a longest side of 3840 pixels, the horizontal resolution of UHD 4K
video. Transparent SVG page regions are flattened against an opaque white
background. The standard graph also creates 33 480-pixel-wide thumbnails for
every whole-map projection, 198 total.
Review the complete all-projection release in the
[generated snapshot catalog](#generated-artifact-previews). The
targets `make generated-projections`, `make
generate-projections`, and `make make-generated` are equivalent aliases.

The credentialed, source-timed Cloud-atmosphere family is absent from a clean
checkout's `make all`. After a successful P-Tree/JAXA refresh and local H3
preparation, `generate-authorized-external` records `jaxa-ptree`; subsequent
configured `make all` runs include its SVG/PDF/PNG and thumbnail products. Direct family
targets remain available as `make generate-cloud-atmosphere` and
`make generate-cloud-atmosphere-artifacts`.

Every print frame preserves the projection's required ratio and has a largest
dimension of exactly 44 inches:

| Projection | Generated frame | Per-projection target |
| --- | ---: | --- |
| Cahill-Keyes | `44 × 22` | `make generate-geometry generate-graticules-ck generate-earth-ck generate-water-ck` |
| AuthaGraph | `44 × 19.052559` (`44 × 11√3`) | `make generate-authagraph` |
| Dymaxion | `44 × 20.78461` (`44 × 3√3/11`) | `make generate-dymaxion` |
| Myriahedral | `44 × 24.75` | `make generate-myriahedral` |
| Star-X | `34 × 44` | `make generate-star-x` |
| Voronoi | `44 × 22.916667` (`44 × 275/12`) | `make generate-voronoi` |

Generated SVG roots express those physical dimensions with `in` suffixes,
while their `viewBox` coordinates remain unitless and numerically identical.
PDFs retain the physical page size; PNG targets independently assign 3840
pixels to the longest side.

Artifact-family targets are also available as
`generate-geometry-projections`, `generate-graticules-projections`,
`generate-earth-projections`, `generate-water-projections`,
`generate-astro-projections`, `generate-cloud-atmosphere-projections`,
`generate-orbiting-projections`,
`generate-resources-projections`,
`generate-anthropocene-projections`,
`generate-network-swarm-projections`,
`generate-network-cdn-projections`,
`generate-network-fiber-projections`,
`generate-network-groundstations-projections`,
`generate-bathymetry-roulette-projections`, and
`generate-bathymetry-hamonshu-projections`. Each generic
family target includes Cahill-Keyes plus AuthaGraph, Dymaxion, Myriahedral,
Star-X, and Voronoi. The fifteen whole-map generators accept a projection name
on their command line. Every generator reopens its SVG to validate the view box,
required layers, path structure, and finite numeric output.

<a id="generated-artifact-previews"></a>

### Complete released artifact catalog

The [visual gallery](../gallery/README.md) leads with projection comparisons
and featured subjects. Each contact sheet presents the same 32 whole-map
plates in one canonical order: five projection foundations (native geometry,
graticules, earth, water, and the restored Cloud-atmosphere snapshot), five
sky and orbital passes, four network passes, four Anthropocene plates, and
fourteen Stage 12 resource plates. The former Art-passes group is retired from
the contact sheets; both bathymetry plates remain in the standard artifact
graph and their documentation.

Thumbnail clicks open the released full-size image (WebP on the top-of-tree
backend, PNG on the AAO backend). The AAO backend separately offers the
compressed layered SVG viewer and the 44-inch print PDF, so a dense SVG is
never required merely to inspect a larger image.

- [AuthaGraph snapshot](../gallery/authagraph.md) — `44 × 19.052559`
- [Cahill–Keyes snapshot](../gallery/cahill-keyes.md) — `44 × 22`
- [Dymaxion snapshot](../gallery/dymaxion.md) — `44 × 20.78461`
- [Myriahedral snapshot](../gallery/myriahedral.md) — `44 × 24.75`
- [Star-X snapshot](../gallery/star-x.md) — `34 × 44`
- [Voronoi snapshot](../gallery/voronoi.md) — `44 × 22.916667`

All preview and full-image links resolve against the selected image backend:
the committed top-of-tree snapshot under `assets.tot/` (the live default,
recorded in `.github/deploy-backend`) or the immutable `cartofreako/v14/`
AAO release when the deployment is switched. GitHub Pages therefore does not
depend on the untracked local `assets.generated/` directory. The standard
inventory has a dedicated 480-pixel thumbnail for all 33 whole-map passes in
each projection, 198 total; the top-of-tree snapshot additionally carries six
restored Cloud-atmosphere plates, and the contact sheets never download a
full-size image merely to draw a preview.

The Cloud-atmosphere plate is a preview-only addition to the top-of-tree
snapshot. The sealed v14 standard corpus removed the credentialed P-Tree
Cloud-atmosphere snapshot, which remains readable in the immutable v13
record. Licensed network topology, Stage 15 experiments, and unpromoted FIRMS
candidates remain outside the public catalog.

The [SVG generation pipeline](generation.md) explains the generator
sources and Make targets, Natural Earth acquisition, seam handling, sampling,
polygon clipping, projected-path folding, layer construction, self-checks,
perceptual tradeoffs, and both Cahill-Keyes enlargement styles. It is the
authoritative reference for individual `generate-*` targets and the
ocean/land versus physical-feature layer partition. The
[astronomy notes](../passes/astronomy.md) cover the profile,
source evaluation, calculations, instrument filter, and accuracy boundary.
The [Cloud-atmosphere notes](../passes/cloud-atmosphere.md)
record the astro/atmosphere boundary, P-Tree regional/daytime cloud decision,
JAXA source timing, raster-to-H3 preparation, QA and missing-data rules,
terms, products, and verification.
The [Orbital Technosphere notes](../passes/orbital-technosphere.md)
record its naming decision, NASA/CelesTrak feasibility evaluation, OMM and
SGP4 pipeline, semantic detiling, and non-operational accuracy boundary.
The [Anthropocene notes](../passes/anthropocene/implementation.md) record the
dual-year particulate/temperature status, source classifications, record and
rainfall formulas, Canada/Russia fire-source evaluation, EPA/smoke separation,
PurpleAir and water-debris experiment boundaries, snapshot audit, and
interpretation limits.
The [Stage 8b enrichment plan](../passes/anthropocene/enrichment-plan.md) documents
the coverage diagnosis, implemented complete-2025/partial-2026 particulate and
CPC families, FIRMS refresh gate, synthetic PurpleAir interface, and remaining
CAMS, observed PurpleAir, and ocean themes.
The [Resources Stage 12 implementation notes](../passes/resources/implementation.md)
and [enrichment plan](../passes/resources/enrichment-plan.md) define the six
implemented target families, v3 country/spatial contracts, non-sparse
coverage gates, actual reef geometry, corrected human-measure semantics,
refresh workflow, and rejected-candidate audit.
The [resources metric catalog](../passes/resources/metric-catalog.md) makes all 59
catalog entries and their lifecycle visible, including the unreleased
LGBTQIA-related and drug-policy definitions.

### Resource metric catalog and pass classes

The resource catalog distinguishes production behavior from research status:

| Pass class | Meaning | Current resource count |
| --- | --- | ---: |
| **Standard pass** | Offline, included in `make all`, and eligible for the next generated-assets release | 14 |
| **Optional pass** | Fully implemented but deliberately opt-in because of credentials, license acceptance, or an operator decision | 0 |
| **Exploration only** | Cataloged or source-tested, but without a production output tag and released artifact | 45 |

No resource metric is currently optional. Project-wide optional passes are the
credentialed P-Tree Cloud-atmosphere product and licensed network topology.
NASA FIRMS has an optional authorization boundary, but remains an unrendered
exploration input rather than an optional released pass.

The 45 exploration-only entries comprise 41 `planned`, three `supplemental`,
and one `research-gap` metric. `Supplemental` means a possible supporting
product; it does **not** mean an implemented optional pass. The complete
[human-readable catalog](../passes/resources/metric-catalog.md) maps every metric
to its class and promotion boundary, while
[`resources-profile.json`](../../../assets.static/resources/resources-profile.json)
remains the machine-readable authority.
The [network-swarm notes](../passes/network-swarm.md) record the fixed
source audit, variable-input contract, H3/Izzi clustering, independent
downloader encodings, SVG metadata, and interpretation limits.
The [network-infrastructure notes](../passes/network-infrastructure.md)
record the audited external pins, Network CDN site atlas, CC BY-NC-SA 3.0 topology
opt-in, physical-versus-logical edge boundary, seam handling, Izzi collision
layout, products, and verification.
The [Network Fiber notes](../passes/network-fiber.md)
record the cleanup/union decision, checked 2022 and 20260805 snapshots,
default newer layer, neutral snapshot-only semantics, standard build targets,
licensing, and verification.
The [Network Groundstations notes](../passes/network-groundstations.md)
record the vendored alpha60 Starlink gateway snapshot, red-triangle gateway
style, provenance pins, standard build targets, and verification.
The [Bathymetry Roulette notes](../passes/bathymetry/roulette.md)
record the confirmed curve catalogue, explicit varied-line-field and clipping
model, visible key, accepted moiré, products, and verification.
The [Bathymetry Hamonshū notes](../passes/bathymetry/hamonshu.md)
record its source-indexed wave catalogue, depth form mapping, shared Voronoi
field architecture, provenance, commands, products, and verification.
