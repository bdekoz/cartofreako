# Stage 15 GPU consumer products and benchmark ledger

[Documentation index](../../../index.md) ·
[Development records](README.md) ·
[Stage 14 convergence ledger](stage-14.md) ·
[AI-agent and 1080p consumer plan](../runtime/ai-agent-and-1080p-gaming.md)

## Status

**Planned.** Stage 15 has no implemented GPU product, benchmark target, or
promotion decision. This ledger establishes the handoff so Stage 14 can close
with a stable print, projection, catalog, and 1080p baseline instead of
changing scope while GPU experiments are in progress.

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

## Stage 14 benchmark handoff

Stage 15 benchmarks from a frozen Stage 14 input manifest. The first harness
can use the existing 24-artifact canary—Water, Anthropocene Temperature 2026,
Network Infrastructure Sites, and Bathymetry Roulette across all six
projection families. A promotion decision waits for Stage 14 to freeze the
complete standard whole-map and approved-slice catalog.

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

## Planned products

| Candidate | Role | Initial rule |
| --- | --- | --- |
| Stage 14 PNG and lossless WebP | Access and transfer baseline | Preserve the exact 1920 × 1080 files and hashes; do not regenerate them inside the benchmark |
| 2K reference PNG | Lossless power-of-two control | Exact 2048 × 1024 `contain` canvas, declared padding, full projection visible, same parent as Stage 14 |
| 2K WebP | Transfer/decode comparison | Test lossless first; any lossy profile receives its own ID, settings, hashes, and visual threshold |
| KTX2/Basis candidates | GPU-upload candidates | Evaluate ETC1S and UASTC profiles, mip levels, supercompression, alpha, orientation, and color-space metadata separately |
| Topology mask | Qualified-picking aid | Implement before feature masks; encode native cell and component losslessly with a checked value dictionary and matching transform |
| Feature-ID mask | Visible-feature picking aid | Consider only after the topology-mask contract passes and source licensing permits redistribution |
| Float32 geometry adapter | Dynamic GPU path | Keep Float64 CPU coordinates authoritative and measure forward, screen, and reverse-selection differences before adoption |

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

## Proposed anthropocene-water-debris-scale evidence tier

Investigate water-based debris phenomena like The Great Pacific Garbage Patch, only extend scope to all world locations. Also track river waste and debis.

Sources
https://theoceancleanup.com

Suggsted generator profile pass changes:
move 'anthropocene' to 'anthropocene-temperature'

make this 'antropocene-water-debris'


Evaluate feasibility and propose a plan for a new generate pass for " anthropocene-water-debris" detailing location, shape, depth
src.generate/generate-anthropocene-water-debris.cc


Research, evaulate, and suggest plan before continuing.
Then detail plan and way for confirmation before implementing.

After confirmation, assume authorized and proceed and finish work without prompting.

## Proposed atoll-scale evidence tier

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

## Staging plan

| Stage | Work | Exit gate |
| --- | --- | --- |
| **15A — benchmark contract** | Freeze the Stage 14 handoff manifest; define result schema, corpus, deterministic derivation recipes, benchmark harness, and lossless reference checks | A rerun identifies every input and environment and cannot mutate a Stage 14 parent |
| **15B — texture formats** | Produce 2K PNG/WebP controls and pinned KTX2/Basis candidates; measure size, decode, upload, memory, first frame, and visual behavior | Per-pass and per-machine evidence supports retaining or rejecting each profile without one aggregate quality claim |
| **15C — topology masks** | Define a lossless native-cell/component mask and value dictionary, then test qualified picking across all six families, including Star-X components | Mask and display transforms match exactly; cuts and overlaps retain complete candidate semantics |
| **15D — dynamic geometry** | Audit Float32 conversion, worker transfer, WebGL/WebGPU upload, cancellation, and representative interactive loads | Positional and candidate-set tolerances are declared and pass while Float64 remains authoritative |
| **15E — consumer trials** | Extend the checked Stage 14 Three.js flat-plane canary to accepted GPU texture, mask, and Float32 profiles; consider MapLibre, Godot, or Unity adapters only against the same catalog and projection contracts | Each adapter reproduces the same flat-map placement and picking fixtures without inventing projection semantics |
| **15F — promotion decision** | Compare measured benefit, tooling/license burden, reproducibility, accessibility, fallbacks, and archive separation | Accepted profiles get explicit product IDs and checks; rejected profiles remain documented evidence rather than becoming silent defaults |
| **15G — atoll-scale evidence** | Define the dated, uncertainty-bearing topobathymetry, inundation, freshwater, infrastructure, shoreline, reef, and ocean-heat contract; build a Marshall Islands canary before any global generalization | Every visible layer and scenario is source-traceable, scale-qualified, reverse-addressable, and reviewed before it can leave exploration-only status |

## Proposed repository surface

Names remain provisional until implementation:

```text
contracts/gpu-benchmark-v1.schema.json
fixtures/gpu-benchmark/v1/stage-14-inputs.json
scripts/generate-gpu-canary.mjs
scripts/benchmark-gpu-products.mjs
tests/test-gpu-products.mjs
reports/stage-15-gpu-benchmark.json
reports/stage-15-gpu-benchmark.md
contracts/atoll-evidence-v1.schema.json
fixtures/atoll-evidence/v1/manifest.json
reports/stage-15-atoll-evidence-canary.md
```

Candidate Make targets are `generate-gpu-canary`, `check-gpu-products`, and
`benchmark-gpu-products`. Generation and checking should be deterministic and
offline once tools are installed. Hardware timing remains an explicitly
invoked benchmark and must not enter `make all`, ordinary `make check`, GitHub
release, or UCB AAO/S3 release.

## Promotion and release rule

GPU products begin as exploration-only development artifacts. A format becomes
optional only after its toolchain, license, determinism, metadata, visual QA,
positional tolerance, and fallback behavior pass. Promotion to the standard
generation graph requires a separate reviewed decision with no change to the
authoritative archive/art, print, full-raster, or Stage 14 screen products.

GitHub source publication and UCB AAO/S3 preservation remain separate human
decisions. No benchmark target invokes either path.
