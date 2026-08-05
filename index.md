# Cartographic projection documentation

This repository contains native C++20 forward implementations of the
AuthaGraph, Cahill-Keyes, Dymaxion, Star-X, Myriahedral, and icosahedral
Voronoi projections for `a60::carto::projection_api`. All six accept variable-size
`a60::carto::frame` values while enforcing the aspect ratio required by the
selected geometry or source-canvas registration.

Before building, see [Prerequisites](docs/prerequisites.md) for the compiler,
GNU Make, Alpha60, Izzi, H3, GDAL/GEOS, Natural Earth, Inkscape, and optional
WebAssembly requirements.

## Repository layout

| Directory | Responsibility | Start here |
| --- | --- | --- |
| [`src.projections/`](src.projections/) | Projection interface, frame abstraction, and native implementations | [`a60-carto-projection.h`](src.projections/a60-carto-projection.h) |
| [`src.generate/`](src.generate/) | Native SVG generators and their shared generation support | [Generation guide](docs/generation.md) |
| [`src.wasm/`](src.wasm/) | Browser adapters, seam-prepared input, smoke tests, and generated WASM builds | [WebAssembly renderer README](src.wasm/README.md) |
| [`tests/`](tests/) | Standalone algorithm and public-API tests | [`make check`](Makefile) |
| [`assets.static/`](assets.static/) | Source plates, historical implementations, reference rasters, and downloaded geographic data | [Myriahedral reconstruction assets](assets.static/myriahedral/README.md) |
| [`assets.generated/`](assets.generated/) | Generated SVG, PDF, and opaque PNG deliverables | [Preview matrix](#generated-artifact-previews) |

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
| Installation and build dependencies | [Prerequisites](docs/prerequisites.md) |
| SVG/PDF/PNG generation, Natural Earth, folding, slicing, and review | [Generation guide](docs/generation.md) |
| Generate-pass evaluation record plus configured, full-suite, family, and exact workflows | [Generate-pass methods and decision record](docs/generation-methods.md) |
| Timestamped all-sky and observer astronomy generation | [Astronomy implementation notes](docs/astro-implementation-notes.md) |
| Process-start solar illumination and source-timed JAXA physical atmosphere generation | [Cloud-atmosphere implementation notes](docs/cloud-atmosphere-implementation-notes.md) |
| Human-made Earth-orbit population and observer generation | [Orbital Technosphere implementation notes](docs/orbital-technosphere-implementation-notes.md) |
| Fuller and McHale 1960 production leaders with separate modern resource context | [World Game resources implementation notes](docs/resources-implementation-notes.md) |
| Source-separated climate, weather, fire, smoke, and air-quality atlas | [Anthropocene implementation notes](docs/anthropocene-implementation-notes.md) |
| Cumulative H3 network-swarm generation | [Network-swarm generation implementation notes](docs/network-swarm-implementation-notes.md) |
| Cloud/CDN site atlas and opt-in cable/exchange topology | [Network-infrastructure implementation notes](docs/network-infrastructure-implementation-notes.md) |
| Monochrome, explicitly varied roulette-line-field bathymetry generation | [Bathymetry Roulette implementation notes](docs/bathymetry-roulette-implementation-notes.md) |
| Natural Earth acquisition, digest, and license | [Natural Earth data note](docs/natural-earth-10m-physical-vectors.md) |
| Production Cahill-Keyes and Myriahedral browser renderers | [WebAssembly renderer README](src.wasm/README.md) |
| Illustrative raster-backed Myriahedral overlay | [WebAssembly workflow](docs/web-workflow.md) and [complete example](docs/web-example.md) |

Each projection has three complementary documents. Context explains the
geometry and cuts, implementation notes describe formulas and code, and the
bibliography records primary sources and attribution.

| Projection | Context | Implementation | Bibliography |
| --- | --- | --- | --- |
| AuthaGraph | [Context](docs/authagraph-context.md) | [Notes](docs/authagraph-implementation-notes.md) | [Sources](docs/authagraph-bibliography.md) |
| Cahill-Keyes | [Context](docs/cahill-keyes-context.md) | [Notes](docs/cahill-keyes-implementation-notes.md) | [Sources](docs/cahill-keyes-bibliography.md) |
| Dymaxion | [Context](docs/dymaxion-context.md) | [Notes](docs/dymaxion-implementation-notes.md) | [Sources](docs/dymaxion-bibliography.md) |
| Star-X | [Context](docs/star-x-context.md) | [Notes](docs/star-x-implementation-notes.md) | [Sources](docs/star-x-bibliography.md) |
| Myriahedral | [Context](docs/myriahedral-context.md) | [Notes](docs/myriahedral-implementation-notes.md) | [Sources](docs/myriahedral-bibliography.md) |
| Icosahedral Voronoi | [Context](docs/voronoi-context.md) | [Notes](docs/voronoi-implementation-notes.md) | [Sources](docs/voronoi-bibliography.md) |

## Choose a projection

| Projection | Geometric model | Required map ratio | Public class | Factory |
| --- | --- | ---: | --- | --- |
| AuthaGraph | Oblique tetrahedron, 24 symmetric sectors, periodic rectangle | `4:sqrt(3)` | `agproj` | `make_authagraph_projection()` |
| Cahill-Keyes | Octahedron, 8 octants, M-shaped rectangular layout | `2:1` | `ckproj` | `make_cahill_keyes_projection()` |
| Dymaxion | Fuller-oriented icosahedron, exact 20-face transform, 23-piece Airocean net | `11/(3sqrt(3))` | `dymaxionproj` | `make_dymaxion_projection()` |
| Star-X | Cahill-Keyes octants, two stacked four-face groups, polar-centered X | `17:22` | `starxproj` | `make_star_x_projection()` |
| Myriahedral | Depth-5 icosahedral mesh, land-aware spanning-tree net | `16:9` source canvas | `myriaproj` | `make_myriahedral_projection()` |
| Voronoi | Regular icosahedron, 20 nearest-site gnomonic faces | `48:25` source canvas | `voronoiproj` | `make_voronoi_projection()` |

## Build and generated artifacts

A bare `make` validates [`generation-profile.json`](generation-profile.json)
and builds only its selected projection/pass SVG matrix. Preview the
normalized selection and targets with `make generation-plan`; see the
[generation methods](docs/generation-methods.md) for schema details and the
generation-pass and Stage 7 decision records. The explicit `make all`
workflow below remains the complete release/review build.

Run all standalone projection checks with:

```sh
make check
```

Generate geometry, labeled graticules, both Natural Earth layer families,
both timestamped astronomy products, both timestamped Orbital Technosphere
products, the Anthropocene observation atlas, the cumulative network-swarm,
the cloud/CDN network-infrastructure site atlas, and Bathymetry Roulette for
all six projections with:

```sh
make all
```

The 24 production whole-earth maps, 12 astronomy maps, 12 Orbital
Technosphere maps, six Anthropocene maps, six network-swarm maps, six
network-infrastructure site maps, six Bathymetry Roulette maps, five
exploratory Myriahedral water perspectives, 12 Cahill-Keyes enlargement
slices, and two Myriahedral face-group slices are each written as a layered SVG under
`assets.generated/svg/`, an Inkscape PDF under `assets.generated/pdf/`, and a
PNG under `assets.generated/png/`. PNGs preserve the source aspect ratio and
have a longest side of 3840 pixels, the horizontal resolution of UHD 4K
video. Transparent SVG page regions are flattened against an opaque white
background. The targets `make generated-projections`, `make
generate-projections`, and `make make-generated` are equivalent aliases.

The credentialed, source-timed Cloud-atmosphere family is deliberately not
part of `make all`. After a P-Tree/JAXA refresh and local H3 preparation,
generate it with `make generate-cloud-atmosphere` or export all three formats
with `make generate-cloud-atmosphere-artifacts`.

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
`generate-network-infrastructure-projections`, and
`generate-bathymetry-roulette-projections`. Each generic
family target includes Cahill-Keyes plus AuthaGraph, Dymaxion, Myriahedral,
Star-X, and Voronoi. The twelve whole-map generators accept a projection name
on their command line. Every generator reopens its SVG to validate the view box,
required layers, path structure, and finite numeric output.

### Generated artifact previews

| Projection | Geometry | Graticules | Earth | Water |
| --- | --- | --- | --- | --- |
| Cahill-Keyes | [`geometry-ck-44-22.png`](assets.generated/png/geometry-ck-44-22.png) | [`graticules-ck-44-22.png`](assets.generated/png/graticules-ck-44-22.png) | [`earth-ck-44-22.png`](assets.generated/png/earth-ck-44-22.png) | [`water-ck-44-22.png`](assets.generated/png/water-ck-44-22.png) |
| AuthaGraph | [`geometry-authagraph-44-19.052559.png`](assets.generated/png/geometry-authagraph-44-19.052559.png) | [`graticules-authagraph-44-19.052559.png`](assets.generated/png/graticules-authagraph-44-19.052559.png) | [`earth-authagraph-44-19.052559.png`](assets.generated/png/earth-authagraph-44-19.052559.png) | [`water-authagraph-44-19.052559.png`](assets.generated/png/water-authagraph-44-19.052559.png) |
| Dymaxion | [`geometry-dymaxion-44-20.78461.png`](assets.generated/png/geometry-dymaxion-44-20.78461.png) | [`graticules-dymaxion-44-20.78461.png`](assets.generated/png/graticules-dymaxion-44-20.78461.png) | [`earth-dymaxion-44-20.78461.png`](assets.generated/png/earth-dymaxion-44-20.78461.png) | [`water-dymaxion-44-20.78461.png`](assets.generated/png/water-dymaxion-44-20.78461.png) |
| Myriahedral | [`geometry-myriahedral-44-24.75.png`](assets.generated/png/geometry-myriahedral-44-24.75.png) | [`graticules-myriahedral-44-24.75.png`](assets.generated/png/graticules-myriahedral-44-24.75.png) | [`earth-myriahedral-44-24.75.png`](assets.generated/png/earth-myriahedral-44-24.75.png) | [`water-myriahedral-44-24.75.png`](assets.generated/png/water-myriahedral-44-24.75.png) |
| Star-X | [`geometry-star-x-34-44.png`](assets.generated/png/geometry-star-x-34-44.png) | [`graticules-star-x-34-44.png`](assets.generated/png/graticules-star-x-34-44.png) | [`earth-star-x-34-44.png`](assets.generated/png/earth-star-x-34-44.png) | [`water-star-x-34-44.png`](assets.generated/png/water-star-x-34-44.png) |
| Voronoi | [`geometry-voronoi-44-22.916667.png`](assets.generated/png/geometry-voronoi-44-22.916667.png) | [`graticules-voronoi-44-22.916667.png`](assets.generated/png/graticules-voronoi-44-22.916667.png) | [`earth-voronoi-44-22.916667.png`](assets.generated/png/earth-voronoi-44-22.916667.png) | [`water-voronoi-44-22.916667.png`](assets.generated/png/water-voronoi-44-22.916667.png) |

The same frames carry an all-sky atlas and the observer-filtered view computed
from the timestamp and San Francisco point stored in the JSON profile:

| Projection | All sky | Observer |
| --- | --- | --- |
| Cahill-Keyes | [`astro-all-sky-ck-44-22.png`](assets.generated/png/astro-all-sky-ck-44-22.png) | [`astro-observer-ck-44-22.png`](assets.generated/png/astro-observer-ck-44-22.png) |
| AuthaGraph | [`astro-all-sky-authagraph-44-19.052559.png`](assets.generated/png/astro-all-sky-authagraph-44-19.052559.png) | [`astro-observer-authagraph-44-19.052559.png`](assets.generated/png/astro-observer-authagraph-44-19.052559.png) |
| Dymaxion | [`astro-all-sky-dymaxion-44-20.78461.png`](assets.generated/png/astro-all-sky-dymaxion-44-20.78461.png) | [`astro-observer-dymaxion-44-20.78461.png`](assets.generated/png/astro-observer-dymaxion-44-20.78461.png) |
| Myriahedral | [`astro-all-sky-myriahedral-44-24.75.png`](assets.generated/png/astro-all-sky-myriahedral-44-24.75.png) | [`astro-observer-myriahedral-44-24.75.png`](assets.generated/png/astro-observer-myriahedral-44-24.75.png) |
| Star-X | [`astro-all-sky-star-x-34-44.png`](assets.generated/png/astro-all-sky-star-x-34-44.png) | [`astro-observer-star-x-34-44.png`](assets.generated/png/astro-observer-star-x-34-44.png) |
| Voronoi | [`astro-all-sky-voronoi-44-22.916667.png`](assets.generated/png/astro-all-sky-voronoi-44-22.916667.png) | [`astro-observer-voronoi-44-22.916667.png`](assets.generated/png/astro-observer-voronoi-44-22.916667.png) |

The Orbital Technosphere products use the separately pinned propagation time
and make-invocation observer point. Global maps show terrestrial subpoints;
observer maps show only the above-horizon topocentric population:

| Projection | Global | Observer |
| --- | --- | --- |
| Cahill-Keyes | [`orbital-technosphere-global-ck-44-22.png`](assets.generated/png/orbital-technosphere-global-ck-44-22.png) | [`orbital-technosphere-observer-ck-44-22.png`](assets.generated/png/orbital-technosphere-observer-ck-44-22.png) |
| AuthaGraph | [`orbital-technosphere-global-authagraph-44-19.052559.png`](assets.generated/png/orbital-technosphere-global-authagraph-44-19.052559.png) | [`orbital-technosphere-observer-authagraph-44-19.052559.png`](assets.generated/png/orbital-technosphere-observer-authagraph-44-19.052559.png) |
| Dymaxion | [`orbital-technosphere-global-dymaxion-44-20.78461.png`](assets.generated/png/orbital-technosphere-global-dymaxion-44-20.78461.png) | [`orbital-technosphere-observer-dymaxion-44-20.78461.png`](assets.generated/png/orbital-technosphere-observer-dymaxion-44-20.78461.png) |
| Myriahedral | [`orbital-technosphere-global-myriahedral-44-24.75.png`](assets.generated/png/orbital-technosphere-global-myriahedral-44-24.75.png) | [`orbital-technosphere-observer-myriahedral-44-24.75.png`](assets.generated/png/orbital-technosphere-observer-myriahedral-44-24.75.png) |
| Star-X | [`orbital-technosphere-global-star-x-34-44.png`](assets.generated/png/orbital-technosphere-global-star-x-34-44.png) | [`orbital-technosphere-observer-star-x-34-44.png`](assets.generated/png/orbital-technosphere-observer-star-x-34-44.png) |
| Voronoi | [`orbital-technosphere-global-voronoi-44-22.916667.png`](assets.generated/png/orbital-technosphere-global-voronoi-44-22.916667.png) | [`orbital-technosphere-observer-voronoi-44-22.916667.png`](assets.generated/png/orbital-technosphere-observer-voronoi-44-22.916667.png) |

The Anthropocene products preserve temperature and precipitation records,
active fire, observed smoke, flood/heavy-rain and severe-weather reports, and
EPA PM2.5 exposure as independent H3 cell-day layers. PM2.5 is not used as a
proxy for smoke, and absent observations do not assert zero:

| Projection | Anthropocene |
| --- | --- |
| Cahill-Keyes | [`anthropocene-ck-44-22.png`](assets.generated/png/anthropocene-ck-44-22.png) |
| AuthaGraph | [`anthropocene-authagraph-44-19.052559.png`](assets.generated/png/anthropocene-authagraph-44-19.052559.png) |
| Dymaxion | [`anthropocene-dymaxion-44-20.78461.png`](assets.generated/png/anthropocene-dymaxion-44-20.78461.png) |
| Myriahedral | [`anthropocene-myriahedral-44-24.75.png`](assets.generated/png/anthropocene-myriahedral-44-24.75.png) |
| Star-X | [`anthropocene-star-x-34-44.png`](assets.generated/png/anthropocene-star-x-34-44.png) |
| Voronoi | [`anthropocene-voronoi-44-22.916667.png`](assets.generated/png/anthropocene-voronoi-44-22.916667.png) |

The World Game resources pass preserves all 40 headings and marked leaders in
the source's 1960 production matrix. The bottom band keeps selected modern
FAO/IRENA indicators outside that historical evidence class:

| Projection | World Game resources |
| --- | --- |
| Cahill-Keyes | [`resources-ck-44-22.png`](assets.generated/png/resources-ck-44-22.png) |
| AuthaGraph | [`resources-authagraph-44-19.052559.png`](assets.generated/png/resources-authagraph-44-19.052559.png) |
| Dymaxion | [`resources-dymaxion-44-20.78461.png`](assets.generated/png/resources-dymaxion-44-20.78461.png) |
| Myriahedral | [`resources-myriahedral-44-24.75.png`](assets.generated/png/resources-myriahedral-44-24.75.png) |
| Star-X | [`resources-star-x-34-44.png`](assets.generated/png/resources-star-x-34-44.png) |
| Voronoi | [`resources-voronoi-44-22.916667.png`](assets.generated/png/resources-voronoi-44-22.916667.png) |

The cumulative network-swarm pass detiles the pinned resolution-5 H3 swarm into
projection-safe resolution-3 Izzi honeycombs while preserving every raw
downloader field:

| Projection | Network-swarm |
| --- | --- |
| Cahill-Keyes | [`network-swarm-ck-44-22.png`](assets.generated/png/network-swarm-ck-44-22.png) |
| AuthaGraph | [`network-swarm-authagraph-44-19.052559.png`](assets.generated/png/network-swarm-authagraph-44-19.052559.png) |
| Dymaxion | [`network-swarm-dymaxion-44-20.78461.png`](assets.generated/png/network-swarm-dymaxion-44-20.78461.png) |
| Myriahedral | [`network-swarm-myriahedral-44-24.75.png`](assets.generated/png/network-swarm-myriahedral-44-24.75.png) |
| Star-X | [`network-swarm-star-x-34-44.png`](assets.generated/png/network-swarm-star-x-34-44.png) |
| Voronoi | [`network-swarm-voronoi-44-22.916667.png`](assets.generated/png/network-swarm-voronoi-44-22.916667.png) |

The ordinary network-infrastructure pass maps located cloud/CDN records. The
separately generated topology variant adds source-backed TeleGeography cable
routes and logical exchange/facility incidence. Topology is an explicit CC
BY-NC-SA 3.0 opt-in and is not part of `make all`:

| Projection | Cloud/CDN sites | Opt-in topology |
| --- | --- | --- |
| Cahill-Keyes | [`network-infrastructure-sites-ck-44-22.png`](assets.generated/png/network-infrastructure-sites-ck-44-22.png) | [`network-infrastructure-topology-ck-44-22.png`](assets.generated/png/network-infrastructure-topology-ck-44-22.png) |
| AuthaGraph | [`network-infrastructure-sites-authagraph-44-19.052559.png`](assets.generated/png/network-infrastructure-sites-authagraph-44-19.052559.png) | [`network-infrastructure-topology-authagraph-44-19.052559.png`](assets.generated/png/network-infrastructure-topology-authagraph-44-19.052559.png) |
| Dymaxion | [`network-infrastructure-sites-dymaxion-44-20.78461.png`](assets.generated/png/network-infrastructure-sites-dymaxion-44-20.78461.png) | [`network-infrastructure-topology-dymaxion-44-20.78461.png`](assets.generated/png/network-infrastructure-topology-dymaxion-44-20.78461.png) |
| Myriahedral | [`network-infrastructure-sites-myriahedral-44-24.75.png`](assets.generated/png/network-infrastructure-sites-myriahedral-44-24.75.png) | [`network-infrastructure-topology-myriahedral-44-24.75.png`](assets.generated/png/network-infrastructure-topology-myriahedral-44-24.75.png) |
| Star-X | [`network-infrastructure-sites-star-x-34-44.png`](assets.generated/png/network-infrastructure-sites-star-x-34-44.png) | [`network-infrastructure-topology-star-x-34-44.png`](assets.generated/png/network-infrastructure-topology-star-x-34-44.png) |
| Voronoi | [`network-infrastructure-sites-voronoi-44-22.916667.png`](assets.generated/png/network-infrastructure-sites-voronoi-44-22.916667.png) | [`network-infrastructure-topology-voronoi-44-22.916667.png`](assets.generated/png/network-infrastructure-topology-voronoi-44-22.916667.png) |

The Bathymetry Roulette pass uses one pale ground and one dark ink, mapping
successively deeper Natural Earth thresholds to more variable and complex
Izzi epitrochoid and hypotrochoid families. Twelve staggered, overlapping
variations per depth form explicit line fields instead of a repeated-symbol
grid:

| Projection | Bathymetry Roulette |
| --- | --- |
| Cahill-Keyes | [`bathymetry-roulette-ck-44-22.png`](assets.generated/png/bathymetry-roulette-ck-44-22.png) |
| AuthaGraph | [`bathymetry-roulette-authagraph-44-19.052559.png`](assets.generated/png/bathymetry-roulette-authagraph-44-19.052559.png) |
| Dymaxion | [`bathymetry-roulette-dymaxion-44-20.78461.png`](assets.generated/png/bathymetry-roulette-dymaxion-44-20.78461.png) |
| Myriahedral | [`bathymetry-roulette-myriahedral-44-24.75.png`](assets.generated/png/bathymetry-roulette-myriahedral-44-24.75.png) |
| Star-X | [`bathymetry-roulette-star-x-34-44.png`](assets.generated/png/bathymetry-roulette-star-x-34-44.png) |
| Voronoi | [`bathymetry-roulette-voronoi-44-22.916667.png`](assets.generated/png/bathymetry-roulette-voronoi-44-22.916667.png) |

The [SVG generation pipeline](docs/generation.md) explains the generator
sources and Make targets, Natural Earth acquisition, seam handling, sampling,
polygon clipping, projected-path folding, layer construction, self-checks,
perceptual tradeoffs, and both Cahill-Keyes enlargement styles. It is the
authoritative reference for individual `generate-*` targets and the
ocean/land versus physical-feature layer partition. The
[astronomy notes](docs/astro-implementation-notes.md) cover the profile,
source evaluation, calculations, instrument filter, and accuracy boundary.
The [Cloud-atmosphere notes](docs/cloud-atmosphere-implementation-notes.md)
record the astro/atmosphere boundary, P-Tree regional/daytime cloud decision,
JAXA source timing, raster-to-H3 preparation, QA and missing-data rules,
terms, products, and verification.
The [Orbital Technosphere notes](docs/orbital-technosphere-implementation-notes.md)
record its naming decision, NASA/CelesTrak feasibility evaluation, OMM and
SGP4 pipeline, semantic detiling, and non-operational accuracy boundary.
The [Anthropocene notes](docs/anthropocene-implementation-notes.md) record the
feasibility boundary, literal 2026 profile, source classifications, record and
rainfall formulas, Canada/Russia fire-source evaluation, EPA/smoke separation,
deferred coral phase, snapshot audit, and interpretation limits.
The [World Game resources notes](docs/resources-implementation-notes.md) record
the bounded source decision, archive and rights review, exact 40-row profile,
separate modern context, authorized-copy transcription workflow, and limits.
The [network-swarm notes](docs/network-swarm-implementation-notes.md) record the fixed
source audit, variable-input contract, H3/Izzi clustering, independent
downloader encodings, SVG metadata, and interpretation limits.
The [network-infrastructure notes](docs/network-infrastructure-implementation-notes.md)
record the audited external pins, normal site atlas, CC BY-NC-SA 3.0 topology
opt-in, physical-versus-logical edge boundary, seam handling, Izzi collision
layout, products, and verification.
The [Bathymetry Roulette notes](docs/bathymetry-roulette-implementation-notes.md)
record the confirmed curve catalogue, explicit varied-line-field and clipping
model, visible key, accepted moiré, products, and verification.

## AuthaGraph

The AuthaGraph implementation follows Hajime Narukawa's 2022 analytic
formulation, orients the tetrahedron with the four published geographic
vertices, and scales the unfolded periodic net to any valid map frame. A named
A3 preset aligns projected coordinates with the checked-in AuthaGraph drawing
sheet.

Construction examples, screen-coordinate conventions, optional raster naming,
the exact frame predicate, and the source-plate `ag_a3` preset are in the
[AuthaGraph public API notes](docs/authagraph-implementation-notes.md#public-api-and-usage).

## Cahill-Keyes

The Cahill-Keyes implementation is derived from Mary Jo Graça and Gene
Keyes's [`MegamapMaker-prep9.pl`](assets.static/cahill-keyes/MegamapMaker-prep9.pl),
preserves the existing Visionscarto map registration, and scales to any finite,
positive 2:1 `a60::carto::frame`.

Construction examples, compatibility presets, screen coordinates, and error
behavior are in the
[Cahill-Keyes public API notes](docs/cahill-keyes-implementation-notes.md#public-construction-and-usage).
The same guide distinguishes a valid 2:1 world carrier from arbitrary-ratio
[enlargement slices](docs/cahill-keyes-implementation-notes.md#carrier-slicing-and-enlargement).

## Star-X

Star-X reuses the native Cahill-Keyes geometry, splits the ordinary M layout
into left and right groups of four spatial face slots, rotates the right
group by 180 degrees, and stacks it above the left group. This produces the
portrait X arrangement around the northern polar locus without raster tiles
or temporary maps. Its default layout closes the former central gap, enlarges
the complete X 120 percent about the page center, adds a central North-pole
star, and composes Natural Earth Antarctica once at the lower end at the
projection's geographic scale.

Construction examples and `star_x_layout` configuration are in the
[Star-X public API notes](docs/star-x-implementation-notes.md#public-c-api).
The signed gap and page-centered enlargement default to `-9/88` of frame
height and `1.2`. The central star and unified Antarctica remain layer-aware
SVG composition helpers, not hidden changes to the point transform.

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
[Dymaxion implementation notes](docs/dymaxion-implementation-notes.md). The
[geometric context](docs/dymaxion-context.md) illustrates the facets, cuts,
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
[Myriahedral public API notes](docs/myriahedral-implementation-notes.md#public-api-and-use).
The same notes record the
[perspective configurations](docs/myriahedral-implementation-notes.md#perspective-configuration-metadata)
and [Myriahedral slicing](docs/myriahedral-implementation-notes.md#myriahedral-slicing).
The production
[WebAssembly base-map option](docs/myriahedral-implementation-notes.md#webassembly-land-and-ocean-option)
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
[Voronoi public API notes](docs/voronoi-implementation-notes.md#public-api-and-use).

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
| [`src.wasm/cahill-keyes-web.cc`](src.wasm/cahill-keyes-web.cc) | Emscripten/Embind adapter that projects points and generates the browser SVG with the native C++20 Cahill-Keyes implementation |
| [`src.wasm/cartofreako-cahill-keyes.mjs`](src.wasm/cartofreako-cahill-keyes.mjs) | Generated ES-module loader for the Cahill-Keyes WebAssembly binary |
| [`src.wasm/cartofreako-cahill-keyes.wasm`](src.wasm/cartofreako-cahill-keyes.wasm) | Generated Cahill-Keyes WebAssembly binary |
| [`src.wasm/cahill-keyes-smoke.mjs`](src.wasm/cahill-keyes-smoke.mjs) | Node smoke test for projection identity, reference coordinates, variable frames, validation, land input, and generated SVG structure |
| [`src.wasm/cahill-myriahedral.cc`](src.wasm/cahill-myriahedral.cc) | Emscripten/Embind Myriahedral adapter with exact terminal-face clipping and an ocean/land-only SVG contract |
| [`src.wasm/cahill-myriahedral-smoke.mjs`](src.wasm/cahill-myriahedral-smoke.mjs) | Node smoke test for the Myriahedral API, 16:9 frames, all 5,120 ocean faces, exact two-layer output, and seam-safe land |
| [`src.wasm/cartofreako-cahill-myriahedral.mjs`](src.wasm/cartofreako-cahill-myriahedral.mjs) | Generated ES-module loader for the Myriahedral WebAssembly binary |
| [`src.wasm/cartofreako-cahill-myriahedral.wasm`](src.wasm/cartofreako-cahill-myriahedral.wasm) | Generated Myriahedral WebAssembly binary |
| [`src.wasm/README.md`](src.wasm/README.md) | Browser builds, layer choices, output artifacts, runtime clipping, shared Natural Earth input, and provenance |
| [`docs/web-workflow.md`](docs/web-workflow.md) | Emscripten workflow for an illustrative raster-backed 1920×1080 Myriahedral overlay |
| [`docs/web-example.md`](docs/web-example.md) | Complete copyable C++, HTML, JavaScript, and build example for that Myriahedral workflow |
| [`docs/generation.md`](docs/generation.md) | End-to-end SVG generation, seam and folding techniques, data preparation, structural checks, and perceptual considerations |
| [`docs/generation-methods.md`](docs/generation-methods.md) | Central `generate-*` evaluation ledger, implemented conclusions, configured workflows, JSON schema, and Stage 7 decisions |
| [`docs/prerequisites.md`](docs/prerequisites.md) | Native build, data acquisition, Inkscape review, and optional WebAssembly prerequisites |
| [`docs/astro-implementation-notes.md`](docs/astro-implementation-notes.md) | Astronomy profile schema, source evaluation, astrometric formulas, instrumentation filter, output contract, verification, and accuracy boundary |
| [`docs/cloud-atmosphere-implementation-notes.md`](docs/cloud-atmosphere-implementation-notes.md) | Stage 4.1a feasibility, astronomy boundary, JAXA sources, process time, P-Tree QA, H3 preparation, products, terms, verification, and limits |
| [`docs/ptree-production-download.md`](docs/ptree-production-download.md) | Quick-start P-Tree registration, secure credentials, connection test, reproducible production refresh, expected files, and troubleshooting |
| [`docs/orbital-technosphere-implementation-notes.md`](docs/orbital-technosphere-implementation-notes.md) | Stage 4.2 feasibility, naming, NASA/CelesTrak source roles, OMM/SGP4 formulas, products, verification, and accuracy boundary |
| [`docs/resources-implementation-notes.md`](docs/resources-implementation-notes.md) | Stage 6 feasibility, source and rights audit, 1960 production-leader profile, modern context, SVG contract, workflow, and limitations |
| [`src.projections/cart0freak0-star-x.h`](src.projections/cart0freak0-star-x.h) | Star-X group assembly, configurable centered scale, polar-composition geometry, frame validation, public API, and factory |
| [`tests/test-star-x-projection-api.cc`](tests/test-star-x-projection-api.cc) | Star-X anchors, assembly and scale, global domain, polar helpers, variable-frame, validation, and API tests |
| [`docs/star-x-context.md`](docs/star-x-context.md) | Star-X octahedral context, face-slot mapping, group rotation, page enlargement, polar composition, and cuts |
| [`docs/star-x-implementation-notes.md`](docs/star-x-implementation-notes.md) | Star-X gap, scale, and polar formulas, API, safeguards, verification, and provenance |
| [`docs/star-x-bibliography.md`](docs/star-x-bibliography.md) | Star-X arrangement, Cahill-Keyes geometry, historical, asset, and test sources |
| [`src.generate/projection-generation-common.h`](src.generate/projection-generation-common.h) | Exact 44-unit frame configurations, projection dispatch, native-cell lookup, cut bisection, and shared seam-safe path projection |
| [`src.generate/generation-instant.h`](src.generate/generation-instant.h) | Shared strict UTC parsing, Julian dates, process-start sampling, `SOURCE_DATE_EPOCH`, and source-age calculation |
| [`src.generate/solar-geometry.h`](src.generate/solar-geometry.h) | Shared astronomy/atmosphere Sun ephemeris, sidereal time, subsolar point, solar altitude, and twilight zones |
| [`generation-profile.json`](generation-profile.json) | Checked-in projection and generation-pass preference used by a bare `make` |
| [`src.generate/generation-profile.h`](src.generate/generation-profile.h) | Strict generation-profile schema, aliases, canonical projection/pass matrix, and safe Make target expansion |
| [`src.generate/resolve-generation-profile.cc`](src.generate/resolve-generation-profile.cc) | Machine-readable target resolver and human-readable `generation-plan` entry point |
| [`tests/test-generation-profile.cc`](tests/test-generation-profile.cc) | Profile defaults, aliases, all-selection expansion, duplicate detection, and invalid-schema tests |
| [`src.generate/projection-area-generation.h`](src.generate/projection-area-generation.h) | Face-local Dymaxion, Myriahedral, and Voronoi transforms plus exact planar-triangle clipping for filled paths |
| [`src.generate/generate-geometry.cc`](src.generate/generate-geometry.cc) | Izzi SVG generator and structural test for native AuthaGraph, Cahill-Keyes/Star-X, Dymaxion, Myriahedral, and Voronoi faces plus four map quadrants |
| [`assets.generated/png/geometry-ck-44-22.png`](assets.generated/png/geometry-ck-44-22.png) | PNG preview of the generated layered Cahill-Keyes face geometry in a 44×22 frame |
| [`src.generate/generate-graticules.cc`](src.generate/generate-graticules.cc) | Izzi SVG generator and structural test for grouped, degree-labeled, discontinuity-split 10° latitude and longitude lines |
| [`assets.generated/png/graticules-ck-44-22.png`](assets.generated/png/graticules-ck-44-22.png) | PNG preview of the generated 44×22 Cahill-Keyes graticule with 17 latitudes and 36 longitudes |
| [`src.generate/natural-earth-generation.h`](src.generate/natural-earth-generation.h) | Shared GDAL/Izzi renderer and structural checks for the complementary Natural Earth base and overlay layer sets |
| [`src.generate/generate-earth.cc`](src.generate/generate-earth.cc) | Thin generator entry point for the `ocean` and `land` base layers |
| [`assets.generated/png/earth-ck-44-22.png`](assets.generated/png/earth-ck-44-22.png) | PNG preview of the generated 44×22 Cahill-Keyes ocean-and-land base |
| [`src.generate/generate-water.cc`](src.generate/generate-water.cc) | Thin generator entry point for every Natural Earth physical layer except `ocean` and `land` |
| [`assets.generated/png/water-ck-44-22.png`](assets.generated/png/water-ck-44-22.png) | PNG preview of the complementary 44×22 Cahill-Keyes physical-feature overlay |
| [`src.generate/bathymetry-roulette-style.h`](src.generate/bathymetry-roulette-style.h) | Validated twelve-depth epitrochoid/hypotrochoid catalogue, twelve field variations, curve construction, palette, and mosaic constants |
| [`src.generate/generate-bathymetry-roulette.cc`](src.generate/generate-bathymetry-roulette.cc) | Six-projection Natural Earth clip and explicit monochrome page-space roulette-line-field generator with key and embedded SVG checks |
| [`tests/test-bathymetry-roulette-style.cc`](tests/test-bathymetry-roulette-style.cc) | Depth ordering, variation, closure period, curve uniqueness, paint transition, and identifier tests |
| [`assets.generated/png/bathymetry-roulette-ck-44-22.png`](assets.generated/png/bathymetry-roulette-ck-44-22.png) | PNG preview of the generated 44×22 Cahill-Keyes roulette bathymetry |
| [`docs/bathymetry-roulette-implementation-notes.md`](docs/bathymetry-roulette-implementation-notes.md) | Stage 4.5 feasibility, confirmed catalogue, clipping and layering model, products, verification, accepted moiré, and limits |
| [`src.generate/astro-data.h`](src.generate/astro-data.h) | Validated JSON profile and catalog ingestion, proper motion, Solar System approximation, sidereal time, altitude, event window, and band filtering |
| [`src.generate/astro-generation.h`](src.generate/astro-generation.h) | Projection-aware astronomy layers, metadata, markers, spherical uncertainty contours, labels, and embedded SVG checks |
| [`src.generate/generate-astro.cc`](src.generate/generate-astro.cc) | Thin all-sky and observer astronomy generator entry point |
| [`tests/test-astro-generation.cc`](tests/test-astro-generation.cc) | Profile authority, time, orientation, horizon, catalog, event-window, instrumentation, and JPL Horizons tolerance tests |
| [`assets.static/astronomy/astro-profile.json`](assets.static/astronomy/astro-profile.json) | Reproducible timestamp, San Francisco reference point, celestial orientation, multi-band instrumentation, event interval, display budgets, and catalog paths |
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
| [`src.generate/resources-data.h`](src.generate/resources-data.h) | Strict historical and modern-context profile loading, source-year and page validation, missing-value semantics, and count invariants |
| [`src.generate/resources-generation.h`](src.generate/resources-generation.h) | Six-projection resource rendering, deterministic collision layout, semantic metadata, and embedded SVG checks |
| [`src.generate/generate-resources.cc`](src.generate/generate-resources.cc) | Thin six-projection World Game resources generator entry point |
| [`tests/test-resources-generation.cc`](tests/test-resources-generation.cc) | Profile facts, source provenance, null semantics, strict-schema failures, metadata, and six-projection layout tests |
| [`assets.static/resources/resources-profile.json`](assets.static/resources/resources-profile.json) | Audited 1960 production leaders and independently sourced modern resource context |
| [`scripts/transcribe-fuller-minerals.py`](scripts/transcribe-fuller-minerals.py) | Conservative OCR workbench for manually re-auditing pages from an authorized local scan |
| [`src.generate/orbiting-data.h`](src.generate/orbiting-data.h) | Orbital Technosphere profile and OMM validation, category membership, SGP4 adapter, frame transforms, illumination, and visibility state |
| [`src.generate/orbiting-generation.h`](src.generate/orbiting-generation.h) | Global and observer semantic SVG layers, subdued Natural Earth base, representative tracks, markers, metadata, and embedded checks |
| [`src.generate/generate-orbiting.cc`](src.generate/generate-orbiting.cc) | Thin Orbital Technosphere generator entry point |
| [`src.generate/third_party/sgp4/`](src.generate/third_party/sgp4/) | Unmodified Vallado/CelesTrak SGP4 C++ reference implementation and provenance |
| [`tests/test-orbiting-generation.cc`](tests/test-orbiting-generation.cc) | Profile, OMM, large catalog ID, published SGP4 vector, NASA SSCWeb tolerance, and finite-state tests |
| [`assets.static/orbital-technosphere/orbital-technosphere-profile.json`](assets.static/orbital-technosphere/orbital-technosphere-profile.json) | Pinned propagation time, make-invocation location, source catalog roles, freshness, visibility, and display budgets |
| [`scripts/fetch-orbiting-data.sh`](scripts/fetch-orbiting-data.sh) | Atomic CelesTrak OMM and NASA SSCWeb snapshot refresh with schema checks and hashes |
| [`src.generate/network-swarm-data.h`](src.generate/network-swarm-data.h) | Strict cumulative swarm GeoJSON and profile validation, 64-bit H3 handling, fixed log scales, and snapshot provenance |
| [`src.generate/network-swarm-clustering.h`](src.generate/network-swarm-clustering.h) | H3 parent grouping, native-projection seam partitioning, and canonicalized Izzi radial honeycomb placement |
| [`src.generate/network-swarm-generation.h`](src.generate/network-swarm-generation.h) | Dark terrestrial base, independent downloader glyph layers, labels, provenance, and embedded SVG checks |
| [`src.generate/generate-network-swarm.cc`](src.generate/generate-network-swarm.cc) | Thin six-projection cumulative network-swarm generator entry point |
| [`tests/test-network-swarm-generation.cc`](tests/test-network-swarm-generation.cc) | Snapshot totals, overlap semantics, H3 statistics, honeycomb uniqueness, and six-projection layout tests |
| [`assets.static/network-swarm/network-swarm-profile.json`](assets.static/network-swarm/network-swarm-profile.json) | H3 resolutions, physical mark dimensions, label/tether settings, fixed p99 scales, hashes, commit, and license |
| [`scripts/prepare-network-swarm-data.sh`](scripts/prepare-network-swarm-data.sh) | Bounded, safe, atomic staging of local ZIP or plain GeoJSON network-swarm input |
| [`docs/network-swarm-implementation-notes.md`](docs/network-swarm-implementation-notes.md) | Stage 4.4 feasibility, source audit, clustering, visual encodings, products, verification, and limits |
| [`src.generate/network-infrastructure-data.h`](src.generate/network-infrastructure-data.h) | Strict profile, cloud-manifest, submarine-cable, landing, and Internet-exchange parsing with exact source audits |
| [`src.generate/network-infrastructure-clustering.h`](src.generate/network-infrastructure-clustering.h) | Shared projection-cell-aware Izzi radial-hexagon collision layout for infrastructure point families |
| [`src.generate/network-infrastructure-generation.h`](src.generate/network-infrastructure-generation.h) | Dark terrestrial base, seam-safe physical and logical topology, semantic point layers, attribution, and embedded SVG checks |
| [`src.generate/generate-network-infrastructure.cc`](src.generate/generate-network-infrastructure.cc) | Thin six-projection network-infrastructure generator entry point for normal sites and opted-in topology profiles |
| [`tests/test-network-infrastructure-generation.cc`](tests/test-network-infrastructure-generation.cc) | Profile license gate, seam geometry, honeycomb uniqueness, mixed-model, XML, and six-projection tests |
| [`assets.static/network-infrastructure/`](assets.static/network-infrastructure/) | Commit/digest/count-pinned sites and topology profiles plus external-source and licensing contract |
| [`scripts/check-network-infrastructure-sources.sh`](scripts/check-network-infrastructure-sources.sh) | Offline commit, digest, and consumed-path validation for external infrastructure checkouts |
| [`docs/network-infrastructure-implementation-notes.md`](docs/network-infrastructure-implementation-notes.md) | Stage 9 feasibility, source audit, license boundary, semantics, profiles, rendering, products, verification, and limits |
| [`src.generate/generate-4-slice.cc`](src.generate/generate-4-slice.cc) | Four full-height, quarter-width Cahill-Keyes quadrant-pair enlargements |
| [`src.generate/generate-8-slice.cc`](src.generate/generate-8-slice.cc) | Eight naturally bounded, face-clipped Cahill-Keyes octant enlargements |
| [`src.generate/generate-myriahedral-slices.cc`](src.generate/generate-myriahedral-slices.cc) | Two complementary, exact-terminal-face Myriahedral water slices |
| [`scripts/fetch-natural-earth-10m.sh`](scripts/fetch-natural-earth-10m.sh) | Pinned, checksum-verifying acquisition of the required Natural Earth shapefiles |
| [`docs/natural-earth-10m-physical-vectors.md`](docs/natural-earth-10m-physical-vectors.md) | Natural Earth source, checksum, extracted-dataset, and licensing note |
| [`src.projections/cart0freak0-myriahedral.h`](src.projections/cart0freak0-myriahedral.h) | Myriahedral mesh, unfolding, forward transform, frame validation, API, and source-raster preset |
| [`src.projections/cart0freak0-myriahedral-tree.inc`](src.projections/cart0freak0-myriahedral-tree.inc) | Compact fixed parent tree for the 5120-face net |
| [`src.generate/myriahedral-perspective-generation.h`](src.generate/myriahedral-perspective-generation.h) | Five exploratory tree configurations, raw bounds, registrations, and lazy layouts |
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
[AuthaGraph implementation provenance](docs/authagraph-implementation-notes.md#provenance)
and [bibliography](docs/authagraph-bibliography.md).

The Cahill-Keyes map design is Gene Keyes's development of B.J.S. Cahill's
octahedral map. The computational construction ported here was written in Perl
by Mary Jo Graça. Its source header permits non-commercial use with attribution
to Graça and Keyes and asks commercial users to contact Gene Keyes. See the
[Cahill-Keyes provenance and licensing note](docs/cahill-keyes-implementation-notes.md#provenance-and-licensing)
and [bibliography](docs/cahill-keyes-bibliography.md).

The Dymaxion map is R. Buckminster Fuller's icosahedral world-map design. The
exact face equations follow Robert W. Gray's published work; the spherical
subface and horizontal net tables derive from PROJ 9.6.2 under its retained
MIT-style notice. Gray's separately distributed reference C program is not
incorporated. See the
[Dymaxion provenance and licensing note](docs/dymaxion-implementation-notes.md#provenance-and-licensing)
and [bibliography](docs/dymaxion-bibliography.md).

Star-X retains that Cahill-Keyes construction and its terms, then applies
Benjamin De Kosnik's two-group arrangement. See the
[Star-X implementation provenance](docs/star-x-implementation-notes.md#provenance-and-limitations)
and [bibliography](docs/star-x-bibliography.md).

The Myriahedral method was published by Jarke J. van Wijk. The fixed mesh,
tree-building method, source command, and raster derive from Hannes Schulz's
`temporaer/myriaworld` implementation; historical land geometry came from
Natural Earth. See the
[Myriahedral implementation provenance](docs/myriahedral-implementation-notes.md#provenance)
and [bibliography](docs/myriahedral-bibliography.md).

The icosahedral Voronoi geometry, parent tree, and registration derive from
the ISC-licensed [`d3-geo-polygon`](https://github.com/d3/d3-geo-polygon)
implementation by Mike Bostock, with the Icosahedral map implemented by Jason
Davies, Enrico Spinielli, and Philippe Rivière. The required ISC notice is
retained in `src.projections/cart0freak0-voronoi.h`. See the
[Voronoi implementation provenance](docs/voronoi-implementation-notes.md#provenance-and-licensing)
and [bibliography](docs/voronoi-bibliography.md).
