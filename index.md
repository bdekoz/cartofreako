---
layout: default
title: Cartofreako
---

# Cartofreako

<p class="page-deck">Six projection systems, 32 released whole-map passes
apiece, and one visual catalog for comparing physical, social, environmental,
network, astronomy, and art layers.</p>

## Start with the maps

The water pass holds the subject constant across all six projections. Select
a thumbnail for the 3840-pixel PNG; layered SVG and print PDF remain explicit
secondary actions.

{% include v13-projection-gallery.md %}

[Explore featured subjects and all six projection catalogs](docs/pages/gallery/README.md).

## Since the v13 generated-assets release

The public gallery above remains the immutable v13 UCB AAO/S3 deposit. Current
source development adds capabilities without rewriting that release:

- runtime API 3 now provides structured forward and candidate-aware reverse
  projection for all six families, portable numerical fixtures, independent
  reverse oracles, typed JavaScript/TypeScript, workers, Canvas/SVG/D3, and an
  offline Three.js flat-map path;
- the current standard graph contains 211 products across 32 pass IDs and has
  exact 1920 × 1080 PNG/lossless-WebP derivatives, affine screen transforms,
  deterministic artifact requests, and decision receipts;
- the former unqualified Anthropocene observation atlas is replaced by
  complete-2025 and partial-2026 `anthropocene-particulate` passes alongside
  the two accepted temperature passes; and
- closed Stage 15 implements a six-projection Majuro evidence pass plus bounded
  PurpleAir-interface and water-debris experiments. These remain local,
  exploration-only products and are not present in v13; and
- Stage 16 now holds the deferred GPU evidence, atoll-source expansion, and
  approved atmosphere-first agentic atlas research plan. Stage 16J also adds
  standalone Equal Earth forward/reverse equations, neutral PROJ/D3 fixtures,
  and five local positioning/slice comparisons without changing the six-family
  release runtime.

GitHub source publication and human-invoked UCB AAO/S3 preservation remain
separate operations. No current development or experiment silently updates
the public v13 object tree.

## Project and build

This repository contains native C++20 forward implementations of the
AuthaGraph, Cahill-Keyes, Dymaxion, Star-X, Myriahedral, and icosahedral
Voronoi projections, plus candidate-aware reverse projection for all six
families through runtime API 3. Star-X exposes its ordinary carrier and unified
Antarctic cap as separate components. All six accept variable-size
`a60::carto::frame` values while enforcing the aspect ratio required by the
selected geometry or source-canvas registration.

Before building, see [Prerequisites](docs/pages/getting-started/prerequisites.md) for the compiler,
GNU Make, Alpha60, Izzi, H3, GDAL/GEOS, Natural Earth, Inkscape, and optional
WebAssembly requirements, or use the
[technical documentation hub](docs/pages/README.md).

## Repository layout

| Directory | Responsibility | Start here |
| --- | --- | --- |
| [`src.projections/`](src.projections/) | Projection interface, frame abstraction, and native implementations | [`a60-carto-projection.h`](src.projections/a60-carto-projection.h) |
| [`src.generate/`](src.generate/) | Native SVG generators and their shared generation support | [Generation guide](docs/pages/getting-started/generation.md) |
| [`src.wasm/`](src.wasm/) | All-projection browser runtime, workers, SVG/Canvas/D3 adapters, compatibility modules, examples, and smoke tests | [WebAssembly quick start](docs/pages/runtime/webassembly-quick-start.md) |
| [`tests/`](tests/) | Standalone algorithm and public-API tests | [`make check`](Makefile) |
| [`assets.static/`](assets.static/) | Source plates, historical implementations, reference rasters, and downloaded geographic data | [Myriahedral reconstruction assets](assets.static/myriahedral/README.md) |
| `assets.generated/` | Projection-organized SVG (`.svg.gz` release companions), PDF, full PNG, and thumbnail deliverables | [Visual gallery](docs/pages/gallery/README.md), [S3 v13 publication](docs/pages/releases/s3-v13.md), and [projection snapshot catalog](#generated-artifact-previews) |

This separation keeps reproducible inputs distinct from rendered outputs and
keeps generation programs out of the test suite.

Most projection-specific headers use the `cart0freak0-*.h` basename. The
Dymaxion header uses its requested
[`a60-carto-projection-dymaxion.h`](src.projections/a60-carto-projection-dymaxion.h)
name. The shared Alpha60-compatible interface and frame headers retain their
established `a60-carto-*.h` names. Paths from the earlier `src/`, `generated/`,
`web/`, and `assets/` layout are no longer canonical.

## Documentation map

| Topic | Authoritative documentation |
| --- | --- |
| Installation and build dependencies | [Prerequisites](docs/pages/getting-started/prerequisites.md) |
| SVG/PDF/PNG generation, Natural Earth, folding, slicing, and review | [Generation guide](docs/pages/getting-started/generation.md) |
| Stage 12 resource, authorization, default-year, snapshot, and Star-X integration | [Stage 12 implementation notes](docs/pages/development/stage-12.md) |
| Stage 13 visual, observer, external-source, and bathymetry development | [Stage 13 convergence notes](docs/pages/development/stage-13.md) |
| Stage 14 projection API, visual hierarchy, verification, and release plan | [Stage 14 convergence ledger](docs/pages/development/stage-14.md) |
| Closed Stage 15 GPU controls, consumer layout, Majuro full pass, and Anthropocene experiments | [Stage 15 closed ledger](docs/pages/development/stage-15.md), [atoll report](reports/stage-15-atoll-evidence-canary.md), and [water-debris report](reports/stage-15-water-debris-feasibility.md) |
| Stage 16 compressed GPU evidence, atoll expansion, and agentic atlas research | [Stage 16 development ledger](docs/pages/development/stage-16.md) |
| Equal Earth control, Africa-centered variant, and one-to-five projection/slice comparisons | [Stage 16J positioning speculations](docs/pages/development/equal-earth-positioning-speculations-v01.md) |
| AI-agent discovery, 1080p gaming derivatives, and preservation of authoritative archive/art/print products | [AI Workflows assessment and 1080p gaming improvement plan](docs/pages/runtime/ai-agent-and-1080p-gaming.md) |
| Visual contact sheets for every projection and released pass | [Visual gallery](docs/pages/gallery/README.md) and [generated projection snapshots](#generated-artifact-previews) |
| Compact index of build, projection, pass, browser, and release documentation | [Technical documentation](docs/pages/README.md) |
| GitHub source releases versus UCB AAO/S3 deposits, static assets, manifests, and render hardware | [`v20260811` Stage 15 source release](docs/pages/releases/v20260811.md), [`v20260810` Stage 14 source release](docs/pages/releases/v20260810.md), [S3 v13 publication](docs/pages/releases/s3-v13.md), and [release runbook](docs/pages/releases/README.md) |
| Generate-pass evaluation record plus configured, full-suite, family, and exact workflows | [Generate-pass methods and decision record](docs/pages/getting-started/generation-methods.md) |
| Timestamped all-sky and observer astronomy generation | [Astronomy implementation notes](docs/pages/passes/astronomy.md) |
| Process-start solar illumination and source-timed JAXA physical atmosphere generation | [Cloud-atmosphere implementation notes](docs/pages/passes/cloud-atmosphere.md) |
| Human-made Earth-orbit population and observer generation | [Orbital Technosphere implementation notes](docs/pages/passes/orbital-technosphere.md) |
| Implemented energy, food, fauna, flora, mineral, and human resource families | [Resources Stage 12 implementation notes](docs/pages/passes/resources/implementation.md) and [enrichment plan](docs/pages/passes/resources/enrichment-plan.md) |
| Standard, optional, and exploration-only resource metrics | [Resources metric catalog](docs/pages/passes/resources/metric-catalog.md) |
| Current accepted-experimental dual-year particulate and temperature atlases plus exploration boundaries | [Anthropocene implementation notes](docs/pages/passes/anthropocene/implementation.md) and [pass-status manifest](contracts/pass-status-v1.json) |
| Implemented dual-year particulate/CPC families, synthetic PurpleAir interface, and planned CAMS, observed PurpleAir, and ocean enrichment | [Anthropocene Stage 8b enrichment plan](docs/pages/passes/anthropocene/enrichment-plan.md) |
| Cumulative H3 network-swarm generation | [Network-swarm generation implementation notes](docs/pages/passes/network-swarm.md) |
| Cloud/CDN site atlas and opt-in cable/exchange topology | [Network-infrastructure implementation notes](docs/pages/passes/network-infrastructure.md) |
| Checked cleanup/union of 2022 and 20260805 submarine fiber | [Fiber Synthesized implementation notes](docs/pages/passes/fiber-synthesized.md) |
| Filled, blue-ramp, Voronoi-grouped roulette bathymetry generation | [Bathymetry Roulette implementation notes](docs/pages/passes/bathymetry/roulette.md) |
| Source-indexed Hamonshū wave-field bathymetry generation | [Bathymetry Hamonshū implementation notes](docs/pages/passes/bathymetry/hamonshu.md) |
| Natural Earth acquisition, digest, and license | [Natural Earth data note](docs/pages/data/natural-earth.md) |
| All-six-projection browser runtime, slices, workers, SVG, Canvas, and D3 | [WebAssembly quick start](docs/pages/runtime/webassembly-quick-start.md) and [runtime reference](src.wasm/README.md) |
| Structured forward results and face-qualified reverse candidates | [Forward/reverse projection API](docs/pages/runtime/projection-api.md) |
| Stage 10 browser architecture and verification | [Stage 10 implementation notes](docs/pages/runtime/webassembly-architecture.md) |
| Implemented topic-oriented Pages structure and repository ownership | [Documentation architecture](docs/pages/development/documentation-layout.md) |
| Illustrative raster-backed Myriahedral overlay | [WebAssembly workflow](docs/pages/runtime/myriahedral-workflow.md) and [complete example](docs/pages/runtime/myriahedral-example.md) |

Each projection has three complementary documents. Context explains the
geometry and cuts, implementation notes describe formulas and code, and the
bibliography records primary sources and attribution.

| Projection | Context | Implementation | Bibliography |
| --- | --- | --- | --- |
| AuthaGraph | [Context](docs/pages/projections/authagraph/context.md) | [Notes](docs/pages/projections/authagraph/implementation.md) | [Sources](docs/pages/projections/authagraph/bibliography.md) |
| Cahill-Keyes | [Context](docs/pages/projections/cahill-keyes/context.md) | [Notes](docs/pages/projections/cahill-keyes/implementation.md) | [Sources](docs/pages/projections/cahill-keyes/bibliography.md) |
| Dymaxion | [Context](docs/pages/projections/dymaxion/context.md) | [Notes](docs/pages/projections/dymaxion/implementation.md) | [Sources](docs/pages/projections/dymaxion/bibliography.md) |
| Star-X | [Context](docs/pages/projections/star-x/context.md) | [Notes](docs/pages/projections/star-x/implementation.md) | [Sources](docs/pages/projections/star-x/bibliography.md) |
| Myriahedral | [Context](docs/pages/projections/myriahedral/context.md) | [Notes](docs/pages/projections/myriahedral/implementation.md) | [Sources](docs/pages/projections/myriahedral/bibliography.md) |
| Icosahedral Voronoi | [Context](docs/pages/projections/voronoi/context.md) | [Notes](docs/pages/projections/voronoi/implementation.md) | [Sources](docs/pages/projections/voronoi/bibliography.md) |
| Equal Earth *(exploration only)* | [Context](docs/pages/projections/equal-earth/context.md) | [Notes](docs/pages/projections/equal-earth/implementation.md) | [Sources](docs/pages/projections/equal-earth/bibliography.md) |

## Choose a projection

| Projection | Geometric model | Required map ratio | Public class | Factory |
| --- | --- | ---: | --- | --- |
| AuthaGraph | Oblique tetrahedron, 24 symmetric sectors, periodic rectangle | `4:sqrt(3)` | `agproj` | `make_authagraph_projection()` |
| Cahill-Keyes | Octahedron, 8 octants, M-shaped rectangular layout | `2:1` | `ckproj` | `make_cahill_keyes_projection()` |
| Dymaxion | Fuller-oriented icosahedron, exact 20-face transform, 23-piece Airocean net | `11/(3sqrt(3))` | `dymaxionproj` | `make_dymaxion_projection()` |
| Star-X | Cahill-Keyes octants, two stacked four-face groups, polar-centered X | `17:22` | `starxproj` | `make_star_x_projection()` |
| Myriahedral | Depth-5 icosahedral mesh, land-aware spanning-tree net | `16:9` source canvas | `myriaproj` | `make_myriahedral_projection()` |
| Voronoi | Regular icosahedron, 20 nearest-site gnomonic faces | `48:25` source canvas | `voronoiproj` | `make_voronoi_projection()` |

Equal Earth is not a seventh entry in that release table. Its Stage 16J
standalone API uses the method's native `2.0545821300028537:1` spherical
carrier for explicit comparison work; see the
[implementation boundary](docs/pages/projections/equal-earth/implementation.md).

## Build and generated artifacts

A bare `make` validates [`generation-profile.json`](generation-profile.json)
and builds only its selected projection/pass SVG matrix. Preview the
normalized selection and targets with `make generation-plan`; see the
[generation methods](docs/pages/getting-started/generation-methods.md) for schema details and the
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
the cloud/CDN network-infrastructure site atlas, the default-rendered Fiber
Synthesized union, Bathymetry Roulette, and
Bathymetry Hamonshū for
all six projections with:

```sh
make all
```

The 24 production whole-earth maps, 18 astronomy maps, 12 Orbital
Technosphere maps, 84 resources maps, 24 Anthropocene maps, six network-swarm
maps, six network-infrastructure site maps, six Fiber Synthesized maps, six
Bathymetry Roulette maps, six Bathymetry Hamonshū maps, five
exploratory Myriahedral water perspectives, 12 Cahill-Keyes enlargement
slices, and two Myriahedral face-group slices total 211 current standard
products. An explicitly authorized P-Tree workflow can add six source-timed
Cloud-atmosphere products, producing 217 local products. They are
organized first by projection beneath `assets.generated/`, then into `svg/`,
`pdf/`, `png/`, and `thumbnail/` directories. The 84 resource SVGs also
receive deterministic `.svg.gz` release archives. All 211 standard products have an Inkscape
PDF and PNG beside their projection peers. PNGs preserve the source aspect ratio and
have a longest side of 3840 pixels, the horizontal resolution of UHD 4K
video. Transparent SVG page regions are flattened against an opaque white
background. The standard graph also creates 32 480-pixel-wide thumbnails for
every projection, 192 total.
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
`generate-network-infrastructure-projections`,
`generate-fiber-synthesized-projections`,
`generate-bathymetry-roulette-projections`, and
`generate-bathymetry-hamonshu-projections`. Each generic
family target includes Cahill-Keyes plus AuthaGraph, Dymaxion, Myriahedral,
Star-X, and Voronoi. The fifteen whole-map generators accept a projection name
on their command line. Every generator reopens its SVG to validate the view box,
required layers, path structure, and finite numeric output.

<a id="generated-artifact-previews"></a>

### Complete released artifact catalog

The [visual gallery](docs/pages/gallery/README.md) now leads with projection comparisons
and featured subjects. Each contact sheet below presents the same 32
complete-release whole-map passes, grouped into projection foundations, sky
and orbital work, networks and Anthropocene, resources, and both bathymetry
art passes. The thirty-second pass is the explicitly authorized P-Tree
Cloud-atmosphere snapshot.

Thumbnail clicks open the released 3840-pixel PNG. Every entry separately
offers the compressed layered SVG viewer and the 44-inch print PDF, so a dense
SVG is never required merely to inspect a larger image.

- [AuthaGraph snapshot](docs/pages/gallery/authagraph.md) — `44 × 19.052559`
- [Cahill–Keyes snapshot](docs/pages/gallery/cahill-keyes.md) — `44 × 22`
- [Dymaxion snapshot](docs/pages/gallery/dymaxion.md) — `44 × 20.78461`
- [Myriahedral snapshot](docs/pages/gallery/myriahedral.md) — `44 × 24.75`
- [Star-X snapshot](docs/pages/gallery/star-x.md) — `34 × 44`
- [Voronoi snapshot](docs/pages/gallery/voronoi.md) — `44 × 22.916667`

All preview, PNG, viewer, and PDF links resolve against the completed
`cartofreako/v13/` public S3 release, so GitHub Pages does not depend on the
untracked local `assets.generated/` directory. The complete v13 inventory has
a dedicated 480-pixel thumbnail for all 32 passes in each projection, 192 total;
the contact sheets never download a full-size PNG merely to draw a preview.

The v13 sheets show the release-era legacy observation atlas, both CPC
temperature fields, and the authorized P-Tree Cloud-atmosphere snapshot. The
current source graph instead carries complete-2025 and partial-2026 particulate
passes plus both CPC temperature fields; those post-v13 particulate products
are not claimed to exist in the immutable v13 object tree. Licensed network
topology, Stage 15 experiments, and unpromoted FIRMS candidates remain outside
the public catalog.

The [SVG generation pipeline](docs/pages/getting-started/generation.md) explains the generator
sources and Make targets, Natural Earth acquisition, seam handling, sampling,
polygon clipping, projected-path folding, layer construction, self-checks,
perceptual tradeoffs, and both Cahill-Keyes enlargement styles. It is the
authoritative reference for individual `generate-*` targets and the
ocean/land versus physical-feature layer partition. The
[astronomy notes](docs/pages/passes/astronomy.md) cover the profile,
source evaluation, calculations, instrument filter, and accuracy boundary.
The [Cloud-atmosphere notes](docs/pages/passes/cloud-atmosphere.md)
record the astro/atmosphere boundary, P-Tree regional/daytime cloud decision,
JAXA source timing, raster-to-H3 preparation, QA and missing-data rules,
terms, products, and verification.
The [Orbital Technosphere notes](docs/pages/passes/orbital-technosphere.md)
record its naming decision, NASA/CelesTrak feasibility evaluation, OMM and
SGP4 pipeline, semantic detiling, and non-operational accuracy boundary.
The [Anthropocene notes](docs/pages/passes/anthropocene/implementation.md) record the
dual-year particulate/temperature status, source classifications, record and
rainfall formulas, Canada/Russia fire-source evaluation, EPA/smoke separation,
PurpleAir and water-debris experiment boundaries, snapshot audit, and
interpretation limits.
The [Stage 8b enrichment plan](docs/pages/passes/anthropocene/enrichment-plan.md) documents
the coverage diagnosis, implemented complete-2025/partial-2026 particulate and
CPC families, FIRMS refresh gate, synthetic PurpleAir interface, and remaining
CAMS, observed PurpleAir, and ocean themes.
The [Resources Stage 12 implementation notes](docs/pages/passes/resources/implementation.md)
and [enrichment plan](docs/pages/passes/resources/enrichment-plan.md) define the six
implemented target families, v3 country/spatial contracts, non-sparse
coverage gates, actual reef geometry, corrected human-measure semantics,
refresh workflow, and rejected-candidate audit.
The [resources metric catalog](docs/pages/passes/resources/metric-catalog.md) makes all 59
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
[human-readable catalog](docs/pages/passes/resources/metric-catalog.md) maps every metric
to its class and promotion boundary, while
[`resources-profile.json`](assets.static/resources/resources-profile.json)
remains the machine-readable authority.
The [network-swarm notes](docs/pages/passes/network-swarm.md) record the fixed
source audit, variable-input contract, H3/Izzi clustering, independent
downloader encodings, SVG metadata, and interpretation limits.
The [network-infrastructure notes](docs/pages/passes/network-infrastructure.md)
record the audited external pins, normal site atlas, CC BY-NC-SA 3.0 topology
opt-in, physical-versus-logical edge boundary, seam handling, Izzi collision
layout, products, and verification.
The [Fiber Synthesized notes](docs/pages/passes/fiber-synthesized.md)
record the cleanup/union decision, checked 2022 and 20260805 snapshots,
default newer layer, neutral snapshot-only semantics, standard build targets,
licensing, and verification.
The [Bathymetry Roulette notes](docs/pages/passes/bathymetry/roulette.md)
record the confirmed curve catalogue, explicit varied-line-field and clipping
model, visible key, accepted moiré, products, and verification.
The [Bathymetry Hamonshū notes](docs/pages/passes/bathymetry/hamonshu.md)
record its source-indexed wave catalogue, depth form mapping, shared Voronoi
field architecture, provenance, commands, products, and verification.

## AuthaGraph

The AuthaGraph implementation follows Hajime Narukawa's 2022 analytic
formulation, orients the tetrahedron with the four published geographic
vertices, and scales the unfolded periodic net to any valid map frame. A named
A3 preset aligns projected coordinates with the checked-in AuthaGraph drawing
sheet.

Construction examples, screen-coordinate conventions, optional raster naming,
the exact frame predicate, and the source-plate `ag_a3` preset are in the
[AuthaGraph public API notes](docs/pages/projections/authagraph/implementation.md#public-api-and-usage).

## Cahill-Keyes

The Cahill-Keyes implementation is derived from Mary Jo Graça and Gene
Keyes's [`MegamapMaker-prep9.pl`](assets.static/cahill-keyes/MegamapMaker-prep9.pl),
preserves the existing Visionscarto map registration, and scales to any finite,
positive 2:1 `a60::carto::frame`.

Construction examples, compatibility presets, screen coordinates, and error
behavior are in the
[Cahill-Keyes public API notes](docs/pages/projections/cahill-keyes/implementation.md#public-construction-and-usage).
The same guide distinguishes a valid 2:1 world carrier from arbitrary-ratio
[enlargement slices](docs/pages/projections/cahill-keyes/implementation.md#carrier-slicing-and-enlargement).

## Star-X

Star-X reuses the native Cahill-Keyes geometry, splits the ordinary M layout
into left and right groups of four spatial face slots, rotates the right
group by 180 degrees, and stacks it above the left group. This produces the
portrait X arrangement around the northern polar locus without raster tiles
or temporary maps. Its default layout closes the former central gap, enlarges
the complete X 120 percent about the page center, adds a central North-pole
star, and composes Antarctic source geometry once at the lower end at the
projection's geographic scale. Natural Earth provides the standard physical
content but does not control the cap geometry.

The current compositor cuts every source at the fixed `60°S` parallel and
reunites the four southern physical and graticule fragments around one
bottom-center pole. It preserves ordinary source-tip radius and registers the
complete projected boundary independently of any land dataset. Its bottommost
point retains `0.25/44` of frame height—exactly `0.25` units on a 34-by-44
plate—so the blue edge remains inside the view box. Every unified Antarctic
fragment is emitted after the ordinary quadrants and paints above them. The
[Star-X snapshot](docs/pages/gallery/star-x.md) shows the released
projection family; the next generated release will carry the corrected lower
clearance.

Construction examples and `star_x_layout` configuration are in the
[Star-X public API notes](docs/pages/projections/star-x/implementation.md#public-c-api).
The signed gap and page-centered enlargement default to `-9/88` of frame
height and `1.2`. The central star and unified Antarctica remain layer-aware
SVG composition helpers, not hidden changes to the point transform; cap
points preserve their ordinary source-tip radius while normalizing bearing so
all four bent Cahill-Keyes edges meet. This fixed, data-independent cap makes
a checked reverse practical: undo the carrier into Cahill–Keyes candidates,
or recover cap bearing and solve latitude on `[-90°,-60°]`, while retaining
component identity for overlaps and cuts. The runtime still advertises Star-X
reverse as `candidates`: component `0` owns the ordinary carrier north of
`60°S`, component `1` owns the cutoff and unified cap, and qualifiers resolve
otherwise valid overlap candidates without guessing.

## Dymaxion

The Dymaxion implementation uses Fuller's geographic icosahedron orientation
and Robert W. Gray's exact sphere-to-equilateral-face equations. It places the
result through the 23-piece horizontal Airocean net: 18 complete faces, two
pieces of the Australia parent face, and three pieces of the Japan parent
face. The local transform preserves uniform scale along every facet edge and
is intentionally distinct from a radial, gnomonic projection.

The public frame may have any finite positive size that retains the exact
`11/(3sqrt(3))` net ratio. Construction examples, formulas, face selection,
split-face registration, generator behavior, and verification are in the
[Dymaxion implementation notes](docs/pages/projections/dymaxion/implementation.md). The
[geometric context](docs/pages/projections/dymaxion/context.md) illustrates the facets, cuts,
screen quadrants, graticules, and resulting Earth map.

## Myriahedral

The Myriahedral implementation reproduces the depth-5 icosahedral mesh of
`temporaer/myriaworld` and uses a fixed default tree reconstructed and
registered for the checked-in source raster. Compact embedded
minimum-spanning trees specify which of the 5120 small faces stay attached;
the generation layer also includes five exploratory perspectives and two
exact complementary face-group slices.
The projection locates a spherical face, intersects its central ray with the
face plane, transfers the gnomonic barycentric coordinates to the unfolded
planar copy, and scales the complete net to a variable frame. It has
no runtime dependency on the historical generator, Boost.Graph, S2, GDAL, or
Natural Earth.

Construction examples, the `myriahedral_source` preset, and the distinction
between this raster-registered 16:9 net and other possible Myriahedral nets
are in the
[Myriahedral public API notes](docs/pages/projections/myriahedral/implementation.md#public-api-and-use).
The same notes record the
[perspective configurations](docs/pages/projections/myriahedral/implementation.md#perspective-configuration-metadata)
and [Myriahedral slicing](docs/pages/projections/myriahedral/implementation.md#myriahedral-slicing).
The production
[WebAssembly base-map option](docs/pages/projections/myriahedral/implementation.md#webassembly-land-and-ocean-option)
emits only the `ocean` and `land` layers.

## Icosahedral Voronoi

The Voronoi implementation reproduces the default `geoIcosahedral()` layout
from `d3-geo-polygon` without a JavaScript dependency. Twelve spherical
vertices define twenty regular triangular faces. Each triangle centroid is a
Voronoi site; the forward transform selects the nearest site by maximizing its
dot product with the geographic unit vector, projects onto that face's
gnomonic tangent plane, and carries the result through the fixed shared-edge
unfolding tree.

This is distinct from the Myriahedral projection above: both begin with an
icosahedron, but this projection retains 20 regular faces and a conventional
fixed net, while Myriahedral subdivides to 5120 faces and uses a land-aware
tree.

Construction examples, source-canvas registration, screen coordinates, and
the `voronoi_source` preset are in the
[Voronoi public API notes](docs/pages/projections/voronoi/implementation.md#public-api-and-use).

## Source guide

| File | Role |
| --- | --- |
| [`src.projections/cart0freak0-authagraph.h`](src.projections/cart0freak0-authagraph.h) | AuthaGraph analytic forward transform, frame validation, API, and A3 preset |
| [`tests/test-authagraph-projection-api.cc`](tests/test-authagraph-projection-api.cc) | AuthaGraph formula, source-plate, variable-frame, domain, and API tests |
| [`src.projections/cart0freak0-cahill-keyes.h`](src.projections/cart0freak0-cahill-keyes.h) | Native scalable forward construction, `projection_api`, frame validation, and named presets |
| [`src.projections/cart0freak0-cahill-keyes-functions.h`](src.projections/cart0freak0-cahill-keyes-functions.h) | Scale- and offset-aware Cahill-Keyes projected-path seam splitting |
| [`src.projections/cart0freak0-cahill-keyes-slicing.h`](src.projections/cart0freak0-cahill-keyes-slicing.h) | Whole-Earth carrier validation, arbitrary-ratio viewport descriptors, exact-octant clipping, SVG wrappers, and slice verification |
| [`tests/test-cahill-keyes-projection.cc`](tests/test-cahill-keyes-projection.cc) | Cahill-Keyes mathematical reference, scaling, and domain tests |
| [`tests/test-cahill-keyes-projection-api.cc`](tests/test-cahill-keyes-projection-api.cc) | Cahill-Keyes public API, frame, raster, and integration-anchor tests |
| [`tests/test-cahill-keyes-path-functions.cc`](tests/test-cahill-keyes-path-functions.cc) | Cahill-Keyes path seam, scaling, offset, state, and validation tests |
| [`tests/test-cahill-keyes-slicing.cc`](tests/test-cahill-keyes-slicing.cc) | Four-strip and exact-octant geometry, metadata, SVG linkage, physical-size, and invalid-carrier tests |
| [`src.projections/a60-carto-projection-dymaxion.h`](src.projections/a60-carto-projection-dymaxion.h) | Exact Fuller face transform, 23-piece Airocean net, frame validation, public API, factory, and native-size preset |
| [`tests/test-dymaxion-projection-api.cc`](tests/test-dymaxion-projection-api.cc) | Dymaxion edge scale, Gray reference coordinates, topology, variable-frame, domain, and API tests |
| [`src.projections/cart0freak0-equal-earth.h`](src.projections/cart0freak0-equal-earth.h) | Stage 16J standalone spherical Equal Earth forward/reverse equations and normalized page wrapper |
| [`tests/test-equal-earth-projection.cc`](tests/test-equal-earth-projection.cc) | C++ consumption of the neutral canonical and Africa-centered Equal Earth fixtures |
| [`tests/check-equal-earth-projection.mjs`](tests/check-equal-earth-projection.mjs) | JavaScript oracle, round-trip, area-scale, local-scale, angular-deformation, and Tissot diagnostics |
| [`src.projections/cart0freak0-projection-runtime.h`](src.projections/cart0freak0-projection-runtime.h) | All-model registry, layouts, frame validation, native-cell classification, and shared seam-safe paths |
| [`src.projections/cart0freak0-projection-geometry.h`](src.projections/cart0freak0-projection-geometry.h) | Batched flat geometry protocol, adaptive sampling, filled clipping, carrier geometry, and ABI 1 buffers |
| [`src.projections/cart0freak0-projection-slicing.h`](src.projections/cart0freak0-projection-slicing.h) | Generic viewport, native-cell, geographic, and planar-tile descriptors plus CK/Myria catalogs |
| [`src.wasm/cartofreako-projections-web.cc`](src.wasm/cartofreako-projections-web.cc) | Thin all-projection Emscripten/Embind boundary |
| `src.wasm/cartofreako-projections.mjs` / `.wasm` | Generated all-projection ES-module loader and companion binary from `make wasm-projections` |
| [`src.wasm/cartofreako-web.mjs`](src.wasm/cartofreako-web.mjs) | Stable high-level runtime, projection lifecycle, and GeoJSON flattener |
| [`src.wasm/cartofreako-svg.mjs`](src.wasm/cartofreako-svg.mjs) | Shared command-buffer SVG renderer |
| [`src.wasm/cartofreako-canvas.mjs`](src.wasm/cartofreako-canvas.mjs) | Shared command-buffer Canvas/OffscreenCanvas renderer |
| [`src.wasm/cartofreako-d3.mjs`](src.wasm/cartofreako-d3.mjs) | D3-compatible topology-safe stream adapter |
| [`src.wasm/cartofreako-projections-worker.mjs`](src.wasm/cartofreako-projections-worker.mjs) | Module-worker WASM host and transferable buffer protocol |
| [`tests/test-projection-runtime.cc`](tests/test-projection-runtime.cc) | Native all-model buffers, holes, multipolygons, carriers, and slices |
| [`src.wasm/cahill-keyes-web.cc`](src.wasm/cahill-keyes-web.cc) | Emscripten/Embind adapter that projects points and generates the browser SVG with the native C++20 Cahill-Keyes implementation |
| `src.wasm/cartofreako-cahill-keyes.mjs` | Generated ES-module loader for the Cahill-Keyes WebAssembly binary; produced locally by `make wasm-cahill-keyes` and not checked in |
| `src.wasm/cartofreako-cahill-keyes.wasm` | Generated Cahill-Keyes WebAssembly binary; produced locally by `make wasm-cahill-keyes` and not checked in |
| [`src.wasm/cahill-keyes-smoke.mjs`](src.wasm/cahill-keyes-smoke.mjs) | Node smoke test for projection identity, reference coordinates, variable frames, validation, land input, and generated SVG structure |
| [`src.wasm/cahill-myriahedral.cc`](src.wasm/cahill-myriahedral.cc) | Emscripten/Embind Myriahedral adapter with exact terminal-face clipping and an ocean/land-only SVG contract |
| [`src.wasm/cahill-myriahedral-smoke.mjs`](src.wasm/cahill-myriahedral-smoke.mjs) | Node smoke test for the Myriahedral API, 16:9 frames, all 5,120 ocean faces, exact two-layer output, and seam-safe land |
| `src.wasm/cartofreako-cahill-myriahedral.mjs` | Generated ES-module loader for the Myriahedral WebAssembly binary; produced locally by `make wasm-cahill-myriahedral` and not checked in |
| `src.wasm/cartofreako-cahill-myriahedral.wasm` | Generated Myriahedral WebAssembly binary; produced locally by `make wasm-cahill-myriahedral` and not checked in |
| [`src.wasm/README.md`](src.wasm/README.md) | Browser builds, layer choices, output artifacts, runtime clipping, shared Natural Earth input, and provenance |
| [Myriahedral web workflow](docs/pages/runtime/myriahedral-workflow.md) | Emscripten workflow for an illustrative raster-backed 1920×1080 Myriahedral overlay |
| [Myriahedral web example](docs/pages/runtime/myriahedral-example.md) | Complete copyable C++, HTML, JavaScript, and build example for that Myriahedral workflow |
| [Generation guide](docs/pages/getting-started/generation.md) | End-to-end SVG generation, seam and folding techniques, data preparation, structural checks, and perceptual considerations |
| [Generation methods](docs/pages/getting-started/generation-methods.md) | Central `generate-*` evaluation ledger, implemented conclusions, configured workflows, JSON schema, and Stage 7 decisions |
| [Prerequisites](docs/pages/getting-started/prerequisites.md) | Native build, data acquisition, Inkscape review, and optional WebAssembly prerequisites |
| [Astronomy implementation](docs/pages/passes/astronomy.md) | Astronomy profile schema, source evaluation, astrometric formulas, instrumentation filter, output contract, verification, and accuracy boundary |
| [Cloud-atmosphere implementation](docs/pages/passes/cloud-atmosphere.md) | Stage 4.1a feasibility, astronomy boundary, JAXA sources, process time, P-Tree QA, H3 preparation, products, terms, verification, and limits |
| [P-Tree production download](docs/pages/data/ptree-download.md) | Quick-start P-Tree registration, secure credentials, connection test, reproducible production refresh, expected files, and troubleshooting |
| [Orbital Technosphere implementation](docs/pages/passes/orbital-technosphere.md) | Stage 4.2 feasibility, naming, NASA/CelesTrak source roles, OMM/SGP4 formulas, products, verification, and accuracy boundary |
| [Stage 12 implementation](docs/pages/development/stage-12.md) | Stage 12 resource expansion, Anthropocene defaults, external authorization, render hardware, generated snapshots, and Star-X paint-order integration |
| [Visual gallery](docs/pages/gallery/README.md) | Projection comparison, featured subjects, and entry points to all six 32-pass contact sheets |
| [Technical documentation](docs/pages/README.md) | Compact build, projection, pass-lifecycle, browser, release, and preservation index |
| `_data/generated_passes.yml` | Canonical 32-pass labels, stems, alternate text, categories, and stable section identifiers |
| `_includes/generated-snapshot.md` | Shared PNG-first contact sheet with explicit layered SVG and print PDF actions for all six projections |
| [Resources enrichment plan](docs/pages/passes/resources/enrichment-plan.md) | Stage 12 six-family taxonomy, source evaluation, non-sparse options, v3 schema, migration sequence, and release QA |
| [`src.projections/cart0freak0-star-x.h`](src.projections/cart0freak0-star-x.h) | Star-X group assembly, configurable centered scale, fixed-`60°S` cap geometry, frame validation, public API, and factory |
| [`tests/test-star-x-projection-api.cc`](tests/test-star-x-projection-api.cc) | Star-X anchors, assembly and scale, global domain, cap invariants, variable-frame, validation, and API tests |
| [Star-X context](docs/pages/projections/star-x/context.md) | Star-X octahedral context, face-slot mapping, group rotation, page enlargement, polar composition, and cuts |
| [Star-X implementation](docs/pages/projections/star-x/implementation.md) | Star-X gap, scale, and polar formulas, API, safeguards, verification, and provenance |
| [Star-X sources](docs/pages/projections/star-x/bibliography.md) | Star-X arrangement, Cahill-Keyes geometry, historical, asset, and test sources |
| [`src.generate/projection-generation-common.h`](src.generate/projection-generation-common.h) | Exact 44-unit frame configurations, projection dispatch, native-cell lookup, cut bisection, and shared seam-safe path projection |
| [`src.generate/generation-instant.h`](src.generate/generation-instant.h) | Shared strict UTC parsing, Julian dates, process-start sampling, `SOURCE_DATE_EPOCH`, and source-age calculation |
| [`src.generate/solar-geometry.h`](src.generate/solar-geometry.h) | Shared astronomy/atmosphere Sun ephemeris, sidereal time, subsolar point, solar altitude, and twilight zones |
| [`generation-profile.json`](generation-profile.json) | Checked-in projection and generation-pass preference used by a bare `make` |
| [`src.generate/generation-profile.h`](src.generate/generation-profile.h) | Strict generation-profile schema, aliases, canonical projection/pass matrix, and safe Make target expansion |
| [`src.generate/resolve-generation-profile.cc`](src.generate/resolve-generation-profile.cc) | Machine-readable target resolver and human-readable `generation-plan` entry point |
| [`tests/test-generation-profile.cc`](tests/test-generation-profile.cc) | Profile defaults, aliases, all-selection expansion, duplicate detection, and invalid-schema tests |
| [`src.generate/projection-area-generation.h`](src.generate/projection-area-generation.h) | Face-local Dymaxion, Myriahedral, and Voronoi transforms plus exact planar-triangle clipping for filled paths |
| [`src.generate/generate-geometry.cc`](src.generate/generate-geometry.cc) | Izzi SVG generator and structural test for native AuthaGraph, Cahill-Keyes/Star-X, Dymaxion, Myriahedral, and Voronoi faces plus four map quadrants |
| [`geometry-ck-44-22.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/cahill-keyes/thumbnail/geometry-ck-44-22.png) | PNG preview of the generated layered Cahill-Keyes face geometry in a 44×22 frame |
| [`src.generate/generate-graticules.cc`](src.generate/generate-graticules.cc) | Izzi SVG generator and structural test for grouped, degree-labeled, discontinuity-split 10° latitude and longitude lines |
| [`graticules-ck-44-22.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/cahill-keyes/thumbnail/graticules-ck-44-22.png) | PNG preview of the generated 44×22 Cahill-Keyes graticule with 17 latitudes and 36 longitudes |
| [`src.generate/natural-earth-generation.h`](src.generate/natural-earth-generation.h) | Shared GDAL/Izzi renderer and structural checks for the complementary Natural Earth base and overlay layer sets |
| [`src.generate/generate-earth.cc`](src.generate/generate-earth.cc) | Thin generator entry point for the `ocean` and `land` base layers |
| [`earth-ck-44-22.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/cahill-keyes/thumbnail/earth-ck-44-22.png) | PNG preview of the generated 44×22 Cahill-Keyes ocean-and-land base |
| [`src.generate/generate-water.cc`](src.generate/generate-water.cc) | Thin generator entry point for every Natural Earth physical layer except `ocean` and `land` |
| [`water-ck-44-22.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/cahill-keyes/thumbnail/water-ck-44-22.png) | PNG preview of the complementary 44×22 Cahill-Keyes physical-feature overlay |
| [`src.generate/bathymetry-roulette-style.h`](src.generate/bathymetry-roulette-style.h) | Validated twelve-depth epitrochoid/hypotrochoid catalogue, twelve field variations, curve construction, palette, and mosaic constants |
| [`src.generate/generate-bathymetry-roulette.cc`](src.generate/generate-bathymetry-roulette.cc) | Six-projection Natural Earth clip and explicit filled, blue-ramp, Voronoi-grouped roulette-field generator with key and embedded SVG checks |
| [`tests/test-bathymetry-roulette-style.cc`](tests/test-bathymetry-roulette-style.cc) | Cycloid minimum, depth ordering, equal Voronoi distribution, closure period, curve uniqueness, all-fill, opacity, and identifier tests |
| [`bathymetry-roulette-ck-44-22.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/cahill-keyes/thumbnail/bathymetry-roulette-ck-44-22.png) | PNG preview of the generated 44×22 Cahill-Keyes roulette bathymetry |
| [`docs/bathymetry-roulette-implementation-notes.md`](docs/pages/passes/bathymetry/roulette.md) | Stage 4.5 feasibility, confirmed catalogue, clipping and layering model, products, verification, accepted moiré, and limits |
| [`src.generate/bathymetry-hamonshu-style.h`](src.generate/bathymetry-hamonshu-style.h) | Twelve depth parameter pairs, twelve source-indexed Izzi wave motifs, blue ramp, field geometry, and Voronoi mapping |
| [`src.generate/generate-bathymetry-hamonshu.cc`](src.generate/generate-bathymetry-hamonshu.cc) | Six-projection Natural Earth clip and explicit 30%-opacity Hamonshū wave-field generator |
| [`tests/test-bathymetry-hamonshu-style.cc`](tests/test-bathymetry-hamonshu-style.cc) | Source uniqueness, monotonic density/curvature, overlap, opacity, Voronoi balance, and identifier tests |
| [`docs/bathymetry-hamonshu-implementation-notes.md`](docs/pages/passes/bathymetry/hamonshu.md) | Stage 4.6 source, form mapping, field/layer contract, commands, verification, and limits |
| [`docs/anthropocene-source-expansion-stage-13.md`](docs/pages/passes/anthropocene/source-expansion-stage-13.md) | Stage 13 full-GHCN, OpenAQ, CAMS/MAIAC, GFAS, and PurpleAir source evaluation and promotion gates |
| [`src.generate/astro-data.h`](src.generate/astro-data.h) | Validated dual-observer profiles and catalog ingestion, proper motion, Solar System approximation, physical planet radii/apparent sizes, sidereal time, event window, and band filtering |
| [`src.generate/astro-observer.h`](src.generate/astro-observer.h) | Terrestrial altitude and orbiting-Hubble SGP4 state, Earth-limb/Sun separation, and platform visibility rules |
| [`src.generate/astro-generation.h`](src.generate/astro-generation.h) | Projection-aware astronomy layers, distinct ground/Hubble metadata and guides, 2× planet glyphs, dotted true-size outlines, labels, and embedded SVG checks |
| [`src.generate/generate-astro.cc`](src.generate/generate-astro.cc) | Thin all-sky and profile-selected observer astronomy generator entry point |
| [`tests/test-astro-generation.cc`](tests/test-astro-generation.cc) | Dual-profile authority, time, ground horizon, Hubble orbit/avoidance, planet scale, catalogs, instrumentation, and JPL Horizons tolerance tests |
| [`assets.static/astronomy/astro-profile.json`](assets.static/astronomy/astro-profile.json) | Reproducible San Francisco `ground-multiband` observer and generic multi-band instrument contract |
| [`assets.static/astronomy/astro-hubble-profile.json`](assets.static/astronomy/astro-hubble-profile.json) | Reproducible Hubble NORAD/OMM observer, HST composite instrument, and pointing-avoidance contract |
| [`assets.static/astronomy/curated-sky.json`](assets.static/astronomy/curated-sky.json) | Provenanced persistent multi-band objects and timestamped GCN/NSSDC transient snapshot |
| [`scripts/fetch-astro-data.sh`](scripts/fetch-astro-data.sh) | Bounded Gaia DR3, NASA Exoplanet Archive, and JPL SBDB snapshot refresh |
| [`src.generate/cloud-atmosphere-data.h`](src.generate/cloud-atmosphere-data.h) | Strict source profile and prepared H3 observation loading, QA policy, source timing, and missing-data validation |
| [`src.generate/cloud-atmosphere-generation.h`](src.generate/cloud-atmosphere-generation.h) | Projection-aware solar/twilight and physical-atmosphere layers, provenance, visible coverage limits, and embedded checks |
| [`src.generate/generate-cloud-atmosphere.cc`](src.generate/generate-cloud-atmosphere.cc) | Thin six-projection Cloud-atmosphere generator entry point |
| [`src.generate/prepare-cloud-atmosphere.cc`](src.generate/prepare-cloud-atmosphere.cc) | GDAL NetCDF/COG sampling, scale/QA handling, H3 aggregation, and prepared GeoJSON writer |
| [`tests/test-cloud-atmosphere-generation.cc`](tests/test-cloud-atmosphere-generation.cc) | Profile, fixture, time, shared-Sun, semantics, H3, and six-projection geometry tests |
| [`tests/test-resolve-jaxa-stac.py`](tests/test-resolve-jaxa-stac.py) | Offline latest-not-after and nonoverlapping JAXA COG tile-level selection test |
| [`assets.static/cloud-atmosphere/`](assets.static/cloud-atmosphere/) | Authoritative source/QA profile, terms and workflow note, and visibly synthetic test fixture |
| [`scripts/fetch-cloud-atmosphere-data.sh`](scripts/fetch-cloud-atmosphere-data.sh) | Credential-safe P-Tree and public JAXA Earth latest-not-after refresh |
| [`scripts/resolve-jaxa-stac.py`](scripts/resolve-jaxa-stac.py) | Static-STAC traversal, COG-level selection, download, and source manifest helper |
| [`scripts/prepare-cloud-atmosphere-data.sh`](scripts/prepare-cloud-atmosphere-data.sh) | Atomic raw-to-prepared H3 snapshot workflow |
| [`scripts/verify-cloud-atmosphere-data.sh`](scripts/verify-cloud-atmosphere-data.sh) | Prepared snapshot checksum and production-schema gate |
| [`src.generate/resources-data.h`](src.generate/resources-data.h) | Strict Stage 12 v3 source catalogue, six-family country/spatial profile, coverage, and normalized-value loader |
| [`src.generate/resources-generation.h`](src.generate/resources-generation.h) | Metric-specific country choropleths and spatial reef fields, missing-data layers, catalogue metadata, legends, and embedded SVG checks |
| [`src.generate/generate-resources.cc`](src.generate/generate-resources.cc) | Six-family, fourteen-metric resource-generator entry point |
| [`tests/test-resources-generation.cc`](tests/test-resources-generation.cc) | Stage 12 source, coverage, spatial schema, derivation, catalogue, alias, and naming tests |
| [Resources metric catalog](docs/pages/passes/resources/metric-catalog.md) | Human-readable classification of all 59 standard and exploration-only resource metrics, plus the optional-pass boundary |
| [`assets.static/resources/resources-profile.json`](assets.static/resources/resources-profile.json) | Checked v3 family/source/metric/coverage/spatial catalogue |
| [`assets.static/resources/resources-values.json`](assets.static/resources/resources-values.json) | Checked normalized country observations for released/default and available metrics |
| [`assets.static/resources/countries-110m.geojson`](assets.static/resources/countries-110m.geojson) | Natural Earth Admin-0 country geometry with normalized resource join keys |
| [`assets.static/resources/coral-reefs-025deg.geojson`](assets.static/resources/coral-reefs-025deg.geojson) | Checked 0.25-degree WRI Reefs at Risk threat-cell geometry |
| [`scripts/fetch-resources-data.sh`](scripts/fetch-resources-data.sh) | Explicit primary-source refresh staging workflow; never an ordinary build dependency |
| [`scripts/prepare-resources-data.py`](scripts/prepare-resources-data.py) | Deterministic source parsing, country normalization, human derivation, reef-cell normalization, coverage, schema, and checksum preparation |
| [`scripts/authorize-external.sh`](scripts/authorize-external.sh) | Secret-safe read-only authorization checks for optional P-Tree, NASA FIRMS, and licensed topology passes |
| [`src.generate/orbiting-data.h`](src.generate/orbiting-data.h) | Orbital Technosphere profile and OMM validation, category membership, SGP4 adapter, frame transforms, illumination, and visibility state |
| [`src.generate/orbiting-generation.h`](src.generate/orbiting-generation.h) | Global and observer semantic SVG layers, subdued Natural Earth base, representative tracks, markers, metadata, and embedded checks |
| [`src.generate/generate-orbiting.cc`](src.generate/generate-orbiting.cc) | Thin Orbital Technosphere generator entry point |
| [`src.generate/third_party/sgp4/`](src.generate/third_party/sgp4/) | Unmodified Vallado/CelesTrak SGP4 C++ reference implementation and provenance |
| [`tests/test-orbiting-generation.cc`](tests/test-orbiting-generation.cc) | Profile, OMM, large catalog ID, published SGP4 vector, NASA SSCWeb tolerance, and finite-state tests |
| [`assets.static/orbital-technosphere/orbital-technosphere-profile.json`](assets.static/orbital-technosphere/orbital-technosphere-profile.json) | Pinned propagation time, make-invocation location, source catalog roles, freshness, visibility, and display budgets |
| [`scripts/fetch-orbiting-data.sh`](scripts/fetch-orbiting-data.sh) | Atomic CelesTrak OMM and NASA SSCWeb snapshot refresh with schema checks and hashes |
| [`src.generate/network-swarm-data.h`](src.generate/network-swarm-data.h) | Strict cumulative swarm GeoJSON and profile validation, 64-bit H3 handling, fixed log scales, and snapshot provenance |
| [`src.generate/network-swarm-clustering.h`](src.generate/network-swarm-clustering.h) | H3 parent grouping, native-projection seam partitioning, and canonicalized Izzi radial honeycomb placement |
| [`src.generate/network-swarm-generation.h`](src.generate/network-swarm-generation.h) | WCAG light-gray terrestrial base, enlarged independent downloader glyph layers, 2× title, provenance, and embedded SVG checks |
| [`src.generate/generate-network-swarm.cc`](src.generate/generate-network-swarm.cc) | Thin six-projection cumulative network-swarm generator entry point |
| [`tests/test-network-swarm-generation.cc`](tests/test-network-swarm-generation.cc) | Snapshot totals, overlap semantics, H3 statistics, honeycomb uniqueness, and six-projection layout tests |
| [`assets.static/network-swarm/network-swarm-profile.json`](assets.static/network-swarm/network-swarm-profile.json) | H3 resolutions, physical mark dimensions, label/tether settings, fixed p99 scales, hashes, commit, and license |
| [`scripts/prepare-network-swarm-data.sh`](scripts/prepare-network-swarm-data.sh) | Bounded, safe, atomic staging of local ZIP or plain GeoJSON network-swarm input |
| [Network-swarm implementation](docs/pages/passes/network-swarm.md) | Stage 4.4 feasibility, source audit, clustering, visual encodings, products, verification, and limits |
| [`src.generate/network-infrastructure-data.h`](src.generate/network-infrastructure-data.h) | Strict profile, cloud-manifest, submarine-cable, landing, and Internet-exchange parsing with exact source audits |
| [`src.generate/network-infrastructure-clustering.h`](src.generate/network-infrastructure-clustering.h) | Shared projection-cell-aware Izzi radial-hexagon collision layout for infrastructure point families |
| [`src.generate/network-infrastructure-generation.h`](src.generate/network-infrastructure-generation.h) | Dark terrestrial base, seam-safe physical and logical topology, semantic point layers, attribution, and embedded SVG checks |
| [`src.generate/generate-network-infrastructure.cc`](src.generate/generate-network-infrastructure.cc) | Thin six-projection network-infrastructure generator entry point for normal sites and opted-in topology profiles |
| [`tests/test-network-infrastructure-generation.cc`](tests/test-network-infrastructure-generation.cc) | Profile license gate, seam geometry, honeycomb uniqueness, mixed-model, XML, and six-projection tests |
| [`assets.static/network-infrastructure/`](assets.static/network-infrastructure/) | Commit/digest/count-pinned sites and topology profiles plus external-source and licensing contract |
| [`scripts/check-network-infrastructure-sources.sh`](scripts/check-network-infrastructure-sources.sh) | Offline commit, digest, and consumed-path validation for external infrastructure checkouts |
| [Network-infrastructure implementation](docs/pages/passes/network-infrastructure.md) | Stage 9 feasibility, source audit, license boundary, semantics, profiles, rendering, products, verification, and limits |
| [`assets.static/fiber-synthesized/`](assets.static/fiber-synthesized/) | Checked 2022/20260805 cleaned union, source-separated audit observations, manifest, and hashes |
| [`scripts/synthesize-submarine-cable-snapshots.py`](scripts/synthesize-submarine-cable-snapshots.py) | Deterministic validation, exact matching, source-separated audit, and cleaned-union preparation |
| [`src.generate/fiber-synthesized-data.h`](src.generate/fiber-synthesized-data.h) | Strict manifest and cleaned-union GeoJSON loader |
| [`src.generate/fiber-synthesized-generation.h`](src.generate/fiber-synthesized-generation.h) | Six-projection default-union rendering, temporal semantics, provenance, and embedded checks |
| [`tests/test-fiber-synthesized-generation.cc`](tests/test-fiber-synthesized-generation.cc) | Counts, default snapshot, classification, hashes, and six-projection geometry tests |
| [Fiber Synthesized implementation](docs/pages/passes/fiber-synthesized.md) | Union-versus-difference decision, source validation, algorithm, default layer, licensing, commands, and verification |
| [`src.generate/generate-4-slice.cc`](src.generate/generate-4-slice.cc) | Four full-height, quarter-width Cahill-Keyes quadrant-pair enlargements |
| [`src.generate/generate-8-slice.cc`](src.generate/generate-8-slice.cc) | Eight naturally bounded, face-clipped Cahill-Keyes octant enlargements |
| [`src.generate/generate-myriahedral-slices.cc`](src.generate/generate-myriahedral-slices.cc) | Two complementary, exact-terminal-face Myriahedral water slices |
| [`scripts/fetch-natural-earth-10m.sh`](scripts/fetch-natural-earth-10m.sh) | Pinned, checksum-verifying acquisition of the required Natural Earth shapefiles |
| [Natural Earth source data](docs/pages/data/natural-earth.md) | Natural Earth source, checksum, extracted-dataset, and licensing note |
| [`src.projections/cart0freak0-myriahedral.h`](src.projections/cart0freak0-myriahedral.h) | Myriahedral mesh, unfolding, forward transform, frame validation, API, and source-raster preset |
| [`src.projections/cart0freak0-myriahedral-tree.inc`](src.projections/cart0freak0-myriahedral-tree.inc) | Compact fixed parent tree for the 5120-face net |
| [`src.projections/cart0freak0-myriahedral-perspectives.h`](src.projections/cart0freak0-myriahedral-perspectives.h) | Five exploratory tree configurations, raw bounds, registrations, and lazy layouts shared by native and WASM clients |
| [`assets.static/myriahedral/perspective-configurations.json`](assets.static/myriahedral/perspective-configurations.json) | Machine-readable Myriahedral preprocessing and perspective metadata |
| [`src.projections/cart0freak0-myriahedral-slicing.h`](src.projections/cart0freak0-myriahedral-slicing.h) | Five-hinge semantic partition, exact face masks, SVG wrappers, and validation |
| [`tests/test-myriahedral-projection-api.cc`](tests/test-myriahedral-projection-api.cc) | Myriahedral topology, reference-coordinate, variable-frame, domain, and API tests |
| [`tests/test-myriahedral-slicing.cc`](tests/test-myriahedral-slicing.cc) | Complementary face counts, hinge boundaries, registered viewports, and carrier validation |
| [`tests/test-projection-generation-common.cc`](tests/test-projection-generation-common.cc) | Seam-safe path regressions, Dymaxion generator dispatch, and exploratory Myriahedral metadata/layout checks |
| [`src.projections/cart0freak0-voronoi.h`](src.projections/cart0freak0-voronoi.h) | Icosahedral Voronoi geometry, gnomonic face projection, affine unfolding, frame validation, API, and source-canvas preset |
| [`tests/test-voronoi-projection-api.cc`](tests/test-voronoi-projection-api.cc) | Voronoi topology, independent D3 reference coordinates, variable-frame, global-domain, seam, and API tests |
| [`src.projections/a60-carto-projection.h`](src.projections/a60-carto-projection.h) | Common projection interface and state |
| [`src.projections/a60-carto-frame.h`](src.projections/a60-carto-frame.h) | Shared frame and `frame_area` abstraction |
| [`src.projections/a60-svg-carto-geo.h`](src.projections/a60-svg-carto-geo.h) | Geographic integration points exercised by API tests |

## Attribution and licensing

AuthaGraph was invented and developed by Hajime Narukawa. The implementation
uses his published 2022 analytic formulation and an official Narukawa Lab
drawing sheet. See the
[AuthaGraph implementation provenance](docs/pages/projections/authagraph/implementation.md#provenance)
and [bibliography](docs/pages/projections/authagraph/bibliography.md).

The Cahill-Keyes map design is Gene Keyes's development of B.J.S. Cahill's
octahedral map. The computational construction ported here was written in Perl
by Mary Jo Graça. Its source header permits non-commercial use with attribution
to Graça and Keyes and asks commercial users to contact Gene Keyes. See the
[Cahill-Keyes provenance and licensing note](docs/pages/projections/cahill-keyes/implementation.md#provenance-and-licensing)
and [bibliography](docs/pages/projections/cahill-keyes/bibliography.md).

The Dymaxion map is R. Buckminster Fuller's icosahedral world-map design. The
exact face equations follow Robert W. Gray's published work; the spherical
subface and horizontal net tables derive from PROJ 9.6.2 under its retained
MIT-style notice. Gray's separately distributed reference C program is not
incorporated. See the
[Dymaxion provenance and licensing note](docs/pages/projections/dymaxion/implementation.md#provenance-and-licensing)
and [bibliography](docs/pages/projections/dymaxion/bibliography.md).

Star-X retains that Cahill-Keyes construction and its terms, then applies
Benjamin De Kosnik's two-group arrangement. See the
[Star-X implementation provenance](docs/pages/projections/star-x/implementation.md#provenance-and-limitations)
and [bibliography](docs/pages/projections/star-x/bibliography.md).

The Myriahedral method was published by Jarke J. van Wijk. The fixed mesh,
tree-building method, source command, and raster derive from Hannes Schulz's
`temporaer/myriaworld` implementation; historical land geometry came from
Natural Earth. See the
[Myriahedral implementation provenance](docs/pages/projections/myriahedral/implementation.md#provenance)
and [bibliography](docs/pages/projections/myriahedral/bibliography.md).

The icosahedral Voronoi geometry, parent tree, and registration derive from
the ISC-licensed [`d3-geo-polygon`](https://github.com/d3/d3-geo-polygon)
implementation by Mike Bostock, with the Icosahedral map implemented by Jason
Davies, Enrico Spinielli, and Philippe Rivière. The required ISC notice is
retained in `src.projections/cart0freak0-voronoi.h`. See the
[Voronoi implementation provenance](docs/pages/projections/voronoi/implementation.md#provenance-and-licensing)
and [bibliography](docs/pages/projections/voronoi/bibliography.md).
