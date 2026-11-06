# Setouchi H3 resolution trials — 6 November 2026

Open [the comparison gallery](index.html) for Atmosphere and Temperature
records · 2026, World and Japan, at H3r3, H3r5, and H3r8. H3r3 is the saved
website baseline. The eight new maps have separate legend/source sheets.

The observation dates, source sampling, quality rules, colors, and line
weights are fixed. Both finer products are reaggregated directly from the
same raw samples. Atmosphere retains the 720-samples-per-axis limit;
Temperature uses the original 0.5° CPC centers. These are trials of the H3
grid, with **sample-center support**: gaps are not necessarily missing source
pixels, and finer indexing adds no observations. R8 can expose the sampling
lattice; physical stroke width can exceed the size of a cell.

Atmosphere keeps the amber background, topmost white nominal 0.66 pt
outlines, and the common 100-level radiation opacity scale (0–400 W/m²).
Temperature keeps the wine background and existing count classes. World and
Japan use identical products, with the original modified AuthaGraph framing.

Maps are 44 × 19.052559 inches. SVGs retain separate named data layers and
reference adjacent `layers/` PNGs: keep that directory with the SVG. PDFs are
self-contained, and PNGs are 300 dpi. Coastlines, solar contours, and type
remain vectors in SVG/PDF; dense observed-cell layers render at 300 dpi at
their placed size. WebP details are 3840 pixels; cards are 1280 pixels, with
the saved Japan crop.

PDF packaging shares duplicate image objects used by the cyclic World
layout. For single-hue layers it restores the declared source RGB after
premultiplied-alpha rounding, with at most one 8-bit premultiplied channel
step of difference. Every opacity plane and raster dimension is verified
unchanged. No images are downsampled or JPEG-encoded by packaging.

- [H3r5 World: maps and legends](h3r5/world.pdf)
- [H3r5 Japan: maps and legends](h3r5/japan.pdf)
- [H3r8 World: maps and legends](h3r8/world.pdf)
- [H3r8 Japan: maps and legends](h3r8/japan.pdf)
- [Product provenance](products.json) and [plate provenance](plates.json)
- [Validation](validation.json)
- [Development record](../../docs/development/20261106_setouchi_triennale_futures.md#controlled-h3r5-and-h3r8-plate-trials--6-november-2026)

## Rebuild

Run from the repository root. Existing C++20, GDAL, H3, Alpha60, Izzi, Cairo,
Inkscape, Poppler, and Python image/document dependencies are required. The
optional PDF tooling is pinned and isolated in the ignored build directory:

```sh
python3 -m pip install --target build/setouchi-h3-python -r scripts/requirements-setouchi-h3.txt
python3 scripts/build-setouchi-h3-trials.py
make check-setouchi-h3
python3 scripts/validate-setouchi-h3-trials.py --browser
```

`--prepare-only`, `--render-only`, and `--package-only` resume individual
stages; `--resolutions 5` or `--resolutions 8` limits a run. Run the default
both-resolution delivery or `--package-only` afterwards for the complete
comparison gallery. Input hashes and cache receipts prevent reuse after a
source or renderer changes. The original raw-source files must remain
available; the build does not fetch new observations.

Inkscape's local PNG decoder needs its D-Bus service. A sandbox that blocks
that service must allow the local render process to use it; the builder now
fails on decoder errors, and validation rejects missing-image placeholders
inside PDFs even if Inkscape returned success.

Intermediate GeoJSON and projected raster layers stay under
`build/setouchi-h3-trials-20261106/`. Their hashes, profiles, source-manifest
hashes, and packaging checks are retained in `sources/`. The atlas masters,
H3r3 website package, WordPress page, and outreach remain unchanged.
