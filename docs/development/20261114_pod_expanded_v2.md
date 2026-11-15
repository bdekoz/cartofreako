# A4 landscape print-on-demand and EPUB plan - 14 November 2026

## Revised direction and status

A further [v4 variation](20261114_pod_expanded_v4.md) now places each complete
map across two full-bleed portrait A4 pages, followed by two legend/source
pages. The landscape delivery documented here remains available.

**Give the cartographic plate as much of an A4 landscape page as possible,
with its legend on the facing page.** Use true 297 x 210 mm landscape pages
throughout each print interior. Each complete map occupies an even-numbered
left page; its title, readable symbol key and explanation occupy the next
odd-numbered right page. Reserve the map page for cartography.

The approved landscape revision is **implemented and rebuilt** for both
books in [the landscape delivery directory](../../output/atlas-optional-v3-landscape/README.md).

| Book | A4 landscape interior | Reflowable EPUB |
| --- | --- | --- |
| World Atlas | [102 pages, 55.16 MiB](../../output/atlas-optional-v3-landscape/atlas-world.20261112.v3.a4-landscape.pdf) | [13.34 MiB](../../output/atlas-optional-v3-landscape/atlas-world.20261112.v3.epub) |
| Starlink Star Light v3 | [38 pages, 17.96 MiB](../../output/atlas-optional-v3-landscape/starlink-star-light.v3.a4-landscape.pdf) | [8.96 MiB](../../output/atlas-optional-v3-landscape/starlink-star-light.v3.epub) |

All 47 maps have their complete primary legend on the facing page. All
140 print pages decode; the content audit retains 403 paragraphs, 421
keys and 1,541 source SVG text lines. Actual PDF placements pass maximum-fit,
parity, resolution, margin, font, color and ink checks. Both EPUBs pass
EPUBCheck 5.4.0 with zero errors and warnings. Seven fast Izzi tests and six
integration tests pass, including final blank pages through PDF/X conversion.
All final pages/spreads and selected phone/tablet/dark-theme EPUB previews
were visually inspected. The
[landscape validation record](20261114_pod_expanded_v2.landscape.validation.json)
identifies exact outputs, tool/profile hashes and review scope.

World Atlas uses a 268 x 184 mm map frame with 16 mm inside allowance;
Starlink uses 271 x 184 mm with 13 mm inside allowance. Every map preserves
its complete original extent and aspect ratio. Source observations and data
were not refreshed. Dense original labels still require enlargement.

Reproduce or verify this delivery from the Cartofreako root:

```sh
make publication-editions-landscape
make check-publication-editions-landscape
```

Use `PUBLICATION_LANDSCAPE_OUTPUT=output/atlas-optional-v3-landscape-rebuild`
for a fresh build, and `PUBLICATION_IZZI` / `PUBLICATION_EPUBCHECK` for tool
path overrides. To resume the delivered files after the v4 engine update,
use their frozen production tools as described in the
[landscape README](../../output/atlas-optional-v3-landscape/README.md#reproduce).
The delivery preserves exact production scripts/profile and build-time base
Git revisions; those historical receipts are unchanged. New
layout/profile/output identity checks prevent a portrait receipt from being
accepted as a landscape delivery. The separate 12-page Izzi landscape example
uses the same production path without Cartofreako inputs.

The previous 58-page and 30-page portrait files and their
[original validation record](20261114_pod_expanded_v2.validation.json) remain
the historical baseline below. Full independent PDF/X certification,
provider-specific product/export validation, print wraparound covers, final
title/ISBN setup, Kindle Previewer and a physical proof remain publishing
steps. No upload, publication or order was performed.

## Decision and scope

**Izzi owns the general publication and production capability. Cartofreako
owns cartographic content and geographic data.** This follows the user's
explicit direction: Izzi is the visualization and production layer, and
these output types are useful beyond cartography.

Produce two independent books, each with an **A4 landscape print interior
PDF** and a corresponding reflowable EPUB, in
`output/atlas-optional-v3-landscape/`:

| Book | Frozen content |
| --- | --- |
| Cartofreako: World Atlas | The complete `atlas-world.20261112.v3.pdf`: 39 maps and their legends, with the source title/contents information retained in recomposed frontmatter. Source PDF: 80 pages. |
| Starlink Star Light v3 | The complete `starlink-star-light-v3-20261109` collection: SLSL1-SLSL4, each with World and USA views and a companion legend. Source PDF: 16 pages. |

The user explicitly requested both collections. The World atlas refers to
the full World edition just optimized, not the combined World/Japan atlas.
The Starlink book retains the complete World/USA v3 collection; the differing
calculation dates in the two collections remain visible.

This plan expands and supersedes the format recommendation in
[`20261109_starlink_star_light_v3_pod.md`](20261109_starlink_star_light_v3_pod.md).
It also builds on the completed
[mobile PDF procedure](20261114_pdf_optimization_mobile.md).

The print design takes priority over the previous provider choice. A4
landscape is 297 mm wide and 210 mm high, bound at the short edge. Rotating
an A4 portrait PDF for screen viewing does not produce this book format.
Keep the complete overview on one page, without extending the map across
the binding. The opposite page supplies the readable legend.

## Repository ownership assessment

The inspected Izzi repository is `/home/bkoz/src/izzi`, a sibling checkout.
Its README describes a C++20 SVG library with physical artifact and print
workflows. Its production tooling already includes:

- `scripts/review_raster.py`: shared SVG rasterization and multipage PDF
  export with physical sizing, fonts, and outlines.
- `scripts/export-examples-compact.py`: replaces complex artwork with
  bounded-resolution rasters while preserving surrounding vector annotations,
  input hashes, page order, and export receipts.
- `scripts/export-fuller-pdf.mjs`: book-style exports with selectable text,
  source evidence, and generated contents.
- `docs/visual_workflow/tool_portrait_print.md` and `docs/dependencies.md`:
  optional production adapters, print editions, and validation workflows.

Before the portrait implementation, the inspected export and core surfaces
did not supply a general EPUB or POD PDF/X workflow. Izzi's
`src/izzi-portrait.h::print_spec` governs physical mark widths, gaps, and
local coverage; it is not a book/publisher specification.
Extending that portrait type with ISBN, EPUB, or vendor settings would mix
unrelated responsibilities.

| Responsibility | Owner |
| --- | --- |
| Geographic data acquisition, projections, map generation, feature selection | Cartofreako |
| Atlas/Starlink content selection, observation dates, legend semantics, source bibliography | Cartofreako |
| Publication manifest assembled from the selected maps and text | Cartofreako adapter |
| Page geometry, margins, typography, image placement, pagination, reusable title/contents layouts | Izzi production tooling |
| Rasterization, image encoding, color conversion, ink limits, PDF/X and mobile PDF packaging | Izzi production tooling |
| EPUB structure, navigation, metadata, covers, image limits, accessibility plumbing | Izzi production tooling |
| Dated provider profiles and format preflight | Izzi production tooling |
| Final landscape delivery files and content-specific receipts | `cartofreako/output/atlas-optional-v3-landscape/` |

Extend the shared orchestration in the existing optional Izzi tools with
explicit input and output paths. Keep external PDF, image, and EPUB
dependencies outside the header-only C++ installation. A reusable CLI can consume a versioned
publication manifest without knowing about AuthaGraph, Starlink, NOAA, or the
Cartofreako checkout layout.

Cartofreako should invoke that tool with its prepared manifest. It should not
grow a second EPUB writer, PDF/X converter, or provider policy database.
The existing Cartofreako mobile PDF helper is a migration candidate for the
same generic Izzi exporter; retain a compatibility entry point if it moves.
Existing recipes and source artifacts must remain reproducible during that
transition.

## Provider assessment

Landscape requirements rechecked against official material on 14 November
2026. **Lulu is the first candidate for the exact requested trim.** Confirm
the binding, paper, page-count range, region and distribution eligibility in
its product selector before preparing a provider-specific submission.

| Provider | A4 landscape print treatment | Electronic treatment |
| --- | --- | --- |
| Lulu | The guide explicitly lists A4 Landscape, 297 x 210 mm, including a trim-size interior with white margins. Use the selected product's template and color/export requirements. [Book creation guide, pp. 10-12](https://assets.lulu.com/media/guides/en/lulu-book-creation-guide.pdf). | Retain the reflowable EPUB and separate RGB JPEG cover; confirm electronic distribution independently of the print product. |
| IngramSpark | The standard matrix lists A4 portrait and 11 x 8.5 in landscape, not 297 x 210 mm landscape. Its documented custom-width range also does not establish support for this trim. An 11 x 8.5 in edition would require a separate layout/profile. [File creation guide, pp. 40-41](https://www.ingramspark.com/hubfs/downloads/file-creation-guide.pdf). | Continue the EPUB 3 plus RGB JPEG workflow from the earlier plan. |
| Amazon KDP / Amazon.com | A4 landscape exceeds KDP's 8.5 in maximum custom paperback width. The A4 preset is portrait. Do not label the requested landscape PDF a KDP-compatible interior. [Print options](https://kdp.amazon.com/en_US/help/topic/G201834180). | The reflowable EPUB remains independent of print trim and can be prepared for KDP. |

Lulu's Amazon color-print distribution requires at least 72 pages. The
completed World interior has 102 pages; Starlink has 38. World exceeds that
minimum and Starlink falls below it. Page count alone does not establish
format, binding or distribution eligibility.
[Lulu distribution requirements](https://help.lulu.com/en/support/solutions/articles/64000255462-mandatory-print-book-distribution-requirements).

Use the IngramSpark file guide's stricter **3.2-million-pixel** EPUB image
limit: its ebook web page instead says 5.6 million. Keep EPUBs below 100 MB.
Retain this conservative electronic profile independently of the print
profile. [File creation guide, p. 6](https://www.ingramspark.com/hubfs/downloads/file-creation-guide.pdf),
[ebook guidance](https://www.ingramspark.com/plan-your-book/ebooks).

Provider comparison is about format suitability, not an invented cost quote.
Printing, shipping, royalties, and final price depend on page count, paper,
printing region, quantity, and distribution choices.

## Print edition design

### Map page: maximum proportional fit

Use A4 landscape throughout, with a dedicated map page template. The map gets
the entire safe frame: no chapter heading, subtitle, caption, legend, running
header/footer, visible folio, decorative border or reserved text band. Its
logical page number remains in the contents and facing legend. Keep intrinsic
cartographic labels, graticules, scale information and insets with the map.

Use white page edges and contained artwork. Set the top, bottom and outer
safety margins to **13 mm**, with the total inner margin determined by the
binding and final page count. For example, Lulu recommends a total inside
margin of about 16 mm for 61-150 pages. That gives a **268 x 184 mm** map
frame; a product permitting a 13 mm inside margin gives **271 x 184 mm**.
Recheck the frame if pagination moves the book into a different binding
allowance. These are design calculations from the trim and margin values.
[Lulu book creation guide, pp. 9, 23](https://assets.lulu.com/media/guides/en/lulu-book-creation-guide.pdf).

For artwork bounds `w x h` and available frame `W x H`, use uniform scale
`s = min(W / w, H / h)` and center the resulting `s*w x s*h` placement within
the frame. At least one placed dimension must reach its available limit.
Honor source page boxes and rotation before measuring. Do not stretch the
projection, crop geographic coverage or turn an upright map sideways simply
to fill both dimensions. Panoramic plates will retain some vertical space;
that is the consequence of preserving their full aspect ratio.

Inspect source margins before scaling. Remove only verified empty outer
padding, recording the crop bounds in the manifest. Preserve every map mark,
label, inset and meaningful edge. Move any separable publication title or
credit to the facing page with its text retained; do not trim it away along
with cartographic content. Where the source has no removable padding, fit
the complete original plate.

The portrait Izzi `Book.picture()` defaults to a 95 mm maximum height and
`Book.render()` places headings, captions and keys on the map page. The new
`FacingBook` template uses the full calculated frame without that overview
height cap and suppresses running footers on map pages.

Rasterize from the original artwork at the enlarged placement size. The
268 mm frame is about 53% wider than the previous 175 mm portrait frame;
this is a width comparison, not a guarantee of every plate's scale gain.
Even a full-width 44-inch original reduced to 268 mm turns a 6 pt source
label into approximately 1.44 pt. Keep dense-label limitations explicit in
the facing legend and use original-artwork details where they help reading.

### Facing legend page

Place the complete symbol key on the page opposite its map. Recompose the
original SVG/legend text and swatches as live text and images; do not shrink
the A3 legend sheet into a page-sized screenshot. Put the plate number,
title, subtitle, observation date, coordinate context and overview caption
here, followed by the key and reading notes.

Use embedded Atkinson Hyperlegible fonts, approximately 10.5 pt body/key
text and 9.5 pt source notes, in black-only ink. Use two or three columns
where needed, reading across each row and then down, while retaining source
key order. The largest current keys contain 25 entries in the World book and 24 in Starlink;
include those pages in the layout proof. Keep each swatch beside its label.

The primary legend, including every symbol key entry and the context needed
to interpret the map, must fit on the facing page at the intended readable
size. Fit additional interpretation and source references there when space
permits. Lengthy methods, bibliography and enlarged details may continue
after the pair with explicit references from the facing page. Preserve all
original explanatory/source text. If the primary key cannot fit, revise its
column layout and spacing; report unresolved overflow rather than silently
dropping keys, shrinking the type or moving the legend away from the map.

### Spreads, sequence and pagination

Treat each map and its primary legend as one indivisible spread:

| Physical page | Content |
| --- | --- |
| Even page `2n`, left | Complete cartographic plate at maximum proportional fit |
| Odd page `2n + 1`, right | Matching title, complete symbol key and reading context |
| Following pages, if needed | Legend/source continuations and original-artwork details |

Page parity counts from the first interior PDF page, including frontmatter
and intentional blanks. A map on page 5 and legend on page 6 are back-to-back,
not facing. Ensure every next map starts on an even page after any preceding
continuations, and record the reason for any alignment blank. Do not insert
text, a detail page or a blank between the paired map and legend.

Begin with title, edition/credit page, contents and a reading guide. Keep all
39 World maps and all eight Starlink World/USA views in their established
order. End with methods/source notes and a colophon. The paired pages alone
require 78 World pages and 16 Starlink pages; frontmatter, continuations,
details and necessary padding determine final totals. Recalculate contents,
binding margins and cover dimensions from that pagination.

Export individual landscape pages in normal reading order. Use paired
even/odd page renders for review so that a contact sheet cannot hide a parity
error. A review spread is separate from the single-page-sequence interior.

Render artwork at approximately 300 ppi at its **placed A4 size**; flatten
complex paths/transparency as needed while preserving newly composed text.
Use a recorded CMYK conversion profile and enforce total ink coverage no
greater than 240%. Record any resulting color changes and inspect the wine,
amber, fine-line, and dense orbital pages.

Export a single-page-sequence interior for each book, with exact landscape
TrimBox/MediaBox dimensions for the no-bleed master. Keep PDF/X-3:2002 as the
existing production baseline; a provider-specific derivative must meet that
provider's selected template/export requirements. Check fonts, resolution,
color spaces, ink coverage, transparency and spread order. A PDF/X metadata
label alone is not a conformance check.

## EPUB design

Use **reflowable EPUB 3**, with one chapter per map/view. Reuse the mobile
World atlas's raster maps as overview assets where they pass image-quality
checks. Produce analogous bounded-resolution assets for Starlink, and use
original artwork for additional detail assets when necessary.

The facing-page requirement belongs to the print edition. Keep each ebook
map followed by its readable legend in the same chapter; do not force
landscape pages, blank parity pages or a two-page screen layout into EPUB.
Retain the established electronic image/cover limits and content inventory.

Recover legend text from the original source material: the mobile PDF has
no text layer. Use actual XHTML headings, paragraphs, lists, captions, source
links, and keys rather than making every ebook page a screenshot. This
supports font-size changes and text-to-speech, and avoids Amazon's problems
with wholly scanned books. See
[KDP image guidance](https://kdp.amazon.com/en_US/help/topic/G75V4YX5X8GRGXWV)
and [content-quality requirements](https://kdp.amazon.com/en_US/help/topic/G200952510).

Provide a navigation document, reading order, language, title, author,
edition metadata, internal cover, and external JPEG front cover. Use RGB
images and useful alternative text. Do not hard-code body font colors or
backgrounds that defeat reader themes. Do not invent an ISBN; use an EPUB
identifier that is valid independently of a later distribution ISBN.

Each EPUB must contain the same selected maps, interpretation, and sources
as its print counterpart, even though pagination and image placement differ.
Maps still need visual inspection at useful zoom levels; successful archive
validation does not make tiny map labels legible.

## Implementation stages and acceptance

The following stages are completed for this delivery; the linked validation
record and delivery README contain the measured results and reproduction commands.

1. **Retain frozen content.** Reuse the two source PDFs, original map/legend
   assets, World mobile derivative, content order and hashes. Preserve source
   dates, all 47 views, 403 paragraphs and 421 key entries. Record any verified
   outer-padding crops without modifying the frozen originals.
2. **Extend production in Izzi.** Add an explicit landscape facing-spread
   layout mode, dedicated map/legend templates, maximum-fit placement,
   column-based legends, continuation handling and even-page map alignment.
   Version the layout/profile contract and receipts; retain the existing
   portrait mode. Keep these capabilities generic and independent of maps.
3. **Connect the Cartofreako adapter.** Select that layout and a new
   landscape profile explicitly, update edition/reading-guide/colophon text,
   and use neutral landscape output names. The current adapter and default
   Izzi build select the portrait profile; changing only `PUBLICATION_OUTPUT`
   does not implement this revision. Expose the layout/profile choice in
   the reproducible build target and resume identity checks.
4. **Proof the layout.** Render representative complete spreads first:
   a panoramic World map, a USA view, a tall or square source, the 25-entry
   World key and a 24-entry Starlink key. Check the entire primary legend
   opposite its map, actual-size text, source crop edges and maximum fit.
5. **Build both editions.** Generate the landscape interiors, reflowable
   EPUBs, ebook covers, manifests and receipts in the new directory. Let
   pagination determine the final binding allowance, then rerun layout if
   that allowance changes. Do not reuse the old page counts or print covers.
6. **Validate and document.** Run the checks below, inspect every paired
   spread, and record exact output/tool/profile hashes. Add the new build
   and validation commands, sizes, page counts and remaining provider checks
   only after they have been exercised. Preserve the portrait validation
   record and create a separate landscape validation summary.

## Documentation

Update the existing generic documentation in Izzi, then describe Cartofreako's
use of the landscape mode here. The landscape additions below are implemented
alongside the existing portrait documentation.

| Location | Documentation coverage |
| --- | --- |
| `izzi/docs/visual_workflow/tool_publication.md` | Landscape facing-spread workflow, maximum-fit artwork, legend columns, continuation/parity rules, spread previews, explicit profile selection and recovery. Preserve portrait/mobile/EPUB instructions. |
| `izzi/docs/publication.md` | Versioned layout contract and CLI reference, source crop bounds, physical placement, map/legend page relationships, provider profiles, output naming and resume identity. |
| `izzi/docs/dependencies.md` | Optional Python, Poppler, Ghostscript, color-profile, and Java/EPUBCheck dependencies; versions exercised; installation/preflight instructions. Keep these separate from C++ consumer dependencies. |
| `izzi/docs/development/sessions/20261114.publication_production.md` | Implementation decisions, existing-exporter reuse, compatibility/migration notes, provider-source dates, test results, and known limitations. |
| `izzi/examples/publication/README.md` | Runnable generic examples with exact commands, checked-in small inputs, output inventory, and expected validation results. |
| `cartofreako/docs/development/20261114_pod_expanded_v2.md` | Current landscape specification, completed delivery evidence and a clearly labeled portrait baseline. |
| `cartofreako/docs/development/20261109_starlink_star_light_v3_pod.md` | Preserve the earlier study and portrait delivery; point to this revised landscape specification. |
| `cartofreako/output/atlas-optional-v3-landscape/README.md` | Landscape outputs, map/legend page pairs, exact trim and binding profile, actual sizes/counts, validations, reproducible commands and remaining submission steps. |

The reference must distinguish full-page rasterization, selective artwork
rasterization with live text, and reflowable EPUB. Explain why a mobile PDF
cannot supply selectable text and why its resolution is unsuitable for
enlarged print details. Describe physical units, effective placed ppi, CMYK
conversion and ink limiting, reading order, image descriptions, and the
difference between structural validation and visual/retailer acceptance.

Include provider requirements as dated profiles with primary-source links.
Document conflicting guidance explicitly, including IngramSpark's EPUB pixel
limits, rather than silently choosing the more permissive value. Show how to
update a profile without changing an already delivered edition's receipt.

## Test plan

Use focused tests for the new production boundary and integration checks for
the actual deliverables. Do not make every Izzi C++ build depend on the full
publishing toolchain, network access, or the large Cartofreako datasets.

| Layer | Cases and assertions | Owner |
| --- | --- | --- |
| Manifest and input admission | Missing/changed asset, unsupported schema, duplicate identifiers, invalid page order, missing title/language, invalid physical units, zero-size image, conflicting source/destination, and unsafe archive paths fail before output is declared complete. | Izzi |
| Page geometry and maximum fit | Exact 297 x 210 mm trim; mixed source frames/crop boxes and 90/180/270-degree source rotation; uniform scale; mirrored margins; source marks retained. Recompute the largest permissible placement independently and require at least one dimension to fill its frame within 0.1 mm. No inherited 95 mm cap, heading/footer reservation, stretch or clipping. | Izzi |
| Facing spreads and continuations | Every map is on an even physical page and its complete primary legend on the immediately following odd page. Exercise odd/even frontmatter, long source continuations, details and alignment blanks. Verify matching chapter IDs, order, contents references and absence of unrelated content between pairs. | Izzi, Cartofreako |
| Legend fit | All key entries and essential context remain on the facing page; swatches stay with labels; two/three-column reading order is explicit; 10.5 pt body/key and 9.5 pt source text remain readable. Unresolved primary-legend overflow fails instead of silently spilling or shrinking. | Izzi, Cartofreako |
| Text and fonts | Real body text remains searchable in print and adjustable in EPUB; all print fonts embedded; intended small text uses K-only black; long titles, URLs, Unicode, and long legends wrap without overflow or silent loss. | Izzi |
| Image/color pipeline | Rasterize complex vectors and transparency at the placed size; enforce dimension/ppi bounds; verify alpha flattening, RGB ebook images, CMYK print images, total ink coverage, and recorded profiles. Distinguish intentionally lossy output from lossless expectations. | Izzi |
| PDF packaging | PDF syntax, page count/order, boxes, PDF/X declarations and output intent, fonts, image resources, resolution, absence of unsupported transparency/annotations, and no printer marks. Mobile profile additionally checks linearization and bounded image dimensions. | Izzi |
| EPUB packaging | Correct first/uncompressed `mimetype` entry; container and package documents; complete manifest/spine/nav; unique IDs; local resource and fragment links; cover declaration; language/metadata; pixel/file limits; no scripts or missing remote assets. | Izzi |
| External validation | Run EPUBCheck against every final EPUB. Run PDF/X preflight with an independent capable validator where available; record the actual validator and checks rather than inferring compliance from metadata alone. | Izzi |
| Visual regression | Render cover, contents, every even-map/odd-legend spread, continuation pages and the last page. Inspect full-book thumbnails plus representative actual-size spreads, including the largest keys, crop edges and dense map labels. Use appropriate color/render tolerances. | Izzi |
| Reader behavior | Preview reflow at phone/tablet widths and larger text settings; ensure headings, keys, source links, image captions, and navigation remain usable in light/dark themes. Kindle Previewer remains a named retailer-specific check. | Izzi |
| Content integration | Exactly 39 World and eight Starlink map/legend pairs in source order; all 403 paragraphs and 421 keys retained across print and EPUB; original dates and asset hashes preserved; every map page contains only its cartography. | Cartofreako |
| Reproduction and failure recovery | Build from a clean example directory; rerun with identical inputs; reject changed layout/profile/crop/output identity under an old receipt. A portrait receipt cannot satisfy a landscape resume. Preserve the previous delivery and reject partial files. | Izzi, exercised by Cartofreako |

Extend the small synthetic fixtures in Izzi with wide, tall and square
artwork, verified empty borders, a long primary key, source continuations
and frontmatter that exercises both starting parities. Retain the gradient,
transparency, dense lines and multilingual text cases. These must not require
Cartofreako or its input services. Use the generic artwork to exercise the same implementation
used by the real atlas books.

Optional targets are `check-publication-unit`, `check-publication-integration`,
`examples-publication`, and `examples-publication-landscape` in Izzi.
Cartofreako uses `publication-editions-landscape` and
`check-publication-editions-landscape` for the two actual books. Fast
manifest/geometry checks run independently; renderer and EPUBCheck checks
have their optional dependencies documented in Izzi.

Acceptance evidence must identify the tested source/tool/profile hashes and
include machine-readable reports. A passing ZIP/XML or PDF parser check is
insufficient by itself: content coverage, render checks, and visual review
are also required. Do not claim physical proofing, device testing, full
accessibility conformance, or a retailer upload happened when it did not.

## Examples

| Example | Purpose | Outputs |
| --- | --- | --- |
| Izzi visual sampler | A non-cartographic artwork/explanation book using the same landscape facing-spread mode, plus the existing portrait example. | A4 landscape interior and spread previews; mobile PDF, reflowable EPUB, ebook cover and receipts. |
| Izzi geometry and overflow fixture | Wide/tall/square sources, rotations, empty borders, primary-key overflow, source continuations and parity transitions. | Expected-pass renders and expected-failure reports; not a commercial book. |
| Cartofreako World atlas | Complete 39-map publication, preserving all legends and sources. Use original print artwork and existing mobile overview assets for EPUB. | A4 landscape interior with 39 matching facing legends and corresponding EPUB. |
| Starlink Star Light v3 | Eight World/USA views spanning natural sky, observer sky, satellite subpoints and ground infrastructure, with their differing source dates. | A4 landscape interior with eight matching facing legends and corresponding EPUB. |

Each example README should state required dependencies, a single build entry
point, a separate validation entry point, expected outputs, and cleanup
limited to its own generated directory. Include a small preview/contact
sheet and a manifest example. Keep generated binaries and the large real
books out of the ordinary source example fixtures; preserve reproducible
recipes and compact validation records.

The generic example should run from an Izzi checkout without the Cartofreako
checkout. Conversely, Cartofreako should select its content and invoke the
same Izzi entry point without copying the production implementation. This
two-direction check is the acceptance test for the repository boundary.

The official EPUBCheck 5.4.0 distribution and current provider PDF guides
have been downloaded into `build/pod-tools/` for this work. Poppler,
Ghostscript, ReportLab, Pillow/ImageCms, and the existing optional pikepdf
installation are available. Izzi already documents optional production
dependencies separately from its C++ core.

Delivered landscape output names:

```text
output/atlas-optional-v3-landscape/
  atlas-world.20261112.v3.a4-landscape.pdf
  atlas-world.20261112.v3.epub
  atlas-world.20261112.v3.ebook-cover.jpg
  starlink-star-light.v3.a4-landscape.pdf
  starlink-star-light.v3.epub
  starlink-star-light.v3.ebook-cover.jpg
  sources/
  validation/
```

These PDFs are **book interiors**. A print submission also needs the
separate full cover produced from the selected provider's template, final page count,
paper/binding, and ISBN. The external ebook front covers do not replace print
wraparound covers. Final account metadata, provider upload checks, Kindle
Previewer review, and a physical print proof are subsequent publishing steps;
the local build does not perform publication or place orders.

## Previous portrait delivery

The previous portrait plan was implemented for both books. The generic
production engine, mobile exporter, dated provider profile, standalone
example and ten tests live in **Izzi**. Cartofreako supplies the content adapter and checks
that the complete selected cartographic content reaches both formats.

The [portrait delivery directory](../../output/atlas-optional-v3/README.md) contains:

| Book | Previous A4 portrait interior | Reflowable EPUB | Scope |
| --- | --- | --- | --- |
| World Atlas | [58 pages, 33.65 MiB](../../output/atlas-optional-v3/atlas-world.20261112.v3.a4.ingramspark.pdf) | [13.33 MiB](../../output/atlas-optional-v3/atlas-world.20261112.v3.epub) | All 39 maps; 291 paragraphs and 265 keys |
| Starlink Star Light v3 | [30 pages, 11.92 MiB](../../output/atlas-optional-v3/starlink-star-light.v3.a4.ingramspark.pdf) | [8.95 MiB](../../output/atlas-optional-v3/starlink-star-light.v3.epub) | All eight World/USA views; 112 paragraphs and 156 keys |

Each book also has a 1400 x 2240 RGB JPEG ebook cover. The PDFs use A4
210 x 297 mm pages, mirrored 20/15 mm inner/outer margins, 10.5 pt body text,
9.5 pt sources, embedded fonts, approximately 300 ppi CMYK artwork, and a
240% total-ink cap. Longer symbol keys use two columns in row order. The
print details come from original artwork; the World EPUB overview images
reuse the completed mobile edition. No source content was updated.

All 88 print pages decode, all 47 chapters retain their original order, and
the integration check accounts for 1,541 original SVG text lines. PDF syntax,
page boxes, actual image placement/resolution, ink samples, font embedding,
K-only text and text safety bounds pass. EPUBCheck 5.4.0 reports zero errors
and warnings for both books. All final pages were inspected in contact
sheets, with selected larger page renders and phone/tablet/dark-theme EPUB
screenshots. The [compact validation record](20261114_pod_expanded_v2.validation.json)
links the measurements to exact output, tool and profile hashes.

The PDFs were generated as PDF/X-3:2002 and pass the documented local
preflight; an independent full PDF/X certification tool was unavailable.
Dense labels inherited from the source maps still require enlargement.
Separate print wraparound covers, final ISBN/title setup, Kindle Previewer,
retailer upload checks and a physical proof remain publishing steps. Both
books are below Lulu's 72-page minimum for Amazon color-print distribution.

Reproduce or verify the existing **portrait** delivery from the Cartofreako
root. These historical commands require the frozen portrait production tools;
the current Izzi tool hashes deliberately reject the old receipt. Restore the
three snapshotted scripts (`izzi_publication.py`, `build-publication.py`,
`review_raster.py`) under a temporary Izzi `scripts/` directory and the original
profile under `config/publication/`, then set `PUBLICATION_IZZI` to that root.
This frozen-tool resume was exercised successfully for both original books.
These commands do not select the landscape layout:

```sh
make publication-editions
make check-publication-editions
```

The first target uses `--resume`: it verifies source, manifest, profile, tool
and output hashes before accepting an existing edition. For a fresh build:

```sh
make publication-editions PUBLICATION_OUTPUT=output/atlas-optional-v3-rebuild
make check-publication-editions PUBLICATION_OUTPUT=output/atlas-optional-v3-rebuild
```

Override `PUBLICATION_IZZI` and `PUBLICATION_EPUBCHECK` for another Izzi
checkout or EPUBCheck jar. The defaults use the sibling Izzi checkout and
`build/pod-tools/epubcheck-5.4.0/epubcheck.jar`. The adapter retains the
existing optional pikepdf location, `build/setouchi-h3-python`. Input paths
and hashes are frozen in the generated `sources/*.manifest.json` files;
the original frozen data/render assets must be available to rebuild.

The delivered `sources/environment.json` records the base Git revisions and
versions. `sources/production-tools/` preserves the exact production scripts
and profile used during rendering; their hashes also appear in the receipts.
The implementation is committed in Izzi as `03fd482dd30e279a874af3fbf8907a09c929ac22`.
Fresh builds reproduce the content and layout. The standalone example's
EPUB and JPEG cover reproduce byte-for-byte; Ghostscript refreshes PDF dates
and identifiers, so fresh print PDFs are identical only after those fields
are excluded. A resumed delivery retains and verifies its exact bytes.

Izzi usage and tests are documented in its `docs/publication.md`,
`docs/visual_workflow/tool_publication.md`, and `examples/publication/README.md`.
The implemented optional targets are `check-publication-unit`,
`check-publication-integration`, and `examples-publication`. The revised
design above replaces the portrait page layout. Existing tests remain useful
baseline checks; the facing-spread and maximum-fit checks above cover the
implemented landscape revision.
