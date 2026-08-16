---
layout: default
title: Equal Earth implementation
---

# Equal Earth implementation

[Context](context.md) · [Sources](bibliography.md) ·
[Portable fixtures](../../runtime/projection-fixtures.md) ·
[Stage 16J comparisons](../../../development/equal-earth-positioning-speculations-v01.md)

Stage 16J supplies the spherical Equal Earth forward and reverse equations in
the standalone C++ header
[`cart0freak0-equal-earth.h`](../../../../src.projections/cart0freak0-equal-earth.h)
and the dependency-free JavaScript module
[`equal-earth.mjs`](../../../../scripts/equal-earth.mjs). Both expose raw
radian-space operations and full-carrier, top-left normalized page mapping.
The C++ page wrapper returns `unique` or `outside`; this uninterrupted method
does not need the face-qualified candidate sets used by interrupted
Cartofreako carriers.

The implementation uses the published coefficients:

```text
A1 =  1.340264
A2 = -0.081106
A3 =  0.000893
A4 =  0.003796
M  = sqrt(3) / 2
```

For longitude `lambda`, latitude `phi`, and
`theta = asin(M sin(phi))`, the forward equations are:

```text
x = lambda cos(theta) /
    (M (A1 + 3 A2 theta² + theta⁶ (7 A3 + 9 A4 theta²)))
y = theta (A1 + A2 theta² + theta⁶ (A3 + A4 theta²))
```

Reverse projection solves `theta` from `y` with at most 12 Newton steps,
then reconstructs longitude and latitude. Unit-domain clamps apply only at
the inverse trigonometric boundary. A page point is accepted only when its
reconstructed longitude remains within the selected antimeridian and its
forward residual returns to the requested page point. Page corners outside
the curved carrier are therefore `outside`, not silently clamped to land.
The two page edges are duplicate representations of the selected
antimeridian. Reverse projection accepts both and reports the same canonical
longitude; its residual check recognizes the equivalent opposite edge
without relaxing interior-point validation.

## Checked numerical evidence

Run:

```sh
make check-equal-earth-projection
```

The offline gate validates 30 neutral cases in two layouts through C++ and
JavaScript. The frozen cross-implementation observations use PROJ 9.6.2 and
D3 Geo 2.0.1. On the development run:

- the maximum PROJ-to-D3 raw-coordinate difference was
  `7.021666937153402e-16`;
- the maximum JavaScript-to-fixture raw difference was the same;
- the maximum forward/reverse angular difference was
  `2.842170943040401e-14°`; and
- the maximum finite-difference spherical area-scale error over 35 diagnostic
  samples was `1.203175781228083e-9`.

These are implementation diagnostics, not a claim about survey accuracy,
ellipsoidal geodesy, campaign compliance, or human perception. The diagnostic
report is generated locally at
`build/stage-16j/equal-earth-diagnostics.json`.

## Runtime boundary

Equal Earth intentionally remains outside `projection_kind`, runtime API 3,
the standard artifact manifest, `make all`, print generation, GitHub release,
and UCB AAO/S3 publication. Stage 16J uses it through a dedicated API and
comparison renderer so implementing a research control cannot mutate the
six-family release corpus by accident. Promotion would require a separate
runtime/API, pass-matrix, gallery, print, and lifecycle decision.
