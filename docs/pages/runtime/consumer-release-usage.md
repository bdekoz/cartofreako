# Consuming the v14 AAO release

[Documentation index](../../../index.md) ·
[Technical documentation](../README.md) ·
[v14 AAO release record](../releases/aao-v14.md) ·
[Artifact catalog and selection](artifact-selection.md) ·
[Visual gallery](../gallery/README.md)

This page is the practical guide to the published generated-assets v14 tree
at `https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/`.
It explains how to turn an artifact ID into a URL, what the authority classes
mean, and the five most common consumer workflows.

## Artifact ID grammar

Every published product has a stable ID of the form
`<pass>.<projection>.<layout>`; a `sliceId` appears only for slice layouts.
Examples:

- `water.cahill-keyes.whole-map`
- `network-groundstations.star-x.whole-map`
- `majuro-atoll-evidence.myriahedral-pacific.<slice>` for slice-specific
  products (not present in the standard v14 partition).

`indexes/artifacts-v1.json` is the primary machine-readable index. It stores,
for each of the 217 artifacts: `id`, `lifecycle`, `passId`, `projectionId`,
`layoutId`, `sliceId`, `authority`, SHA-256 `hashes`, the historical `v13`
locations, and the `proposedV14` locations. The companion
`indexes/by-pass/<pass>.json` and `indexes/by-projection/<projection>.json`
files point back to the same IDs so a consumer can make one bounded request
for a known interest instead of listing the whole prefix.

## Authority classes

| Class | Object family | Use |
| --- | --- | --- |
| `archive-art-master` | `master/*.svg.gz` | Authoritative layered vector |
| `print-presentation` | `print/*.pdf` | 44-inch-leading-edge print plate |
| `full-raster` | `full/*.png` | 3840-pixel-longest-side raster |
| `access-derivative` | `screen-1080p/{png,webp}/...` | 1920 × 1080 consumer derivatives |

These are documentation and authority labels, not a ranking or a license.

## Resolving an ID to a URL

```sh
curl -sS \
  https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/indexes/by-pass/water.json \
  | jq '.'
```

Prefix the returned `proposedV14` path with the release base:

```text
https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/<proposedV14 path>
```

Known caveat: the `masterSvgGzip` values in the published index end in a
doubled `.svg.gz.gz`. The actual object has one `.gz`; remove one suffix
before requesting it. `fullPng`, `printPdf`, `thumbnailPng`, and the
`screen-1080p` values are correct as published.

## Runtime

The browser runtime is a release contract under `runtime/api-3/`:
the projection loader, companion WASM, high-level projection API, and
declarations are core; screen transforms, artifact selection, workers, and
Canvas/SVG/D3 helpers are optional. `runtime-manifest.json` records byte
length, SHA-256, MIME type, role, and core/optional classification for each
file. The required delivery metadata is stated in the
[v14 AAO release record](../releases/aao-v14.md).

## Workflow 1 — browse the release

Open the [visual gallery](../gallery/README.md), select a projection contact
sheet, then follow **Full PNG** or **Print PDF** for any of the 33 standard
passes. Thumbnails exist only for the six whole-map projections; use the full
PNG for the five Myriahedral slice directories.

## Workflow 2 — find one product by ID

1. Choose an ID, for example `network-groundstations.cahill-keyes.whole-map`.
2. Read `indexes/artifacts-v1.json` (or the `by-pass`/`by-projection` subset)
   and take the `proposedV14.fullPng` value.
3. Download `https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/<fullPng>`.
4. Check the downloaded bytes against `hashes.fullRaster`.

## Workflow 3 — consume the screen-1080p family

For 1920 × 1080 consumers, request
`products/standard/<projection>/screen-1080p/png/<stem>.png` or the WebP
sibling. Pair them with the runtime files under `runtime/api-3/`; the
screen-1080p objects are `access-derivative` outputs and never replace the
archive, print, or full-raster authorities.

## Workflow 4 — verify the release

```sh
release_base=https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14
curl -sS "$release_base/SHA256SUMS" -o /tmp/cartofreako-v14-SHA256SUMS
curl -sS "$release_base/release.json" -o /tmp/cartofreako-v14-release.json
```

`SHA256SUMS` covers every payload object except itself and `release.json`;
`release.json` records the counts, source identity, and the
`manifest_sha256`. The completion marker is written last and the prefix is
immutable: never treat a missing marker as durable incompleteness after a
completed upload, and never repair an object in place.

## Workflow 5 — rebuild and review locally

The release is machine-bound to eureka. To reproduce the gate and review its
evidence there:

```sh
make all-experiments-resilient   # clean, fetch, resilient build, experiments
```

Human-review evidence lands in `output/` (Marshall Islands and Equal Earth
plates, water-debris and Majuro contact sheets, atoll canary) with the
PurpleAir and Majuro SVGs under `assets.generated/`. The review pass itself
is visual and does not publish anything; publication remains the separate,
human-invoked AAO target.
