# Setouchi futures — selected H3r5 edition

Open the [website gallery](index.html) or the [four print plates](print/index.html).
Atmosphere and Temperature records · 2026 now use **H3r5** in both World and
Japan. The two galleries retain Water, Fiber, the orbital observer, and the
three Hamonshū details. This is the current local edition selected after the
[r3/r5/r8 comparison](../setouchi-h3-trials-20261106/index.html).

- [World maps and legends](print/world.pdf), four 44 × 19.052559-inch pages.
- [Japan maps and legends](print/japan.pdf), four pages of the same size.
- [Saved settings](../../config/setouchi-futures-20261106-h3r5.json).
- [Provenance and artifact hashes](prepared.json).
- [Validation receipt](validation.json).
- [Development record](../../docs/development/20261106_setouchi_triennale_futures.md#selected-h3r5-edition--6-november-2026).

The selected print index also links each map's PDF, SVG, and 300 dpi PNG,
and its separate legend/source PDF. SVGs retain reference vectors and named
data layers linked to adjacent `layers/` PNGs; keep that directory with the
SVG. PDFs embed those raster layers. Map geometry and imagery are identical
to the validated r5 trial; legends now identify the selected edition.

## Settings and interpretation

Atmosphere keeps light amber `#fcc553`, topmost white nominal 0.66 pt land
outlines, and 100 radiation-opacity levels on the shared 0–400 W/m² scale.
The 1,448,374 radiation cells occupy all 100 levels. Temperature keeps the
wine background, warm record-high classes, and blue record-low outlines.
World and Japan use the same data products and saved modified AuthaGraph
framing, including the horizontal adjustment.

Observation dates and sampled source centers are unchanged. Atmosphere uses
the archived October JAXA rasters with the original 720-samples-per-axis cap.
Temperature uses the original 0.5° CPC centers, with 62,035 covered H3r5 cells
through 28 October 2026. Daily spatial means precede strict comparisons with
1979–2025, requiring at least 30 valid history years.

Finer cells do not add observations. Cells without a sampled center are
unobserved; they do not necessarily indicate missing source pixels. Source
pixel footprints are not filled. R5 improves legibility relative to r8 at
this sheet size while retaining the original physical stroke widths.

The website package includes 640/1280-pixel cards, 3840-pixel details, and
separate legend PDFs. Japan's Water, Atmosphere, and Temperature cards keep
the saved crop; full sheets remain available. Fiber and Observer retain the
complete composition. Native WordPress blocks provide the two-column grids,
full-width observer rows, and three-column Hamonshū strip, stacked on phones.

## Rebuild and check

From the repository root:

```sh
python3 scripts/update-setouchi-futures.py prepare --workers 2
python3 tests/test-setouchi-futures.py
python3 tests/test-setouchi-radiation.py
python3 scripts/validate-setouchi-futures.py --browser
```

The active manifest selects this output. To reproduce the edition explicitly,
add `--manifest config/setouchi-futures-20261106-h3r5.json` to `prepare`.
The entry point verifies the selected trial manifest and every source artifact
before copying the validated print layers, rebuilding the legends, and
generating responsive images and print booklets. It rejects a mismatched H3
resolution, product hash, or changed style. It does not reapply already baked
outline and radiation styling.

The verified r5 trial plates are the production inputs; intermediate GeoJSON
files under `build/` are not required for this rebuild. To reaggregate the
original observations, use [the trial builder](../setouchi-h3-trials-20261106/README.md#rebuild).
That requires the pinned raw files and preserves the r5/r8 comparison edition.

Dependencies remain Inkscape, Poppler, the pinned Atkinson fonts,
Pillow/lxml/Beautiful Soup/ReportLab/requests, and the verified Hamonshū crops
in the adjacent `situationshipin.space` checkout. Use `--hamonshu-root PATH`
for another checkout or `--download-sources` for the three pinned public JPEGs.
Chrome is used for browser validation. Build caches stay under `build/`.

## Publishing later

The current website and media library have not been updated. The new print
files are local/repository deliverables; the publisher still uploads only the
36 media assets used by the gallery blocks. Its default bundle now follows
the active manifest, so planning selects H3r5 rather than the archived r3 set.

```sh
python3 scripts/update-setouchi-futures.py plan --transport rest
python3 scripts/update-setouchi-futures.py apply \
  --plan output/setouchi-futures-h3r5-20261106/private/publish-plan.json
python3 scripts/update-setouchi-futures.py verify \
  --receipt output/setouchi-futures-h3r5-20261106/private/publish-receipt.json --public
```

Authentication, WP-CLI, conflict detection, and recovery retain the
[documented workflow](../setouchi-futures-20261106/README.md#publish-later-without-routine-wordpress-ui-work).
Use the current bundle paths above. Keep credentials, backups, and receipts
private; they are ignored by Git. Preparation, tests, and validation perform
no publishing or outreach. The illustrated brief and contact draft remain unsent.

The [saved H3r3 gallery](../setouchi-futures-20261106/index.html), original atlas
masters, and [resolution comparison](../setouchi-h3-trials-20261106/index.html)
remain available for reference.
