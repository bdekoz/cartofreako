---
layout: default
title: Equal Earth context
---

# Equal Earth context

[Projection reference](../README.md) · [Implementation](implementation.md) ·
[Sources](bibliography.md) ·
[Stage 16J comparisons](../../../development/20260815_equal-earth-positioning-speculations-v01.md)

Equal Earth is an uninterrupted equal-area pseudocylindrical world-map
projection introduced by Bojan Šavrič, Tom Patterson, and Bernhard Jenny. It
was designed to combine equal-area behavior with a familiar, legible global
outline. The canonical method uses a Greenwich central meridian and is
available in PROJ as `+proj=eqearth`.

Cartofreako uses Equal Earth in Stage 16J as an **exploration-only comparison
method**. It does not replace or silently join the six standard atlas carrier
families. This distinction matters: a method comparison, a centered variant,
and participation in the `#CorrectTheMap` campaign are different claims.
Implementing the equations establishes only the first.

## Intended comparison roles

- Use canonical Equal Earth for global area-aware comparison against a
  Mercator control.
- Use an explicitly labeled central-meridian variant to test positioning and
  layout while holding the equations fixed.
- Use a WGS 84 geographic source preclip for a regional view; do not present
  the fitted panel as a new registered CRS.
- Compare it with AuthaGraph, Dymaxion, Myriahedral, or Cahill–Keyes only when
  data, dimensions, colors, labels, and extent remain controlled.

The Africa-centered Stage 16J variant uses `11.5°E`. It is deliberately
labeled a Cartofreako experiment and **not** EPSG:8857. A change of central
meridian moves the interruption and positional emphasis; it does not change
the Equal Earth equal-area method or prove a change in human interpretation.
