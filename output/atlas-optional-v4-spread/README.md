# v4: full-bleed maps across portrait A4 spreads

Each complete map spans two facing portrait A4 pages. The next two facing
pages contain its legend, interpretation and source notes. All 47 maps
retain their complete original extent; their background extends to every
page edge. The map pages contain no publication headings or page numbers.

| Book | Full-bleed print interior | Reflowable EPUB | Ebook cover |
| --- | --- | --- | --- |
| World Atlas | [162 pages, 98.78 MiB](atlas-world.20261112.v4.a4-portrait-spread.pdf) | [13.34 MiB](atlas-world.20261112.v4.epub) | [RGB JPEG](atlas-world.20261112.v4.ebook-cover.jpg) |
| Starlink Star Light v3 | [38 pages, 23.42 MiB](starlink-star-light.v4.a4-portrait-spread.pdf) | [8.96 MiB](starlink-star-light.v4.epub) | [RGB JPEG](starlink-star-light.v4.ebook-cover.jpg) |

## Geometry and reading order

Each finished page is **210 x 297 mm**; the open spread is **420 x 297 mm**.
There is **3 mm bleed on every edge**, so PDF MediaBox/BleedBox is 216 x
303 mm per page. Text pages keep mirrored safe margins. Map pages have no
inner or outer white margins: the complete map is proportionally fitted to
the spread, with the original border background extended where needed.

Each chapter occupies exactly four consecutive pages: even/odd map pages,
then even/odd legend pages. At 12 pixels/mm (**304.8 ppi**), the map is rendered
once and split into matching halves. Fold bleed includes the adjacent half's
pixels outside the trim; outer bleed extends edge pixels. Review images
crop to TrimBox, so the map joins continuously. A PDF viewer displaying the
MediaBox shows the extra bleed outside the finished page.

Legends retain 10.5 pt body/key type and 9.5 pt source notes. Read keys across
each row, then down; read explanatory text down each column. World uses
25 mm inside text margins at its final page count; Starlink uses 13 mm.
These allowances apply to text pages, not the full-bleed map spreads.

All 39 World maps retain 291 original paragraphs and 265 keys. All eight
Starlink World/USA views retain 112 paragraphs and 156 keys. Source dates
and geographic assets are unchanged. v4 identifies this layout variation;
the Starlink collection remains v3 source content. Selected enlarged details
remain in EPUB; print uses the complete larger map spread. EPUB keeps
unsplit maps, real adjustable text, source links and chapter navigation.

## Validation and previews

All **200 PDF pages** decode, and all **47 four-page sequences** pass
the content audit. Independent inspection of the final PDF image pixels
reconstructs every complete map, checks its recorded hash and confirms exact
matching fold bleed. Full-bleed placement, maximum proportional source fit,
A4 trim/bleed boxes, embedded fonts, K-only text, CMYK artwork, 300 ppi minimum
resolution and the 240% total-ink cap pass.

Both EPUBs pass **EPUBCheck 5.4.0 with zero errors and warnings**. The audit
accounts for all **403 paragraphs, 421 keys and 1,541 source SVG text lines**.
Eight fast tests and eight integration tests pass, including wrong-half
rejection, two-page legend overflow, existing layout regressions and EPUB
build/resume behavior. A separate 14-page generic Izzi example also passes.

Every final page and both spreads of every chapter were inspected in contact
sheets, with selected larger map/legend renders. Selected EPUB chapters were
checked at phone/tablet widths and with large dark-theme text in Firefox.
These are browser viewport simulations; physical-device, Kindle Previewer
and physical print checks were not performed.

- [World map and legend spread previews](validation/atlas-world.20261112.v4.pages/spread-contact-1.jpg)
- [Starlink map and legend spread previews](validation/starlink-star-light.v4.pages/spread-contact-1.jpg)
- [Complete content audit](validation/content.json)
- [Compact validation record](../../docs/development/20261114_pod_expanded_v4.validation.json)
- [v4 design and reproduction notes](../../docs/development/20261114_pod_expanded_v4.md)

`sources/` preserves exact manifests, source extraction, production scripts,
profile, environment and SHA-256 hashes. `validation/` holds build receipts,
actual-PDF reviews, all-page/spread previews, EPUBCheck logs and reader
screenshots. Build receipts record visual review as pending at build time;
the later review reports record the completed inspection.

## Reproduce

From the Cartofreako root:

```sh
make publication-editions-v4
make check-publication-editions-v4
```

For a fresh build, set `PUBLICATION_SPREAD_OUTPUT` to a new directory on both
commands. `PUBLICATION_IZZI` and `PUBLICATION_EPUBCHECK` override tool paths.
The validated production engine is in
[Izzi `a2132cf9`](https://github.com/bdekoz/izzi/commit/a2132cf956cbc9a836f4f397639e43b3b1d946cc).
Exact tool snapshots identify this delivery. The environment and validation
records retain the pre-commit build state; subsequent source commits do not
rewrite that provenance. The previous portrait and landscape editions remain
in their original directories with their frozen receipts. Resume those older
deliveries using their own production-tool snapshots, because tool hashes
are part of each receipt's identity.

Git versions this README and the compact validation record. PDFs, EPUBs,
covers, full receipts, tool snapshots and rendered previews are reproducible
local delivery files; a source checkout does not download those artifacts.

## Print submission

These are neutral full-bleed interior masters generated as PDF/X-3:2002 and
locally preflighted. Independent full PDF/X certification was unavailable.
Provider template/product validation, separate wraparound covers, final
metadata/ISBN setup and a physical proof remain publishing steps. The
physical binding may hide fine marks at the centre fold; dense source labels
still need enlargement. Ebook submission still needs retailer/Kindle Previewer
checks. No files were uploaded and no book or proof was ordered.
