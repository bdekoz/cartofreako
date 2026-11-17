# A4 landscape print-on-demand and EPUB delivery - 14 November 2026

The full [A4 landscape and portrait production plan](https://github.com/bdekoz/izzi/blob/main/docs/development/sessions/20261114_pod_expanded_v2.md)
moved to Izzi on 17 November 2026. It preserves design decisions, production
ownership, dated provider research, implementation stages and test planning.
This note keeps Cartofreako's delivery evidence and reproduction commands
beside its content adapter and frozen inputs.

The later [v4 variation](20261114_pod_expanded_v4.md) puts each complete map
across two full-bleed portrait A4 pages, followed by two legend/source pages.

## Landscape delivery

The [landscape delivery directory](../../output/atlas-optional-v3-landscape/README.md)
contains both books, with the complete map on an even left A4 landscape
page and its primary legend on the next odd right page.

| Book | A4 landscape interior | Reflowable EPUB |
| --- | --- | --- |
| World Atlas | 102 pages, 55.16 MiB (`output/atlas-optional-v3-landscape/atlas-world.20261112.v3.a4-landscape.pdf`) | 13.34 MiB (`output/atlas-optional-v3-landscape/atlas-world.20261112.v3.epub`) |
| Starlink Star Light v3 | 38 pages, 17.96 MiB (`output/atlas-optional-v3-landscape/starlink-star-light.v3.a4-landscape.pdf`) | 8.96 MiB (`output/atlas-optional-v3-landscape/starlink-star-light.v3.epub`) |

The delivery retains all **47 maps, 403 paragraphs, 421 keys and 1,541
source SVG text lines**. All 140 print pages decode; placement, parity,
resolution, margins, fonts, color and ink checks pass. Both EPUBs passed
EPUBCheck 5.4.0 without errors or warnings. The
[landscape validation record](20261114_pod_expanded_v2.landscape.validation.json)
identifies exact outputs, tools, profiles and visual review scope.

## Reproduce from Cartofreako

Run from the **Cartofreako checkout root**:

```sh
make publication-editions-landscape
make check-publication-editions-landscape
```

Existing landscape receipts require the frozen production tools described
in the [delivery reproduction instructions](../../output/atlas-optional-v3-landscape/README.md#reproduce).
For a fresh build with current Izzi tools, select a new directory:

```sh
make publication-editions-landscape PUBLICATION_LANDSCAPE_OUTPUT=output/atlas-optional-v3-landscape-rebuild
make check-publication-editions-landscape PUBLICATION_LANDSCAPE_OUTPUT=output/atlas-optional-v3-landscape-rebuild
```

`PUBLICATION_IZZI` and `PUBLICATION_EPUBCHECK` override the sibling Izzi
checkout and EPUBCheck jar. Source manifests, profiles, tool snapshots and
hashes remain with each delivery. The original source assets must be available.

## Previous portrait delivery

The [portrait delivery directory](../../output/atlas-optional-v3/README.md)
retains the earlier **58-page World Atlas** and **30-page Starlink** interiors,
their EPUBs and ebook covers. The
[original validation record](20261114_pod_expanded_v2.validation.json) remains
with Cartofreako. These historical commands require that delivery's frozen
production tools, selected with `PUBLICATION_IZZI`:

```sh
make publication-editions
make check-publication-editions
```

## Provider assessment

The [dated provider assessment](https://github.com/bdekoz/izzi/blob/main/docs/development/sessions/20261114_pod_expanded_v2.md#provider-assessment)
is preserved in the Izzi record. Provider-specific format, binding and cover
checks, independent PDF/X certification, retailer previews and a physical
proof remain publishing steps. The local build targets create and validate
files; no upload, publication or order was performed.

Cartofreako owns the map selection, original observation dates, source
bibliography, publication manifests and content audit. Izzi owns reusable
layout, raster/color conversion, PDF, mobile and EPUB production. See also
the [mobile PDF delivery](20261114_pdf_optimization_mobile.md) and
[earlier Starlink format study](20261109_starlink_star_light_v3_pod.md).
