# Expanded print-on-demand and EPUB plan - 14 November 2026

## Decision and scope

**Izzi owns the general publication and production capability. Cartofreako
owns cartographic content and geographic data.** This follows the user's
explicit direction: Izzi is the visualization and production layer, and
these output types are useful beyond cartography.

Produce two independent books, each with an A4 print interior PDF and a
corresponding EPUB, in `output/atlas-optional-v3/`:

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

The inspected export and core surfaces do not yet supply a general EPUB or
POD PDF/X workflow. Izzi's `src/izzi-portrait.h::print_spec` governs physical
mark widths, gaps, and local coverage; it is not a book/publisher specification.
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
| Final Cartofreako delivery files and content-specific receipts | `cartofreako/output/atlas-optional-v3/` |

Implement the shared orchestration as optional Izzi tools with explicit input
and output paths. Keep external PDF, image, and EPUB dependencies outside the
header-only C++ installation. A reusable CLI can consume a versioned
publication manifest without knowing about AuthaGraph, Starlink, NOAA, or the
Cartofreako checkout layout.

Cartofreako should invoke that tool with its prepared manifest. It should not
grow a second EPUB writer, PDF/X converter, or provider policy database.
The existing Cartofreako mobile PDF helper is a migration candidate for the
same generic Izzi exporter; retain a compatibility entry point if it moves.
Existing recipes and source artifacts must remain reproducible during that
transition.

## Provider assessment

Requirements checked against the providers' official material on
14 November 2026. Product availability and the upload validator still govern
the selected binding and printing region.

| Provider | A4 print treatment | Electronic treatment |
| --- | --- | --- |
| IngramSpark | Primary target: A4 portrait, 210 x 297 mm, perfect-bound color paperback. The current matrix includes A4 Premium Color on 70 lb white paper. Use one interior PDF, PDF/X-1a:2001 or PDF/X-3:2002, CMYK, embedded fonts, and no printer marks. | EPUB 3 plus a separate RGB JPEG front cover. Prefer reflowable text because fixed-layout distribution is limited. |
| Amazon KDP / Amazon.com | A4 paperback is available in premium color, 24-590 pages; standard color is unavailable at this size. Check against KDP's A4 preset and its own cover template. | Submit the EPUB directly to KDP. Preserve adjustable text, navigation, image descriptions, and legible maps. |
| Lulu | A4 portrait is offered. Premium Color is the relevant image-book comparison. Apply Lulu's selected product/template rules; its bleed handling differs from IngramSpark. | EPUB supports ebook distribution; a PDF ebook alone is a Lulu-store product. Lulu's Amazon print distribution requires at least 72 pages for color books, which may exclude the shorter Starlink book. |

Sources: [IngramSpark file creation guide, dated 24 August 2026](https://www.ingramspark.com/hubfs/downloads/file-creation-guide.pdf),
[IngramSpark ebook guidance](https://www.ingramspark.com/plan-your-book/ebooks),
[KDP paperback submission guidelines](https://kdp.amazon.com/en_US/help/topic/G201857950),
[KDP color options](https://kdp.amazon.com/en_US/help/topic/GX56BFPW4BKNPGFW),
[Lulu book creation guide](https://assets.lulu.com/media/guides/en/lulu-book-creation-guide.pdf),
[Lulu distribution requirements](https://help.lulu.com/en/support/solutions/articles/64000255462-mandatory-print-book-distribution-requirements),
and [Lulu ebook guidance](https://help.lulu.com/en/support/solutions/articles/64000255507-ebook-creation-the-basics).

Use the IngramSpark file guide's stricter **3.2-million-pixel** EPUB image
limit: its ebook web page instead says 5.6 million. Keep EPUBs below 100 MB.
Document this discrepancy and follow the conservative profile.

Provider comparison is about format suitability, not an invented cost quote.
Printing, shipping, royalties, and final price depend on page count, paper,
printing region, quantity, and distribution choices.

## Print edition design

Use A4 portrait throughout. The initial production profile uses white page
edges and contained artwork, avoiding bleed-dependent pagination. Use at least
13 mm safety margins, with additional inner margin for binding. Body text is
recomposed at approximately 10-11 pt, with source notes around 9-10 pt and
embedded Atkinson Hyperlegible fonts. Small text uses black-only ink.

Do not shrink the original A3 legend sheets into unreadable images. Recover
their text and symbol meaning from the original SVG/legend models and lay
them out for the book. Preserve the original maps as complete overviews;
use additional detail panels where they materially improve reading.

A4 alone does not make 44-inch map labels readable: a 6 pt label reduced
into a roughly 7-inch-wide overview becomes about 1 pt. Identify overviews
as such, keep full explanations and keys readable, and verify selected detail
views at actual print size. Enlargement must come from the original artwork,
not upsampling the mobile PDF.

Planned sequence for each book:

1. Title, edition/credit page, navigable contents, and a reading guide.
2. Complete map views in their established sequence, followed by readable
   keys, interpretation, observation dates, and sources.
3. Enlarged details where required; distinguish celestial coordinates,
   terrestrial subpoints, ground observers, and surface infrastructure.
4. Methods/source notes and colophon. Final page counts follow the completed
   layout and selected product constraints, rather than the old A5 proposal.

Render artwork at approximately 300 ppi at its **placed A4 size**; flatten
complex paths/transparency as needed while preserving newly composed text.
Use a recorded CMYK conversion profile and enforce total ink coverage no
greater than 240%. Record any resulting color changes and inspect the wine,
amber, fine-line, and dense orbital pages.

Export a single-page-sequence PDF/X interior for each book. Check TrimBox,
MediaBox, fonts, image resolution, color spaces, ink coverage, transparency,
and page order. A PDF/X metadata label alone is not a conformance check.

## EPUB design

Use **reflowable EPUB 3**, with one chapter per map/view. Reuse the mobile
World atlas's raster maps as overview assets where they pass image-quality
checks. Produce analogous bounded-resolution assets for Starlink, and use
original artwork for additional detail assets when necessary.

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

1. **Freeze inputs.** Record the two source PDFs, the World mobile derivative,
   individual map/legend sources, content order, and their hashes. Preserve
   existing source dates and source content.
2. **Prepare content in Cartofreako.** Extract structured legend models where
   available and adapt the remaining Starlink legends without OCR or lost
   text. Emit a generic publication manifest.
3. **Implement production in Izzi.** Add reusable, optional manifest-driven
   layout/export/validation tooling. Keep book-specific choices in manifests
   and dated provider constraints in profiles.
4. **Build both editions.** Generate A4 print interiors, EPUBs, cover images,
   manifests, and receipts into the requested output directory.
5. **Validate files.** Run PDF structural/print checks and EPUBCheck. Check
   every page/asset for successful decoding, compare content inventory with
   sources, and inspect representative layouts and dense diagrams visually.
6. **Document delivery.** Update the original POD study and this plan with
   actual filenames, page counts, sizes, checks, and remaining submission
   requirements. Include reproducible commands and the Izzi revision/tool
   hashes consumed by Cartofreako.

## Documentation plan

Document the generic capability in Izzi, then describe Cartofreako's use of
it here. The following paths are proposed additions, not claims that the
interfaces already exist.

| Location | Planned documentation |
| --- | --- |
| `izzi/docs/visual_workflow/tool_publication.md` | End-to-end print, mobile PDF, and EPUB workflow; which inputs each output requires; commands; expected files; validation and failure recovery. Link from the workflow index and portrait/print guide. |
| `izzi/docs/publication.md` | Versioned publication manifest and CLI reference: metadata, page/trim units, text structure, images, fonts, asset hashes, ordering, output paths, profiles, and receipts. |
| `izzi/docs/dependencies.md` | Optional Python, Poppler, Ghostscript, color-profile, and Java/EPUBCheck dependencies; versions exercised; installation/preflight instructions. Keep these separate from C++ consumer dependencies. |
| `izzi/docs/development/sessions/20261114.publication_production.md` | Implementation decisions, existing-exporter reuse, compatibility/migration notes, provider-source dates, test results, and known limitations. |
| `izzi/examples/publication/README.md` | Runnable generic examples with exact commands, checked-in small inputs, output inventory, and expected validation results. |
| `cartofreako/docs/development/20261114_pod_expanded_v2.md` | Accepted scope, repository split, the two real book manifests, reproduction commands, and measured delivery results. |
| `cartofreako/docs/development/20261109_starlink_star_light_v3_pod.md` | Preserve the original study and point to the implemented A4 recommendation, provider comparison, and actual book files. |
| `cartofreako/output/atlas-optional-v3/README.md` | Which files to upload as interiors and ebook covers; book scope, page counts, source dates, validator results, and outstanding print-cover/title-setup steps. |

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
| Page geometry | Exact A4 trim; mixed source frames; crop boxes; 90/180/270-degree rotation; proportional containment; mirrored inner/outer margins; no unintended stretch, clipping, or bleed at the binding edge. | Izzi |
| Text and fonts | Real body text remains searchable in print and adjustable in EPUB; all print fonts embedded; intended small text uses K-only black; long titles, URLs, Unicode, and long legends wrap without overflow or silent loss. | Izzi |
| Image/color pipeline | Rasterize complex vectors and transparency at the placed size; enforce dimension/ppi bounds; verify alpha flattening, RGB ebook images, CMYK print images, total ink coverage, and recorded profiles. Distinguish intentionally lossy output from lossless expectations. | Izzi |
| PDF packaging | PDF syntax, page count/order, boxes, PDF/X declarations and output intent, fonts, image resources, resolution, absence of unsupported transparency/annotations, and no printer marks. Mobile profile additionally checks linearization and bounded image dimensions. | Izzi |
| EPUB packaging | Correct first/uncompressed `mimetype` entry; container and package documents; complete manifest/spine/nav; unique IDs; local resource and fragment links; cover declaration; language/metadata; pixel/file limits; no scripts or missing remote assets. | Izzi |
| External validation | Run EPUBCheck against every final EPUB. Run PDF/X preflight with an independent capable validator where available; record the actual validator and checks rather than inferring compliance from metadata alone. | Izzi |
| Visual regression | Render cover, contents, text-heavy legend, dense vector artwork, and last page. Check full-book thumbnails and representative actual-size pages. Use appropriate tolerances for color conversion and renderer changes. | Izzi |
| Reader behavior | Preview reflow at phone/tablet widths and larger text settings; ensure headings, keys, source links, image captions, and navigation remain usable in light/dark themes. Kindle Previewer remains a named retailer-specific check. | Izzi |
| Content integration | Exactly 39 World atlas maps and eight Starlink World/USA maps; every corresponding legend/source section represented; source dates and hashes preserved; no substitution between the two collections. | Cartofreako |
| Reproduction and failure recovery | Build from a clean example directory; rerun with identical inputs; reject changed inputs under an old receipt; interrupt and resume without replacing a valid prior delivery or accepting partial files. | Izzi, exercised by Cartofreako |

Keep small synthetic fixtures in Izzi: a gradient/transparency drawing, a
dense line field, colored symbols with text, a long multilingual caption,
and mixed page sizes/orientations. These must not require Cartofreako or its
input services. Use the generic artwork to exercise the same implementation
used by the real atlas books.

Suggested optional targets are `check-publication-unit`,
`check-publication-integration`, and `examples-publication` in Izzi, with a
Cartofreako integration target for the two actual books. Final names should
follow each repository's existing target conventions. Fast manifest/geometry
checks can run independently; renderer and EPUBCheck checks should state
their dependency requirements clearly.

Acceptance evidence must identify the tested source/tool/profile hashes and
include machine-readable reports. A passing ZIP/XML or PDF parser check is
insufficient by itself: content coverage, render checks, and visual review
are also required. Do not claim physical proofing, device testing, full
accessibility conformance, or a retailer upload happened when it did not.

## Example plan

| Example | Purpose | Planned outputs |
| --- | --- | --- |
| Izzi visual sampler | A small non-cartographic art/diagram publication with typography, gradients, complex linework, and explanatory text. Demonstrates that the capability belongs to a general production layer. | A4 print PDF, mobile PDF, reflowable EPUB, ebook cover, and receipts. |
| Izzi geometry and overflow fixture | Short automated examples with portrait/landscape sources, rotation, long captions, unusually tall images, and deliberately invalid inputs. Makes the layout and rejection behavior inspectable. | Expected-pass renders and expected-failure reports; not a commercial book. |
| Cartofreako World atlas | Complete 39-map publication, preserving the selected edition's legends and sources. Demonstrates reuse of the existing mobile map images alongside original text and print assets. | Requested A4 IngramSpark interior and corresponding EPUB. |
| Starlink Star Light v3 | Eight World/USA views spanning natural sky, observer sky, satellite subpoints, and ground infrastructure. Exercises complex symbols, dense labels, observer notes, and differing source dates. | Requested A4 IngramSpark interior and corresponding EPUB. |

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

Proposed delivery names:

```text
output/atlas-optional-v3/
  atlas-world.20261112.v3.a4.ingramspark.pdf
  atlas-world.20261112.v3.epub
  atlas-world.20261112.v3.ebook-cover.jpg
  starlink-star-light.v3.a4.ingramspark.pdf
  starlink-star-light.v3.epub
  starlink-star-light.v3.ebook-cover.jpg
  sources/
  validation/
```

These PDFs are **book interiors**. A print submission also needs the separate
full cover produced from the selected provider's template, final page count,
paper/binding, and ISBN. The external ebook front covers do not replace print
wraparound covers. Final account metadata, provider upload checks, Kindle
Previewer review, and a physical print proof are subsequent publishing steps;
the local build does not perform publication or place orders.
