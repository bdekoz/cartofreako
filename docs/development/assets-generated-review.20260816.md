
- big question: can the following be consolidated?

  - gpu-control-2k-landscape
  - screen-1080p
  - screen-1080p-webp
  
  and how does this relate to
  - png, which is a 4k landcape portrait?
  
  
  Should all of these be webp? Should the 2k resolutions just coalesce down to one 1080p lanscape webp representation?
  
- render fail: gpu-control-2k-portrait all frames are clipped, the image needs to be rotated 90 degrees

anthropocene-temperature-202? , bump up opacity to 80%

- render fail: network-fiber-authagraph-44-19.052559.png, looks better, but there is one render bug in this, a green line that runs from the left to the right all through the image, this is probably an edge folding bug? the error line hits the west coast of the usa around seattle or vancouver, and south ameria around sao palo

- render pass: network-fiber-ck-44-22.png
no green line in this one

---

## Improvement plan proposal

### 1. Treat the raster trees by role, not by extension

Current files should be classified before consolidation:

| Tree | Proposed role | Consolidation decision |
| --- | --- | --- |
| `assets.generated/<projection>/png/` | Authoritative full-raster 3840px parent | Keep as the archive/print-derived master. Do not demote to WebP. |
| `assets.generated/<projection>/screen-1080p-webp/` | Preferred lossless screen/access derivative | Keep. This is the likely web/GPU default. |
| `assets.generated/<projection>/screen-1080p/` | PNG fallback for consumers that cannot take lossless WebP | Keep only during a transition period, then mark non-authoritative or stop publishing. |
| `assets.generated/<projection>/gpu-control-2k-landscape/` | Stage 16 benchmark fixture, not a standard screen derivative | Keep separate. Do not fold into `screen-1080p`. |
| `assets.generated/<projection>/gpu-control-2k-portrait/` | Stage 16 benchmark fixture | Fix orientation/clipping first; retain only if the benchmark contract actually needs portrait controls. |

Recommendation: do **not** collapse everything to one 1080p landscape WebP. Preserve
the full PNG parent and the lossless screen WebP as distinct roles. The 2K GPU
controls should be consolidated only after Stage 16B/16F decides which consumer
formats are being benchmarked.

If the benchmark target is really 1080p landscape, change the GPU-control recipe
from `2048x1024` to `1920x1080` and rename the output tree, rather than
pretending `screen-1080p-webp` is the benchmark control.

### 2. Fix `gpu-control-2k-portrait` clipping

Suspected cause: the portrait recipe is using the same `magick` contain/resize
pipeline as landscape, so non-landscape source frames are being padded or
cropped without an explicit orientation decision.

Plan:

1. Add an orientation assertion to `scripts/generate-gpu-controls.mjs` for the
   portrait recipe: inspect the authoritative source frame and require the
   generated content rectangle to remain inside the portrait canvas.
2. Generate one failing control manually and compare its `contentRectangle`
   with the source frame and expected 90° rotation.
3. Apply the smallest targeted fix: either rotate portrait-source parents
   before `containTransform`, or swap the recipe canvas when the source is
   portrait-dominant.
4. Regenerate and run `make check-gpu-controls` plus the Stage 15 contract
   checker.

### 3. Bump anthropocene-temperature opacity to 80%

The current profile sets:

```text
data_graphic_opacity: 0.60
```

Change both checked profiles to `0.80`:

- `assets.static/anthropocene/anthropocene-temperature-2025-profile.json`
- `assets.static/anthropocene/anthropocene-temperature-2026-profile.json`

Then regenerate:

```sh
make generate-anthropocene-temperature-2025
make generate-anthropocene-temperature-2026
```

Regenerate dependent PNG/screen trees and update the generated-artifact
checksums/fixtures only after a side-by-side review of the 0.80 result.

### 4. Fix the AuthaGraph network-fiber green seam line

Likely cause: a submarine-cable path crosses an AuthaGraph periodic/seam
boundary and the current path projector connects the two projected sides with
a long straight segment. Cahill-Keyes is clean because it has explicit
fold-path handling; AuthaGraph is classified as `periodic` and may be reaching
only the generic coordinate-wrap fallback.

Plan:

1. Reproduce narrowly:

```sh
make generate-network-fiber-authagraph
```

2. Identify the offending route by scanning the generated
   `network-fiber-authagraph-44-19.052559.svg` for a path segment whose
   projected endpoints are near opposite horizontal edges but whose geographic
   separation is small.
3. Instrument `project_path_detailed()` for AuthaGraph to report
   `cell_transitions`, `periodic_wraps`, `cuts`, and the offending segment
   endpoints.
4. Implement an AuthaGraph seam-safe route split or fold policy, or densify
   the source path across the AuthaGraph tetrahedron boundary before
   projection.
5. Add a regression test that checks no generated fiber route segment exceeds
   the AuthaGraph maximum valid screen jump.
6. Regenerate, then compare AuthaGraph and Cahill-Keyes network-fiber PNGs.

### 5. Acceptance sequence

1. Run the narrow render fixes first:
   - `make check-network-fiber`
   - `make generate-gpu-controls check-gpu-controls`
   - `make generate-anthropocene-temperature-2025 generate-anthropocene-temperature-2026`
2. Run the wider generated-assets gate after the visual defects are fixed:
   - `make check-stage-15-active`
   - `make check-docs`
3. Do not promote any changed file to S3/AAO until the user re-reviews the
   three problem classes: AuthaGraph fiber seam, portrait controls, and
   temperature opacity.
