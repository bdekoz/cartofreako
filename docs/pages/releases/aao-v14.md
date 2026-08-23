# Generated assets v14 in UCB Active Archive Object Storage

[Documentation index](../../../index.md) ·
[Release runbook](README.md) ·
[Consumer release usage](../runtime/consumer-release-usage.md) ·
[v13 AAO publication](aao-v13.md) ·
[v13 to v14 consumer layout](v13-to-v14-consumer-layout.md) ·
[Stage 15 ledger](../../development/20260815_stage-15.md)

Generated assets v14 are the current, live browser-facing release. They are
published separately from any GitHub source release at the immutable Berkeley
S3 prefix `cartofreako/v14/`. This page is the live reference for that
deposit; the older `cartofreako/v12/` and `cartofreako/v13/` records remain
historical evidence and are not rewritten.

## Release identity

| Field | Value |
| --- | --- |
| Endpoint | `https://s3-ewh.ist.berkeley.edu` |
| Signing region | `us-east-1` |
| Bucket | `adekosnik-bucket01` |
| Immutable prefix | `cartofreako/v14/` |
| Upload profile | [`docs/releases/v14-aao-upload-profile.json`](../../releases/v14-aao-upload-profile.json) |
| Source commit | `a51f1d8dc6175981e5dba478b1b59ad8b717fbb4` |
| Source tag | `UNAVAILABLE` (no GitHub tag identifies this generated-assets deposit) |
| Generated release timestamp | `2026-08-16T09:35:46Z` |
| Upload run ID | `20260816T171544Z-70007` |
| Completed at | `2026-08-16T17:21:50Z` |
| Completion marker | [`release.json`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/release.json) |
| Upload receipt | `reports/cartofreako-v14-aao-upload-receipt.json` |
| Archive invoice | `reports/archive-invoice-cartofreako-v14-2026-08-17.pdf` |

## Object layout

```text
cartofreako/v14/
├── products/<lifecycle>/<projection>/
│   ├── master/<stem>.svg.gz
│   ├── print/<stem>.pdf
│   ├── full/<stem>.png
│   ├── thumbnail/<stem>.png            (whole-map projections only)
│   └── screen-1080p/{png,webp}/<stem>.{png,webp}
├── indexes/
│   ├── artifacts-v1.json
│   ├── by-pass/<pass>.json
│   └── by-projection/<projection>.json
├── runtime/api-3/  +  runtime-manifest.json
├── viewer.html
├── README.md
├── SHA256SUMS
└── release.json                        (written last)
```

The `standard` partition holds the complete frozen corpus. The `optional` and
`exploration` partitions are declared by the layout but contain no objects;
their absence is not promotion or omission of unpromoted local experiments.

## Inventory

1349 objects, 1,618,300,704 stored bytes. Breakdown from the sealed
`release.json`:

| Family | Count |
| --- | ---: |
| Master SVG gzip | 217 |
| Print PDF | 217 |
| Full PNG | 217 |
| Screen-1080p PNG | 217 |
| Screen-1080p WebP | 217 |
| Thumbnail PNG | 198 |
| Indexes | 45 |
| Runtime files | 17 |
| `SHA256SUMS` + `release.json` | 2 |

Thumbnails exist for the six whole-map projections (33 each). The five
Myriahedral slice projection directories carry no thumbnail family.

## Corpus composition

217 artifacts across 33 pass IDs, 11 projection IDs, and 14 approved slices,
all `standard`, frozen at the Stage 15A input commit `c3263c1`.

Relative to v13:

| Change | Products |
| --- | --- |
| Added `network-groundstations` | 6 |
| Added `anthropocene-particulate-2025` | 6 |
| Added `anthropocene-particulate-2026` | 6 |
| Removed `cloud-atmosphere` | −6 |
| Removed legacy `anthropocene` observation atlas | −6 |
| Renamed `fiber-synthesized` → `network-fiber` | 6 |
| Renamed `network-infrastructure-sites` → `network-cdn` | 6 |
| Added screen-1080p PNG/WebP derivatives | 217 + 217 |

## Verification

- Upload receipt status `complete`; `standard` verification and
  `full_download` re-hash both passed for all 1,349 objects.
- The archive invoice PDF records the same run and was generated after the
  upload with embedded fonts and rendered QA pages.
- On 2026-08-19 the completion marker returned HTTP 200 from eureka, the
  machine-bound release host. The same endpoint is not reachable from rizal
  without the Berkeley route/VPN, so external link checks must run from
  eureka or a VPN session.

## Known defects (documented, not silently repaired)

1. **Published `viewer.html` is the v13 viewer.** It validates
   `tree/<projection>/svg/...` asset paths and cannot open v14
   `products/...` objects. The corrected viewer is
   [`docs/releases/v14-aao-viewer.html`](../../releases/v14-aao-viewer.html) (GitHub Pages).
   Streaming from that page requires the bucket to serve CORS headers; the
   viewer falls back to a direct compressed download with an explanatory
   message when streaming is blocked. The v14 prefix itself is immutable and
   is not repaired in place; a corrected same-origin viewer ships with the
   next prefix.
2. **`indexes/artifacts-v1.json` doubles the master extension.** The
   `masterSvgGzip` values end in `.svg.gz.gz`; the actual objects are single
   `.svg.gz`. Consumers should derive the master path by removing one `.gz`
   from the indexed value or by taking `full`/`print` paths, which are
   correct.
3. **Slice directories have no thumbnails.** Use `full` PNGs for
   `myriahedral-{afro-eur-asia,americas,antarctic,atlantic,pacific}` previews.

## Consumer quick reference

- Resolve any published product by ID using `indexes/artifacts-v1.json`;
  see [consumer release usage](../runtime/consumer-release-usage.md).
- Authority classes: `archive-art-master` (SVG), `print-presentation` (PDF),
  `full-raster` (PNG), `access-derivative` (screen-1080p PNG/WebP).
- Runtime files live under `runtime/api-3/` with `runtime-manifest.json`.

## Immutability and correction policy

Never repair or replace bytes under `cartofreako/v14/`. The completion marker
is written last and the manifest covers the sealed object set. A correction
to the viewer, an index, or any product requires a new immutable prefix after
a separate review, source release, static asset build, and human-invoked AAO
deposit; it never rewrites this release.

## Rebuild and deposit commands

The staged tree is rebuilt offline with:

```sh
scripts/build-generated-assets-s3-release-v14.sh
```

The applied deposit is a separate, top-level, interactive-only human
operation delegated to the shared transport:

```sh
make release-ucb-aao-s3 \
  UCB_AAO_RELEASE_PROFILE=docs/releases/v14-aao-upload-profile.json \
  UCB_AAO_RELEASE_DATA_ROOT=build/s3-release-v14 \
  UCB_AAO_RELEASE_RECEIPT=reports/cartofreako-v14-aao-upload-receipt.json
```

That target must never run unattended, from CI, or inside another Make
target.
