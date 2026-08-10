# Stage 14 generation convergence

[Documentation index](../../../index.md) ·
[Forward/reverse projection API](../runtime/projection-api.md) ·
[AI-agent and 1080p gaming follow-on](../runtime/ai-agent-and-1080p-gaming.md) ·
[WebAssembly quick start](../runtime/webassembly-quick-start.md) ·
[Stage 13 implementation ledger](stage-13.md) ·
[Release runbook](../releases/README.md)

## Purpose and boundary

Stage 14 begins with the post-v13 projection-runtime work on 2026-08-09. Its
first development objective is a stable, headless forward/reverse projection
API for native C++ and JavaScript consumers. Stage 14 does not alter the
geometry command-buffer protocol: runtime API 3 deliberately retains geometry
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
- [x] Finish focused native and WebAssembly verification for the complete
  API 3 capability set after the final numerical review.
- [x] Freeze the current Star-X composition as a projection-only fixed-`60°S`
  cap, retain visible proportional lower clearance, remove its Natural Earth
  registration dependency, and document the component-qualified inverse plan.
- [x] Implement and verify the three remaining reverse families in this order:
  Dymaxion, AuthaGraph, then component-aware Star-X.
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

- added the [forward/reverse API specification](../runtime/projection-api.md);
- updated the [WebAssembly quick start](../runtime/webassembly-quick-start.md),
  [WebAssembly architecture record](../runtime/webassembly-architecture.md), native and
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

### 2026-08-10 — current Star-X cap specification

Status: **implemented; focused native and visual verification passing**.

- made `60°S`, zero cap-bearing rotation, quarter-degree boundary sampling,
  and `0.25/44` lower clearance named projection constants;
- derived the unified-cap pole from the projected boundary alone, removing the
  Natural Earth mainland extent scan and the graticule target's Natural Earth
  prerequisite;
- registered the bottommost boundary point at `H - H(0.25/44)`, which is
  `43.75` on the 34-by-44 SVG and keeps its blue edge within the view box;
- retained the existing radius-preserving geographic-bearing transform and
  topmost per-layer paint order;
- regenerated and visually inspected the Star-X graticule and Earth plate,
  and generated the graticule successfully with a deliberately nonexistent
  Natural Earth directory; and
- specified separate carrier and cap reverse paths, both with forward-residual
  checks and explicit component/cut/pole ambiguity.

Natural Earth remains a source of physical feature geometry for Earth and
water plates. It no longer chooses any Star-X cutoff or placement parameter.

### 2026-08-10 — complete all-family reverse, runtime API 3

Status: **implemented; native, Node, worker, D3, and browser checks passing**.

- completed the exact Gray-transform reverse for all 23 Dymaxion registered
  faces/subfaces, including the Australia and Japan split registrations;
- completed the analytic AuthaGraph inverse across all 24 tetrahedral sectors,
  enumerating periodic page copies and preserving singular-vertex and sector
  boundary candidates;
- implemented the Star-X ordinary-carrier reverse by undoing enlargement,
  group placement, and the upper-group rotation before invoking the checked
  Cahill–Keyes inverse;
- implemented the Star-X unified-cap reverse by recovering geographic bearing
  and solving latitude in `[-90°,-60°]` against the authoritative source-radius
  function;
- made the structured Star-X forward use carrier component `0` north of the
  cutoff and cap component `1` at or south of it, while retaining the direct
  `starxproj` ordinary-carrier transform used by composition code;
- defined deterministic cut behavior at `60°S` and registered quadrant
  meridians, plus four face-qualified representative longitudes at the
  otherwise longitude-indeterminate South Pole;
- added the optional `component` inverse qualifier and `componentCount`
  metadata, promoting the point contract to runtime API 3 while leaving
  geometry ABI 1 unchanged;
- promoted AuthaGraph and Dymaxion to `inverseMode: "face-qualified"` and
  Star-X to `inverseMode: "candidates"`; every current registered projection
  layout now advertises reverse support; and
- propagated API 3 through Embind, the ES-module wrapper, module workers, D3,
  packed batches, TypeScript declarations, Node checks, and headless Chrome.

The inverse implementation is family-specific rather than one generic
numerical guess. Every candidate is forced through its selected forward
transform and rejected when its pixel residual exceeds the caller's tolerance.

### Headless execution and consent

The Stage 14 API and its checks are designed to run without a display,
interactive prompts, network access, credentials, publication, or external
side effects. The operator authorized this completion run to perform focused,
sanitizer, browser, and repository-wide local verification without another
prompt. That authorization does not publish a release, upload assets, or alter
an external service.

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
| `make check-forward-reverse-projection-api` | Native API, 1,560 Cahill–Keyes zone samples plus seams/poles, all 24 AuthaGraph sectors and four singular vertices plus a global lattice, all 23 Dymaxion faces/subfaces plus a global lattice and edge cut, all 30,720 Myriahedral face centers, all 20 Voronoi face centers, Star-X carrier/cap/cut/overlap/pole behavior, three additional frame scales, batches, outside states, and invalid qualifiers | Passed 2026-08-10 for all six families |
| Native projection-runtime regression | Geometry ABI 1 and runtime API 3 coexistence | Passed 2026-08-10 |
| `make wasm-projections` | Rebuild bindings and browser distribution | Passed 2026-08-10 with Emscripten warnings treated as errors |
| `make check-wasm-projections` | Node API 3, immutable component metadata, all-family single/batch reverse, typed arrays, Star-X cap/pole/component behavior, and D3 candidates | Passed 2026-08-10 |
| `make check-wasm-projections-browser` | Headless Chrome API 3 plus main-thread and module-worker reverse, including the Star-X cap | Passed 2026-08-10; its temporary server was restricted to loopback |
| `make check-wasm-cahill-keyes check-wasm-cahill-myriahedral` | Legacy compatibility modules after canonical Izzi include migration | Passed 2026-08-10 |
| Focused UBSan/ASan builds | Complete all-family projection-neutral reverse campaign; UBSan at `-O2`, ASan at `-O1` | Passed 2026-08-10; leak detection was disabled only because LeakSanitizer cannot run under the executor's ptrace boundary |
| Static syntax and `git diff --check` | Module syntax and patch hygiene | Passed 2026-08-10 |
| Resource and temperature generator tests | 60% observed fields, 2× titles, metadata, and profile validation | Passed 2026-08-09 |
| Resource checksum manifest | Source-profile digest after the 60% change and all pinned resource payloads | Passed 2026-08-09 |
| `tests/test-star-x-projection-api` plus regenerated graticule/Earth | Fixed cutoff/bearing, projection-only registration (including a no-Natural-Earth smoke run), proportional lower clearance, complete in-frame boundary, topmost land composition, and visual unclipping | Passed 2026-08-10 |
| Repository-wide `make check` | Full projection, generator, data-integrity, authorization, resources, atmosphere, astronomy, network, bathymetry, slicing, and runtime gate | Passed 2026-08-10 after replacing two stale pre-Izzi bathymetry curve include names with their canonical Izzi headers |

## Release completion criteria

Stage 14 is ready to freeze only when:

1. every advertised reverse capability passes native and WebAssembly checks;
2. every current registered family remains mechanically reversible, with
   candidate/component ambiguity explicit rather than silently collapsed;
3. all generated projection/pass manifests agree with the documented standard,
   optional, and exploration-only classifications;
4. the full repository check passes at the authorized release gate;
5. any independently authorized generated-assets deposit has a
   projection-organized archive, S3 browser tree, PNG previews, viewer,
   completion marker, and download verification that agree on one immutable
   inventory; and
6. any such UCB AAO deposit produces the canonical Devastation Pacific Active
   Archive check-in report through the shared headless archive workflow.

## Remaining release work

The all-family reverse implementation is complete. The Stage 14 source is
released on GitHub independently of generated-asset preservation. A later v14
UCB AAO deposit is not part of that source release: it requires its own frozen
generated manifest, reviewed profile, human invocation of
`make release-ucb-aao-s3`, immutable inventory verification, and canonical
Active Archive check-in record. `make release-github` cannot reach that target.

## Post-release consumer follow-on

Runtime API 3 completes the reverse-projection foundation identified by the
special-topics audit. The separate
[AI-agent and 1080p gaming improvement plan](../runtime/ai-agent-and-1080p-gaming.md)
turns the remaining JavaScript/catalog and gaming recommendations into phased,
testable work. Its screen derivatives are additive and cannot alter the
authoritative SVG/PDF archive and art objects, projection-specific 44-inch or
A0 inkjet workflows, 3840-pixel raster, or print-generation contracts.

### 2026-08-10 — 1080p consumer and agent catalog v1

Status: **implemented as a bounded 24-artifact audit canary; focused checks
passing**.

- added exact 1920 × 1080 contain-fit PNG and lossless-WebP derivatives for
  Water, Anthropocene Temperature 2026, Network Infrastructure Sites, and
  Bathymetry Roulette across all six reference projection families;
- retained the projection-specific whole-map ratio without crop or stretch,
  using declared `#f4f5f5` letterbox/pillarbox padding;
- added the checked `cartofreako-artifacts-v1` schema and generated catalog,
  with parent SVG/PDF/full-PNG hashes, authority classes, source revision,
  content rectangles, and both affine matrices;
- added projection-to-screen, padding-aware screen-to-projection, and
  candidate-preserving screen-to-geographic APIs plus TypeScript declarations;
- added a dependency-free flat texture-plane record suitable for Three.js or
  raw WebGL while explicitly rejecting equirectangular-sphere treatment;
- added a runnable exact-1080p Canvas example and extended headless Chrome to
  cover all six families, affine picks, no-crop layout, and the flat plane;
- verified decoded PNG/WebP pixel equality and re-hashed every authoritative
  parent after derivative generation; and
- kept all consumer targets out of `make all`, GitHub release, and UCB AAO/S3
  publication paths.

`make generate-screen-1080p` produces the bounded set;
`make check-screen-1080p` validates its files, catalog, transforms, and picks;
`make consumer-assets-v1` also runs the browser canary. Extending the catalog
to every standard pass, perspective, and approved slice remains a separate
promotion gate. KTX2, semantic masks, engine-specific importers, and a
collaborator clean-room run remain `UNAVAILABLE`.

The systematic round-trip audit adds 46,656 face/component-qualified interior
samples: 2,592 points × six families × three frame scales. All candidates
returned and all statuses were unique on the deliberately seam-avoiding grid.
The maximum spherical error was approximately `1.22e-10°` for the bounded
numerical Cahill–Keyes solver and its Star-X carrier, and approximately
`4.20e-13°` or less for the analytic families. These round trips are strong
implementation consistency evidence, not independent mathematical proof;
published anchors, exact seams, poles, face centers, and retained-hinge tests
remain necessary independent/structural evidence.
