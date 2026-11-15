# v4: full-bleed maps across portrait A4 spreads

The requested variation preserves each complete cartographic plate across
**two facing portrait A4 pages**, then puts the legend, interpretation and
source notes on the **next two facing pages**. The user specified full bleed
on both map pages and chose to preserve the whole map by extending its
background to the page edges.

The two books use the same frozen content as the
[completed landscape variation](20261114_pod_expanded_v2.md): all 39 World
Atlas maps and all eight Starlink Star Light v3 World/USA views. v4 names the
publication variation; source observation dates and the Starlink v3 content
remain unchanged. Output is in `output/atlas-optional-v4-spread/`.

## Completed delivery

Both books are rebuilt and validated in the [v4 delivery directory](../../output/atlas-optional-v4-spread/README.md):
**162 World Atlas pages** and **38 Starlink pages**, plus their reflowable EPUBs
and ebook covers. All 200 print pages decode; all 47 four-page chapters preserve
403 paragraphs, 421 keys and 1,541 source SVG text lines. Final PDF halves
rejoin to the recorded complete-map hashes with matching fold bleed. Both
EPUBs pass EPUBCheck 5.4.0 without errors or warnings. Every page/spread and
selected reader previews were visually inspected. The
[validation record](20261114_pod_expanded_v4.validation.json) identifies exact
outputs, production snapshots and review scope.

## Layout

| Pages in each chapter | Content |
| --- | --- |
| Even left page and following odd right page | One complete map across the spread, without headings, captions, folios or internal white margins |
| Next even left page | Plate title, original subtitle, interpretation context and complete key; keys may continue within this pair when necessary |
| Next odd right page | Remaining legend explanations and source notes |

Each chapter occupies exactly four pages. Contents point to its first map
page. Frontmatter and final production notes are outside these sequences.
Any alignment blank is recorded explicitly.

The spread trim is **420 x 297 mm**. Each page has a **210 x 297 mm TrimBox**
and **3 mm bleed on all four edges**, so its MediaBox/BleedBox is **216 x
303 mm**. Artwork fills the entire physical page. The complete source is
proportionally fitted within the spread; its most frequent border color
fills the remaining background. Nothing is stretched or cropped away.
Panoramic maps fill the 420 mm width, with background above and below.

The entire spread is rasterized once, converted to CMYK, and split at
integral pixel coordinates. At **12 pixels/mm (304.8 ppi)**, the two trimmed
halves join exactly. Bleed at the fold contains pixels from the adjacent
half; outer bleed repeats the outer edge pixels. This extra image area lies
outside each TrimBox and is not duplicated within the finished spread.

Legend text retains 10.5 pt body/key type and 9.5 pt source notes. Mirrored
text margins follow the final page count; map pages have no inside allowance.
A legend that exceeds its allocated two pages fails before rendering instead
of losing text, shrinking type or adding an unexpected fifth page. Selected
enlarged details remain in EPUB; the print variation devotes its four-page
sequence to the complete map and all original legend/source text.

## Production and checks

Izzi owns `portrait-map-spreads-v1`, the dated
`a4-portrait-spread-20261114.json` profile, geometry, raster/color conversion,
PDF/X packaging, EPUB production and independent PDF review. Cartofreako
owns content selection, geographic sources, the adapter and content audit.
The existing portrait and landscape outputs are retained.

The reusable production implementation is committed in
[Izzi `a2132cf9`](https://github.com/bdekoz/izzi/commit/a2132cf956cbc9a836f4f397639e43b3b1d946cc).
Its engine and profile hashes match the reviewed v4 delivery.

```sh
make publication-editions-v4
make check-publication-editions-v4
```

Set `PUBLICATION_SPREAD_OUTPUT` to a new directory for a fresh build.
`PUBLICATION_IZZI` and `PUBLICATION_EPUBCHECK` override the sibling engine and
EPUBCheck jar. Resuming checks manifests, source assets, profiles, production
tools and output hashes; an older layout receipt cannot satisfy this mode.

The repository versions the adapter, content checker, design/delivery notes
and compact validation records. Generated books, covers, full receipts and
previews remain local, following the existing publication-output convention.
Build-time environment records retain their original base revisions and
pre-commit state; exact tool snapshots and output hashes remain the evidence
for the reviewed delivery.

Eight fast tests and eight integration tests pass. These include bleed/page
boxes, wide and tall artwork, the four-page sequence, maximum proportional
fit, matching fold pixels, reconstruction of the complete map from final PDF
images, rejection of a substituted wrong half, fixed-two-page legend
overflow, and the existing portrait/landscape/mobile/EPUB checks. The generic
Izzi example builds independently of Cartofreako data and has 14 pages.

Final review verified all 47 reconstructed maps against their recorded
complete-spread pixel hashes, every text pair against the original source
paragraphs and keys, print preflight, EPUBCheck, and trimmed page/spread
renders. Delivery receipts preserve output, asset, tool and profile hashes.

## Viewing and publishing

Review images crop to the TrimBox and join the map pages without an artificial
centre gap. A PDF viewer displaying MediaBox shows the extra bleed; that is
outside the finished A4 pages. The reflowable EPUBs retain complete unsplit
maps, adjustable text, links and optional enlarged details.

This is a neutral interior master. The physical binding can obscure fine
marks at the fold, and dense source labels still need enlargement. Product
setup must check the selected provider's bleed template and binding before
exporting a submission derivative. A physical proof, provider-specific
validation and separate print wraparound covers remain publishing steps.
No book or proof is uploaded or ordered by these build targets.
