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
| **Standard** | Reproducible without a credential or special acceptance, part of the default artifact graph, and represented in the public galleries |
| **Optional** | Implemented but gated by a credential, license acceptance, source availability, or deliberate operator authorization |
| **Exploration only** | Evaluated or proposed without a released production artifact; absence from a release is intentional |

Lifecycle and maturity are independent. Lifecycle controls what is generated
and released; maturity describes the present review disposition of that
design. **Accepted experimental** means the current visual and research
implementation is accepted for ongoing standard use while its methods,
sources, or interpretation may still be revised. It does not mean
exploration-only, and it does not broaden an evidence claim.

The machine-readable [current pass-status manifest](../../../contracts/pass-status-v1.json)
classifies `anthropocene`, `anthropocene-temperature-2025`, and
`anthropocene-temperature-2026` as current, standard, default-generated, and
accepted-experimental. `make check-pass-status` verifies all 18 projection
artifacts against the standard manifest.

## Pass families

- [Astronomy and observer instruments](astronomy.md)
- [Orbital Technosphere](orbital-technosphere.md)
- [Anthropocene](anthropocene/implementation.md), its [source expansion](anthropocene/source-expansion-stage-13.md), and [enrichment plan](anthropocene/enrichment-plan.md)
- [Cloud-atmosphere](cloud-atmosphere.md)
- [Resources](resources/implementation.md), [metric catalog](resources/metric-catalog.md), and [enrichment plan](resources/enrichment-plan.md)
- [Network swarm](network-swarm.md), [network infrastructure](network-infrastructure.md), and [Fiber Synthesized](fiber-synthesized.md)
- [Bathymetry Roulette](bathymetry/roulette.md) and [Bathymetry Hamonshū](bathymetry/hamonshu.md)
