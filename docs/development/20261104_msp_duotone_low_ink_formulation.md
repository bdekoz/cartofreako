# MSP duotone formulation and low-ink proof strip

Production date: 4 November 2026.

Create a companion ink proof for MSP 5 containing all four approved
Randoma11y pairs, their RGB formulations, clickable palette links and map
samples at their original print scale. The requested filename is
**`msp-4-ink-profile.20261104.svg`**; retain that spelling and number while
using the current **MSP 5** artwork and settings. Export matching PNG and
PDF files alongside it.

## Background and purpose

The reported printing conditions are an **Epson Stylus Pro 9000**, low
**cyan and light magenta** inks, and **metallic glossy paper**. Grays were
reported to print as light violet, and darker backgrounds were preferred
to white backgrounds on this paper. The earlier green designs were rejected;
the atlas now defaults to wine/amber, with three other approved pairs
available for comparison.

These pairs specify intended RGB colors. No measured printer response or
ICC characterization was supplied, so the formulation does not predict the
final printed hue or apply a computed ink correction. Despite the requested
`ink-profile` filename, this is a physical comparison strip rather than an
ICC profile. Its purpose is to compare the actual swatches, small type and
colored map marks under the reported production conditions.

The pairs control the map ground and typography. Astronomy symbols and
orbital vendor colors retain their source encodings, including the black
debris x marks with light halos. The samples therefore test the palette in
the context of the existing multicolor artwork.

The preceding decisions and source refresh are recorded in the
[November 3 work log](20261103_starlink_update_explore.md); the
[atlas guide](../pages/getting-started/generation-styles.md#setouchi-st2-print-layout)
records the adopted defaults.

## Formulations

Use the exact saved pairs from
[`config/msp-speculations-20261103.json`](../../config/msp-speculations-20261103.json)
and the [Randoma11y source receipt](../../config/randoma11y-pairs-20261103.json).
Each panel shows both colors as solid boxes, followed by `rgb(r,g,b)` labels
and hexadecimal values. The palette heading, boxes and printed URL form a
clickable link in the SVG and PDF; the PNG retains the visible URL text.

| Pair | Ground box | Foreground box | Randoma11y link |
| --- | --- | --- | --- |
| Wine / amber | `rgb(36,4,19)` / `#240413` | `rgb(252,197,83)` / `#fcc553` | [Open wine / amber](https://randoma11y.com/%23fcc553/%23240413) |
| Ultramarine / porcelain | `rgb(25,63,184)` / `#193fb8` | `rgb(245,234,231)` / `#f5eae7` | [Open ultramarine / porcelain](https://randoma11y.com/%23193fb8/%23f5eae7) |
| Plum / ice blue | `rgb(42,12,65)` / `#2a0c41` | `rgb(115,222,249)` / `#73def9` | [Open plum / ice blue](https://randoma11y.com/%2373def9/%232a0c41) |
| Midnight blue / champagne | `rgb(1,4,52)` / `#010434` | `rgb(234,215,132)` / `#ead784` | [Open midnight / champagne](https://randoma11y.com/%23ead784/%23010434) |

The link destinations follow the approved recipe and are checked in the
SVG and exported PDF.

## Strip layout

The sheet is **44 inches × 20 cm**: **1117.6 × 200 mm**, with a viewBox
corresponding to 44 × 7.874015748 inches. Four adjacent panels are each
**10.5 inches / 266.7 mm wide**, occupying 42 inches. The remaining width is
split into **one-inch left and right margins**.

Each panel contains:

1. Its palette name and the two solid color boxes, each 4.8 × 0.6 inches.
2. The RGB formulations, hex values and the exact Randoma11y pair URL.
3. An astronomy all-sky crop, an orbital global crop and an orbital observer
   crop, each **9.85 × 1.15 inches**. Both orbital views are included so the
   strip tests NORAD IDs and satellite names.

All panels use the same crop for each subject. Crops are measured from the
upper-left corner of the already framed 44-inch source sheet:

| Source subject | Left / top, inches | Size, inches | Printed object labels |
| --- | --- | --- | --- |
| Astronomy all sky | 10.00 / 8.50 | 9.85 × 1.15 | 12 pt; includes Moon, HD 260655 and Halley context |
| Orbital technosphere global | 18.25 / 13.25 | 9.85 × 1.15 | 6 pt Starlink NORAD IDs |
| Orbital technosphere observer | 31.00 / 7.75 | 9.85 × 1.15 | 6 pt Starlink names |

The samples retain **1:1 physical scale**, 1.5× Starlink sunbursts, vendor
colors, marker-over-label order and the global plate's doubled trajectory
strokes. Cropping changes the visible extent, not the projection or the
printed type size. Source dates remain **29 October 2026, 20:00 UTC** for
astronomy and **3 November 2026, 17:10 UTC** for the orbital plates. The
observer sample is the world/San Francisco view from MSP 5.

## Production and reproduction

The durable builder is
[`scripts/build-msp-ink-profile.py`](../../scripts/build-msp-ink-profile.py).
It reads the twelve approved compressed map SVGs from the four MSP 5
palettes, verifies their source hashes, and embeds clipped vector samples
with unique IDs. Objects wholly outside the crop are pruned to keep the
editable file manageable; original basemap and trajectory vertices remain
unchanged. A source-pixel comparison checks that this pruning preserves the
rendered samples.

```sh
make msp-ink-profile
# Equivalent direct invocation:
python3 scripts/build-msp-ink-profile.py
```

The output directory is
`output/msp-speculations-20261103/msp-speculation-5/`. The SVG and PDF have
exact physical sheet dimensions. The PNG is rendered at **300 dpi**,
**13,200 × 2,362 pixels**, with its height rounded to the nearest pixel.
Typography uses the bundled Atkinson Hyperlegible fonts. No existing MSP
map, legend, palette recipe or atlas default needs to be regenerated.

Print the PDF at **100% / actual size**, with fit-to-page scaling disabled.
Use one paper stock, orientation and printer/driver setup for all four
panels. Record the selected media setting, color-management settings, ink
condition and viewing light alongside the proof. Compare the solid swatches
with their intended hues, then inspect 6 pt satellite names, 12 pt astronomy
labels, vendor distinctions and the black debris marks. Because the substrate
is metallic, record the viewing angle used for the comparison as well.

A preferred result can guide a subsequent palette choice. Measured readings
and a controlled printer state would be needed to formulate a calibrated
color correction; this strip supplies neither by itself.

## Deliverables and checks

The requested files are:

- [Editable SVG](../../output/msp-speculations-20261103/msp-speculation-5/msp-4-ink-profile.20261104.svg)
- [300 dpi PNG](../../output/msp-speculations-20261103/msp-speculation-5/msp-4-ink-profile.20261104.png)
- [Print PDF](../../output/msp-speculations-20261103/msp-speculation-5/msp-4-ink-profile.20261104.pdf)
- [Source and validation receipt](../../output/msp-speculations-20261103/msp-speculation-5/msp-4-ink-profile.20261104.provenance.json)

The builder checks sheet dimensions, four 10.5-inch panels, exact swatch/RGB
label matches, unique embedded IDs, internal references and retained physical
label sizes. For each of the three subjects, it compares the cropped wine/amber
artwork with an unmodified source crop at 300 dpi. It also checks PNG size,
PDF page size and all four clickable Randoma11y destinations. The receipt
records source, configuration, font, builder and output checksums.

Completed verification on 4 November 2026:

- The SVG and PDF are 44 inches × 200 mm; the PDF page is
  **3168 × 566.929 points**. The PNG is **13,200 × 2,362 pixels at 300 dpi**.
- All eight rendered swatch centers exactly match their RGB labels, and
  all four Randoma11y links are present as PDF link annotations.
- The three pruned sample crops match the unmodified wine/amber source
  crops pixel for pixel at 300 dpi.
- PDF text inspection confirms **12 pt astronomy labels**, **6 pt Starlink
  names** and **18 pt RGB labels**. Both Atkinson Hyperlegible font faces
  are embedded. SVG checks also confirm the global NORAD IDs remain 6 pt.
- The rendered strip was visually inspected for panel boundaries, clipped
  samples, palette differences and readable swatch labels. Each crop has an
  explicit clipping path so its source background stays inside its window
  in both raster and PDF exports.

The digital proof is complete. The physical printing and hue comparison
remain the next production step; no printed result has been measured.
