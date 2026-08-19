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
