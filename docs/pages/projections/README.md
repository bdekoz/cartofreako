---
layout: default
title: Projection reference
---

# Projection reference

[Documentation index](../README.md) · [Visual gallery](../gallery/README.md) ·
[Forward/reverse API](../runtime/projection-api.md)

Each projection family keeps its mathematical context, implementation
contract, sources, and visual contact sheet together.

Equal Earth is currently a Stage 16J exploration-only comparison method. Its
standalone forward/reverse API and five comparison plates do not add a seventh
standard runtime or release projection.

Runtime API 3 implements forward and candidate-aware reverse support for all
six families. Cuts, duplicated edges, poles, and Star-X carrier/cap overlap
remain explicit candidates rather than being forced into a false unique
answer. See the [portable fixtures and independent reverse oracles](../runtime/projection-fixtures.md).

| Projection | Context | Implementation | Sources | Contact sheet |
| --- | --- | --- | --- | --- |
| AuthaGraph | [Context](authagraph/context.md) | [Implementation](authagraph/implementation.md) | [Sources](authagraph/bibliography.md) | [Gallery](../gallery/authagraph.md) |
| Cahill–Keyes | [Context](cahill-keyes/context.md) | [Implementation](cahill-keyes/implementation.md) | [Sources](cahill-keyes/bibliography.md) | [Gallery](../gallery/cahill-keyes.md) |
| Dymaxion | [Context](dymaxion/context.md) | [Implementation](dymaxion/implementation.md) | [Sources](dymaxion/bibliography.md) | [Gallery](../gallery/dymaxion.md) |
| Myriahedral | [Context](myriahedral/context.md) | [Implementation](myriahedral/implementation.md) | [Sources](myriahedral/bibliography.md) | [Gallery](../gallery/myriahedral.md) |
| Star-X | [Context](star-x/context.md) | [Implementation](star-x/implementation.md) | [Sources](star-x/bibliography.md) | [Gallery](../gallery/star-x.md) |
| Icosahedral Voronoi | [Context](voronoi/context.md) | [Implementation](voronoi/implementation.md) | [Sources](voronoi/bibliography.md) | [Gallery](../gallery/voronoi.md) |
| Equal Earth *(exploration only)* | [Context](equal-earth/context.md) | [Implementation](equal-earth/implementation.md) | [Sources](equal-earth/bibliography.md) | [Five Stage 16J comparisons](../../development/equal-earth-positioning-speculations-v01.md) |
