---
layout: default
title: Setouchi 2028 world and Japan review
---

# Setouchi 2028 world and Japan review

Open the [world and Japan review gallery](https://situationshipin.space/review/cartofreako-setouchi-2028-20261030/)
on situationshipin.space. The **2026-10-30 review edition** contains **38 world
plates and 38 Japan companions**, paired by subject. It includes the complete
plate set from the Setouchi delivery and is listed in the site's
[Proofs catalog](https://situationshipin.space/proofs.html).

[Documentation index](../README.md) · [Visual gallery](README.md) ·
[Default generation styles](../getting-started/generation-styles.md)

The subsequent [ST2 revision](../../development/20261030_setouchi_triennale_explore_2.md)
has a [plate-by-plate source bibliography](setouchi-2028-bibliography.md)
covering all 38 pairs. The local edition in
`output/setouchi-triennale-2028-st2/` contains **76 legend-free maps and 76
separate legend/source sheets**, with each data bibliography on its matching
legend. Its `index.html` opens the paired review. The separate
`setouchi-tri-explore-v2-world.pdf` and `setouchi-tri-explore-v2-japan.pdf`
contain **79 pages each**: a large **CARTOFREAKO / 2026-10-30** title page,
edition notes, a plate index, and 38 cartography/data sheets each followed
by its legend/data bibliography. The combined
`setouchi-tri-explore-v2.pdf` has 155 pages. Plate numbers identify subjects 01–38, shared by the
world and Japan companions; they are independent of PDF page positions.
The number alone appears in 36 pt bold with white fill and a fully opaque
black 0.5 pt outline.

The standard files under `plates/world/` and `plates/japan/` follow this
same two-sheet arrangement. A base filename is the cartography/data sheet;
the matching `-legend` filename is its legend/data bibliography sheet.
This includes every SVG, PDF, PNG and preview, including both temperature
years. Combined build intermediates are kept under `sources/composition/`.

Every ST2 map has a 43.5-inch image width centered on its 44-inch sheet.
The world fiber and groundstation maps also use the approved horizontal
move and deliberately displaced Antarctica, consolidated at the lower left.
Their current four-sheet proof is
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
