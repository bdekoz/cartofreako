# v4: full-bleed maps across portrait A4 spreads

The full [v4 production and design record](https://github.com/bdekoz/izzi/blob/main/docs/development/sessions/20261114_pod_expanded_v4.md)
moved to Izzi on 17 November 2026. It preserves the approved spread layout,
bleed geometry, legend sequencing and review decisions. This note keeps
Cartofreako's completed delivery and reproduction entry point beside its
content-specific evidence.

## Completed delivery

The [v4 delivery directory](../../output/atlas-optional-v4-spread/README.md)
contains **162 World Atlas pages** and **38 Starlink Star Light pages**, plus
reflowable EPUBs and ebook covers. Each complete map occupies two full-bleed
portrait A4 pages, followed by two legend/source pages. The content remains
the same frozen 39 World maps and eight Starlink World/USA views as the
[landscape delivery](20261114_pod_expanded_v2.md).

All **200 print pages** decode. All 47 four-page chapters preserve **403
paragraphs, 421 keys and 1,541 source SVG text lines**. Reconstructed map
halves match complete-spread pixel hashes and fold bleed. Both EPUBs passed
EPUBCheck 5.4.0 without errors or warnings; every page/spread and selected
reader previews were visually inspected. The
[validation record](20261114_pod_expanded_v4.validation.json) identifies exact
outputs, production snapshots and review scope.

The external ebook covers are **1600 x 2560 pixels**. Use the
`.ebook-cover.1600.jpg` and `.cover1600.epub` files in the delivery README;
the [cover correction](20261114_ebook_cover_1600.md) explains the separate
upload and embedded-image limits. Original book receipts remain preserved.
The World Atlas [typographic print-cover master](20261114_world_atlas_print_cover.md)
is a separate delivery with its own reproduction notes.

## Reproduce from Cartofreako

Run from the **Cartofreako checkout root**, with the original source assets
and the matching Izzi production tools available:

```sh
make publication-editions-v4
make check-publication-editions-v4
```

The build target includes the digital cover export stage. Set
`PUBLICATION_SPREAD_OUTPUT` to a new directory for a fresh build.
`PUBLICATION_IZZI` and `PUBLICATION_EPUBCHECK` override the sibling engine
and EPUBCheck jar. Resume checks source assets, manifests, profiles, tool
hashes and output hashes; use the delivery's frozen tools for its original
receipts. See the delivery README for exact inputs and snapshots.

Cartofreako retains the adapter, content checker, compact validation JSON
and delivery notes. Generated books, full receipts, covers and previews
remain local artifacts. Izzi owns the reusable `portrait-map-spreads-v1`
layout, print profile, PDF/EPUB production and independent PDF review.

## Viewing and publishing

Review images crop to the TrimBox and join the map pages. A viewer showing
MediaBox includes the extra bleed outside the finished pages. Reflowable
EPUBs retain complete unsplit maps, adjustable text and source links.

Binding can obscure fine marks at the fold, and dense source labels still
need enlargement. Final provider templates, binding and wraparound-cover
checks, retailer validation and a physical proof remain publishing steps.
No book or proof is uploaded or ordered by these build targets.
