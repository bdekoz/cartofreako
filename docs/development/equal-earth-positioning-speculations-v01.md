---
layout: default
title: Equal Earth positioning and slice speculations v01
experiment_id: equal-earth-positioning-speculations-v01
status: SPECULATIVE_RENDER_COMPLETE
rendered_at: 2026-08-11
lifecycle: exploration-only
evidence_boundary: >-
  Published Equal Earth equations, PROJ 9.6.2, D3 Geo 2.0.1, checked
  Cartofreako source/runtime/fixtures, Natural Earth 1:110m context, and the
  approved Stage 16J comparison brief; no campaign endorsement, measured
  perception outcome, community authorization, or publication authority.
projection_queue:
  - "1: Web Mercator control and canonical Equal Earth, matched full world"
  - "2: canonical and 11.5E-centered Equal Earth with Tissot diagnostics"
  - "3: Africa-Europe WGS 84 source-window slice through three registrations"
  - "4: Equal Earth, AuthaGraph, Dymaxion, and Myriahedral full carriers"
  - "5: full carrier, geographic preclip, registered perspective, and CK native-cell slice"
outputs:
  - path: output/equal-earth-positioning-speculations-v01/01-mercator-equal-earth-full-world.png
    dimensions: 2560x1440
    sha256: 98ccb7c0ae5fe9a3ba9edb7fa7003b46fd21bfa163e2560bfc7572fee75e46e2
  - path: output/equal-earth-positioning-speculations-v01/02-equal-earth-centering-and-tissot.png
    dimensions: 2560x1440
    sha256: 27343fc5c92c02603342a2d15117ad013aa8f633e7055ebd46eb39e84fc14dbf
  - path: output/equal-earth-positioning-speculations-v01/03-africa-europe-source-window.png
    dimensions: 2560x1440
    sha256: 823e588f76ff622f48274d664a9fbe2ca5bdd5fcfa3b2239ba47f8b4902510c0
  - path: output/equal-earth-positioning-speculations-v01/04-cartofreako-full-carrier-alternatives.png
    dimensions: 2560x1440
    sha256: ef1f6e13ab0b435235348cc8bd912eb5b94238712b743ad760ebf0927a2f98c5
  - path: output/equal-earth-positioning-speculations-v01/05-projection-and-slice-strategies.png
    dimensions: 2560x1440
    sha256: 4ac276a78f8afbde5d325526a0a6af15851265e945d5eb49908668e106e2810e
---

# Equal Earth positioning and slice speculations v01

[Development records](README.md) · [Stage 16 ledger](stage-16.md) ·
[Equal Earth implementation](../pages/projections/equal-earth/implementation.md)

These five 2560 × 1440 PNGs implement the Stage 16J one-to-five comparison
queue. They are local research previews. Equal Earth remains outside the six
standard release projections, and none of these files enters `make all`, a
GitHub release, or UCB AAO/S3.

## Recommended one-to-five sequence

| Iteration | Projection and slice | Recommended use | Required caution |
| --- | --- | --- | --- |
| 1 | Web Mercator at its explicit `±85.0511288°` limit beside canonical Greenwich Equal Earth, both full world | Establish the familiar control before discussing area and positioning | Mercator omits the polar caps; do not let familiarity become an unstated quality criterion. |
| 2 | Canonical Equal Earth and the same method centered on `11.5°E`, both full world with identical indicatrices | Isolate centering as the named layout variable and inspect area-preserving shape deformation | The centered variant is not EPSG:8857. Tissot diagnostics test mathematics, not audience response. |
| 3 | One WGS 84 source window, `25°W–60°E, 40°S–75°N`, through Mercator, canonical Equal Earth, and centered Equal Earth | Compare an Africa–Europe regional discussion without changing the source selection | Each panel is fit to its projected extent. It is a source slice, not a newly registered regional CRS. |
| 4 | Canonical Equal Earth, AuthaGraph, Dymaxion, and Myriahedral Afro–Eur–Asia as full carriers | Compare uninterrupted area, rectangular continuity, Fuller interruption, and registered regional topology | Cuts and carrier geometry change together; this is not a single-variable perceptual study. |
| 5 | Equal Earth full, centered Equal Earth geographic preclip, Myriahedral Afro–Eur–Asia registered perspective, and CK `ck-octant-3` native-cell mask | Choose a slice grammar by purpose: planetary, regional source window, interpretive registered perspective, or repeatable native cell | Every sliced delivery needs a full-carrier locator plus seam, cell, source-window, and inverse-behavior metadata. |

### 01 · Matched full-world baseline

![Web Mercator and canonical Equal Earth rendered with a shared source, palette, dimensions, and graticule](../../output/equal-earth-positioning-speculations-v01/01-mercator-equal-earth-full-world.png)

### 02 · Centering and Tissot diagnostics

![Canonical and Africa-centered Equal Earth with matching indicatrices](../../output/equal-earth-positioning-speculations-v01/02-equal-earth-centering-and-tissot.png)

### 03 · Africa–Europe source-window slice

![The same Africa-Europe WGS 84 source preclip rendered through three projection registrations](../../output/equal-earth-positioning-speculations-v01/03-africa-europe-source-window.png)

### 04 · Full-carrier alternatives

![Equal Earth beside AuthaGraph, Dymaxion, and Myriahedral Afro-Eur-Asia](../../output/equal-earth-positioning-speculations-v01/04-cartofreako-full-carrier-alternatives.png)

### 05 · Projection and slice strategies

![Full, geographic-preclip, registered-perspective, and native-cell slice roles](../../output/equal-earth-positioning-speculations-v01/05-projection-and-slice-strategies.png)

## Numerical and evidence controls

The implementation-neutral bundle under
[`fixtures/projections/equal-earth-v1/`](../../fixtures/projections/equal-earth-v1/)
contains 30 cases across canonical and `11.5°E` layouts. PROJ and D3 are
recorded as cross-implementation oracles. C++ and JavaScript consume the same
neutral raw/page contract, and the offline checker adds forward/reverse,
outside-carrier, seam, pole, Jacobian, local-scale, angular-deformation,
Tissot, and spherical area-scale diagnostics.

The Mercator plate is a control only. The Equal Earth plates demonstrate an
implemented equal-area method and explicit centering alternatives; they do
not establish compliance with `#CorrectTheMap`, correction of human bias, a
decolonial outcome, or a preferred projection for every task. Those require
campaign criteria and participatory human evaluation beyond Stage 16J.

## Reproduce headlessly

```sh
make check-equal-earth-projection
make render-equal-earth-positioning-v01
```

The renderer uses checked local 1:110m geometry, the dedicated Equal Earth
module, the six-family WebAssembly runtime for comparison carriers, GDAL for
the regional source preclip, Inkscape for rasterization, and ImageMagick for
stable PNG metadata. It performs no network access, acquisition,
authorization, email, release, upload, or external transfer.

`make all-experiments` includes this renderer because its five products are
implemented and non-release. Promotion remains a separate human decision.
