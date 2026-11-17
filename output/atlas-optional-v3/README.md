# A4 and digital book editions - 14 November 2026

These are the complete World atlas and Starlink Star Light v3 editions,
produced by Izzi from Cartofreako's frozen maps, legends and source notes.

| Book | A4 print interior | Reflowable EPUB | External ebook cover |
| --- | --- | --- | --- |
| World Atlas: 39 maps, 58 pages | PDF, 33.65 MiB (`output/atlas-optional-v3/atlas-world.20261112.v3.a4.ingramspark.pdf`) | EPUB, 13.33 MiB (`output/atlas-optional-v3/atlas-world.20261112.v3.epub`) | RGB JPEG (`output/atlas-optional-v3/atlas-world.20261112.v3.ebook-cover.jpg`) |
| Starlink Star Light v3: eight World/USA maps, 30 pages | PDF, 11.92 MiB (`output/atlas-optional-v3/starlink-star-light.v3.a4.ingramspark.pdf`) | EPUB, 8.95 MiB (`output/atlas-optional-v3/starlink-star-light.v3.epub`) | RGB JPEG (`output/atlas-optional-v3/starlink-star-light.v3.ebook-cover.jpg`) |

The print PDFs are interiors for an IngramSpark A4 portrait premium-color
paperback: 210 x 297 mm, no bleed or printer marks, mirrored 20/15 mm inner/outer
margins, embedded fonts, live black-only text, approximately 300 ppi CMYK
artwork and a 240% total-ink cap. They were generated as PDF/X-3:2002 and pass
the documented local preflight. Full independent PDF/X certification was
unavailable. Final retailer validation and a physical proof are still needed.

The EPUBs retain all map chapters, interpretation, keys and sources with
adjustable XHTML text, navigation and image descriptions. Images are RGB and
at most 3.2 million pixels; the separate ebook covers are 1400 x 2240 pixels.
Use the EPUB and matching JPEG for electronic title setup at IngramSpark or
KDP. These covers are not print wraparound covers.

KDP's A4 premium-color size accepts this page-count range; standard color is
unavailable at A4. Lulu needs its own product/template assessment. Both books
are below Lulu's 72-page minimum for Amazon color-print distribution. See the
[delivery notes and reproduction commands](../../docs/development/20261114_pod_expanded_v2.md),
which link to the full dated provider assessment in Izzi.

## Content and reading

The World book retains all 39 map/legend pairs from
`atlas-world.20261112.v3.pdf`, its original edition/acquisition information,
291 explanatory/source paragraphs and 265 key entries. Its ebook overview
images reuse the existing 80-page mobile PDF (`output/data-edition/20261111/atlas/atlas-world.20261112.v3.mobile.pdf`).
Print overviews and enlarged details use original artwork, not the mobile PDF.

Starlink retains all eight SLSL1-SLSL4 World/USA map/legend pairs, 112
paragraphs and 156 keys. Its celestial context keeps the 29 October 2026
source time; orbital views retain 9 November at 01:12 UTC; ground
infrastructure retains the 3 November source snapshot. These are deliberately
different from the World atlas's dates. Page 30 is intentional even-page padding.

Longer print keys read across each row, then down. Original symbol swatches
retain their local background. Whole-map images show relationships across
the composition; dense original labels require enlargement. Selected detail
panels help, but do not make every original label readable at A4. Original
label overlaps remain in the artwork. Reflowed explanations and keys are live
text in both print and electronic editions.

## Validation and evidence

Six fast Izzi tests and four renderer/integration tests pass. The Cartofreako
integration check accounts for 47 chapters and 1,541 source SVG text lines,
and compares the final PDF and EPUB text with the extracted source content.
All 88 print pages decode. Actual image placements meet approximately 300 ppi;
fonts, page boxes, color/transparency, ink samples, text safety bounds and
K-only text pass. Both EPUBs pass EPUBCheck 5.4.0 with zero errors and warnings.

All pages were visually inspected in contact sheets; selected larger page
renders and ebook covers were reviewed. Firefox previews cover phone/tablet
widths and 24 px text in a dark theme. These are browser viewport simulations,
not physical device tests or Kindle Previewer acceptance.

- `sources/*.manifest.json` and `*.content.json`: frozen asset hashes,
  chapter order, source text and content inventory.
- `sources/environment.json` and `sources/production-tools/`: exact version
  evidence, base revisions, production code/profile snapshots and SHA-256 hashes.
- `validation/*.json`: build receipts, output hashes, independent placement
  review and content checks; `.log` files contain actual tool output.
- `validation/*.pages/` and `*.reader/`: contact sheets, selected large renders
  and browser screenshots, with inspection results in the review reports.

Build receipts record visual review as pending at build time. The subsequent
`*.review.json` and `*.reader/reader-review.json` files record the completed
inspection and its scope; the original build receipts remain unchanged.
The source-controlled [compact validation record](../../docs/development/20261114_pod_expanded_v2.validation.json)
preserves the delivery identity without committing large generated files.

## Rebuild and publishing steps

From the Cartofreako root, run `make publication-editions` to verify/resume
this delivery and `make check-publication-editions` for the content audit.
Choose a new `PUBLICATION_OUTPUT` directory for a fresh render. The sibling
Izzi checkout, frozen source assets and optional production dependencies are
required. See the expanded plan for path overrides and full commands.

Final print setup still needs a separate provider-template wraparound cover
for the chosen binding/paper, page count and ISBN. Electronic setup needs
final title metadata and Kindle Previewer/retailer checks. No ISBN was
invented; EPUB identifiers are distinct UUID URNs. No files were uploaded,
books published, or proofs ordered by this local production workflow.
