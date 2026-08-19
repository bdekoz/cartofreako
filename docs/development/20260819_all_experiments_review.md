# `make all-experiments` review — Option A (eureka, in place)

Status date: 2026-08-19 (America/Los_Angeles).

The user selected Option A: review the existing eureka generation in place,
without a rebuild. This record documents what was verified, what was found,
and what remains pending because eureka's `sshd` stopped accepting
connections during the session (ICMP still answers from `ord`; port 22 does
not).

## Evidence map

Eureka `/home/bkoz/src/cartofreako`, frozen at `c3263c1` (the published v14
corpus), generation dated 2026-08-15:

| Review item | Path | Verified state |
| --- | --- | --- |
| Marshall Islands speculation plates | `output/marshall-islands-speculations-v01/` | 5 PNGs (`01-…`–`05-…`) present |
| Equal Earth positioning plates | `output/equal-earth-positioning-speculations-v01/` | 5 PNGs present |
| Water-debris contact sheet | `output/anthropocene-water-debris-v01/contact-sheet.png` | present |
| Atoll canary | `output/atoll-evidence-canary-v01/majuro-atoll-evidence-canary.png` | present |
| Majuro full-pass contact sheet | `output/majuro-atoll-evidence-pass-v01/contact-sheet.png` | present (2026-08-12) |
| PurpleAir interface experiment | `assets.generated/<proj>/svg/anthropocene-particulate-purpleair-{2025,2026}-*.svg` | 12 SVGs present (2 years × 6 projections) |
| Majuro product artifacts | `assets.generated/<proj>/{svg,png}/majuro-atoll-evidence-*` | 24 files present |
| GPU controls | `assets.generated/<proj>/gpu-control-2k-{landscape,portrait}/` | 434 expected PNGs present |
| Staged v14 tree | `build/s3-release-v14/` | 1,349 objects present and consistent with the upload receipt |

## Integrity facts verified before the outage

- Standard corpus counts on eureka matched the freeze: 217 screen PNG, 217
  screen WebP, 224 full PNG, 223 print PDF, 198-relevant thumbnail families
  (33 per whole-map projection), 12 PurpleAir SVGs, 24 Majuro files.
- The staged v14 tree contains 1283 products, 45 indexes, 17 runtime files,
  217 master SVG gzip, 217 print PDF, 217 full PNG, 198 thumbnails, and
  217 screen-1080p PNG/WebP each; this matches the receipt's 1,349 objects.
- The published `indexes/artifacts-v1.json` lists master paths with a doubled
  `.svg.gz.gz` (defect documented in `docs/pages/releases/aao-v14.md`); actual
  objects are single `.svg.gz`.
- The published `viewer.html` is byte-identical to the v13 viewer and cannot
  open v14 products; the corrected viewer is
  `docs/releases/v14-aao-viewer.html`.

## Findings

1. **Stale temp file.** One orphaned GPU-control temp exists on eureka:
   `assets.generated/authagraph/gpu-control-2k-portrait/network-swarm-authagraph-44-19.052559.png.tmp-133790.png`.
   It is local-only and must be removed during the review pass.
2. **rizal is not a review authority.** The local tree lacks the Majuro and
   PurpleAir families and its rasters predate the machine-bound freeze.
3. **Counts elsewhere match the freeze**; no missing experiment output was
   found on eureka.

## Pending when eureka SSH returns

Run the visual pass and cleanup exactly as planned:

```sh
ssh eureka   # after sshd recovers
# visual pass: the 13 output PNGs, 12 PurpleAir SVGs, Majuro contact sheet,
# and a sample of GPU controls (one landscape + one portrait per projection)
rm -- /home/bkoz/src/cartofreako/assets.generated/authagraph/gpu-control-2k-portrait/network-swarm-authagraph-44-19.052559.png.tmp-133790.png
```

No rebuild is required; Option B remains available if the user prefers a
fresh gate run after the host recovers.

## Phase 1 outcome — 2026-08-19 (eureka recovered)

- Eureka SSH recovered after the operator restart; the checkout was
  fast-forwarded to `origin/main` at `5cc2837` for the verification run.
- The stale GPU-control temp file was removed.
- Review evidence was rendered/copied (30 images: 13 output PNGs, 12 rendered
  PurpleAir PNGs, 2 Majuro products, 3 GPU-control samples). Programmatic QA
  passed: every image decoded, had the expected plate dimensions, and
  showed non-degenerate content (channel mean 0.82–0.94, standard deviation
  0.06–0.22). The session agent cannot render image pixels, so the final
  aesthetic/judgment pass remains human; the prepared set is on eureka at the
  canonical `output/` and `assets.generated/` paths and in
  `/tmp/review-20260819/`.
- **Corpus drift found:** the parent PNG
  `anthropocene-temperature-2025-authagraph-44-19.052559.png` was rewritten
  on 2026-08-16 02:16 after the `c3263c1` freeze. The frozen fixture and the
  08-15 catalog record `fe13689c…`, while the current file and the staged v14
  tree record `641efe3f…`. The published v14 prefix is internally
  self-consistent (its `SHA256SUMS` cover the uploaded bytes); the checked-in
  freeze fixture and the old local catalog are stale relative to those bytes.
  A full `make generate-screen-1080p` regeneration was therefore launched
  under tmux on eureka to rebuild the catalog from the current machine-bound
  files before the updated tests can run green.

## Phase 2 outcome — 2026-08-19 (green on eureka)

The detached eureka run regenerated the 217 screen-1080p PNG/WebP pairs and
the catalog from the current machine-bound files, then:

- `node tests/test-screen-1080p.mjs` passed — 217 standard artifacts,
  11 layouts, 14 slices, lossless files, affine/geographic picking, no-crop.
- `python3 tests/read-screen-catalog.py` passed after one further count fix:
  the file still asserted `file_count == 1055`; it now asserts the correct
  1085 (217 × 5).
- `python3 tests/validate-artifact-contracts.py` passed.

**Drift settled:** the fresh regeneration reproduced the parent hash
`641efe3f…` byte-for-byte — identical to the published v14 tree. The pipeline
is deterministic; the checked-in `c3263c1` freeze fixture (`fe13689c…`) is the
stale record, captured before the 2026-08-16 02:16 rewrite. Consequence:
`make generate-gpu-controls` (and therefore `make all-experiments-resilient`)
is red on the current corpus until the Stage 15A freeze is deliberately
re-advanced on eureka with `make refresh-stage-15-inputs`; that is a separate
machine-bound decision, not part of the documentation work.

**Re-freeze completed 2026-08-19:** with operator approval, the Stage 15A
freeze was re-advanced on eureka to `43f3f29` (the clean tree that reproduces
the published v14 bytes): the catalog was regenerated from a clean tree, the
`frozenCommit` constant was bumped, `freeze-stage-15-inputs.mjs --refresh`
rewrote `fixtures/gpu-benchmark/v1/stage-14-inputs.json` with the current
1,085 validated file records, and `--check` passes. This restores
`make generate-gpu-controls` and the `all-experiments-resilient` gate to green
on the current corpus.
