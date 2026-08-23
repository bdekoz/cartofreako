# Network Fiber implementation notes

[Documentation index](../../../index.md) ·
[Generation pipeline](../getting-started/generation.md) ·
[Stage 13 convergence](../../development/20260815_stage-13.md) ·
[v13 AAO publication](../releases/aao-v13.md)

## Status and scope

`network-fiber` is a **standard, default-rendered pass** (formerly "Fiber
Synthesized"). Its checked-in input lives in `assets.static/fiber-synthesized`,
so ordinary generation does not need network access, an external checkout,
credentials, or the optional network-topology authorization state.

The dataset is a validated cleanup and union of the TeleGeography submarine-
cable API snapshots `v3.2022` and `v3.20260805`. It is not a strict set
difference. The unused path `assets.static/fiber-evolution` is reserved for a
future `new - old` product if one is implemented.

## Published v14 previews

Network Fiber is present in every projection of the immutable v14 AAO release
(published under the former "Fiber Synthesized" product name). These dedicated
480-pixel thumbnails show the checked cleanup and union with `v3.20260805` as
the primary visible snapshot. Select one to stream the corresponding layered
`.svg.gz` through the corrected v14 viewer.

{% include v14-pass-gallery.md stem="network-fiber" label="Network Fiber" %}

## Source boundary

Both source directories came from checkout
`4d98b5472152a7c2272c49d8d0125b1ae0419984` of
`https://github.com/telegeography/www.submarinecablemap.com`:

| Snapshot | Systems | Route features | Route parts | Vertices | Landings | Planned systems |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `v3.2022` | 526 | 532 | 1,458 | 11,590 | 1,436 | 65 |
| `v3.20260805` | 697 | 718 | 1,930 | 14,075 | 1,922 | 91 |

The manifest pins the route, landing, and combined cable-detail SHA-256
digests for both snapshots. Every JSON document parses; route and landing
GeoJSON types and coordinate bounds validate; cable-index IDs exactly match
routed IDs; cable details match filenames; and every cable-to-landing
reference resolves.

Each snapshot lacks one otherwise redundant standalone landing-detail file:
`sapporo-japan.json` in 2022 and `cape-town-south-africa.json` in 20260805.
This is recorded as benign because the aggregate landing collections are
complete, every cable reference resolves, and neither synthesis nor rendering
consumes the standalone landing-detail files.

TeleGeography map data is CC BY-NC-SA 3.0 Unported. The static dataset and
generated pass retain that license and attribution boundary.

## Cleanup and union algorithm

`scripts/synthesize-submarine-cable-snapshots.py` performs the synthesis
deterministically:

1. recursively parse and validate every source JSON file;
2. validate cable index, details, routes, landings, IDs, references,
   coordinate bounds, and source counts;
3. pair system observations when they have the same safe ID, one unique exact
   Unicode-normalized name, or one unique exact nonempty landing-ID set across
   both complete snapshots whose names also share a normalized token of at
   least three characters; the last is recorded separately as strong topology
   evidence rather than an exact-name identity;
4. classify exact pairs as retained active, retained planned,
   planned-to-active, or active-to-planned;
5. retain unmatched observations with neutral `SNAPSHOT-only` labels rather
   than claiming additions, removals, construction, or decommission;
6. preserve both source geometries in audit files without averaging,
   interpolation, or fuzzy identity inference; and
7. build the cleaned union from every `v3.20260805` feature plus only unmatched
   `v3.2022-only` features, preventing matched older geometry from being drawn
   twice.

The result contains 746 comparison identities: 456 stable-ID matches, three
unique exact normalized-name matches, 18 strong unique landing-set/name-token
matches, 49 `v3.2022-only` records, and 220 `v3.20260805-only` records. There
are 34 planned-to-active system identities. Three unique landing-set
candidates with no shared name token remain unmatched rather than risking a
false identity assertion.

The checked outputs are:

| File | Role |
| --- | --- |
| `routes.geojson` | 767-feature cleaned union consumed by the renderer |
| `landings.geojson` | 2,037-feature cleaned union consumed by the renderer |
| `systems.json` | identity matches, observations, change flags, and classifications |
| `route-observations.geojson` | all 1,250 source-separated route observations |
| `landing-observations.geojson` | all 3,358 source-separated landing observations |
| `manifest.json` | source pins, selection policy, counts, caveats, and payload hashes |
| `SHA256SUMS` | integrity list for every checked payload and README |

Regenerate the static snapshot explicitly with:

```sh
make refresh-network-fiber
make check-network-fiber
```

Refresh is intentionally not a dependency of `make all`: a source refresh is
a reviewable static-data change, while standard rendering remains offline.

## Default rendering

The SVG group `network-fiber` is the default data layer. It draws all 718
route features from `v3.20260805` plus 49 unmatched `v3.2022-only` route
features. The 20260805 snapshot is therefore the primary and complete visible
network, with older-only context kept faint and dashed. The rendering follows
the alpha60 fiber style: current and activated routes are green
(`rgb(18,152,12)`), while planned and 2022-only context routes are black.

| Rendering | Meaning |
| --- | --- |
| green solid | exactly matched, current active route |
| green solid | unmatched `v3.20260805-only` active route |
| green solid | current route whose exact system identity changed from planned to active |
| black dashed | current planned route |
| black dashed | unmatched `v3.2022-only` route; historical snapshot context only |

The plate explicitly states “snapshot-only ≠ construction or decommission.”
Current landing points are filled; unmatched older landing points are hollow.
All products use the Stage 13 light-gray background, enlarged route/point
marks, and 2× plate title.

The same Natural Earth base and seam-safe path projection serve Cahill–Keyes,
AuthaGraph, Dymaxion, Myriahedral, Star-X, and Voronoi. Star-X uses the shared
fixed 60°S Antarctic cap and topmost Antarctic paint order.

## Build targets and profile selectors

Generate the standard family with:

```sh
make generate-network-fiber
make generate-network-fiber-artifacts
make generate-network-fiber-cahill-keyes
```

`network-fiber`, `fiber`, and `fiber-map` are generation-profile aliases.
Because the pass is standard, its six SVG, PDF, PNG, and Cahill–Keyes snapshot
products are part of the ordinary `make all` graph.

## Verification

`tests/test-fiber-synthesized-generation.cc` checks the source/default labels,
manifest counts and digests, cleaned-union classifications, and representative
geometry in all six projections. The generator reopens every SVG and checks
its viewBox, required semantic groups, exact route and landing element counts,
default-layer metadata, source hashes, attribution, caveat, font, and finite
coordinates.

The focused Cahill–Keyes preview contains exactly 767 route elements and 2,037
landing elements. `make check-network-fiber` independently verifies every
checked static payload against `SHA256SUMS`.
