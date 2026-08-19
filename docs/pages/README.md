---
layout: default
title: Cartofreako technical documentation
---

# Technical documentation

Use the [visual gallery](gallery/README.md) to browse the release first. This page is
the compact route into building, projection mathematics, pass semantics,
browser integration, verification, and preservation.

The gallery is the sealed v14 AAO release: 217 standard products across 33
pass IDs, including the Network Groundstations pass and the dual-year
Anthropocene particulate/temperature families. Current source development may
be newer, and Stage 15/16 research products remain local; those changes are
documented here without claiming they have been uploaded into the immutable
v14 prefix.

## Start, build, and generate

| Need | Documentation |
| --- | --- |
| Install compilers, libraries, data tools, and optional WebAssembly support | [Prerequisites](getting-started/prerequisites.md) |
| Generate SVG, PDF, PNG, thumbnails, slices, and projection families | [Generation guide](getting-started/generation.md) |
| Understand the selected profile, pass evaluation, and exact versus family workflows | [Generation methods and decision record](getting-started/generation-methods.md) |
| Review the complete Stage 13 development manifest | [Stage 13 convergence notes](../development/stage-13.md) |
| Follow the Stage 14 plan, implementation changes, and verification evidence | [Stage 14 convergence ledger](../development/stage-14.md) |
| Review the closed GPU controls, Majuro full pass, and Anthropocene experiments | [Stage 15 closed ledger](../development/stage-15.md), [atoll report](../../reports/stage-15-atoll-evidence-canary.md), and [water-debris report](../../reports/stage-15-water-debris-feasibility.md) |
| Plan compressed GPU evidence, additional consumers, atoll expansion, and agentic research iteration | [Stage 16 development ledger](../development/stage-16.md) |
| Inspect the implemented Equal Earth control, Africa-centered variant, and one-to-five slice queue | [Stage 16J positioning comparisons](../development/equal-earth-positioning-speculations-v01.md) |
| Authorize and generate credentialed external products | [Configured generation](getting-started/generation.md#configured-development-generation), [Cloud-atmosphere generation](getting-started/generation.md#cloud-atmosphere-generation), and [P-Tree production download](data/ptree-download.md) |

## Pass catalog and lifecycle

The [resources metric catalog](passes/resources/metric-catalog.md) is the visible
index of all 59 resource metrics. It states both subject meaning and release
status; [`resources-profile.json`](../../assets.static/resources/resources-profile.json)
is the machine-readable authority.

| Class | Meaning |
| --- | --- |
| **Standard pass** | Reproducible without a credential or special acceptance, included in `make all`, and eligible for the next generated-assets release. A sealed older gallery may have a different standard composition. |
| **Optional pass** | Implemented but deliberately gated by credentials, license acceptance, or an operator decision. Authorization makes it eligible for subsequent configured generation. |
| **Exploration only** | Cataloged, proposed, or source-tested without a released production output. It is not silently generated and is not a missing release artifact. |

The current resource profile has 14 standard passes, no optional resource
passes, and 45 exploration-only metrics. Project-wide optional products include
the credentialed P-Tree Cloud-atmosphere pass and licensed network topology;
NASA FIRMS remains an exploration input rather than a released optional pass.
Pass maturity is a separate axis: the four current dual-year Anthropocene pass
IDs are standard and default-generated with **accepted-experimental**
maturity. The synthetic PurpleAir interface, bounded water-debris, and Majuro
evidence products remain exploration-only. See
the [generation-pass overview](passes/README.md) and machine-readable
[pass-status manifest](../../contracts/pass-status-v1.json).

| Family | Documentation |
| --- | --- |
| Energy, food, fauna, flora, mineral, and human resources | [Stage 12 resource implementation](passes/resources/implementation.md), [metric catalog](passes/resources/metric-catalog.md), and [enrichment plan](passes/resources/enrichment-plan.md) |
| Astronomy and observer instruments | [Astronomy implementation](passes/astronomy.md) |
| Orbital Technosphere | [Orbital Technosphere implementation](passes/orbital-technosphere.md) |
| Climate, weather, fire, smoke, and air quality | [Anthropocene implementation and accepted-experimental status](passes/anthropocene/implementation.md), [source expansion](passes/anthropocene/source-expansion-stage-13.md), and [enrichment plan](passes/anthropocene/enrichment-plan.md) |
| JAXA physical atmosphere | [Cloud-atmosphere implementation](passes/cloud-atmosphere.md) |
| Network swarm and infrastructure | [Network swarm](passes/network-swarm.md) and [network infrastructure](passes/network-infrastructure.md) |
| Cleaned submarine-fiber union | [Fiber Synthesized implementation](passes/network-fiber.md) |
| Bathymetry art systems | [Bathymetry Roulette](passes/bathymetry/roulette.md) and [Bathymetry Hamonshū](passes/bathymetry/hamonshu.md) |

## Projection mathematics

Each projection has context, implementation, and source documents. Its
33-pass contact sheet provides a visual test across very different data and
path structures.

Equal Earth is listed separately as a Stage 16J exploration control; it has
five local comparison plates rather than a standard 33-pass release gallery.

| Projection | Context | Implementation | Sources | Contact sheet |
| --- | --- | --- | --- | --- |
| AuthaGraph | [Context](projections/authagraph/context.md) | [Notes](projections/authagraph/implementation.md) | [Bibliography](projections/authagraph/bibliography.md) | [33 passes](gallery/authagraph.md) |
| Cahill–Keyes | [Context](projections/cahill-keyes/context.md) | [Notes](projections/cahill-keyes/implementation.md) | [Bibliography](projections/cahill-keyes/bibliography.md) | [33 passes](gallery/cahill-keyes.md) |
| Dymaxion | [Context](projections/dymaxion/context.md) | [Notes](projections/dymaxion/implementation.md) | [Bibliography](projections/dymaxion/bibliography.md) | [33 passes](gallery/dymaxion.md) |
| Myriahedral | [Context](projections/myriahedral/context.md) | [Notes](projections/myriahedral/implementation.md) | [Bibliography](projections/myriahedral/bibliography.md) | [33 passes](gallery/myriahedral.md) |
| Star-X | [Context](projections/star-x/context.md) | [Notes](projections/star-x/implementation.md) | [Bibliography](projections/star-x/bibliography.md) | [33 passes](gallery/star-x.md) |
| Icosahedral Voronoi | [Context](projections/voronoi/context.md) | [Notes](projections/voronoi/implementation.md) | [Bibliography](projections/voronoi/bibliography.md) | [33 passes](gallery/voronoi.md) |
| Equal Earth *(exploration only)* | [Context](projections/equal-earth/context.md) | [Notes](projections/equal-earth/implementation.md) | [Bibliography](projections/equal-earth/bibliography.md) | [Five comparisons](../development/equal-earth-positioning-speculations-v01.md) |

## Browser and embedding

| Need | Documentation |
| --- | --- |
| Use all six projections in WebAssembly, workers, SVG, Canvas, or D3 | [WebAssembly quick start](runtime/webassembly-quick-start.md) and [runtime reference](../../src.wasm/README.md) |
| Consume portable numeric cases or compare independent reverse implementations | [Projection fixtures and reverse oracles](runtime/projection-fixtures.md) |
| Check the standalone Equal Earth forward/reverse control and PROJ/D3 oracle bundle | [Equal Earth implementation](projections/equal-earth/implementation.md) and [Stage 16J comparisons](../development/equal-earth-positioning-speculations-v01.md) |
| Select one standard artifact deterministically and retain a decision receipt | [Artifact catalog and selection](runtime/artifact-selection.md) |
| Resolve a published artifact ID to a URL, verify a release, or follow the consumer workflows | [v14 consumer release usage](runtime/consumer-release-usage.md) |
| Use structured forward points and face-qualified reverse candidates | [Forward/reverse projection API](runtime/projection-api.md) |
| Plan machine-readable agent discovery and 1080p/Three.js derivatives without changing archive/art/print masters | [AI Workflows assessment and 1080p gaming improvement plan](runtime/ai-agent-and-1080p-gaming.md) |
| Review the approved Marshall Islands-to-new-experiment agent workflow | [Stage 16 agentic atlas research plan](../development/stage-16.md) |
| Understand the Stage 10 browser architecture and checks | [Stage 10 WebAssembly notes](runtime/webassembly-architecture.md) |
| Follow a raster-backed overlay workflow | [Web workflow](runtime/myriahedral-workflow.md) and [complete example](runtime/myriahedral-example.md) |
| Inspect the immutable generated release without checking it into Git | [Visual gallery](gallery/README.md), [v14 AAO release record](releases/aao-v14.md), and [release marker](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/release.json) |

## Releases and preservation

| Need | Documentation |
| --- | --- |
| Publish a GitHub source release without invoking S3 | [Release runbook](releases/README.md) and [`v20260811`](releases/v20260811.md) |
| Deposit generated assets in UCB AAO through the separate human-invoked S3 target | [Release runbook](releases/README.md) |
| Inspect v14 paths, formats, metadata, and verification | [v14 AAO release record](releases/aao-v14.md) |
| Inspect the historical v13 deposit | [v13 AAO publication](releases/aao-v13.md) |
| Read the corrected source and generated-assets release notes | [`v20260808.1`](releases/v20260808.1.md) |
| Review source-data acquisition and attribution | [Natural Earth data note](data/natural-earth.md) and the family-specific implementation notes above |
