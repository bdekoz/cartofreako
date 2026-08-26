---
layout: default
title: Source layout conventions
---

{% include image-backend.md %}

# Source layout conventions

[Documentation index](../README.md) ·
[Build and generated artifacts](build.md) ·
[Visual gallery](../gallery/README.md)

## Repository layout

| Directory | Responsibility | Start here |
| --- | --- | --- |
| [`src.projections/`](../../../src.projections/) | Projection interface, frame abstraction, and native implementations | [`a60-carto-projection.h`](../../../src.projections/a60-carto-projection.h) |
| [`src.generate/`](../../../src.generate/) | Native SVG generators and their shared generation support | [Generation guide](generation.md) |
| [`src.wasm/`](../../../src.wasm/) | All-projection browser runtime, workers, SVG/Canvas/D3 adapters, compatibility modules, examples, and smoke tests | [WebAssembly quick start](../runtime/webassembly-quick-start.md) |
| [`tests/`](../../../tests/) | Standalone algorithm and public-API tests | [`make check`](../../../Makefile) |
| [`assets.static/`](../../../assets.static/) | Source plates, historical implementations, reference rasters, and downloaded geographic data | [Myriahedral reconstruction assets](../../../assets.static/myriahedral/README.md) |
| `assets.generated/` | Projection-organized SVG (`.svg.gz` release companions), PDF, full PNG, and thumbnail deliverables | [Visual gallery](../gallery/README.md), [v14 AAO release record](../releases/aao-v14.md), and [projection snapshot catalog](build.md#generated-artifact-previews) |

This separation keeps reproducible inputs distinct from rendered outputs and
keeps generation programs out of the test suite.

Most projection-specific headers use the `cart0freak0-*.h` basename. The
Dymaxion header uses its requested
[`a60-carto-projection-dymaxion.h`](../../../src.projections/a60-carto-projection-dymaxion.h)
name. The shared Alpha60-compatible interface and frame headers retain their
established `a60-carto-*.h` names. Paths from the earlier `src/`, `generated/`,
`web/`, and `assets/` layout are no longer canonical.

## Source guide

| File | Role |
| --- | --- |
| [`src.projections/cart0freak0-authagraph.h`](../../../src.projections/cart0freak0-authagraph.h) | AuthaGraph analytic forward transform, frame validation, API, and A3 preset |
| [`tests/test-authagraph-projection-api.cc`](../../../tests/test-authagraph-projection-api.cc) | AuthaGraph formula, source-plate, variable-frame, domain, and API tests |
| [`src.projections/cart0freak0-cahill-keyes.h`](../../../src.projections/cart0freak0-cahill-keyes.h) | Native scalable forward construction, `projection_api`, frame validation, and named presets |
| [`src.projections/cart0freak0-cahill-keyes-functions.h`](../../../src.projections/cart0freak0-cahill-keyes-functions.h) | Scale- and offset-aware Cahill-Keyes projected-path seam splitting |
| [`src.projections/cart0freak0-cahill-keyes-slicing.h`](../../../src.projections/cart0freak0-cahill-keyes-slicing.h) | Whole-Earth carrier validation, arbitrary-ratio viewport descriptors, exact-octant clipping, SVG wrappers, and slice verification |
| [`tests/test-cahill-keyes-projection.cc`](../../../tests/test-cahill-keyes-projection.cc) | Cahill-Keyes mathematical reference, scaling, and domain tests |
| [`tests/test-cahill-keyes-projection-api.cc`](../../../tests/test-cahill-keyes-projection-api.cc) | Cahill-Keyes public API, frame, raster, and integration-anchor tests |
| [`tests/test-cahill-keyes-path-functions.cc`](../../../tests/test-cahill-keyes-path-functions.cc) | Cahill-Keyes path seam, scaling, offset, state, and validation tests |
| [`tests/test-cahill-keyes-slicing.cc`](../../../tests/test-cahill-keyes-slicing.cc) | Four-strip and exact-octant geometry, metadata, SVG linkage, physical-size, and invalid-carrier tests |
| [`src.projections/a60-carto-projection-dymaxion.h`](../../../src.projections/a60-carto-projection-dymaxion.h) | Exact Fuller face transform, 23-piece Airocean net, frame validation, public API, factory, and native-size preset |
| [`tests/test-dymaxion-projection-api.cc`](../../../tests/test-dymaxion-projection-api.cc) | Dymaxion edge scale, Gray reference coordinates, topology, variable-frame, domain, and API tests |
| [`src.projections/cart0freak0-equal-earth.h`](../../../src.projections/cart0freak0-equal-earth.h) | Stage 16J standalone spherical Equal Earth forward/reverse equations and normalized page wrapper |
| [`tests/test-equal-earth-projection.cc`](../../../tests/test-equal-earth-projection.cc) | C++ consumption of the neutral canonical and Africa-centered Equal Earth fixtures |
| [`tests/check-equal-earth-projection.mjs`](../../../tests/check-equal-earth-projection.mjs) | JavaScript oracle, round-trip, area-scale, local-scale, angular-deformation, and Tissot diagnostics |
| [`src.projections/cart0freak0-projection-runtime.h`](../../../src.projections/cart0freak0-projection-runtime.h) | All-model registry, layouts, frame validation, native-cell classification, and shared seam-safe paths |
| [`src.projections/cart0freak0-projection-geometry.h`](../../../src.projections/cart0freak0-projection-geometry.h) | Batched flat geometry protocol, adaptive sampling, filled clipping, carrier geometry, and ABI 1 buffers |
| [`src.projections/cart0freak0-projection-slicing.h`](../../../src.projections/cart0freak0-projection-slicing.h) | Generic viewport, native-cell, geographic, and planar-tile descriptors plus CK/Myria catalogs |
| [`src.wasm/cartofreako-projections-web.cc`](../../../src.wasm/cartofreako-projections-web.cc) | Thin all-projection Emscripten/Embind boundary |
| `src.wasm/cartofreako-projections.mjs` / `.wasm` | Generated all-projection ES-module loader and companion binary from `make wasm-projections` |
| [`src.wasm/cartofreako-web.mjs`](../../../src.wasm/cartofreako-web.mjs) | Stable high-level runtime, projection lifecycle, and GeoJSON flattener |
| [`src.wasm/cartofreako-svg.mjs`](../../../src.wasm/cartofreako-svg.mjs) | Shared command-buffer SVG renderer |
| [`src.wasm/cartofreako-canvas.mjs`](../../../src.wasm/cartofreako-canvas.mjs) | Shared command-buffer Canvas/OffscreenCanvas renderer |
| [`src.wasm/cartofreako-d3.mjs`](../../../src.wasm/cartofreako-d3.mjs) | D3-compatible topology-safe stream adapter |
| [`src.wasm/cartofreako-projections-worker.mjs`](../../../src.wasm/cartofreako-projections-worker.mjs) | Module-worker WASM host and transferable buffer protocol |
| [`tests/test-projection-runtime.cc`](../../../tests/test-projection-runtime.cc) | Native all-model buffers, holes, multipolygons, carriers, and slices |
| [`src.wasm/cahill-keyes-web.cc`](../../../src.wasm/cahill-keyes-web.cc) | Emscripten/Embind adapter that projects points and generates the browser SVG with the native C++20 Cahill-Keyes implementation |
| `src.wasm/cartofreako-cahill-keyes.mjs` | Generated ES-module loader for the Cahill-Keyes WebAssembly binary; produced locally by `make wasm-cahill-keyes` and not checked in |
| `src.wasm/cartofreako-cahill-keyes.wasm` | Generated Cahill-Keyes WebAssembly binary; produced locally by `make wasm-cahill-keyes` and not checked in |
| [`src.wasm/cahill-keyes-smoke.mjs`](../../../src.wasm/cahill-keyes-smoke.mjs) | Node smoke test for projection identity, reference coordinates, variable frames, validation, land input, and generated SVG structure |
| [`src.wasm/cahill-myriahedral.cc`](../../../src.wasm/cahill-myriahedral.cc) | Emscripten/Embind Myriahedral adapter with exact terminal-face clipping and an ocean/land-only SVG contract |
| [`src.wasm/cahill-myriahedral-smoke.mjs`](../../../src.wasm/cahill-myriahedral-smoke.mjs) | Node smoke test for the Myriahedral API, 16:9 frames, all 5,120 ocean faces, exact two-layer output, and seam-safe land |
| `src.wasm/cartofreako-cahill-myriahedral.mjs` | Generated ES-module loader for the Myriahedral WebAssembly binary; produced locally by `make wasm-cahill-myriahedral` and not checked in |
| `src.wasm/cartofreako-cahill-myriahedral.wasm` | Generated Myriahedral WebAssembly binary; produced locally by `make wasm-cahill-myriahedral` and not checked in |
| [`src.wasm/README.md`](../../../src.wasm/README.md) | Browser builds, layer choices, output artifacts, runtime clipping, shared Natural Earth input, and provenance |
| [Myriahedral web workflow](../runtime/myriahedral-workflow.md) | Emscripten workflow for an illustrative raster-backed 1920×1080 Myriahedral overlay |
| [Myriahedral web example](../runtime/myriahedral-example.md) | Complete copyable C++, HTML, JavaScript, and build example for that Myriahedral workflow |
| [Generation guide](generation.md) | End-to-end SVG generation, seam and folding techniques, data preparation, structural checks, and perceptual considerations |
| [Generation methods](generation-methods.md) | Central `generate-*` evaluation ledger, implemented conclusions, configured workflows, JSON schema, and Stage 7 decisions |
| [Prerequisites](prerequisites.md) | Native build, data acquisition, Inkscape review, and optional WebAssembly prerequisites |
| [Astronomy implementation](../passes/astronomy.md) | Astronomy profile schema, source evaluation, astrometric formulas, instrumentation filter, output contract, verification, and accuracy boundary |
| [Cloud-atmosphere implementation](../passes/cloud-atmosphere.md) | Stage 4.1a feasibility, astronomy boundary, JAXA sources, process time, P-Tree QA, H3 preparation, products, terms, verification, and limits |
| [P-Tree production download](../data/ptree-download.md) | Quick-start P-Tree registration, secure credentials, connection test, reproducible production refresh, expected files, and troubleshooting |
| [Orbital Technosphere implementation](../passes/orbital-technosphere.md) | Stage 4.2 feasibility, naming, NASA/CelesTrak source roles, OMM/SGP4 formulas, products, verification, and accuracy boundary |
| [Stage 12 implementation](../../development/20260815_stage-12.md) | Stage 12 resource expansion, Anthropocene defaults, external authorization, render hardware, generated snapshots, and Star-X paint-order integration |
| [Visual gallery](../gallery/README.md) | Projection comparison, featured subjects, and entry points to all six 32-plate contact sheets |
| [Technical documentation](../README.md) | Compact build, projection, pass-lifecycle, browser, release, and preservation index |
| `_data/generated_passes.yml` | Canonical 32-plate labels, stems, alternate text, categories, and stable section identifiers |
| `_includes/generated-snapshot.md` | Shared PNG-first contact sheet with explicit layered SVG and print PDF actions for all six projections |
| [Resources enrichment plan](../passes/resources/enrichment-plan.md) | Stage 12 six-family taxonomy, source evaluation, non-sparse options, v3 schema, migration sequence, and release QA |
| [`src.projections/cart0freak0-star-x.h`](../../../src.projections/cart0freak0-star-x.h) | Star-X group assembly, configurable centered scale, fixed-`60°S` cap geometry, frame validation, public API, and factory |
| [`tests/test-star-x-projection-api.cc`](../../../tests/test-star-x-projection-api.cc) | Star-X anchors, assembly and scale, global domain, cap invariants, variable-frame, validation, and API tests |
| [Star-X context](../projections/star-x/context.md) | Star-X octahedral context, face-slot mapping, group rotation, page enlargement, polar composition, and cuts |
| [Star-X implementation](../projections/star-x/implementation.md) | Star-X gap, scale, and polar formulas, API, safeguards, verification, and provenance |
| [Star-X sources](../projections/star-x/bibliography.md) | Star-X arrangement, Cahill-Keyes geometry, historical, asset, and test sources |
| [`src.generate/projection-generation-common.h`](../../../src.generate/projection-generation-common.h) | Exact 44-unit frame configurations, projection dispatch, native-cell lookup, cut bisection, and shared seam-safe path projection |
| [`src.generate/generation-instant.h`](../../../src.generate/generation-instant.h) | Shared strict UTC parsing, Julian dates, process-start sampling, `SOURCE_DATE_EPOCH`, and source-age calculation |
| [`src.generate/solar-geometry.h`](../../../src.generate/solar-geometry.h) | Shared astronomy/atmosphere Sun ephemeris, sidereal time, subsolar point, solar altitude, and twilight zones |
| [`generation-profile.json`](../../../generation-profile.json) | Checked-in projection and generation-pass preference used by a bare `make` |
| [`src.generate/generation-profile.h`](../../../src.generate/generation-profile.h) | Strict generation-profile schema, aliases, canonical projection/pass matrix, and safe Make target expansion |
| [`src.generate/resolve-generation-profile.cc`](../../../src.generate/resolve-generation-profile.cc) | Machine-readable target resolver and human-readable `generation-plan` entry point |
| [`tests/test-generation-profile.cc`](../../../tests/test-generation-profile.cc) | Profile defaults, aliases, all-selection expansion, duplicate detection, and invalid-schema tests |
| [`src.generate/projection-area-generation.h`](../../../src.generate/projection-area-generation.h) | Face-local Dymaxion, Myriahedral, and Voronoi transforms plus exact planar-triangle clipping for filled paths |
| [`src.generate/generate-geometry.cc`](../../../src.generate/generate-geometry.cc) | Izzi SVG generator and structural test for native AuthaGraph, Cahill-Keyes/Star-X, Dymaxion, Myriahedral, and Voronoi faces plus four map quadrants |
| [`geometry-ck-44-22.png`]({{ release_base }}/products/standard/cahill-keyes/thumbnail/geometry-ck-44-22.png) | PNG preview of the generated layered Cahill-Keyes face geometry in a 44×22 frame |
| [`src.generate/generate-graticules.cc`](../../../src.generate/generate-graticules.cc) | Izzi SVG generator and structural test for grouped, degree-labeled, discontinuity-split 10° latitude and longitude lines |
| [`graticules-ck-44-22.png`]({{ release_base }}/products/standard/cahill-keyes/thumbnail/graticules-ck-44-22.png) | PNG preview of the generated 44×22 Cahill-Keyes graticule with 17 latitudes and 36 longitudes |
| [`src.generate/natural-earth-generation.h`](../../../src.generate/natural-earth-generation.h) | Shared GDAL/Izzi renderer and structural checks for the complementary Natural Earth base and overlay layer sets |
| [`src.generate/generate-earth.cc`](../../../src.generate/generate-earth.cc) | Thin generator entry point for the `ocean` and `land` base layers |
| [`earth-ck-44-22.png`]({{ release_base }}/products/standard/cahill-keyes/thumbnail/earth-ck-44-22.png) | PNG preview of the generated 44×22 Cahill-Keyes ocean-and-land base |
| [`src.generate/generate-water.cc`](../../../src.generate/generate-water.cc) | Thin generator entry point for every Natural Earth physical layer except `ocean` and `land` |
| [`water-ck-44-22.png`]({{ release_base }}/products/standard/cahill-keyes/thumbnail/water-ck-44-22.png) | PNG preview of the complementary 44×22 Cahill-Keyes physical-feature overlay |
| [`src.generate/bathymetry-roulette-style.h`](../../../src.generate/bathymetry-roulette-style.h) | Validated twelve-depth epitrochoid/hypotrochoid catalogue, twelve field variations, curve construction, palette, and mosaic constants |
| [`src.generate/generate-bathymetry-roulette.cc`](../../../src.generate/generate-bathymetry-roulette.cc) | Six-projection Natural Earth clip and explicit filled, blue-ramp, Voronoi-grouped roulette-field generator with key and embedded SVG checks |
| [`tests/test-bathymetry-roulette-style.cc`](../../../tests/test-bathymetry-roulette-style.cc) | Cycloid minimum, depth ordering, equal Voronoi distribution, closure period, curve uniqueness, all-fill, opacity, and identifier tests |
| [`bathymetry-roulette-ck-44-22.png`]({{ release_base }}/products/standard/cahill-keyes/thumbnail/bathymetry-roulette-ck-44-22.png) | PNG preview of the generated 44×22 Cahill-Keyes roulette bathymetry |
| [`docs/bathymetry-roulette-implementation-notes.md`](../passes/bathymetry/roulette.md) | Stage 4.5 feasibility, confirmed catalogue, clipping and layering model, products, verification, accepted moiré, and limits |
| [`src.generate/bathymetry-hamonshu-style.h`](../../../src.generate/bathymetry-hamonshu-style.h) | Twelve depth parameter pairs, twelve source-indexed Izzi wave motifs, blue ramp, field geometry, and Voronoi mapping |
| [`src.generate/generate-bathymetry-hamonshu.cc`](../../../src.generate/generate-bathymetry-hamonshu.cc) | Six-projection Natural Earth clip and explicit 30%-opacity Hamonshū wave-field generator |
| [`tests/test-bathymetry-hamonshu-style.cc`](../../../tests/test-bathymetry-hamonshu-style.cc) | Source uniqueness, monotonic density/curvature, overlap, opacity, Voronoi balance, and identifier tests |
| [`docs/bathymetry-hamonshu-implementation-notes.md`](../passes/bathymetry/hamonshu.md) | Stage 4.6 source, form mapping, field/layer contract, commands, verification, and limits |
| [`docs/anthropocene-source-expansion-stage-13.md`](../passes/anthropocene/source-expansion-stage-13.md) | Stage 13 full-GHCN, OpenAQ, CAMS/MAIAC, GFAS, and PurpleAir source evaluation and promotion gates |
| [`src.generate/astro-data.h`](../../../src.generate/astro-data.h) | Validated dual-observer profiles and catalog ingestion, proper motion, Solar System approximation, physical planet radii/apparent sizes, sidereal time, event window, and band filtering |
| [`src.generate/astro-observer.h`](../../../src.generate/astro-observer.h) | Terrestrial altitude and orbiting-Hubble SGP4 state, Earth-limb/Sun separation, and platform visibility rules |
| [`src.generate/astro-generation.h`](../../../src.generate/astro-generation.h) | Projection-aware astronomy layers, distinct ground/Hubble metadata and guides, 2× planet glyphs, dotted true-size outlines, labels, and embedded SVG checks |
| [`src.generate/generate-astro.cc`](../../../src.generate/generate-astro.cc) | Thin all-sky and profile-selected observer astronomy generator entry point |
| [`tests/test-astro-generation.cc`](../../../tests/test-astro-generation.cc) | Dual-profile authority, time, ground horizon, Hubble orbit/avoidance, planet scale, catalogs, instrumentation, and JPL Horizons tolerance tests |
| [`assets.static/astronomy/astro-profile.json`](../../../assets.static/astronomy/astro-profile.json) | Reproducible San Francisco `ground-multiband` observer and generic multi-band instrument contract |
| [`assets.static/astronomy/astro-hubble-profile.json`](../../../assets.static/astronomy/astro-hubble-profile.json) | Reproducible Hubble NORAD/OMM observer, HST composite instrument, and pointing-avoidance contract |
| [`assets.static/astronomy/curated-sky.json`](../../../assets.static/astronomy/curated-sky.json) | Provenanced persistent multi-band objects and timestamped GCN/NSSDC transient snapshot |
| [`scripts/fetch-astro-data.sh`](../../../scripts/fetch-astro-data.sh) | Bounded Gaia DR3, NASA Exoplanet Archive, and JPL SBDB snapshot refresh |
| [`src.generate/cloud-atmosphere-data.h`](../../../src.generate/cloud-atmosphere-data.h) | Strict source profile and prepared H3 observation loading, QA policy, source timing, and missing-data validation |
| [`src.generate/cloud-atmosphere-generation.h`](../../../src.generate/cloud-atmosphere-generation.h) | Projection-aware solar/twilight and physical-atmosphere layers, provenance, visible coverage limits, and embedded checks |
| [`src.generate/generate-cloud-atmosphere.cc`](../../../src.generate/generate-cloud-atmosphere.cc) | Thin six-projection Cloud-atmosphere generator entry point |
| [`src.generate/prepare-cloud-atmosphere.cc`](../../../src.generate/prepare-cloud-atmosphere.cc) | GDAL NetCDF/COG sampling, scale/QA handling, H3 aggregation, and prepared GeoJSON writer |
| [`tests/test-cloud-atmosphere-generation.cc`](../../../tests/test-cloud-atmosphere-generation.cc) | Profile, fixture, time, shared-Sun, semantics, H3, and six-projection geometry tests |
| [`tests/test-resolve-jaxa-stac.py`](../../../tests/test-resolve-jaxa-stac.py) | Offline latest-not-after and nonoverlapping JAXA COG tile-level selection test |
| [`assets.static/cloud-atmosphere/`](../../../assets.static/cloud-atmosphere/) | Authoritative source/QA profile, terms and workflow note, and visibly synthetic test fixture |
| [`scripts/fetch-cloud-atmosphere-data.sh`](../../../scripts/fetch-cloud-atmosphere-data.sh) | Credential-safe P-Tree and public JAXA Earth latest-not-after refresh |
| [`scripts/resolve-jaxa-stac.py`](../../../scripts/resolve-jaxa-stac.py) | Static-STAC traversal, COG-level selection, download, and source manifest helper |
| [`scripts/prepare-cloud-atmosphere-data.sh`](../../../scripts/prepare-cloud-atmosphere-data.sh) | Atomic raw-to-prepared H3 snapshot workflow |
| [`scripts/verify-cloud-atmosphere-data.sh`](../../../scripts/verify-cloud-atmosphere-data.sh) | Prepared snapshot checksum and production-schema gate |
| [`src.generate/resources-data.h`](../../../src.generate/resources-data.h) | Strict Stage 12 v3 source catalogue, six-family country/spatial profile, coverage, and normalized-value loader |
| [`src.generate/resources-generation.h`](../../../src.generate/resources-generation.h) | Metric-specific country choropleths and spatial reef fields, missing-data layers, catalogue metadata, legends, and embedded SVG checks |
| [`src.generate/generate-resources.cc`](../../../src.generate/generate-resources.cc) | Six-family, fourteen-metric resource-generator entry point |
| [`tests/test-resources-generation.cc`](../../../tests/test-resources-generation.cc) | Stage 12 source, coverage, spatial schema, derivation, catalogue, alias, and naming tests |
| [Resources metric catalog](../passes/resources/metric-catalog.md) | Human-readable classification of all 59 standard and exploration-only resource metrics, plus the optional-pass boundary |
| [`assets.static/resources/resources-profile.json`](../../../assets.static/resources/resources-profile.json) | Checked v3 family/source/metric/coverage/spatial catalogue |
| [`assets.static/resources/resources-values.json`](../../../assets.static/resources/resources-values.json) | Checked normalized country observations for released/default and available metrics |
| [`assets.static/resources/countries-110m.geojson`](../../../assets.static/resources/countries-110m.geojson) | Natural Earth Admin-0 country geometry with normalized resource join keys |
| [`assets.static/resources/coral-reefs-025deg.geojson`](../../../assets.static/resources/coral-reefs-025deg.geojson) | Checked 0.25-degree WRI Reefs at Risk threat-cell geometry |
| [`scripts/fetch-resources-data.sh`](../../../scripts/fetch-resources-data.sh) | Explicit primary-source refresh staging workflow; never an ordinary build dependency |
| [`scripts/prepare-resources-data.py`](../../../scripts/prepare-resources-data.py) | Deterministic source parsing, country normalization, human derivation, reef-cell normalization, coverage, schema, and checksum preparation |
| [`scripts/authorize-external.sh`](../../../scripts/authorize-external.sh) | Secret-safe read-only authorization checks for optional P-Tree, NASA FIRMS, and licensed topology passes |
| [`src.generate/orbiting-data.h`](../../../src.generate/orbiting-data.h) | Orbital Technosphere profile and OMM validation, category membership, SGP4 adapter, frame transforms, illumination, and visibility state |
| [`src.generate/orbiting-generation.h`](../../../src.generate/orbiting-generation.h) | Global and observer semantic SVG layers, subdued Natural Earth base, representative tracks, markers, metadata, and embedded checks |
| [`src.generate/generate-orbiting.cc`](../../../src.generate/generate-orbiting.cc) | Thin Orbital Technosphere generator entry point |
| [`src.generate/third_party/sgp4/`](../../../src.generate/third_party/sgp4/) | Unmodified Vallado/CelesTrak SGP4 C++ reference implementation and provenance |
| [`tests/test-orbiting-generation.cc`](../../../tests/test-orbiting-generation.cc) | Profile, OMM, large catalog ID, published SGP4 vector, NASA SSCWeb tolerance, and finite-state tests |
| [`assets.static/orbital-technosphere/orbital-technosphere-profile.json`](../../../assets.static/orbital-technosphere/orbital-technosphere-profile.json) | Pinned propagation time, make-invocation location, source catalog roles, freshness, visibility, and display budgets |
| [`scripts/fetch-orbiting-data.sh`](../../../scripts/fetch-orbiting-data.sh) | Atomic CelesTrak OMM and NASA SSCWeb snapshot refresh with schema checks and hashes |
| [`src.generate/network-swarm-data.h`](../../../src.generate/network-swarm-data.h) | Strict cumulative swarm GeoJSON and profile validation, 64-bit H3 handling, fixed log scales, and snapshot provenance |
| [`src.generate/network-swarm-clustering.h`](../../../src.generate/network-swarm-clustering.h) | H3 parent grouping, native-projection seam partitioning, and canonicalized Izzi radial honeycomb placement |
| [`src.generate/network-swarm-generation.h`](../../../src.generate/network-swarm-generation.h) | WCAG light-gray terrestrial base, enlarged independent downloader glyph layers, 2× title, provenance, and embedded SVG checks |
| [`src.generate/generate-network-swarm.cc`](../../../src.generate/generate-network-swarm.cc) | Thin six-projection cumulative network-swarm generator entry point |
| [`tests/test-network-swarm-generation.cc`](../../../tests/test-network-swarm-generation.cc) | Snapshot totals, overlap semantics, H3 statistics, honeycomb uniqueness, and six-projection layout tests |
| [`assets.static/network-swarm/network-swarm-profile.json`](../../../assets.static/network-swarm/network-swarm-profile.json) | H3 resolutions, physical mark dimensions, label/tether settings, fixed p99 scales, hashes, commit, and license |
| [`scripts/prepare-network-swarm-data.sh`](../../../scripts/prepare-network-swarm-data.sh) | Bounded, safe, atomic staging of local ZIP or plain GeoJSON network-swarm input |
| [Network-swarm implementation](../passes/network-swarm.md) | Stage 4.4 feasibility, source audit, clustering, visual encodings, products, verification, and limits |
| [`src.generate/network-infrastructure-data.h`](../../../src.generate/network-infrastructure-data.h) | Strict profile, cloud-manifest, submarine-cable, landing, and Internet-exchange parsing with exact source audits |
| [`src.generate/network-infrastructure-clustering.h`](../../../src.generate/network-infrastructure-clustering.h) | Shared projection-cell-aware Izzi radial-hexagon collision layout for infrastructure point families |
| [`src.generate/network-infrastructure-generation.h`](../../../src.generate/network-infrastructure-generation.h) | Dark terrestrial base, seam-safe physical and logical topology, semantic point layers, attribution, and embedded SVG checks |
| [`src.generate/generate-network-infrastructure.cc`](../../../src.generate/generate-network-infrastructure.cc) | Thin six-projection network-infrastructure generator entry point for normal sites and opted-in topology profiles |
| [`tests/test-network-infrastructure-generation.cc`](../../../tests/test-network-infrastructure-generation.cc) | Profile license gate, seam geometry, honeycomb uniqueness, mixed-model, XML, and six-projection tests |
| [`assets.static/network-infrastructure/`](../../../assets.static/network-infrastructure/) | Commit/digest/count-pinned sites and topology profiles plus external-source and licensing contract |
| [`scripts/check-network-infrastructure-sources.sh`](../../../scripts/check-network-infrastructure-sources.sh) | Offline commit, digest, and consumed-path validation for external infrastructure checkouts |
| [Network-infrastructure implementation](../passes/network-infrastructure.md) | Stage 9 feasibility, source audit, license boundary, semantics, profiles, rendering, products, verification, and limits |
| [`assets.static/fiber-synthesized/`](../../../assets.static/fiber-synthesized/) | Checked 2022/20260805 cleaned union (Network Fiber input), source-separated audit observations, manifest, and hashes |
| [`scripts/synthesize-submarine-cable-snapshots.py`](../../../scripts/synthesize-submarine-cable-snapshots.py) | Deterministic validation, exact matching, source-separated audit, and cleaned-union preparation |
| [`src.generate/fiber-synthesized-data.h`](../../../src.generate/fiber-synthesized-data.h) | Strict manifest and cleaned-union GeoJSON loader |
| [`src.generate/fiber-synthesized-generation.h`](../../../src.generate/fiber-synthesized-generation.h) | Network Fiber six-projection alpha60-style rendering, temporal semantics, provenance, and embedded checks |
| [`tests/test-fiber-synthesized-generation.cc`](../../../tests/test-fiber-synthesized-generation.cc) | Counts, default snapshot, classification, hashes, and six-projection geometry tests |
| [Network Fiber implementation](../passes/network-fiber.md) | Union-versus-difference decision, source validation, algorithm, default layer, licensing, commands, and verification |
| [`assets.static/network-groundstations/`](../../../assets.static/network-groundstations/) | Vendored alpha60 Starlink gateway/POP snapshot, profile, and hashes |
| [`src.generate/network-groundstations-data.h`](../../../src.generate/network-groundstations-data.h) | Strict profile and gateway GeoJSON loader |
| [`src.generate/network-groundstations-generation.h`](../../../src.generate/network-groundstations-generation.h) | Network Groundstations alpha60 Starlink-style rendering, provenance, and embedded checks |
| [Network Groundstations implementation](../passes/network-groundstations.md) | Vendored source, red-triangle gateway style, provenance pins, build targets, and verification |
| [`src.generate/generate-4-slice.cc`](../../../src.generate/generate-4-slice.cc) | Four full-height, quarter-width Cahill-Keyes quadrant-pair enlargements |
| [`src.generate/generate-8-slice.cc`](../../../src.generate/generate-8-slice.cc) | Eight naturally bounded, face-clipped Cahill-Keyes octant enlargements |
| [`src.generate/generate-myriahedral-slices.cc`](../../../src.generate/generate-myriahedral-slices.cc) | Two complementary, exact-terminal-face Myriahedral water slices |
| [`scripts/fetch-natural-earth-10m.sh`](../../../scripts/fetch-natural-earth-10m.sh) | Pinned, checksum-verifying acquisition of the required Natural Earth shapefiles |
| [Natural Earth source data](../data/natural-earth.md) | Natural Earth source, checksum, extracted-dataset, and licensing note |
| [`src.projections/cart0freak0-myriahedral.h`](../../../src.projections/cart0freak0-myriahedral.h) | Myriahedral mesh, unfolding, forward transform, frame validation, API, and source-raster preset |
| [`src.projections/cart0freak0-myriahedral-tree.inc`](../../../src.projections/cart0freak0-myriahedral-tree.inc) | Compact fixed parent tree for the 5120-face net |
| [`src.projections/cart0freak0-myriahedral-perspectives.h`](../../../src.projections/cart0freak0-myriahedral-perspectives.h) | Five exploratory tree configurations, raw bounds, registrations, and lazy layouts shared by native and WASM clients |
| [`assets.static/myriahedral/perspective-configurations.json`](../../../assets.static/myriahedral/perspective-configurations.json) | Machine-readable Myriahedral preprocessing and perspective metadata |
| [`src.projections/cart0freak0-myriahedral-slicing.h`](../../../src.projections/cart0freak0-myriahedral-slicing.h) | Five-hinge semantic partition, exact face masks, SVG wrappers, and validation |
| [`tests/test-myriahedral-projection-api.cc`](../../../tests/test-myriahedral-projection-api.cc) | Myriahedral topology, reference-coordinate, variable-frame, domain, and API tests |
| [`tests/test-myriahedral-slicing.cc`](../../../tests/test-myriahedral-slicing.cc) | Complementary face counts, hinge boundaries, registered viewports, and carrier validation |
| [`tests/test-projection-generation-common.cc`](../../../tests/test-projection-generation-common.cc) | Seam-safe path regressions, Dymaxion generator dispatch, and exploratory Myriahedral metadata/layout checks |
| [`src.projections/cart0freak0-voronoi.h`](../../../src.projections/cart0freak0-voronoi.h) | Icosahedral Voronoi geometry, gnomonic face projection, affine unfolding, frame validation, API, and source-canvas preset |
| [`tests/test-voronoi-projection-api.cc`](../../../tests/test-voronoi-projection-api.cc) | Voronoi topology, independent D3 reference coordinates, variable-frame, global-domain, seam, and API tests |
| [`src.projections/a60-carto-projection.h`](../../../src.projections/a60-carto-projection.h) | Common projection interface and state |
| [`src.projections/a60-carto-frame.h`](../../../src.projections/a60-carto-frame.h) | Shared frame and `frame_area` abstraction |
| [`src.projections/a60-svg-carto-geo.h`](../../../src.projections/a60-svg-carto-geo.h) | Geographic integration points exercised by API tests |
