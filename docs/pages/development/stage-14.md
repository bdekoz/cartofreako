# Stage 14 generation convergence

[Documentation index](../../../index.md) ·
[Forward/reverse projection API](../runtime/projection-api.md) ·
[AI-agent and 1080p gaming follow-on](../runtime/ai-agent-and-1080p-gaming.md) ·
[WebAssembly quick start](../runtime/webassembly-quick-start.md) ·
[Stage 13 implementation ledger](stage-13.md) ·
[Stage 15 GPU benchmark ledger](stage-15.md) ·
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
- [x] Run the repository-wide full check for the `v20260810` source-release
  baseline.
- [x] Freeze and publish the core Stage 14 reverse-projection source identity
  independently of generated assets and UCB AAO/S3 preservation.
- [ ] Complete the post-release numerical-evidence, portable-fixture,
  deterministic-selection, and standard-consumer promotion stages below.
- [ ] Stop for explicit operator confirmation before the next repository-wide
  full check and expanded Stage 14 source-release gate.
- [ ] If separately authorized, freeze a generated-v14 manifest, checksums,
  publication evidence, and Active Archive record through the human-invoked
  UCB AAO/S3 path.

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

## Expanded Stage 14 completion criteria

The original all-family reverse scope passed the full repository gate and was
published as the source-only `v20260810` release. The expanded post-release
Stage 14 scope is ready to freeze only when:

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

## Current release state and remaining gates

The all-family reverse implementation is complete. The Stage 14 source is
released on GitHub independently of generated-asset preservation. A later v14
UCB AAO deposit is not part of that source release: it requires its own frozen
generated manifest, reviewed profile, human invocation of
`make release-ucb-aao-s3`, immutable inventory verification, and canonical
Active Archive check-in record. `make release-github` cannot reach that target.

The numerical-evidence and consumer-contract additions described below are
later Stage 14 work and are not claims retroactively attached to the
`v20260810` source release. Focused checks accompany each addition. The next
repository-wide `make check` remains a distinct release gate and requires
explicit operator confirmation.

## Remaining Stage 14 staging plan

GPU-specific products and performance measurements are intentionally excluded
from this plan. Stage 14 will freeze the authoritative inputs and portable
consumer baseline; [Stage 15](stage-15.md) will benchmark GPU products from
that baseline.

| Stage | Work | Exit gate |
| --- | --- | --- |
| **14A — baseline and print contract** | Reconcile release-state wording, inventory exact-ratio 44-inch-leading-edge and A0 workflows, and implement `check-print-contract` | Consumer targets cannot change canonical SVG/PDF geometry, print dimensions, the 3840-pixel parent, or archived-art identity |
| **14B — numerical closure** | Implement the observation-only Dymaxion ULP classifier/clamp audit; make no behavior change without a reproducible discrepancy and explicit error bound | Every probed edge, vertex, subface, frame, tie, and clamp event is classified in machine-readable evidence |
| **14C — neutral projection fixtures** | Define stable topology keys and evidence grades, publish the six-family fixture bundle and checksums, and add native, WebAssembly, and minimal independent consumers | Offline `make check-projection-fixtures` passes without generated art, S3, or network access |
| **14D — cross-implementation oracle** | Audit `d3-geo-polygon` v1.12.1 versus v2.0.1, then add independent Voronoi, Dymaxion, and Myriahedral producers before extending the remaining evidence tiers | At least two direct or clean-room independent families pass, and every disagreement is retained and classified before production code changes |
| **14E — agent selection protocol** | Add artifact request and decision-receipt schemas, a pure deterministic selector, reason codes, hashes, CLI support, and golden fixtures | Node, browser, and a minimal independent consumer choose the same artifact and decision-core hash from identical bytes |
| **14F — consumer promotion** | Expand the 24-item 1080p canary to the standard whole-map and approved-slice matrix; add gallery links, Three.js interaction, cancellation, and a clean-room handoff | Print, catalog, screen, interaction, accessibility, and independent-consumer gates pass for every promoted standard product |
| **14G — release gate** | Run focused checks throughout, request confirmation before repository-wide `make check`, then freeze source identity, manifests, checksums, notes, and publication evidence | The expanded source release is internally consistent; any generated-v14 UCB AAO deposit remains a later, separate human invocation |

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
promotion gate. A collaborator clean-room run remains `UNAVAILABLE`. KTX2,
semantic masks, Float32 GPU geometry, and engine-specific GPU-product importers
are assigned to the [Stage 15 ledger](stage-15.md), not this completion gate.

The systematic round-trip audit adds 46,656 face/component-qualified interior
samples: 2,592 points × six families × three frame scales. All candidates
returned and all statuses were unique on the deliberately seam-avoiding grid.
The maximum spherical error was approximately `1.22e-10°` for the bounded
numerical Cahill–Keyes solver and its Star-X carrier, and approximately
`4.20e-13°` or less for the analytic families. These round trips are strong
implementation consistency evidence, not independent mathematical proof;
published anchors, exact seams, poles, face centers, and retained-hinge tests
remain necessary independent/structural evidence.

### Planned — Dymaxion ULP-scale classifier and clamp audit

Status: **planned; not yet implemented or run**.

The 46,656-sample campaign above deliberately avoids seams. It therefore does
not establish behavior within a few representable floating-point steps of a
Dymaxion face edge, vertex, Australia/Japan subdivision, pole, antimeridian,
frame-ratio boundary, or clamp threshold. The current constants are not
presumed defective, but the fixed spherical face tolerance, frame classifier,
inverse bounds, barycentric tolerance, and forward clamps merit a dedicated
ULP-scale audit before Stage 14 numerical work is considered closed.

The proposed implementation adds `tests/audit-dymaxion-ulp.cc`, a focused
`make audit-dymaxion-ulp` target, and an ignored
`reports/dymaxion-ulp-audit.json` evidence file. It should:

1. inventory and name the numerical role of the spherical classifier's
   `8 * epsilon`, the frame-ratio classifier's
   `16 * epsilon * scale`, the inverse angle/equation bounds, the
   caller-scaled planar barycentric tolerance, and every forward or inverse
   clamp;
2. enumerate every unique spherical edge and vertex, including the five
   registered Australia/Japan subfaces, and probe exact boundaries plus both
   sides with boundary-normal and `std::nextafter` displacements from 1 through
   4096 ULPs;
3. compare the production `double` classifier and Gray transform with an
   independent test-only `long double` or multiprecision oracle, recording raw
   determinants, expected/observed face membership, tie resolution, candidate
   sets, clamp activation, and forward residual;
4. audit frame acceptance around the exact Dymaxion ratio at native, 44-inch,
   1920-pixel, and 13,200-pixel scales, including the first accepted and
   rejected representable widths on each side;
5. require valid interior points to avoid clamping, permit boundary clamping
   only within a derived roundoff bound, and reject larger excursions rather
   than silently snapping them onto the frame; and
6. repeat the acceptance campaign in native and WebAssembly builds without
   changing the authoritative print, SVG, PDF, or 3840-pixel products.

Acceptance requires no unclassified gaps, the documented lowest-face-index
choice for exact ties, the expected adjacent face or subface on each side of a
boundary, complete topology-correct reverse candidates, and no non-boundary
reference regression. A tolerance or clamp changes only when both the oracle
and an explicit floating-point error bound support the replacement. The final
result belongs in the Dymaxion implementation notes whether it confirms the
existing constants or produces a corrective patch.

### Planned — true cross-implementation reverse oracle

Status: **planned; no oracle fixtures generated and no production behavior
changed**.

The existing round-trip tests use Cartofreako's forward and reverse paths
together. They are strong consistency evidence, but both directions can share
one convention or implementation error. This project should compare
Cartofreako reverse results with geographic answers produced by independent
programs from independently selected projected coordinates.

For the direct Voronoi oracle, pin the latest upstream release verified on
2026-08-10:
[`d3-geo-polygon` v2.0.1](https://github.com/d3/d3-geo-polygon/releases/tag/v2.0.1),
commit
[`45d62833536fde08053a0675a488b937d41cde07`](https://github.com/d3/d3-geo-polygon/commit/45d62833536fde08053a0675a488b937d41cde07).
The tagged
[`icosahedral.js`](https://github.com/d3/d3-geo-polygon/blob/v2.0.1/src/icosahedral.js)
constructs the upstream icosahedral projection, and its generic
[`polyhedral/index.js`](https://github.com/d3/d3-geo-polygon/blob/v2.0.1/src/polyhedral/index.js)
installs inverse traversal when the face projections expose inverses. Fixture
generation must also lock and hash the complete npm dependency graph rather
than accepting the package's semver ranges at refresh time.

The production Voronoi compatibility record remains pinned to v1.12.1 until a
separate version-delta audit compares v1.12.1 with v2.0.1. Selecting the newer
oracle must not silently redefine the current forward projection or cause a
version-registration difference to be reported as a reverse defect.

An oracle qualifies as cross-implementation evidence only when it:

- neither includes nor imports Cartofreako projection or runtime code;
- derives equations and constants from a pinned primary publication or an
  independently maintained implementation;
- begins with independently selected projected coordinates rather than
  Cartofreako forward output;
- records source version, command, environment, license, dependency lock, and
  hashes;
- emits immutable fixtures that normal offline Cartofreako tests consume; and
- compares complete candidate sets at cuts instead of selecting one convenient
  winner.

The proposed oracle routes and their evidence grades are:

| Projection | Independent route | Evidence grade |
| --- | --- | --- |
| Voronoi | Pinned `d3-geo-polygon` v2.0.1 inverse runner after the v1.12.1-to-v2.0.1 delta audit | Direct upstream cross-implementation |
| Dymaxion | Clean-room implementation of Crider's published inverse, checked against Gray's published/reference coordinates | Independent published-mathematics implementation |
| AuthaGraph | Standalone high-precision inverse/root solver derived from Narukawa 2022, with published numeric and A3 registration anchors kept distinct | Independent algorithmic implementation |
| Myriahedral | Standalone face-local inverse derived from van Wijk, reading a frozen mesh/layout fixture rather than production headers | Independent inverse mathematics over shared declared topology |
| Cahill–Keyes | Separately implemented high-precision search against the published forward construction and external reference material | Compatibility evidence until an external inverse exists |
| Star-X | Independent declarative reversal of its CK carrier and fixed-60°S cap composition | Derived-composition oracle, not an external base projection |

The repository surface should use the implementation-neutral fixture contract
below rather than define a competing oracle-only coordinate schema:

- `contracts/projection-fixtures-v1.schema.json`;
- isolated producers and provenance under `tests/oracles/`;
- checked immutable oracle cases under
  `fixtures/projections/v1/oracles/`;
- `tests/test-cross-implementation-reverse-oracle.cc`;
- offline `make check-reverse-oracles`;
- separately invoked `make refresh-reverse-oracle-fixtures`; and
- ignored `reports/cross-implementation-reverse-oracle.json`.

Fixture refresh is an explicit maintenance operation and must not run through
`make all`, GitHub release, UCB AAO/S3 release, or ordinary offline checks.
The first milestone covers Voronoi, Dymaxion, and Myriahedral interiors,
edges, vertices, cuts, one-sided boundary probes, poles, outside points, and
native/44-inch/1920-pixel/13,200-pixel frames.

Acceptance requires agreement within a declared angular bound, candidate-set
agreement at cuts after longitude canonicalization, scale-independent
geographic answers, and retained failing fixtures for every discrepancy. Each
disagreement must be classified as convention, registration, oracle, or
production error before production code changes. At least two direct or
clean-room independent families must pass before documentation claims that a
true cross-implementation reverse oracle exists. Cahill–Keyes and Star-X keep
their narrower evidence labels until an actual external implementation is
available.

### Planned — publish implementation-neutral projection fixtures

Status: **planned; schema, public bundle, and independent consumer not yet
implemented**.

Publish a small, versioned projection-mathematics dataset that JavaScript,
Python, Rust, GIS, D3, Mapshaper, and agent workflows can consume without
compiling or importing Cartofreako. These fixtures are distinct from rendered
maps, runtime tests, and the isolated programs that produce independent oracle
evidence.

The neutral contract must:

- declare geographic order as `[longitude, latitude]` in degrees and projected
  coordinates as normalized top-left page space `u=x/width`, `v=y/height`;
- declare native aspect, origin, axis directions, longitude and pole
  conventions, layout, component model, and cut topology;
- use stable geometric topology keys instead of making Cartofreako's numeric
  `nativeCell` values normative;
- treat reverse candidate sets as unordered and preserve every valid
  face/component result at cuts and overlaps;
- serialize expected decimal values reproducibly with explicit angular and
  normalized-planar tolerances;
- record source, producer, version, hash, license, evidence grade, and revision
  for every case; and
- keep runtime API/ABI versions in adapter provenance rather than fixture
  semantics.

The proposed public source tree is:

```text
contracts/projection-fixtures-v1.schema.json
fixtures/projections/v1/
  manifest.json
  cahill-keyes.json
  authagraph.json
  dymaxion.json
  myriahedral.json
  star-x.json
  voronoi.json
  topology-crosswalk-cartofreako.json
  oracles/
  SHA256SUMS
docs/pages/runtime/projection-fixtures.md
tests/test-projection-fixtures.cc
scripts/check-projection-fixtures.mjs
```

The numeric Cartofreako cell crosswalk remains separate from stable geometric
identifiers. Each case records a stable case/projection/layout ID, operation,
normalized input and expected output, topology keys, expected status and full
candidate set, boundary class, tolerances, evidence, and revision history.

Evidence grades are deliberately narrow:

| Grade | Meaning |
| --- | --- |
| `published-anchor` | Coordinate or invariant supplied by a primary publication |
| `upstream-implementation` | Produced by a pinned independently maintained implementation |
| `independent-reimplementation` | Produced by a clean-room implementation of published mathematics |
| `structural-invariant` | Face center, edge, pole, hinge, scale, or topology fact |
| `cartofreako-compatibility` | Existing behavior preserved for compatibility; not independent evidence |

Cartofreako round trips must never be silently promoted to an independent
grade. The initial publication set covers all Cahill–Keyes octants and
representative A–L zones; all 24 AuthaGraph sectors and singular vertices; all
23 Dymaxion faces/subfaces; representative Myriahedral cases plus a separate
5,120-face-center pack for each registered layout; Star-X carrier/cap
quadrants, cutoff, pole, cut, and overlap; and all 20 Voronoi faces, edges, and
vertices.

Implementation order is:

1. define stable topology keys, evidence grades, canonical serialization, and
   the JSON Schema;
2. extract existing hard-coded published/reference anchors without changing
   their values or evidence claims;
3. make native C++ and WebAssembly checks consume the same fixture records;
4. add independently generated reverse cases through the oracle workflow
   above;
5. add a dependency-free Node checker and a minimal non-Cartofreako Python
   consumer; and
6. publish versioned raw JSON, checksums, and a downloadable bundle through
   GitHub Pages and source releases.

Fixture publication does not depend on generated assets, graphics rendering,
S3, or UCB AAO. Schema/fixture major versions change for semantic changes;
additions and corrections retain an explicit revision ledger rather than
silently rewriting evidence.

Acceptance requires offline schema and checksum validation; identical fixture
use by native and WebAssembly adapters; successful parsing by a non-Cartofreako
consumer; semantic rather than array-order candidate comparison;
scale-independent geographic answers; and provenance plus redistribution
clearance for every value. Establish this neutral contract before implementing
the cross-implementation producers so every oracle emits one portable evidence
format.

### Planned — artifact request and decision-receipt schemas

Status: **planned; schemas, selector, and receipts not yet implemented**.

Define a deterministic, inspectable interface between an agent's request and
the artifact catalog. The selector uses structured constraints and explicit
preference order rather than hidden model judgment, and emits a receipt even
when no artifact matches. Neither a request nor a selection receipt authorizes
external-source access, license acceptance, publication, release, S3 upload,
research interpretation, or training-data transfer.

The two self-contained JSON Schema Draft 2020-12 contracts are:

```text
contracts/artifact-request-v1.schema.json
contracts/artifact-decision-receipt-v1.schema.json
```

An artifact request records:

- a stable request ID, schema version, and purpose profile: `preview`,
  `flat-screen`, `interactive-flat`, `print-review`, `archive-reference`, or
  `research-comparison`;
- subject/pass IDs, allowed lifecycle states, year or source period, and
  allowed or preferred projection/layout/slice IDs;
- viewport, fit, format, transparency, losslessness, byte limit, required
  interaction capability, and acceptable authority classes;
- an offline-by-default network policy, checksum/metadata requirements,
  ordered preference clauses, explicit fallback sequence, and human-review
  requirement; and
- no transcript, credential, external authorization, or secret material.

Defaults allow only `standard` passes. Optional passes require explicit opt-in
and must already be authorized and present. Exploration-only products require
a separate explicit opt-in and a human-review disposition.

The versioned deterministic selector should:

1. validate and normalize the request;
2. verify catalog schema and hash;
3. apply hard constraints;
4. rank survivors lexicographically using the request's ordered preferences;
5. break final ties by stable artifact ID and variant ID;
6. relax only the constraints named in the explicit fallback sequence;
7. return `no-match` instead of inferring an unstated preference; and
8. emit the receipt before optional file retrieval.

Missing catalog metadata is `UNAVAILABLE`, never false, zero, unrestricted, or
acceptable. Phase one supports only fields actually present in
`artifacts-v1`; source-period, licensing, or governance constraints return
`METADATA_UNAVAILABLE` until a later catalog revision supplies those fields.

The decision receipt records:

- request ID, canonical request hash, and normalized request;
- catalog version, source revision, and catalog SHA-256;
- selection-policy and runtime versions;
- outcome: `selected`, `no-match`, `requires-human-review`, or `error`;
- selected artifact/variant IDs, file hash, authority class, lifecycle,
  projection/layout/slice, source period, limitations, interaction support,
  and exact screen transform when available;
- every evaluated candidate with its rank vector and rejection reason codes;
- every explicit constraint relaxation and each schema, checksum,
  availability, or retrieval verification state;
- any human override with prior choice, replacement, reason, and actor label;
- an explicit non-authority statement; and
- a canonical decision-core SHA-256.

Timestamp and host information belong in a run envelope outside the
deterministic decision core. An override or later selection creates a new
receipt referencing the prior receipt; it never rewrites the original. The
initial rejection vocabulary is:

```text
SUBJECT_MISMATCH
YEAR_MISMATCH
LIFECYCLE_DISALLOWED
PROJECTION_DISALLOWED
SLICE_MISMATCH
FORMAT_UNAVAILABLE
VIEWPORT_INCOMPATIBLE
INTERACTION_UNSUPPORTED
AUTHORITY_CLASS_DISALLOWED
MAX_BYTES_EXCEEDED
CHECKSUM_UNAVAILABLE
METADATA_UNAVAILABLE
GOVERNANCE_REVIEW_REQUIRED
LOWER_PREFERENCE_RANK
STABLE_TIE_BREAK
```

The implementation surface should be:

```text
src.wasm/cartofreako-catalog.mjs
src.wasm/cartofreako-catalog.d.ts
scripts/select-artifact.mjs
tests/fixtures/artifact-selection/
tests/test-artifact-selection.mjs
docs/pages/runtime/artifact-selection.md
```

Add offline `make check-artifact-selection`. The selector is pure and performs
no network, authorization, generation, release, or upload action.

Acceptance requires identical request/catalog bytes to produce the same
decision-core hash; catalog order not to affect the decision; standard-only
defaults never to select optional or exploration-only artifacts; missing
metadata to yield an explicit rejection or human review; every rejection to
have a reason code; `no-match` to produce a valid receipt; tampered request,
catalog, or artifact hashes to fail verification; human overrides to remain
append-only; and Node, browser, and a minimal independent consumer to agree on
the selected ID. Selecting an artifact never implies permission to publish or
authority to interpret its evidence.
