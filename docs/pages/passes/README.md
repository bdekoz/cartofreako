---
layout: default
title: Generation passes
---

# Generation passes

[Documentation index](../README.md) ·
[Resource metric catalog](resources/metric-catalog.md) ·
[Generation guide](../getting-started/generation.md)

Pass documentation records the source, transformation, output, lifecycle
class, visual policy, verification, and scientific or licensing boundary.

| Lifecycle | Meaning |
| --- | --- |
| **Standard** | Reproducible without a credential or special acceptance, part of the default artifact graph, and eligible for the next generated-assets release; sealed older galleries may differ |
| **Optional** | Implemented outside the default artifact graph; includes opt-in prototypes and products gated by credentials, terms or source availability |
| **Exploration only** | Evaluated or proposed without a released production artifact; absence from a release is intentional |

Lifecycle and maturity are independent. Lifecycle controls what is generated
and released; maturity describes the present review disposition of that
design. **Accepted experimental** means the current visual and research
implementation is accepted for ongoing standard use while its methods,
sources, or interpretation may still be revised. It does not mean
exploration-only, and it does not broaden an evidence claim.

The machine-readable [current pass-status manifest](../../../contracts/pass-status-v1.json)
classifies `anthropocene-particulate-2025`,
`anthropocene-particulate-2026`, `anthropocene-land-temperature-2025`, and
`anthropocene-land-temperature-2026` as current, standard, default-generated, and
accepted-experimental. `make check-pass-status` verifies all 24 projection
artifacts against the standard manifest. The synthetic PurpleAir interface,
bounded water-debris, and Majuro evidence families remain exploration-only
despite having implemented generators.

The [November 8 plate catalog](../../../config/atlas-plates.json) contains
**53 named plates: 39 defaults and 14 optional prototypes**. Each default has
World/Japan cartography + graphics sheets and separate legend/source sheets,
giving **156 verified sheets**. It also records
Bathymetry Roulette and Hamonshū as optional prototypes, moves historical
reef threat to Anthropocene, and groups petroleum studies under Energy.
The [water-temperature study](../../development/20261108_anthropocene_ocean_temperature_stage_1.md)
documents the separate SST/anomaly prototypes and the completed mineral additions.
The completed [Stage 2 study](../../development/20261108_anthropocene_ocean_temperature_stage_2.md)
adds the following optional families, each with separate 2025 and 2026 IDs:

| Canonical family (`YYYY` is a four-digit year) | Measure and support |
| --- | --- |
| `anthropocene-marine-heatwave-YYYY` | Persistent seasonal SST exceedance; event days, observed duration and intensity |
| `anthropocene-ocean-thermal-season-YYYY` | Experimental local onset/length measures with explicit open and undefined seasons |
| `anthropocene-coastal-compound-heat-YYYY` | Date-aligned CPC land heat and adjacent-ocean warmth |
| `anthropocene-heat-particulate-coexposure-YYYY` | Date-aligned heat and PM2.5 at selected India monitors; reference and low-cost products remain separate |

Stage 2 has **32 measure/period views and 128 sheets**, plus four scientific
figures. Ocean/coastal views use World/Japan; the India pilot uses World/India.
The 14 prototypes are the eight Stage 2 identities, four Stage 1 water
temperature/anomaly identities and two Bathymetry identities. They remain
outside the 39-pass default atlas. `make all` builds the standard native
projection graph; Stage 2 uses `make prepare-ocean-stage-2`,
`make render-ocean-stage-2` and `make check-ocean-stage-2` with the study's
pinned inputs restored first.

## Pass families

- [Astronomy and observer instruments](astronomy.md)
- [Orbital Technosphere](orbital-technosphere.md)
- [Anthropocene](anthropocene/implementation.md), its [source expansion](anthropocene/source-expansion-stage-13.md), and [enrichment plan](anthropocene/enrichment-plan.md)
- [Cloud-atmosphere](cloud-atmosphere.md)
- [Resources](resources/implementation.md), [metric catalog](resources/metric-catalog.md), and [enrichment plan](resources/enrichment-plan.md)
- [Network swarm](network-swarm.md), [Network CDN](network-infrastructure.md), [Network Fiber](network-fiber.md), and [Network Groundstations](network-groundstations.md)
- [Bathymetry Roulette](bathymetry/roulette.md) and [Bathymetry Hamonshū](bathymetry/hamonshu.md)
