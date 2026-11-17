# Mobile PDF optimization - 14 November 2026

The full [mobile PDF production record](https://github.com/bdekoz/izzi/blob/main/docs/development/sessions/20261114_pdf_optimization_mobile.md)
moved to Izzi on 17 November 2026. It preserves the conversion method,
exporter migration, original hashes, verification and limitations. This note
keeps the Cartofreako delivery and reproduction entry point beside its inputs.

## Completed delivery

The World atlas mobile edition retains all **80 pages** at a 2400-pixel
longest edge. It is **17.18 MiB**, reduced from **716.74 MiB** by **97.60%**.
Each page contains one opaque RGB image; 60 use lossless Flate and 20 use
JPEG, with all 39 A3 legend pages lossless.

| Artifact | Local delivery |
| --- | --- |
| Original atlas | [atlas-world.20261112.v3.pdf](../../output/data-edition/20261111/atlas/atlas-world.20261112.v3.pdf) |
| Mobile edition | [atlas-world.20261112.v3.mobile.pdf](../../output/data-edition/20261111/atlas/atlas-world.20261112.v3.mobile.pdf) |
| Original conversion receipt | [atlas-world.20261112.v3.mobile.json](../../output/data-edition/20261111/atlas/sources/atlas-world.20261112.v3.mobile.json) |

The original receipt uses `cartofreako-mobile-pdf-v1`. New Izzi conversions
use `izzi-mobile-pdf-v1`; preserve the existing delivery and receipt.
Rasterization removes searchable text, interactive features and vector zoom
detail. Retain the original atlas for printing and close inspection.

## Reproduce from Cartofreako

Run from the **Cartofreako checkout root**, with sibling `../izzi` available
or `IZZI_ROOT` set to that checkout. The
[compatibility entry point](../../scripts/build-mobile-pdf.py) delegates to
Izzi's generic exporter. Requirements are Poppler's `pdftoppm`, Pillow,
ReportLab and pikepdf; the wrapper retains `build/setouchi-h3-python` as an
optional dependency location.

Use new output and receipt names for a fresh conversion:

```sh
python3 scripts/build-mobile-pdf.py \
  output/data-edition/20261111/atlas/atlas-world.20261112.v3.pdf \
  output/data-edition/20261111/atlas/atlas-world.20261112.v3.mobile-rebuild.pdf \
  --max-edge 2400 \
  --jpeg-quality 85 \
  --receipt output/data-edition/20261111/atlas/sources/atlas-world.20261112.v3.mobile-rebuild.json
```

The [publication delivery notes](20261114_pod_expanded_v2.md) describe the
print and EPUB editions that use the same frozen content.
