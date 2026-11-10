# Starlink Star Light v3: IngramSpark book options

Research checked 9 November 2026. These are editorial options and actual-size
layout proofs, not a finished book or a publishing submission.

Start with **A5 portrait, 48 pages**, using each full map as an overview and
devoting subsequent pages to details. It meets the requested small format.
The 44-inch originals cannot simply be reduced to readable book pages.

## Vendor envelope

IngramSpark's dated 24 August 2026 guide lists A5 (5.83 × 8.27 in), 8 × 8 in
and 11 × 8.5 in. The landscape option requires Premium Color and has a
400-page maximum. A3, 297 × 420 mm, is absent from the standard matrix;
it also exceeds the website's custom-size envelope. Keep A3 for the separate
legend sheets. A4 appears in the guide, but is larger than the preferred
small book. The guide and general website differ on some maximum dimensions;
use the title-setup product selector for the final binding/paper combination.
[File Creation Guide, pp. 10, 40](https://www.ingramspark.com/hubfs/downloads/file-creation-guide.pdf),
[print options](https://www.ingramspark.com/plan-your-book/print/trim-sizes).

Premium Color on 70 lb white paper is the first proof candidate for these
image-heavy plates. The vendor also describes Ultra-Premium Color, whose
availability depends on the selected product. Neither is a metallic-paper
process; the original Epson low-ink experiment is a separate production
context. [IngramSpark print options](https://www.ingramspark.com/plan-your-book/print/trim-sizes).

## Three approaches

All figures below are our calculations from a 44-inch-wide master, allowing
0.5 inch at each side. They describe an ordinary single-page overview.
The typography columns are the resulting sizes of existing labels, not
recommended body sizes.

| Option | Proposed book | Usable map width | Reduction | 9.6 pt sky label | 6 pt satellite label | Editorial treatment |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 1: A5 portrait | 5.83 × 8.27 in / about 148 × 210 mm; 48 pages; paperback | 4.83 in | 10.98% | 1.05 pt | 0.66 pt | Portable field guide: overview, observer paragraph and several carefully chosen detail pages per plate. Recommended. |
| 2: Small square | 8 × 8 in / 203 × 203 mm; 40 pages; paperback or case laminate | 7 in | 15.91% | 1.53 pt | 0.95 pt | More breathing room for the USA panels and symbol keys. Still requires details and reflowed text. |
| 3: Landscape | 11 × 8.5 in / 279 × 216 mm; 32 pages; Premium Color | 10 in | 22.73% | 2.18 pt | 1.36 pt | Best single-page match to the long map composition, but least portable. Separate detail pages remain necessary. |

The six-page [format proof](../../output/starlink-star-light-v3-20261109/pod/format-proofs.pdf)
places SLSL1 and SLSL4 at each proposed physical size, with readable explanatory
text outside the image. Print at 100%, without “fit to page.” These proofs use
screen previews to study scale; they are not the final print interiors.
The computed dimensions are also saved in `pod/format-comparison.json`.

## Proposed A5 sequence

Use eight opening pages for title, imprint, contents, the four viewpoints,
palette and symbol conventions. Give each of the four plates eight pages:
two for the complete view and observer notes, two for the USA context, and
four for enlarged details and a reflowed key. Finish with eight pages of
source notes, methods, the source-date register and a colophon: 48 pages total.

For SLSL1, select celestial details by object group, not US longitude. For
SLSL2, keep San Francisco's actual horizon and identify the time. For SLSL3
and SLSL4, give Alaska and Hawaii their own readable detail panels. Keep names
away from the gutter. The panorama can span facing pages as an overview, but
the binding will interrupt it; no essential glyph or label should depend on
that join. Recompose observer notes at 10–11 pt and keys at 9–10 pt. A light
amber notes page opposite a wine map page would carry the new legend treatment
into the book.

The square version can use six opening pages, seven per plate and six closing
pages (40 total). The landscape version can use four opening pages, six per
plate and four closing pages (32 total). These are proposals, not imposed
page counts.

## Preparing an eventual print interior

The guide requires embedded fonts, CMYK color and a single PDF of individual
pages compliant with PDF/X-1a:2001 or PDF/X-3:2002. Its color guidance calls
for 300 ppi, 0.125-inch bleed on the three outside edges, and a 0.5-inch safety
margin. Covers use the vendor template; perfect-bound books below 48 pages
cannot carry spine text.
[File Creation Guide, pp. 4, 10–11, 18](https://www.ingramspark.com/hubfs/downloads/file-creation-guide.pdf).

The delivered SVG/PDF plates remain editable RGB artwork. A selected book
would need reflowed pages, print color conversion, preflight, a cover and a
physical proof. Small wine-colored type should be tested for registration;
the guide recommends black-only small body text, so a book-specific text
treatment may be appropriate while retaining wine in larger headings.

No price has been invented. Compare the three specifications in the vendor
calculator with the intended printing region, quantity and shipping address;
page count, color and binding affect the result. Ordering or publication is
outside this implementation. [IngramSpark book printing](https://www.ingramspark.com/book-printing).
