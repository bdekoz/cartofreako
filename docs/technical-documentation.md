---
layout: default
title: Cartofreako technical documentation
---

# Technical documentation

Use the [visual gallery](gallery.md) to browse the release first. This page is
the compact route into building, projection mathematics, pass semantics,
browser integration, verification, and preservation.

## Start, build, and generate

| Need | Documentation |
| --- | --- |
| Install compilers, libraries, data tools, and optional WebAssembly support | [Prerequisites](prerequisites.md) |
| Generate SVG, PDF, PNG, thumbnails, slices, and projection families | [Generation guide](generation.md) |
| Understand the selected profile, pass evaluation, and exact versus family workflows | [Generation methods and decision record](generation-methods.md) |
| Review the complete Stage 13 development manifest | [Stage 13 convergence notes](converge-generation-13.md) |
| Follow the Stage 14 plan, implementation changes, and verification evidence | [Stage 14 convergence ledger](converge-generation-14.md) |
| Authorize and generate credentialed external products | [Configured generation](generation.md#configured-development-generation), [Cloud-atmosphere generation](generation.md#cloud-atmosphere-generation), and [P-Tree production download](ptree-production-download.md) |

## Pass catalog and lifecycle

The [resources metric catalog](resources-metric-catalog.md) is the visible
index of all 59 resource metrics. It states both subject meaning and release
status; [`resources-profile.json`](../assets.static/resources/resources-profile.json)
is the machine-readable authority.

| Class | Meaning |
| --- | --- |
| **Standard pass** | Released, reproducible without a credential or special acceptance, included in `make all`, and represented in the public contact sheets. |
| **Optional pass** | Implemented but deliberately gated by credentials, license acceptance, or an operator decision. Authorization makes it eligible for subsequent configured generation. |
| **Exploration only** | Cataloged, proposed, or source-tested without a released production output. It is not silently generated and is not a missing release artifact. |

The current resource profile has 14 standard passes, no optional resource
passes, and 45 exploration-only metrics. Project-wide optional products include
the credentialed P-Tree Cloud-atmosphere pass and licensed network topology;
NASA FIRMS remains an exploration input rather than a released optional pass.

| Family | Documentation |
| --- | --- |
| Energy, food, fauna, flora, mineral, and human resources | [Stage 12 resource implementation](resources-implementation-notes.md), [metric catalog](resources-metric-catalog.md), and [enrichment plan](resources-enrichment-plan.md) |
| Astronomy and observer instruments | [Astronomy implementation](astro-implementation-notes.md) |
| Orbital Technosphere | [Orbital Technosphere implementation](orbital-technosphere-implementation-notes.md) |
| Climate, weather, fire, smoke, and air quality | [Anthropocene implementation](anthropocene-implementation-notes.md), [source expansion](anthropocene-source-expansion-stage-13.md), and [enrichment plan](anthropocene-enrichment-plan.md) |
| JAXA physical atmosphere | [Cloud-atmosphere implementation](cloud-atmosphere-implementation-notes.md) |
| Network swarm and infrastructure | [Network swarm](network-swarm-implementation-notes.md) and [network infrastructure](network-infrastructure-implementation-notes.md) |
| Cleaned submarine-fiber union | [Fiber Synthesized implementation](fiber-synthesized-implementation-notes.md) |
| Bathymetry art systems | [Bathymetry Roulette](bathymetry-roulette-implementation-notes.md) and [Bathymetry Hamonshū](bathymetry-hamonshu-implementation-notes.md) |

## Projection mathematics

Each projection has context, implementation, and source documents. Its
32-pass contact sheet provides a visual test across very different data and
path structures.

| Projection | Context | Implementation | Sources | Contact sheet |
| --- | --- | --- | --- | --- |
| AuthaGraph | [Context](authagraph-context.md) | [Notes](authagraph-implementation-notes.md) | [Bibliography](authagraph-bibliography.md) | [32 passes](generated-snapshot-authagraph.md) |
| Cahill–Keyes | [Context](cahill-keyes-context.md) | [Notes](cahill-keyes-implementation-notes.md) | [Bibliography](cahill-keyes-bibliography.md) | [32 passes](generated-snapshot-ck.md) |
| Dymaxion | [Context](dymaxion-context.md) | [Notes](dymaxion-implementation-notes.md) | [Bibliography](dymaxion-bibliography.md) | [32 passes](generated-snapshot-dymaxion.md) |
| Myriahedral | [Context](myriahedral-context.md) | [Notes](myriahedral-implementation-notes.md) | [Bibliography](myriahedral-bibliography.md) | [32 passes](generated-snapshot-myriahedral.md) |
| Star-X | [Context](star-x-context.md) | [Notes](star-x-implementation-notes.md) | [Bibliography](star-x-bibliography.md) | [32 passes](generated-snapshot-star-x.md) |
| Icosahedral Voronoi | [Context](voronoi-context.md) | [Notes](voronoi-implementation-notes.md) | [Bibliography](voronoi-bibliography.md) | [32 passes](generated-snapshot-voronoi.md) |

## Browser and embedding

| Need | Documentation |
| --- | --- |
| Use all six projections in WebAssembly, workers, SVG, Canvas, or D3 | [WebAssembly quick start](pages/webassembly-quick-start.md) and [runtime reference](../src.wasm/README.md) |
| Use structured forward points and face-qualified reverse candidates | [Forward/reverse projection API](forward-reverse-projection-api.md) |
| Understand the Stage 10 browser architecture and checks | [Stage 10 WebAssembly notes](pages/stage-10-webassembly.md) |
| Follow a raster-backed overlay workflow | [Web workflow](web-workflow.md) and [complete example](web-example.md) |
| Inspect the immutable generated release without checking it into Git | [Visual gallery](gallery.md), [S3 v13 contract](releases/s3-v13.md), and [release marker](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/release.json) |

## Releases and preservation

| Need | Documentation |
| --- | --- |
| Publish a static generated-assets release through the shared AAO interface | [Release runbook](releases/README.md) |
| Inspect v13 paths, formats, metadata, and verification | [S3 v13 publication](releases/s3-v13.md) |
| Read the corrected source and generated-assets release notes | [`v20260808.1`](releases/v20260808.1.md) |
| Review source-data acquisition and attribution | [Natural Earth data note](natural-earth-10m-physical-vectors.md) and the family-specific implementation notes above |
