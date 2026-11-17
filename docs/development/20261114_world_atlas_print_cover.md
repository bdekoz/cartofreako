# World Atlas typographic print cover

The cover PDF (`output/atlas-optional-v4-spread/atlas-world.20261112.v4.print-cover.pdf`)
matches the latest 162-page, portrait A4 World Atlas. The right/front panel
has large **CARTO** over **FREAKO**. The left/back panel has **WORLD ATLAS**
and **12 NOVEMBER 2026**, the source edition date. The spine is unlettered.
The design uses amber Atkinson Hyperlegible Bold on wine, without maps,
decorative marks or additional cover copy.

Preview (`output/atlas-optional-v4-spread/atlas-world.20261112.v4.print-cover.png`)
and separate front/back panel masters (`output/atlas-optional-v4-spread/atlas-world.20261112.v4.print-cover.panels.pdf`)
are included. The panels PDF contains the front first, then the back, each
with exact 210 x 297 mm trim and 3.175 mm bleed. It can be placed on a final
printer template independently of the wrap's working spine width.

## Print geometry and status

The wrap has 210 x 297 mm front/back panels, an **11.328 mm spine**, and
3.175 mm outside bleed. Its complete PDF page is **437.678 x 303.350 mm**.
It is a production artwork master awaiting the final title-specific printer
template, not a claim of retailer submission acceptance.

IngramSpark's [public spine calculator](https://myaccount.ingramspark.com/Portal/Tools/SpineCalculator)
returned 0.440 in / 11.176 mm for 162 pages and 0.446 in / 11.328 mm for 164
pages with A4 perfect binding, Color 70 white paper and matte laminate
(public product 4464). The wrap uses 164 as a working allowance for the
manufacturer/barcode pages after the 162-page interior. The
[file checklist](https://www.ingramspark.com/hubfs/downloads/pdf-checklist.pdf)
describes added manufacturing pages; the processed page count and final cover
template govern. The current public A4 selector labels this product Color 70
(standard color), so the record does not silently equate it with the earlier
Premium Color proposal. Confirm the selected paper/product at title setup.

No ISBN or barcode was invented. A 57.15 x 31.75 mm region at the lower left
of the back, inset 20 mm from trim, is clear of text and available for the
printer barcode. The wine background continues through this region; a white
barcode backing is added with the real barcode. See IngramSpark's
[cover requirements](https://www.ingramspark.com/hubfs/downloads/file-creation-guide.pdf).

## Production and checks

The general exporter is `izzi/scripts/build-type-cover.py`. Cartofreako's
[cover specification](20261114_world_atlas_print_cover.json) supplies the
text, geometry, color, edition date, font/ICC hashes and exact interior hash.
It verifies the interior's page count and every page's trim before rendering.

The background is CMYK 15/90/40/85 (230% total ink), and type is 0/22/75/0
(97%). These are deliberate print colors, not a claim of exact sRGB matching.
The PDF uses embedded vector type and flat CMYK fills; no raster resolution
limit is imposed on the letters. Ghostscript exports PDF/X-3:2002 with the
same Artifex CMYK output intent as the interior workflow.

Both PDFs pass local syntax, trim/bleed boxes, embedded fonts, color, ink,
transparency, requested-text and full-decode checks. All type clears panel
trim/fold edges by at least 6 mm, and the barcode region is unobstructed.
The wrap and both panel renders were visually inspected. Independent full
PDF/X certification and a physical proof were not performed. The JSON
receipt beside the cover records hashes, geometry, checks and review scope.

Rebuild into a new filename from the Cartofreako root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=build/setouchi-h3-python \
  python3 ../izzi/scripts/build-type-cover.py \
  docs/development/20261114_world_atlas_print_cover.json \
  output/atlas-optional-v4-spread/atlas-world.20261112.v4.print-cover-rebuild.pdf
```

The exporter refuses to replace an existing cover, panel PDF, preview or
receipt. Change `spine_mm` in a copied specification when the printer template
confirms the final width. Preserve the actual edition date when changing
production dimensions. Calculator responses and the exporter snapshot are
retained under the delivery's `sources/` directory.
