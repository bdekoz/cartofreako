# A4 landscape and EPUB editions - 14 November 2026

Each complete cartographic plate occupies an even left page, at the largest
proportional scale within its safe frame. The matching title, complete symbol
key and primary context occupy the facing odd right page. The map pages
contain only their original cartography.

| Book | A4 landscape interior | Reflowable EPUB | Ebook cover |
| --- | --- | --- | --- |
| World Atlas | [102 pages, 55.16 MiB](atlas-world.20261112.v3.a4-landscape.pdf) | [13.34 MiB](atlas-world.20261112.v3.epub) | [RGB JPEG](atlas-world.20261112.v3.ebook-cover.jpg) |
| Starlink Star Light v3 | [38 pages, 17.96 MiB](starlink-star-light.v3.a4-landscape.pdf) | [8.96 MiB](starlink-star-light.v3.epub) | [RGB JPEG](starlink-star-light.v3.ebook-cover.jpg) |

The interiors use true **297 x 210 mm** pages. Top, bottom and outer margins
are 13 mm. World Atlas uses a 16 mm total inner margin and a 268 x 184 mm
map frame; Starlink uses 13 mm inside and a 271 x 184 mm frame. Panoramic
source plates fill the width while retaining their aspect ratio and complete
coverage. Original labels, graticules and insets remain with the artwork.
There are no publication headings, captions or folios on the map pages.

The World book retains all 39 maps, 291 explanatory/source paragraphs and
265 key entries. Starlink retains all eight World/USA views, 112 paragraphs
and 156 keys. Source dates and original assets are unchanged. All keys and
the selected interpretation context fit on each facing page at 10.5 pt body
type, using two or three columns; source notes use 9.5 pt. Read keys across
rows and explanatory prose down each column. Longer notes, bibliography and
selected original-artwork details continue after the map/legend pair.

Alignment blanks and final even-page padding are intentional and recorded
in each receipt's page-role inventory. Contents point to the map pages.
The EPUBs retain real adjustable text, navigation, source links and RGB
images in one chapter per map, without imposed print spreads or blank pages.
The JPEGs are ebook front covers, 1400 x 2240 pixels.

## Validation

All **140 PDF pages** decode. Independent checks of actual PDF image
matrices confirm all 47 facing pairs and maximum proportional map fit
(largest placement error 0.000147 mm; tolerance 0.1 mm).
Minimum actual placed resolution is 300.004 ppi. Page boxes,
embedded fonts, K-only text, text safety bounds, CMYK artwork, transparency
and the 240% ink cap pass. Both EPUBs pass **EPUBCheck 5.4.0 with zero errors
and warnings**. The content audit accounts for all 403 paragraphs, 421 keys
and 1,541 source SVG text lines in print and EPUB.

Seven fast Izzi tests and six integration tests pass, including primary-key
overflow, multi-column continuations, source rotation/crops, final blank-page
preservation through PDF/X conversion, resume rejection and independent
placement/parity checks. The standalone landscape example also builds and
validates without Cartofreako data.

Every final page and all map/legend spreads were inspected in contact sheets,
with selected larger page renders. Selected EPUB chapters were inspected at
phone/tablet widths and with large dark-theme text in Firefox. These are
browser viewport simulations, not physical-device or Kindle Previewer tests.
Dense source labels and source overlaps still require enlargement.

- [World spread previews](validation/atlas-world.20261112.v3.pages/spread-contact-1.jpg)
- [Starlink spread previews](validation/starlink-star-light.v3.pages/spread-contact-1.jpg)
- [Content audit](validation/content.json)
- [Compact validation record](../../docs/development/20261114_pod_expanded_v2.landscape.validation.json)
- `sources/`: frozen manifests, content extraction, environment and exact
  production-tool/profile snapshots with SHA-256 hashes.
- `validation/`: build receipts, actual-placement reviews, decoding/EPUBCheck
  logs, all-page/spread contact sheets and reader screenshots.

Build receipts record visual review as pending at build time; subsequent
review reports record the completed inspection without changing those receipts.

## Reproduce

From the Cartofreako root:

```sh
make publication-editions-landscape
make check-publication-editions-landscape
```

The first command verifies source, manifest, profile, production-tool and
output hashes before resuming. For a fresh build, set
`PUBLICATION_LANDSCAPE_OUTPUT=output/atlas-optional-v3-landscape-rebuild` on
both commands. `PUBLICATION_IZZI` and `PUBLICATION_EPUBCHECK` override the
sibling Izzi checkout and EPUBCheck jar. The original frozen source assets
must remain available. Exact tool/profile snapshots identify this delivery;
the environment and validation records preserve its pre-commit build state.

The newer v4 engine has a different tool hash and intentionally rejects a
resume of these older receipts. To verify the existing landscape files, copy
`izzi_publication.py`, `build-publication.py` and `review_raster.py` from this
delivery's `sources/production-tools/` into a temporary `scripts/` directory,
and copy `a4-landscape-facing-20261114.json` into its `config/publication/`.
Pass that temporary root as `PUBLICATION_IZZI` to the build command above.
The content-check command works with the current Cartofreako checker. A fresh
build with the current engine uses a new output directory.

Git versions this README and the compact validation record. PDFs, EPUBs,
covers, full receipts, tool snapshots and rendered previews are reproducible
local delivery files; a source checkout does not download those artifacts.

## Print submission

These are neutral A4 landscape **interior masters**, generated as PDF/X-3:2002
and locally preflighted. Independent full PDF/X certification was unavailable.
Lulu lists the exact landscape trim; final binding, paper, region and retail
distribution eligibility still need product setup. These files are not
labeled as IngramSpark or KDP landscape interiors. See the dated
[provider assessment](../../docs/development/20261114_pod_expanded_v2.md#provider-assessment).

Print submission still needs the selected provider's template/export checks,
a separate wraparound cover based on final binding and page count, final
title/ISBN setup and a physical proof. Ebook setup still needs retailer/Kindle
Previewer checks. No files were uploaded and no books or proofs were ordered.
The previous portrait delivery remains in `output/atlas-optional-v3/`.
