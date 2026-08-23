---
layout: default
title: v13 to v14 consumer layout
---

# v13 to v14 consumer layout

[Documentation index](../README.md) ·
[Release and preservation records](README.md) ·
[v14 AAO release record](aao-v14.md) ·
[Stage 15 ledger](../../development/20260815_stage-15.md) ·
[v13 publication](aao-v13.md)

> **Superseded as a proposal; kept as the migration reference.** v14 is now
> the published AAO release. The live description of the applied layout,
> counts, verification, and known defects is
> [aao-v14.md](aao-v14.md). This page retains the cutover table below as the
> v13 → v14 path-mapping evidence.

This document records the Stage 15I layout experiment that became the applied
v14 AAO release. The original candidate tree is built beneath
`build/consumer-release-layout-v1/`; the applied release tree adds the
products, indexes, runtime, manifest, and completion marker beneath the
immutable `cartofreako/v14/` prefix. This page remains the v13 → v14
path-mapping reference.

## Outcome

Keep the projection-first v13 products recognizable, but add a small
machine-readable control plane and explicit lifecycle partitions. Preserve
Emscripten loader/WASM filenames together beneath immutable
`runtime/api-3/`; their individual SHA-256 values live in a runtime manifest.
Renaming the loader and companion WASM independently would break the default
loader lookup and offers no benefit inside an already immutable versioned
release prefix.

The unpromoted Stage 15 2K controls are excluded. They remain local benchmark
evidence until a separate promotion decision.

## Object-path comparison

| Role | Immutable v13 | Proposed v14 |
| --- | --- | --- |
| Completion marker | `release.json` | `release.json`, still written only by the human-invoked shared transport |
| Artifact inventory | release-level counts and `SHA256SUMS` | `indexes/artifacts-v1.json` plus pass and projection indexes |
| SVG master | `tree/<projection>/svg/<stem>.svg.gz` | `products/<lifecycle>/<projection>/master/<stem>.svg.gz` |
| Print PDF | `tree/<projection>/pdf/<stem>.pdf` | `products/<lifecycle>/<projection>/print/<stem>.pdf` |
| Full PNG | `tree/<projection>/png/<stem>.png` | `products/<lifecycle>/<projection>/full/<stem>.png` |
| Thumbnail | `tree/<projection>/thumbnail/<stem>.png` when present | `products/<lifecycle>/<projection>/thumbnail/<stem>.png` when present |
| 1080p PNG/WebP | absent | `products/<lifecycle>/<projection>/screen-1080p/{png,webp}/...` |
| Runtime | absent as a release contract | `runtime/api-3/` with a SHA-256 runtime manifest |

The candidate uses `standard`, `optional`, and `exploration` partitions so a
consumer can distinguish support status without parsing a filename. The
current frozen corpus populates only `standard`; absence is not promotion of
optional or exploratory work.

## Indexes for browsers, games, and agents

The primary index preserves 205 stable artifact IDs and their pass,
projection, layout, slice, authority, hashes, v13 locations, and proposed v14
locations. Thirty-one pass indexes and eleven projection/layout indexes point
back to those IDs. This lets a consumer make one bounded request for a known
interest instead of listing an S3 prefix or inferring semantics from stems.

Indexes are versioned data, not a search service. They contain no credentials,
signed URLs, user state, or mutable ranking. A future agent can pair them with
the existing artifact-request and decision-receipt schemas and retain an
auditable selection result.

## Runtime delivery

The core set is the projection loader, companion WASM, high-level projection
API, and declarations. Screen transforms, artifact selection, workers,
canvas/SVG/D3/Three.js helpers, and their declarations are optional. Files
retain their import-compatible basenames beneath the versioned directory;
`runtime-manifest.json` records byte length, SHA-256, MIME type, role, and
core/optional classification.

Required delivery metadata is explicit:

- `.wasm`: `application/wasm`;
- `.mjs`: `text/javascript`;
- `.json`: `application/json`;
- `.svg.gz`: `application/gzip` with no `Content-Encoding` because the viewer
  explicitly decompresses the object;
- PNG, WebP, and PDF: their standard media types; and
- immutable payloads: `public,max-age=31536000,immutable`.

The completion marker uses `no-store` so a failed pre-publication lookup is
not mistaken for durable incompleteness. JSON/module gzip and WASM Brotli are
documented candidates, not built products: sidecars require a checked browser
loader, correct HTTP metadata, fallback, and byte verification together.

## Local commands and release boundary

```sh
make build-consumer-release-layout
make check-consumer-release-layout
```

Both commands are offline and local. They do not run `rclone`, resolve S3
credentials, build a release archive, create a completion marker, or invoke
the shared transport. A future UCB AAO/S3 action remains a separate,
human-invoked wrapper around
[`alpha60-clusterops/bin/load-s3-aao`](https://github.com/alpha60-devops/alpha60-clusterops/blob/main/bin/load-s3-aao).

## Cutover policy

No compatibility alias is required: documentation and consumers were
re-indexed for v14, and the table above remains the migration reference.
Immutable v13 paths and bytes must not be rewritten; any future layout change
begins at a new prefix after a separate review, source release, static asset
build, and human-invoked AAO deposit.
