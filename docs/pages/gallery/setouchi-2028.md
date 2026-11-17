---
layout: default
title: World and Japan atlas review
---

# World and Japan atlas review

Open the [current World/Japan atlas-optional review](https://situationshipin.space/review/cartofreako-atlas-optional-20261117/)
on situationshipin.space. The **17 November 2026 review round** contains
**80 subjects, 151 maps and 151 companion legend/source sheets**, using the
current map presentation and amber A3 v3 legends. It implements the complete
World/Japan revision requested in
[issue #83](https://github.com/bdekoz/situationshipin.space/issues/83) and is
listed in the [Proofs catalog](https://situationshipin.space/proofs.html).

[Documentation index](../README.md) · [Visual gallery](README.md) ·
[Default generation styles](../getting-started/generation-styles.md)

## Current atlas-optional review

The review includes all available World/Japan map and legend sheets from the
selected completed `atlas-optional` build: 39 default subjects, nine optional
ocean variants and 32 optional climate variants. Catalog identities expand
into separate periods and measures in this review. There are **80 World
views** and **71 Japan views**, each with its own legend. Nine optional
World/India products contribute their World sheets; no Japan sheet exists
for those variants. India sheets are outside this collection.

The source data edition is **11 November 2026**, and the completed render
build is `20261113t054328z-8f8b6a07f3a4`. This review publication reuses those
validated artifacts. Source observation dates, coverage, uncertainty and
interpretation stay on the companion legends. The
[source and image inventory](https://situationshipin.space/review/media/cartofreako-atlas-optional-20261117/plates.json)
records the build/dataset identities, original implementation revision and
working-tree state, style fingerprints, source hashes and every published
image hash. The original full-build receipt and the three render-validation
reports accompany that inventory.

The gallery provides geographic filtering, search, expandable legends and
separate feedback pages for every map and legend. Open a full image to zoom;
review copies use lossless WebP up to 3840 pixels on the longest edge, with
960-pixel thumbnails. Atlas PNG masters and optional print PDFs supply the
derivatives. Full print masters remain local to Cartofreako.

Saved reviews remain bound to exact source and image hashes. Download all
302 sheet reviews and collection notes as one JSON file. The
[previous October 30 round](https://situationshipin.space/review/cartofreako-setouchi-2028-20261030/)
retains its 38 subjects, 76 original plates and review identities, and links
forward to the current round. Earlier feedback is not assigned to revised
images. Preparation and publication commands are documented in the
[review site's README](https://github.com/bdekoz/situationshipin.space#current-cartofreako-atlas-optional-review).

## Earlier October review rounds

The October 30 gallery and ST2 delivery below retain their dated editions.
The historical ST2 presentation has 152 SVG sheets and 20 selected print
sheets; the current default atlas and completed books are described in the
[build guide](../getting-started/build.md) and
[publication delivery notes](../../development/20261114_pod_expanded_v4.md).

The subsequent [ST2 revision](../../development/20261030_setouchi_triennale_explore_2.md)
has a [plate-by-plate source bibliography](setouchi-2028-bibliography.md)
covering all 38 pairs. The local edition in
`output/setouchi-triennale-2028-st2/` contains **76 legend-free maps and 76
separate legend/source sheets**, with each data bibliography on its matching
legend. Its `index.html` opens the paired review. The separate
`setouchi-tri-explore-v2-world.pdf` and `setouchi-tri-explore-v2-japan.pdf`
contain **75 pages each**: a large **CARTOFREAKO / 2026-10-31** title page,
edition notes, a plate index, and 36 cartography/data sheets each followed
by its legend/data bibliography. The combined
`setouchi-tri-explore-v2.pdf` has 147 pages. The PDF editions omit Bathymetry
Roulette and Bathymetry Hamonshu, including their legend/bibliography sheets.
World and Japan companions keep their original plate identifiers 01–38,
with 05 and 06 omitted. These are independent of PDF page positions.
The number alone appears in 36 pt bold with white fill and a fully opaque
black 0.5 pt outline.

The standard files under `plates/world/` and `plates/japan/` follow this
same two-sheet arrangement. A base filename is the cartography/data sheet;
the matching `-legend` filename is its legend/data bibliography sheet.
This includes every SVG, PDF, PNG and preview, including both temperature
years. Combined build intermediates are kept under `sources/composition/`.

Every ST2 map has a 43.5-inch image width centered on its 44-inch sheet.
Every world sheet uses the approved horizontal move. Terrestrial maps
consolidate Antarctica at the same lower-left position, with its coastlines,
ice and country fills; Japan detail views retain their Japan framing.
Both swarm resolutions use fill-only location names, with zero text stroke
width, in the world and Japan views.
The approved four-sheet network sample is
`proofs/43p5-antarctica-left/setouchi-network-separated-proof.pdf` inside
the ST2 delivery. The published gallery above remains the first edition.
The bibliography documents the same observational inputs, with per-source
dates, methods and a downloadable checksum ledger. The
[regeneration instructions](../getting-started/generation-styles.md#setouchi-st2-print-layout)
preserve the new layout and typography.

## Review and return feedback

1. Search for a subject, such as fiber, particulate, petroleum or coral.
   Choose **World + Japan**, **World** or **Japan** to set the geographic scope.
2. Use **Zoom image** to inspect details. Choose **Review & notes** to open
   the individual plate page; its navigation links to the companion plate.
3. Select a decision, enter a note and choose **Save local review**.
   Decisions are `UNREVIEWED`, `KEEP`, `KEEP-PARTS`, `REVISE`, `REJECT` or `DISCUSS`.
   Name the feature, location or legend entry that needs attention.
4. Return to the paired gallery. Add overall comments under **Notes across
   the collection**, then choose **Save collection notes**.
5. Choose **Download all saved reviews** and return that JSON file with your
   feedback. It contains the collection notes and all 76 plate entries,
   including the decisions and notes saved in this browser.

Saved reviews stay in the same browser and device. Downloading exports them;
it does not send them to the project. An individual page can also download its
own review JSON or open a GitHub issue draft for the reviewer to submit.
Source and image checksums accompany each review so feedback can be matched
to the exact edition. Feedback saved against different image hashes is excluded
from the current collection.

## What to inspect

| Subject | Changes in this edition |
| --- | --- |
| Fiber | Ocean routes and Kelly green ITU terrestrial routes use 0.5 pt strokes at 75% opacity. Japan uses smaller landing symbols with 0.5 pt outlines. |
| Network swarm | Native Alpha60 circles for Dan Da Dan 210 use AuthaGraph. The 1080p/4K and 720p/lower-resolution bands each have their own world/Japan pair. |
| Particulate | Both years include Japan, China and selected Indian PM2.5 observations. Review observed-day coverage alongside concentrations; the [source page](../data/anthropocene-particulate.md) explains periods, missing data and provider limits. |
| Temperature | New daily high records use shared annual count classes: 1–5, 6–10, 11–20, 21–40, 41–80 and ≥81 days. |
| Resources and coral | Resource classes use opaque, distinct palettes; petroleum uses browns and solar yellow through orange. Coral threat uses grouped honeycombs. |
| Atmosphere and water | Atmosphere places land outlines with zero fill opacity above pink cloud and blue precipitation layers. Rivers use 0.75 pt globally and 1.5 pt in Japan; Japan coastlines use 1 pt. |
| CDN | Vendor-reel honeycombs use the pinned 2026-10-21 CDN source manifest. |

The [generation styles guide](../getting-started/generation-styles.md) records
the full visual settings and regeneration commands. Plate captions and the
[source inventory](https://situationshipin.space/review/media/cartofreako-setouchi-2028-20261030/plates.json)
retain the observation dates; the review edition date is the publication date.

## Screen copies, print files and provenance

The gallery serves **3,840 × 1,663 lossless WebP** review images and
960 × 416 thumbnails. These were downsampled from the verified
13,200 × 5,716 PNG masters. AuthaGraph is the geographic projection;
celestial subjects use the Setouchi observer/context companions recorded in
the delivery.

The local delivery is `output/setouchi-triennale-2028/`. It contains the
44 × 19.052559 inch SVG/PDF masters, 300 dpi PNGs, show catalogs and the
aggregate `setouchi-tri-explore-v1.pdf`. The web review collection provides
screen copies of the plates. The local delivery index and print files are
excluded from the Cartofreako documentation site. Print legibility, Japanese captions, attribution
and venue decisions remain covered by the
[development plan and human review steps](../../development/20261029_setouchi_triennale_explore.md).

The source inventory identifies Cartofreako commit `385650c`, the delivery
manifest and each original and published image checksum. Site commit
`e3d0e5b` was [deployed successfully](https://github.com/bdekoz/situationshipin.space/actions/runs/41106927988).
On 2026-10-30, all 308 checked public files returned HTTP 200 and matched
their prepared checksums. Desktop and phone checks covered image loading,
search, geographic filters, saved notes and the combined feedback download.

For another review round, regenerate with the saved styles, validate the
complete delivery, and follow the site's
[preparation and publication instructions](https://github.com/bdekoz/situationshipin.space/blob/e3d0e5b03d5e776dc65e07b300052c3578749e08/README.md).
Use a new dated collection ID to keep editions and their feedback distinct.
