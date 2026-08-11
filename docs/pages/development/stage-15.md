# Stage 15 GPU consumer products and benchmark ledger

[Documentation index](../../../index.md) ·
[Development records](README.md) ·
[Stage 14 convergence ledger](stage-14.md) ·
[AI-agent and 1080p consumer plan](../runtime/ai-agent-and-1080p-gaming.md)

## Status

**Bounded active scope implemented and locally verified 2026-08-10.** The
active scope is 15A
(frozen handoff and benchmark contract), 15B (lossless landscape and portrait
2K controls), 15I (local consumer-oriented CDN/WASM layout), and two
exploration-only research prototypes. Stages 15C through 15H are deferred.
No compressed texture, hardware benchmark, picking mask, Float32 geometry,
engine adapter, promotion, release, or upload was implemented or implied.

## Purpose and boundary

Stage 15 measures whether GPU-oriented derivatives materially improve game,
installation, and interactive-atlas delivery. It owns power-of-two texture
derivatives, GPU compression experiments, topology and feature masks,
Float32 positional audits, upload/decode measurements, and later
engine-specific import examples.

Stage 15 does not redefine projection mathematics, pass content, source
authority, archive/art masters, large-format print products, the 3840-pixel
full raster, or the Stage 14 1920 × 1080 access derivative. It cannot publish
to GitHub or UCB AAO/S3, accept a license, authorize an external source, or
promote an experimental format merely by running a benchmark.

All interrupted projections remain flat-map textures. No Stage 15 artifact may
be described or sampled as an equirectangular globe texture.

The active subset stops before compressed texture experiments or performance
claims. Stage 15A defines a future result and environment envelope but neither
installs encoders nor executes GPU timing. Stage 15I builds and checks only a
local candidate object tree; it has no network, credential, release, or upload
operation.

## Stage 14 benchmark handoff

Stage 15 benchmarks from the frozen Stage 14 standard input manifest: 205
artifacts across 31 pass IDs, 11 layouts, and 14 approved slices. A first
hardware canary may select a smaller deterministic subset through the Stage 14
request/decision-receipt interface, but the benchmark must retain the full
manifest identity and cannot redefine the baseline by filename convention.

The handoff records, without rewriting:

- the Stage 14 source revision, runtime API 3 and geometry ABI 1 manifests;
- canonical SVG/PDF and exact-ratio print geometry plus the
  `check-print-contract` result;
- each authoritative 3840-pixel parent and SHA-256;
- each exact 1920 × 1080 PNG/lossless-WebP baseline, content rectangle,
  padding color, affine transform, parent identity, and SHA-256;
- projection, layout, slice, lifecycle, authority class, source period,
  license, limitation, and interaction metadata; and
- the completed Stage 14 request/decision receipt when selection is performed
  through an agent workflow.

A 2048 × 1024 texture reference is derived from the same authoritative
3840-pixel parent as the Stage 14 screen product. It is never produced by
upscaling the 1920 × 1080 derivative. If a Stage 14 parent, transform, or
catalog record changes, its benchmark case receives a new identity and must be
rerun.

Stage 15A begins from a newly regenerated ignored artifact catalog stamped by
the clean frozen Stage 14 commit `750efb321cc5553c7f0f7aa6d64e47ed9f2e8bef`.
The previously present catalog identified commit `3a861c7` and a modified
tree; it was not eligible for the handoff. The checked freeze records the
clean commit, catalog hash, standard-manifest hash, parent hashes, and existing
lossless-screen hashes without rewriting any authoritative artifact.

## Planned products and current disposition

| Candidate | Role | Disposition |
| --- | --- | --- |
| Stage 14 PNG and lossless WebP | Access and transfer baseline | **Active 15A input.** Preserve the exact 1920 × 1080 files and hashes; do not regenerate them inside a benchmark |
| Landscape 2K PNG | Lossless power-of-two control | **Active 15B.** Exact 2048 × 1024 `contain` canvas, declared padding, full projection visible, same 3840-pixel parent as Stage 14 |
| Portrait 2K PNG | Lossless vertical control | **Active 15B.** Exact 1024 × 2048 `contain` canvas with the same no-crop, parent, color, and transform rules |
| 2K WebP | Transfer/decode comparison | **Deferred 15C** |
| KTX2/Basis candidates | GPU-upload candidates | **Deferred 15C** |
| Hardware timing | Decode, upload, memory, and first-frame evidence | **Deferred 15D** |
| Topology and feature-ID masks | Qualified-picking aids | **Deferred 15E** |
| Float32 geometry adapter | Dynamic GPU path | **Deferred 15F**; Float64 remains authoritative |
| Additional engine adapters | Consumer trials beyond the existing Three.js canary | **Deferred 15G** |
| Product promotion | Standard or optional lifecycle decision | **Deferred 15H** |

PNG is the visual reference, not necessarily the intended runtime transfer
format. A single aggregate score must not hide that flat water, translucent
temperature fields, point networks, and moiré-prone bathymetry respond very
differently to compression.

## Benchmark contract

Every run emits a machine-readable result plus a compact human summary. The
result records:

- input/product hashes; encoder, decoder, browser/runtime, driver, operating
  system, and dependency versions; exact options; color space; alpha mode;
  mip policy; and determinism status;
- encoded bytes, compression ratio, encode time, CPU decode time, GPU upload
  time, time to first usable frame, peak host memory, estimated texture
  memory, and steady-state sampling behavior;
- cold and warm observations, a warm-up count, repetition count, median, and
  tail measurement rather than one favorable timing;
- pixel and structural error against the lossless reference, transparency and
  edge behavior, title/legend legibility, thin-line retention, field-opacity
  preservation, and pass-specific moiré observations;
- Float64-to-Float32 projected displacement, screen-pixel displacement,
  reverse residual, status, and complete candidate-set agreement at cuts and
  overlaps; and
- unsupported operations, failures, warnings, and human visual-review
  disposition without silently dropping a product or machine.

Visual metrics are supporting evidence, not the sole acceptance rule. The
review must inspect representative flat fills, translucent fields, fine
networks, text, boundaries, transparency, and high-frequency curve work at
native display scale.

## Hardware matrix

The first reproducible baseline is the existing Framework Desktop with AMD
Ryzen AI Max+ 395, integrated Radeon 8060S, 16 physical cores/32 hardware
threads, and approximately 125 GiB of reported memory. Each run must capture
the then-current GPU driver, browser/runtime, power profile, display/headless
mode, and available memory rather than treating the machine name as a complete
environment record.

Broad adoption additionally requires at least one discrete-GPU result and one
browser GPU path. Results are reported per machine; they are not merged into a
claim of universal performance. Software rendering may be retained as a
correctness fallback but cannot serve as GPU-performance evidence.

## Research prototype R2 — anthropocene water debris

The approved prototype is a source-and-contract feasibility study, not a data
download or generation pass. It must distinguish observed shoreline or
surface debris, modeled concentration fields, modeled river emissions,
recorded cleanup operations, and unavailable depth. A two-dimensional patch
shape must never be presented as an observed three-dimensional debris body.

The source inventory begins with [The Ocean Cleanup](https://theoceancleanup.com/)
and public NOAA marine-debris records. Before a generator is proposed, the
prototype records access method, reuse rights, observation/model period,
spatial and temporal resolution, units, uncertainty, and whether coordinate
or depth observations are actually available. Unknown depth is
`UNAVAILABLE`, not zero.

A future `anthropocene-water-debris` generator and pass may be specified only
after the feasibility report identifies a redistributable spatial source. It
is not implemented or promoted in this stage. The existing `anthropocene`
pass remains the stable legacy multi-source climate, fire, and smoke atlas;
the dated `anthropocene-temperature-2025` and
`anthropocene-temperature-2026` pass IDs also remain unchanged.

The checked outcome is
[Stage 15 R2 — anthropocene water-debris feasibility](../../../reports/stage-15-water-debris-feasibility.md).

## Research prototype R1 — atoll-scale evidence

Add an atoll-scale evidence tier for place-specific research, beginning with
the Marshall Islands experiments. Bring in high-resolution topobathymetry,
inundation scenarios, freshwater, infrastructure, shoreline, reef, and
ocean-heat data, with explicit uncertainty and observation/source dates.

This tier is an evidence project, not a raster-resolution shortcut. Every
layer must retain source identity, spatial and temporal resolution, vertical
datum where applicable, license and redistribution terms, uncertainty or
scenario assumptions, preparation history, and the date or period that the
observation represents. Scenario output must remain distinguishable from an
observation, and missing uncertainty must be `UNAVAILABLE` rather than zero.

Atoll-scale products begin as exploration-only. Promotion requires local and
regional review of feature meaning and omission, an explicit relationship to
the global atlas layer, documented scale limits, and a decision about whether
the product is suitable for research comparison, public interpretation, or
visual speculation only. The tier must support forward and reverse projection
fixtures so a selected pixel, feature, or scenario can be traced back to its
source coordinate and evidence record.

The Stage 15 prototype is limited to a checked contract, a source/rights
inventory, one Marshall Islands canary-manifest plan, and explicit
`UNAVAILABLE` fields. It performs no restricted download, creates no new
evidentiary render, and makes no promotion decision.

The checked outcome is
[Stage 15 R1 — atoll-scale evidence canary](../../../reports/stage-15-atoll-evidence-canary.md).

## Active 15I — consumer-oriented CDN and WASM layout

Stage 15I treats the object tree as a versioned CDN data ABI. It compares the
immutable v13 publication with a proposed v14 layout that adds machine-readable
indexes, stable lifecycle partitions, declared media and cache policy, and a
runtime manifest for browser, game, and AI-agent consumers.

Implementation is local only: a checked schema, fixture, builder, checker, and
v13-to-proposed-v14 compatibility document. The builder may copy local runtime
files into an ignored staging tree, but it cannot access S3 or invoke release
transport. Shared AAO publication mechanics remain owned by
`alpha60-clusterops/bin/load-s3-aao`; Cartofreako supplies manifests and a thin
release-specific wrapper only.

The review covers immutable or content-addressed runtime identity, correct
WASM and module MIME types, cache policy, optional precompression, and the
split between core projection runtime and optional canvas, SVG, D3, Three.js,
worker, and catalog helpers. A versioned immutable runtime directory is
preferred where independently hashed Emscripten loader/WASM renames would
break their default pairing. No v14 archive is rebuilt, released, or uploaded
by this work. The compatibility reference is v13-to-proposed-v14, not
v14-to-v14.

The checked compatibility and implementation reference is
[v13 to proposed-v14 consumer layout](../releases/v13-to-v14-consumer-layout.md).

## Implemented active results

| Work | Local result | Identity or evidence |
| --- | --- | --- |
| **15A** | Frozen 205 standard artifacts, 31 pass IDs, 11 layouts, and 14 approved slices from the clean Stage 14 catalog | Commit `750efb321cc5553c7f0f7aa6d64e47ed9f2e8bef`; input-fixture SHA-256 `af793ba88ebaead4aeedfdf179e35a1a786eab5ff7e2cd2f51ca086b4970df8b` |
| **15B** | Generated and checked 205 landscape 2048 × 1024 PNGs and 205 portrait 1024 × 2048 PNGs | 410 files; 141,014,973 bytes; generated-catalog SHA-256 `901fb44bdc1bd70acd781f66ba0e4b277adfaf0d66ec022becda9b7ec215ccb4` |
| **15I** | Built a 61-file local candidate with one primary index, 31 pass indexes, 11 projection indexes, and 16 runtime files | 1,291,121 bytes; local `release-layout.json` SHA-256 `763c86011c6c9a8db56f90a9fac1bceb357a0893991c863f68fd5a4b85289e3d`; no `release.json` |
| **R1** | Validated the Majuro canary contract and source/rights inventory | No download, evidence render, or promotion |
| **R2** | Validated the water-debris evidence classes and feasibility inventory | No download, generator, pass rename, or promotion |

The 15B generator hashes every authoritative full PNG before and after
conversion. Both controls use `contain`, Lanczos resampling, the WCAG-light
gray `#f4f5f5` background, opaque 8-bit sRGB PNG, and no crop. They are built
directly from the 3840-pixel parent, never from the 1080p derivative. The
portrait control intentionally has substantial letterboxing for landscape
layouts; it preserves the entire flat projection instead of zooming or
cropping.

A representative water-plate contact-sheet review covered all eleven layouts
in both orientations. All maps were fully contained, the vertical Star-X
product retained its central black star and Antarctic component, and no
content edge was clipped. This is control-product QA, not a GPU quality or
performance claim.

The implementation remains explicit and offline:

```sh
make freeze-stage-15-inputs
make check-gpu-controls
make check-consumer-release-layout
make check-stage-15-research-prototypes
make check-stage-15-active
```

These targets are deliberately absent from `make all`, ordinary `make check`,
GitHub release, and UCB AAO/S3 release.


## Staging plan

| Stage | Disposition | Active work or deferral |
| --- | --- | --- |
| **15A — frozen handoff** | **Approved and active** | Freeze the clean Stage 14 catalog, hashes, deterministic corpus, and future benchmark result/environment envelope |
| **15B — lossless 2K controls** | **Approved and active** | Produce checked 2048 × 1024 landscape and 1024 × 2048 portrait PNG controls from authoritative full PNG parents |
| **15C — compressed formats** | **Deferred** | Lossless/lossy WebP and KTX2/Basis profiles, encoder installation, mips, and compression comparisons |
| **15D — hardware benchmark** | **Deferred** | Decode, GPU upload, memory, first-frame, and repeated machine timing |
| **15E — topology and feature masks** | **Deferred** | Native-cell/component masks and licensed visible-feature IDs |
| **15F — Float32 geometry** | **Deferred** | Dynamic geometry conversion and positional/reverse residual audit |
| **15G — consumer trials** | **Deferred** | Additional browser and game-engine adapters |
| **15H — promotion** | **Deferred** | Lifecycle, release, fallback, and adoption decision |
| **15I — CDN/WASM layout** | **Approved and active** | Build and check a local consumer-oriented object-tree fixture; document v13-to-proposed-v14 compatibility |
| **R1 — atoll evidence** | **Approved prototype only** | Contract, source/rights inventory, and Marshall Islands canary plan; no evidence render |
| **R2 — water debris** | **Approved prototype only** | Contract and feasibility/source inventory; no generator or pass promotion |

## Implemented repository surface

The active implementation uses:

```text
contracts/gpu-benchmark-v1.schema.json
fixtures/gpu-benchmark/v1/stage-14-inputs.json
scripts/freeze-stage-15-inputs.mjs
scripts/generate-gpu-controls.mjs
assets.generated/<projection>/gpu-control-2k-{landscape,portrait}/*.png
assets.generated/catalog/gpu-controls-v1.json
tests/test-gpu-controls.mjs
tests/validate-stage15-contracts.py
contracts/consumer-release-layout-v1.schema.json
fixtures/consumer-release-layout/v1/manifest.json
scripts/build-consumer-release-layout.mjs
scripts/check-consumer-release-layout.mjs
docs/pages/releases/v13-to-v14-consumer-layout.md
contracts/atoll-evidence-v1.schema.json
fixtures/atoll-evidence/v1/manifest.json
reports/stage-15-atoll-evidence-canary.md
contracts/water-debris-evidence-v1.schema.json
fixtures/water-debris-evidence/v1/manifest.json
reports/stage-15-water-debris-feasibility.md
```

Active Make targets are `freeze-stage-15-inputs`,
`generate-gpu-controls`, `check-gpu-controls`,
`build-consumer-release-layout`, `check-consumer-release-layout`, and explicit
nonproduction checks for the two research prototypes. The deferred
`benchmark-gpu-products` target is not added. Nothing in Stage 15 enters
`make all`, ordinary `make check`, GitHub release, or UCB AAO/S3 release
without a later promotion decision.

## Promotion and release rule

GPU products begin as exploration-only development artifacts. The approved
scope creates lossless controls and local layout evidence only; it creates no
compressed or GPU-promoted product. A future format becomes optional only
after its toolchain, license, determinism, metadata, visual QA, positional
tolerance, and fallback behavior pass. Promotion to the standard generation
graph requires a separate reviewed decision with no change to the
authoritative archive/art, print, full-raster, or Stage 14 screen products.

GitHub source publication and UCB AAO/S3 preservation remain separate human
decisions. No benchmark target invokes either path.
