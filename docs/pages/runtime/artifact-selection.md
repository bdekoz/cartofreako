---
layout: default
title: Artifact catalog, selection, and decision receipts
---

# Artifact catalog, selection, and decision receipts

[Runtime index](README.md) ·
[1080p and AI-agent products](ai-agent-and-1080p-gaming.md) ·
[Stage 14 ledger](../development/stage-14.md)

Stage 14 provides a deterministic, offline bridge from an agent or application
request to one existing Cartofreako artifact. It does not authorize external
data, accept a license, publish, release, upload, interpret research evidence,
or transfer training data.

## Catalog surface

`make generate-screen-1080p` builds
`assets.generated/catalog/artifacts-v1.json` from the checked
[`standard-artifact-manifest-v1.json`](../../../contracts/standard-artifact-manifest-v1.json).
That Make-declared manifest now contains 211 standard products across 32 pass
IDs, 11 layouts, and 14 approved slices. It excludes authorized optional and
exploration-only products.

The Stage 15 benchmark fixture separately freezes the earlier Stage 14
205-product/31-pass catalog. Updating the live access catalog does not rewrite
that benchmark identity.

Each catalog record keeps the authoritative SVG or explicit SVG-gzip, print
PDF, and 3840-pixel PNG distinct from the 1920 × 1080 PNG/lossless-WebP access
derivatives. It records hashes, byte counts, authority classes, carrier and
artifact frames, non-zero slice origins, exact affine matrices, source period
when present, and `UNAVAILABLE` when license, governance, transparency, or
other evidence metadata is not established.

## Request and receipt

The two JSON Schema Draft 2020-12 contracts are:

- [`artifact-request-v1.schema.json`](../../../contracts/artifact-request-v1.schema.json)
- [`artifact-decision-receipt-v1.schema.json`](../../../contracts/artifact-decision-receipt-v1.schema.json)

A request supplies hard constraints, ordered preferences, and—only when the
caller wants them—an ordered `fallbackSequence`. Standard is the only default
lifecycle. Optional requires `optionalOptIn`; exploration-only requires both
`explorationOptIn` and an explicit human-review requirement.

The selector relaxes only these fields when the request names them:
`projectionIds`, `formats`, `maxBytes`, `viewport`, and `authorityClasses`.
It cannot relax lifecycle, checksum, evidence, governance, interaction, or
human-review boundaries. Every applied relaxation records its before/after
values and reason inside the hashed decision core.

Run the JSON-only CLI with:

```sh
scripts/select-artifact.mjs request.json \
  assets.generated/catalog/artifacts-v1.json receipt.json
```

The receipt includes the normalized request and hash, exact catalog hash,
selection or `no-match`, all evaluated variants and rejection reason codes,
the selected file and affine transform, explicit `UNAVAILABLE` metadata, and
a non-authority statement. Timestamps remain outside the deterministic core.
A human override creates a new receipt referencing the prior hash; it never
rewrites the original.

## Verification and clean-room handoff

```sh
make check-artifact-selection
make check-screen-1080p
```

The selector gate makes Node, headless Chrome, and a dependency-free Python
consumer choose the same golden artifact and decision-core hash. It also
checks catalog-order independence, explicit fallbacks, standard lifecycle
containment, missing metadata, tampered hashes, `no-match`, and append-only
overrides.

The screen gate validates all 211 records, 1,055 referenced files, no-crop
contain placement, lossless PNG/WebP identity, carrier-aware reverse picks,
all approved slices, and all eleven layouts. The independent
[`read-screen-catalog.py`](../../../tests/read-screen-catalog.py) imports no
Cartofreako code: it recomputes both affine matrices from each declared frame,
verifies every hash, and agrees on the exact inventory.

Public v13 S3 galleries predate these Stage 14 derivatives. Their thumbnails
continue to link directly to full 3840-pixel PNG, SVG-gzip viewer, and print
PDF. Screen URLs must not be advertised until a later, separately
human-invoked v14 UCB AAO/S3 deposit actually contains them.
