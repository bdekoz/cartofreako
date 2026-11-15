# Mobile PDF optimization - 14 November 2026

The mobile atlas is a flattened, screen-resolution edition of the completed
World atlas. Each page contains one opaque RGB image, so a reader decodes a
bounded-size bitmap instead of repainting the original map's paths, labels,
transparency groups, and high-resolution image layers.

- Source: [`atlas-world.20261112.v3.pdf`](../../output/data-edition/20261111/atlas/atlas-world.20261112.v3.pdf)
- Mobile edition: [`atlas-world.20261112.v3.mobile.pdf`](../../output/data-edition/20261111/atlas/atlas-world.20261112.v3.mobile.pdf)
- Builder: [`scripts/build-mobile-pdf.py`](../../scripts/build-mobile-pdf.py)
- Conversion receipt: [`atlas-world.20261112.v3.mobile.json`](../../output/data-edition/20261111/atlas/sources/atlas-world.20261112.v3.mobile.json)

The completed mobile edition is **17.18 MiB**, reduced from **716.74 MiB**
by **97.60%** (about 41.7 times smaller). All 80 pages are retained. Of the
80 page images, 60 use lossless Flate compression and 20 use JPEG; all 39
A3 legend pages use lossless compression.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Original | 751,560,373 | `2dcbfc480081b0970f9813a73fc4967d54fdc0620ad249f4e961b31300085c11` |
| Mobile | 18,010,765 | `72a41e854d86658a641f5616411e729c99b33a32e35e4ee8154f8e5f7baf2ae1` |

## Relationship to earlier work

The existing [1080p screen exports](../pages/runtime/ai-agent-and-1080p-gaming.md)
and [`generate-screen-1080p.mjs`](../../scripts/generate-screen-1080p.mjs)
established the approach of making smaller raster derivatives from completed
artwork while preserving the master. Those exports fit maps inside a
1920 x 1080 canvas and use lossless PNG/WebP. This PDF uses each page's own
aspect ratio and a 2400-pixel longest edge, giving the A3 legends more room
for readable text and modest zooming.

The earlier [Setouchi H3 work](20261106_setouchi_triennale_futures.md)
rasterized complex cell layers at their placed 300 dpi size, keeping text
and outlines as vectors. Its
[`setouchi_pdf_images.py`](../../scripts/setouchi_pdf_images.py) packaging
deduplicates repeated images and preserves alpha planes and dimensions.
That remains useful for print PDFs. The mobile conversion applies a smaller
pixel budget to the whole finished page and flattens transparency as well.
It reuses the optional pikepdf installation from that work.

SVG-derived content inside a PDF is normally represented by PDF drawing
instructions, not an SVG file that a viewer opens separately. Rasterizing the
finished PDF removes that drawing complexity while retaining its existing
page order, embedded resources, colors, and visible layout. Using the named
PDF as the input also avoids rebuilding the atlas against newer data or
accidentally substituting an older preview image.

## Conversion profile

| Setting | Value |
| --- | --- |
| Page count and order | All 80 source pages, including title, contents, maps, and legends |
| Page frame | Original visible dimensions and aspect ratio; no added padding |
| Maximum raster edge | 2400 pixels |
| Wide map/frontmatter image | 2400 x 1040 pixels |
| A3 landscape legend image | 2400 x 1698 pixels |
| Color and transparency | Opaque 8-bit RGB; existing page appearance composited during rendering |
| Image compression | Smaller of lossless RGB Flate and JPEG quality 85 |
| JPEG settings | 4:4:4 color sampling, optimized coding, baseline JPEG |
| PDF packaging | PDF 1.4, binary image streams, compressed content, linearized |
| Per-page drawing | One image placement; no fonts, text drawing, vector paths, or masks |

The limit is expressed in pixels because the input mixes 44-inch-wide maps
with A3 source sheets. A uniform 150 or 300 dpi export would create very large
map images again. At the retained physical page sizes, this profile gives
roughly 54.5 dpi on the maps and 145 dpi on the legends. It is for screen
reading, not high-resolution printing.

The builder first renders lossless PNG intermediates using Poppler. It then
compares the sizes of the two PDF-compatible encodings for each RGB image.
Lossless Flate often wins for text and flat-color pages, keeping their
rasterized letter edges free of JPEG artifacts. JPEG is smaller for dense
maps and gradients. Disabling chroma subsampling helps retain colored line
and label edges. The selected JPEG bytes are embedded directly without a
second lossy encoding. ASCII85 wrapping is disabled to avoid its size overhead.

Linearization puts first-page data near the front of the file and adds page
access hints. Readers and HTTP servers that support byte-range access can
use this for earlier display while a file downloads. The main gains for
local mobile viewing come from the smaller file and simpler page contents.

## Reproduce the conversion

Run from the repository root. Requirements are `pdftoppm` from Poppler and
the Python packages Pillow, ReportLab, and pikepdf. This conversion used
Poppler 26.01.0, Pillow 12.3.0, ReportLab 4.5.1, and pikepdf 10.17.0.
The existing atlas environment supplies Pillow and ReportLab. If the optional
PDF package is absent, install it in the same local directory as the prior
packaging work:

```sh
python3 -m pip install --target build/setouchi-h3-python \
  -r scripts/requirements-setouchi-h3.txt
```

Build the mobile edition:

```sh
python3 scripts/build-mobile-pdf.py \
  output/data-edition/20261111/atlas/atlas-world.20261112.v3.pdf \
  output/data-edition/20261111/atlas/atlas-world.20261112.v3.mobile.pdf \
  --max-edge 2400 \
  --jpeg-quality 85 \
  --receipt output/data-edition/20261111/atlas/sources/atlas-world.20261112.v3.mobile.json
```

The script refuses to overwrite either the source, an existing destination,
or an existing receipt. For a new comparison, give the output and receipt
new names. It creates intermediate page images under a temporary
`tmp/pdfs/mobile-*` directory, removes them on completion, and records source
and output SHA-256 hashes, byte counts, tool versions, per-page pixel sizes,
and selected encodings in the receipt. PDF metadata timestamps are fixed
for repeatable output; the receipt records the actual conversion time.

The operations are:

1. Hash the source and read each page's visible frame and orientation.
2. Render every page using `pdftoppm -cropbox -scale-to 2400 -png`, with
   text and vector antialiasing enabled. Complex SVG-derived paths and all
   other page contents become pixels at this step.
3. Encode each raster as both RGB Flate and JPEG quality 85, selecting the
   smaller image stream. Assemble the pages with ReportLab in source order.
4. Remove unused font setup, keep only image placement operations, and
   save a linearized PDF with pikepdf.
5. Check page count, visible dimensions, image sizes, opaque RGB encoding,
   lack of vector/text drawing, PDF syntax, and linearization. Rehash the
   original to confirm it is unchanged before writing the deliverables.

For a smaller edition, try `--max-edge 1920 --jpeg-quality 80` with new output
names. For more zoom detail, increase the longest edge to 3000. Increasing
both dimensions increases decoded memory approximately with the square of
the scale, so inspect a dense map and a small-text legend before choosing a
different profile. Repeatedly recompressing the mobile PDF cannot restore
lost detail; regenerate from the original PDF.

## Verification and limitations

Inspect the PDF's metadata, page images, and fonts:

```sh
pdfinfo output/data-edition/20261111/atlas/atlas-world.20261112.v3.mobile.pdf
pdfimages -list output/data-edition/20261111/atlas/atlas-world.20261112.v3.mobile.pdf
pdffonts output/data-edition/20261111/atlas/atlas-world.20261112.v3.mobile.pdf
```

Expect 80 pages, `Optimized: yes`, PDF 1.4, one RGB image per page, no soft
masks, and no font rows. Render the final file with Poppler and inspect the
title/contents, dense atmosphere and orbital maps, small-text legends, and
last page. Check for missing layers, changed framing, blank pages, clipping,
and unreadable text at useful screen zoom levels.

For this edition, all structural checks passed. Poppler rendered and decoded
all 80 final pages without errors or blank pages. Four contact sheets were
visually reviewed, with full-size inspection of the contents, atmosphere
map and legend, dense orbital map, and final mineral legend. The final
images retain the source framing and visible layers; legend body text is
readable at the retained raster size. `pdfimages` reports exactly 80 RGB
images, `pdffonts` reports no fonts, and `pdftotext` finds no text layer.
A separate two-page fixture also exercised crop boxes, rotation, and mixed
page dimensions through the same builder.

Rasterization intentionally removes selectable/searchable text and vector
zoom detail. This builder also does not preserve interactive links,
bookmarks, form controls, or accessibility tags; visible annotations are
flattened into the page image. The source atlas had no document outlines or
page links. Very small map labels and fine marks can merge or disappear at
this pixel budget, and JPEG pages have lossy color/detail changes. The
original edition remains the reference for printing and close inspection.

No physical handset performance test is implied by PDF structure or desktop
render checks.
