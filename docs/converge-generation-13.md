# Stage 13 generation convergence

[Documentation index](../index.md) ·
[Generation guide](generation.md) ·
[Generation methods](generation-methods.md) ·
[Stage 12 implementation notes](stage-12-implementation-notes.md) ·
[Resource metric catalog](resources-metric-catalog.md) ·
[Release runbook](releases/README.md)

## Scope and release boundary

Stage 13 begins after the immutable `v20260807` source tag at
`2bd3d760fef540addfcbb4f8002ef7b283d8000f` and the independently versioned
`assets.generated.v12.tar.xz` bundle. The credential-free rendering changes
were first frozen at `c7d9c09be630f1ac16d750b7da4e98cb9082d139` and tagged
`v20260808`. That standard-only package was superseded without moving its tag;
the corrected complete graph and authorization-aware thumbnail contract are
published from `v20260808.1`. Neither attempt mutates the v12 tag, GitHub
asset, or Berkeley S3 prefix.

The v12 browser tree remains immutable at
[`cartofreako/v12/`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/).
It contains 594 objects, preserves the XZ package as the recovery artifact,
publishes large SVGs only as explicit `.svg.gz` objects, embeds PNG previews,
and uses `release.json` as its last-written completion marker. See the
[S3 v12 publication record](releases/s3-v12.md) for its exact digest,
inventory, viewer, verification, and Active Archive delivery evidence.

The first projection-first package attempt contained only the 205-product
credential-free graph. Publication was stopped before S3 because the release
manifest requires the already authorized Cloud-atmosphere family as well as
standard Fiber Synthesized. The corrected graph has 211 SVG, PDF, and PNG
products, 84 resource SVG-gzip companions, and 192 thumbnails. Final package
identity and publication evidence belong to the versioned release record, not
to this implementation ledger.

## Current outcome

| Area | Stage 13 result | Pass class |
| --- | --- | --- |
| Release publication | Projection-first recovery package, v13 browser tree, six thumbnail grids, immutable upload checks, and canonical report workflow are integrated | Operations, not a generation pass |
| External sources | Successful optional generation persists only canonical authorization names for later local `make all` runs | Optional |
| JAXA P-Tree | The resolver uses the newest advertised H09 CLP observation not after process start and records the actual source time, even when older than six hours | Optional |
| Star-X | Fixed `60°S` Antarctic split, source-radius preservation, lower uncut-quadrant Y alignment, topmost cap paint order, and a final black water-map polar star | Standard projection behavior |
| Astronomy | Separate ground-multiband and Hubble observer products; true-apparent planet outlines plus enlarged display glyphs | Standard |
| Resources | 30% data opacity and 2× titles across all 14 released metrics; reef generation remains in the default fauna graph | Standard |
| Anthropocene | 30% temperature fields, 2× titles, and a larger legacy-atlas title | Standard |
| Network plates | Larger site/swarm marks, 2× titles, and a WCAG-oriented light-gray ground | Standard sites/swarm; optional licensed topology |
| Cloud-atmosphere | The background layer remains available but is emitted hidden with an explicit default-visibility marker | Optional |
| Fiber Synthesized | Checked 2022/20260805 cleanup and union, with 20260805 as the default rendered layer | Standard |
| Bathymetry Roulette | Every form is filled, begins at cycloid `d/r = 1`, increases `d/r` with depth, and uses Voronoi-grouped variation | Standard art pass |
| Bathymetry Hamonshū | New Izzi wave-field pass using the Roulette depth-field architecture | Standard art pass |
| Air and smoke research | Full GHCN and OpenAQ prioritized; CAMS, MAIAC, GFAS, and PurpleAir boundaries documented without merging unlike observations | Exploration only |

## Post-v13 projection API development

On 2026-08-09, the shared native/WebAssembly runtime added independently
versioned API 2 while retaining geometry command-buffer ABI 1; Cahill–Keyes
reverse support followed on 2026-08-10. Structured forward calls now return
native cell and component metadata. Analytic face-qualified reverse covers
every Myriahedral layout and Voronoi; zone-aware numerical reverse covers
Cahill–Keyes. All return explicit `unique`, `ambiguous`, `outside`, `cut`, or
`unsupported` states. The JavaScript wrapper, TypeScript declarations, module
worker, D3
adapter, native exhaustive-face check, Node smoke test, and headless Chrome
test share the same contract. AuthaGraph, Dymaxion, and Star-X continue to
report unsupported reverse capability. See the
[forward/reverse projection API](forward-reverse-projection-api.md).
Ongoing implementation and verification are tracked in the
[Stage 14 convergence ledger](converge-generation-14.md).

## Build graph and pass classes

A clean checkout has 205 standard layered SVG products, 205 PDFs, 205
full-size PNGs, 84 deterministic resource `.svg.gz` files, and 31 additional
480-pixel thumbnails for each of the six projections, 186 total. The increase
from v12's 187 products and 28 Cahill–Keyes-only thumbnails is six Hubble
observer maps, six Bathymetry Hamonshū maps, and six Fiber Synthesized maps. The
renamed ground observer maps replace, rather than duplicate, the former
ambiguous observer names.

The complete release graph records `jaxa-ptree` after an end-to-end successful
fetch, preparation, verification, and six-projection render. That adds six
Cloud-atmosphere SVG/PDF/PNG products plus one thumbnail per projection, for
211 full-size products, 32 thumbnails per projection, and 192 thumbnails
total. Fiber Synthesized is already part of the 205-product standard count.

The generated tree is projection-first:

```text
assets.generated/<projection>/{svg,pdf,png,thumbnail}/
```

This is also the v13 S3 tree contract. GitHub Pages embeds the dedicated S3
thumbnail PNGs and links each to a same-origin viewer that fetches the nested
explicit `.svg.gz` object; no contact sheet relies on a checked-in generated
tree or downloads a full-resolution PNG merely for display.

The checked generation-profile vocabulary has 19 selectable passes. Profile
`"all"` expands the six projections across those pass families and yields 180
SVG products because astronomy, Orbital Technosphere, Anthropocene, and
several resource families emit more than one product. It includes the
credentialed Cloud-atmosphere selector and therefore requires prepared JAXA
data. The offline release-oriented `make all` graph instead keeps the 205
credential-free standard products and excludes Cloud-atmosphere until local
authorization has succeeded.

The three public classes are intentionally distinct:

| Class | Meaning in Stage 13 | Current examples |
| --- | --- | --- |
| **Standard pass** | Source-pinned, implemented, checked, and included in the clean offline artifact graph | 14 resource metrics, astronomy including Hubble, dual-year Anthropocene temperature, network swarm/sites, Fiber Synthesized, Roulette, and Hamonshū |
| **Optional pass** | Implemented to the same artifact standard but gated by credentials, terms, or an operator decision; absence never breaks a clean checkout | JAXA Cloud-atmosphere and licensed network topology |
| **Exploration only** | Researched, cataloged, or acquired for review but not promoted to a production output or release graph | NASA FIRMS prepared candidate, PurpleAir, OpenAQ, full GHCN, CAMS/MAIAC, LGBTQIA legal dimensions, and drug-policy dimensions |

Authorization does not promote an exploration. A successful NASA FIRMS run
may be recorded locally, but it still ends at a prepared review snapshot and
adds no rendered artifact until a separate source, metric, coverage, digest,
test, and documentation review promotes it.

The [resource metric catalog](resources-metric-catalog.md) is the authoritative
human-readable lifecycle index. It makes all 14 standard resource metrics and
45 exploration-only definitions visible, including the current blockers for
consensual-same-sex-activity law and drug-possession policy. Neither policy
candidate currently has normalized values, coverage, targets, artifacts, or
previews.

## Post-v12 release and documentation foundation

Changes committed after the v12 tag establish the next release's operational
base:

- the v13 S3 builder reconstructs a projection-first publication tree only
  from the pinned XZ package, preserves PNG/PDF/thumbnail/document objects,
  converts every browser SVG to an explicit gzip object, and creates a sorted
  manifest and completion marker;
- the uploader uses an ephemeral rclone configuration, exact-prefix
  confirmation, pilot-object and anonymous-browser checks, immutable uploads,
  payload verification, last-marker publication, and optional full readback;
- the same-origin viewer fetches `.svg.gz`, uses `DecompressionStream`, and
  offers compressed and decompressed downloads while documentation embeds the
  much smaller S3 PNG previews;
- successful applied upload runs produce the canonical three-page
  **cartofreako v13 checked in to UCB Active Archive Object Storage** report,
  validate its document kind, page geometry, fonts, text extraction, and QA
  renders, exclude the unrelated generic deposit-report layout, and hand the
  exact PDF to the authenticated release orchestrator for automatic Gmail
  delivery to the two fixed recipients, without a desktop composer;
- projection snapshot pages share navigation and use the immutable S3 PNG and
  viewer URLs instead of assuming `assets.generated/` is checked into Git;
  and
- the resource metric catalog and documentation index expose lifecycle and
  pass-class boundaries directly.

These procedures are documented in [S3 v13 publication](releases/s3-v13.md),
the [release runbook](releases/README.md), and the
[generated snapshot catalog](../index.md#generated-artifact-previews).

## Persistent optional generation

`make authorize-external` remains a read-only authorization check.
`make generate-authorized-external` first authorizes the complete selected
set, then performs each bounded acquisition/generation workflow. Only after
every selected workflow succeeds does it atomically merge canonical names into
the ignored local file:

```text
.cartofreako/authorized-external-passes
```

The state file has mode `0600`, contains no credentials or Make syntax, and is
read through an exact whitelist. A failed transaction records nothing new.
Later `make all` invocations in the same checkout add all three formats for a
recorded `jaxa-ptree` or `network-topology` pass. A recorded `nasa-firms` name
retains authorization/acquisition provenance but adds no render graph.

```sh
make EXTERNAL_PASSES=jaxa-ptree generate-authorized-external
make all

# One standard-only invocation without changing the state file.
make AUTHORIZED_EXTERNAL_PASSES= all
```

`EXTERNAL_AUTHORIZATION_STATE` may select a different local state path. The
certificate installer and P-Tree workflow are documented in
[Prerequisites](prerequisites.md) and the
[P-Tree production-download guide](ptree-production-download.md).

The P-Tree resolver no longer guesses a directory from the current UTC date.
It walks advertised month/day/hour directories and selects the newest H09
L2CLP010 `.nc` or `.nc.gz` observation whose timestamp is not after process
start. Publication delay no longer turns an otherwise usable latest snapshot
into a six-hour failure. The prepared profile and SVG metadata retain the exact
observation interval, age, source URL, and digest. Non-P-Tree source freshness
rules remain hard limits. This also avoids curl error 9 when the guessed
current directory has not yet been published.

## Star-X projection composition

The Stage 13 Star-X compositor uses a fixed geographic rule:

1. geometry at latitude greater than `60°S` stays in its ordinary quadrant;
2. geometry at or south of `60°S` enters the unified Antarctic cap;
3. each point keeps its exact radius from the ordinary lower-quadrant South
   Pole tip while only its bearing changes around the shared pole;
4. the cap is centered on the page axis with no maximum-land-distance
   boundary or boundary bisection;
5. its vertical anchor derives from the original, uncut Natural Earth
   Antarctic mainland's lower-quadrant extent, not the already cut fragment,
   placing the continent lower on the page; and
6. ordinary paths are queued first and every transformed Antarctic fragment
   is serialized last inside the same thematic layer.

The graticule uses the same fixed boundary. Earth keeps the layer-aware
North-pole star. Water appends its black star as a final `polar-mark` group
after every physical layer, so neither bathymetry nor another quadrant can
cover it. Embedded generator assertions verify the cap boundary, centering,
uncut-Y alignment, path order, and final polar mark. See the
[Star-X implementation notes](star-x-implementation-notes.md) and
[context](star-x-context.md).

## Astronomy observers and planet scale

The former `astro-observer-*` family is disambiguated into:

- `astro-observer-ground-multiband-*`, using the existing San Francisco
  terrestrial point and generic infrared/optical/radio instrument model; and
- `astro-observer-hubble-*`, propagating NORAD 20580 from the checked
  CelesTrak science OMM with SGP4, a seven-day maximum element age, a 20° Earth
  limb clearance, and a 60.3° Sun-avoidance rule for a composite HST
  infrared/optical/ultraviolet instrument.

Both observer and instrument IDs are stable filename and SVG-metadata fields.
Hubble is therefore a different platform/visibility product, not a relabeling
of the ground map.

Planet source sizes use equatorial radii and geocentric distance to calculate
their true apparent angular radii. Each planet now has a dotted projected
outline at that physical apparent scale plus a fixed `0.15 in` display glyph,
twice the previous `0.075 in` size, so a print viewer can see the object without
mistaking the enlargement for physical scale. The
[astronomy implementation notes](astro-implementation-notes.md) record the
JPL physical-parameter and Horizons conventions and the exact observer model.

## Visual hierarchy and opacity

Stage 13 applies a common rule to dense resource and temperature data: keep
the base geography legible by limiting the observed field to 30% opacity, and
double the primary plate title without changing its wording or evidence
metadata.

- all country-resource fills and coral-reef cells use 30%; missing/unknown and
  legend samples remain explicit and legible;
- 2025 and 2026 Anthropocene temperature H3 fields use 30%, and the legacy
  observation-atlas title is enlarged independently;
- network-swarm and network-infrastructure site/topology marks are enlarged,
  while the page/land ground uses the WCAG-oriented light gray `#f2f4f3` and
  a darker accessible data palette;
- Fiber Synthesized uses the same light-gray ground, enlarged cable/landing
  marks, and 2× title while keeping 2022-only context subdued; and
- network titles are doubled; the requested
  `Anthropocene temperature / 2026 Partial Year` title is likewise doubled in
  its own family.

These are display changes, not metric or observation changes. Exact profile
metadata and implementation constants are recorded in the
[resources](resources-implementation-notes.md),
[Anthropocene](anthropocene-implementation-notes.md),
[network-swarm](network-swarm-implementation-notes.md),
[network-infrastructure](network-infrastructure-implementation-notes.md), and
[Fiber Synthesized](fiber-synthesized-implementation-notes.md) notes.

## Fiber Synthesized standard pass

The two validated submarine-cable API snapshots are now promoted as a checked
cleanup and union under `assets.static/fiber-synthesized`; this is not a set
difference, and `assets.static/fiber-evolution` remains reserved for a future
strict `new - old` product. The synthesis validates all JSON, GeoJSON,
identifiers, cable details, landing references, coordinate bounds, and source
counts before writing a manifest and checksums.

Exact stable-ID and unique normalized-name matches, plus 18 unique exact
landing-set/name-token matches recorded as strong topology evidence, are deduplicated for
normal rendering. The standard layer selects all 718 route features and 1,922 landing
points from `v3.20260805`, then adds 49 unmatched 2022-only routes and 115
unmatched 2022-only landings as faint historical context. Both complete source
observations remain in audit GeoJSON. Snapshot-only is explicitly neutral and
does not assert construction or decommission.

`fiber-synthesized`, `fiber`, and `fiber-map` select the pass. Its six SVGs,
PDFs, PNGs, and Cahill–Keyes thumbnail are in the default `make all` graph;
`refresh-fiber-synthesized` is a separate reviewable source operation and is
never an ordinary render dependency. Exact counts, source hashes, licensing,
layer grammar, commands, and verification are in the
[Fiber Synthesized implementation notes](fiber-synthesized-implementation-notes.md).

## Bathymetry art passes

### Roulette

All twelve Natural Earth depth thresholds now use filled roulette forms. The
shallowest is exactly the cycloid boundary `d/r = 1`; depth monotonically
raises `d/r` through `5.0`. Diameter, phase, offset, radius family, closure
period, and epitrochoid/hypotrochoid choice retain independent visual
variation. Twenty-four deterministic jittered Voronoi sites group the twelve
form variations in broad page-space neighborhoods. Motifs may cross those
planar neighborhoods and create accepted interference or moiré, but remain
clipped by the geographic depth polygon.

### Hamonshū

`bathymetry-hamonshu` is a separate standard pass using Izzi's
`a60-svg-curves-hamonshu` implementation and twelve source-indexed motifs from
Mori Yūzan's *Hamonshū*. It uses the same twelve depth thresholds, 24-region
Voronoi assignment, overlap, geographic clipping, paint order, projections,
and artifact graph as Roulette. Depth raises native density and curvature
instead of inventing a Hamonshū `d/r` value.

### Shared color contract

Both art passes use the original Natural Earth shallow-to-deep blue family in
addition to their independent form experiments. Every one of the twelve depth
bands has a distinct blue, from `rgb(190,219,235)` at 0 m through
`rgb(15,49,88)` at -10,000 m, and every motif is drawn at 30% opacity. Color is
a redundant depth cue; motif geometry remains an art mapping rather than a
claim about currents, wave energy, geology, or bottom roughness.

```sh
make generate-bathymetry-roulette
make generate-bathymetry-roulette-artifacts
make generate-bathymetry-hamonshu
make generate-bathymetry-hamonshu-artifacts
```

Both families are included in `make all`, resilient/single release builds,
generation profiles, and Cahill–Keyes thumbnails. See the
[Roulette](bathymetry-roulette-implementation-notes.md) and
[Hamonshū](bathymetry-hamonshu-implementation-notes.md) implementation notes
for every depth parameter and structural assertion.

## Anthropocene source expansion boundary

The legacy observation atlas remains valued specifically because it preserves
source-separated climate records, precipitation, fire, and HMS smoke instead
of merging them into a synthetic score. Stage 13 research identifies these
next candidates:

1. full NOAA GHCN-Daily for a much larger climate-record inventory;
2. OpenAQ's public object archive for a separate surface-air-quality field;
3. CAMS EAC4, NASA MAIAC, or CAMS GFAS as explicitly modeled, satellite, or
   emissions products; and
4. PurpleAir only as an optional supplemental source after an API key plus a
   bounded sensor manifest or provider-arranged bulk extract exists.

None is silently merged into the released atlas. Promotion requires pinned
bytes, rights, units, time semantics, QA, deduplication, coverage, digest,
tests, and a new labeled output. The complete findings and gates are in
[Anthropocene source expansion](anthropocene-source-expansion-stage-13.md).

## Focused verification checkpoint

The following strict-warning focused tests were recompiled and passed on
2026-08-07:

- Anthropocene legacy and temperature generation;
- resources generation;
- astronomy generation with SGP4;
- network-infrastructure, network-swarm, and Fiber Synthesized generation;
- generation-profile normalization and target mapping;
- Star-X projection API;
- Bathymetry Roulette and Bathymetry Hamonshū style catalogs; and
- the authorized-external transaction/state driver; and
- Cloud-atmosphere generation, including the retained but default-hidden
  `cloud-atmosphere-background` layer.

Representative Cahill–Keyes PNGs were regenerated and visually reviewed for
Hubble astronomy, 2026 Anthropocene temperature, wind resources, network
swarm, network-infrastructure sites, Fiber Synthesized, Bathymetry Roulette,
and Bathymetry Hamonshū. Earth, water, and
graticule Star-X PNGs were regenerated and reviewed together; they show the
lower unified Antarctica, fixed `60°S` guide, topmost cap, and final black
water-map star.

The restored `/home/bkoz/src/cloud_cdn_cache` source passed its focused check,
and the representative network-infrastructure site PNG regenerated normally.
Fiber Synthesized static checksums, strict loader test, generation-profile
mapping, embedded SVG checks, and the 767-route/2,037-landing Cahill–Keyes
preview also passed. Inkscape emitted its existing headless Pango/GTK warning
while producing valid nonempty PNGs.

The operator froze the Stage 13 manifest and authorized the full checks,
complete six-projection render, release packaging, and publication on
2026-08-07. Native and browser/WebAssembly checks passed. The completed render
passed exact inventory, XML, gzip round-trip, single-page PDF, PNG color and
opacity, thumbnail-dimension, and visual contact-sheet checks before the
recovery package was sealed. Publication results belong in the release record
rather than being duplicated here.

## Release checkpoint

The Stage 13 release follows this completed sequence:

1. restored and verified every documented sibling source prerequisite;
2. ran the full checks after operator confirmation;
3. rendered all standard products, plus only locally authorized optional
   passes;
4. inspected all 192 thumbnails, including every changed Star-X family and
   the six authorized Cloud-atmosphere previews;
5. published the new immutable generated-assets version and verified
   `cartofreako/v13/` without changing `cartofreako/v12/`; and
6. completed the source tag, static asset, last-written completion marker,
   canonical Active Archive check-in report, full readback, and authenticated
   Gmail notification as one evidenced release flow.
