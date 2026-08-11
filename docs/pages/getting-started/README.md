---
layout: default
title: Build and generate
---

# Build and generate

[Documentation index](../README.md) · [Visual gallery](../gallery/README.md)

Start with the [prerequisites](prerequisites.md), then use the
[generation guide](generation.md) for the standard or configured artifact
graphs. The [generation methods record](generation-methods.md) explains pass
selection, exact targets, family targets, and the evidence used to decide
which products belong in a release.

Optional external products are not implied by `make all`. Authorize their
sources first, then use the configured external-generation entry point
documented in the generation guide.

Local-only research builders are separately enumerated by
`make list-experiments` and `make all-experiments`. That aggregate never
fetches data, authorizes a provider, benchmarks hardware, promotes a pass,
publishes GitHub, or uploads UCB AAO/S3 assets.
