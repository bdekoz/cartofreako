# Stage 14 generation convergence

[Documentation index](../index.md) ·
[Forward/reverse projection API](forward-reverse-projection-api.md) ·
[WebAssembly quick start](pages/webassembly-quick-start.md) ·
[Stage 13 implementation ledger](converge-generation-13.md) ·
[Release runbook](releases/README.md)

## Purpose and boundary

Stage 14 begins with the post-v13 projection-runtime work on 2026-08-09. Its
first development objective is a stable, headless forward/reverse projection
API for native C++ and JavaScript consumers. Stage 14 does not alter the
geometry command-buffer protocol: runtime API 2 deliberately retains geometry
ABI 1 so existing render consumers remain compatible.

This document is the Stage 14 working plan and implementation ledger. It will
record changes as they land, the evidence used to verify them, and the
remaining release gates. A checked item means its scoped implementation is in
the working tree; it does not by itself mean that the eventual v14 release has
been built or published.

## Plan

- [x] Define a versioned structured forward/reverse contract without changing
  geometry ABI 1.
- [x] Implement structured native forward projection, including native-cell
  and component identity.
- [x] Implement analytic, face-qualified reverse projection for all six
  Myriahedral layouts and Voronoi.
- [x] Implement octant-qualified Cahill–Keyes reverse projection across every
  piecewise construction zone, seam, hemisphere, and pole convention.
- [x] Return explicit reverse outcomes rather than guessing across cuts:
  `unique`, `ambiguous`, `outside`, `cut`, and `unsupported`.
- [x] Expose the same contract through WebAssembly, the JavaScript wrapper,
  module worker, D3 adapter, and TypeScript declarations.
- [x] Add native exhaustive-face, JavaScript, worker, D3, and headless-browser
  coverage.
- [x] Raise dense resource and Anthropocene temperature fields to 60% opacity
  while retaining the established 2× primary-title scale.
- [x] Finish focused native and WebAssembly verification for the implemented
  API 2 capability set after the final numerical review.
- [ ] Review the three remaining reverse families in this order: Dymaxion,
  AuthaGraph, then Star-X. Until implemented, each must continue
  to advertise `inverseMode: "none"` and return `unsupported`.
- [ ] Run the repository-wide full check only at the established release gate.
- [ ] Freeze final source identity, generated manifest, checksums, publication
  evidence, and Active Archive record for the eventual v14 release.

## Change ledger

### 2026-08-09 — projection runtime API 2

Status: **implemented and focused checks passing**.

Native runtime changes:

- added separately versioned runtime API 2 while retaining geometry ABI 1;
- introduced structured geographic/projected coordinates, forward results,
  inverse candidates, inverse options, inverse results, and batch calls;
- made every forward result carry its native cell and component identity;
- added analytic Myriahedral and Voronoi inverse solvers that enumerate or
  honor a caller-supplied native face, forward-check every candidate, and
  report boundary ambiguity explicitly;
- rejected non-finite coordinates and unsafe options at the public boundary;
  and
- preserved honest capability discovery for projection families that do not
  yet have reverse implementations.

JavaScript-consumer changes:

- extended the WebAssembly binding and ES-module wrapper with `forward`,
  `forwardMany`, `inverse`, and `inverseMany`;
- added the documented `runtime.projection({ name, frame })` constructor while
  retaining `createProjection` compatibility;
- made axes, input order/domain, units, native aspect, cut topology, and
  reverse capability explicit in a deeply immutable projection manifest;
- added packed typed-array batch inverse results suitable for headless and
  agentic workflows;
- propagated the contract through the module worker and worker client;
- exposed candidate-aware D3 inversion without silently choosing a face at a
  cut; and
- added checked TypeScript declarations in
  `src.wasm/cartofreako-web.d.ts`.

Documentation changes:

- added the [forward/reverse API specification](forward-reverse-projection-api.md);
- updated the [WebAssembly quick start](pages/webassembly-quick-start.md),
  [WebAssembly architecture record](pages/stage-10-webassembly.md), native and
  browser runtime READMEs, the main README, and documentation indexes; and
- recorded the post-v13 development boundary in the Stage 13 ledger while
  assigning the ongoing work to this Stage 14 ledger.

Build compatibility changes:

- migrated projection-runtime, slicing, and generator includes from the
  removed `a60-svg.h` compatibility shim to canonical `izzi-svg.h`; and
- retained Izzi as an explicit build dependency without introducing a local
  compatibility copy.

### 2026-08-10 — Cahill–Keyes reverse support

Status: **implemented; focused verification passing**.

- added an octant-qualified native inverse to the authoritative scalable
  Cahill–Keyes construction;
- exactly undid the M-layout translation, rotation, and southern reflection
  before solving within one canonical half-octant;
- used a zone-aware bounded numerical search across the 29°/30° meridian and
  15°/73°/75° parallel transitions, followed by forced-octant forward-residual
  acceptance;
- reversed the one-degree raster registration and retained explicit
  equator/outer-meridian/pole boundary semantics;
- promoted Cahill–Keyes metadata from `inverseMode: "none"` to
  `inverseMode: "face-qualified"` without changing runtime API 2 or geometry
  ABI 1;
- extended native coverage to 1,560 interior zone samples, 16 registered seam
  probes, all eight qualified pole copies, batches, outside points, and direct
  native compatibility anchors; and
- extended Node, D3, main-thread browser, and module-worker coverage through
  the existing projection-neutral surface.

The polar longitude returned for a qualified cell is deliberately the center
of that octant. Latitude and residual remain authoritative at the pole;
longitude is a stable representative because every meridian converges there.

### Headless execution and consent

The Stage 14 API and its checks are designed to run without a display,
interactive prompts, network access, credentials, publication, or external
side effects. The operator has authorized headless focused verification. That
authorization does not publish a release and does not collapse the explicit
repository-wide full-check gate.

## Visual hierarchy and opacity

Stage 14 applies a common rule to dense resource and temperature data: keep
the base geography legible by limiting the observed field to 60% opacity, and
double the primary plate title without changing its wording or evidence
metadata.

The source profiles, native defaults, generator assertions, and focused tests
now agree on `data_graphic_opacity = 0.60` for all resource plates and the
2025/2026 Anthropocene temperature fields. Bathymetry art passes retain their
separately documented 30% opacity because their filled curve fields follow a
different visual system. Immutable v12 and v13 assets are not rewritten; the
60% rule applies to newly generated Stage 14 output.

## Verification ledger

| Check | Scope | Current result |
| --- | --- | --- |
| `make check-forward-reverse-projection-api` | Native API, 1,560 Cahill–Keyes zone samples plus seams/poles, all 30,720 Myriahedral face centers, all 20 Voronoi face centers, batches, boundary status, unsupported paths, and invalid input | Passed 2026-08-10 with Cahill–Keyes enabled |
| Native projection-runtime regression | Geometry ABI 1 and runtime API 2 coexistence | Passed 2026-08-10 |
| `make wasm-projections` | Rebuild bindings and browser distribution | Passed 2026-08-10 with Emscripten warnings treated as errors |
| `make check-wasm-projections` | Node API, immutable metadata, typed-array batches, Cahill–Keyes/Myriahedral D3, and single/batch reverse | Passed 2026-08-10 |
| `make check-wasm-projections-browser` | Headless Chrome API 2 plus main-thread and worker Cahill–Keyes reverse | Passed 2026-08-10; its temporary server was restricted to loopback |
| `make check-wasm-cahill-keyes check-wasm-cahill-myriahedral` | Legacy compatibility modules after canonical Izzi include migration | Passed 2026-08-10 |
| Focused UBSan builds | Native Cahill–Keyes anchors and complete projection-neutral reverse campaign at `-O2` | Passed 2026-08-10 |
| Static syntax and `git diff --check` | Module syntax and patch hygiene | Passed 2026-08-10 |
| Resource and temperature generator tests | 60% observed fields, 2× titles, metadata, and profile validation | Passed 2026-08-09 |
| Resource checksum manifest | Source-profile digest after the 60% change and all pinned resource payloads | Passed 2026-08-09 |
| Repository-wide `make check` | Full project release gate | Deliberately not run yet |

## Release completion criteria

Stage 14 is ready to freeze only when:

1. every advertised reverse capability passes native and WebAssembly checks;
2. unsupported families remain mechanically and visibly unsupported;
3. all generated projection/pass manifests agree with the documented standard,
   optional, and exploration-only classifications;
4. the full repository check passes at the authorized release gate;
5. the projection-organized archive, S3 browser tree, PNG previews, viewer,
   completion marker, and download verification agree on one immutable
   inventory; and
6. the canonical Devastation Pacific Active Archive check-in report records
   the exact uploaded object identity and is delivered through the shared
   headless archive workflow.

## Deferred decisions

Reverse support for Dymaxion, AuthaGraph, and Star-X is not
simulated by numerical guessing. Each needs a family-specific inverse,
candidate enumeration at seams, forward-residual validation, exhaustive
boundary fixtures, and an explicit capability upgrade. Star-X additionally
needs component-aware treatment of its four-way composition and unified
Antarctic cap; its carrier stage can now build on the checked Cahill–Keyes
reverse, but the compositor still needs separate semantics.
